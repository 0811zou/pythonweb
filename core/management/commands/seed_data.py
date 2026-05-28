"""seed_data 管理命令 — 填充演示数据"""
import random
from datetime import datetime, timedelta
from django.core.management.base import BaseCommand
from django.contrib.auth.models import User
from core.models import Cooperative, FarmerProfile, Product, ProductBatch, Order, OrderItem, Review


class Command(BaseCommand):
    help = '填充丰富的演示数据'

    def handle(self, *args, **options):
        # 清理旧数据（保留管理员）
        User.objects.filter(is_superuser=False).delete()
        Cooperative.objects.all().delete()
        FarmerProfile.objects.all().delete()
        Product.objects.all().delete()
        ProductBatch.objects.all().delete()
        Order.objects.all().delete()
        OrderItem.objects.all().delete()
        Review.objects.all().delete()

        # === 合作社 ===
        coops = [
            Cooperative.objects.create(name='绿源生态合作社', region='山东省寿光市', verified=True),
            Cooperative.objects.create(name='果香园农业合作社', region='陕西省洛川县', verified=True),
            Cooperative.objects.create(name='云雾山茶业合作社', region='福建省武夷山市', verified=True),
            Cooperative.objects.create(name='渔米之乡合作社', region='湖南省洞庭湖区', verified=True),
            Cooperative.objects.create(name='阳光果园合作社', region='新疆维吾尔自治区', verified=False),
        ]
        self.stdout.write(f'✅ {len(coops)} 个合作社')

        # === 农户 ===
        raw_farmers = [
            ('farmer_wang', 0, '13800001001', '山东省寿光市孙家集街道'),
            ('farmer_li', 1, '13800001002', '陕西省洛川县旧县镇'),
            ('farmer_chen', 2, '13800001003', '福建省武夷山市星村镇'),
            ('farmer_zhang', 3, '13800001004', '湖南省岳阳市君山区'),
            ('farmer_zhao', 4, '13800001005', '新疆阿克苏地区温宿县'),
        ]
        farmers = []
        for uname, ci, phone, addr in raw_farmers:
            u = User.objects.create_user(uname, f'{uname}@test.com', 'demo123')
            fp = FarmerProfile.objects.create(user=u, cooperative=coops[ci], phone=phone, address=addr, verified=True)
            farmers.append(fp)
        self.stdout.write(f'✅ {len(farmers)} 个农户')

        # === 消费者 ===
        consumers = []
        for name in ['consumer_zheng', 'consumer_wu', 'consumer_liu']:
            consumers.append(User.objects.create_user(name, f'{name}@test.com', 'demo123'))
        self.stdout.write(f'✅ {len(consumers)} 个消费者')

        # === 产品 ===
        raw_products = [
            (0, '有机西红柿', '蔬菜', '普罗旺斯', '8.50', '斤', '温室有机种植，自然成熟，酸甜可口。'),
            (0, '黄瓜', '蔬菜', '密刺黄瓜', '5.00', '斤', '新鲜采摘，清脆爽口。'),
            (0, '草莓', '水果', '红颜', '28.00', '盒', '蜜蜂授粉，自然成熟，每盒约500g。'),
            (1, '洛川苹果', '水果', '红富士', '12.00', '斤', '洛川苹果，中国地理标志产品。'),
            (1, '嘎啦苹果', '水果', '嘎啦', '9.00', '斤', '早熟品种，口感脆甜。'),
            (2, '大红袍茶叶', '茶叶', '武夷岩茶', '168.00', '盒', '正宗武夷岩茶，每盒250g。'),
            (2, '正山小种', '茶叶', '红茶', '88.00', '盒', '传统烟熏工艺，每盒200g。'),
            (3, '洞庭湖大米', '粮油', '湘晚籼', '35.00', '袋', '洞庭湖区生态种植，每袋5kg。'),
            (3, '莲子', '干货', '湘莲', '45.00', '斤', '洞庭湖优质湘莲，煲汤佳品。'),
            (4, '阿克苏冰糖心苹果', '水果', '冰糖心', '15.00', '斤', '新疆阿克苏特产，甜度极高。'),
            (4, '新疆红枣', '干货', '灰枣', '25.00', '斤', '若羌灰枣，皮薄肉厚。'),
            (0, '紫薯', '蔬菜', '日本紫薯', '6.00', '斤', '富含花青素，软糯香甜。'),
        ]
        products = []
        for fi, name, cat, var, price, unit, desc in raw_products:
            p = Product.objects.create(
                farmer=farmers[fi], name=name, category=cat, variety=var,
                price=price, unit=unit, description=desc, status='approved'
            )
            products.append(p)
        self.stdout.write(f'✅ {len(products)} 个产品（已上架）')

        # === 批次 ===
        now = datetime.now()
        batches = []
        for idx in [0, 3, 4, 5, 7, 9, 10, 11]:
            p = products[idx]
            for _ in range(random.randint(1, 2)):
                batch = ProductBatch.objects.create(
                    product=p,
                    quantity=random.randint(50, 300),
                    harvest_date=(now - timedelta(days=random.randint(1, 60))).date(),
                    trace_info={
                        'planting': f'{p.name}种植于优质产区',
                        'fertilizing': '使用农家有机肥',
                        'harvesting': f'于{(now - timedelta(days=random.randint(1,30))).strftime("%Y年%m月%d日")}人工采摘',
                        'testing': '经检测，农残未检出',
                    },
                    qc_report=f'QC-2026-{random.randint(1000,9999)}',
                )
                batches.append(batch)
        self.stdout.write(f'✅ {len(batches)} 个批次')

        # === 订单 ===
        status_choices = ['pending', 'paid_offline', 'confirmed', 'shipped', 'delivered', 'cancelled']
        weights = [2, 1, 1, 2, 8, 1]
        regions = ['北京市朝阳区', '上海市浦东新区', '广州市天河区', '深圳市南山区', '杭州市西湖区', '成都市武侯区', '武汉市洪山区', '南京市鼓楼区']
        orders = []
        for i in range(20):
            buyer = random.choice(consumers)
            status = random.choices(status_choices, weights=weights)[0]
            created = now - timedelta(days=random.randint(1, 45))
            order = Order.objects.create(
                buyer=buyer, total_amount=0,
                status=status,
                address=random.choice(regions) + '某某路XX号',
                created_at=created,
                updated_at=created + timedelta(hours=random.randint(1, 72)),
            )
            total = 0
            for _ in range(random.randint(1, 3)):
                bp = random.choice(batches)
                qty = random.randint(1, 5)
                price = float(bp.product.price)
                OrderItem.objects.create(order=order, product_batch=bp, quantity=qty, price=price)
                total += price * qty
            order.total_amount = total
            order.save()
            orders.append(order)
        delivered = sum(1 for o in orders if o.status == 'delivered')
        self.stdout.write(f'✅ {len(orders)} 个订单（{delivered}个已完成）')

        # === 评价 ===
        comments = ['包装很好，水果新鲜！', '品质不错，物流很快', '第二次购买了，家人很喜欢', '茶叶味道醇厚，推荐', '价格实惠，还会回购']
        for order in orders[:5]:
            if order.status == 'delivered' and order.items.count() > 0:
                Review.objects.create(
                    order=order, buyer=order.buyer,
                    farmer=order.items.first().product_batch.product.farmer,
                    rating=random.randint(3, 5),
                    comment=random.choice(comments),
                )
        self.stdout.write('✅ 评价数据')

        self.stdout.write(self.style.SUCCESS('\n=== 填充完成！==='))
        self.stdout.write('  管理员: demo_admin / DemoPass#2026')
        self.stdout.write('  农户:   farmer_wang / demo123')
        self.stdout.write('  消费者: consumer_zheng / demo123')
