# ModelRouter Portal - Development Rules

## Project Overview

基于阿里云 ModelRouter API（AiContent/20240611）的终端客户自助门户。
用户可浏览AI模型、自助开通模型、管理 API Key、模拟充值、查看用量账单。
用户获取 API Key 后直接调用阿里云 ModelRouter 端点，不经过本平台代理。

## Tech Stack

- Backend: Python FastAPI + SQLAlchemy + SQLite
- Frontend: React (Vite + TypeScript) + Ant Design + Recharts
- Auth: 自建用户系统 (username/password + JWT HS256 24h)
- Cloud SDK: alibabacloud_aicontent20240611 (>=7.3.0)

## Architecture

```
React SPA (Vite + TS + Antd)  ──Axios+JWT──>  FastAPI (BFF)  ──SDK──>  阿里云 ModelRouter API
                                                    |
                                               SQLAlchemy
                                                    |
                                                 SQLite
```

FastAPI 作为 BFF 层：持有阿里云 AccessKey，代理所有 ModelRouter 调用，确保凭证不暴露给前端。

## Directory Structure

```
ModelRouterPortal/
├── backend/
│   ├── app/
│   │   ├── main.py              # FastAPI app, CORS, lifespan
│   │   ├── config.py            # pydantic-settings (.env)
│   │   ├── database.py          # SQLAlchemy engine + session
│   │   ├── dependencies.py      # get_db, get_current_user
│   │   ├── models/              # SQLAlchemy ORM
│   │   │   ├── user.py
│   │   │   ├── model.py         # 本地模型信息缓存
│   │   │   ├── activation.py    # 用户模型开通记录
│   │   │   └── recharge.py
│   │   ├── schemas/             # Pydantic request/response
│   │   ├── routes/              # FastAPI routers
│   │   ├── services/            # Business logic + SDK 调用
│   │   │   └── alicloud_client.py  # SDK singleton (关键文件)
│   │   └── utils/security.py    # bcrypt + JWT helpers
│   ├── requirements.txt
│   └── .env.example
├── frontend/
│   ├── src/
│   │   ├── api/                 # Axios client + API modules
│   │   ├── contexts/            # AuthContext
│   │   ├── pages/               # 10 pages
│   │   ├── components/          # layout + shared components
│   │   └── types/
│   ├── package.json
│   └── vite.config.ts
├── AGENTS.md
└── .gitignore
```

## Alibaba Cloud SDK Integration

### Installation

```bash
pip install alibabacloud_aicontent20240611
```

### Client Initialization (alicloud_client.py)

```python
import os
from alibabacloud_aicontent20240611.client import Client
from alibabacloud_aicontent20240611 import models as aicontent_models
from alibabacloud_tea_openapi import models as open_api_models

def create_client() -> Client:
    config = open_api_models.Config(
        access_key_id=os.environ['ALIBABA_CLOUD_ACCESS_KEY_ID'],
        access_key_secret=os.environ['ALIBABA_CLOUD_ACCESS_KEY_SECRET'],
    )
    config.endpoint = 'aicontent.cn-beijing.aliyuncs.com'
    return Client(config)
```

### SDK Method Naming Convention

PascalCase API 名 -> snake_case 方法名：
- ModelRouterQueryModelList -> `client.model_router_query_model_list(request)`
- ModelRouterCreateClient -> `client.model_router_create_client(request)`
- ModelRouterCreateApiKey -> `client.model_router_create_api_key(request)`
- ModelRouterQueryClientTree -> `client.model_router_query_client_tree(request)`
- ModelRouterQueryBillingRuleList -> `client.model_router_query_billing_rule_list(request)`

Request 对象: `aicontent_models.ModelRouterQueryModelListRequest(...)`

### Environment Variables (.env)

```
ALIBABA_CLOUD_ACCESS_KEY_ID=your_key_id
ALIBABA_CLOUD_ACCESS_KEY_SECRET=your_key_secret
SECRET_KEY=your_jwt_secret_key
DATABASE_URL=sqlite:///./model_router_portal.db
FRONTEND_URL=http://localhost:5173
```

