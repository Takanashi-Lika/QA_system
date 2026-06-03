# 电商平台 Shop-Service 开发任务清单

> 依据：需求设计文档 v5.4 + 技术设计方案 v2.1 + SDD 开发实操指南（依赖分析）

---

## 第一阶段：基础设施层（无业务依赖，最先构建）

本阶段搭建项目骨架、中间件、公共模块和基础设施，为后续所有业务模块提供"地基"。

### Task 1.1: 项目骨架搭建
- [x] 创建 `shop-service/` 目录结构（apps/c_endpoint/..., apps/b_endpoint/..., apps/internal/, domain/..., infrastructure/, middleware/, common/, data/）
- [x] 每个目录放置 `__init__.py`
- [x] 编写 `requirements.txt`（fastapi, psycopg2, redis-py, pyjwt, bcrypt, apscheduler, uvicorn, httpx）
- [x] 编写 `.env` 文件（DATABASE_URL, REDIS_URL, JWT_SECRET, INTERNAL_API_TOKEN, LOG_LEVEL）
- [x] 编写 `Dockerfile`（Python 3.10.10 基础镜像）

### Task 1.2: 公共模块 — 异常树
- [x] 创建 `common/exceptions.py`，定义 `ShopException` 基类 + 7 个子类
  - `ValidationError`(40001, 400) / `AuthenticationError`(40101, 401) / `PermissionDeniedError`(40301, 403) / `NotFoundError`(40401, 404) / `BusinessError`(42201, 422) / `DatabaseError`(50001, 500) / `InternalError`(50002, 500)
- [x] 创建 `common/context.py`，定义 `request_id_var: ContextVar[str]`
- [x] 创建 `common/logger.py`，实现 `RequestIDFilter` + `setup_logger()`（StreamHandler→stdout，格式：`时间 | 级别 | request_id | 模块:行号 | 消息`）

### Task 1.3: 中间件层
- [x] 创建 `middleware/request_id.py`：从请求头读取/生成 8 位 UUID → 写入 ContextVar → 回写响应头
- [x] 创建 `middleware/request_log.py`：记录方法、路径、状态码、耗时（毫秒）
- [x] 创建 `middleware/exception_handler.py`：全局捕获 `ShopException` → 映射为 `{code, message, request_id}` JSON 响应；兜底捕获 `Exception` → 50002

### Task 1.4: 基础设施 — 数据库与连接池
- [x] 创建 `infrastructure/database.py`：`ThreadedConnectionPool`（min=2, max=10, search_path='shop'）
- [x] 实现 `get_connection()` / `release_connection()` 函数
- [x] 实现 `get_cursor()` 上下文管理器（自动 commit/rollback + 归还连接）

### Task 1.5: 基础设施 — Redis 客户端
- [x] 创建 `infrastructure/redis_client.py`：`init_redis()` / `get_cache()` / `set_cache()` / `delete_cache()` / `delete_keys()`
- [x] Redis 不可用时降级（try/except 返回 None，不抛异常）
- [x] 实现缓存互斥锁 `CacheLocks`（防止缓存击穿）

### Task 1.6: 基础设施 — Scheduler 定时任务
- [x] 创建 `infrastructure/scheduler.py`：`BackgroundScheduler`（5分钟间隔，misfire_grace_time=60s，coalesce=True）
- [x] 实现 `start_scheduler()` / `shutdown_scheduler()`，预留 `add_job` 注册接口

### Task 1.7: 认证与鉴权模块
- [x] 创建 `apps/common/auth.py`：`get_current_user()`（解码 JWT 返回 `{user_id, email, role}`）
- [x] 实现 `get_current_admin()`（调用 `get_current_user` + 校验 `role == 'admin'`）
- [x] 实现 `verify_internal_token()`（校验 `X-Internal-Token` Header）
- [x] JWT 签发逻辑在用户模块中实现，此处仅提供解码验证

---

## 第二阶段：业务模块 — C 端（按依赖顺序）

本阶段实现 C 端全部 P0 功能。模块间有部分依赖，按依赖链顺序开发：用户 → 分类 → 商品 → 购物车 → 订单 → 物流 → 售后。

