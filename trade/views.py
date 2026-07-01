from decimal import Decimal, InvalidOperation
from rest_framework import viewsets, permissions, status
from rest_framework.decorators import action, api_view
from rest_framework.exceptions import PermissionDenied
from rest_framework.response import Response
from django.shortcuts import get_object_or_404, render, redirect, reverse
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.db import transaction
from django.utils import timezone
from core.models import Order, OrderItem, Cart, CartItem, Favorite, Product, ProductBatch, FarmerProfile, Review
from notifications.notify import notify, notify_farmer, notify_buyer
from core.permissions import IsOrderParticipantOrAdmin, get_farmer_profile
from accounts.views import farmer_required
from trade.serializers import OrderSerializer
from products.serializers import ReviewSerializer, ReviewDetailSerializer


class OrderViewSet(viewsets.ModelViewSet):
    queryset = Order.objects.prefetch_related('items__product_batch__product').select_related('buyer').all()
    serializer_class = OrderSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        qs = super().get_queryset().order_by('-created_at')
        if self.request.user.is_staff:
            return qs
        farmer = get_farmer_profile(self.request.user)
        if farmer:
            return qs.filter(items__product_batch__product__farmer=farmer).distinct()
        return qs.filter(buyer=self.request.user)

    def get_permissions(self):
        if self.action in ('retrieve', 'update', 'partial_update', 'destroy', 'upload_payment'):
            return [permissions.IsAuthenticated(), IsOrderParticipantOrAdmin()]
        return super().get_permissions()

    @action(detail=True, methods=['post'])
    def upload_payment(self, request, pk=None):
        order = self.get_object()
        if order.buyer_id != request.user.id and not request.user.is_staff:
            return Response({'detail':'只能为自己的订单上传付款凭证'}, status=status.HTTP_403_FORBIDDEN)
        proof = request.data.get('payment_proof')
        if not proof:
            return Response({'detail':'请上传付款凭证'}, status=status.HTTP_400_BAD_REQUEST)
        order.payment_proof = str(proof)[:500]
        order.status = 'paid_offline'
        order.save(update_fields=['payment_proof', 'status', 'updated_at'])
        return Response({'detail':'已上传，等待后台确认'})


# ===== 消费者下单 =====

def order_create_view(request):
    """消费者下单页面"""
    if not request.user.is_authenticated:
        return redirect(f"{reverse('accounts:login')}?next={request.path}")

    product_id = request.GET.get('product') or request.POST.get('product_id')
    product = get_object_or_404(Product, pk=product_id, status='approved')

    # 农户不能买自己的产品
    try:
        if request.user.farmerprofile and product.farmer.user_id == request.user.id:
            messages.warning(request, '不能购买自己的产品')
            return redirect('products:detail', pk=product.id)
    except FarmerProfile.DoesNotExist:
        pass

    if request.method == 'POST':
        try:
            quantity = int(request.POST.get('quantity', 1))
        except (TypeError, ValueError):
            return render(request, 'order_create.html', {'product': product, 'error': '数量必须为整数'})
        receiver_name = request.POST.get('receiver_name', '').strip()
        phone = request.POST.get('phone', '').strip()
        address = request.POST.get('address', '').strip()
        if not receiver_name:
            return render(request, 'order_create.html', {'product': product, 'error': '请输入收货人姓名'})
        if not phone:
            return render(request, 'order_create.html', {'product': product, 'error': '请输入联系电话'})
        if not address:
            return render(request, 'order_create.html', {'product': product, 'error': '请填写收货地址'})
        if quantity <= 0:
            return render(request, 'order_create.html', {'product': product, 'error': '数量必须大于0'})
        try:
            with transaction.atomic():
                batch = (
                    ProductBatch.objects
                    .select_for_update()
                    .filter(product=product, quantity__gte=quantity)
                    .order_by('harvest_date', 'created_at')
                    .first()
                )
                if not batch:
                    return render(request, 'order_create.html', {'product': product, 'error': '库存不足'})
                total = product.price * Decimal(quantity)
                unit_price = product.price
                # 批发价判断：满足起订量时使用批发价
                if product.wholesale_price and quantity >= product.wholesale_min_quantity:
                    unit_price = product.wholesale_price
                    total = unit_price * Decimal(quantity)
                order = Order.objects.create(
                    buyer=request.user,
                    total_amount=total,
                    receiver_name=receiver_name,
                    phone=phone,
                    address=address,
                    status='pending',
                )
                OrderItem.objects.create(order=order, product_batch=batch, quantity=quantity, price=unit_price)
                batch.quantity -= quantity
                batch.save(update_fields=['quantity'])
        except (InvalidOperation, ValueError):
            return render(request, 'order_create.html', {'product': product, 'error': '订单金额计算失败'})
        return redirect('trade:payment', order_id=order.id)

    return render(request, 'order_create.html', {'product': product})


