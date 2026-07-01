from rest_framework import viewsets, permissions, status
from rest_framework.decorators import action, api_view, permission_classes
from rest_framework.exceptions import PermissionDenied
from rest_framework.response import Response
from drf_spectacular.utils import extend_schema
from drf_spectacular.types import OpenApiTypes
from django.shortcuts import get_object_or_404, render, redirect, reverse
from django.contrib import messages
from django.db.models import Count, Sum, Q
from django.utils import timezone
from django.db.models.functions import TruncMonth
from decimal import Decimal, InvalidOperation
from functools import wraps
from core.models import Product, ProductBatch, Order, OrderItem, FarmerProfile, Review, TraceEvent, SupplyDemandPost, FarmingGuide, Favorite
from core.permissions import IsFarmerOwnerOrAdmin, get_farmer_profile
from products.serializers import ProductSerializer, ProductBatchSerializer, ReviewSerializer, ReviewDetailSerializer
from trade.serializers import OrderSerializer


class ProductViewSet(viewsets.ModelViewSet):
    queryset = Product.objects.select_related('farmer__user').prefetch_related('batches').all()
    serializer_class = ProductSerializer
    permission_classes = [IsFarmerOwnerOrAdmin]
    ordering = ['-created_at']

    def get_queryset(self):
        qs = super().get_queryset().order_by('-created_at')
        farmer = get_farmer_profile(self.request.user)

        if self.request.method in permissions.SAFE_METHODS:
            if self.request.user.is_authenticated and self.request.user.is_staff:
                pass
            elif self.request.query_params.get('mine') == '1' and farmer:
                qs = qs.filter(farmer=farmer)
            else:
                qs = qs.filter(status='approved')
        elif self.request.user.is_staff:
            pass
        elif farmer:
            qs = qs.filter(farmer=farmer)
        else:
            return Product.objects.none()

        category = self.request.query_params.get('category')
        variety = self.request.query_params.get('variety')
        origin = self.request.query_params.get('origin')
        search = self.request.query_params.get('search')
        if category:
            qs = qs.filter(category=category)
        if variety:
            qs = qs.filter(variety=variety)
        if origin:
            qs = qs.filter(farmer__address__icontains=origin)
        if search:
            qs = qs.filter(Q(name__icontains=search) | Q(description__icontains=search))
        return qs

    def perform_create(self, serializer):
        farmer = get_farmer_profile(self.request.user)
        if self.request.user.is_staff:
            raise PermissionDenied('管理员请在后台为指定农户创建产品')
        elif farmer:
            serializer.save(farmer=farmer, status='pending')
        else:
            raise PermissionDenied('只有农户可以发布产品')

    def perform_update(self, serializer):
        product = self.get_object()
        next_status = product.status
        if not self.request.user.is_staff and product.status in ('approved', 'pending'):
            next_status = 'pending'
        serializer.save(status=next_status)


# ===== 省份提取工具 =====
CHINA_PROVINCES = [
    '北京市', '天津市', '上海市', '重庆市',
    '河北省', '山西省', '辽宁省', '吉林省', '黑龙江省',
    '江苏省', '浙江省', '安徽省', '福建省', '江西省', '山东省', '河南省',
    '湖北省', '湖南省', '广东省', '海南省',
    '四川省', '贵州省', '云南省', '陕西省', '甘肃省', '青海省', '台湾省',
    '内蒙古自治区', '广西壮族自治区', '西藏自治区', '宁夏回族自治区', '新疆维吾尔自治区',
    '香港特别行政区', '澳门特别行政区',
]

def extract_province(address):
    """从地址字符串中提取省份名称"""
    if not address:
        return None
    for prov in sorted(CHINA_PROVINCES, key=len, reverse=True):
        if address.startswith(prov):
            return prov
    short_map = {'新疆': '新疆维吾尔自治区', '西藏': '西藏自治区', '内蒙古': '内蒙古自治区', '广西': '广西壮族自治区', '宁夏': '宁夏回族自治区'}
    for short, full in short_map.items():
        if address.startswith(short):
            return full
    return None


