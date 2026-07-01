"""seed_data 管理命令 — 填充演示数据（不会删除用户账号）"""
import random
from datetime import datetime, timedelta
from django.core.management.base import BaseCommand
from django.contrib.auth.models import User
from accounts.models import FarmerProfile
from products.models import Product, ProductBatch, Review, generate_batch_code
from trade.models import Order, OrderItem, Cart, CartItem, Favorite
from marketplace.models import SupplyDemandPost
from knowledge.models import FarmingGuide
from preorder.models import PreOrderCampaign
from core.models import Training


class Command(BaseCommand):
    help = '填充演示数据（不会删除用户账号）'

    def handle(self, *args, **options):
        # 只删除临时数据（订单/购物车/评价等），产品和批次使用 get_or_create 保留用户数据
        Order.objects.all().delete()
        OrderItem.objects.all().delete()
        Review.objects.all().delete()
        Cart.objects.all().delete()
        CartItem.objects.all().delete()
        OrderItem.objects.all().delete()
        Review.objects.all().delete()
        SupplyDemandPost.objects.all().delete()
        FarmingGuide.objects.all().delete()
        PreOrderCampaign.objects.all().delete()
        Training.objects.all().delete()
        Cart.objects.all().delete()
        CartItem.objects.all().delete()
        Favorite.objects.all().delete()

        now = datetime.now()

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
        for uname, _, addr in raw_farmers:
            user, created = User.objects.get_or_create(username=uname, defaults={'email': f'{uname}@test.com'})
            if created:
                user.set_password('demo123')
                user.save()
            fp, _ = FarmerProfile.objects.get_or_create(user=user, defaults={
                'phone': '1380000', 'address': addr, 'verified': True
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
        for uname, _, addr in legacy_farmers:
            user, created = User.objects.get_or_create(username=uname, defaults={'email': f'{uname}@test.com'})
            if created:
                user.set_password('demo123')
                user.save()
            fp, _ = FarmerProfile.objects.get_or_create(user=user, defaults={
                'phone': '1380000', 'address': addr, 'verified': True
            })

        # === 消费者（get_or_create 保留已有账号密码） ===
        consumer_names = [
            'consumer_zheng', 'consumer_wu', 'consumer_liu',
            'consumer_zhao', 'consumer_sun', 'consumer_qian',
            'consumer_zhou', 'consumer_ma', 'consumer_chen',
            'consumer_yang', 'consumer_huang', 'consumer_lin',
            'consumer_xu', 'consumer_he', 'consumer_gao',
            'consumer_wei', 'consumer_jiang', 'consumer_peng',
            'consumer_fang', 'consumer_shang',
        ]
        consumers = []
        for name in consumer_names:
            user, created = User.objects.get_or_create(username=name, defaults={'email': f'{name}@test.com'})
            if created:
                user.set_password('demo123')
                user.save()
            consumers.append(user)
        self.stdout.write(f'  {len(consumers)} 个消费者')

        # === 农场故事 + 照片（丰富5个典型农户的店铺页） ===
        farm_stories_data = [
            (farmers[7],  # 黑龙江五常
             '我家三代种植水稻，这片黑土地养育了我们。从爷爷那辈起，我们就坚持传统农耕方式——施农家肥、人工除草、稻鸭共作。'
             '每年10月，金灿灿的稻穗弯下腰的时候，是一年中最幸福的时刻。我们的大米，每一粒都带着黑土地的诚意。'
             '欢迎来五常做客，品尝真正的稻花香。',
             ['https://images.unsplash.com/photo-1574323347407-f5e1ad6d020b?w=600',  # 稻田
              'https://images.unsplash.com/photo-1536052954887-fd25a05b61e3?w=600',  # 水稻
              'https://images.unsplash.com/photo-1586444248902-2f64eddc13df?w=600']),  # 农田
            (farmers[12],  # 福建武夷山
             '武夷山的云雾里长出来的茶，天生带着岩骨花香。我家的茶园坐落在海拔800米的岩壁间，'
             '茶树扎根于丹霞地貌的风化岩中，吸收了岩石的矿物质和山间的云雾精华。'
             '从采摘到炭焙，每一道工序都是祖传手艺。我们不做量产，只做好茶。',
             ['https://images.unsplash.com/photo-1563822249366-3efb23b8e0c9?w=600',  # 茶园
              'https://images.unsplash.com/photo-1597318181409-cf64d0b5d8a2?w=600',
              'https://images.unsplash.com/photo-1544787219-7f47ccb76574?w=600']),
            (farmers[22],  # 四川郫县
             '郫县豆瓣，川菜之魂。我家的豆瓣酱选用优质蚕豆和二荆条辣椒，在百年老缸里自然发酵。'
             '每天翻缸、晒露，365天从不间断。三年陈酿的豆瓣酱，色泽红润、酱香浓郁，是正宗川菜的灵魂。'
             '我们坚持古法酿造，让每一勺豆瓣酱都能带你回味儿时的川味。',
             ['https://images.unsplash.com/photo-1571757760251-7ed249121e04?w=600',
              'https://images.unsplash.com/photo-1504674900247-0877df9cc836?w=600',
              'https://images.unsplash.com/photo-1555939594-58d7cb561ad1?w=600']),
            (farmers[29],  # 宁夏中卫
             '宁夏枸杞甲天下，中宁枸杞甲宁夏。我们地处黄河灌区，光照充足、昼夜温差大，'
             '种出来的枸杞个大、籽少、肉厚、味甜。每一颗都是手工采摘、自然晾晒，'
             '锁住了枸杞最原始的营养和甘甜。泡一杯枸杞水，红润透亮，是来自塞上江南的健康问候。',
             ['https://images.unsplash.com/photo-1587132137056-bfbf0166836e?w=600',
              'https://images.unsplash.com/photo-1571771891175-bfce4c3e8bf6?w=600',
              'https://images.unsplash.com/photo-1546549032-1f3e0e16bb91?w=600']),
            (farmers[0],  # 北京平谷
             '平谷大桃，北京人的夏天记忆。我家桃园位于大华山镇核心产区，沙质土壤、充足光照，'
             '每一颗桃子都经过精心修剪和套袋保护。从6月到9月，不同品种接力成熟，'
             '大久保、绿化九、蟠桃……咬一口，甜汁顺着嘴角流下来的幸福感，就是平谷的味道。'
             '欢迎来桃园采摘，感受京郊田园之乐。',
             ['https://images.unsplash.com/photo-1551773184-6307854fa8b9?w=600',
              'https://images.unsplash.com/photo-1523049673857-eb18f1d7b578?w=600',
              'https://images.unsplash.com/photo-1595981267035-7b04ca84a6fd?w=600']),
        ]
        for fp, story, photos in farm_stories_data:
            fp.farm_story = story
            fp.farm_photos = photos
            fp.save(update_fields=['farm_story', 'farm_photos'])
        self.stdout.write(f'  已为 {len(farm_stories_data)} 个农户添加农场故事和照片')

        # === 管理员（确保存在） ===
        admin, created = User.objects.get_or_create(username='demo_admin', defaults={
            'email': 'admin@test.com', 'is_staff': True, 'is_superuser': True
        })
        if created:
            admin.set_password('DemoPass#2026')
            admin.save()

        # === 产品（34省 × 2-3个当地特色产品 ≈ 90个） ===
        # 格式: (farmer_index, name, category, variety, price, unit, description)
        # 产品分布有参差：大农业省5个，中等4个，常规3个，小省2个，特区1个
        product_data = [
            # 1. 北京市 (2个)
            (0, '平谷大桃', '水果', '大久保', 18.0, '斤', '北京市平谷区特产，果肉细腻多汁，甜度高'),
            (0, '京白梨', '水果', '秋子梨', 15.0, '斤', '北京传统名果，皮薄肉细，清甜爽口'),
            # 2. 天津市 (2个)
            (1, '沙窝萝卜', '蔬菜', '卫青', 6.0, '斤', '天津沙窝特产，脆甜多汁，赛鸭梨'),
            (1, '小站稻', '粮油', '津优1号', 8.0, '斤', '天津小站贡米，晶莹剔透，香糯可口'),
            # 3. 河北省 (4个) ★
            (2, '赵县雪梨', '水果', '雪花梨', 10.0, '斤', '河北赵县特产，汁多渣少，润肺止咳'),
            (2, '沧州金丝小枣', '干货', '金丝枣', 28.0, '斤', '沧州特产，皮薄肉厚，含糖量高'),
            (2, '迁西板栗', '干货', '京东板栗', 16.0, '斤', '河北迁西特产，香甜软糯'),
            (2, '张家口燕麦', '粮油', '坝莜1号', 12.0, '袋', '张家口坝上特产，高寒燕麦，β-葡聚糖丰富'),
            # 4. 山西省 (3个)
            (3, '沁州黄小米', '粮油', '沁州黄', 12.0, '斤', '山西沁县特产，四大名米之一，营养丰富'),
            (3, '山西核桃', '干货', '晋龙1号', 25.0, '斤', '山西汾阳特产，皮薄仁满，出油率高'),
            (3, '山西老陈醋', '粮油', '宁化府', 15.0, '瓶', '山西太原特产，酸香醇厚，百年传承'),
            # 5. 内蒙古自治区 (3个)
            (4, '乌兰察布马铃薯', '蔬菜', '克新1号', 4.0, '斤', '内蒙古特产，个大质优，全国马铃薯之都'),
            (4, '河套雪花粉', '粮油', '永良4号', 12.0, '袋', '巴彦淖尔河套地区特产，面粉筋道'),
            (4, '科尔沁风干牛肉', '畜禽', '西门塔尔', 88.0, '袋', '内蒙古科尔沁草原特产，肉质紧实'),
            # 6. 辽宁省 (3个)
            (5, '大连樱桃', '水果', '美早', 58.0, '斤', '大连特产，个大味甜，温室种植品质佳'),
            (5, '盘锦蟹田大米', '粮油', '盐丰47', 18.0, '袋', '辽宁盘锦特产，蟹稻共生，米香浓郁'),
            (5, '丹东久久草莓', '水果', '红颜', 35.0, '斤', '丹东特产，个大色红，香甜多汁'),
            # 7. 吉林省 (3个)
            (6, '吉林大米', '粮油', '稻花香2号', 15.0, '袋', '吉林特产，黑土地孕育，口感软糯'),
            (6, '长白山人参', '干货', '西洋参', 168.0, '盒', '吉林长白山特产，补气佳品'),
            (6, '长白山黑木耳', '干货', '黑山', 55.0, '斤', '吉林长白山特产，肉厚脆嫩'),
            # 8. 黑龙江省 (3个)
            (7, '五常大米', '粮油', '稻花香2号', 25.0, '袋', '黑龙江五常特产，中国最好吃的大米'),
            (7, '哈尔滨红肠', '畜禽', '秋林', 35.0, '袋', '哈尔滨特产，蒜香浓郁，烟熏风味'),
            (7, '大兴安岭蓝莓', '水果', '北陆', 45.0, '斤', '黑龙江大兴安岭特产，花青素含量高'),
            # 9. 上海市 (2个)
            (8, '南汇水蜜桃', '水果', '大团蜜露', 25.0, '斤', '上海南汇特产，皮薄汁多，入口即化'),
            (8, '崇明生态米', '粮油', '南粳46', 12.0, '袋', '上海崇明岛特产，生态种植，清香软糯'),
            # 10. 江苏省 (5个) ★
            (9, '阳澄湖大闸蟹', '畜禽', '中华绒螯蟹', 128.0, '只', '苏州阳澄湖特产，蟹黄饱满，鲜香无比'),
            (9, '洞庭碧螺春', '茶叶', '碧螺春', 288.0, '盒', '苏州洞庭山特产，卷曲如螺，清香甘醇'),
            (9, '南京盐水鸭', '畜禽', '麻鸭', 45.0, '只', '南京特产，皮白肉嫩，咸香适口'),
            (9, '镇江香醋', '粮油', '镇江陈醋', 18.0, '瓶', '镇江特产，酸而不涩，香而微甜，百年工艺'),
            (9, '太湖银鱼', '畜禽', '银鱼', 55.0, '斤', '太湖三白之一，晶莹剔透，鲜嫩无刺'),
            # 11. 浙江省 (4个) ★
            (10, '西湖龙井', '茶叶', '龙井43号', 388.0, '盒', '杭州西湖特产，色绿香郁，味甘形美'),
            (10, '金华火腿', '畜禽', '两头乌', 198.0, '只', '浙江金华特产，三年陈酿，鲜香浓郁'),
            (10, '临安山核桃', '干货', '薄壳', 48.0, '斤', '浙江临安特产，壳薄肉香，营养丰富'),
            (10, '绍兴黄酒', '粮油', '加饭酒', 38.0, '瓶', '绍兴特产，馥郁芳香，温润醇厚，国宴用酒'),
            # 12. 安徽省 (3个)
            (11, '黄山毛峰', '茶叶', '毛峰', 158.0, '盒', '安徽黄山特产，形似雀舌，清香回甘'),
            (11, '砀山酥梨', '水果', '酥梨', 8.0, '斤', '安徽砀山特产，酥脆多汁，润肺止咳'),
            (11, '霍山石斛', '干货', '铁皮石斛', 388.0, '盒', '安徽霍山特产，九大仙草之首，养生佳品'),
            # 13. 福建省 (4个) ★
            (12, '大红袍茶叶', '茶叶', '大红袍', 588.0, '盒', '武夷山特产，岩骨花香，茶中之王'),
            (12, '琯溪蜜柚', '水果', '琯溪蜜柚', 12.0, '个', '福建平和特产，汁多味甜，润肺佳品'),
            (12, '福州茉莉花茶', '茶叶', '茉莉花茶', 88.0, '盒', '福州特产，花香茶韵，百年窨制工艺'),
            (12, '古田银耳', '干货', '银耳', 48.0, '斤', '福建古田特产，朵大肉厚，胶质丰富，银耳之乡'),
            # 14. 江西省 (3个)
            (13, '赣南脐橙', '水果', '纽荷尔', 10.0, '斤', '江西赣州特产，汁多味甜，中国名橙'),
            (13, '庐山云雾茶', '茶叶', '云雾', 128.0, '盒', '江西庐山特产，高山云雾出好茶'),
            (13, '鄱阳湖大米', '粮油', '赣晚籼', 8.0, '袋', '江西鄱阳湖特产，湖水灌溉，米质优良'),
            # 15. 山东省 (5个) ★
            (14, '烟台苹果', '水果', '红富士', 9.0, '斤', '山东烟台特产，脆甜多汁，中国苹果之都'),
            (14, '潍坊萝卜', '蔬菜', '潍县青', 4.0, '斤', '山东潍坊特产，脆嫩清甜，水果萝卜'),
            (14, '章丘大葱', '蔬菜', '大梧桐', 5.0, '斤', '山东章丘特产，葱白长而脆嫩'),
            (14, '金乡大蒜', '蔬菜', '金乡白蒜', 6.0, '斤', '山东金乡特产，蒜头大瓣匀，世界大蒜之乡'),
            (14, '日照绿茶', '茶叶', '日照绿', 78.0, '盒', '山东日照特产，北茶代表，叶片厚耐冲泡'),
            # 16. 河南省 (5个) ★
            (15, '信阳毛尖', '茶叶', '毛尖', 98.0, '盒', '河南信阳特产，细圆光直，香高味醇'),
            (15, '新郑红枣', '干货', '新郑灰枣', 22.0, '斤', '河南新郑特产，皮薄肉厚核小'),
            (15, '温县铁棍山药', '蔬菜', '铁棍', 18.0, '斤', '河南温县特产，药食同源，健脾养胃'),
            (15, '南阳黄牛肉', '畜禽', '南阳黄牛', 78.0, '斤', '河南南阳特产，五大良种黄牛，肉质细嫩'),
            (15, '洛阳牡丹糕', '干货', '牡丹花', 28.0, '盒', '洛阳特产，牡丹入馔，花香酥甜，盛唐遗风'),
            # 17. 湖北省 (4个) ★
            (16, '洪湖莲藕', '蔬菜', '鄂莲', 8.0, '斤', '湖北洪湖特产，粉糯清甜，煲汤佳品'),
            (16, '恩施玉露', '茶叶', '玉露', 168.0, '盒', '湖北恩施特产，蒸青绿茶，富硒健康'),
            (16, '秭归脐橙', '水果', '秭归脐橙', 12.0, '斤', '湖北秭归特产，屈原故里，甜蜜多汁'),
            (16, '孝感麻糖', '干货', '糯米麻糖', 18.0, '盒', '湖北孝感特产，酥脆香甜，百年传承'),
            # 18. 湖南省 (4个) ★
            (17, '君山银针', '茶叶', '银针', 198.0, '盒', '湖南岳阳特产，黄茶之冠，三起三落'),
            (17, '湘西猕猴桃', '水果', '米良1号', 12.0, '斤', '湖南湘西特产，维C之王，酸甜可口'),
            (17, '洞庭湖大米', '粮油', '湘晚籼', 9.0, '袋', '湖南洞庭湖区特产，鱼米之乡'),
            (17, '安化黑茶', '茶叶', '黑砖茶', 128.0, '饼', '湖南安化特产，越陈越香，消食解腻'),
            # 19. 广东省 (5个) ★
            (18, '增城荔枝', '水果', '挂绿', 38.0, '斤', '广东增城特产，壳红肉白，清甜多汁'),
            (18, '潮州凤凰单丛', '茶叶', '鸭屎香', 268.0, '盒', '广东潮州特产，香气高扬，回甘悠长'),
            (18, '新会陈皮', '干货', '大红柑', 88.0, '盒', '广东新会特产，陈久者良，理气健脾'),
            (18, '梅州金柚', '水果', '沙田柚', 16.0, '个', '广东梅州特产，金柚之乡，清甜微酸耐贮藏'),
            (18, '清远麻黄鸡', '畜禽', '清远鸡', 68.0, '只', '广东清远特产，皮脆肉滑，白切鸡首选'),
            # 20. 广西壮族自治区 (3个)
            (19, '容县沙田柚', '水果', '沙田柚', 15.0, '个', '广西容县特产，柚中之王，甜脆无渣'),
            (19, '梧州六堡茶', '茶叶', '六堡', 128.0, '盒', '广西梧州特产，越陈越香，祛湿养胃'),
            (19, '百色芒果', '水果', '台农1号', 20.0, '斤', '广西百色特产，芒果之乡，香甜浓郁'),
            # 21. 海南省 (2个)
            (20, '文昌鸡', '畜禽', '文昌鸡', 68.0, '只', '海南文昌特产，皮脆肉嫩，四大名鸡'),
            (20, '桥头地瓜', '蔬菜', '桥头', 5.0, '斤', '海南澄迈特产，富硒沙地种植，粉糯香甜'),
            # 22. 重庆市 (3个)
            (21, '涪陵榨菜', '蔬菜', '涪杂2号', 6.0, '袋', '重庆涪陵特产，鲜香脆嫩，佐餐佳品'),
            (21, '奉节脐橙', '水果', '奉节72-1', 10.0, '斤', '重庆奉节特产，汁多味甜，三峡名果'),
            (21, '城口老腊肉', '畜禽', '城口土猪', 68.0, '斤', '重庆城口特产，柏枝熏制，腊香浓郁'),
            # 23. 四川省 (5个) ★
            (22, '郫县豆瓣', '干货', '红油豆瓣', 15.0, '瓶', '四川郫县特产，川菜之魂，三年陈酿'),
            (22, '汉源花椒', '干货', '大红袍花椒', 45.0, '斤', '四川汉源特产，色泽红润，麻香浓郁'),
            (22, '竹叶青茶', '茶叶', '竹叶青', 188.0, '盒', '四川峨眉山特产，形似竹叶，清香宜人'),
            (22, '眉山泡菜', '干货', '乳酸菌发酵', 12.0, '袋', '四川眉山特产，酸爽脆嫩，中国泡菜之乡'),
            (22, '泸州老窖', '粮油', '浓香型', 268.0, '瓶', '四川泸州特产，千年老窖万年糟，酒中泰斗'),
            # 24. 贵州省 (3个)
            (23, '都匀毛尖', '茶叶', '毛尖', 138.0, '盒', '贵州都匀特产，卷曲披毫，香清味醇'),
            (23, '茅台镇酱酒', '粮油', '酱香型', 398.0, '瓶', '贵州茅台镇特产，酱香突出，幽雅细腻'),
            (23, '威宁荞麦', '粮油', '苦荞', 10.0, '斤', '贵州威宁特产，高原苦荞，降糖佳品'),
            # 25. 云南省 (4个) ★
            (24, '普洱茶', '茶叶', '大叶种', 158.0, '饼', '云南普洱特产，越陈越香，降脂减肥'),
            (24, '昭通苹果', '水果', '红富士', 8.0, '斤', '云南昭通特产，高原苹果，脆甜多汁'),
            (24, '文山三七', '干货', '春三七', 298.0, '盒', '云南文山特产，活血化瘀，金不换'),
            (24, '宣威火腿', '畜禽', '乌金猪', 168.0, '只', '云南宣威特产，色鲜肉嫩，中华三大名腿'),
            # 26. 西藏自治区 (2个)
            (25, '林芝松茸', '干货', '松茸', 588.0, '斤', '西藏林芝特产，高原珍菌，香气独特'),
            (25, '青稞香米', '粮油', '藏青2000', 12.0, '斤', '西藏特产高原谷物，β-葡聚糖含量高'),
            # 27. 陕西省 (4个) ★
            (26, '洛川苹果', '水果', '红富士', 12.0, '斤', '陕西洛川特产，黄土高原苹果，脆甜耐贮'),
            (26, '汉中仙毫', '茶叶', '仙毫', 168.0, '盒', '陕西汉中专产，秦巴高山茶，清香回甘'),
            (26, '秦岭土蜂蜜', '干货', '百花蜜', 68.0, '瓶', '陕西秦岭特产，百花酿造，天然纯净'),
            (26, '临潼石榴', '水果', '净皮甜', 15.0, '个', '西安临潼特产，粒大汁多，酸甜可口，丝路遗珍'),
            # 28. 甘肃省 (3个)
            (27, '兰州百合', '蔬菜', '兰州百合', 35.0, '斤', '甘肃兰州特产，瓣大肉厚，清甜无苦'),
            (27, '静宁苹果', '水果', '红富士', 10.0, '斤', '甘肃静宁特产，高原有机，脆甜耐放'),
            (27, '定西宽粉', '干货', '马铃薯粉', 8.0, '袋', '甘肃定西特产，Q弹爽滑，火锅必备'),
            # 29. 青海省 (1个)
            (28, '柴达木红枸杞', '干货', '宁杞7号', 58.0, '斤', '青海柴达木特产，高原枸杞，颗粒饱满营养丰富'),
            # 30. 宁夏回族自治区 (3个)
            (29, '宁夏枸杞', '干货', '宁杞1号', 65.0, '斤', '宁夏中宁特产，世界枸杞之都，粒大籽小'),
            (29, '盐池滩羊肉', '畜禽', '滩羊', 88.0, '斤', '宁夏盐池特产，不膻不腻，鲜嫩可口'),
            (29, '贺兰山东麓葡萄酒', '粮油', '赤霞珠', 168.0, '瓶', '宁夏贺兰山特产，世界优质葡萄酒产区'),
            # 31. 新疆维吾尔自治区 (5个) ★
            (30, '阿克苏冰糖心苹果', '水果', '冰糖心', 15.0, '斤', '新疆阿克苏特产，糖心明显，甜度极高'),
            (30, '哈密瓜', '水果', '西州蜜', 12.0, '个', '新疆哈密特产，香气浓郁，甜蜜多汁'),
            (30, '新疆红枣', '干货', '骏枣', 25.0, '斤', '新疆特产，日照充足，枣大核小'),
            (30, '吐鲁番葡萄干', '干货', '无核白', 30.0, '斤', '吐鲁番特产，自然晾晒，甜糯无核'),
            (30, '库尔勒香梨', '水果', '香梨', 16.0, '斤', '库尔勒特产，皮薄肉细，酥脆多汁，梨中珍品'),
            # 32. 台湾省 (2个)
            (31, '冻顶乌龙茶', '茶叶', '冻顶', 188.0, '盒', '台湾南投特产，喉韵醇厚，炭焙香浓'),
            (31, '台湾凤梨', '水果', '金钻', 16.0, '个', '台湾特产，果肉金黄，酸甜多汁'),
            # 33. 香港特别行政区 (1个)
            (32, '元朗老婆饼', '粮油', '传统手工', 28.0, '盒', '香港元朗特产，皮酥馅软，传统美味'),
            # 34. 澳门特别行政区 (1个)
            (33, '澳门杏仁饼', '干货', '杏仁饼', 35.0, '盒', '澳门特产手信，酥脆杏仁香，手工炭烤'),
        ]
        products = []
        for idx, (fi, name, cat, variety, price, unit, desc) in enumerate(product_data):
            p, _ = Product.objects.get_or_create(
                farmer=farmers[fi], name=name,
                defaults={'category': cat, 'variety': variety, 'price': price,
                          'unit': unit, 'description': desc, 'status': 'approved'}
            )
            products.append(p)
        self.stdout.write(f'  {len(products)} 个产品（已上架，覆盖{len(set(fi for fi,_,_,_,_,_,_ in product_data))}省）')

        # === 批量设置批发价 ===
        cat_min_qty = {'水果': (10,15), '蔬菜': (10,15), '粮油': (15,20), '干货': (10,20), '茶叶': (5,10), '畜禽': (5,8)}
        from decimal import Decimal
        ws_count = 0
        for p in Product.objects.all():
            if p.wholesale_price:
                continue
            ratio = Decimal(str(round(random.uniform(0.65, 0.80), 2)))
            p.wholesale_price = (p.price * ratio).quantize(Decimal('0.01'))
            min_q, max_q = cat_min_qty.get(p.category, (10, 15))
            p.wholesale_min_quantity = random.randint(min_q, max_q)
            p.save(update_fields=['wholesale_price', 'wholesale_min_quantity'])
            ws_count += 1
        self.stdout.write(f'  {ws_count} 个产品已设置批发价')

        # === 待审核产品（8个，分布在8个不同省份，模拟农户提交上架申请） ===
        pending_product_data = [
            (farmers[1], '天津小麻花', '干货', '十八街', 22.0, '盒', '天津传统小吃，酥脆香甜，手工精制'),
            (farmers[5], '大连海参', '畜禽', '辽参', 388.0, '盒', '辽宁大连特产，底播野生海参，肉质肥厚'),
            (farmers[9], '太湖翠竹茶叶', '茶叶', '翠竹', 198.0, '盒', '江苏无锡特产，形似翠竹，清香甘甜'),
            (farmers[14], '山东阿胶', '干货', '东阿', 298.0, '盒', '山东东阿特产，精选驴皮熬制，滋阴补血'),
            (farmers[18], '新会柑普茶', '茶叶', '小青柑', 128.0, '盒', '广东新会特产，柑普合一，养生佳品'),
            (farmers[21], '重庆火锅底料', '干货', '麻辣牛油', 25.0, '袋', '重庆特产，正宗牛油火锅底料，麻辣鲜香'),
            (farmers[26], '兰州鲜百合', '蔬菜', '兰州百合', 42.0, '斤', '甘肃兰州特产，瓣大肉厚，清甜无苦，药食同源'),
            (farmers[31], '台湾高山茶', '茶叶', '阿里山', 258.0, '盒', '台湾阿里山特产，高山云雾茶，清香回甘'),
        ]
        pending_products = []
        for farmer, name, cat, variety, price, unit, desc in pending_product_data:
            p, _ = Product.objects.get_or_create(
                farmer=farmer, name=name,
                defaults={'category': cat, 'variety': variety, 'price': price,
                          'unit': unit, 'description': desc, 'status': 'pending'}
            )
            pending_products.append(p)
        self.stdout.write(f'  {len(pending_products)} 个待审核产品（管理员后台审批）')

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
            # 已有已通过批次的产品跳过，不重复创建
            existing_approved = ProductBatch.objects.filter(product=products[idx], status='approved')
            if existing_approved.exists():
                batch_list = list(existing_approved)
                batch_map[idx] = batch_list
                total_batches += len(batch_list)
                continue
            cat = products[idx].category
            qc_list = qc_templates.get(cat, qc_templates['蔬菜'])
            num_batches = random.randint(2, 5)
            batch_list = []
            for bi in range(num_batches):
                b = ProductBatch.objects.create(
                    product=products[idx],
                    batch_code=generate_batch_code(),
                    quantity=random.randint(30, 250),
                    harvest_date=(now - timedelta(days=random.randint(1, 180))).date(),
                    trace_info={
                        '产地': products[idx].farmer.address,
                        '种植方式': random.choice(['有机种植', '绿色种植', '传统种植', '生态种植']),
                        '批次号': bi + 1,
                    },
                    qc_report=random.choice(qc_list),
                    status='approved',
                )
                batch_list.append(b)
                total_batches += 1
            batch_map[idx] = batch_list
        self.stdout.write(f'  {total_batches} 个批次（{unsold_count} 个待售产品，每产品2-5批）')

        # === 待审核批次（10个，申请溯源二维码和编码，管理员后台审批） ===
        pending_batch_count = 0
        # 从已上架产品中选10个不同省份的产品创建待审核批次（不覆盖已有待审核批次）
        pending_batch_candidates = random.sample(range(len(products)), min(10, len(products)))
        for idx in pending_batch_candidates:
            product = products[idx]
            # 跳过已有待审核批次的产品，避免重复
            if ProductBatch.objects.filter(product=product, status='pending').exists():
                continue
            cat = product.category
            qc_list = qc_templates.get(cat, qc_templates['蔬菜'])
            b = ProductBatch.objects.create(
                product=product,
                quantity=random.randint(50, 200),
                harvest_date=(now + timedelta(days=random.randint(30, 120))).date(),
                trace_info={
                    '产地': product.farmer.address,
                    '种植方式': random.choice(['有机种植', '绿色种植', '传统种植', '生态种植']),
                    '批次号': 1,
                },
                qc_report=random.choice(qc_list),
                status='pending',
            )
            pending_batch_count += 1
        self.stdout.write(f'  {pending_batch_count} 个待审核批次（等待管理员审批溯源编码和二维码）')

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

        # === 购物车（10个消费者各有1-3件商品在购物车中） ===
        cart_consumers = random.sample(consumers, min(10, len(consumers)))
        cart_count = 0
        for user in cart_consumers:
            cart, _ = Cart.objects.get_or_create(user=user)
            # 随机选1-3个已上架产品加入购物车
            cart_products = random.sample(products, random.randint(1, 3))
            for product in cart_products:
                CartItem.objects.get_or_create(
                    cart=cart, product=product,
                    defaults={'quantity': random.randint(1, 5)}
                )
                cart_count += 1
        self.stdout.write(f'  {len(cart_consumers)} 个购物车（共{ cart_count }件商品）')

        # === 收藏（15个消费者各收藏2-5个产品） ===
        fav_consumers = random.sample(consumers, min(15, len(consumers)))
        fav_count = 0
        for user in fav_consumers:
            fav_products = random.sample(products, random.randint(2, 5))
            for product in fav_products:
                _, created = Favorite.objects.get_or_create(user=user, product=product)
                if created:
                    fav_count += 1
        self.stdout.write(f'  {fav_count} 条收藏（{len(fav_consumers)} 个消费者）')

        # === 农技知识库 ===
        guide_defs = [
            ('水稻种植高产技术要点', 'planting', 'rice',
             '一、选种与育秧\n选择适合当地气候的高产抗病品种。播前浸种消毒，用50℃温水浸泡30分钟。\n\n二、整地与施肥\n深耕20-25cm，每亩施腐熟农家肥2000-3000kg作基肥。\n\n三、水肥管理\n分蘖期保持浅水层(3-5cm)，拔节期适当晒田，抽穗扬花期保持深水(7-10cm)。追肥分三次：返青肥、分蘖肥、穗肥。\n\n四、病虫害防治\n重点防治稻瘟病、纹枯病、稻飞虱。采用生物防治为主，化学农药为辅。',
             'https://images.unsplash.com/photo-1536052954887-fd25a05b61e3?w=400'),
            ('苹果树常见病害防治指南', 'pest', 'fruit',
             '一、炭疽病\n多发生于高温多雨季节。症状：果实表面出现褐色圆形病斑，逐渐扩大凹陷。防治：发病初期喷施多菌灵800倍液，每7-10天一次。\n\n二、轮纹病\n主要危害枝干和果实。防治：冬季清园，刮除病斑，涂抹石硫合剂。\n\n三、早期落叶病\n导致树势衰弱，影响花芽分化。防治：加强肥水管理，增强树势；发病前喷施波尔多液预防。\n\n四、综合防治原则\n"预防为主，综合防治"。合理修剪保持通风透光，及时清除病残体。',
             'https://images.unsplash.com/photo-1560806887-1e4cd0b6cbd6?w=400'),
            ('有机蔬菜施肥管理方案', 'fertilizer', 'vegetable',
             '一、基肥\n每亩施腐熟农家肥2000-3000kg，配合饼肥50-100kg，深翻入土。\n\n二、追肥原则\n"少量多次"，根据蔬菜种类和生长期调整。叶菜类以氮肥为主，果菜类增施磷钾肥。\n\n三、有机肥料选择\n- 饼肥：菜籽饼、豆饼含氮量高\n- 草木灰：含钾丰富，适合果菜类\n- 沼液沼渣：营养全面，含活性微生物\n\n四、禁止使用的肥料\n化学合成肥料、城市垃圾、未腐熟的人畜粪尿。',
             'https://images.unsplash.com/photo-1574943320219-553eb213f72d?w=400'),
            ('茶叶采摘与加工储存技术', 'harvest', 'tea',
             '一、采摘标准\n绿茶：一芽一叶或一芽二叶初展。红茶：一芽二叶或一芽三叶。乌龙茶：对夹叶（小开面至中开面）。\n\n二、绿茶加工流程\n摊青→杀青→揉捻→干燥。杀青温度280-320℃，时间3-5分钟，至叶质柔软、散发清香。\n\n三、红茶加工流程\n萎凋→揉捻→发酵→干燥。发酵温度24-28℃，湿度95%以上，时间3-5小时。\n\n四、储存要点\n避光、密封、防潮、低温(0-5℃最佳)。绿茶保质期12-18个月，普洱茶可长期陈化。',
             'https://images.unsplash.com/photo-1563822249366-3efb23b8e0c9?w=400'),
            ('果蔬冷链运输保鲜方法', 'storage', 'general',
             '一、预冷处理\n采收后尽快预冷：叶菜类1-2小时内预冷至4-8℃，果菜类预冷至8-12℃。\n\n二、包装要求\n使用透气保鲜膜或带孔塑料袋，避免密封导致厌氧呼吸。箱内加冰袋或蓄冷剂。\n\n三、运输温度控制\n- 叶菜类：0-4℃\n- 果菜类：7-10℃\n- 热带水果：10-13℃\n- 根茎类：4-8℃\n\n四、常见问题\n冷害：温度过低导致褐变。乙烯伤害：不同果蔬混装导致催熟。建议分类运输。',
             'https://images.unsplash.com/photo-1574269909862-7e1d70bb8078?w=400'),
        ]
        for title, cat, crop, content, cover in guide_defs:
            FarmingGuide.objects.get_or_create(
                title=title,
                defaults={'category': cat, 'crop_type': crop, 'content': content, 'cover_image': cover, 'is_published': True}
            )
        self.stdout.write(f'  {len(guide_defs)} 篇农技指南')

        # === 培训课程 ===
        training_defs = [
            ('有机农业认证流程与标准',
             '有机农业认证是农产品进入高端市场的通行证。本课程详细讲解中国有机产品认证的全流程：'
             '1. 申请阶段——选择认证机构、提交申请材料（土地承包合同、生产基地图、管理体系文件等）；'
             '2. 文件审核——认证机构审核申请材料，确认生产基地符合有机标准；'
             '3. 现场检查——检查员实地考察土壤、水源、投入品使用情况，采样检测农药残留和重金属；'
             '4. 认证决定——认证委员会根据检查报告决定是否颁证，认证周期一般3-6个月；'
             '5. 获证后管理——每年进行监督审核，证书有效期1年，到期需重新申请。'
             '注意事项：转换期内（一般2-3年）产品不得使用有机标识，但可标注"有机转换期产品"。',
             'https://www.ccof.net.cn/'),
            ('智能温室大棚建设与管理',
             '智能温室通过环境控制系统实现温、光、水、气、肥的精准管理，可显著提高产量和品质。'
             '主要内容：1. 温室选址与结构设计——南北向采光好，跨度8-12米适宜，肩高≥3米；'
             '2. 覆盖材料选择——PO膜透光率高寿命长，PC板保温性佳，玻璃透光率最高但造价贵；'
             '3. 环境控制系统——温度控制（风机+湿帘夏季降温，热水管道冬季加温）、湿度控制（自动喷雾+通风）、光照控制（遮阳网+补光灯）；'
             '4. 水肥一体化——滴灌系统精准供水供肥，EC/pH传感器实时监测，比传统灌溉节水50%、节肥30%；'
             '5. 物联网平台——手机APP远程监控，异常报警（温度过高/过低、设备故障），数据自动记录生成报表。'
             '投资回报：标准温室约200-300元/㎡，配合高附加值作物（樱桃番茄、草莓等）2-3年可收回成本。',
             'https://www.agri-iot.cn/'),
            ('农产品电商运营实战指南',
             '本课程面向想拓展线上销路的农户，系统讲解电商运营的核心技能：'
             '1. 平台选择——拼多多（农产品流量大，适合走量）、抖音电商（短视频+直播带货，转化率高）、社区团购（美团优选/多多买菜，直达社区）；'
             '2. 店铺装修——产品主图6张（正面/背面/细节/场景/包装/对比），标题公式=品牌+品种+规格+卖点；'
             '3. 定价策略——成本加成法（收购价+包装+快递+平台扣点+利润），竞品分析法（同品类top10均价），活动促销（限时折扣/满减/拼团）；'
             '4. 物流包装——生鲜冷链（泡沫箱+冰袋+保温袋），干货防潮（铝箔袋+干燥剂），易碎品气柱袋；'
             '5. 客服与售后——响应时间≤3分钟，坏果包赔（拍照退款），主动跟进物流状态，好评返现引导复购。'
             '数据参考：农产品电商平均客单价60-120元，退货率3-8%（远低于服装类），复购率30-50%是核心盈利来源。',
             'https://www.alibaba.com/'),
            ('农产品品牌打造与市场营销',
             '品牌是农产品溢价的核心竞争力。本课程涵盖从0到1建立农产品品牌的完整方法论：'
             '1. 品牌定位——找准差异化卖点：地理标志（赣南脐橙）、品种独特（阳光玫瑰葡萄）、种植方式（古法耕种/零农药）、文化故事（祖传手艺/红色老区）；'
             '2. 品牌命名——地域+品类+特色（如"北大仓·稻花香"），易记易传播，注册35类（广告销售）和31类（农产品）商标；'
             '3. 包装设计——突出品牌色（绿色=生态，金色=品质，红色=喜庆），二维码溯源信息，小规格尝鲜装+大规格家庭装组合；'
             '4. 渠道策略——线下：商超专柜/社区店/农夫市集，线上：电商平台/短视频/社区团购，B端：餐饮连锁/企业团购/礼品定制；'
             '5. 品牌传播——抖音短视频展示种植过程（真实感=信任），微信社群维护老客户（复购+转介绍），参加农产品展销会（政府组织/行业协会）。'
             '案例：褚橙从云南哀牢山到全国知名品牌，核心是"品质+人物故事+全渠道营销"三位一体。',
             ''),
            ('绿色防控技术与病虫害综合治理',
             '绿色防控是减少化学农药使用、保障农产品安全的关键技术体系。课程内容：'
             '1. 农业防治——选用抗病虫品种（如抗稻瘟病水稻品种）、合理轮作（豆科-禾本科轮作减少土传病害）、清洁田园（清除病残体降低病虫基数）；'
             '2. 物理防治——杀虫灯（每20-30亩1盏，诱杀鳞翅目成虫）、色板诱杀（黄板诱蚜虫、蓝板诱蓟马，每亩20-30片）、防虫网（40-60目，阻隔害虫进入）；'
             '3. 生物防治——天敌释放（赤眼蜂防治玉米螟、捕食螨防治红蜘蛛）、微生物制剂（Bt制剂防治菜青虫、白僵菌防治地下害虫）、植物源农药（苦参碱、印楝素）；'
             '4. 化学防治（最后手段）——选用高效低毒低残留农药，严格按安全间隔期施药，交替用药防抗药性；'
             '5. 预测预报——利用性诱剂监测成虫发生高峰期，结合气象数据预测病害流行趋势，精准把握防治适期。'
             '目标：通过综合应用上述技术，实现化学农药使用量减少50%以上，农产品农药残留合格率100%。',
             'https://www.agri.cn/'),
        ]
        for title, content, resource_url in training_defs:
            Training.objects.get_or_create(
                title=title,
                defaults={'content': content, 'resource_url': resource_url}
            )
        self.stdout.write(f'  {len(training_defs)} 个培训课程')

        # === 供需对接帖子 ===
        if farmers and consumers:
            SupplyDemandPost.objects.get_or_create(
                product_name='云南咖啡豆', post_type='supply',
                defaults={'author': farmers[0].user, 'category': '干货', 'quantity': 500, 'unit': 'kg',
                    'price_range': '40-60元/kg', 'region': '云南省普洱市',
                    'description': '2026年6月采收，阿拉比卡品种，海拔1200米种植，日晒处理，风味醇厚。'}
            )
            SupplyDemandPost.objects.get_or_create(
                product_name='五常有机大米', post_type='supply',
                defaults={'author': farmers[7].user, 'category': '粮油', 'quantity': 3000, 'unit': 'kg',
                    'price_range': '12-18元/kg', 'region': '黑龙江省五常市',
                    'description': '2025年秋季新米，有机认证，稻花香2号品种，颗粒饱满，口感香甜。'}
            )
            SupplyDemandPost.objects.get_or_create(
                product_name='新鲜时蔬（每周团购需求）', post_type='demand',
                defaults={'author': consumers[0], 'category': '蔬菜', 'quantity': 200, 'unit': 'kg',
                    'price_range': '3-8元/kg', 'region': '北京市朝阳区',
                    'description': '社区团购每周需要200kg时令蔬菜，要求无农药残留，可长期合作。'}
            )
            SupplyDemandPost.objects.get_or_create(
                product_name='赣南脐橙', post_type='supply',
                defaults={'author': farmers[15].user, 'category': '水果', 'quantity': 2000, 'unit': 'kg',
                    'price_range': '8-12元/kg', 'region': '江西省赣州市',
                    'description': '赣南脐橙，国家地理标志产品，11月成熟，甜度高、汁多化渣。'}
            )
            SupplyDemandPost.objects.get_or_create(
                product_name='优质茶叶（长期采购需求）', post_type='demand',
                defaults={'author': consumers[5], 'category': '茶叶', 'quantity': 100, 'unit': 'kg',
                    'price_range': '100-300元/kg', 'region': '浙江省杭州市',
                    'description': '茶庄长期寻找龙井/白茶供应商，要求有质检报告，品质稳定。'}
            )
            self.stdout.write(f'  5 条供需对接帖子')

        # === 预售活动 ===
        if farmers:
            PreOrderCampaign.objects.get_or_create(
                product_name='阳光玫瑰葡萄',
                defaults={'farmer': farmers[0], 'description': '云南高原阳光玫瑰，甜度20+，果粒饱满，8月中旬成熟。现开启预售，成熟即发。',
                    'target_quantity': 500, 'current_quantity': 168, 'unit_price': 30.00, 'discount_price': 22.00, 'unit': 'kg',
                    'start_date': now, 'end_date': now + timedelta(days=60), 'harvest_date': (now + timedelta(days=50)).date(),
                    'status': 'active'}
            )
            PreOrderCampaign.objects.get_or_create(
                product_name='正宗五常大米（新米预售）',
                defaults={'farmer': farmers[7], 'description': '2026年新米预售，稻花香2号，有机种植，预计10月收割、11月发货。这是真正的五常核心产区大米。',
                    'target_quantity': 2000, 'current_quantity': 520, 'unit_price': 18.00, 'discount_price': 13.80, 'unit': 'kg',
                    'start_date': now, 'end_date': now + timedelta(days=120), 'harvest_date': (now + timedelta(days=110)).date(),
                    'status': 'active'}
            )
            self.stdout.write(f'  2 个预售活动')

        self.stdout.write(self.style.SUCCESS('\n=== 填充完成 ==='))
        self.stdout.write(f'  账号: {len(consumers)}个消费者 + {len(farmers)}个农户 + 1个管理员(demo_admin)')
        self.stdout.write(f'  密码: 消费者/农户 → demo123 | 管理员 → DemoPass#2026')
        self.stdout.write(f'  管理员后台可查看:')
        self.stdout.write(f'    - {len(pending_products)} 个待审核产品（产品审核）')
        self.stdout.write(f'    - {pending_batch_count} 个待审核批次（批次审核/溯源编码审批）')
        self.stdout.write(f'    - {cart_count} 件购物车商品')
        self.stdout.write(f'    - {fav_count} 条收藏记录')
        self.stdout.write(f'    - {len(all_orders)} 个订单 + {cnt} 条评价')
        self.stdout.write(f'  覆盖 34 省 / {len(farmers)} 农户 / {len(products)} 产品 / {total_batches} 批次')
        self.stdout.write(f'  新增: 5篇农技指南 + 5条供需帖子 + 2个预售活动 + {len(training_defs)}个培训课程')
