"""助农平台单元测试"""
import json
import shutil
import tempfile
from django.test import TestCase, Client
from django.test import override_settings
from django.urls import reverse
from django.contrib.auth.models import User
from rest_framework import status
from accounts.models import FarmerProfile
from products.models import Product, ProductBatch
from trade.models import Order, OrderItem

TEST_MEDIA_ROOT = tempfile.mkdtemp(prefix='agro-test-media-')

@override_settings(MEDIA_ROOT=TEST_MEDIA_ROOT)
class ModelTests(TestCase):
    """数据模型测试"""

    def setUp(self):
        self.user = User.objects.create_user('testuser', 'test@test.com', 'testpass123')
        self.farmer = FarmerProfile.objects.create(
            user=self.user,
            phone='13800138000',
            address='测试地址'
        )
        self.product = Product.objects.create(
            farmer=self.farmer,
            name='测试苹果',
            price='15.00',
            unit='kg'
        )
        self.batch = ProductBatch.objects.create(
            product=self.product,
            quantity=50
        )

    def test_farmer_profile_creation(self):
        """测试农户档案创建"""
        self.assertEqual(self.farmer.phone, '13800138000')
        self.assertIn('testuser', str(self.farmer))

    def test_product_creation(self):
        """测试农产品创建"""
        self.assertEqual(self.product.name, '测试苹果')
        self.assertEqual(str(self.product.price), '15.00')
        self.assertEqual(str(self.product), '测试苹果')

    def test_batch_creation(self):
        """测试批次创建（审核后才生成编码，创建时batch_code为空）"""
        self.assertEqual(self.batch.quantity, 50)
        # batch_code is now deferred — only generated on admin approval
        self.assertIn('测试苹果', str(self.batch))

    def test_product_farmer_relationship(self):
        """测试产品-农户关联"""
        self.assertEqual(self.product.farmer, self.farmer)
        self.assertIn(self.product, self.farmer.products.all())

    def test_batch_product_relationship(self):
        """测试批次-产品关联"""
        self.assertEqual(self.batch.product, self.product)
        self.assertIn(self.batch, self.product.batches.all())

    def test_order_creation(self):
        """测试订单创建"""
        order = Order.objects.create(
            buyer=self.user,
            total_amount=30.00,
            address='收货地址'
        )
        OrderItem.objects.create(
            order=order,
            product_batch=self.batch,
            quantity=2,
            price=15.00
        )
        self.assertEqual(order.status, 'pending')
        self.assertEqual(order.items.count(), 1)
        self.assertEqual(order.total_amount, 30.00)


@override_settings(MEDIA_ROOT=TEST_MEDIA_ROOT)
class AuthTests(TestCase):
    """认证功能测试"""

    def setUp(self):
        self.client = Client()
        self.user = User.objects.create_user('authuser', 'auth@test.com', 'authpass123')

    def test_login_page_loads(self):
        """测试登录页面加载"""
        response = self.client.get(reverse('accounts:login'))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, '登录')

    def test_login_success(self):
        """测试登录成功"""
        response = self.client.post(reverse('accounts:login'), {
            'username': 'authuser',
            'password': 'authpass123'
        })
        # 非农户用户登录后跳转到产品列表页
        self.assertRedirects(response, '/products/')

    def test_login_failure(self):
        """测试登录失败"""
        response = self.client.post(reverse('accounts:login'), {
            'username': 'authuser',
            'password': 'wrongpass'
        })
        # 登录失败应停留在登录页（status 200），而不是重定向
        self.assertEqual(response.status_code, 200)
        # 检查页面仍然是登录页
        self.assertContains(response, '登录')

    def test_logout(self):
        """测试退出登录"""
        self.client.login(username='authuser', password='authpass123')
        response = self.client.get(reverse('accounts:logout'))
        self.assertRedirects(response, '/')

    def test_register_page_loads(self):
        """测试注册页面加载"""
        response = self.client.get(reverse('accounts:register'))
        self.assertEqual(response.status_code, 200)

    def test_register_success(self):
        """测试注册成功"""
        response = self.client.post(reverse('accounts:register'), {
            'username': 'newuser',
            'password1': 'ComplexPass123!',
            'password2': 'ComplexPass123!',
        })
        self.assertEqual(response.status_code, 302)
        self.assertTrue(User.objects.filter(username='newuser').exists())


