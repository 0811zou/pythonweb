from functools import wraps
from django.shortcuts import get_object_or_404, render, redirect, reverse
from django.contrib.auth.models import User
from django.contrib import messages
from django.utils import timezone
from core.models import Product, ProductBatch, Order, FarmerProfile, generate_batch_code, TraceEvent, JoinApplication
from notifications.notify import notify, notify_farmer, notify_buyer


# ===== 装饰器 =====

def admin_required(view_func):
    """装饰器：检查是否为管理员"""
    @wraps(view_func)
    def wrapper(request, *args, **kwargs):
        if not request.user.is_authenticated or not request.user.is_staff:
            messages.error(request, '无权限')
            return redirect('/')
        return view_func(request, *args, **kwargs)
    return wrapper


# ===== 管理后台首页 =====

@admin_required
def admin_dashboard(request):
    """管理后台首页"""
    products_pending = Product.objects.filter(status='pending').count()
    products_total = Product.objects.count()
    farmers_total = FarmerProfile.objects.count()
    users_total = User.objects.count()
    orders_total = Order.objects.count()
    batches_pending = ProductBatch.objects.filter(status='pending').count()
    return render(request, 'admin/dashboard.html', {
        'products_pending': products_pending,
        'products_total': products_total,
        'farmers_total': farmers_total,
        'users_total': users_total,
        'orders_total': orders_total,
        'batches_pending': batches_pending,
    })


# ===== 产品审核 =====

@admin_required
def admin_products(request):
    """管理端 — 产品审核"""
    status_filter = request.GET.get('status', 'pending')
    products = Product.objects.select_related('farmer__user').all()
    if status_filter != 'all':
        products = products.filter(status=status_filter)
    products = products.order_by('-created_at')
    return render(request, 'admin/products.html', {
        'products': products,
        'current_status': status_filter,
    })


@admin_required
def admin_product_review(request, pk, action):
    """管理端 — 审核操作"""
    if request.method != 'POST':
        messages.error(request, '审核操作请通过页面按钮提交')
        return redirect('admin_panel:products')
    product = get_object_or_404(Product, pk=pk)
    if action == 'approve':
        product.status = 'approved'
        product.review_note = request.POST.get('note', '审核通过')
        messages.success(request, f'「{product.name}」已通过审核')
    elif action == 'reject':
        note = request.POST.get('note', '').strip()
        product.status = 'rejected'
        product.review_note = note
        messages.warning(request, f'「{product.name}」未通过审核')
    else:
        messages.error(request, '未知审核操作')
        return redirect('admin_panel:products')
    product.save(update_fields=['status', 'review_note'])
    # 通知农户
    if action == 'approve':
        notify_farmer(product, 'product',
            f'产品「{product.name}」已通过审核',
            '你的产品已上架，消费者可以浏览和购买了',
            reverse('products:farmer_dashboard'))
    else:
        notify_farmer(product, 'product',
            f'产品「{product.name}」未通过审核',
            f'原因: {product.review_note}',
            reverse('products:farmer_dashboard'))
    return redirect('admin_panel:products')


# ===== 用户管理 =====

@admin_required
def admin_users(request):
    """管理端 — 用户管理（含产品与批次信息）"""
    from products.models import Product
    users = list(User.objects.select_related('farmerprofile').all().order_by('-date_joined'))
    # 构建用户ID→索引映射，O(1)查找
    user_idx = {u.id: i for i, u in enumerate(users)}
    for u in users:
        u.user_products = []
        u.user_batches = []
    # 产品按农户分组
    for p in Product.objects.select_related('farmer__user').all().order_by('-created_at'):
        idx = user_idx.get(p.farmer.user_id)
        if idx is not None:
            users[idx].user_products.append(p)
    # 批次按农户分组
    for b in ProductBatch.objects.select_related('product__farmer').all().order_by('-created_at'):
        fid = b.product.farmer_id
        if fid:
            idx = user_idx.get(b.product.farmer.user_id)
            if idx is not None:
                users[idx].user_batches.append(b)
    # 批次按产品分组（供产品详情展示已通过批次）
    product_batches = {}
    for b in ProductBatch.objects.select_related('product').filter(status='approved').order_by('-created_at'):
        product_batches.setdefault(b.product_id, []).append(b)
    for u in users:
        for p in u.user_products:
            p.approved_batches = product_batches.get(p.id, [])
    return render(request, 'admin/users.html', {'users': users})