@extend_schema(responses=OpenApiTypes.OBJECT)
@api_view(['GET'])
def province_products(request):
    """按省份统计产品分布"""
    products = Product.objects.filter(status='approved').select_related('farmer__user')
    farmer_agg = (
        products.values('farmer__address', 'farmer__user__username')
        .annotate(product_count=Count('id'))
        .order_by()
    )
    province_counts = {}
    province_detail = {}
    for fp in farmer_agg:
        prov = extract_province(fp['farmer__address']) or '其他'
        province_counts[prov] = province_counts.get(prov, 0) + fp['product_count']
        if prov not in province_detail:
            province_detail[prov] = {'product_count': 0, 'farmers': [], 'products': []}
        province_detail[prov]['product_count'] += fp['product_count']
        farmer_name = fp['farmer__user__username']
        if farmer_name not in province_detail[prov]['farmers']:
            province_detail[prov]['farmers'].append(farmer_name)
    for p in products.iterator():
        prov = extract_province(p.farmer.address) or '其他'
        province_detail[prov]['products'].append({
            'id': p.id,
            'name': p.name,
            'category': p.category or '未分类',
            'price': str(p.price),
            'unit': p.unit,
            'image_url': request.build_absolute_uri(p.image.url) if p.image else None,
            'farmer': p.farmer.user.username,
        })
    map_data = [{'name': k, 'value': v} for k, v in sorted(province_counts.items())]
    return Response({'map_data': map_data, 'provinces': province_detail})


def province_map_view(request):
    """中国地图产品分布页面"""
    return render(request, 'map.html')


# ===== 产品评价 API =====

@extend_schema(methods=['GET'], responses=OpenApiTypes.OBJECT)
@extend_schema(methods=['POST'], request=OpenApiTypes.OBJECT, responses=OpenApiTypes.OBJECT)
@api_view(['GET'])
def product_filter_options(request):
    categories = (
        Product.objects.filter(status='approved')
        .values('category')
        .exclude(category='')
        .annotate(count=Count('id'))
        .order_by('-count')
    )
    # 品种按分类分组
    varieties_qs = (
        Product.objects.filter(status='approved')
        .values('category', 'variety')
        .exclude(variety='')
        .annotate(count=Count('id'))
        .order_by('-count')
    )
    varieties = {}
    for v in varieties_qs:
        cat = v['category'] or '其他'
        if cat not in varieties:
            varieties[cat] = []
        varieties[cat].append(v['variety'])
    # 产地（从农户地址中提取省份/地区）
    origins = (
        FarmerProfile.objects
        .exclude(address='')
        .values('address')
        .annotate(count=Count('id'))
        .order_by('-count')
    )
    return Response({
        'categories': [c['category'] for c in categories],
        'varieties': varieties,
        'origins': [o['address'][:10] for o in origins if o['address']],
    })


class ProductBatchViewSet(viewsets.ModelViewSet):
    queryset = ProductBatch.objects.select_related('product__farmer__user').prefetch_related('events').all()
    serializer_class = ProductBatchSerializer
    permission_classes = [IsFarmerOwnerOrAdmin]

    def get_queryset(self):
        qs = super().get_queryset().order_by('-created_at')
        farmer = get_farmer_profile(self.request.user)
        if self.request.method in permissions.SAFE_METHODS:
            if self.request.user.is_authenticated and self.request.user.is_staff:
                pass
            elif self.request.query_params.get('mine') == '1' and farmer:
                qs = qs.filter(product__farmer=farmer)
            else:
                qs = qs.filter(product__status='approved')
        elif self.request.user.is_staff:
            pass
        elif farmer:
            qs = qs.filter(product__farmer=farmer)
        else:
            return ProductBatch.objects.none()
        product_id = self.request.query_params.get('product')
        if product_id:
            qs = qs.filter(product_id=product_id)
        return qs

    def perform_create(self, serializer):
        product = serializer.validated_data['product']
        farmer = get_farmer_profile(self.request.user)
        if not self.request.user.is_staff and product.farmer != farmer:
            raise PermissionDenied('只能为自己的产品创建批次')
        serializer.save()


# ===== 数据统计与可视化 =====

