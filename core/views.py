from rest_framework import viewsets, permissions, status
from rest_framework.decorators import action, api_view, permission_classes
from rest_framework.exceptions import PermissionDenied
from rest_framework.response import Response
from drf_spectacular.utils import extend_schema
from drf_spectacular.types import OpenApiTypes
from django.shortcuts import get_object_or_404, render, redirect, reverse
from django.contrib.auth import login, logout, authenticate
from django.contrib.auth.decorators import login_required
from django.contrib.auth.models import User
from django.contrib.auth.forms import UserCreationForm, AuthenticationForm
from django.contrib import messages
from django.db import transaction
from django.db.models import Count, Sum, Q, F, DecimalField, ExpressionWrapper
from django.utils import timezone
from django.db.models.functions import TruncMonth
from decimal import Decimal, InvalidOperation
from functools import wraps
from .models import Product, ProductBatch, Order, OrderItem, SubsidyApplication, Training, FarmerProfile, Cooperative, Review, TraceEvent, Announcement, Cart, CartItem, Favorite
from .permissions import IsAdminOrReadOnly, IsFarmerOwnerOrAdmin, IsOrderParticipantOrAdmin, IsSubsidyOwnerOrAdmin, get_farmer_profile
from .serializers import (
    ProductSerializer, ProductBatchSerializer, OrderSerializer,
    SubsidyApplicationSerializer, TrainingSerializer,
    ReviewSerializer, ReviewDetailSerializer,
)
from .llm_service import generate_analysis

class ProductViewSet(viewsets.ModelViewSet):
    queryset = Product.objects.select_related('farmer__user', 'farmer__cooperative').prefetch_related('batches').all()
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
@api_view(['GET', 'POST'])
def product_reviews(request, pk):
    """获取/提交产品评价"""
    product = get_object_or_404(Product, pk=pk)

    if request.method == 'GET':
        reviews = Review.objects.filter(product=product).select_related('buyer').order_by('-created_at')[:20]
        return Response([{
            'id': r.id,
            'buyer': r.buyer.username,
            'rating': r.rating,
            'comment': r.comment,
            'created_at': r.created_at.strftime('%Y-%m-%d'),
        } for r in reviews])

    # POST — 提交评价
    if not request.user.is_authenticated:
        return Response({'detail': '请先登录'}, status=401)

    try:
        rating = int(request.data.get('rating'))
    except (TypeError, ValueError):
        return Response({'detail': '评分需为1-5的整数'}, status=400)
    comment = str(request.data.get('comment', '')).strip()[:500]
    if rating < 1 or rating > 5:
        return Response({'detail': '评分需为1-5的整数'}, status=400)

    # 找用户的已完成订单中是否包含该产品
    has_purchased = OrderItem.objects.filter(
        order__buyer=request.user,
        order__status='delivered',
        product_batch__product=product,
    ).exists()
    if not has_purchased:
        return Response({'detail': '您尚未购买该产品，无法评价'}, status=403)

    # 检查是否已评过
    if Review.objects.filter(buyer=request.user, product=product).exists():
        return Response({'detail': '您已评价过该产品'}, status=400)

    # 找到这笔订单
    order_item = OrderItem.objects.filter(
        order__buyer=request.user,
        order__status='delivered',
        product_batch__product=product,
    ).select_related('order').latest('order__updated_at')
    order = order_item.order

    review = Review.objects.create(
        order=order,
        buyer=request.user,
        farmer=product.farmer,
        product=product,
        rating=rating,
        comment=comment,
    )
    return Response({
        'id': review.id,
        'buyer': review.buyer.username,
        'rating': review.rating,
        'comment': review.comment,
        'created_at': review.created_at.strftime('%Y-%m-%d'),
    }, status=201)


@extend_schema(responses=OpenApiTypes.OBJECT)
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

