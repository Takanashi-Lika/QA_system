# 智居商城 — 电商平台 + RAG + AI Agent

轻量级电商平台，覆盖**浏览→购物车→下单→支付→售后**完整交易闭环。集成 **RAG FAQ 检索**、**LLM 智能回复**、**Agent 自然语言购物**。React 前端 + Docker Compose 一键部署。

---

## 🖥 系统架构

```
浏览器 :5173 (前端) / :8080 (Nginx)
    │
    ▼
┌──────────────────────────────────────────────────┐
│  Nginx (反向代理 :8080)                           │
│  /api/shop/*     →  shop-service:8001            │
│  /api/ai/*       →  rag-service:8000             │
└──────────┬──────────────────┬────────────────────┘
           │                  │
    ┌──────┴──────┐    ┌──────┴──────────┐
    ▼             ▼    ▼             ▼   ▼
┌───────────┐ ┌────────────────┐ ┌──────────────────┐
│  Redis 7  │ │  PostgreSQL 16 │ │  rag-service :8000│
│  缓存      │ │  + pgvector    │ │  FAQ检索+LLM+Agent│
│  :6379    │ │  :5432         │ │  (OpenAI tools)   │
└───────────┘ └────────────────┘ └──────────────────┘
         ▲            ▲
         │  ┌─────────┘
         │  │
┌────────┴──┴────────┐
│  shop-service :8001│
│  FastAPI + Python  │
└────────────────────┘
         ▲
         │ HTTP REST
┌────────┴───────────┐
│ React SPA :5173    │
│ 商品浏览·购物车    │
│ 下单·AI客服·Agent  │
└────────────────────┘
```

| 容器 | 端口 | 用途 |
|------|------|------|
| **shop-frontend** (dev) | 5173 | React SPA 可视化界面 |
| **nginx** | 8080 | 统一入口、反向代理 |
| **shop-service** | 8001 | 电商业务 API（FastAPI） |
| **rag-service** | 8000 | FAQ检索 + LLM + Agent 智能购物 |
| **postgres** | 5432 | 关系数据 + 向量数据 (pgvector) |
| **redis** | 6379 | 商品/热门/分类树缓存 |

---

## 📦 技术栈

| 层面 | 选型 |
|------|------|
| 前端 | React 18 + TypeScript + Tailwind CSS + Vite |
| 后端 | Python 3.10 + FastAPI |
| 数据库 | PostgreSQL 16 + pgvector |
| 缓存 | Redis 7（Cache-Aside 模式） |
| 认证 | JWT (PyJWT) + bcrypt 密码加密 |
| LLM | OpenAI SDK → DeepSeek API（兼容 Ollama/vLLM） |
| AI Agent | OpenAI function calling（tools API），零 langchain 依赖 |
| RAG 检索 | ChromaDB + sentence-transformers + BM25 + jieba |
| 部署 | Docker Compose（5 容器） |

---

## 🚀 快速开始（Docker 方式）

### 前置条件