> 必须使用 RAM 用户的 AccessKey，禁止使用主账号 AccessKey

## Database Schema

### users
- id (Integer PK), username (String UNIQUE), hashed_password (String)
- client_id (Integer) -- 阿里云 ModelRouter client ID
- client_uuid (String) -- 阿里云 client UUID
- display_name (String), is_active (Boolean), is_admin (Boolean)
- created_at (DateTime)

### models (本地缓存，定期从阿里云同步)
- id (Integer PK), model_id (String UNIQUE) -- 如 "qwen3.6-plus"
- name (String), description (Text), model_type (String), provider (String)
- icon_url (String), is_available (Boolean), sort_order (Integer)
- synced_at (DateTime), created_at (DateTime)

> 价格/计费规则不存本地，实时从阿里云 QueryBillingRuleList 获取

### user_model_activations
- id (Integer PK), user_id (FK->users.id), model_id (String)
- status (String: active/deactivated)
- activated_at (DateTime), deactivated_at (DateTime)

### recharge_records
- id (Integer PK), user_id (FK->users.id), amount (Float)
- balance_before (Float), balance_after (Float)
- status (String: pending/completed/failed), remark (String)
- created_at (DateTime), completed_at (DateTime)

## Available Models

当前平台支持 4 个模型，模型信息定期从阿里云同步：

| 展示名称 | Model ID | 类型 | 供应商 |
|----------|----------|------|--------|
| Qwen3.6-Plus | qwen3.6-plus | Chat | 通义 |
| Qwen3-Max | qwen3-max | Chat | 通义 |
| Kimi-K2.6 | kimi-k2.6 | Chat | 月之暗面 |
| DeepSeek-V4-Pro | deepseek-v4-pro | Chat | DeepSeek |

## Business Rules

### Model Activation
- 新用户注册后默认无任何模型权限
- 用户在模型市场页面自助点击"开通"按钮激活单个模型
- 开通记录存储在本地 user_model_activations 表
- 用户只能使用已开通的模型

### Authentication
- 注册：创建本地用户 -> 调用 ModelRouterCreateClient 创建阿里云客户 -> 存储 client_id -> 签发 JWT
- 登录：验证 bcrypt 密码 -> 签发 JWT (HS256, 24h 过期)
- 保护机制：Axios 拦截器附加 Bearer token -> 后端 get_current_user 解码 JWT -> 加载 user.client_id -> 作用域隔离所有 SDK 调用

### Recharge
- MVP 阶段为模拟充值：用户提交充值请求 -> 管理员审批 -> 更新余额
- 后续可对接支付宝等真实支付

### API Key Usage
- 用户在门户创建 API Key 后，直接用该 Key 调用阿里云 ModelRouter 端点
- Base URL: https://aicontent.cn-beijing.aliyuncs.com
- 认证: Authorization: Bearer YOUR_API_KEY

## Frontend Routing

### Public Pages (无需登录)
| Route | Page | Description |
|-------|------|-------------|
| / | GuidePage | 平台介绍、接入地址、代码示例(Python/curl/JS)、模型列表、FAQ |
| /login | LoginPage | 登录表单 |
| /register | RegisterPage | 注册表单 |

### Protected Pages (需登录，侧边栏布局)
| Route | Page | Description |
|-------|------|-------------|
| /dashboard | DashboardPage | 余额/消费/调用概览 + 快捷操作 + 7日趋势图 |
| /models | ModelMarketPage | 模型卡片 + 开通状态 + 搜索筛选 |
| /models/:id | ModelDetailPage | 模型详情 + 计费规则 + 接入代码示例 + 开通按钮 |
| /api-keys | ApiKeysPage | Key列表 + 创建(一次性展示) + 删除 |
| /balance | BalancePage | 余额卡片 + 模拟充值弹窗 + 充值历史 |
| /usage | UsagePage | 日期范围 + 概览卡片 + 趋势图 + 模型明细表 |
| /settings | SettingsPage | 修改密码 |