class SubsidyViewSet(viewsets.ModelViewSet):
    queryset = SubsidyApplication.objects.all()
    serializer_class = SubsidyApplicationSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        qs = super().get_queryset().order_by('-submitted_at')
        if self.request.user.is_staff:
            return qs
        farmer = get_farmer_profile(self.request.user)
        if farmer:
            return qs.filter(farmer=farmer)
        return SubsidyApplication.objects.none()

    def get_permissions(self):
        if self.action in ('retrieve', 'update', 'partial_update', 'destroy'):
            return [permissions.IsAuthenticated(), IsSubsidyOwnerOrAdmin()]
        return super().get_permissions()

    def perform_create(self, serializer):
        farmer = get_farmer_profile(self.request.user)
        if not farmer:
            raise PermissionDenied('只有农户可以申请补贴')
        serializer.save(farmer=farmer)

class TrainingViewSet(viewsets.ModelViewSet):
    queryset = Training.objects.all()
    serializer_class = TrainingSerializer
    permission_classes = [IsAdminOrReadOnly]

# 溯源页面
def trace_view(request, batch_code):
    batch = get_object_or_404(
        ProductBatch.objects.select_related('product__farmer__user').prefetch_related('events'),
        batch_code=batch_code,
    )
    batch.ensure_qr_code()
    return render(request, 'trace.html', {'batch': batch, 'events': batch.events.all()})


# ===== 前端页面 =====
def home_view(request):
    announcements = Announcement.objects.filter(is_active=True)[:5]
    return render(request, 'index.html', {'announcements': announcements})

def product_list_view(request):
    return render(request, 'products.html')

def map_view(request):
    """中国地图 — 各省产品分布"""
    return render(request, 'map.html')

def product_detail_view(request, pk):
    product = get_object_or_404(Product.objects.select_related('farmer__user', 'farmer__cooperative'), pk=pk)
    return render(request, 'product_detail.html', {'product': product})


def product_batches_view(request, pk):
    """产品批次列表页"""
    product = get_object_or_404(Product.objects.select_related('farmer__user'), pk=pk)
    batches = ProductBatch.objects.filter(product=product).order_by('-created_at')
    for batch in batches:
        batch.ensure_qr_code()
    return render(request, 'product_batches.html', {'product': product, 'batches': batches})

def trace_query_view(request):
    """溯源查询页面 - 手动输入批次号"""
    batch = None
    code = request.GET.get('code', '')
    if code:
        try:
            batch = ProductBatch.objects.select_related('product').get(batch_code=code)
            return redirect('trace', batch_code=code)
        except ProductBatch.DoesNotExist:
            messages.error(request, f'未找到批次编号：{code}')
    return render(request, 'trace_query.html')

def login_view(request):
    if request.user.is_authenticated:
        return redirect('/')
    if request.method == 'POST':
        form = AuthenticationForm(request, data=request.POST)
        if form.is_valid():
            user = form.get_user()
            login(request, user)
            messages.success(request, f'欢迎回来，{user.username}！')
            next_url = request.GET.get('next', '')
            if next_url:
                return redirect(next_url)
            # 根据角色跳转
            if user.is_staff:
                return redirect('admin_dashboard')
            try:
                user.farmerprofile
                return redirect('farmer_dashboard')
            except FarmerProfile.DoesNotExist:
                return redirect('product_list')
    else:
        form = AuthenticationForm()
    return render(request, 'login.html', {'form': form})

def logout_view(request):
    logout(request)
    messages.success(request, '已成功退出登录')
    return redirect('/')

def register_view(request):
    if request.user.is_authenticated:
        return redirect('/')
    if request.method == 'POST':
        form = UserCreationForm(request.POST)
        role = request.POST.get('role', 'consumer')
        if form.is_valid():
            user = form.save()
            # 如果选择农户身份，自动创建农户档案
            if role == 'farmer':
                FarmerProfile.objects.create(user=user, phone='', address='')
            login(request, user)
            messages.success(request, f'注册成功，欢迎 {user.username}！')
            if role == 'farmer':
                return redirect('farmer_dashboard')
            return redirect('product_list')
    else:
        form = UserCreationForm()
    return render(request, 'register.html', {'form': form})


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
        total_coops = Cooperative.objects.count()
        order_status = (
            Order.objects.values('status')
            .annotate(count=Count('id'))
        )
        recent_orders = OrderSerializer(
            Order.objects.prefetch_related('items').order_by('-created_at')[:10],
            many=True
        ).data
        result['total_coops'] = total_coops
        result['order_status'] = {s['status']: s['count'] for s in order_status}
        result['recent_orders'] = recent_orders

    return Response(result)