@extend_schema(responses=OpenApiTypes.OBJECT)
@api_view(['GET'])
def dashboard_stats(request):
    """数据驾驶舱 — 根据角色返回不同数据"""
    is_staff = request.user.is_authenticated and request.user.is_staff
    product_scope = Product.objects.all() if is_staff else Product.objects.filter(status='approved')

    # 基础数据（所有人可见）
    total_products = product_scope.count()
    total_farmers = FarmerProfile.objects.count()
    total_orders = Order.objects.filter(status='delivered').count()

    # 月销量趋势
    monthly_sales = (
        Order.objects.filter(status='delivered')
        .annotate(month=TruncMonth('created_at'))
        .values('month')
        .annotate(total=Sum('total_amount'), count=Count('id'))
        .order_by('month')
    )

    # 产品分类分布
    category_dist = (
        product_scope.values('category')
        .annotate(count=Count('id'))
        .order_by('-count')
    )

    result = {
        'total_products': total_products,
        'total_farmers': total_farmers,
        'total_orders': total_orders,
        'monthly_sales': [
            {'month': s['month'].strftime('%Y-%m') if s['month'] else '未知', 'total': float(s['total'] or 0), 'count': s['count']}
            for s in monthly_sales
        ],
        'category_distribution': [
            {'category': c['category'] or '未分类', 'count': c['count']}
            for c in category_dist
        ],
    }

    # 管理员专属数据
    if is_staff:
        order_status = (
            Order.objects.values('status')
            .annotate(count=Count('id'))
        )
        recent_orders = OrderSerializer(
            Order.objects.prefetch_related('items').order_by('-created_at')[:10],
            many=True
        ).data
        result['order_status'] = {s['status']: s['count'] for s in order_status}
        result['recent_orders'] = recent_orders

    return Response(result)


# ===== 产品评价 =====