def consumer_orders_view(request):
    """消费者订单列表"""
    if not request.user.is_authenticated:
        return redirect(f"{reverse('accounts:login')}?next={request.path}")
    orders = Order.objects.filter(buyer=request.user).prefetch_related('items__product_batch__product').order_by('-created_at')
    return render(request, 'consumer_orders.html', {'orders': orders})


@api_view(['POST'])
def order_review_api(request, order_id):
    """从已完成订单提交评价"""
    if not request.user.is_authenticated:
        return Response({'detail': '请先登录'}, status=status.HTTP_401_UNAUTHORIZED)

    order = get_object_or_404(Order, pk=order_id, buyer=request.user)
    # 付款确认后（paid 及以上状态）即可评价
    reviewable_statuses = ['paid', 'shipped', 'delivered']
    if order.status not in reviewable_statuses:
        return Response({'detail': '只有付款已确认的订单才能评价'}, status=status.HTTP_403_FORBIDDEN)

    product_id = request.data.get('product_id')
    if not product_id:
        return Response({'detail': '请指定要评价的产品'}, status=status.HTTP_400_BAD_REQUEST)

    product = get_object_or_404(Product, pk=product_id)

    # 验证该产品确实在此订单中
    has_item = order.items.filter(product_batch__product=product).exists()
    if not has_item:
        return Response({'detail': '该产品不在此订单中'}, status=status.HTTP_400_BAD_REQUEST)

    # 检查是否已评价过（按订单+产品去重）
    existing = Review.objects.filter(order=order, buyer=request.user, product=product).first()
    if existing:
        return Response({'detail': '您已对该产品评价过了'}, status=status.HTTP_409_CONFLICT)

    serializer = ReviewSerializer(data=request.data)
    if serializer.is_valid():
        serializer.save(
            order=order, buyer=request.user,
            farmer=product.farmer, product=product
        )
        return Response(serializer.data, status=status.HTTP_201_CREATED)
    return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


# ===== 农户端订单与物流 =====

@farmer_required
def farmer_orders_view(request):
    """农户查看自己产品的订单"""
    profile = request.farmer_profile
    orders = Order.objects.filter(
        items__product_batch__product__farmer=profile
    ).prefetch_related('items__product_batch__product', 'buyer').distinct().order_by('-created_at')
    return render(request, 'farmer/orders.html', {'orders': orders})


@farmer_required
def farmer_set_tracking(request, order_id):
    """农户填写快递单号"""
    profile = request.farmer_profile
    order = get_object_or_404(Order, pk=order_id, items__product_batch__product__farmer=profile)
    if request.method == 'POST':
        tracking = request.POST.get('tracking_number', '').strip()
        if not tracking:
            messages.error(request, '请输入快递单号')
        else:
            order.tracking_number = tracking
            order.status = 'shipped'
            order.shipped_at = timezone.now()
            order.save(update_fields=['tracking_number', 'status', 'shipped_at'])
            # 通知买家
            notify_buyer(order, 'order',
                f'订单 #{order.id} 已发货',
                f'快递单号: {tracking}',
                reverse('trade:consumer_orders'))
            messages.success(request, '发货成功')
        return redirect('trade:farmer_orders')
    return render(request, 'farmer/tracking_form.html', {'order': order})


# ===== 购物车 =====

@login_required
def cart_view(request):
    """购物车页面"""
    cart, _ = Cart.objects.get_or_create(user=request.user)
    items = cart.items.select_related('product').all()
    return render(request, 'cart.html', {'cart': cart, 'items': items})


@login_required
def cart_add(request, pk):
    """加入购物车"""
    product = get_object_or_404(Product, pk=pk, status='approved')
    if request.method == 'POST':
        cart, _ = Cart.objects.get_or_create(user=request.user)
        item, created = CartItem.objects.get_or_create(cart=cart, product=product, defaults={'quantity': 1})
        if not created:
            item.quantity += 1
            item.save()
        messages.success(request, f'「{product.name}」已加入购物车')
    return redirect(request.META.get('HTTP_REFERER', 'product_list'))