def dashboard_view(request):
    """数据驾驶舱页面"""
    return render(request, 'dashboard.html')


# ===== 中国地图 — 各省产品分布 =====

# 34个省级行政区（按长度降序排列，确保匹配短别名时不误匹配）
CHINA_PROVINCES = [
    '黑龙江省', '内蒙古自治区', '新疆维吾尔自治区', '西藏自治区', '广西壮族自治区',
    '宁夏回族自治区', '香港特别行政区', '澳门特别行政区',
    '北京市', '天津市', '上海市', '重庆市',
    '河北省', '山西省', '辽宁省', '吉林省',
    '江苏省', '浙江省', '安徽省', '福建省', '江西省', '山东省',
    '河南省', '湖北省', '湖南省', '广东省', '海南省',
    '四川省', '贵州省', '云南省', '陕西省', '甘肃省', '青海省', '台湾省',
]


# ===== 产品评价 =====

@api_view(['GET', 'POST'])
def product_reviews(request, product_id):
    """获取或创建产品评价

    GET: 返回该产品的所有评价
    POST: 创建评价（仅限购买过该产品的用户，可选填写评论）
    """
    product = get_object_or_404(Product, pk=product_id)

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


# ===== 智能供需分析 =====

@extend_schema(responses=OpenApiTypes.OBJECT)
@api_view(['GET'])
@permission_classes([permissions.IsAuthenticated])
def demand_analysis(request):
    """需求分析 API — 分析产品卖往哪些地区、什么产品需求大"""
    sales_value = ExpressionWrapper(
        F('price') * F('quantity'),
        output_field=DecimalField(max_digits=12, decimal_places=2),
    )
    valid_items = OrderItem.objects.exclude(order__status='cancelled')

    # 1. 各产品需求排行（排除已取消订单，统计所有有效需求）
    product_demand = (
        valid_items
        .values('product_batch__product__name')
        .annotate(
            total_qty=Sum('quantity'),
            total_revenue=Sum(sales_value)
        )
        .order_by('-total_qty')
    )
    regional_demand = product_demand[:10]

    # 2. 各产品供需情况（遍历所有有批次的产品，含销量为0的）
    available_map = dict(
        ProductBatch.objects.values('product__name')
        .annotate(total=Sum('quantity'))
        .values_list('product__name', 'total')
    )
    sold_map = {
        item['product_batch__product__name']: item['total_qty'] or 0
        for item in product_demand
    }
    all_product_names = set(list(available_map.keys()) + list(sold_map.keys()))
    product_supply_demand = []
    for pname in all_product_names:
        sold = sold_map.get(pname, 0)
        available = available_map.get(pname, 0) or 0
        product_supply_demand.append({
            'product': pname,
            'sold': sold,
            'available': available,
            'gap': available - sold if available > sold else 0,
            'shortage': sold - available if sold > available else 0,
        })
    product_supply_demand.sort(key=lambda x: x['sold'], reverse=True)

    # 3. 地区分布只展示粗粒度省份，避免暴露完整收货地址
    region_map = {}
    valid_orders = (
        Order.objects
        .exclude(status='cancelled')
        .values('address', 'total_amount')
    )
    for order in valid_orders:
        region = extract_province(order['address']) or '其他'
        if region not in region_map:
            region_map[region] = {'region': region, 'orders': 0, 'total': Decimal('0')}
        region_map[region]['orders'] += 1
        region_map[region]['total'] += order['total_amount'] or Decimal('0')
    region_stats = sorted(region_map.values(), key=lambda x: x['orders'], reverse=True)[:8]

    # 4. AI 分析简报（优先调本地 Ollama 大模型，不可用时回退规则引擎）
    llm_input = {
        'product_supply_demand': product_supply_demand,
        'regional_demand_top': [
            {'product': r['product_batch__product__name'], 'sold': r['total_qty'], 'revenue': float(r['total_revenue'] or 0)}
            for r in regional_demand
        ],
        'region_stats': [
            {'region': r['region'], 'orders': r['orders'], 'total': float(r['total'] or 0)}
            for r in region_stats
        ],
    }

    analysis_result = generate_analysis(llm_input)

    return Response({
        'product_supply_demand': product_supply_demand,
        'regional_demand_top': llm_input['regional_demand_top'],
        'analysis_summary': analysis_result,
    })


