from rest_framework import viewsets, permissions, status
from rest_framework.decorators import action, api_view
from rest_framework.response import Response
from django.shortcuts import get_object_or_404, render, redirect
from django.contrib.auth import login, logout, authenticate
from django.contrib.auth.forms import UserCreationForm, AuthenticationForm
from django.contrib import messages
from django.db.models import Count, Sum
from django.db.models.functions import TruncMonth
from .models import Product, ProductBatch, Order, OrderItem, SubsidyApplication, Training, FarmerProfile, Cooperative, Review
from .serializers import ProductSerializer, ProductBatchSerializer, OrderSerializer, SubsidyApplicationSerializer, TrainingSerializer

class ProductViewSet(viewsets.ModelViewSet):
    queryset = Product.objects.select_related('farmer').all()
    serializer_class = ProductSerializer
    permission_classes = [permissions.IsAuthenticatedOrReadOnly]

class ProductBatchViewSet(viewsets.ModelViewSet):
    queryset = ProductBatch.objects.select_related('product').all()
    serializer_class = ProductBatchSerializer

class OrderViewSet(viewsets.ModelViewSet):
    queryset = Order.objects.prefetch_related('items').all()
    serializer_class = OrderSerializer
    permission_classes = [permissions.IsAuthenticated]

    @action(detail=True, methods=['post'])
    def upload_payment(self, request, pk=None):
        order = self.get_object()
        proof = request.data.get('payment_proof')
        if not proof:
            return Response({'detail':'请上传付款凭证'}, status=status.HTTP_400_BAD_REQUEST)
        order.payment_proof = proof
        order.status = 'paid_offline'
        order.save()
        return Response({'detail':'已上传，等待后台确认'})

class SubsidyViewSet(viewsets.ModelViewSet):
    queryset = SubsidyApplication.objects.all()
    serializer_class = SubsidyApplicationSerializer
    permission_classes = [permissions.IsAuthenticated]

class TrainingViewSet(viewsets.ModelViewSet):
    queryset = Training.objects.all()
    serializer_class = TrainingSerializer

# 溯源页面
def trace_view(request, batch_code):
    batch = get_object_or_404(ProductBatch, batch_code=batch_code)
    return render(request, 'trace.html', {'batch': batch})

# ===== 前端页面 =====
def home_view(request):
    return render(request, 'index.html')

def product_list_view(request):
    return render(request, 'products.html')

def product_detail_view(request, pk):
    product = get_object_or_404(Product.objects.select_related('farmer__user', 'farmer__cooperative'), pk=pk)
    return render(request, 'product_detail.html', {'product': product})

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
            next_url = request.GET.get('next', '/')
            return redirect(next_url)
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
        if form.is_valid():
            user = form.save()
            login(request, user)
            messages.success(request, f'注册成功，欢迎 {user.username}！')
            return redirect('/')
    else:
        form = UserCreationForm()
    return render(request, 'register.html', {'form': form})


# ===== 数据统计与可视化 =====

@api_view(['GET'])
def dashboard_stats(request):
    """首页统计面板数据"""
    total_products = Product.objects.count()
    total_farmers = FarmerProfile.objects.count()
    total_orders = Order.objects.filter(status='delivered').count()
    total_coops = Cooperative.objects.count()

    # 月销量趋势（按月份统计已完成订单总额）
    monthly_sales = (
        Order.objects.filter(status='delivered')
        .annotate(month=TruncMonth('created_at'))
        .values('month')
        .annotate(total=Sum('total_amount'), count=Count('id'))
        .order_by('month')
    )

    # 产品分类分布
    category_dist = (
        Product.objects.values('category')
        .annotate(count=Count('id'))
        .order_by('-count')
    )

    # 订单状态分布
    order_status = (
        Order.objects.values('status')
        .annotate(count=Count('id'))
    )

    # 最新订单
    recent_orders = OrderSerializer(
        Order.objects.prefetch_related('items').order_by('-created_at')[:5],
        many=True
    ).data

    return Response({
        'total_products': total_products,
        'total_farmers': total_farmers,
        'total_orders': total_orders,
        'total_coops': total_coops,
        'monthly_sales': [
            {'month': s['month'].strftime('%Y-%m') if s['month'] else '未知', 'total': float(s['total'] or 0), 'count': s['count']}
            for s in monthly_sales
        ],
        'category_distribution': [
            {'category': c['category'] or '未分类', 'count': c['count']}
            for c in category_dist
        ],
        'order_status': {s['status']: s['count'] for s in order_status},
        'recent_orders': recent_orders,
    })


def dashboard_view(request):
    """数据驾驶舱页面"""
    return render(request, 'dashboard.html')


# ===== 智能供需分析 =====

@api_view(['GET'])
def demand_analysis(request):
    """需求分析 API — 分析产品卖往哪些地区、什么产品需求大"""
    # 1. 各地区需求排行（基于订单收货地址）
    regional_demand = (
        OrderItem.objects
        .filter(order__status='delivered')
        .values('product_batch__product__name')
        .annotate(
            total_qty=Sum('quantity'),
            total_revenue=Sum('price')
        )
        .order_by('-total_qty')[:10]
    )

    # 2. 各产品供需情况
    product_supply_demand = []
    for item in regional_demand:
        pname = item['product_batch__product__name']
        sold = item['total_qty']
        # 可用供应量（所有批次总量）
        available = ProductBatch.objects.filter(
            product__name=pname
        ).aggregate(total=Sum('quantity'))['total'] or 0
        product_supply_demand.append({
            'product': pname,
            'sold': sold,
            'available': available,
            'gap': available - sold if available > sold else 0,
            'shortage': sold - available if sold > available else 0,
        })

    # 3. 地区分布
    region_stats = (
        Order.objects
        .filter(status='delivered')
        .values('address')
        .annotate(order_count=Count('id'), total=Sum('total_amount'))
        .order_by('-order_count')[:8]
    )

    # 4. AI 分析简报（基于数据生成描述）
    total_products_analyzed = len(product_supply_demand)
    hot_product = product_supply_demand[0]['product'] if product_supply_demand else '暂无'
    shortage_products = [p for p in product_supply_demand if p['shortage'] > 0]

    analysis_summary = {
        'total_products_analyzed': total_products_analyzed,
        'hot_product': hot_product,
        'shortage_products_count': len(shortage_products),
        'shortage_products': [p['product'] for p in shortage_products[:5]],
        'regional_orders': [
            {'region': r['address'][:6], 'orders': r['order_count'], 'total': float(r['total'] or 0)}
            for r in region_stats
        ],
    }

    return Response({
        'product_supply_demand': product_supply_demand,
        'regional_demand_top': [
            {'product': r['product_batch__product__name'], 'sold': r['total_qty'], 'revenue': float(r['total_revenue'] or 0)}
            for r in regional_demand
        ],
        'analysis_summary': analysis_summary,
    })


def market_analysis_view(request):
    """市场分析页面"""
    return render(request, 'market_analysis.html')
