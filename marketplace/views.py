from django.shortcuts import get_object_or_404, render, redirect
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.db.models import Q
from core.models import SupplyDemandPost, Product, FarmerProfile


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
    post = get_object_or_404(SupplyDemandPost.objects.select_related('author'), pk=pk)
    return render(request, 'marketplace_detail.html', {'post': post})
