#!/bin/bash
set -e
cd /opt/pythonweb

echo "=== Load new image ==="
docker load -i pythonweb_app.tar

echo "=== Clean old container ==="
docker rm -f pythonweb_container 2>/dev/null || true

echo "=== Start container with auto-init ==="
docker run -d \
  --name pythonweb_container \
  -p 8000:8000 \
  pythonweb_app:latest \
  sh -c '
    python manage.py migrate 2>&1
    echo "--- migrate done ---"

    # init demo data (idempotent)
    python manage.py shell <<PYEOF
import sys, os
sys.path.insert(0, "/app")
os.environ["DJANGO_SETTINGS_MODULE"] = "config.settings"
import django
django.setup()
from core.models import Product, Cooperative, FarmerProfile, ProductBatch
from django.contrib.auth.models import User
if Product.objects.count() == 0:
    u = User.objects.create_user("demo_farmer", "farmer@test.com", "demo123")
    coop, _ = Cooperative.objects.get_or_create(name="示例合作社", region="示例区")
    fp = FarmerProfile.objects.create(user=u, cooperative=coop, phone="13800000000", address="示例村")
    p = Product.objects.create(farmer=fp, name="示例苹果", price="10.00", unit="kg")
    ProductBatch.objects.create(product=p, batch_code="edaadbf6-e392-4b81-8aff-26efc7ba6424", quantity=100)
    print("INIT OK: Product=%d" % p.id)
else:
    print("Data exists, skip init")
PYEOF

    # collect static
    python manage.py collectstatic --noinput 2>&1

    # start gunicorn
    exec gunicorn config.wsgi:application --bind 0.0.0.0:8000
  '

echo "=== Container started ==="
sleep 5
docker ps --filter name=pythonweb_container
echo "=== Logs ==="
docker logs pythonweb_container --tail 15