### Task 2.1: 用户模块
- [x] 创建 `domain/user/user_service.py`：注册（邮箱唯一校验 + bcrypt + INSERT）、登录（bcrypt 比对 + JWT 签发 24h）、获取个人信息、更新地址
- [x] 创建 `apps/c_endpoint/user/router.py`：POST `/register`、POST `/login`、GET `/me`、PUT `/address`
- [x] 创建 `apps/c_endpoint/user/schema.py`：Pydantic 请求体（邮箱格式校验、密码 ≥6 位）
- [x] 更新 `domain/user/__init__.py` 和 `apps/c_endpoint/user/__init__.py`

### Task 2.2: 分类模块 — B 端
- [x] 创建 `domain/category/category_service.py`：创建分类、编辑分类、删除分类（检查商品引用）、获取分类树（含缓存）
- [x] 创建 `apps/b_endpoint/category/router.py`：POST/PUT/DELETE/GET 分类（admin 权限）
- [x] 创建 `apps/b_endpoint/category/schema.py`：Pydantic 请求体
- [x] 更新 `domain/category/__init__.py` 和 `apps/b_endpoint/category/__init__.py`

### Task 2.3: 商品模块 — C 端 + B 端
- [x] 创建 `domain/product/product_service.py`：
  - C 端：分类浏览（含子分类）、关键词搜索（ILIKE）、商品详情（Cache-Aside）、热门商品列表
  - B 端：发布商品（删除 `hot:products:list` 缓存）、编辑商品（删除 `product:{id}` + `hot:products:list` 缓存）、上下架（同上）
- [x] 创建 `apps/c_endpoint/product/router.py`：GET 列表/详情/搜索/热门
- [x] 创建 `apps/b_endpoint/product/router.py`：POST/PUT/PATCH 状态（admin 权限）
- [x] 创建 `apps/c_endpoint/product/schema.py` 和 `apps/b_endpoint/product/schema.py`
- [x] 更新 `domain/product/__init__.py` 和相关 `apps/` 的 `__init__.py`

### Task 2.4: 购物车模块
- [x] 创建 `domain/cart/cart_service.py`：添加（UPSERT 幂等，校验库存上限）、修改数量、删除、查看（JOIN products）
- [x] 创建 `apps/c_endpoint/cart/router.py`：POST/PUT/DELETE/GET（需登录）
- [x] 创建 `apps/c_endpoint/cart/schema.py`
- [x] 更新 `domain/cart/__init__.py` 和 `apps/c_endpoint/cart/__init__.py`

### Task 2.5: 订单模块
- [x] 创建 `domain/order/order_service.py`：
  - `create_order()`：手动事务 — FOR UPDATE 锁库存 → 校验 → 扣减 → INSERT orders + order_items（快照）→ DELETE cart_items → COMMIT
  - `pay_order()`：手动事务 — FOR UPDATE 锁订单 → 校验 status=pending → UPDATE paid → INSERT payment_records → COMMIT
  - `cancel_order()`：手动事务 — FOR UPDATE 锁订单 → 校验 status=pending → UPDATE cancelled → 回滚库存（SET stock = stock + quantity）→ COMMIT
  - `cancel_timeout_orders()`：逐条独立事务，二次校验防竞态
  - `get_order_list()` / `get_order_detail()`：校验归属
- [x] 创建 `apps/c_endpoint/order/router.py`：POST 创建/POST 支付/DELETE 取消/GET 列表/GET 详情
- [x] 创建 `apps/c_endpoint/order/schema.py`
- [x] 更新 `domain/order/__init__.py` 和 `apps/c_endpoint/order/__init__.py`

### Task 2.6: 物流模块
- [x] 创建 `domain/logistics/logistics_service.py`：按 order_id 查询物流记录（含状态、运输节点 timeline、预计送达）
- [x] 创建 `apps/c_endpoint/logistics/router.py`：GET 物流信息（校验归属 + 订单状态为 paid）
- [x] 更新 `domain/logistics/__init__.py` 和 `apps/c_endpoint/logistics/__init__.py`

