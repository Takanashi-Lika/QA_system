# 电商平台 + RAG 智能客服

轻量级企业电商平台，覆盖**用户→商品→订单→支付→物流→售后**完整交易闭环，集成 **RAG 智能客服**（FAQ 知识库检索）。通过 Docker Compose 一键部署。

---

## 🖥 系统架构

```
浏览器 :80
    │
    ▼
┌─────────────────────────────────────────────┐
│  Nginx (反向代理)                             │
│  /api/shop/*  →  shop-service:8001          │
│  /api/ai/*    →  ai-service (预留)           │
└──────────────┬──────────────────────────────┘
               │
    ┌──────────┴──────────┐
    ▼                     ▼
┌───────────┐    ┌────────────────┐
│  Redis 7  │    │  PostgreSQL 16 │
│  缓存      │    │  + pgvector    │
│  :6379    │    │  :5432         │
└───────────┘    └────────────────┘
         ▲                 ▲
         │    ┌────────────┘
         │    │
┌────────┴────┴────────┐
│  shop-service :8001  │
│  FastAPI + Python    │
│  + APScheduler       │
│  + JWT 认证          │
└──────────────────────┘
```

| 容器 | 端口 | 用途 |
|------|------|------|
| **nginx** | 80 | 统一入口、反向代理、CORS |
| **shop-service** | 8001 | 电商业务 API（FastAPI） |
| **postgres** | 5432 | 关系数据 + 向量数据 |
| **redis** | 6379 | 商品详情/热门/分类树缓存 |

---

## 📦 技术栈

| 层面 | 选型 |
|------|------|
| 语言 | Python 3.10 |
| Web 框架 | FastAPI（异步、自动 API 文档） |
| 数据库 | PostgreSQL 16 + pgvector |
| 缓存 | Redis 7（Cache-Aside 模式） |
| 定时任务 | APScheduler（超时订单自动取消） |
| 认证 | JWT（PyJWT）+ bcrypt 密码加密 |
| RAG 检索 | ChromaDB + sentence-transformers + BM25 + jieba |
| 部署 | Docker Compose（4 容器） |

---

## 🚀 快速开始（Docker 方式）

### 前置条件

