import os, django
os.environ['DJANGO_SETTINGS_MODULE'] = 'config.settings'
django.setup()

from django.contrib.auth.models import User
from core.models import FarmerProfile, Product, ProductBatch, generate_batch_code

if Product.objects.count() > 0:
    print('数据已存在，跳过')
    exit()

# 创建农户用户
u = User.objects.create_user('demo_farmer', 'farmer@test.com', 'demo123')
u.save()

# 创建农户档案
fp = FarmerProfile.objects.create(
    user=u, phone='13800000000', address='示例村'
)

# 创建产品
p = Product.objects.create(
    farmer=fp, name='示例苹果', price='10.00', unit='kg'
)

# 创建批次
pb = ProductBatch.objects.create(
    product=p, batch_code=generate_batch_code(), quantity=100, status='approved'
)

print(f'Demo data created: Product={p.id}, Batch={pb.batch_code}')
