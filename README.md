# 助农农产品帮扶平台（MVP）

这是一个基于 Django + DRF 的最小可运行骨架，包含：用户认证、农户/商品/批次/下单与线下支付模拟、溯源页面、Docker 支持与快速启动说明。

快速开始（本地开发，Python 3.10+）：

1. 克隆仓库并切换分支（如果需要）：
   git clone https://github.com/0811zou/pythonweb.git
   cd pythonweb
   git checkout feat/agro-mvp

2. 创建虚拟环境并安装依赖：
   python -m venv venv
   source venv/bin/activate
   pip install -r requirements.txt

3. 运行数据库迁移并创建管理员：
   python manage.py migrate
   python manage.py createsuperuser

4. 启动开发服务器：
   python manage.py runserver

访问： http://127.0.0.1:8000/  管理后台： http://127.0.0.1:8000/admin  API 文档（如已启用）： /api/docs/

演示账号：请用你创建的 superuser 登录 Admin 并创建 FarmerProfile / Product 等示例数据。

文件说明：
- manage.py
- config/ (Django 项目配置)
- core/ (业务 app: models, serializers, views, urls, admin)
- templates/ (示例模板)
- requirements.txt, Dockerfile, docker-compose.yml, README.md

如需我把本分支合并到 main 或做额外功能（示例数据、PPT、CI、部署脚本），请回复说明。
