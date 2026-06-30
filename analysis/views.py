from decimal import Decimal
from rest_framework import permissions
from rest_framework.decorators import api_view, permission_classes
from rest_framework.response import Response
from drf_spectacular.utils import extend_schema
from drf_spectacular.types import OpenApiTypes
from django.shortcuts import render, redirect, reverse
from django.contrib import messages
from django.db.models import Count, Sum, Q, F, DecimalField, ExpressionWrapper
from core.models import Order, OrderItem, ProductBatch, Product
from .llm_service import generate_analysis, chat_with_farmer


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


# ===== 市场分析页面（公共功能 — 所有登录用户可访问）=====

def market_analysis_view(request):
    """市场分析页面 — 消费者与农户均可查看"""
    if not request.user.is_authenticated:
        messages.info(request, '请先登录后查看市场分析')
        return redirect(f"{reverse('accounts:login')}?next={request.path}")
    return render(request, 'market_analysis.html')


# ===== AI 智能问答助手 =====

def ai_assistant_view(request):
    """AI 智能问答页面 — 对所有用户开放"""
    return render(request, 'ai_assistant.html')


@extend_schema(responses=OpenApiTypes.OBJECT)
@api_view(['POST'])
def ai_chat_api(request):
    """AI 问答 API — 接收问题，返回 AI 回答"""
    import json
    # 尝试 UTF-8 解码，失败则回退到 GBK（Windows curl 发中文用系统 ANSI 编码）
    try:
        raw = request.body.decode('utf-8')
    except UnicodeDecodeError:
        raw = request.body.decode('gbk')
    try:
        body = json.loads(raw)
    except json.JSONDecodeError:
        return Response({'error': '请求格式错误'}, status=400)

    question = body.get('question', '').strip()
    if not question:
        return Response({'error': '请输入问题'}, status=400)
    if len(question) > 500:
        return Response({'error': '问题不能超过500字'}, status=400)

    # 获取对话历史（前端维护，最多保留10条）
    history = body.get('history', [])
    if not isinstance(history, list):
        history = []
    history = history[-10:]  # 限制上下文长度

    result = chat_with_farmer(question, history)

    return Response({
        'question': question,
        'answer': result['answer'],
        'model': result['model'],
    })
