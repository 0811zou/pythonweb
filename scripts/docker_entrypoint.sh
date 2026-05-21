#!/bin/bash
set -e

echo "=== Running migrations ==="
python manage.py migrate --noinput

echo "=== Init demo data ==="
python manage.py shell << 'PYEOF'
import os, django
os.environ["DJANGO_SETTINGS_MODULE"] = "config.settings"
django.setup()
from django.contrib.auth.models import User
from core.models import Cooperative, FarmerProfile, Product, ProductBatch
if Product.objects.count() == 0:
    u = User.objects.create_user("demo_farmer", "farmer@test.com", "demo123")
    coop, _ = Cooperative.objects.get_or_create(name="示例合作社", region="示例区")
    fp = FarmerProfile.objects.create(user=u, cooperative=coop, phone="13800000000", address="示例村")
    p = Product.objects.create(farmer=fp, name="示例苹果", price="10.00", unit="kg")
    ProductBatch.objects.create(product=p, batch_code="edaadbf6-e392-4b81-8aff-26efc7ba6424", quantity=100)
    print("INIT OK")
PYEOF

echo "=== Collect static ==="
python manage.py collectstatic --noinput

echo "=== Starting gunicorn ==="
exec gunicorn config.wsgi:application --bind 0.0.0.0:8000
