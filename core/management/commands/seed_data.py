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

        # === 34省合作社 ===
        coop_defs = [
            ('京郊绿源合作社', '北京市平谷区'), ('津门生态合作社', '天津市西青区'),
            ('燕赵农产品合作社', '河北省石家庄市'), ('三晋丰饶合作社', '山西省晋中市'),
            ('草原牧歌合作社', '内蒙古自治区呼和浩特市'), ('辽河明珠合作社', '辽宁省沈阳市'),
            ('长白山珍合作社', '吉林省长春市'), ('北大仓合作社', '黑龙江省哈尔滨市'),
            ('沪上鲜农合作社', '上海市浦东新区'), ('苏韵江南合作社', '江苏省南京市'),
            ('浙里鲜合作社', '浙江省杭州市'), ('徽乡源合作社', '安徽省合肥市'),
            ('八闽大地合作社', '福建省福州市'), ('赣鄱绿谷合作社', '江西省南昌市'),
            ('齐鲁农耕合作社', '山东省济南市'), ('中原粮仓合作社', '河南省郑州市'),
            ('荆楚鱼米合作社', '湖北省武汉市'), ('湘味源合作社', '湖南省长沙市'),
            ('岭南佳果合作社', '广东省广州市'), ('壮乡绿野合作社', '广西壮族自治区南宁市'),
            ('椰岛风情合作社', '海南省海口市'), ('巴渝山珍合作社', '重庆市渝北区'),
            ('天府之国合作社', '四川省成都市'), ('黔贵生态合作社', '贵州省贵阳市'),
            ('彩云之南合作社', '云南省昆明市'), ('雪域高原合作社', '西藏自治区拉萨市'),
            ('三秦大地合作社', '陕西省西安市'), ('陇上人家合作社', '甘肃省兰州市'),
            ('青海源合作社', '青海省西宁市'), ('塞上江南合作社', '宁夏回族自治区银川市'),
            ('西域绿洲合作社', '新疆维吾尔自治区乌鲁木齐市'), ('宝岛农会合作社', '台湾省台北市'),
            ('香江鲜农合作社', '香港特别行政区'), ('澳葡风情合作社', '澳门特别行政区'),
        ]
        coops = []
        for name, region in coop_defs:
            coop, _ = Cooperative.objects.get_or_create(name=name, defaults={'region': region, 'verified': True})
            coops.append(coop)
        self.stdout.write(f'  {len(coops)} 个合作社')

        # === 34省农户（get_or_create 保留已有账号密码） ===
        raw_farmers = [
            ('farmer_bj', 0, '北京市平谷区大华山镇'),
            ('farmer_tj', 1, '天津市西青区辛口镇'),
            ('farmer_he', 2, '河北省石家庄市赵县'),
            ('farmer_sx', 3, '山西省晋中市太谷区'),
            ('farmer_nmg', 4, '内蒙古自治区呼和浩特市武川县'),
            ('farmer_ln', 5, '辽宁省沈阳市辽中区'),
            ('farmer_jl', 6, '吉林省长春市农安县'),
            ('farmer_hlj', 7, '黑龙江省哈尔滨市五常市'),
            ('farmer_sh', 8, '上海市浦东新区南汇镇'),
            ('farmer_js', 9, '江苏省南京市溧水区'),
            ('farmer_zj', 10, '浙江省杭州市西湖区龙井村'),
            ('farmer_ah', 11, '安徽省合肥市巢湖市'),
            ('farmer_fj', 12, '福建省福州市武夷山市'),
            ('farmer_jx', 13, '江西省南昌市赣州市'),
            ('farmer_sd', 14, '山东省济南市章丘区'),
            ('farmer_hn', 15, '河南省郑州市新郑市'),
            ('farmer_hub', 16, '湖北省武汉市洪山区'),
            ('farmer_hun', 17, '湖南省长沙市岳阳市'),
            ('farmer_gd', 18, '广东省广州市增城区'),
            ('farmer_gx', 19, '广西壮族自治区南宁市武鸣区'),
            ('farmer_hain', 20, '海南省海口市文昌市'),
            ('farmer_cq', 21, '重庆市涪陵区'),
            ('farmer_sc', 22, '四川省成都市郫都区'),
            ('farmer_gz', 23, '贵州省贵阳市遵义市'),
            ('farmer_yn', 24, '云南省昆明市普洱市'),
            ('farmer_xz', 25, '西藏自治区拉萨市林芝市'),
            ('farmer_sax', 26, '陕西省西安市洛川县'),
            ('farmer_gs', 27, '甘肃省兰州市定西市'),
            ('farmer_qh', 28, '青海省西宁市海西州'),
            ('farmer_nx', 29, '宁夏回族自治区银川市中卫市'),
            ('farmer_xj', 30, '新疆维吾尔自治区乌鲁木齐市阿克苏地区'),
            ('farmer_tw', 31, '台湾省台北市南投县'),
            ('farmer_hk', 32, '香港特别行政区新界'),
            ('farmer_mo', 33, '澳门特别行政区路环'),
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

        # === 原5个demo农户确保存在（兼容已有账号） ===
        legacy_farmers = [
            ('farmer_wang', 14, '山东省寿光市孙家集街道'),
            ('farmer_li', 26, '陕西省洛川县旧县镇'),
            ('farmer_chen', 12, '福建省武夷山市星村镇'),
            ('farmer_zhang', 17, '湖南省岳阳市君山区'),
            ('farmer_zhao', 30, '新疆阿克苏地区温宿县'),
        ]
        for uname, ci, addr in legacy_farmers:
            user, created = User.objects.get_or_create(username=uname, defaults={'email': f'{uname}@test.com'})
            if created:
                user.set_password('demo123')
                user.save()
            fp, _ = FarmerProfile.objects.get_or_create(user=user, defaults={
                'phone': '1380000', 'address': addr, 'verified': True, 'cooperative': coops[ci]
            })

        # === 消费者（get_or_create 保留已有账号密码） ===
        consumer_names = [
            'consumer_zheng', 'consumer_wu', 'consumer_liu',
            'consumer_zhao', 'consumer_sun', 'consumer_qian',
            'consumer_zhou', 'consumer_ma', 'consumer_chen',
            'consumer_yang', 'consumer_huang', 'consumer_lin',
            'consumer_xu', 'consumer_he', 'consumer_gao',
        ]
        consumers = []
        for name in consumer_names:
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

        # === 产品（34省 × 2-3个当地特色产品 ≈ 90个） ===
        # 格式: (farmer_index, name, category, variety, price, unit, description)
        product_data = [
            # 1. 北京市 (farmer_bj=0)
            (0, '平谷大桃', '水果', '大久保', 18.0, '斤', '北京市平谷区特产，果肉细腻多汁，甜度高'),
            (0, '京白梨', '水果', '秋子梨', 15.0, '斤', '北京传统名果，皮薄肉细，清甜爽口'),
            # 2. 天津市 (farmer_tj=1)
            (1, '沙窝萝卜', '蔬菜', '卫青', 6.0, '斤', '天津沙窝特产，脆甜多汁，赛鸭梨'),
            (1, '茶淀玫瑰香葡萄', '水果', '玫瑰香', 22.0, '斤', '天津茶淀特产，玫瑰香气浓郁，甜而不腻'),
            (1, '小站稻', '粮油', '津优1号', 8.0, '斤', '天津小站贡米，晶莹剔透，香糯可口'),
            # 3. 河北省 (farmer_he=2)
            (2, '赵县雪梨', '水果', '雪花梨', 10.0, '斤', '河北赵县特产，汁多渣少，润肺止咳'),
            (2, '沧州金丝小枣', '干货', '金丝枣', 28.0, '斤', '沧州特产，皮薄肉厚，含糖量高'),
            (2, '迁西板栗', '干货', '京东板栗', 16.0, '斤', '河北迁西特产，香甜软糯'),
            # 4. 山西省 (farmer_sx=3)
            (3, '沁州黄小米', '粮油', '沁州黄', 12.0, '斤', '山西沁县特产，四大名米之一，营养丰富'),
            (3, '山西核桃', '干货', '晋龙1号', 25.0, '斤', '山西汾阳特产，皮薄仁满，出油率高'),
            (3, '山西老陈醋', '粮油', '宁化府', 15.0, '瓶', '山西太原特产，酸香醇厚，百年传承'),
            # 5. 内蒙古自治区 (farmer_nmg=4)
            (4, '乌兰察布马铃薯', '蔬菜', '克新1号', 4.0, '斤', '内蒙古特产，个大质优，全国马铃薯之都'),
            (4, '河套雪花粉', '粮油', '永良4号', 12.0, '袋', '巴彦淖尔河套地区特产，面粉筋道'),
            (4, '科尔沁风干牛肉', '畜禽', '西门塔尔', 88.0, '袋', '内蒙古科尔沁草原特产，肉质紧实'),
            # 6. 辽宁省 (farmer_ln=5)
            (5, '大连樱桃', '水果', '美早', 58.0, '斤', '大连特产，个大味甜，温室种植品质佳'),
            (5, '盘锦蟹田大米', '粮油', '盐丰47', 18.0, '袋', '辽宁盘锦特产，蟹稻共生，米香浓郁'),
            (5, '丹东久久草莓', '水果', '红颜', 35.0, '斤', '丹东特产，个大色红，香甜多汁'),
            # 7. 吉林省 (farmer_jl=6)
            (6, '吉林大米', '粮油', '稻花香2号', 15.0, '袋', '吉林特产，黑土地孕育，口感软糯'),
            (6, '长白山人参', '干货', '西洋参', 168.0, '盒', '吉林长白山特产，补气佳品'),
            (6, '长白山黑木耳', '干货', '黑山', 55.0, '斤', '吉林长白山特产，肉厚脆嫩'),
            # 8. 黑龙江省 (farmer_hlj=7)
            (7, '五常大米', '粮油', '稻花香2号', 25.0, '袋', '黑龙江五常特产，中国最好吃的大米'),
            (7, '哈尔滨红肠', '畜禽', '秋林', 35.0, '袋', '哈尔滨特产，蒜香浓郁，烟熏风味'),
            (7, '大兴安岭蓝莓', '水果', '北陆', 45.0, '斤', '黑龙江大兴安岭特产，花青素含量高'),
            # 9. 上海市 (farmer_sh=8)
            (8, '南汇水蜜桃', '水果', '大团蜜露', 25.0, '斤', '上海南汇特产，皮薄汁多，入口即化'),
            (8, '崇明生态米', '粮油', '南粳46', 12.0, '袋', '上海崇明岛特产，生态种植，清香软糯'),
            # 10. 江苏省 (farmer_js=9)
            (9, '阳澄湖大闸蟹', '畜禽', '中华绒螯蟹', 128.0, '只', '苏州阳澄湖特产，蟹黄饱满，鲜香无比'),
            (9, '洞庭碧螺春', '茶叶', '碧螺春', 288.0, '盒', '苏州洞庭山特产，卷曲如螺，清香甘醇'),
            (9, '南京盐水鸭', '畜禽', '麻鸭', 45.0, '只', '南京特产，皮白肉嫩，咸香适口'),
            # 11. 浙江省 (farmer_zj=10)
            (10, '西湖龙井', '茶叶', '龙井43号', 388.0, '盒', '杭州西湖特产，色绿香郁，味甘形美'),
            (10, '金华火腿', '畜禽', '两头乌', 198.0, '只', '浙江金华特产，三年陈酿，鲜香浓郁'),
            (10, '临安山核桃', '干货', '薄壳', 48.0, '斤', '浙江临安特产，壳薄肉香，营养丰富'),
            # 12. 安徽省 (farmer_ah=11)
            (11, '黄山毛峰', '茶叶', '毛峰', 158.0, '盒', '安徽黄山特产，形似雀舌，清香回甘'),
            (11, '砀山酥梨', '水果', '酥梨', 8.0, '斤', '安徽砀山特产，酥脆多汁，润肺止咳'),
            (11, '霍山石斛', '干货', '铁皮石斛', 388.0, '盒', '安徽霍山特产，九大仙草之首，养生佳品'),
            # 13. 福建省 (farmer_fj=12)
            (12, '大红袍茶叶', '茶叶', '大红袍', 588.0, '盒', '武夷山特产，岩骨花香，茶中之王'),
            (12, '琯溪蜜柚', '水果', '琯溪蜜柚', 12.0, '个', '福建平和特产，汁多味甜，润肺佳品'),
            (12, '福州茉莉花茶', '茶叶', '茉莉花茶', 88.0, '盒', '福州特产，花香茶韵，百年窨制工艺'),
            # 14. 江西省 (farmer_jx=13)
            (13, '赣南脐橙', '水果', '纽荷尔', 10.0, '斤', '江西赣州特产，汁多味甜，中国名橙'),
            (13, '庐山云雾茶', '茶叶', '云雾', 128.0, '盒', '江西庐山特产，高山云雾出好茶'),
            (13, '鄱阳湖大米', '粮油', '赣晚籼', 8.0, '袋', '江西鄱阳湖特产，湖水灌溉，米质优良'),
            # 15. 山东省 (farmer_sd=14)
            (14, '烟台苹果', '水果', '红富士', 9.0, '斤', '山东烟台特产，脆甜多汁，中国苹果之都'),
            (14, '潍坊萝卜', '蔬菜', '潍县青', 4.0, '斤', '山东潍坊特产，脆嫩清甜，水果萝卜'),
            (14, '章丘大葱', '蔬菜', '大梧桐', 5.0, '斤', '山东章丘特产，葱白长而脆嫩'),
            # 16. 河南省 (farmer_hn=15)
            (15, '信阳毛尖', '茶叶', '毛尖', 98.0, '盒', '河南信阳特产，细圆光直，香高味醇'),
            (15, '新郑红枣', '干货', '新郑灰枣', 22.0, '斤', '河南新郑特产，皮薄肉厚核小'),
            (15, '温县铁棍山药', '蔬菜', '铁棍', 18.0, '斤', '河南温县特产，药食同源，健脾养胃'),
            # 17. 湖北省 (farmer_hub=16)
            (16, '洪湖莲藕', '蔬菜', '鄂莲', 8.0, '斤', '湖北洪湖特产，粉糯清甜，煲汤佳品'),
            (16, '恩施玉露', '茶叶', '玉露', 168.0, '盒', '湖北恩施特产，蒸青绿茶，富硒健康'),
            (16, '秭归脐橙', '水果', '秭归脐橙', 12.0, '斤', '湖北秭归特产，屈原故里，甜蜜多汁'),
            # 18. 湖南省 (farmer_hun=17)
            (17, '君山银针', '茶叶', '银针', 198.0, '盒', '湖南岳阳特产，黄茶之冠，三起三落'),
            (17, '湘西猕猴桃', '水果', '米良1号', 12.0, '斤', '湖南湘西特产，维C之王，酸甜可口'),
            (17, '洞庭湖大米', '粮油', '湘晚籼', 9.0, '袋', '湖南洞庭湖区特产，鱼米之乡'),
            # 19. 广东省 (farmer_gd=18)
            (18, '增城荔枝', '水果', '挂绿', 38.0, '斤', '广东增城特产，壳红肉白，清甜多汁'),
            (18, '潮州凤凰单丛', '茶叶', '鸭屎香', 268.0, '盒', '广东潮州特产，香气高扬，回甘悠长'),
            (18, '新会陈皮', '干货', '大红柑', 88.0, '盒', '广东新会特产，陈久者良，理气健脾'),
            # 20. 广西壮族自治区 (farmer_gx=19)
            (19, '容县沙田柚', '水果', '沙田柚', 15.0, '个', '广西容县特产，柚中之王，甜脆无渣'),
            (19, '梧州六堡茶', '茶叶', '六堡', 128.0, '盒', '广西梧州特产，越陈越香，祛湿养胃'),
            (19, '百色芒果', '水果', '台农1号', 20.0, '斤', '广西百色特产，芒果之乡，香甜浓郁'),
            # 21. 海南省 (farmer_hain=20)
            (20, '文昌鸡', '畜禽', '文昌鸡', 68.0, '只', '海南文昌特产，皮脆肉嫩，四大名鸡'),
            (20, '海南芒果', '水果', '贵妃芒', 18.0, '斤', '海南特产热带水果，甜度高口感好'),
            (20, '桥头地瓜', '蔬菜', '桥头', 5.0, '斤', '海南澄迈特产，富硒沙地种植，粉糯香甜'),
            # 22. 重庆市 (farmer_cq=21)
            (21, '涪陵榨菜', '蔬菜', '涪杂2号', 6.0, '袋', '重庆涪陵特产，鲜香脆嫩，佐餐佳品'),
            (21, '奉节脐橙', '水果', '奉节72-1', 10.0, '斤', '重庆奉节特产，汁多味甜，三峡名果'),
            (21, '城口老腊肉', '畜禽', '城口土猪', 68.0, '斤', '重庆城口特产，柏枝熏制，腊香浓郁'),
            # 23. 四川省 (farmer_sc=22)
            (22, '郫县豆瓣', '干货', '红油豆瓣', 15.0, '瓶', '四川郫县特产，川菜之魂，三年陈酿'),
            (22, '汉源花椒', '干货', '大红袍花椒', 45.0, '斤', '四川汉源特产，色泽红润，麻香浓郁'),
            (22, '竹叶青茶', '茶叶', '竹叶青', 188.0, '盒', '四川峨眉山特产，形似竹叶，清香宜人'),
            # 24. 贵州省 (farmer_gz=23)
            (23, '都匀毛尖', '茶叶', '毛尖', 138.0, '盒', '贵州都匀特产，卷曲披毫，香清味醇'),
            (23, '茅台镇酱酒', '粮油', '酱香型', 398.0, '瓶', '贵州茅台镇特产，酱香突出，幽雅细腻'),
            (23, '威宁荞麦', '粮油', '苦荞', 10.0, '斤', '贵州威宁特产，高原苦荞，降糖佳品'),
            # 25. 云南省 (farmer_yn=24)
            (24, '普洱茶', '茶叶', '大叶种', 158.0, '饼', '云南普洱特产，越陈越香，降脂减肥'),
            (24, '昭通苹果', '水果', '红富士', 8.0, '斤', '云南昭通特产，高原苹果，脆甜多汁'),
            (24, '文山三七', '干货', '春三七', 298.0, '盒', '云南文山特产，活血化瘀，金不换'),
            # 26. 西藏自治区 (farmer_xz=25)
            (25, '林芝松茸', '干货', '松茸', 588.0, '斤', '西藏林芝特产，高原珍菌，香气独特'),
            (25, '青稞香米', '粮油', '藏青2000', 12.0, '斤', '西藏特产高原谷物，β-葡聚糖含量高'),
            (25, '藏红花', '干货', '藏红花', 288.0, '克', '西藏特产，活血养颜，花中黄金'),
            # 27. 陕西省 (farmer_sax=26)
            (26, '洛川苹果', '水果', '红富士', 12.0, '斤', '陕西洛川特产，黄土高原苹果，脆甜耐贮'),
            (26, '汉中仙毫', '茶叶', '仙毫', 168.0, '盒', '陕西汉中专产，秦巴高山茶，清香回甘'),
            (26, '秦岭土蜂蜜', '干货', '百花蜜', 68.0, '瓶', '陕西秦岭特产，百花酿造，天然纯净'),
            # 28. 甘肃省 (farmer_gs=27)
            (27, '兰州百合', '蔬菜', '兰州百合', 35.0, '斤', '甘肃兰州特产，瓣大肉厚，清甜无苦'),
            (27, '静宁苹果', '水果', '红富士', 10.0, '斤', '甘肃静宁特产，高原有机，脆甜耐放'),
            (27, '定西宽粉', '干货', '马铃薯粉', 8.0, '袋', '甘肃定西特产，Q弹爽滑，火锅必备'),
            # 29. 青海省 (farmer_qh=28)
            (28, '柴达木红枸杞', '干货', '宁杞7号', 58.0, '斤', '青海柴达木特产，高原枸杞，颗粒饱满'),
            (28, '青海牦牛肉干', '畜禽', '高原牦牛', 98.0, '袋', '青海特产高原牦牛，肉质鲜美有嚼劲'),
            (28, '门源菜籽油', '粮油', '小油菜', 25.0, '瓶', '青海门源特产，高原冷榨，醇香浓厚'),
            # 30. 宁夏回族自治区 (farmer_nx=29)
            (29, '宁夏枸杞', '干货', '宁杞1号', 65.0, '斤', '宁夏中宁特产，世界枸杞之都，粒大籽小'),
            (29, '盐池滩羊肉', '畜禽', '滩羊', 88.0, '斤', '宁夏盐池特产，不膻不腻，鲜嫩可口'),
            (29, '贺兰山东麓葡萄酒', '粮油', '赤霞珠', 168.0, '瓶', '宁夏贺兰山特产，世界优质葡萄酒产区'),
            # 31. 新疆维吾尔自治区 (farmer_xj=30)
            (30, '阿克苏冰糖心苹果', '水果', '冰糖心', 15.0, '斤', '新疆阿克苏特产，糖心明显，甜度极高'),
            (30, '哈密瓜', '水果', '西州蜜', 12.0, '个', '新疆哈密特产，香气浓郁，甜蜜多汁'),
            (30, '新疆红枣', '干货', '骏枣', 25.0, '斤', '新疆特产，日照充足，枣大核小'),
            # 32. 台湾省 (farmer_tw=31)
            (31, '冻顶乌龙茶', '茶叶', '冻顶', 188.0, '盒', '台湾南投特产，喉韵醇厚，炭焙香浓'),
            (31, '金门高粱酒', '粮油', '高粱酒', 258.0, '瓶', '台湾金门特产，清香甘冽，纯粮酿造'),
            (31, '台湾凤梨', '水果', '金钻', 16.0, '个', '台湾特产，果肉金黄，酸甜多汁'),
            # 33. 香港特别行政区 (farmer_hk=32)
            (32, '元朗老婆饼', '粮油', '传统手工', 28.0, '盒', '香港元朗特产，皮酥馅软，传统美味'),
            (32, '有机菜心', '蔬菜', '本地菜心', 12.0, '斤', '香港本地有机种植，清甜脆嫩'),
            # 34. 澳门特别行政区 (farmer_mo=33)
            (33, '澳门杏仁饼', '干货', '杏仁饼', 35.0, '盒', '澳门特产手信，酥脆杏仁香'),
            (33, '澳门蛋卷', '干货', '手工蛋卷', 28.0, '盒', '澳门特产，酥脆蛋香，手工制作'),
        ]
        products = []
        for idx, (fi, name, cat, variety, price, unit, desc) in enumerate(product_data):
            p = Product.objects.create(
                farmer=farmers[fi], name=name, category=cat,
                variety=variety, price=price, unit=unit,
                description=desc, status='approved'
            )
            products.append(p)
        self.stdout.write(f'  {len(products)} 个产品（已上架，覆盖{len(set(fi for fi,_,_,_,_,_,_ in product_data))}省）')

        # === 批次（每产品2-5个批次，动态生成） ===
        qc_templates = {
            '蔬菜': [
                '已通过农药残留检测，检测单位：当地农产品质检中心',
                '符合绿色食品标准（NY/T 391-2021），无农残检出',
                '有机转换认证检测中，送检样品全部合格',
                '蔬菜类重金属及农残检测均低于国家标准限值',
            ],
            '水果': [
                '经检测，糖度≥14%，果径达标，一级果率96%',
                '水果类农残检测全部合格，符合绿色食品标准',
                '糖度及酸度检测达标，口感品质一级',
                '地理标志产品质量检测合格',
            ],
            '茶叶': [
                '国家标准（GB/T）质量等级：特级',
                '经欧盟农残标准检测全部合格',
                '茶叶类重金属及农残检测均低于国家标准限值',
                '地理标志保护产品，原产地认证',
            ],
            '粮油': [
                '重金属及农残检测均低于国家标准限值',
                '质量等级：一级，碎米率≤5%，水分≤14.5%',
                '产品符合国家粮食安全标准',
            ],
            '干货': [
                '二氧化硫检测合格，符合食品安全标准',
                '地理标志产品质量检测合格，颗粒饱满度≥95%',
                '水分含量达标，无添加防腐剂',
            ],
            '畜禽': [
                '兽药残留检测合格，检疫合格证明齐全',
                '通过动物产品检疫，符合国家食品安全标准',
                '无注水、无激素添加，肉质检测合格',
            ],
        }

        batch_qtys = []
        target_solds = []
        n = len(products)
        # ~12% 产品为待售（至少1个，至多 n//8）
        unsold_count = max(1, min(n // 8, int(n * 0.12)))
        unsold_indices = set(random.sample(range(n), unsold_count))

        for i in range(n):
            qty = random.randint(50, 300)
            batch_qtys.append(qty)
            if i in unsold_indices:
                target_solds.append(0)
            else:
                ratio = random.choice([0.25, 0.4, 0.55, 0.7, 0.85, 0.95, 1.1, 1.5, 2.0])
                target_solds.append(max(1, int(qty * ratio)))

        batch_map = {}
        total_batches = 0
        for idx in range(n):
            cat = products[idx].category
            qc_list = qc_templates.get(cat, qc_templates['蔬菜'])
            num_batches = random.randint(2, 5)
            batch_list = []
            for bi in range(num_batches):
                b = ProductBatch.objects.create(
                    product=products[idx],
                    quantity=random.randint(30, 250),
                    harvest_date=(now - timedelta(days=random.randint(1, 180))).date(),
                    trace_info={
                        '产地': products[idx].farmer.address,
                        '种植方式': random.choice(['有机种植', '绿色种植', '传统种植', '生态种植']),
                        '批次号': bi + 1,
                    },
                    qc_report=random.choice(qc_list),
                )
                batch_list.append(b)
                total_batches += 1
            batch_map[idx] = batch_list
        self.stdout.write(f'  {total_batches} 个批次（{unsold_count} 个待售产品，每产品2-5批）')

        # === 订单（动态生成，逻辑同前） ===
        regions = [
            '北京市朝阳区', '上海市浦东新区', '广州市天河区', '深圳市南山区',
            '杭州市西湖区', '成都市武侯区', '武汉市洪山区', '南京市鼓楼区',
            '重庆市渝中区', '西安市雁塔区', '长沙市岳麓区', '郑州市金水区',
            '济南市历下区', '福州市鼓楼区', '昆明市五华区', '南宁市青秀区',
            '哈尔滨市南岗区', '长春市南关区', '沈阳市和平区', '合肥市蜀山区',
            '南昌市东湖区', '贵阳市云岩区', '兰州市城关区', '太原市小店区',
            '石家庄市长安区', '呼和浩特市赛罕区', '乌鲁木齐市天山区',
            '拉萨市城关区', '西宁市城中区', '银川市金凤区',
            '海口市龙华区', '天津市南开区',
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
        no_sale_idx = {i for i, t in enumerate(target_solds) if t == 0}
        random_batches = [b for i, bs in batch_map.items() if i not in no_sale_idx for b in bs]
        extra_order_count = max(20, len(products) * 4)
        for _ in range(extra_order_count):
            buyer = random.choice(consumers)
            order = Order.objects.create(buyer=buyer, total_amount=0,
                status=random.choice(['shipped','delivered']), address=random.choice(regions))
            total = 0
            for _ in range(random.randint(1, 3)):
                bp = random.choice(random_batches)
                qty = random.randint(1, 5)
                price = float(bp.product.price)
                OrderItem.objects.create(order=order, product_batch=bp, quantity=qty, price=price)
                total += price * qty
            order.total_amount = total
            order.save()

        self.stdout.write(f'  {len(all_orders)} 个订单（时间跨度6个月）')

        # === 评价（覆盖60%已送达订单） ===
        comments = [
            '包装很好，水果新鲜！', '品质不错，物流很快',
            '第二次购买了，家人很喜欢', '价格实惠，还会回购',
            '产地直发，非常满意', '比超市买的更新鲜',
            '物流包装需要改进', '口感很好，推荐购买',
            '性价比很高，支持农户', '新鲜度一般，但总体还行',
            '非常满意，和描述一致', '发货速度快，品质好',
            '农产品很新鲜，点赞', '好评，下次还来',
        ]
        cnt = 0
        for order in all_orders:
            if order.status == 'delivered' and order.items.count() > 0 and random.random() < 0.6:
                Review.objects.create(order=order, buyer=order.buyer,
                    farmer=order.items.first().product_batch.product.farmer,
                    rating=random.randint(3, 5), comment=random.choice(comments))
                cnt += 1
        self.stdout.write(f'  {cnt} 条评价')

        self.stdout.write(self.style.SUCCESS('\n=== 填充完成 ==='))
        self.stdout.write('  账号密码未改变')
        self.stdout.write(f'  覆盖 {len(coops)} 省合作社 / {len(farmers)} 农户 / {len(products)} 产品 / {total_batches} 批次')
