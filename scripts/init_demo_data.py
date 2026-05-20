import os, django
os.environ['DJANGO_SETTINGS_MODULE'] = 'config.settings'
django.setup()

from django.contrib.auth.models import User
from core.models import Cooperative, FarmerProfile, Product, ProductBatch

if Product.objects.count() > 0:
    print('数据已存在，跳过')
    exit()

# 创建农户用户
u = User.objects.create_user('demo_farmer', 'farmer@test.com', 'demo123')
u.save()

# 创建合作社
coop, _ = Cooperative.objects.get_or_create(name='示例合作社', region='示例区')

# 创建农户档案
fp = FarmerProfile.objects.create(
    user=u, cooperative=coop, phone='13800000000', address='示例村'
)

# 创建产品
p = Product.objects.create(
    farmer=fp, name='示例苹果', price='10.00', unit='kg'
)

# 创建批次
pb = ProductBatch.objects.create(
    product=p, batch_code='edaadbf6-e392-4b81-8aff-26efc7ba6424', quantity=100
)

print(f'Demo data created: Product={p.id}, Batch={pb.batch_code}')
