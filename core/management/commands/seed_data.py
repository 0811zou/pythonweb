"""seed_data 管理命令 — 填充全国多省份产品及批次数据（不会删除用户账号）"""
import random
from collections import namedtuple
from datetime import datetime, timedelta
from django.core.management.base import BaseCommand
from django.contrib.auth.models import User
from core.models import Cooperative, FarmerProfile, Product, ProductBatch, Order, OrderItem, Review


class Command(BaseCommand):
    help = '填充演示数据（不会删除用户账号）'

    def handle(self, *args, **options):
        Product.objects.all().delete()
        ProductBatch.objects.all().delete()
        Order.objects.all().delete()
        OrderItem.objects.all().delete()
        Review.objects.all().delete()

        now = datetime.now()

        # ============================
        # 合作社（全国覆盖）
        # ============================
        coop_defs = [
            ('绿源生态合作社', '山东省寿光市', True),
            ('果香园农业合作社', '陕西省洛川县', True),
            ('云雾山茶业合作社', '福建省武夷山市', True),
            ('渔米之乡合作社', '湖南省洞庭湖区', True),
            ('阳光果园合作社', '新疆维吾尔自治区', False),
            ('天府农业合作社', '四川省眉山市', True),
            ('彩云之南农业合作社', '云南省普洱市', True),
            ('岭南佳果合作社', '广东省茂名市', True),
            ('黑土地生态合作社', '黑龙江省五常市', True),
            ('太湖农业合作社', '江苏省苏州市', True),
            ('钱塘农业合作社', '浙江省杭州市', True),
            ('长白山特产合作社', '吉林省白山市', True),
            ('八桂农业合作社', '广西百色市', True),
            ('黔农合作社', '贵州省遵义市', True),
            ('燕赵农业合作社', '河北省石家庄市', True),
            # === 新增 19 省合作社 ===
            ('三晋农业合作社', '山西省太原市', True),
            ('辽河农业合作社', '辽宁省盘锦市', True),
            ('徽州农业合作社', '安徽省黄山市', True),
            ('赣鄱农业合作社', '江西省赣州市', True),
            ('中原农业合作社', '河南省郑州市', True),
            ('荆楚农业合作社', '湖北省恩施市', True),
            ('琼岛农业合作社', '海南省三亚市', True),
            ('丝路农业合作社', '甘肃省兰州市', True),
            ('青海湖农业合作社', '青海省海东市', True),
            ('草原牧歌合作社', '内蒙古呼和浩特市', True),
            ('雪域高原合作社', '西藏林芝市', True),
            ('塞上江南合作社', '宁夏银川市', True),
            ('京郊生态合作社', '北京市平谷区', True),
            ('津沽农业合作社', '天津市津南区', True),
            ('申城农业合作社', '上海市崇明区', True),
            ('巴渝农业合作社', '重庆市涪陵区', True),
            ('宝岛农业合作社', '台湾省南投县', True),
            ('香港有机农场', '香港特别行政区', True),
            ('澳门农业合作社', '澳门特别行政区', True),
        ]
        coops = []
        for name, region, verified in coop_defs:
            coop, _ = Cooperative.objects.get_or_create(
                name=name, defaults={'region': region, 'verified': verified}
            )
            coops.append(coop)
        self.stdout.write(f'  {len(coops)} 个合作社')

        # ============================
        # 农户（保留已有账号）
        # ============================
        raw_farmers = [
            ('farmer_wang',  0, '山东省寿光市孙家集街道'),
            ('farmer_li',    1, '陕西省洛川县旧县镇'),
            ('farmer_chen',  2, '福建省武夷山市星村镇'),
            ('farmer_zhang', 3, '湖南省岳阳市君山区'),
            ('farmer_zhao',  4, '新疆阿克苏地区温宿县'),
            ('farmer_sun',   5, '四川省眉山市东坡区'),
            ('farmer_zhou',  6, '云南省普洱市思茅区'),
            ('farmer_huang', 7, '广东省茂名市高州市'),
            ('farmer_wu',    8, '黑龙江省五常市杜家镇'),
            ('farmer_xu',    9, '江苏省苏州市吴中区'),
            ('farmer_ma',   10, '浙江省杭州市西湖区'),
            ('farmer_liu',  11, '吉林省白山市抚松县'),
            ('farmer_wei',  12, '广西百色市田阳区'),
            ('farmer_tan',  13, '贵州省遵义市湄潭县'),
            ('farmer_guo',  14, '河北省石家庄市赵县'),
            # === 新增 19 省农户 ===
            ('farmer_jin',     15, '山西省太原市阳曲县'),
            ('farmer_liao',    16, '辽宁省盘锦市大洼区'),
            ('farmer_wan',     17, '安徽省黄山市徽州区'),
            ('farmer_ganjx',   18, '江西省赣州市章贡区'),
            ('farmer_yu',      19, '河南省郑州市新郑市'),
            ('farmer_echu',    20, '湖北省恩施市芭蕉侗族乡'),
            ('farmer_qiong',   21, '海南省三亚市崖州区'),
            ('farmer_gansu',   22, '甘肃省兰州市七里河区'),
            ('farmer_qinghai', 23, '青海省海东市互助县'),
            ('farmer_neimeng', 24, '内蒙古呼和浩特市土默特左旗'),
            ('farmer_xizang',  25, '西藏林芝市巴宜区'),
            ('farmer_ningxia', 26, '宁夏银川市西夏区'),
            ('farmer_bj',      27, '北京市平谷区大华山镇'),
            ('farmer_tj',      28, '天津市津南区小站镇'),
            ('farmer_sh',      29, '上海市崇明区中兴镇'),
            ('farmer_cq',      30, '重庆市涪陵区南沱镇'),
            ('farmer_tw',      31, '台湾省南投县鹿谷乡'),
            ('farmer_hk',      32, '香港特别行政区元朗区'),
            ('farmer_mo',      33, '澳门特别行政区路环岛'),
        ]
        farmers = []
        for uname, ci, addr in raw_farmers:
            user, created = User.objects.get_or_create(
                username=uname, defaults={'email': f'{uname}@test.com'}
            )
            if created:
                user.set_password('demo123')
                user.save()
            fp, _ = FarmerProfile.objects.get_or_create(
                user=user, defaults={
                    'phone': '1380000', 'address': addr,
                    'verified': True, 'cooperative': coops[ci],
                }
            )
            farmers.append(fp)
        self.stdout.write(f'  {len(farmers)} 个农户')

        # ============================
        # 消费者
        # ============================
        consumers = []
        for name in ['consumer_zheng', 'consumer_wu', 'consumer_liu',
                     'consumer_tian', 'consumer_lin']:
            user, created = User.objects.get_or_create(
                username=name, defaults={'email': f'{name}@test.com'}
            )
            if created:
                user.set_password('demo123')
                user.save()
            consumers.append(user)
        self.stdout.write(f'  {len(consumers)} 个消费者')

        # 管理员
        admin, created = User.objects.get_or_create(username='demo_admin', defaults={
            'email': 'admin@test.com', 'is_staff': True, 'is_superuser': True,
        })
        if created:
            admin.set_password('DemoPass#2026')
            admin.save()

        # ============================
        # 产品定义（全国34省区市全覆盖）
        # ============================
        # (farmer_idx, name, category, variety, price, unit, desc_suffix,
        #  batch_qtys: [每个批次的库存], target_sold: 目标销量)

        ProductDef = namedtuple(
            'ProductDef', 'fi name cat variety price unit desc qtys target'
        )

        product_defs = [
            # farmer_wang — 山东蔬菜
            ProductDef(0, '有机西红柿', '蔬菜', '普罗旺斯',       8.5,  '斤', '自然成熟，沙瓤多汁',                [200, 180, 150], 170),
            ProductDef(0, '黄瓜',      '蔬菜', '密刺黄瓜',       5.0,  '斤', '鲜嫩清脆，顶花带刺',                [300, 250], 0),
            ProductDef(0, '草莓',      '水果', '章姬',           28.0, '盒', '奶香浓郁，甜度≥13%',               [100, 80, 60], 55),
            ProductDef(0, '紫薯',      '蔬菜', '越南紫薯',       6.0,  '斤', '花青素丰富，粉糯香甜',              [150, 120], 68),

            # farmer_li — 陕西苹果
            ProductDef(1, '洛川苹果',  '水果', '红富士',         12.0, '斤', '地理标志产品，脆甜多汁',            [200, 150, 100], 145),
            ProductDef(1, '嘎啦苹果',  '水果', '嘎啦',           9.0,  '斤', '早熟品种，酸甜适口',                [150, 120, 100], 0),

            # farmer_chen — 福建茶叶
            ProductDef(2, '大红袍茶叶','茶叶', '大红袍',         168.0,'盒', '武夷岩茶，岩韵悠长',                [100, 80, 60, 50], 30),
            ProductDef(2, '正山小种',  '茶叶', '正山小种',       88.0, '盒', '传统烟熏工艺，桂圆汤香',            [120, 100, 80], 58),

            # farmer_zhang — 湖南
            ProductDef(3, '洞庭湖大米','粮油', '湘晚籼',         35.0, '袋', '湖区生态种植，软糯回甘',            [150, 120, 100], 85),
            ProductDef(3, '莲子',      '干货', '湘莲',           45.0, '斤', '颗大饱满，无硫熏蒸',                [100, 80], 0),

            # farmer_zhao — 新疆
            ProductDef(4, '阿克苏冰糖心苹果', '水果', '冰糖心',  15.0, '斤', '糖心明显，甜脆多汁',                [200, 180, 150], 85),
            ProductDef(4, '新疆红枣',  '干货', '灰枣',           25.0, '斤', '皮薄肉厚，核小味甜',                [180, 150, 120], 25),

            # farmer_sun — 四川
            ProductDef(5, '爱媛果冻橙','水果', '爱媛38号',       12.0, '斤', '皮薄多汁，入口即化',                [200, 150, 100], 110),
            ProductDef(5, '郫县豆瓣',  '干货', '红油豆瓣',       15.0, '瓶', '百年传承，川菜之魂',                [300, 250, 200], 130),
            ProductDef(5, '汉源花椒',  '干货', '贡椒',           38.0, '盒', '色泽丹红，麻味纯正',                [100, 80], 25),

            # farmer_zhou — 云南
            ProductDef(6, '普洱茶饼',  '茶叶', '生普',           128.0,'饼', '古树原料，越陈越香',                [50, 40, 30, 20], 35),
            ProductDef(6, '松茸干货',  '干货', '香格里拉松茸',   268.0,'盒', '野生菌王，煲汤佳品',                [30, 25, 20], 18),
            ProductDef(6, '鲜花饼',    '粮油', '玫瑰饼',         32.0, '盒', '现烤现发，花香四溢',                [200, 150], 60),

            # farmer_huang — 广东
            ProductDef(7, '妃子笑荔枝','水果', '妃子笑',         18.0, '斤', '核小肉厚，清甜多汁',                [150, 120, 80], 90),
            ProductDef(7, '高州香蕉',  '水果', '矮蕉',           5.0,  '斤', '自然熟，香甜软糯',                  [250, 200, 150], 0),

            # farmer_wu — 黑龙江
            ProductDef(8, '五常大米',  '粮油', '稻花香2号',      45.0, '袋', '中国地理标志，米香浓郁',            [200, 180, 150, 100], 140),
            ProductDef(8, '黑豆',      '粮油', '青仁乌豆',       12.0, '斤', '非转基因，高蛋白',                  [150, 120], 0),

            # farmer_xu — 江苏
            ProductDef(9, '阳澄湖大闸蟹','水产','中华绒螯蟹',    128.0,'只', '青背白肚，金爪黄毛',                [200, 150, 100], 120),
            ProductDef(9, '碧螺春茶叶','茶叶', '洞庭碧螺春',     198.0,'盒', '卷曲如螺，银绿隐翠',                [60, 50, 40], 25),

            # farmer_ma — 浙江
            ProductDef(10,'西湖龙井',  '茶叶', '龙井43',         188.0,'盒', '色翠香郁，味甘形美',                [80, 60, 50, 40], 45),
            ProductDef(10,'临安山核桃','干货', '小核桃',         58.0, '斤', '粒大壳薄，奶油飘香',                [100, 80, 60], 40),

            # farmer_liu — 吉林
            ProductDef(11,'长白山人参','干货', '林下参',         88.0, '盒', '参龄≥15年，芦长体灵',              [50, 40, 30], 10),
            ProductDef(11,'秋木耳',    '干货', '黑木耳',         48.0, '斤', '肉厚无根，泡发率高',                [80, 60, 50], 14),

            # farmer_wei — 广西
            ProductDef(12,'台农芒果',  '水果', '台农1号',        15.0, '斤', '金黄诱人，香甜无丝',                [200, 150, 120], 85),
            ProductDef(12,'百香果',    '水果', '紫香',           10.0, '斤', '酸甜多汁，维C之王',                 [250, 200, 150], 70),

            # farmer_tan — 贵州
            ProductDef(13,'遵义辣椒',  '干货', '朝天椒',         22.0, '斤', '香辣浓郁，色泽红亮',                [150, 120, 100], 45),
            ProductDef(13,'湄潭翠芽',  '茶叶', '翠芽',           98.0, '盒', '贵州绿茶，鲜爽回甘',                [60, 50, 40], 20),

            # farmer_guo — 河北
            ProductDef(14,'赵县雪梨',  '水果', '雪花梨',         8.0,  '斤', '汁多味甜，润肺止咳',                [200, 180, 150], 95),
            ProductDef(14,'迁西板栗',  '干货', '京东板栗',       18.0, '斤', '甜糯可口，壳薄易剥',                [150, 120, 100], 55),

            # farmer_jin — 山西
            ProductDef(15,'沁州黄小米','粮油', '沁州黄',         22.0, '斤', '皇家贡米，米油丰厚',                [200, 150, 120], 45),
            ProductDef(15,'隰县玉露香梨','水果','玉露香',        12.0, '斤', '皮薄肉嫩，汁多无渣',                [150, 120, 100], 60),
            ProductDef(15,'山西老陈醋','干货', '陈醋',           18.0, '瓶', '酸香绵甜，五年陈酿',                [300, 250, 200], 0),

            # farmer_liao — 辽宁
            ProductDef(16,'盘锦蟹田大米','粮油','盐丰',          38.0, '袋', '蟹稻共生，软糯清香',                [200, 180, 150], 75),
            ProductDef(16,'丹东久久草莓','水果','九九',          30.0, '盒', '个大香甜，汁水饱满',                [100, 80, 60, 50], 45),
            ProductDef(16,'大连樱桃',  '水果', '美早',           68.0, '斤', '果硬耐运，脆甜可口',                [80, 60, 50], 20),

            # farmer_wan — 安徽
            ProductDef(17,'黄山毛峰',  '茶叶', '黄山毛峰',       158.0,'盒', '形似雀舌，清香悠远',                [80, 60, 50, 40], 30),
            ProductDef(17,'砀山酥梨',  '水果', '金盖酥',         8.0,  '斤', '酥脆多汁，润肺止咳',                [200, 180, 150], 90),
            ProductDef(17,'霍山石斛',  '干货', '米斛',           298.0,'盒', '中华仙草，养生珍品',                [30, 25, 20], 8),

            # farmer_ganjx — 江西
            ProductDef(18,'赣南脐橙',  '水果', '纽荷尔',         10.0, '斤', '果大形正，橙香浓郁',                [250, 200, 150], 110),
            ProductDef(18,'庐山云雾茶','茶叶', '庐山云雾',       128.0,'盒', '味醇色秀，香馨持久',                [60, 50, 40], 22),
            ProductDef(18,'浮梁红茶',  '茶叶', '浮红',           68.0, '盒', '汤色红艳，蜜香甘醇',                [80, 60, 50], 15),

            # farmer_yu — 河南
            ProductDef(19,'信阳毛尖',  '茶叶', '信阳毛尖',       88.0, '盒', '细圆光直，清香扑鼻',                [100, 80, 60], 35),
            ProductDef(19,'温县铁棍山药','蔬菜','铁棍山药',      15.0, '斤', '药食同源，滋补佳品',                [150, 120, 100], 50),
            ProductDef(19,'新郑红枣',  '干货', '新郑灰枣',       20.0, '斤', '皮薄肉厚，甘甜如蜜',                [200, 150, 120], 55),

            # farmer_echu — 湖北
            ProductDef(20,'洪湖莲藕',  '蔬菜', '粉藕',           10.0, '斤', '粉糯拉丝，煲汤首选',                [200, 180, 150], 55),
            ProductDef(20,'恩施玉露',  '茶叶', '恩施玉露',       128.0,'盒', '蒸汽杀青，三绿特优',                [60, 50, 40], 20),
            ProductDef(20,'秭归脐橙',  '水果', '伦晚',           12.0, '斤', '晚熟品种，花果同枝',                [200, 150, 120], 65),

            # farmer_qiong — 海南
            ProductDef(21,'海南台农芒果','水果','台农',          16.0, '斤', '金黄香甜，无丝细嫩',                [200, 150, 120], 70),
            ProductDef(21,'桥头地瓜',  '蔬菜', '桥头地瓜',       8.0,  '斤', '粉糯香甜，板栗口感',                [250, 200, 150], 0),
            ProductDef(21,'兴隆咖啡',  '干货', '兴隆咖啡',       68.0, '盒', '炭烧风味，浓郁醇厚',                [80, 60, 50], 15),

            # farmer_gansu — 甘肃
            ProductDef(22,'兰州百合',  '蔬菜', '兰州百合',       38.0, '斤', '瓣大肉厚，清甜无苦',                [100, 80, 60], 20),
            ProductDef(22,'静宁苹果',  '水果', '红富士',         12.0, '斤', '黄土高原优生区，色泽艳丽',          [180, 150, 120], 65),
            ProductDef(22,'定西宽粉',  '干货', '马铃薯宽粉',     15.0, '袋', '晶莹爽滑，火锅必备',                [200, 150, 120], 0),

            # farmer_qinghai — 青海
            ProductDef(23,'柴达木红枸杞','干货','柴杞',           45.0, '斤', '粒大皮薄，甘甜无硫',                [100, 80, 60], 28),
            ProductDef(23,'青稞香米',  '粮油', '青稞',           25.0, '袋', '高原生态，营养丰富',                [150, 120, 100], 12),
            ProductDef(23,'门源菜籽油','粮油', '门源菜籽油',     28.0, '瓶', '高原油菜籽，物理压榨',              [120, 100, 80], 20),

            # farmer_neimeng — 内蒙古
            ProductDef(24,'锡林郭勒羔羊肉卷','干货','苏尼特羊',  48.0, '盒', '肉质鲜嫩，不膻不腻',                [80, 60, 50], 22),
            ProductDef(24,'河套雪花粉','粮油', '河套小麦',       25.0, '袋', '粉质细腻，面香浓郁',                [150, 120, 100], 30),
            ProductDef(24,'赤峰小米',  '粮油', '赤峰小米',       18.0, '斤', '金黄饱满，米油丰富',                [200, 150, 120], 0),

            # farmer_xizang — 西藏
            ProductDef(25,'林芝松茸',  '干货', '野生松茸',       268.0,'盒', '菌中之王，鲜香无比',                [20, 15, 10], 10),
            ProductDef(25,'藏红花',    '干货', '番红花',          88.0, '盒', '活血养血，高原珍品',                [15, 10, 8], 5),
            ProductDef(25,'青稞香米',  '粮油', '藏青稞',         28.0, '袋', '雪域高原，生态有机',                [100, 80, 60], 8),

            # farmer_ningxia — 宁夏
            ProductDef(26,'宁夏枸杞',  '干货', '宁杞7号',        35.0, '斤', '中国地理标志，甘甜饱满',            [200, 150, 120], 60),
            ProductDef(26,'盐池滩羊肉','干货', '盐池滩羊',       58.0, '盒', '肉质细嫩，不膻不腥',                [60, 50, 40], 15),
            ProductDef(26,'贺兰山葡萄酒','干货','赤霞珠',        88.0, '瓶', '果香浓郁，余味悠长',                [100, 80, 60], 25),

            # farmer_bj — 北京
            ProductDef(27,'平谷大桃',  '水果', '久保',           15.0, '斤', '个大鲜甜，汁水饱满',                [200, 150, 120], 75),
            ProductDef(27,'昌平草莓',  '水果', '红颜',           30.0, '盒', '色泽红润，奶香浓郁',                [100, 80, 60], 40),
            ProductDef(27,'京白梨',    '水果', '北京白梨',       12.0, '斤', '皮薄汁多，入口即化',                [120, 100, 80], 0),

            # farmer_tj — 天津
            ProductDef(28,'小站稻',    '粮油', '小站稻',         35.0, '袋', '宫廷贡米，晶莹剔透',                [150, 120, 100], 45),
            ProductDef(28,'沙窝萝卜',  '蔬菜', '沙窝萝卜',       8.0,  '斤', '脆甜多汁，赛梨',                    [200, 150, 120], 40),
            ProductDef(28,'茶淀葡萄',  '水果', '玫瑰香',         15.0, '斤', '甜酸适口，玫瑰芳香',                [150, 120, 100], 30),

            # farmer_sh — 上海
            ProductDef(29,'崇明生态米','粮油', '南粳46',         32.0, '袋', '生态岛种植，软糯甘甜',              [150, 120, 100], 30),
            ProductDef(29,'南汇水蜜桃','水果', '湖景蜜露',       22.0, '斤', '汁多味甜，桃香浓郁',                [100, 80, 60], 30),
            ProductDef(29,'崇明蟹',    '水产', '中华绒螯蟹',     68.0, '只', '生态养殖，膏满黄肥',                [100, 80, 60], 0),

            # farmer_cq — 重庆
            ProductDef(30,'涪陵榨菜',  '蔬菜', '榨菜',           5.0,  '斤', '中国地理标志，鲜香脆嫩',            [300, 250, 200], 120),
            ProductDef(30,'奉节脐橙',  '水果', '奉园72-1',       10.0, '斤', '果形端正，橙红艳丽',                [200, 150, 100], 70),
            ProductDef(30,'城口老腊肉','干货', '城口腊肉',       48.0, '盒', '高山生态猪，松柏熏制',              [60, 50, 40, 30], 15),

            # farmer_tw — 台湾
            ProductDef(31,'冻顶乌龙茶','茶叶', '冻顶乌龙',       168.0,'盒', '半球形包种茶，喉韵醇厚',            [50, 40, 30], 12),
            ProductDef(31,'凤梨',      '水果', '金钻凤梨',       25.0, '个', '肉嫩汁多，甜蜜无涩',                [150, 120, 100], 30),
            ProductDef(31,'金门高粱酒','干货', '58度高粱',        128.0,'瓶', '清香纯正，绵甜爽净',                [60, 50, 40], 15),

            # farmer_hk — 香港
            ProductDef(32,'有机菜心',  '蔬菜', '芥兰菜心',       15.0, '斤', '本地种植，鲜嫩脆甜',                [100, 80, 60], 10),
            ProductDef(32,'香港鸡蛋',  '干货', '鲜鸡蛋',         25.0, '盒', '本地农场，新鲜直送',                [200, 150, 120], 15),

            # farmer_mo — 澳门
            ProductDef(33,'澳门杏仁酥','干货', '杏仁饼',         38.0, '盒', '传统工艺，酥脆可口',                [150, 120, 100], 20),
            ProductDef(33,'澳门蛋卷',  '干货', '鸡蛋卷',         32.0, '盒', '香脆松化，蛋香浓郁',                [120, 100, 80], 0),
        ]
        products = []
        for d in product_defs:
            p = Product.objects.create(
                farmer=farmers[d.fi], name=d.name, category=d.cat,
                variety=d.variety, price=d.price, unit=d.unit,
                description=d.name + '，' + d.desc + '。原产地直供，品质保证。',
                status='approved',
            )
            products.append(p)
        self.stdout.write(f'  {len(products)} 个产品（已上架）')

        # ============================
        # 批次（每产品 2~5 个批次）
        # ============================
        # 按产品分类生成质检报告模板
        qc_templates = {
            '蔬菜': [
                '已通过农药残留检测，检测单位：{质检中心}',
                '符合绿色食品标准（NY/T 391-2021），无农残检出',
                '有机转换认证检测中，送检样品全部合格',
                '维生素及矿物质含量检测达标，膳食纤维≥2.5%',
            ],
            '水果': [
                '糖度≥{糖度}%，果径≥{果径}，一级果率≥95%',
                '农残及重金属检测均低于国家标准限值',
                '产地环境质量符合GB/T 18407.2标准',
                '无催熟剂、无防腐剂，自然成熟采摘',
            ],
            '茶叶': [
                '{国标}质量等级：特级',
                '欧盟农残标准检测全部合格，417项未检出',
                '茶多酚含量≥{茶多酚}%，氨基酸含量≥{氨基酸}%',
                '感官评审：外形匀整，汤色明亮，香气持久',
            ],
            '粮油': [
                '重金属及农残检测均低于国家标准限值',
                '水分含量≤14.5%，杂质率≤0.5%',
                '产地土壤环境质量符合GB 15618标准',
                '加工过程通过ISO 22000食品安全管理体系认证',
            ],
            '干货': [
                '水分≤{水分}%，等级：一级品',
                '二氧化硫残留量未检出，无硫熏蒸',
                '微生物指标符合GB 16325标准',
                '经人工精选，颗粒饱满度≥95%，杂质率≤0.1%',
            ],
            '水产': [
                '鲜活度检测：活力充沛，无异味',
                '重金属（铅、镉、汞、砷）检测均合格',
                '产地水域环境符合GB 11607渔业水质标准',
                '暂养时间≥48小时，已充分吐沙净化',
            ],
        }

        # 每省不同的质检机构
        cert_centers = {
            '山东': '寿光市农产品质检中心',
            '陕西': '洛川县果业质检中心',
            '福建': '武夷山市茶检中心',
            '湖南': '岳阳海关',
            '新疆': '阿克苏地区农检中心',
            '四川': '眉山市农产品检测中心',
            '云南': '普洱市茶叶质量检测中心',
            '广东': '茂名市农产品质检中心',
            '黑龙江': '五常市大米检测中心',
            '江苏': '苏州市农产品质量监测中心',
            '浙江': '杭州市茶叶研究院',
            '吉林': '白山市人参质检中心',
            '广西': '百色市农产品检测中心',
            '贵州': '遵义市农产品质检中心',
            '河北': '石家庄市农产品检测中心',
            '山西': '山西省农产品质检中心',
            '辽宁': '辽宁省盘锦市大米检测中心',
            '安徽': '安徽省黄山市茶叶质检中心',
            '江西': '赣州市脐橙检测中心',
            '河南': '河南省农产品质量检测中心',
            '湖北': '恩施州农产品质检中心',
            '海南': '海南省农产品检测中心',
            '甘肃': '甘肃省农产品质检中心',
            '青海': '青海省农产品检测中心',
            '内蒙古': '内蒙古自治区农畜产品质量检测中心',
            '西藏': '西藏自治区农产品质检中心',
            '宁夏': '宁夏回族自治区枸杞检测中心',
            '北京': '北京市农产品质量安全中心',
            '天津': '天津市农产品质检中心',
            '上海': '上海市农产品质量检测中心',
            '重庆': '重庆市农产品检测中心',
            '台湾': '台湾省农产品检验中心',
            '香港': '香港食物安全中心',
            '澳门': '澳门市政署化验所',
        }

        def get_qc(product, batch_idx):
            """按产品类型生成质检报告"""
            cat = product.category
            farmer_addr = product.farmer.address
            # 提取省份简称
            prov_key = ''
            for k in cert_centers:
                if farmer_addr.startswith(k):
                    prov_key = k
                    break
            center = cert_centers.get(prov_key, '省级农产品质检中心')

            # 水果糖度/果径按品种定
            if '苹果' in product.name:
                sugar, size = random.choice(['14', '15', '16']), random.choice(['80', '85', '90'])
            elif '橙' in product.name or '芒果' in product.name:
                sugar, size = random.choice(['12', '13', '14']), random.choice(['60', '65', '70'])
            else:
                sugar, size = '12', '70'

            if '龙井' in product.name or '碧螺春' in product.name or '翠芽' in product.name:
                standard = 'GB/T 18650'
                tp, aa = random.choice(['28', '30']), random.choice(['3.0', '3.5', '4.0'])
            elif '大红袍' in product.name:
                standard = 'GB/T 18745'
                tp, aa = random.choice(['22', '24']), random.choice(['2.5', '3.0'])
            elif '普洱茶' in product.name:
                standard = 'GB/T 22111'
                tp, aa = random.choice(['25', '28']), random.choice(['2.0', '2.5'])
            else:
                standard = 'GB/T 14456'
                tp, aa = '28', '3.0'

            if '红枣' in product.name:
                moisture = random.choice(['22', '25', '28'])
            elif '木耳' in product.name or '香菇' in product.name:
                moisture = random.choice(['12', '14'])
            elif '辣椒' in product.name:
                moisture = random.choice(['10', '12'])
            else:
                moisture = random.choice(['10', '12', '15'])

            templates = qc_templates.get(cat, ['质检合格（编号：QC-{随机号}）'])
            chosen = templates[batch_idx % len(templates)]
            return chosen.format(
                质检中心=center, 糖度=sugar, 果径=size,
                国标=standard, 茶多酚=tp, 氨基酸=aa, 水分=moisture,
                随机号=random.randint(10000, 99999),
            )

        batch_count = 0
        for idx, d in enumerate(product_defs):
            for bi, qty in enumerate(d.qtys):
                cat = products[idx].category
                # 溯源信息按品类丰富
                if cat == '蔬菜':
                    planting = random.choice(['温室大棚种植', '露天自然种植', '有机种植'])
                elif cat == '水果':
                    planting = random.choice(['果园生态种植', '山地梯田种植', '标准化果园种植'])
                elif cat == '茶叶':
                    planting = random.choice(['高山茶园种植', '有机茶园种植', '古茶树采摘'])
                elif cat == '粮油':
                    planting = random.choice(['生态稻田种植', '有机种植', '标准化种植'])
                elif cat == '干货':
                    planting = random.choice(['自然晾晒加工', '传统工艺制作', '标准化车间生产'])
                elif cat == '水产':
                    planting = random.choice(['湖面生态养殖', '标准化养殖基地', '天然水域捕捞'])
                else:
                    planting = '有机种植'

                harvest = (now - timedelta(days=random.randint(1, 120))).date()
                b = ProductBatch.objects.create(
                    product=products[idx],
                    quantity=qty,
                    harvest_date=harvest,
                    trace_info={
                        '产地': products[idx].farmer.address,
                        '种植方式': planting,
                        '采摘日期': harvest.isoformat(),
                    },
                    qc_report=[get_qc(products[idx], bi)],
                )
                batch_count += 1
        self.stdout.write(f'  {batch_count} 个批次（每产品 {len(d.qtys)}~{max(len(d.qtys) for d in product_defs)} 个批次）')

        # ============================
        # 订单
        # ============================
        regions = [
            '北京市朝阳区', '上海市浦东新区', '广州市天河区', '深圳市南山区',
            '杭州市西湖区', '成都市武侯区', '武汉市洪山区', '南京市鼓楼区',
            '西安市雁塔区', '重庆市渝中区', '长沙市岳麓区', '郑州市金水区',
            '天津市和平区', '青岛市市南区', '厦门市思明区',
            '大连市中山区', '昆明市五华区', '合肥市庐阳区',
            '石家庄市长安区', '海口市美兰区', '拉萨市城关区',
            '呼和浩特市赛罕区', '西宁市城中区', '银川市兴庆区',
            '太原市小店区', '南昌市东湖区', '贵阳市南明区',
            '兰州市城关区', '台北市大安区', '香港中环',
        ]
        status_choices = ['pending', 'paid_offline', 'confirmed', 'shipped', 'delivered', 'cancelled']

        # 构建 product → [batches] 映射
        from collections import defaultdict
        product_batches = defaultdict(list)
        for b in ProductBatch.objects.select_related('product').all():
            product_batches[b.product_id].append(b)
        # 按 product_defs 索引映射
        batch_map = {}
        for idx, p in enumerate(products):
            batch_map[idx] = product_batches.get(p.id, [])

        # 为目标销量生成订单项计划
        order_items_plan = []
        for idx, d in enumerate(product_defs):
            remaining = d.target
            while remaining > 0:
                qty = min(remaining, random.randint(1, 10))
                order_items_plan.append((idx, qty))
                remaining -= qty
        random.shuffle(order_items_plan)

        order_groups = []
        i = 0
        while i < len(order_items_plan):
            gs = min(random.randint(1, 5), len(order_items_plan) - i)
            order_groups.append(order_items_plan[i:i+gs])
            i += gs

        all_orders = []
        for group in order_groups:
            buyer = random.choice(consumers)
            days_ago = random.randint(5, 180)
            created = now - timedelta(days=days_ago)
            if days_ago > 60:
                st = random.choices(status_choices, weights=[0, 0, 0, 1, 12, 0])[0]
            elif days_ago > 30:
                st = random.choices(status_choices, weights=[1, 1, 1, 2, 8, 1])[0]
            else:
                st = random.choices(status_choices, weights=[3, 2, 1, 1, 3, 1])[0]
            order = Order.objects.create(
                buyer=buyer, total_amount=0, status=st, address=random.choice(regions)
            )
            total = 0
            for prod_idx, qty in group:
                batches = batch_map.get(prod_idx, [])
                if not batches:
                    continue
                bp = random.choice(batches)
                price = float(products[prod_idx].price)
                OrderItem.objects.create(order=order, product_batch=bp, quantity=qty, price=price)
                total += price * qty
            order.total_amount = total
            order.save()
            Order.objects.filter(pk=order.pk).update(created_at=created)
            all_orders.append(order)

        # 补充随机订单（选中 target=0 的待售产品以外的所有产品）
        no_sale_indices = {i for i, d in enumerate(product_defs) if d.target == 0}
        all_batches = [b for i, p in enumerate(products) for b in batch_map.get(i, []) if i not in no_sale_indices]
        if all_batches:
            for _ in range(15):
                buyer = random.choice(consumers)
                order = Order.objects.create(
                    buyer=buyer, total_amount=0,
                    status=random.choice(['shipped', 'delivered']),
                    address=random.choice(regions),
                )
                total = 0
                for _ in range(random.randint(1, 3)):
                    bp = random.choice(all_batches)
                    qty = random.randint(1, 5)
                    price = float(bp.product.price)
                    OrderItem.objects.create(order=order, product_batch=bp, quantity=qty, price=price)
                    total += price * qty
                order.total_amount = total
                order.save()

        self.stdout.write(f'  {len(all_orders)}+ 个已完成订单（时间跨度6个月）')

        # ============================
        # 评价
        # ============================
        comments = [
            '包装很好，水果新鲜！', '品质不错，物流很快',
            '第二次购买了，家人很喜欢', '价格实惠，还会回购',
            '口感很好，超出预期', '发货速度很快，包装严实',
            '和描述一致，好评', '性价比很高，推荐购买',
        ]
        cnt = 0
        for order in all_orders:
            if order.status == 'delivered' and order.items.count() > 0 and random.random() < 0.5:
                first_item = order.items.first()
                product = first_item.product_batch.product if first_item else None
                Review.objects.create(
                    order=order, buyer=order.buyer,
                    farmer=order.items.first().product_batch.product.farmer,
                    product=product,
                    rating=random.randint(3, 5),
                    comment=random.choice(comments),
                )
                cnt += 1
        self.stdout.write(f'  {cnt} 条评价')

        self.stdout.write(self.style.SUCCESS('\n=== 填充完成 ==='))
        self.stdout.write('  账号密码未改变')
        self.stdout.write(f'  覆盖 {len(farmers)} 个省份/地区的农户')
        self.stdout.write(f'  共 {len(products)} 个产品，{batch_count} 个批次')