# ===== 批次审核 =====

@admin_required
def admin_batches(request):
    """批次审核列表"""
    status_filter = request.GET.get('status', 'all')
    batches = ProductBatch.objects.select_related('product__farmer__user').all()
    if status_filter != 'all':
        batches = batches.filter(status=status_filter)
    batches = batches.order_by('-created_at')
    return render(request, 'admin/batches.html', {'batches': batches, 'current_status': status_filter})


@admin_required
def admin_batch_review(request, pk, action):
    """审核批次 — 通过时生成批次编码和二维码"""
    if request.method != 'POST':
        return redirect('admin_panel:batches')
    batch = get_object_or_404(ProductBatch, pk=pk)
    if action == 'approve':
        batch.status = 'approved'
        if not batch.batch_code:
            batch.batch_code = generate_batch_code()
        batch.save(update_fields=['status', 'batch_code'])
        batch.ensure_qr_code()
        TraceEvent.objects.create(batch=batch, event_type='qc', title='质检通过', operator=request.user, description='批次审核通过，准予上架，已生成溯源编码和二维码')
        messages.success(request, f'批次 {batch.batch_code} 已通过，编码和二维码已生成')
    elif action == 'reject':
        batch.status = 'rejected'
        note = request.POST.get('note', '').strip()
        batch.save(update_fields=['status'])
        TraceEvent.objects.create(batch=batch, event_type='qc', title='质检未通过', operator=request.user, description=note or '未通过质检审核')
        messages.warning(request, f'批次 #{batch.pk} 未通过')
    else:
        messages.error(request, '未知操作')
        return redirect('admin_panel:batches')
    # 通知农户
    farmer_user = batch.product.farmer.user
    if action == 'approve':
        notify(farmer_user, 'batch',
            f'批次 {batch.batch_code} 质检通过',
            f'产品「{batch.product.name}」批次已通过审核，二维码已可用',
            reverse('products:farmer_batch_detail', args=[batch.pk]))
    else:
        note = request.POST.get('note', '').strip() or '未通过质检审核'
        notify(farmer_user, 'batch',
            f'批次 #{batch.pk} 未通过',
            f'原因: {note}',
            reverse('products:farmer_batch_detail', args=[batch.pk]))
    return redirect('admin_panel:batches')


# ===== CSV 导出 =====

@admin_required
def export_orders_csv(request):
    """导出订单 CSV"""
    import csv
    from django.http import HttpResponse
    response = HttpResponse(content_type='text/csv; charset=utf-8-sig')
    response['Content-Disposition'] = 'attachment; filename="orders.csv"'
    writer = csv.writer(response)
    writer.writerow(['订单号', '买家', '总金额', '状态', '地址', '快递单号', '创建时间'])
    for o in Order.objects.select_related('buyer').order_by('-created_at'):
        writer.writerow([o.id, o.buyer.username, o.total_amount, o.status, o.address, o.tracking_number, o.created_at])
    return response


@admin_required
def export_products_csv(request):
    """导出产品 CSV"""
    import csv
    from django.http import HttpResponse
    response = HttpResponse(content_type='text/csv; charset=utf-8-sig')
    response['Content-Disposition'] = 'attachment; filename="products.csv"'
    writer = csv.writer(response)
    writer.writerow(['产品名', '分类', '品种', '价格', '单位', '农户', '状态', '创建时间'])
    for p in Product.objects.select_related('farmer__user').order_by('-created_at'):
        writer.writerow([p.name, p.category, p.variety, p.price, p.unit, p.farmer.user.username, p.status, p.created_at])
    return response


