"""填充丰富的演示数据"""
import os, django, uuid
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')
django.setup()

from django.contrib.auth.models import User
from core.models import Cooperative, FarmerProfile, Product, ProductBatch, Order, OrderItem, Review

print('=== 开始填充演示数据 ===')

# 清理旧数据（保留管理员）
User.objects.filter(is_superuser=False).delete()
Cooperative.objects.all().delete()
FarmerProfile.objects.all().delete()
Product.objects.all().delete()
ProductBatch.objects.all().delete()
Order.objects.all().delete()
OrderItem.objects.all().delete()

# ===== 创建合作社 =====
coops_data = [
    {'name': '绿源生态合作社', 'region': '山东省寿光市', 'verified': True},
    {'name': '果香园农业合作社', 'region': '陕西省洛川县', 'verified': True},
    {'name': '云雾山茶业合作社', 'region': '福建省武夷山市', 'verified': True},
    {'name': '渔米之乡合作社', 'region': '湖南省洞庭湖区', 'verified': True},
    {'name': '阳光果园合作社', 'region': '新疆维吾尔自治区', 'verified': False},
]
coops = [Cooperative.objects.create(**c) for c in coops_data]
print(f'✅ 创建 {len(coops)} 个合作社')

# ===== 创建农户用户 =====
farmers_data = [
    {'username': 'farmer_wang', 'coop': 0, 'phone': '13800001001', 'address': '山东省寿光市孙家集街道'},
    {'username': 'farmer_li', 'coop': 1, 'phone': '13800001002', 'address': '陕西省洛川县旧县镇'},
    {'username': 'farmer_chen', 'coop': 2, 'phone': '13800001003', 'address': '福建省武夷山市星村镇'},
    {'username': 'farmer_zhang', 'coop': 3, 'phone': '13800001004', 'address': '湖南省岳阳市君山区'},
    {'username': 'farmer_zhao', 'coop': 4, 'phone': '13800001005', 'address': '新疆阿克苏地区温宿县'},
]
farmers = []
for i, f in enumerate(farmers_data):
    user = User.objects.create_user(f['username'], f'{f["username"]}@test.com', 'demo123')
    profile = FarmerProfile.objects.create(
        user=user, cooperative=coops[f['coop']],
        phone=f['phone'], address=f['address'],
        verified=True
    )
    farmers.append(profile)
print(f'✅ 创建 {len(farmers)} 个农户')

# ===== 创建消费者用户 =====
consumers_data = [
    {'username': 'consumer_zheng', 'email': 'zheng@test.com'},
    {'username': 'consumer_wu', 'email': 'wu@test.com'},
    {'username': 'consumer_liu', 'email': 'liu@test.com'},
]
consumers = []
for c in consumers_data:
    user = User.objects.create_user(c['username'], c['email'], 'demo123')
    consumers.append(user)
print(f'✅ 创建 {len(consumers)} 个消费者')

# ===== 创建产品 =====
products_data = [
    {'farmer': 0, 'name': '有机西红柿', 'category': '蔬菜', 'variety': '普罗旺斯', 'price': '8.50', 'unit': '斤', 'description': '温室有机种植，自然成熟，酸甜可口，适合生食和烹饪。'},
    {'farmer': 0, 'name': '黄瓜', 'category': '蔬菜', 'variety': '密刺黄瓜', 'price': '5.00', 'unit': '斤', 'description': '新鲜采摘，清脆爽口，农家肥种植。'},
    {'farmer': 0, 'name': '草莓', 'category': '水果', 'variety': '红颜', 'price': '28.00', 'unit': '盒', 'description': '蜜蜂授粉，自然成熟，果香浓郁，每盒约500g。'},
    {'farmer': 1, 'name': '洛川苹果', 'category': '水果', 'variety': '红富士', 'price': '12.00', 'unit': '斤', 'description': '洛川苹果，中国地理标志产品，色泽艳丽、脆甜多汁。'},
    {'farmer': 1, 'name': '嘎啦苹果', 'category': '水果', 'variety': '嘎啦', 'price': '9.00', 'unit': '斤', 'description': '早熟品种，口感脆甜，适合喜欢清爽口感的人群。'},
    {'farmer': 2, 'name': '大红袍茶叶', 'category': '茶叶', 'variety': '武夷岩茶', 'price': '168.00', 'unit': '盒', 'description': '正宗武夷岩茶，传统炭焙工艺，岩韵悠长，每盒250g。'},
    {'farmer': 2, 'name': '正山小种', 'category': '茶叶', 'variety': '红茶', 'price': '88.00', 'unit': '盒', 'description': '传统烟熏工艺，松烟香浓郁，汤色红艳明亮，每盒200g。'},
    {'farmer': 3, 'name': '洞庭湖大米', 'category': '粮油', 'variety': '湘晚籼', 'price': '35.00', 'unit': '袋', 'description': '洞庭湖区生态种植，颗粒饱满，口感软糯，每袋5kg。'},
    {'farmer': 3, 'name': '莲子', 'category': '干货', 'variety': '湘莲', 'price': '45.00', 'unit': '斤', 'description': '洞庭湖优质湘莲，颗粒饱满，无硫熏制，煲汤佳品。'},
    {'farmer': 4, 'name': '阿克苏冰糖心苹果', 'category': '水果', 'variety': '冰糖心', 'price': '15.00', 'unit': '斤', 'description': '新疆阿克苏特产，独特冰糖心，甜度极高，脆爽多汁。'},
    {'farmer': 4, 'name': '新疆红枣', 'category': '干货', 'variety': '灰枣', 'price': '25.00', 'unit': '斤', 'description': '新疆若羌灰枣，皮薄肉厚，核小味甜，自然风干。'},
    {'farmer': 0, 'name': '紫薯', 'category': '蔬菜', 'variety': '日本紫薯', 'price': '6.00', 'unit': '斤', 'description': '富含花青素，软糯香甜，蒸烤皆宜。'},
]