@login_required
def cart_remove(request, pk):
    """从购物车移除"""
    if request.method == 'POST':
        cart = get_object_or_404(Cart, user=request.user)
        CartItem.objects.filter(cart=cart, product_id=pk).delete()
        messages.success(request, '已从购物车移除')
    return redirect('trade:cart_view')


@login_required
def cart_checkout(request):
    """购物车结算"""
    cart = get_object_or_404(Cart, user=request.user)
    all_items = list(cart.items.select_related('product__farmer').all())

    # 支持从购物车页面勾选后跳转，只结算选中的商品
    item_ids = request.GET.getlist('item_ids')
    if item_ids:
        items = [it for it in all_items if str(it.id) in item_ids]
        if not items:
            messages.warning(request, '所选商品不存在')
            return redirect('trade:cart_view')
    else:
        items = all_items

    if not items:
        messages.warning(request, '购物车为空')
        return redirect('trade:cart_view')

    # 计算选中商品的金额（含批发价逻辑）
    def effective_price(pr, qty):
        if pr.wholesale_price and qty >= pr.wholesale_min_quantity:
            return pr.wholesale_price
        return pr.price

    checkout_total = sum(effective_price(item.product, item.quantity) * item.quantity for item in items)

    if request.method == 'POST':
        receiver_name = request.POST.get('receiver_name', '').strip()
        phone = request.POST.get('phone', '').strip()
        address = request.POST.get('address', '').strip()
        if not receiver_name:
            messages.error(request, '请输入收货人姓名')
            return render(request, 'cart_checkout.html', {
                'items': items, 'cart': cart, 'checkout_total': checkout_total
            })
        if not phone:
            messages.error(request, '请输入联系电话')
            return render(request, 'cart_checkout.html', {
                'items': items, 'cart': cart, 'checkout_total': checkout_total
            })
        if not address:
            messages.error(request, '请输入收货地址')
            return render(request, 'cart_checkout.html', {
                'items': items, 'cart': cart, 'checkout_total': checkout_total
            })
        try:
            with transaction.atomic():
                total = Decimal('0')
                for item in items:
                    total += effective_price(item.product, item.quantity) * item.quantity
                order = Order.objects.create(
                    buyer=request.user, total_amount=total,
                    receiver_name=receiver_name, phone=phone, address=address,
                    status='pending'
                )
                for item in items:
                    batch = (
                        ProductBatch.objects
                        .select_for_update()
                        .filter(product=item.product, status='approved', quantity__gte=item.quantity)
                        .order_by('harvest_date', 'created_at')
                        .first()
                    )
                    if not batch:
                        raise ValueError(f'「{item.product.name}」库存不足，请返回购物车调整数量')
                    up = effective_price(item.product, item.quantity)
                    OrderItem.objects.create(order=order, product_batch=batch, quantity=item.quantity, price=up)
                    batch.quantity -= item.quantity
                    batch.save(update_fields=['quantity'])
                # 只删除已结算的商品（保留未选中的）
                CartItem.objects.filter(id__in=[it.id for it in items]).delete()
                return redirect('trade:payment', order_id=order.id)
        except Exception as e:
            messages.error(request, f'下单失败：{str(e)}')
    return render(request, 'cart_checkout.html', {
        'items': items, 'cart': cart, 'checkout_total': checkout_total
    })


