#!/usr/bin/env bash
set -euo pipefail

# deploy.sh - 自动化部署脚本（用于在 VM 上从仓库启动生产环境）
# 使用前请编辑 .env.production 并确保域名 DNS 已指向本机 IP，80/443 已开放。

ROOT_DIR="/opt/pythonweb"
REPO_URL="https://github.com/0811zou/pythonweb.git"
BRANCH="feat/agro-mvp"
COMPOSE_FILE="docker-compose.prod.yml"

echo "创建部署目录 ${ROOT_DIR}（如果不存在）"
sudo mkdir -p ${ROOT_DIR}
sudo chown $USER:$USER ${ROOT_DIR}
cd ${ROOT_DIR}

if [ ! -d .git ]; then
  echo "克隆仓库..."
  git clone --branch ${BRANCH} ${REPO_URL} .
else
  echo "更新仓库..."
  git fetch origin
  git checkout ${BRANCH}
  git pull origin ${BRANCH}
fi

# 确保 .env.production 存在
if [ ! -f .env.production ]; then
  echo "未找到 .env.production，请将 .env.production 放到 ${ROOT_DIR} 并填写生产配置（SECRET_KEY, POSTGRES_PASSWORD 等）。"
  echo "示例文件已生成为 .env.production.example，请复制并编辑后再运行本脚本。"
  cp .env.example .env.production
  echo "请编辑 .env.production 并重新运行本脚本。"
  exit 1
fi

# 启动服务
echo "使用 Docker Compose 启动服务（如未安装 Docker，请先安装）"
sudo docker compose -f ${COMPOSE_FILE} up -d --build

# 运行 DB 迁移、收集静态文件、创建管理员（如果需要）
# 如果你希望自动创建管理员，请在 .env.production 中设置 ADMIN_USERNAME/ADMIN_EMAIL/ADMIN_PASSWORD

echo "运行数据库迁移..."
sudo docker compose -f ${COMPOSE_FILE} exec -T web python manage.py migrate --noinput

echo "收集静态文件..."
sudo docker compose -f ${COMPOSE_FILE} exec -T web python manage.py collectstatic --noinput

if [ -n "${ADMIN_USERNAME:-}" ] && [ -n "${ADMIN_EMAIL:-}" ] && [ -n "${ADMIN_PASSWORD:-}" ]; then
  echo "创建管理员用户 ${ADMIN_USERNAME}（如不存在）"
  sudo docker compose -f ${COMPOSE_FILE} exec -T web python manage.py shell <<PY
from django.contrib.auth import get_user_model
User = get_user_model()
if not User.objects.filter(username='${ADMIN_USERNAME}').exists():
    u = User.objects.create_superuser('${ADMIN_USERNAME}','${ADMIN_EMAIL}','${ADMIN_PASSWORD}')
    print('superuser created')
else:
    print('superuser exists')
PY
else
  echo "未检测到 ADMIN_USERNAME/ADMIN_EMAIL/ADMIN_PASSWORD 环境变量，跳过自动创建管理员。"
  echo "你可以手动运行： docker compose -f ${COMPOSE_FILE} exec web python manage.py createsuperuser"
fi

echo "部署完成。请检查容器状态： docker compose -f ${COMPOSE_FILE} ps"

echo "查看日志： docker compose -f ${COMPOSE_FILE} logs -f web"