# ===== 消费者下单 =====

def order_create_view(request):
    """消费者下单页面"""
    if not request.user.is_authenticated:
        return redirect(f"{reverse('login')}?next={request.path}")
    # 农户不能给自己下单
    try:
        request.user.farmerprofile
        messages.warning(request, '农户账号无法下单')
        return redirect('farmer_dashboard')
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
        except (InvalidOperation, ValueError):
            return render(request, 'order_create.html', {'product': product, 'error': '订单金额计算失败'})
        messages.success(request, f'下单成功！订单编号 #{order.id}')
        return redirect('product_detail', pk=product.id)

    return render(request, 'order_create.html', {'product': product})


def market_analysis_view(request):
    """市场分析页面 — 需登录"""
    if not request.user.is_authenticated:
        messages.info(request, '请先登录或注册后查看市场分析')
        return redirect(f"{reverse('login')}?next={request.path}")
    return render(request, 'market_analysis.html')


def consumer_orders_view(request):
    """消费者订单列表"""
    if not request.user.is_authenticated:
        return redirect(f"{reverse('login')}?next={request.path}")
    orders = Order.objects.filter(buyer=request.user).prefetch_related('items__product_batch__product').order_by('-created_at')
    return render(request, 'consumer_orders.html', {'orders': orders})




# ===== 农户端功能 =====

def farmer_required(view_func):
    """装饰器：检查用户是否为农户"""
    @wraps(view_func)
    def wrapper(request, *args, **kwargs):
        if not request.user.is_authenticated:
            return redirect('login')
        try:
            request.farmer_profile = request.user.farmerprofile
        except FarmerProfile.DoesNotExist:
            messages.error(request, '请先注册为农户')
            return redirect('register')
        return view_func(request, *args, **kwargs)
    return wrapper




@farmer_required
def farmer_orders_view(request):
    """农户查看自己产品的订单"""
    profile = request.farmer_profile
    orders = Order.objects.filter(
        items__product_batch__product__farmer=profile
    ).prefetch_related('items__product_batch__product', 'buyer').distinct().order_by('-created_at')
    return render(request, 'farmer/orders.html', {'orders': orders})


@farmer_required
def farmer_dashboard(request):
    """农户工作台"""
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
    return render(request, 'farmer/dashboard.html', {'products': products, 'stats': stats})


def farmer_products(request):
    """农户产品管理"""
    return redirect('farmer_dashboard')


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
        try:
            price_value = Decimal(price)
        except (InvalidOperation, TypeError):
            price_value = Decimal('0')
        if not name:
            messages.error(request, '请输入产品名称')
        elif price_value <= 0:
            messages.error(request, '请输入有效的价格')
        else:
            product = Product.objects.create(
                farmer=profile, name=name, category=category,
                variety=variety, description=description,
                price=price_value, unit=unit, status='pending'
            )
            if request.FILES.get('image'):
                product.image = request.FILES['image']
                product.save()
            messages.success(request, f'「{name}」已提交审核')
            return redirect('farmer_products')
    return render(request, 'farmer/product_form.html', {'action': '添加'})