你只需要安装 **Docker Desktop**：
- 下载：[docker.com/products/docker-desktop](https://www.docker.com/products/docker-desktop/)
- Windows 用户可能需要先启用 WSL2（安装程序会引导你）

### 1. 克隆项目（或解压到本地）

```bash
cd My_LLM_Project
```

### 2. 一键启动

```bash
docker compose up -d
```

首次运行会拉取镜像（约 5 分钟），之后秒启。启动后 4 个容器全部 Running 即为成功：

```bash
docker compose ps
# 应看到 nginx、shop-service、postgres、redis 全部 Up
```

### 3. 运行端到端测试

```bash
cd shop-service
pip install -r requirements.txt
python test_shop.py
```

期待输出：

```
============================================================
电商平台 Shop-Service 端到端测试
============================================================
0. 健康检查...   通过 ✓
1. 用户注册...   通过 ✓
   ...
============================================================
全部测试通过!
============================================================
```

### 4. 打开 API 文档（Swagger）

浏览器打开：**http://localhost/docs**

每个端点都能在线填参数、发请求、看响应——零代码调试。

---

## 🧪 手动测试常用 API

### 预置账号

| 角色 | 邮箱 | 密码 |
|------|------|------|
| 管理员 | `admin@shop.local` | `admin123` |

### 快速走通购物流程

```bash
# 1. 注册用户
curl -X POST http://localhost/c-endpoint/register \
  -H "Content-Type: application/json" \
  -d '{"email":"test@test.com","password":"123456","nickname":"张三"}'

# 2. 登录（获取 Token）
curl -X POST http://localhost/c-endpoint/login \
  -H "Content-Type: application/json" \
  -d '{"email":"test@test.com","password":"123456"}'
# → 复制返回的 token

# 3. 设为环境变量
TOKEN="eyJhbGci..."

# 4. 查看分类树
curl http://localhost/c-endpoint/products/hot

# 5. 加入购物车
curl -X POST http://localhost/c-endpoint/cart/ \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"product_id":1,"quantity":2}'

# 6. 下单
curl -X POST http://localhost/c-endpoint/orders/ \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"address":"广东省深圳市南山区"}'

# 7. 支付（假设返回的订单 ID 是 1）
curl -X POST http://localhost/c-endpoint/orders/1/pay \
  -H "Authorization: Bearer $TOKEN"

# 8. 查物流
curl "http://localhost/c-endpoint/logistics?order_id=1" \
  -H "Authorization: Bearer $TOKEN"
```

---

## 📁 项目结构

```
My_LLM_Project/
├── shop-service/                 # 电商服务（核心）
│   ├── main.py                  # FastAPI 入口 + 生命周期管理
│   ├── apps/                    # API 路由层
│   │   ├── c_endpoint/          #   C 端：user / product / cart / order / logistics / after_sale
│   │   ├── b_endpoint/          #   B 端：category / product / order / after_sale
│   │   ├── internal/            #   内部接口（供 AI 服务调用）
│   │   └── common/              #   公共：JWT 认证
│   ├── domain/                  # 业务逻辑层
│   │   └── user / category / product / cart / order / logistics / after_sale
│   ├── infrastructure/          # 基础设施
│   │   ├── database.py         #   ThreadedConnectionPool 连接池
│   │   ├── redis_client.py     #   Cache-Aside 缓存客户端
│   │   └── scheduler.py        #   APScheduler 定时任务
│   ├── middleware/              # 中间件（RequestID / 请求日志 / 异常处理）
│   ├── common/                  # 公共模块（异常树 / ContextVar / Logger）
│   ├── Dockerfile
│   ├── requirements.txt
│   └── test_shop.py            # 端到端集成测试
│
├── rag/                         # RAG 检索模块
│   ├── store.py                #   向量存储（ChromaDB）
│   ├── embedding.py            #   向量化（sentence-transformers）
│   ├── bm25.py                 #   BM25 关键词检索
│   └── parser.py               #   FAQ 文档解析
│
├── model/                       # LLM 客户端
│   └── client.py               #   OpenAI 兼容接口
│
├── rag_resource/                # FAQ 知识库文档（5 个产品线）
├── nginx/nginx.conf             # Nginx 反向代理配置
├── init.sql                     # 数据库建表 + 种子数据
├── docker-compose.yml           # 4 容器编排
├── .env                         # 环境变量
├── rag_cli.py                   # RAG CLI 工具（临时）
└── 开发文档/                     # 需求/技术/知识文档
```

---

## 📖 API 概览

### C 端（面向用户）

| 端点 | 方法 | 描述 | 登录 |
|------|------|------|------|
| `/c-endpoint/register` | POST | 注册 | ✗ |
| `/c-endpoint/login` | POST | 登录 | ✗ |
| `/c-endpoint/me` | GET | 个人信息 | ✓ |
| `/c-endpoint/address` | PUT | 更新地址 | ✓ |
| `/c-endpoint/products/hot` | GET | 热门商品 | ✗ |
| `/c-endpoint/products` | GET | 商品列表/搜索 | ✗ |
| `/c-endpoint/products/{id}` | GET | 商品详情 | ✗ |
| `/c-endpoint/cart/` | GET/POST | 查看/添加购物车 | ✓ |
| `/c-endpoint/cart/{id}` | PUT/DELETE | 修改/删除购物车项 | ✓ |
| `/c-endpoint/orders/` | GET/POST | 订单列表/创建订单 | ✓ |
| `/c-endpoint/orders/{id}` | GET | 订单详情 | ✓ |
| `/c-endpoint/orders/{id}/pay` | POST | 支付 | ✓ |
| `/c-endpoint/orders/{id}` | DELETE | 取消订单 | ✓ |
| `/c-endpoint/logistics` | GET | 物流查询 | ✓ |
| `/c-endpoint/after-sales` | GET/POST | 售后申请/查询 | ✓ |

### B 端（管理员，需 `role=admin`）

| 端点 | 方法 | 描述 |
|------|------|------|
| `/b-endpoint/categories/` | GET/POST | 查看/创建分类 |
| `/b-endpoint/categories/{id}` | PUT/DELETE | 编辑/删除分类 |
| `/b-endpoint/products/` | POST | 发布商品 |
| `/b-endpoint/products/{id}` | PUT | 编辑商品 |
| `/b-endpoint/products/{id}/status` | PATCH | 上下架 |
| `/b-endpoint/orders/` | GET | 全部订单 |
| `/b-endpoint/after-sales/` | GET | 全部售后申请 |

### 内部接口（AI 服务调用，需 `X-Internal-Token`）

| 端点 | 描述 |
|------|------|
| `/internal/orders` | 按用户查订单 |
| `/internal/orders/{id}` | 订单详情 |
| `/internal/logistics` | 按用户查物流 |
| `/internal/after-sales` | 按用户查售后 |
| `/internal/products/search` | 商品搜索 |
| `/internal/products/{id}` | 商品详情 |
| `/internal/users/{id}` | 用户信息 |

---

## 🎯 RAG 检索 CLI

项目根目录的 `rag_cli.py` 提供独立的 FAQ 检索命令行工具：

```bash
cd My_LLM_Project
pip install -r requirements.txt

# 构建索引
python rag_cli.py build --force

# 交互式检索（默认 hybrid 模式）
python rag_cli.py interactive

# 单次检索
python rag_cli.py search "门锁没电了怎么办" --mode hybrid
```

检索模式：`dense`（纯语义）+ `sparse`（BM25 关键词）+ `hybrid`（RRF 融合，推荐）。

---

## 🔧 开发模式（不依赖 Docker）

如果你只想调试 `shop-service`，可以只用 Docker 跑数据库，服务在本地启动：

```bash
# 只启动 postgres + redis
docker compose up -d postgres redis

# 本地装依赖并启动
cd shop-service
pip install -r requirements.txt
uvicorn main:app --reload --host 0.0.0.0 --port 8001
```

访问 http://localhost:8001/docs 开始调试。改代码自动热重载（`--reload`）。

---

## 🔍 日志查看

```bash
# 查看 shop-service 日志
docker logs shop-service -f --tail 50

# 查看 Nginx 日志
docker logs nginx -f --tail 50

# 按 request_id 追踪单次请求
docker logs shop-service 2>&1 | grep "abc12345"
```

日志格式：`时间 | 级别 | request_id | 模块:行号 | 消息`

---

## 🐞 常见问题

<details>
<summary><b>Docker 容器启动失败？</b></summary>

```bash
# 清空旧容器和卷，重新启动
docker compose down -v
docker compose up -d
```
</details>

<details>
<summary><b>测试脚本报连接错误？</b></summary>

确保容器已启动且端口未被占用：
```bash
docker compose ps                  # 确认 4 个容器 Up
curl http://localhost:8001/health  # 确认服务响应
```
</details>

<details>
<summary><b>Windows 端口 80 被占用？</b></summary>

修改 `docker-compose.yml` 中 nginx 的端口映射：
```yaml
ports:
  - "8080:80"   # 改为 8080
```
</details>

<details>
<summary><b>想重置数据库？</b></summary>

```bash
docker compose down -v   # -v 会删除数据卷（所有数据丢失）
docker compose up -d     # 重新启动，init.sql 会重新建表
```
</details>

---

## 📚 相关文档

| 文档 | 路径 |
|------|------|
| 需求设计文档 | [`开发文档/需求设计文档_v2.md`](开发文档/需求设计文档_v2.md) |
| 技术设计方案 | [`开发文档/技术设计方案_v2.md`](开发文档/技术设计方案_v2.md) |
| SDD 开发实操指南 | [`开发文档/SDD开发实操指南.md`](开发文档/SDD开发实操指南.md) |
| AI 服务对接指南 | [`开发文档/AI服务对接开发指南.md`](开发文档/AI服务对接开发指南.md) |
| 知识手册 | [`开发文档/知识手册_v2.md`](开发文档/知识手册_v2.md) |
