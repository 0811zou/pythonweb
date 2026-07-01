from django.shortcuts import get_object_or_404, render, redirect
from django.urls import reverse
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.db.models import Q
from core.models import SupplyDemandPost, Product, FarmerProfile
from .models import DemandResponse
from notifications.notify import notify


def supply_demand_list(request):
    """供需对接列表页"""
    post_type = request.GET.get('type', '')
    category = request.GET.get('category', '')
    region = request.GET.get('region', '')
    search = request.GET.get('search', '')

    posts = SupplyDemandPost.objects.filter(status='active').select_related('author').order_by('-created_at')
    if post_type:
        posts = posts.filter(post_type=post_type)
    if category:
        posts = posts.filter(category=category)
    if region:
        posts = posts.filter(region__icontains=region)
    if search:
        posts = posts.filter(Q(product_name__icontains=search) | Q(description__icontains=search))

    # 为农户匹配其产品相关的需求帖
    matching_demands = None
    if request.user.is_authenticated:
        try:
            profile = request.user.farmerprofile
            farmer_categories = Product.objects.filter(farmer=profile, status='approved').values_list('category', flat=True).distinct()
            if farmer_categories:
                matching_demands = SupplyDemandPost.objects.filter(
                    post_type='demand', status='active',
                    category__in=farmer_categories,
                ).select_related('author').order_by('-created_at')[:5]
        except FarmerProfile.DoesNotExist:
            pass

    return render(request, 'marketplace.html', {
        'posts': posts,
        'current_type': post_type,
        'current_category': category,
        'current_region': region,
        'current_search': search,
        'matching_demands': matching_demands,
    })


@login_required
def supply_demand_create(request):
    """发布供需帖子——消费者只能发需求，农户只能发供应"""
    is_farmer = hasattr(request.user, 'farmerprofile')

    # 根据角色自动确定发布类型
    if is_farmer:
        default_type = 'supply'
    else:
        default_type = 'demand'

    if request.method == 'POST':
        post_type = request.POST.get('post_type', default_type)

        # 强制校验：消费者只能发需求，农户只能发供应
        if is_farmer and post_type != 'supply':
            messages.error(request, '农户只能发布供应信息')
            return redirect('marketplace:create')
        if not is_farmer and post_type != 'demand':
            messages.error(request, '消费者只能发布需求信息')
            return redirect('marketplace:create')

        product_name = request.POST.get('product_name', '').strip()
        category = request.POST.get('category', '').strip()
        quantity = request.POST.get('quantity', '0')
        unit = request.POST.get('unit', 'kg')
        price_range = request.POST.get('price_range', '').strip()
        region = request.POST.get('region', '').strip()
        description = request.POST.get('description', '').strip()

        try:
            qty = int(quantity)
        except (TypeError, ValueError):
            messages.error(request, '请输入有效数量')
            return render(request, 'marketplace_create.html', {'is_farmer': is_farmer})

        if not product_name or qty <= 0:
            messages.error(request, '请填写产品名称和有效数量')
            return render(request, 'marketplace_create.html', {'is_farmer': is_farmer})

        SupplyDemandPost.objects.create(
            author=request.user,
            post_type=post_type,
            product_name=product_name,
            category=category,
            quantity=qty,
            unit=unit,
            price_range=price_range,
            region=region,
            description=description,
        )
        messages.success(request, '供需信息发布成功！')
        return redirect('marketplace:list')

    return render(request, 'marketplace_create.html', {'is_farmer': is_farmer})