@farmer_required
def farmer_product_edit(request, pk):
    """农户编辑产品"""
    profile = request.farmer_profile
    product = get_object_or_404(Product, pk=pk, farmer=profile)
    if product.status not in ('draft', 'rejected'):
        messages.warning(request, '只能编辑草稿或未通过审核的产品')
        return redirect('farmer_products')
    if request.method == 'POST':
        price = request.POST.get('price', product.price)
        try:
            price_value = Decimal(price)
        except (InvalidOperation, TypeError):
            messages.error(request, '请输入有效的价格')
            return render(request, 'farmer/product_form.html', {'product': product, 'action': '编辑'})
        if price_value <= 0:
            messages.error(request, '请输入有效的价格')
            return render(request, 'farmer/product_form.html', {'product': product, 'action': '编辑'})
        product.name = request.POST.get('name', product.name)
        product.category = request.POST.get('category', '')
        product.variety = request.POST.get('variety', '')
        product.description = request.POST.get('description', '')
        product.price = price_value
        product.unit = request.POST.get('unit', 'kg')
        if request.FILES.get('image'):
            product.image = request.FILES['image']
        if request.POST.get('submit') == 'submit':
            product.status = 'pending'
            product.review_note = ''
            messages.success(request, f'「{product.name}」已重新提交审核')
        else:
            messages.success(request, '草稿已保存')
        product.save()
        return redirect('farmer_products')
    return render(request, 'farmer/product_form.html', {'product': product, 'action': '编辑'})


@farmer_required
def farmer_product_delete(request, pk):
    """农户下架/删除产品"""
    if request.method != 'POST':
        messages.error(request, '请通过页面按钮删除产品')
        return redirect('farmer_products')
    profile = request.farmer_profile
    product = get_object_or_404(Product, pk=pk, farmer=profile)
    product.delete()
    messages.success(request, f'「{product.name}」已删除')
    return redirect('farmer_products')


@farmer_required
def farmer_product_submit(request, pk):
    """农户提交审核"""
    if request.method != 'POST':
        messages.error(request, '请通过页面按钮提交审核')
        return redirect('farmer_products')
    profile = request.farmer_profile
    product = get_object_or_404(Product, pk=pk, farmer=profile)
    if product.status == 'draft':
        product.status = 'pending'
        product.save()
        messages.success(request, f'「{product.name}」已提交审核')
    return redirect('farmer_products')


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

        messages.success(request, f'批次 {batch.batch_code} 已创建，等待审核')
        return redirect('farmer_batch_list')

    return render(request, 'farmer/batch_form.html', {'products': products})


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


# ===== 农户店铺 =====

def farmer_shop_view(request, farmer_id):
    """农户公开店铺页"""
    profile = get_object_or_404(FarmerProfile, pk=farmer_id)
    products = Product.objects.filter(farmer=profile, status='approved').order_by('-created_at')
    batches = ProductBatch.objects.filter(
        product__farmer=profile, status='approved'
    ).select_related('product').order_by('-created_at')[:10]
    return render(request, 'farmer/shop.html', {
        'farmer': profile,
        'products': products,
        'batches': batches,
    })


# ===== 订单物流 =====

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
            messages.success(request, '发货成功')
        return redirect('farmer_orders')
    return render(request, 'farmer/tracking_form.html', {'order': order})


# ===== 管理端 CSV 导出 =====

def admin_required(view_func):
    """装饰器：检查管理员"""
    @wraps(view_func)
    def wrapper(request, *args, **kwargs):
        if not request.user.is_authenticated or not request.user.is_staff:
            messages.error(request, '需要管理员权限')
            return redirect('home')
        return view_func(request, *args, **kwargs)
    return wrapper


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


# ===== 管理端功能 =====

def admin_required(view_func):
    """装饰器：检查是否为管理员"""
    @wraps(view_func)
    def wrapper(request, *args, **kwargs):
        if not request.user.is_authenticated or not request.user.is_staff:
            messages.error(request, '无权限')
            return redirect('/')
        return view_func(request, *args, **kwargs)
    return wrapper


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


