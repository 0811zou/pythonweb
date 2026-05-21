# 绿农溯源 - 农产品溯源与助农平台

> 基于 Django + Django REST Framework 的农产品溯源与助农帮扶平台。
> 
> 连接农户与消费者，利用批次二维码技术实现农产品全程可追溯。

---

## 📋 项目概述

**绿农溯源**是一个面向农业领域的全栈 Web 平台，提供农产品溯源、在线订购、助农补贴申请、农技培训等功能。平台采用 **前后端混合架构**（Django 模板 + REST API），同时支持浏览器直接访问和第三方客户端集成。

## 🏗 技术架构

| 层级 | 技术 | 说明 |
|------|------|------|
| **后端框架** | Django 5.2 + DRF 3.17 | Python Web 框架 |
| **API 文档** | drf-spectacular (Swagger/OpenAPI) | 自动生成 API 文档 |
| **前端** | Bootstrap 5 + Bootstrap Icons | 响应式 UI |
| **数据库** | SQLite（开发）/ PostgreSQL（生产） | Django ORM |
| **容器化** | Docker + docker compose | 一键部署 |
| **静态文件** | WhiteNoise | 生产环境静态文件服务 |

## ✨ 功能特性

### 核心业务
- **农产品管理** — 农户发布产品（名称、价格、分类、描述）
- **批次溯源** — 每批产品独立二维码，支持全链路追溯
- **在线订购** — 用户下单 + 线下支付模拟（含凭证上传）
- **助农补贴** — 农户在线申请补贴，管理员审核
- **农技培训** — 发布培训内容与资源链接

### 用户系统
- 用户注册、登录、退出
- 农户档案管理（关联合作社）
- 角色权限控制（匿名/认证用户/管理员）

### 系统功能
- RESTful API（Product / Order / Batch / Subsidy / Training）
- 管理后台（Django Admin）
- Swagger API 文档（`/api/docs/`）
- Docker 容器化部署

## 📦 数据模型

```
Cooperative（合作社） ──┐
                       ├── FarmerProfile（农户档案）── Product（农产品）── ProductBatch（批次）
User（用户）────────────┘
                       ├── Order（订单）── OrderItem（订单项）
                       └── Review（评价）
FarmerProfile ── SubsidyApplication（补贴申请）
Training（培训）
```

## 🚀 快速开始（本地开发）

### 前置条件
- Python 3.10+
- pip / venv

### 安装步骤

```bash
# 1. 克隆仓库
git clone https://github.com/0811zou/pythonweb.git
cd pythonweb
git checkout feat/agro-mvp

# 2. 创建虚拟环境并安装依赖
python -m venv venv
# Windows: venv\Scripts\activate
source venv/bin/activate
pip install -r requirements.txt

# 3. 数据库迁移
python manage.py migrate

# 4. 创建管理员
python manage.py createsuperuser

# 5. 加载演示数据（可选）
python manage.py loaddata core/fixtures/demo_data.json

# 6. 启动开发服务器
python manage.py runserver
```

### 访问地址

| 地址 | 说明 |
|------|------|
| `http://localhost:8000/` | 平台首页 |
| `http://localhost:8000/admin/` | 管理后台 |
| `http://localhost:8000/api/docs/` | Swagger API 文档 |
| `http://localhost:8000/api/schema/` | OpenAPI Schema |

### 演示账号

| 角色 | 用户名 | 密码 |
|------|--------|------|
| 管理员 | `demo_admin` | `DemoPass#2026` |
| 农户 | `demo_farmer` | `demo123` |

## 🐳 Docker 部署

### 开发环境
```bash
docker compose up -d --build
```

### 生产环境（含 Nginx + PostgreSQL）
```bash
# 1. 复制环境变量模板
cp .env.example .env.production
# 2. 编辑 .env.production 配置密钥和域名
# 3. 启动生产环境
docker compose -f docker-compose.prod.yml up -d --build
```

## 🧪 测试

```bash
# 运行所有测试
python manage.py test core --verbosity=2

# 运行特定测试类
python manage.py test core.tests.ModelTests
python manage.py test core.tests.APITests
```

### 测试覆盖范围
- ✅ 数据模型创建与关联（9 个模型）
- ✅ API 端点（列表、详情、认证、权限）
- ✅ 前端页面加载（首页、产品、溯源、登录、注册）
- ✅ 用户认证（登录、退出、注册）

## 📁 项目结构

```
pythonweb/
├── config/               # Django 项目配置
│   ├── settings.py       # 主配置（数据库、中间件、静态文件）
│   ├── urls.py           # 根路由（含 API 文档路由）
│   └── wsgi.py           # WSGI 入口
├── core/                 # 业务应用
│   ├── models.py         # 数据模型（9 个模型类）
│   ├── views.py          # 视图（API ViewSet + 前端页面视图）
│   ├── serializers.py    # 序列化器
│   ├── urls.py           # 应用路由
│   ├── admin.py          # 管理后台注册
│   ├── tests.py          # 单元测试（23 个测试用例）
│   ├── fixtures/         # 演示数据
│   └── static/           # 静态文件（CSS）
├── templates/            # 前端模板（Bootstrap 5）
│   ├── base.html         # 基础模板
│   ├── index.html        # 首页
│   ├── products.html     # 产品列表
│   ├── product_detail.html# 产品详情
│   ├── login.html        # 登录
│   ├── register.html     # 注册
│   ├── trace.html        # 溯源结果
│   └── trace_query.html  # 溯源查询
├── scripts/              # 部署脚本
├── deploy/               # 生产部署配置
├── Dockerfile            # Docker 构建文件
├── docker-compose.yml    # Docker Compose（开发）
├── docker-compose.prod.yml # Docker Compose（生产）
└── requirements.txt      # Python 依赖
```

## 🔄 更新流程

```bash
# 1. 本地修改代码
# 2. 运行测试
python manage.py test core
# 3. 提交并推送
git add -A
git commit -m "feat: 你的改动说明"
git push origin feat/agro-mvp
# 4. 生产服务器拉取
# ssh 登录服务器后：
cd /opt/pythonweb
git pull origin feat/agro-mvp
docker compose up -d --build
```