### Task 2.7: 售后模块
- [x] 创建 `domain/after_sale/after_sale_service.py`：提交售后申请（校验 order status=paid + 归属）、查询售后进度
- [x] 创建 `apps/c_endpoint/after_sale/router.py`：POST 申请/GET 查询
- [x] 创建 `apps/c_endpoint/after_sale/schema.py`
- [x] 更新 `domain/after_sale/__init__.py` 和 `apps/c_endpoint/after_sale/__init__.py`

---

## 第三阶段：业务模块 — B 端与管理功能

### Task 3.1: B 端订单查看
- [x] 创建 `apps/b_endpoint/order/router.py`：GET 全部订单列表（admin 权限，支持按状态筛选，只读）
- [x] 更新 `apps/b_endpoint/order/__init__.py`

### Task 3.2: B 端售后审核（P1，保留接口）
- [x] 创建 `apps/b_endpoint/after_sale/router.py`：PUT 审核售后（通过/驳回/确认完成），保持接口结构但标记 P1
- [x] 更新 `apps/b_endpoint/after_sale/__init__.py`

---

## 第四阶段：内部接口层

### Task 4.1: 内部查询接口
- [x] 创建 `apps/internal/router.py`，实现 7 个 GET 端点（全部通过 `Depends(verify_internal_token)` 保护）：
  - `GET /internal/orders` — 用户订单列表（按 user_id 过滤）
  - `GET /internal/orders/{order_id}` — 订单详情（含 order_items 明细）
  - `GET /internal/logistics` — 用户物流信息（按 user_id 过滤）
  - `GET /internal/after-sales` — 用户售后申请（按 user_id 过滤）
  - `GET /internal/products/search` — 关键词搜索商品
  - `GET /internal/products/{product_id}` — 商品详情
  - `GET /internal/users/{user_id}` — 用户基本信息
- [x] 统一返回格式 `{code: 0, data: {...}, message: "success"}`，列表接口含 `page/size` 分页
- [x] 更新 `apps/internal/__init__.py`

---

## 第五阶段：集成与入口组装

### Task 5.1: 主入口 main.py
- [x] 创建 `shop-service/main.py`：
  - `lifespan`：init pool → init redis → start scheduler → register 定时任务 → yield → shutdown
  - 注册中间件链（RequestID → RequestLog → CORS）
  - 挂载全部路由（8 个 C 端 Router + 4 个 B 端 Router + 1 个内部 Router）
  - `/health` 健康检查端点
  - CORS 允许所有来源（开发阶段）
- [x] 将项目根目录的旧 `main.py`（RAG CLI）重命名为 `rag_cli.py`，或移至 `rag/` 目录下

---

## 第六阶段：部署配置

### Task 6.1: 数据库初始化 SQL
- [x] 创建 `init.sql`：
  - pgvector 扩展 + shop schema 8 张表 + customer_service schema 3 张表（完整 DDL，含全部索引）
  - 部分索引 `idx_orders_pending_time WHERE status='pending'`
  - 预置种子数据：管理员账号（bcrypt 哈希）、9 个分类、10 个 on_sale 商品、物流/售后演示数据

### Task 6.2: Nginx 配置
- [x] 创建 `nginx/nginx.conf`：
  - `/api/shop/*` → shop-service:8001
  - `/api/shop/internal/*` 拦截返回 403（内部接口不对外暴露）
  - CORS 头设置

### Task 6.3: Docker Compose 编排
- [x] 创建 `docker-compose.yml`（4 容器）：
  - nginx（alpine, 80:80）
  - shop-service（build, 环境变量注入, depends_on postgres + redis healthy）
  - postgres（pgvector/pgvector:pg16, init.sql 挂载, healthcheck pg_isready）
  - redis（7-alpine, healthcheck redis-cli ping）
  - 全部容器 json-file 日志驱动（max-size=10m, max-file=3）
  - 数据卷 pgdata + redisdata 持久化

---

## 第七阶段：测试与验证