@login_required
def payment_view(request, order_id):
    """支付页面——订单创建后进入"""
    order = get_object_or_404(Order.objects.select_related('buyer').prefetch_related(
        'items__product_batch__product__farmer'
    ), pk=order_id, buyer=request.user)

    if order.status != 'pending':
        messages.info(request, '该订单已支付或已取消')
        return redirect('trade:consumer_orders')

    # 收集订单中涉及的所有农户的收款方式
    farmer_ids = set()
    for item in order.items.all():
        if item.product_batch and item.product_batch.product.farmer:
            farmer_ids.add(item.product_batch.product.farmer_id)

    farmer_methods = {}
    from accounts.models import FarmerPaymentMethod
    for fid in farmer_ids:
        methods = FarmerPaymentMethod.objects.filter(farmer_id=fid, is_active=True)
        if methods.exists():
            farmer_methods[fid] = methods

    if request.method == 'POST':
        payment_method = request.POST.get('payment_method', '').strip()
        payment_proof = request.FILES.get('payment_proof')
        if not payment_method:
            messages.error(request, '请选择付款方式')
            return render(request, 'trade/payment.html', {'order': order, 'farmer_methods': farmer_methods})
        if not payment_proof:
            messages.error(request, '请上传付款凭证截图')
            return render(request, 'trade/payment.html', {'order': order, 'farmer_methods': farmer_methods})
        # 保存上传的凭证图片
        from django.core.files.storage import default_storage
        from django.core.files.base import ContentFile
        import os
        ext = os.path.splitext(payment_proof.name)[1] or '.jpg'
        save_name = f'payment_proofs/order_{order.id}_{request.user.id}{ext}'
        saved_path = default_storage.save(save_name, ContentFile(payment_proof.read()))
        with transaction.atomic():
            order.status = 'paid_offline'
            order.payment_method = payment_method
            order.payment_proof = saved_path
            order.save(update_fields=['status', 'payment_method', 'payment_proof', 'updated_at'])
            # 通知农户：用户已付款，等待平台确认
            for item in order.items.all():
                if item.product_batch and item.product_batch.product.farmer:
                    try:
                        notify(item.product_batch.product.farmer.user, 'order',
                            f'订单 #{order.id} 用户已提交付款凭证',
                            f'消费者 {request.user.username} 已为 {item.product_batch.product.name} 付款 ¥{order.total_amount}，等待平台审核确认。',
                            reverse('trade:farmer_orders'))
                    except Exception:
                        pass
        messages.success(request, f'付款凭证已提交！订单 #{order.id} 等待管理员审核确认。')
        return redirect('trade:consumer_orders')

    return render(request, 'trade/payment.html', {
        'order': order,
        'farmer_methods': farmer_methods,
    })


@login_required
def cart_batch_checkout(request):
    """购物车勾选多件商品批量下单"""
    cart = get_object_or_404(Cart, user=request.user)
    if request.method == 'POST':
        item_ids = request.POST.getlist('selected_items')
        address = request.POST.get('address', '').strip()
        if not item_ids:
            messages.error(request, '请选择要购买的商品')
            return redirect('trade:cart_view')
        if not address:
            messages.error(request, '请填写收货地址')
            return redirect('trade:cart_view')
        items = CartItem.objects.filter(id__in=item_ids, cart=cart).select_related('product__farmer')
        if not items:
            messages.error(request, '所选商品不存在')
            return redirect('trade:cart_view')
        try:
            with transaction.atomic():
                total = Decimal('0')
                for item in items:
                    up = item.product.wholesale_price if (item.product.wholesale_price and item.quantity >= item.product.wholesale_min_quantity) else item.product.price
                    total += up * item.quantity
                order = Order.objects.create(buyer=request.user, total_amount=total, address=address, status='confirmed')
                for item in items:
                    batch = (
                        ProductBatch.objects
                        .select_for_update()
                        .filter(product=item.product, status='approved', quantity__gte=item.quantity)
                        .order_by('harvest_date', 'created_at')
                        .first()
                    )
                    if not batch:
                        raise ValueError(f'「{item.product.name}」库存不足，请返回购物车调整数量')
                    up = item.product.wholesale_price if (item.product.wholesale_price and item.quantity >= item.product.wholesale_min_quantity) else item.product.price
                    OrderItem.objects.create(order=order, product_batch=batch, quantity=item.quantity, price=up)
                    batch.quantity -= item.quantity
                    batch.save(update_fields=['quantity'])
                    # 通知农户
                    notify(item.product.farmer.user, 'order',
                        f'新订单 #{order.id}',
                        f'消费者 {request.user.username} 购买了 {item.product.name} x{item.quantity}，总价 ¥{up * item.quantity}',
                        reverse('trade:farmer_orders'))
                items.delete()
                messages.success(request, f'下单成功！订单编号 #{order.id}')
                return redirect('trade:consumer_orders')
        except Exception as e:
            messages.error(request, f'下单失败：{str(e)}')
            return redirect('trade:cart_view')
    return redirect('trade:cart_view')


# ===== 收藏夹 =====

@login_required
def favorites_view(request):
    """收藏列表"""
    favorites = Favorite.objects.filter(user=request.user).select_related('product').order_by('-created_at')
    return render(request, 'favorites.html', {'favorites': favorites})


@login_required
def favorite_toggle(request, pk):
    """切换收藏状态"""
    product = get_object_or_404(Product, pk=pk)
    fav, created = Favorite.objects.get_or_create(user=request.user, product=product)
    if not created:
        fav.delete()
        messages.info(request, f'已取消收藏「{product.name}」')
    else:
        messages.success(request, f'已收藏「{product.name}」')
    return redirect(request.META.get('HTTP_REFERER', 'product_list'))
