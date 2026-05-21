#!/bin/bash
cd /opt/pythonweb
docker compose exec -T web python manage.py shell << 'PYEOF'
from django.contrib.auth.models import User
u = User.objects.get(username='demo_admin')
u.set_password('DemoPass#2026')
u.save()
print("Password set OK for demo_admin")
PYEOF