@admin_required
def admin_applications(request):
    """入驻申请审核"""
    status_filter = request.GET.get('status', 'pending')
    apps = JoinApplication.objects.select_related('user').order_by('-created_at')
    if status_filter and status_filter != 'all':
        apps = apps.filter(status=status_filter)

    if request.method == 'POST':
        app_id = request.POST.get('app_id')
        action = request.POST.get('action')
        note = request.POST.get('reviewer_note', '').strip()
        app = get_object_or_404(JoinApplication, pk=app_id)
        if action == 'approve':
            app.status = 'approved'
            app.reviewer_note = note
            app.reviewed_by = request.user
            app.save()
            # 验证农户资料
            if app.user:
                fp, created = FarmerProfile.objects.get_or_create(user=app.user)
                if not fp.verified:
                    fp.verified = True
                    fp.phone = fp.phone or app.phone
                    fp.address = fp.address or app.region
                    fp.save(update_fields=['verified', 'phone', 'address'])
                # 通知农户
                notify(app.user, 'system',
                    '入驻申请已通过',
                    f'恭喜！您的入驻申请已通过审核。现在可以使用农户功能，开始上架产品了！',
                    reverse('products:farmer_dashboard'))
            messages.success(request, f'已通过「{app.name}」的入驻申请，农户审核状态已激活')
        elif action == 'reject':
            app.status = 'rejected'
            app.reviewer_note = note
            app.reviewed_by = request.user
            app.save()
            if app.user:
                notify(app.user, 'system',
                    '入驻申请未通过',
                    f'很遗憾，您的入驻申请未通过审核。原因：{note or "未说明"}。请重新提交申请。',
                    reverse('core:apply_join'))
            messages.warning(request, f'已拒绝「{app.name}」的入驻申请')
        return redirect('admin_panel:applications')

    return render(request, 'admin/applications.html', {
        'applications': apps,
        'status_filter': status_filter,
    })


# ===== 支付审核 =====

@admin_required
def admin_payments(request):
    """管理端 — 付款凭证审核"""
    status_filter = request.GET.get('status', 'paid_offline')
    orders = Order.objects.select_related('buyer').prefetch_related(
        'items__product_batch__product__farmer__user'
    ).filter(status__in=['paid_offline', 'paid'])
    if status_filter == 'paid_offline':
        orders = orders.filter(status='paid_offline')
    elif status_filter == 'paid':
        orders = orders.filter(status='paid')
    elif status_filter == 'all':
        pass
    else:
        orders = orders.filter(status='paid_offline')
    orders = orders.order_by('-created_at')
    return render(request, 'admin/payments.html', {
        'orders': orders,
        'current_status': status_filter,
    })


@admin_required
def admin_payment_review(request, pk, action):
    """管理端 — 审核付款凭证"""
    if request.method != 'POST':
        messages.error(request, '请通过页面按钮操作')
        return redirect('admin_panel:payments')
    order = get_object_or_404(Order.objects.select_related('buyer').prefetch_related(
        'items__product_batch__product__farmer__user'
    ), pk=pk)
    if action == 'confirm':
        order.status = 'paid'
        order.save(update_fields=['status', 'updated_at'])
        # 通知所有相关农户：付款已确认，请发货
        for item in order.items.all():
            if item.product_batch and item.product_batch.product.farmer:
                try:
                    notify(item.product_batch.product.farmer.user, 'order',
                        f'订单 #{order.id} 付款已确认',
                        f'消费者 {order.buyer.username} 已付款 ¥{order.total_amount}，请尽快安排发货！收货人：{order.receiver_name}，电话：{order.phone}，地址：{order.address}',
                        reverse('trade:farmer_orders'))
                except Exception:
                    pass
        # 通知买家：支付已确认
        try:
            notify_buyer(order, 'order',
                f'订单 #{order.id} 付款已确认',
                f'平台已确认您的付款 ¥{order.total_amount}，农户将尽快为您发货。',
                reverse('trade:consumer_orders'))
        except Exception:
            pass
        messages.success(request, f'订单 #{order.id} 付款已确认，已通知农户发货')
    elif action == 'reject':
        note = request.POST.get('note', '').strip()
        if not note:
            messages.error(request, '请填写拒绝原因')
            return redirect('admin_panel:payments')
        order.status = 'pending'
        order.payment_proof = ''
        order.save(update_fields=['status', 'payment_proof', 'updated_at'])
        # 通知买家：付款凭证被拒
        try:
            notify_buyer(order, 'order',
                f'订单 #{order.id} 付款凭证未通过',
                f'您的付款凭证审核未通过。原因：{note}。请重新上传正确的付款凭证。',
                reverse('trade:payment', kwargs={'order_id': order.id}))
        except Exception:
            pass
        messages.warning(request, f'订单 #{order.id} 凭证已退回，已通知买家重新上传')
    else:
        messages.error(request, '未知操作')
    return redirect('admin_panel:payments')