安装 **Docker Desktop** 即可：
- 下载：[docker.com/products/docker-desktop](https://www.docker.com/products/docker-desktop/)

### 1. 配置环境变量

```bash
cp .env.example .env
# 编辑 .env，填入 MODEL_API_KEY（DeepSeek API Key）
# 不填也可以：FAQ 检索正常用，Agent 购物功能需要 Key
```

### 2. 一键启动

```bash
docker compose up -d
```

首次运行约 5-10 分钟（自动拉镜像、pip 装依赖、建表 seed 数据）。

### 3. 启动前端界面

```bash
cd shop-frontend
npm install
npm run dev
```

浏览器打开 **http://localhost:5173**。

### 4. 运行端到端测试

```bash
cd shop-service
pip install httpx
python test_shop.py
```

---

## 🧠 AI Agent — 自然语言下单

**无需模式切换**，直接在 AI 助手对话框里说话：

| 用户输入 | AI 做了什么 |
|----------|------------|
| `帮我买个门锁` | `search_products` → `add_to_cart` → `create_order` |
| `门锁没电了怎么办` | `search_faq` 查知识库 → 自然语言回复 |
| `查看我的订单` | `list_orders` |
| `有哪些摄像头` | `search_products` 列出匹配商品 |

LLM 自动判断用户意图，选择调用 FAQ 检索还是购物工具。Token 自动从登录态获取。

**实现**：[agent/unified_agent.py](agent/unified_agent.py) — 9 个工具 + OpenAI function calling，零 langchain 依赖。

---

## 🔌 API 概览

### RAG 智能客服 / AI Agent

| 端点 | 方法 | 说明 |
|------|------|------|
| `/api/chat` | POST | FAQ 检索 + LLM 生成回复 |
| `/api/chat/unified` | POST | **统一对话**（FAQ检索 + 购物Agent） |
| `/api/search` | POST | 纯 FAQ 检索（不调 LLM） |
| `/api/stats` | GET | 索引统计 |
| `/health` | GET | 健康检查 |

```bash
# FAQ 问答
curl -X POST http://localhost:8000/api/chat \
  -H "Content-Type: application/json" \
  -d '{"question":"门锁没电了怎么办"}'

# 统一对话（自然语言购物，需传 JWT Token）
curl -X POST http://localhost:8000/api/chat/unified \
  -H "Content-Type: application/json" \
  -d '{"messages":[{"role":"user","content":"帮我买个门锁"}],"user_token":"eyJ..."}'
```

### 电商 API（部分）

| 端点 | 方法 | 说明 | 需登录 |
|------|------|------|--------|
| `/c-endpoint/register` | POST | 注册 | ✗ |
| `/c-endpoint/login` | POST | 登录 | ✗ |
| `/c-endpoint/products` | GET | 商品列表/搜索/分类 | ✗ |
| `/c-endpoint/products/{id}` | GET | 商品详情 | ✗ |
| `/c-endpoint/cart/` | GET/POST | 查看/添加购物车 | ✓ |
| `/c-endpoint/orders/` | GET/POST | 订单列表/创建 | ✓ |
| `/c-endpoint/orders/{id}/pay` | POST | 支付 | ✓ |

---

## 🧪 curl 快速走通购物流程

```bash
TOKEN=$(curl -s -X POST http://localhost:8001/c-endpoint/login \
  -H "Content-Type: application/json" \
  -d '{"email":"admin@shop.local","password":"admin123"}' | jq -r .data.token)

curl "http://localhost:8001/c-endpoint/products?keyword=门锁"
curl -X POST http://localhost:8001/c-endpoint/cart/ \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"product_id":1,"quantity":1}'
curl -X POST http://localhost:8001/c-endpoint/orders/ \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"address":"广东省深圳市南山区"}'
# 返回订单ID后用下面命令支付
curl -X POST http://localhost:8001/c-endpoint/orders/1/pay \
  -H "Authorization: Bearer $TOKEN"
```

### 预置账号

| 角色 | 邮箱 | 密码 |
|------|------|------|
| 管理员 | `admin@shop.local` | `admin123` |

---

## 📁 项目结构

```
My_LLM_Project/
├── shop-frontend/               # React 前端 SPA
│   └── src/
│       ├── App.tsx              #   主入口 + Tab 切换
│       ├── api.ts               #   全部 API 封装
│       ├── context/AuthContext.tsx  # JWT 登录态
│       ├── components/          #   Navbar/CartDrawer/ProductCard 等
│       └── pages/               #   HomeTab/OrdersTab/AiChatTab
│
├── shop-service/                # 电商服务（核心）
│   ├── main.py                  #   FastAPI 入口
│   ├── apps/                    #   API 路由层 (c/b/internal/common)
│   ├── domain/                  #   业务逻辑层 (user/product/cart/order)
│   ├── infrastructure/          #   DB/Redis/Scheduler
│   ├── Dockerfile
│   └── test_shop.py            #   端到端测试
│
├── agent/                       # AI Agent 模块（无 langchain 依赖）
│   └── unified_agent.py        #   UnifiedAgent: 9 工具 + function calling
│
├── rag/                         # RAG 检索模块
│   └── store.py                #   ChromaDB + 混合检索 (dense+sparse)
│
├── model/                       # LLM 客户端（OpenAI 兼容）
├── retriever/                   # 检索编排（FAQ检索→LLM回复）
├── api/                         # RAG API 服务（FastAPI）
│   └── routes.py               #   /api/chat + /api/chat/unified
│
├── rag_resource/                # FAQ 知识库 (5 个产品线)
├── nginx/nginx.conf             # Nginx 反向代理
├── init.sql                     # 建表 + 25 个商品种子数据
├── docker-compose.yml           # 5 容器编排
├── requirements.txt             # Python 依赖
└── .env.example                 # 环境变量模板
```

---

## 📚 相关文档

| 文档 | 路径 |
|------|------|
| 前端 PRD | [.trae/documents/PRD.md](.trae/documents/PRD.md) |
| 前端技术架构 | [.trae/documents/技术架构.md](.trae/documents/技术架构.md) |
| 电商需求设计 | [开发文档/需求设计文档_v2.md](开发文档/需求设计文档_v2.md) |
| 电商技术设计 | [开发文档/技术设计方案_v2.md](开发文档/技术设计方案_v2.md) |

---

## 🐞 常见问题

<details>
<summary><b>Docker 容器启动失败？</b></summary>

```bash
docker compose down -v
docker compose up -d
```
</details>

<details>
<summary><b>AI 回复"服务不可用"？</b></summary>

`.env` 里需要有效的 `MODEL_API_KEY`。不填 Key 时 FAQ 检索也正常用（回退显示知识库内容）。
</details>

<details>
<summary><b>全部商品只显示 5 条？</b></summary>

这是旧版 Bug，已修。`docker compose up -d --build shop-service` 重建即可。
</details>

<details>
<summary><b>想重置数据库？</b></summary>

```bash
docker compose down -v
docker compose up -d
```
</details>