products = []
for i, p in enumerate(products_data):
    product = Product.objects.create(
        farmer=farmers[p['farmer']],
        name=p['name'], category=p['category'],
        variety=p['variety'], price=p['price'],
        unit=p['unit'], description=p['description'],
        status='approved'  # 直接上架
    )
    products.append(product)
print(f'✅ 创建 {len(products)} 个产品（已上架）')

# ===== 创建批次 =====
import random
from datetime import datetime, timedelta

now = datetime.now()
batches = []
batch_products = [0, 3, 4, 5, 7, 9, 10, 11]  # 哪些产品有批次
for idx in batch_products:
    p = products[idx]
    for b in range(random.randint(1, 2)):  # 每个产品1-2个批次
        batch = ProductBatch.objects.create(
            product=p,
            quantity=random.randint(50, 300),
            harvest_date=(now - timedelta(days=random.randint(1, 60))).date(),
            trace_info={
                'planting': f'{p.name}种植于优质产区，采用有机种植方式',
                'fertilizing': '使用农家有机肥，无化学农药',
                'harvesting': f'于{ (now - timedelta(days=random.randint(1, 30))).strftime("%Y年%m月%d日") }进行人工采摘',
                'testing': '经第三方检测，农残未检出',
            },
            qc_report=f'报告编号：QC-2026-{random.randint(1000,9999)}',
            images=[],
        )
        batches.append(batch)
print(f'✅ 创建 {len(batches)} 个产品批次')

# ===== 创建订单 =====
statuses = ['pending', 'paid_offline', 'confirmed', 'shipped', 'delivered', 'cancelled']
orders = []
for i in range(20):  # 20个订单
    buyer = random.choice(consumers)
    addr = random.choice(['北京市朝阳区', '上海市浦东新区', '广州市天河区', '深圳市南山区', '杭州市西湖区', '成都市武侯区', '武汉市洪山区', '南京市鼓楼区'])
    status = random.choices(statuses, weights=[2, 1, 1, 2, 8, 1])[0]  # 偏向已完成
    created = now - timedelta(days=random.randint(1, 45))
    order = Order.objects.create(
        buyer=buyer,
        total_amount=0,  # 后面计算
        status=status,
        address=addr + '某某路XX号',
        created_at=created,
        updated_at=created + timedelta(hours=random.randint(1, 72)),
    )
    # 随机1-3个订单项
    total = 0
    for j in range(random.randint(1, 3)):
        bp = random.choice(batches)
        qty = random.randint(1, 5)
        price = float(bp.product.price)
        OrderItem.objects.create(order=order, product_batch=bp, quantity=qty, price=price)
        total += price * qty
    order.total_amount = total
    order.save()
    orders.append(order)

print(f'✅ 创建 {len(orders)} 个订单')
delivered = sum(1 for o in orders if o.status == 'delivered')
print(f'   ├─ 已完成: {delivered}')
print(f'   └─ 其他: {len(orders) - delivered}')

# ===== 创建评价 =====
reviews_data = [
    {'order_idx': 0, 'rating': 5, 'comment': '包装很好，水果新鲜，物流也快！'},
    {'order_idx': 0, 'rating': 4, 'comment': '品质不错，价格稍贵了点'},
    {'order_idx': 1, 'rating': 5, 'comment': '第二次购买了，家人很喜欢'},
    {'order_idx': 1, 'rating': 3, 'comment': '这次的质量不如上次好'},
    {'order_idx': 2, 'rating': 4, 'comment': '茶叶味道醇厚，推荐'},
]
for r in reviews_data[:len(orders)]:
    order = orders[r['order_idx'] % len(orders)]
    if order.status == 'delivered':
        Review.objects.create(
            order=order, buyer=order.buyer,
            farmer=order.items.first().product_batch.product.farmer if order.items.count() > 0 else farmers[0],
            rating=r['rating'], comment=r['comment'],
            created_at=order.updated_at
        )

print('✅ 创建评价数据')
print()
print('=== 填充完成！===')
print()
print('演示账号:')
print('  管理员:   demo_admin / DemoPass#2026')
print('  农户:     farmer_wang / demo123')
print('  消费者:   consumer_zheng / demo123')
