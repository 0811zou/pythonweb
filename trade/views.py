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
    # 农户不能给自己下单
    try:
        request.user.farmerprofile
        messages.warning(request, '农户账号无法下单')
        return redirect('products:farmer_dashboard')
    except FarmerProfile.DoesNotExist:
        pass

    product_id = request.GET.get('product') or request.POST.get('product_id')
    product = get_object_or_404(Product, pk=product_id, status='approved')

    if request.method == 'POST':
        try:
            quantity = int(request.POST.get('quantity', 1))
        except (TypeError, ValueError):
            return render(request, 'order_create.html', {'product': product, 'error': '数量必须为整数'})
        address = request.POST.get('address', '').strip()
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
                order = Order.objects.create(
                    buyer=request.user,
                    total_amount=total,
                    status='pending',
                    address=address,
                )
                OrderItem.objects.create(order=order, product_batch=batch, quantity=quantity, price=product.price)
                batch.quantity -= quantity
                batch.save(update_fields=['quantity'])
                # 通知农户
                farmer_user = product.farmer.user
                notify(farmer_user, 'order',
                    f'新订单 #{order.id}',
                    f'消费者 {request.user.username} 购买了 {product.name} x{quantity}，总价 ¥{total}',
                    reverse('trade:farmer_orders'))
        except (InvalidOperation, ValueError):
            return render(request, 'order_create.html', {'product': product, 'error': '订单金额计算失败'})
        messages.success(request, f'下单成功！订单编号 #{order.id}')
        return redirect('products:detail', pk=product.id)

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
    if order.status != 'delivered':
        return Response({'detail': '只有已完成的订单才能评价'}, status=status.HTTP_403_FORBIDDEN)

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

def farmer_orders_view(request):
    """农户查看自己产品的订单"""
    if not request.user.is_authenticated:
        from django.shortcuts import redirect as rd
        return rd('login')
    try:
        profile = request.user.farmerprofile
    except FarmerProfile.DoesNotExist:
        messages.error(request, '请先注册为农户')
        return redirect('accounts:register')
    orders = Order.objects.filter(
        items__product_batch__product__farmer=profile
    ).prefetch_related('items__product_batch__product', 'buyer').distinct().order_by('-created_at')
    return render(request, 'farmer/orders.html', {'orders': orders})


def farmer_set_tracking(request, order_id):
    """农户填写快递单号"""
    if not request.user.is_authenticated:
        return redirect('accounts:login')
    try:
        profile = request.user.farmerprofile
    except FarmerProfile.DoesNotExist:
        messages.error(request, '请先注册为农户')
        return redirect('accounts:register')
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

    # 计算选中商品的金额
    checkout_total = sum(item.product.price * item.quantity for item in items)

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
                total = sum(item.product.price * item.quantity for item in items)
                order = Order.objects.create(
                    buyer=request.user, total_amount=total,
                    receiver_name=receiver_name, phone=phone, address=address,
                    status='pending'
                )
                for item in items:
                    batch = ProductBatch.objects.filter(product=item.product, status='approved').first()
                    OrderItem.objects.create(order=order, product_batch=batch, quantity=item.quantity, price=item.product.price)
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
        payment_method = request.POST.get('payment_method', '模拟支付').strip()
        with transaction.atomic():
            order.status = 'paid'
            order.payment_method = payment_method
            order.save(update_fields=['status', 'payment_method', 'updated_at'])
            # 通知农户
            for item in order.items.all():
                if item.product_batch and item.product_batch.product.farmer:
                    try:
                        notify(item.product_batch.product.farmer.user, 'order',
                            f'新订单 #{order.id} 已支付',
                            f'消费者 {request.user.username} 购买了 {item.product_batch.product.name} x{item.quantity}，已支付 ¥{order.total_amount}',
                            reverse('trade:farmer_orders'))
                    except Exception:
                        pass
            messages.success(request, f'支付成功！订单 #{order.id} 已提交，等待农户确认发货。')
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
                total = sum(item.product.price * item.quantity for item in items)
                order = Order.objects.create(buyer=request.user, total_amount=total, address=address, status='confirmed')
                for item in items:
                    batch = ProductBatch.objects.filter(product=item.product, status='approved').first()
                    OrderItem.objects.create(order=order, product_batch=batch, quantity=item.quantity, price=item.product.price)
                    # 通知农户
                    notify(item.product.farmer.user, 'order',
                        f'新订单 #{order.id}',
                        f'消费者 {request.user.username} 购买了 {item.product.name} x{item.quantity}，总价 ¥{item.product.price * item.quantity}',
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