@api_view(['GET', 'POST'])
def product_reviews(request, pk):
    """获取或创建产品评价

    GET: 返回该产品的所有评价
    POST: 创建评价（仅限购买过该产品的用户，可选填写评论）
    """
    product = get_object_or_404(Product, pk=pk)

    if request.method == 'GET':
        reviews = Review.objects.filter(
            order__items__product_batch__product=product
        ).select_related('buyer', 'order').prefetch_related(
            'order__items__product_batch__product'
        ).distinct().order_by('-created_at')

        serializer = ReviewDetailSerializer(reviews, many=True)
        return Response(serializer.data)

    if request.method == 'POST':
        if not request.user.is_authenticated:
            return Response({'detail': '请先登录'}, status=status.HTTP_401_UNAUTHORIZED)

        # 检查用户是否购买过该产品
        has_purchased = OrderItem.objects.filter(
            order__buyer=request.user,
            product_batch__product=product
        ).exclude(order__status='cancelled').exists()

        if not has_purchased:
            return Response({'detail': '只有购买过该产品的用户才能评价'},
                          status=status.HTTP_403_FORBIDDEN)

        # 查找用户购买该产品的订单
        order = Order.objects.filter(
            buyer=request.user,
            items__product_batch__product=product
        ).exclude(status='cancelled').distinct().first()

        if not order:
            return Response({'detail': '未找到有效订单'}, status=status.HTTP_400_BAD_REQUEST)

        # 检查是否已评价过该订单
        existing = Review.objects.filter(order=order, buyer=request.user).first()
        if existing:
            return Response({'detail': '您已对该订单进行过评价'},
                          status=status.HTTP_409_CONFLICT)

        serializer = ReviewSerializer(data=request.data)
        if serializer.is_valid():
            serializer.save(order=order, buyer=request.user, farmer=product.farmer)
            return Response(serializer.data, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


# ===== 时令推荐 =====

@api_view(['GET'])
def seasonal_products_api(request):
    """API: 返回当季产品"""
    from datetime import date, timedelta
    current_month = timezone.now().month

    # 月份对应时令类别
    season_map = {
        1: ['蔬菜', '干货'], 2: ['蔬菜', '干货'], 3: ['蔬菜', '茶叶'],
        4: ['水果', '茶叶'], 5: ['水果', '茶叶'], 6: ['水果', '蔬菜', '茶叶'],
        7: ['水果', '蔬菜'], 8: ['水果', '蔬菜'], 9: ['水果', '粮油'],
        10: ['水果', '粮油'], 11: ['粮油', '干货'], 12: ['干货', '畜禽'],
    }
    seasonal_categories = season_map.get(current_month, ['水果', '蔬菜'])

    # 查询有近期采收批次的产品
    six_months_ago = date.today() - timedelta(days=180)
    seasonal_batch_products = ProductBatch.objects.filter(
        status='approved',
        harvest_date__gte=six_months_ago,
    ).values_list('product_id', flat=True).distinct()

    products = list(Product.objects.filter(
        status='approved',
        id__in=seasonal_batch_products,
    ).select_related('farmer__user').order_by('-created_at')[:20])

    # 如果批次匹配不足，按分类补充
    if len(products) < 8:
        existing_ids = {p.id for p in products}
        cat_products = Product.objects.filter(
            status='approved',
            category__in=seasonal_categories,
        ).exclude(id__in=existing_ids).select_related('farmer__user').order_by('-created_at')[:8]
        products.extend(cat_products)

    month_names = ['', '一月', '二月', '三月', '四月', '五月', '六月',
                   '七月', '八月', '九月', '十月', '十一月', '十二月']

    return Response({
        'current_season': f'{month_names[current_month]}当季',
        'seasonal_categories': seasonal_categories,
        'products': ProductSerializer(products[:20], many=True, context={'request': request}).data,
    })


# ===== 前端页面 =====

def product_list_view(request):
    return render(request, 'products.html')

def map_view(request):
    """中国地图 — 各省产品分布"""
    return render(request, 'map.html')

def product_detail_view(request, pk):
    product = get_object_or_404(Product.objects.select_related('farmer__user'), pk=pk)
    has_purchased = False
    is_favorited = False
    if request.user.is_authenticated:
        has_purchased = OrderItem.objects.filter(
            order__buyer=request.user,
            product_batch__product=product
        ).exclude(order__status='cancelled').exists()
        is_favorited = Favorite.objects.filter(user=request.user, product=product).exists()
    return render(request, 'product_detail.html', {
        'product': product,
        'has_purchased': has_purchased,
        'is_favorited': is_favorited,
    })

def product_batches_view(request, pk):
    """产品批次列表页"""
    product = get_object_or_404(Product.objects.select_related('farmer__user'), pk=pk)
    batches = ProductBatch.objects.filter(product=product).order_by('-created_at')
    for batch in batches:
        batch.ensure_qr_code()
    return render(request, 'product_batches.html', {'product': product, 'batches': batches})


# ===== 农户端功能 =====

def farmer_required(view_func):
    """装饰器：检查用户是否为农户且已通过审核"""
    @wraps(view_func)
    def wrapper(request, *args, **kwargs):
        if not request.user.is_authenticated:
            return redirect('accounts:login')
        try:
            request.farmer_profile = request.user.farmerprofile
        except FarmerProfile.DoesNotExist:
            messages.error(request, '请先注册为农户并提交入驻申请')
            return redirect('core:apply_join')
        if not request.farmer_profile.verified:
            from core.models import JoinApplication
            app = JoinApplication.objects.filter(user=request.user, status='pending').first()
            if app:
                messages.warning(request, '您的入驻申请正在审核中，审核通过后即可使用农户功能。')
            else:
                messages.warning(request, '请先提交入驻申请，上传相关证件材料。')
            return redirect('core:apply_join')
        return view_func(request, *args, **kwargs)
    return wrapper


@farmer_required
def farmer_dashboard(request):
    """农户工作台 — 增强版：含供需匹配+农技推荐"""
    profile = request.farmer_profile
    products = Product.objects.filter(farmer=profile).order_by('-created_at')
    batches = ProductBatch.objects.filter(product__farmer=profile)
    stats = {
        'total': products.count(),
        'approved': products.filter(status='approved').count(),
        'pending': products.filter(status='pending').count(),
        'draft': products.filter(status='draft').count(),
        'batches_total': batches.count(),
        'batches_approved': batches.filter(status='approved').count(),
        'batches_pending': batches.filter(status='pending').count(),
    }

    # 匹配的供需需求帖
    farmer_categories = products.filter(status='approved').values_list('category', flat=True).distinct()
    matching_demands = SupplyDemandPost.objects.filter(
        post_type='demand', status='active',
        category__in=farmer_categories,
    ).select_related('author').order_by('-created_at')[:5] if farmer_categories else []

    # 相关农技指南
    crop_map = {
        '水稻': 'rice', '小麦': 'wheat', '玉米': 'corn',
        '水果': 'fruit', '蔬菜': 'vegetable', '茶叶': 'tea',
        '中药材': 'herb', '畜禽': 'livestock', '水产': 'aquatic',
    }
    matched_crops = set()
    for cat in farmer_categories:
        crop_key = crop_map.get(cat)
        if crop_key:
            matched_crops.add(crop_key)
    relevant_guides = FarmingGuide.objects.filter(
        is_published=True, crop_type__in=matched_crops
    ).order_by('-created_at')[:4] if matched_crops else []

    return render(request, 'farmer/dashboard.html', {
        'products': products,
        'stats': stats,
        'matching_demands': matching_demands,
        'relevant_guides': relevant_guides,
    })


@farmer_required
def farmer_product_list(request):
    """农户产品管理页"""
    profile = request.farmer_profile
    products = Product.objects.filter(farmer=profile).order_by('-created_at')
    return render(request, 'farmer/product_list.html', {
        'products': products,
        'total': products.count(),
        'approved': products.filter(status='approved').count(),
        'pending': products.filter(status='pending').count(),
        'draft': products.filter(status='draft').count(),
    })


@farmer_required
def farmer_product_create(request):
    """农户管理产品"""
    profile = request.farmer_profile
    if request.method == 'POST':
        name = request.POST.get('name', '').strip()
        category = request.POST.get('category', '').strip()
        variety = request.POST.get('variety', '').strip()
        description = request.POST.get('description', '').strip()
        price = request.POST.get('price', '0')
        unit = request.POST.get('unit', 'kg')
        wholesale_price = request.POST.get('wholesale_price', '').strip()
        wholesale_min_qty = int(request.POST.get('wholesale_min_quantity', '0') or '0')
        try:
            price_value = Decimal(price)
            wholesale_value = Decimal(wholesale_price) if wholesale_price else None
        except (InvalidOperation, TypeError):
            price_value = Decimal('0')
            wholesale_value = None
        if not name:
            messages.error(request, '请输入产品名称')
        elif price_value <= 0:
            messages.error(request, '请输入有效的价格')
        elif wholesale_value is not None and wholesale_value <= 0:
            messages.error(request, '批发价必须大于0')
        elif wholesale_value is not None and wholesale_value >= price_value:
            messages.error(request, '批发价应低于零售价，才能吸引批发客户')
        else:
            product = Product.objects.create(
                farmer=profile, name=name, category=category,
                variety=variety, description=description,
                price=price_value, unit=unit,
                wholesale_price=wholesale_value,
                wholesale_min_quantity=wholesale_min_qty if wholesale_value else 10,
                status='pending'
            )
            if request.FILES.get('image'):
                product.image = request.FILES['image']
                product.save()
            messages.success(request, f'「{name}」已提交审核')
            return redirect('products:farmer_product_list')
    categories = list(Product.objects.exclude(category='').values_list('category', flat=True).distinct().order_by('category'))
    varieties = list(Product.objects.exclude(variety='').values_list('variety', flat=True).distinct().order_by('variety'))
    return render(request, 'farmer/product_form.html', {
        'action': '添加', 'categories': categories, 'varieties': varieties
    })


@farmer_required
def farmer_product_edit(request, pk):
    """农户编辑产品 — 所有状态均可编辑"""
    profile = request.farmer_profile
    product = get_object_or_404(Product, pk=pk, farmer=profile)
    is_approved = product.status == 'approved'
    if request.method == 'POST':
        price = request.POST.get('price', product.price)
        wholesale_price = request.POST.get('wholesale_price', '').strip()
        wholesale_min_qty = int(request.POST.get('wholesale_min_quantity', '0') or '0')
        try:
            price_value = Decimal(price)
            wholesale_value = Decimal(wholesale_price) if wholesale_price else None
        except (InvalidOperation, TypeError):
            messages.error(request, '请输入有效的价格')
            categories = list(Product.objects.exclude(category='').values_list('category', flat=True).distinct().order_by('category'))
            varieties = list(Product.objects.exclude(variety='').values_list('variety', flat=True).distinct().order_by('variety'))
            return render(request, 'farmer/product_form.html', {'product': product, 'action': '编辑', 'categories': categories, 'varieties': varieties})
        if price_value <= 0:
            messages.error(request, '请输入有效的价格')
            categories = list(Product.objects.exclude(category='').values_list('category', flat=True).distinct().order_by('category'))
            varieties = list(Product.objects.exclude(variety='').values_list('variety', flat=True).distinct().order_by('variety'))
            return render(request, 'farmer/product_form.html', {'product': product, 'action': '编辑', 'categories': categories, 'varieties': varieties})
        if wholesale_value is not None and wholesale_value <= 0:
            messages.error(request, '批发价必须大于0')
            categories = list(Product.objects.exclude(category='').values_list('category', flat=True).distinct().order_by('category'))
            varieties = list(Product.objects.exclude(variety='').values_list('variety', flat=True).distinct().order_by('variety'))
            return render(request, 'farmer/product_form.html', {'product': product, 'action': '编辑', 'categories': categories, 'varieties': varieties})
        if wholesale_value is not None and wholesale_value >= price_value:
            messages.error(request, '批发价应低于零售价，才能吸引批发客户')
            categories = list(Product.objects.exclude(category='').values_list('category', flat=True).distinct().order_by('category'))
            varieties = list(Product.objects.exclude(variety='').values_list('variety', flat=True).distinct().order_by('variety'))
            return render(request, 'farmer/product_form.html', {'product': product, 'action': '编辑', 'categories': categories, 'varieties': varieties})
        product.name = request.POST.get('name', product.name)
        product.category = request.POST.get('category', '')
        product.variety = request.POST.get('variety', '')
        product.description = request.POST.get('description', '')
        product.price = price_value
        product.unit = request.POST.get('unit', 'kg')
        product.wholesale_price = wholesale_value
        product.wholesale_min_quantity = wholesale_min_qty if wholesale_value else 10
        if request.FILES.get('image'):
            product.image = request.FILES['image']
        if request.POST.get('submit') == 'submit':
            # 已通过的产品修改后需重新审核
            if product.status == 'approved':
                product.status = 'pending'
                product.review_note = ''
                messages.success(request, f'「{product.name}」已提交修改，等待管理员重新审核')
            elif product.status == 'pending':
                messages.success(request, f'「{product.name}」已更新（审核中）')
            else:
                product.status = 'pending'
                product.review_note = ''
                messages.success(request, f'「{product.name}」已重新提交审核')
        else:
            messages.success(request, '「{product.name}」已保存')
        product.save()
        return redirect('products:farmer_product_list')
    categories = list(Product.objects.exclude(category='').values_list('category', flat=True).distinct().order_by('category'))
    varieties = list(Product.objects.exclude(variety='').values_list('variety', flat=True).distinct().order_by('variety'))
    return render(request, 'farmer/product_form.html', {
        'product': product, 'action': '编辑', 'categories': categories, 'varieties': varieties
    })


@farmer_required
def farmer_product_delete(request, pk):
    """农户下架/删除产品"""
    if request.method != 'POST':
        messages.error(request, '请通过页面按钮删除产品')
        return redirect('products:farmer_product_list')
    profile = request.farmer_profile
    product = get_object_or_404(Product, pk=pk, farmer=profile)
    product.delete()
    messages.success(request, f'「{product.name}」已删除')
    return redirect('products:farmer_product_list')


@farmer_required
def farmer_product_submit(request, pk):
    """农户提交审核"""
    if request.method != 'POST':
        messages.error(request, '请通过页面按钮提交审核')
        return redirect('products:farmer_product_list')
    profile = request.farmer_profile
    product = get_object_or_404(Product, pk=pk, farmer=profile)
    if product.status == 'draft':
        product.status = 'pending'
        product.save()
        messages.success(request, f'「{product.name}」已提交审核')
    return redirect('products:farmer_product_list')


# ===== 农户批次管理 =====

@farmer_required
def farmer_batch_list(request):
    """农户查看所有批次"""
    profile = request.farmer_profile
    batches = ProductBatch.objects.filter(
        product__farmer=profile
    ).select_related('product').order_by('-created_at')
    return render(request, 'farmer/batches.html', {'batches': batches})


@farmer_required
def farmer_batch_create(request):
    """农户创建新批次（含质检上传）"""
    profile = request.farmer_profile
    products = Product.objects.filter(farmer=profile, status='approved')

    if request.method == 'POST':
        product_id = request.POST.get('product_id')
        harvest_date = request.POST.get('harvest_date', '')
        quantity = request.POST.get('quantity', '0')
        qc_report = request.POST.get('qc_report', '').strip()
        location = request.POST.get('location', '').strip()

        product = get_object_or_404(Product, pk=product_id, farmer=profile)
        try:
            qty = int(quantity)
        except (TypeError, ValueError):
            messages.error(request, '请输入有效数量')
            return render(request, 'farmer/batch_form.html', {'products': products})

        if qty <= 0:
            messages.error(request, '数量必须大于0')
            return render(request, 'farmer/batch_form.html', {'products': products})

        batch = ProductBatch.objects.create(
            product=product,
            harvest_date=harvest_date or None,
            quantity=qty,
            qc_report=qc_report,
            trace_info={'location': location, 'farmer': profile.user.username},
            status='pending',
        )

        # 上传质检图片（多图）
        qc_files = request.FILES.getlist('qc_images')
        if qc_files:
            import uuid, os
            from django.core.files.storage import default_storage
            urls = []
            for f in qc_files:
                safe_name = f'{uuid.uuid4().hex}_{f.name}'
                path = default_storage.save(f'qc/{safe_name}', f)
                urls.append(path)
            batch.qc_images = urls
            batch.save(update_fields=['qc_images'])

        # 自动创建溯源事件
        TraceEvent.objects.create(
            batch=batch,
            event_type='qc',
            title='质检报告提交',
            description=qc_report or '已提交质检资料，等待审核',
            operator=request.user,
            occurred_at=timezone.now(),
            location=location,
        )

        messages.success(request, f'批次已创建，等待管理员审核通过后将生成溯源编码和二维码')
        return redirect('products:farmer_batch_list')

    return render(request, 'farmer/batch_form.html', {'products': products})


@farmer_required
def farmer_batch_delete(request, pk):
    """农户删除批次 — 仅允许待审核/草稿/未通过的批次"""
    profile = request.farmer_profile
    batch = get_object_or_404(ProductBatch, pk=pk, product__farmer=profile)
    if batch.status == 'approved':
        messages.error(request, '已通过的批次不能删除，请联系管理员处理')
        return redirect('products:farmer_batch_list')
    if request.method == 'POST':
        batch_name = batch.batch_code or f'#{batch.pk}'
        batch.delete()
        messages.success(request, f'批次 {batch_name} 已删除')
    return redirect('products:farmer_batch_list')


@farmer_required
def farmer_batch_detail(request, pk):
    """批次详情：查看二维码、溯源事件"""
    profile = request.farmer_profile
    batch = get_object_or_404(ProductBatch, pk=pk, product__farmer=profile)
    events = batch.events.all().order_by('occurred_at')
    return render(request, 'farmer/batch_detail.html', {
        'batch': batch,
        'events': events,
    })


def download_qr(request, pk):
    """下载二维码图片"""
    batch = get_object_or_404(ProductBatch, pk=pk)
    if not batch.qr_code:
        batch.ensure_qr_code()
    from django.http import FileResponse
    return FileResponse(batch.qr_code.open('rb'), as_attachment=True,
                        filename=f'{batch.batch_code}_qrcode.png')


# ===== 农户名录 =====

# ===== 农户名录 =====

def farmer_directory(request):
    """入驻农户名录"""
    from accounts.models import FarmerProfile as FP
    farmers = FP.objects.annotate(
        product_count=Count('products', filter=Q(products__status='approved')),
    ).select_related('user').order_by('-product_count')

    return render(request, 'farmer_directory.html', {
        'farmers': farmers,
        'total': farmers.count(),
    })