### Task 7.1: 端到端集成测试
- [x] 创建 `test_e2e.py`（需与项目根目录已有 `test_e2e.py` 区分）：
  - 测试模块（≥13 个模块，≥35 条断言）：
    1. 健康检查
    2. 用户注册（正常 + 重复注册拒绝 + 密码校验）
    3. 用户登录（正常 + 错误密码拒绝）
    4. 个人信息（获取 + 更新地址）
    5. 商品浏览（分类树 + 热门 + 列表 + 搜索 + 详情 + 不存在 404）
    6. 购物车（添加 + UPSERT 幂等 + 修改数量 + 删除）
    7. 订单创建（正常创建 + 库存不足拒绝）
    8. 订单支付（正常支付 + 重复支付拒绝 + 已取消不可支付）
    9. 订单查询（列表 + 详情 + 明细）
    10. 物流追踪（按订单查询）
    11. 售后申请（申请 + 查看进度）
    12. 管理员功能（登录 + 查看全部订单 + 分类管理 + 商品管理）
    13. 权限隔离（普通用户访问 B 端被拒 + 无 Token 401）
    14. 内部接口（Token 认证 + user_id 过滤）
  - 断言期望值来源于需求文档 §14.4 异常码表
  - 关键步骤失败直接终止测试（如登录失败）

---

# 任务依赖关系

```
第一阶段（基础设施 — 全部 P0，无业务依赖，可并行）
  ├── Task 1.1 骨架  ← 必须先做
  ├── Task 1.2 公共模块  ← 可并行于 1.1
  ├── Task 1.3 中间件  ← 依赖 1.2（异常树）
  ├── Task 1.4 数据库  ← 可并行
  ├── Task 1.5 Redis  ← 可并行
  ├── Task 1.6 Scheduler  ← 可并行
  └── Task 1.7 认证   ← 可并行，依赖 JWT_SECRET 环境变量

第二阶段（C 端业务 — 按依赖顺序）
  ├── Task 2.1 用户  ← 依赖 1.2 + 1.4
  ├── Task 2.2 分类  ← 依赖 1.2 + 1.4 + 1.5；可与 2.1 并行
  ├── Task 2.3 商品  ← 依赖 1.2 + 1.4 + 1.5 + 2.2（分类表）；可与 2.1 并行
  ├── Task 2.4 购物车  ← 依赖 2.1 + 2.3
  ├── Task 2.5 订单   ← 依赖 2.1 + 2.3 + 2.4（下单后清空购物车）
  ├── Task 2.6 物流   ← 依赖 2.5
  └── Task 2.7 售后   ← 依赖 2.5

第三阶段（B 端管理）
  ├── Task 3.1 B端订单 ← 依赖 2.5 + 1.7（admin 鉴权）
  └── Task 3.2 B端售后 ← 依赖 2.7 + 1.7

第四阶段（内部接口 — 依赖全部 domain 模块）
  └── Task 4.1 内部接口  ← 依赖 2.1~2.7 全部

第五阶段（入口组装 — 依赖全部模块）
  └── Task 5.1 main.py  ← 依赖 1.x + 2.x + 3.x + 4.x

第六阶段（部署配置 — 不依赖代码模块，可提前并行）
  ├── Task 6.1 init.sql  ← 可提前做
  ├── Task 6.2 nginx    ← 可提前做
  └── Task 6.3 docker-compose ← 可提前做

第七阶段（测试）
  └── Task 7.1 测试脚本  ← 依赖 5.1（服务可运行）
```

# 并行执行建议

| 批次 | 可并行任务 | 说明 |
|------|-----------|------|
| 第1批 | Task 1.1 + Task 1.2 + Task 1.4 + Task 1.5 + Task 1.6 + Task 6.1 + Task 6.2 + Task 6.3 | 骨架、公共模块、基础设施、部署配置互不依赖 |
| 第2批 | Task 1.3 + Task 1.7 | 中间件依赖异常树，认证依赖环境变量 |
| 第3批 | Task 2.1 + Task 2.2 + Task 2.3 | 用户、分类、商品可并行 |
| 第4批 | Task 2.4 | 购物车依赖用户和商品 |
| 第5批 | Task 2.5 | 订单依赖购物车 |
| 第6批 | Task 2.6 + Task 2.7 + Task 3.1 + Task 3.2 | 物流、售后、B端管理可并行 |
| 第7批 | Task 4.1 | 内部接口依赖全部 domain |
| 第8批 | Task 5.1 | 主入口依赖全部 |
| 第9批 | Task 7.1 | 测试依赖服务可运行 |