## Backend API Endpoints

所有接口前缀: `/api/v1`

### Auth -- `/api/v1/auth`
- POST /register -- 注册+创建Cloud Client
- POST /login -- 登录返回JWT
- GET /me -- 获取个人信息+余额

### Models -- `/api/v1/models` (列表公开, 开通需登录)
- GET / -- 模型列表 (公开)
- GET /{model_id} -- 模型详情+计费规则 (公开)
- POST /{model_id}/activate -- 开通模型 (JWT)
- POST /{model_id}/deactivate -- 关闭模型 (JWT)
- GET /activated -- 已开通模型列表 (JWT)
- POST /sync -- 管理员手动同步模型 (JWT+Admin)

### API Keys -- `/api/v1/api-keys` (全部需JWT)
- GET / -- 列出用户API Keys
- POST / -- 创建新Key
- GET /{key_id} -- 查看Key详情
- DELETE /{key_id} -- 删除Key

### Balance -- `/api/v1/balance` (全部需JWT)
- GET / -- 查询余额
- POST /recharge -- 提交充值请求
- GET /history -- 充值历史
- POST /recharge/{id}/approve -- 管理员审批 (JWT+Admin)

### Usage -- `/api/v1/usage` (全部需JWT)
- GET /overview -- 费用概览
- GET /trend -- 费用趋势
- GET /models -- 模型用量列表
- GET /models/{id} -- 模型用量明细
- GET /breakdown -- 计费明细

### Settings -- `/api/v1/settings` (需JWT)
- PUT /password -- 修改密码

## Development Commands

```bash
# Backend
cd backend
pip install -r requirements.txt
uvicorn app.main:app --reload --port 8000

# Frontend
cd frontend
npm install
npm run dev          # dev server on :5173
npm run build        # production build
npm run lint         # ESLint check
npm run type-check   # TypeScript check
```

## Key Conventions

- 后端分层：routes -> services -> alicloud_client (SDK)
- 前端数据获取：pages -> api modules -> axios client
- 所有阿里云 SDK 调用必须通过 services 层，不要在 routes 中直接调用
- 每个受保护接口必须通过 get_current_user 依赖获取用户，用 user.client_id 隔离数据
- 阿里云 AccessKey 只存在后端 .env，绝不暴露给前端
- UI 组件库使用 Ant Design，图表使用 Recharts
- 前端状态管理：AuthContext 管理认证状态，其余用组件本地 state + API 调用
- Issue 和 PR 描述须同时提供中文和英文两个版本（ bilingual ）

## Branch Strategy & Phased Development

Git 工作流：每个开发阶段一个 feature branch，完成后 merge 回 main 并打 tag。

| Phase | Branch | Tag | 内容 |
|-------|--------|-----|------|
| 0 | phase-0-init | v0.1.0 | 项目脚手架 + AGENTS.md + .gitignore |
| 1 | phase-1-auth | v0.2.0 | 认证(注册/登录/JWT) + 全局布局(侧边栏/Header) |
| 2 | phase-2-models | v0.3.0 | GuidePage + 模型市场 + 模型开通 + 同步机制 |
| 3 | phase-3-apikeys | v0.4.0 | API Key 管理 (CRUD + 租户隔离) |
| 4 | phase-4-balance | v0.5.0 | 余额查询 + 模拟充值 + 管理员审批 |
| 5 | phase-5-usage | v0.6.0 | 用量统计 + Dashboard 仪表盘 |
| 6 | phase-6-polish | v1.0.0 | 账户设置 + 错误处理 + Loading/空状态 + lint |

每阶段操作流程：
```bash
git checkout main
git checkout -b phase-X-xxx
# ... 开发 + commit ...
git checkout main
git merge phase-X-xxx
git tag vX.X.X
```