@override_settings(MEDIA_ROOT=TEST_MEDIA_ROOT)
class PageViewTests(TestCase):
    """前端页面访问测试"""

    def setUp(self):
        self.client = Client()
        self.user = User.objects.create_user('pageuser', 'page@test.com', 'pagepass123')
        self.farmer = FarmerProfile.objects.create(
            user=self.user,
            phone='13900000000', address='测试地址'
        )
        self.product = Product.objects.create(
            farmer=self.farmer, name='页面测试苹果', price='20.00', unit='kg'
        )
        self.batch = ProductBatch.objects.create(
            product=self.product, quantity=100
        )

    def test_home_page(self):
        """测试首页"""
        response = self.client.get(reverse('core:home'))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, '智农溯源')

    def test_product_list_page(self):
        """测试产品列表页"""
        response = self.client.get(reverse('products:list'))
        self.assertEqual(response.status_code, 200)

    def test_product_detail_page(self):
        """测试产品详情页"""
        response = self.client.get(reverse('products:detail', args=[self.product.pk]))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, '页面测试苹果')

    def test_trace_query_page(self):
        """测试溯源查询页"""
        response = self.client.get(reverse('traceability:trace_query'))
        self.assertEqual(response.status_code, 200)

    def test_trace_page(self):
        """测试溯源结果页"""
        # batch_code is deferred — generate one for test
        from products.models import generate_batch_code
        self.batch.batch_code = generate_batch_code()
        self.batch.save(update_fields=['batch_code'])
        response = self.client.get(reverse('traceability:trace', args=[self.batch.batch_code]))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, str(self.batch.batch_code)[:8])


@override_settings(MEDIA_ROOT=TEST_MEDIA_ROOT)
class APITests(TestCase):
    """REST API 测试"""

    def setUp(self):
        self.client = Client()
        self.user = User.objects.create_user('apiuser', 'api@test.com', 'apipass123')
        self.buyer = User.objects.create_user('buyeruser', 'buyer@test.com', 'buyerpass123')
        self.farmer = FarmerProfile.objects.create(
            user=self.user,
            phone='13700000000', address='API测试地址'
        )
        self.product = Product.objects.create(
            farmer=self.farmer, name='API测试苹果', price='25.00', unit='kg', status='approved'
        )

    def test_product_list_api(self):
        """测试产品列表 API"""
        response = self.client.get('/api/products/')
        self.assertEqual(response.status_code, 200)
        data = response.json()
        # DRF 分页格式：{ count, results }
        if isinstance(data, dict):
            results = data.get('results', data)
        else:
            results = data
        self.assertIsInstance(results, list)
        self.assertEqual(len(results), 1)
        self.assertEqual(results[0]['name'], 'API测试苹果')

    def test_product_detail_api(self):
        """测试产品详情 API"""
        response = self.client.get(f'/api/products/{self.product.pk}/')
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json()['price'], '25.00')

    def test_api_requires_auth_for_order(self):
        """测试订单 API 需要认证"""
        response = self.client.get('/api/orders/')
        self.assertEqual(response.status_code, 403)

    def test_api_allows_anon_for_products(self):
        """测试产品 API 允许匿名访问"""
        self.client.logout()
        response = self.client.get('/api/products/')
        self.assertEqual(response.status_code, 200)

    def test_create_order_authenticated(self):
        """测试已认证用户创建订单"""
        self.client.login(username='buyeruser', password='buyerpass123')
        batch = ProductBatch.objects.create(product=self.product, quantity=10)
        response = self.client.post('/api/orders/', {
            'address': '测试收货地址',
            'items': [{
                'product_batch': batch.pk,
                'quantity': 2,
                'price': '25.00'
            }]
        }, content_type='application/json')
        self.assertEqual(response.status_code, 201)
        self.assertEqual(response.json()['total_amount'], '50.00')


def tearDownModule():
    shutil.rmtree(TEST_MEDIA_ROOT, ignore_errors=True)