def supply_demand_detail(request, pk):
    """供需帖子详情"""
    post = get_object_or_404(
        SupplyDemandPost.objects.select_related('author'),
        pk=pk
    )

    # 关闭自己的帖子
    if request.method == 'POST' and request.user == post.author:
        action = request.POST.get('action', '')
        if action == 'close' and post.status == 'active':
            post.status = 'closed'
            post.save(update_fields=['status'])
            messages.success(request, '帖子已关闭')
        elif action == 'reopen' and post.status == 'closed':
            post.status = 'active'
            post.save(update_fields=['status'])
            messages.success(request, '帖子已重新开启')
        return redirect('marketplace:detail', pk=post.pk)

    # 获取发帖人的联系方式
    author_profile = None
    author_phone = ''
    author_address = ''
    author_shop_url = ''
    try:
        author_profile = post.author.farmerprofile
        author_phone = author_profile.phone or ''
        author_address = author_profile.address or ''
        from django.urls import reverse
        author_shop_url = reverse('accounts:farmer_shop', args=[author_profile.id])
    except FarmerProfile.DoesNotExist:
        pass

    # 供应帖：尝试匹配发帖人的同名产品
    matching_product = None
    if post.post_type == 'supply' and author_profile:
        matching_product = Product.objects.filter(
            farmer=author_profile,
            name__iexact=post.product_name,
            status='approved',
        ).first()
        if not matching_product:
            matching_product = Product.objects.filter(
                farmer=author_profile,
                name__icontains=post.product_name,
                status='approved',
            ).first()

    # 需求帖：获取农户主动响应的产品
    farmer_responses = []
    if post.post_type == 'demand':
        farmer_responses = list(post.responses.select_related(
            'farmer__user', 'product'
        ).order_by('-created_at'))

    # 当前登录农户是否已响应过
    user_has_responded = False
    user_farmer_profile = None
    if request.user.is_authenticated:
        try:
            user_farmer_profile = request.user.farmerprofile
            if user_farmer_profile.verified:
                user_has_responded = post.responses.filter(farmer=user_farmer_profile).exists()
        except FarmerProfile.DoesNotExist:
            pass

    is_author = request.user == post.author if request.user.is_authenticated else False

    return render(request, 'marketplace_detail.html', {
        'post': post,
        'author_phone': author_phone,
        'author_address': author_address,
        'author_shop_url': author_shop_url,
        'matching_product': matching_product,
        'farmer_responses': farmer_responses,
        'user_has_responded': user_has_responded,
        'is_farmer': bool(user_farmer_profile and user_farmer_profile.verified),
        'is_author': is_author,
    })


@login_required
def respond_to_demand(request, pk):
    """农户主动响应需求帖，提供自己的产品"""
    post = get_object_or_404(SupplyDemandPost, pk=pk, post_type='demand', status='active')

    # 仅农户可响应
    try:
        farmer = request.user.farmerprofile
        if not farmer.verified:
            messages.warning(request, '您的入驻申请尚未通过审核，审核通过后即可响应需求。')
            return redirect('marketplace:detail', pk=pk)
    except FarmerProfile.DoesNotExist:
        messages.error(request, '只有入驻农户才能响应需求')
        return redirect('marketplace:detail', pk=pk)

    # 不能响应自己的需求帖
    if post.author == request.user:
        messages.warning(request, '不能响应自己发布的需求帖')
        return redirect('marketplace:detail', pk=pk)

    # 检查是否已响应过
    if DemandResponse.objects.filter(demand_post=post, farmer=farmer).exists():
        messages.info(request, '您已对该需求响应过了')
        return redirect('marketplace:detail', pk=pk)

    # 获取该农户已上架且同品类的产品
    farmer_products = Product.objects.filter(
        farmer=farmer, status='approved'
    ).filter(
        Q(category=post.category) | Q(category='')
    ).order_by('-created_at')

    if request.method == 'POST':
        product_id = request.POST.get('product_id')
        message = request.POST.get('message', '').strip()
        product = get_object_or_404(Product, pk=product_id, farmer=farmer, status='approved')

        DemandResponse.objects.create(
            farmer=farmer,
            demand_post=post,
            product=product,
            message=message,
        )
        # 通知需求发布者
        notify(post.author, 'demand_response',
            f'农户 {request.user.username} 响应了你的需求「{post.product_name}」',
            f'提供了「{product.name}」¥{product.price}/{product.unit}，{message or ""}',
            reverse('marketplace:detail', args=[pk]))
        messages.success(request, f'已用「{product.name}」响应该需求，买家已收到通知！')
        return redirect('marketplace:detail', pk=pk)

    return render(request, 'marketplace_respond.html', {
        'post': post,
        'farmer_products': farmer_products,
    })
