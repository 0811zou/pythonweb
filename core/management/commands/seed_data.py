"""seed_data 管理命令 — 填充演示数据（不会删除用户账号）"""
import random
from datetime import datetime, timedelta
from django.core.management.base import BaseCommand
from django.contrib.auth.models import User
from core.models import Cooperative, FarmerProfile, Product, ProductBatch, Order, OrderItem, Review


class Command(BaseCommand):
    help = '填充演示数据（不会删除用户账号）'

    def handle(self, *args, **options):
        # 只删除产品/订单数据，绝不碰用户账号
        Product.objects.all().delete()
        ProductBatch.objects.all().delete()
        Order.objects.all().delete()
        OrderItem.objects.all().delete()
        Review.objects.all().delete()

        now = datetime.now()

        # === 合作社 ===
        coop_defs = [
            ('绿源生态合作社', '山东省寿光市', True),
            ('果香园农业合作社', '陕西省洛川县', True),
            ('云雾山茶业合作社', '福建省武夷山市', True),
            ('渔米之乡合作社', '湖南省洞庭湖区', True),
            ('阳光果园合作社', '新疆维吾尔自治区', False),
        ]
        coops = []
        for name, region, verified in coop_defs:
            coop, _ = Cooperative.objects.get_or_create(name=name, defaults={'region': region, 'verified': verified})
            coops.append(coop)
        self.stdout.write(f'  {len(coops)} 个合作社')

        # === 农户（get_or_create 保留已有账号密码） ===
        raw_farmers = [
            ('farmer_wang', 0, '山东省寿光市孙家集街道'),
            ('farmer_li', 1, '陕西省洛川县旧县镇'),
            ('farmer_chen', 2, '福建省武夷山市星村镇'),
            ('farmer_zhang', 3, '湖南省岳阳市君山区'),
            ('farmer_zhao', 4, '新疆阿克苏地区温宿县'),
        ]
        farmers = []
        for uname, ci, addr in raw_farmers:
            user, created = User.objects.get_or_create(username=uname, defaults={'email': f'{uname}@test.com'})
            if created:
                user.set_password('demo123')
                user.save()
            fp, _ = FarmerProfile.objects.get_or_create(user=user, defaults={
                'phone': '1380000', 'address': addr, 'verified': True, 'cooperative': coops[ci]
            })
            farmers.append(fp)
        self.stdout.write(f'  {len(farmers)} 个农户')

        # === 消费者（get_or_create 保留已有账号密码） ===
        consumers = []
        for name in ['consumer_zheng', 'consumer_wu', 'consumer_liu']:
            user, created = User.objects.get_or_create(username=name, defaults={'email': f'{name}@test.com'})
            if created:
                user.set_password('demo123')
                user.save()
            consumers.append(user)
        self.stdout.write(f'  {len(consumers)} 个消费者')

        # === 管理员（确保存在） ===
        admin, created = User.objects.get_or_create(username='demo_admin', defaults={
            'email': 'admin@test.com', 'is_staff': True, 'is_superuser': True
        })
        if created:
            admin.set_password('DemoPass#2026')
            admin.save()

        # === 产品 ===
        product_data = [
            (0, '有机西红柿', '蔬菜', 8.5, '斤'),   # farmer_wang
            (0, '黄瓜', '蔬菜', 5.0, '斤'),        # farmer_wang
            (0, '草莓', '水果', 28.0, '盒'),        # farmer_wang
            (1, '洛川苹果', '水果', 12.0, '斤'),    # farmer_li
            (1, '嘎啦苹果', '水果', 9.0, '斤'),     # farmer_li
            (2, '大红袍茶叶', '茶叶', 168.0, '盒'), # farmer_chen
            (2, '正山小种', '茶叶', 88.0, '盒'),    # farmer_chen
            (3, '洞庭湖大米', '粮油', 35.0, '袋'),  # farmer_zhang
            (3, '莲子', '干货', 45.0, '斤'),        # farmer_zhang
            (4, '阿克苏冰糖心苹果', '水果', 15.0, '斤'), # farmer_zhao
            (4, '新疆红枣', '干货', 25.0, '斤'),    # farmer_zhao
            (0, '紫薯', '蔬菜', 6.0, '斤'),          # farmer_wang
        ]
        products = []
        for idx, (fi, name, cat, price, unit) in enumerate(product_data):
            p = Product.objects.create(
                farmer=farmers[fi], name=name, category=cat,
                price=price, unit=unit, description=name + '，优质农产品。',
                status='approved'
            )
            products.append(p)
        self.stdout.write(f'  {len(products)} 个产品（已上架）')

        # === 批次 ===
        batch_qtys = [200, 220, 70, 70, 200, 200, 80, 150, 100, 150, 200, 85]
        target_solds = [170, 0, 55, 145, 420, 30, 58, 85, 155, 85, 25, 68]
        batch_map = {}
        for idx, qty in enumerate(batch_qtys):
            b = ProductBatch.objects.create(
                product=products[idx], quantity=qty,
                harvest_date=(now - timedelta(days=random.randint(1, 120))).date(),
                trace_info={'产地': products[idx].farmer.address, '种植方式': '有机种植'},
                qc_report=[
                    '已通过农药残留检测，检测单位：寿光市农产品质检中心',
                    '符合绿色食品标准（NY/T 391-2021），无农残检出',
                    '有机转换认证检测中，送检样品全部合格',
                    '洛川苹果地理标志产品质量检测合格',
                    '经检测，糖度≥14%，果径≥80mm，一级果率96%',
                    '武夷岩茶国家标准（GB/T 18745）质量等级：特级',
                    '正山小种红茶，经欧盟农残标准检测全部合格',
                    '重金属及农残检测均低于国家标准限值，检测单位：岳阳海关',
                    '湘莲地理标志产品质量检测合格，颗粒饱满度≥95%',
                    '阿克苏冰糖心苹果，糖度≥16%，果径≥85mm',
                    '新疆红枣，水分≤28%，含糖量≥70%，一级品',
                    '紫薯花青素含量检测：≥120mg/100g，无农药残留',
                ][idx],
            )
            batch_map[idx] = [b]
        self.stdout.write(f'  {len(batch_map)} 个批次')

        # === 订单 ===
        regions = [
            '北京市朝阳区', '上海市浦东新区', '广州市天河区', '深圳市南山区',
            '杭州市西湖区', '成都市武侯区', '武汉市洪山区', '南京市鼓楼区',
        ]
        status_choices = ['pending', 'paid_offline', 'confirmed', 'shipped', 'delivered', 'cancelled']

        # 为目标销量生成订单项计划
        order_items_plan = []
        for idx, target in enumerate(target_solds):
            remaining = target
            while remaining > 0:
                qty = min(remaining, random.randint(1, 8))
                order_items_plan.append((idx, qty))
                remaining -= qty
        random.shuffle(order_items_plan)

        # 分组为订单
        order_groups = []
        i = 0
        while i < len(order_items_plan):
            gs = min(random.randint(1, 4), len(order_items_plan) - i)
            order_groups.append(order_items_plan[i:i+gs])
            i += gs

        all_orders = []
        for group in order_groups:
            buyer = random.choice(consumers)
            days_ago = random.randint(5, 180)
            created = now - timedelta(days=days_ago)
            if days_ago > 60:
                st = random.choices(status_choices, weights=[0,0,0,1,12,0])[0]
            elif days_ago > 30:
                st = random.choices(status_choices, weights=[1,1,1,2,8,1])[0]
            else:
                st = random.choices(status_choices, weights=[3,2,1,1,3,1])[0]
            order = Order.objects.create(buyer=buyer, total_amount=0, status=st, address=random.choice(regions))
            total = 0
            for prod_idx, qty in group:
                bp = random.choice(batch_map[prod_idx])
                price = float(products[prod_idx].price)
                OrderItem.objects.create(order=order, product_batch=bp, quantity=qty, price=price)
                total += price * qty
            order.total_amount = total
            order.save()
            Order.objects.filter(pk=order.pk).update(created_at=created)
            all_orders.append(order)

        # 补充随机订单（避开待售产品）
        no_sale_idx = {1, 2, 11}
        random_batches = [b for i, bs in batch_map.items() if i not in no_sale_idx for b in bs]
        for _ in range(10):
            buyer = random.choice(consumers)
            order = Order.objects.create(buyer=buyer, total_amount=0, status=random.choice(['shipped','delivered']), address=random.choice(regions))
            total = 0
            for _ in range(random.randint(1, 3)):
                bp = random.choice(random_batches)
                qty = random.randint(1, 5)
                price = float(bp.product.price)
                OrderItem.objects.create(order=order, product_batch=bp, quantity=qty, price=price)
                total += price * qty
            order.total_amount = total
            order.save()

        self.stdout.write(f'  {len(all_orders)} 个已完成订单（时间跨度6个月）')

        # === 评价 ===
        comments = ['包装很好，水果新鲜！', '品质不错，物流很快', '第二次购买了，家人很喜欢', '价格实惠，还会回购']
        cnt = 0
        for order in all_orders:
            if order.status == 'delivered' and order.items.count() > 0 and random.random() < 0.5:
                Review.objects.create(order=order, buyer=order.buyer,
                    farmer=order.items.first().product_batch.product.farmer,
                    rating=random.randint(3, 5), comment=random.choice(comments))
                cnt += 1
        self.stdout.write(f'  {cnt} 条评价')

        self.stdout.write(self.style.SUCCESS('\n=== 填充完成 ==='))
        self.stdout.write('  账号密码未改变')