@admin_required
def admin_products(request):
    """管理端 — 产品审核"""
    status_filter = request.GET.get('status', 'pending')
    products = Product.objects.select_related('farmer__user', 'farmer__cooperative').all()
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
        return redirect('admin_products')
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
        return redirect('admin_products')
    product.save(update_fields=['status', 'review_note'])
    return redirect('admin_products')


@admin_required
def admin_users(request):
    """管理端 — 用户管理"""
    users = User.objects.select_related('farmerprofile').all().order_by('-date_joined')
    return render(request, 'admin/users.html', {'users': users})


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
    return redirect('cart_view')


@login_required
def cart_checkout(request):
    """购物车结算"""
    cart = get_object_or_404(Cart, user=request.user)
    items = list(cart.items.select_related('product__farmer').all())
    if not items:
        messages.warning(request, '购物车为空')
        return redirect('cart_view')
    if request.method == 'POST':
        address = request.POST.get('address', '').strip()
        if not address:
            messages.error(request, '请输入收货地址')
            return render(request, 'cart_checkout.html', {'items': items, 'cart': cart})
        try:
            with transaction.atomic():
                total = sum(item.product.price * item.quantity for item in items)
                order = Order.objects.create(buyer=request.user, total_amount=total, address=address, status='confirmed')
                for item in items:
                    batch = ProductBatch.objects.filter(product=item.product, status='approved').first()
                    OrderItem.objects.create(order=order, product_batch=batch, quantity=item.quantity, price=item.product.price)
                cart.items.all().delete()
                messages.success(request, f'下单成功！订单编号 #{order.id}')
                return redirect('consumer_orders')
        except Exception as e:
            messages.error(request, f'下单失败：{str(e)}')
    return render(request, 'cart_checkout.html', {'items': items, 'cart': cart})


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


# ===== 批次审核 =====

@admin_required
def admin_batches(request):
    """批次审核列表"""
    status_filter = request.GET.get('status', 'pending')
    batches = ProductBatch.objects.select_related('product__farmer__user').all()
    if status_filter != 'all':
        batches = batches.filter(status=status_filter)
    batches = batches.order_by('-created_at')
    return render(request, 'admin/batches.html', {'batches': batches, 'current_status': status_filter})


@admin_required
def admin_batch_review(request, pk, action):
    """审核批次"""
    if request.method != 'POST':
        return redirect('admin_batches')
    batch = get_object_or_404(ProductBatch, pk=pk)
    if action == 'approve':
        batch.status = 'approved'
        TraceEvent.objects.create(batch=batch, event_type='qc', title='质检通过', operator=request.user, description='批次审核通过，准予上架')
        messages.success(request, f'批次 {batch.batch_code} 已通过')
    elif action == 'reject':
        batch.status = 'rejected'
        note = request.POST.get('note', '').strip()
        TraceEvent.objects.create(batch=batch, event_type='qc', title='质检未通过', operator=request.user, description=note or '未通过质检审核')
        messages.warning(request, f'批次 {batch.batch_code} 未通过')
    else:
        messages.error(request, '未知操作')
        return redirect('admin_batches')
    batch.save(update_fields=['status'])
    return redirect('admin_batches')


# ===== 农户店铺设置 =====

@farmer_required
def farmer_shop_settings(request):
    """编辑店铺信息"""
    profile = request.farmer_profile
    if request.method == 'POST':
        profile.shop_description = request.POST.get('shop_description', '').strip()
        profile.address = request.POST.get('address', '').strip()
        profile.phone = request.POST.get('phone', '').strip()
        if request.FILES.get('shop_avatar'):
            profile.shop_avatar = request.FILES['shop_avatar']
        profile.save()
        messages.success(request, '店铺信息已保存')
        return redirect('farmer_shop_settings')
    return render(request, 'farmer/shop_settings.html', {'profile': profile})
