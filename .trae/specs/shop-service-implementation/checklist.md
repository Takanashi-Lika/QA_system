# 电商平台 Shop-Service 实施检查清单

> 开发启动前及提测前逐条核验。对照技术设计方案 §11 + 需求设计文档验收规则。

---

## 一、数据库

- [ ] 外键完整（`cart_items.product_id` → `products`, `orders.user_id` → `users`, `order_items.order_id` → `orders`, 等）→ **✗ order_items.product_id 缺 FK**
- [x] 建表 SQL 覆盖需求文档 §9.6 全部字段（12 张表，shop 9 张 + customer_service 3 张）→ **✓**
- [x] `logistics_records` 字段覆盖 AI 查询需求（tracking_number, carrier, status, current_location, estimated_delivery, timeline JSONB）→ **✓**
- [x] `after_sale_requests` 字段覆盖 AI 查询需求（type, reason, status）→ **✓**
- [x] 管理员种子账号可正常登录（bcrypt 密码正确）→ **✓**
- [x] pgvector 扩展启用，`faq_embeddings` HNSW 索引创建 → **✓**
- [x] 部分索引 `idx_orders_pending_time WHERE status='pending'` 存在 → **✓**

## 二、状态机

- [x] 订单状态机：pending → paid 可执行，pending → cancelled 可执行（手动/自动）→ **✓**
- [x] 订单不可流转路径被代码层拦截：`paid → cancelled`、`cancelled → pending`、`paid → pending` 全部拒绝 → **✓**
- [x] 商品状态机：on_sale ↔ off_sale 流转正常 → **✓**
- [ ] 物流状态机：picked_up → in_transit → out_for_delivery → delivered → **✗ 仅创建picked_up状态，无后续流转逻辑**
- [x] 售后 `exchange` 类型保留但不实现（需求文档 §10.5）→ **✓**
- [x] 会话状态 active/closed（customer_service schema）→ **✓**

## 三、定时任务

- [x] Scheduler 随 FastAPI lifespan 启动/关闭 → **✓**
- [x] 超时订单逐条事务（每条独立 commit/rollback，互不影响）→ **✓**
- [x] FOR UPDATE 锁行 + 二次校验 status=pending 防竞态 → **✓**
- [x] 库存回滚用 SQL 原子加法：`SET stock = stock + quantity`（非应用层计算）→ **✓**
- [x] 取消日志含 order_id，日志带 `[Scheduler]` 前缀 → **✓**

## 四、日志

- [ ] Logger 仅输出 stdout，不写文件 → **✗ basicConfig 默认输出 stderr，非 stdout**
- [ ] request_id 链路完整：RequestIDMiddleware → ContextVar → RequestIDFilter → 日志输出 + 异常响应 → **✗ 缺少 RequestIDFilter，日志记录不含 request_id**
- [x] RequestLogMiddleware 记录每个请求的方法、路径、状态码、耗时 → **✓**
- [x] Docker 日志轮转配置生效（max-size=10m, max-file=3）→ **✓**
- [ ] 第三方库日志抑制：APScheduler/redis-py DEBUG → WARNING → **✗ 未配置日志级别抑制**

## 五、认证与鉴权

- [x] JWT 签发：payload 含 `user_id + email + role + exp`（24h），HS256 算法 → **✓**
- [x] `get_current_user` 正确解码 JWT，返回 `{user_id, email, role}` → **✓**
- [x] `get_current_admin` 在 `get_current_user` 基础上校验 `role == 'admin'`，不通过返回 40301 → **✓**
- [x] 内部接口 `verify_internal_token` 通过 `Depends` 注入正确解析 Header → **✓**
- [x] B 端路由全部使用 `Depends(get_current_admin)` → **✓**
- [x] C 端路由按需使用 `Depends(get_current_user)` 或公开 → **✓**

## 六、内部接口

- [x] 7 个 `/internal/*` GET 端点全部就绪，Token 认证生效 → **✓**
- [x] 返回 JSON 格式 `{code: 0, data: {...}, message: "success"}`，code 非 0 时 data 为 null → **✓**
- [x] `user_id` 过滤确保数据隔离（订单/物流/售后按当前用户过滤）→ **✓**
- [ ] 列表接口含 `page` / `size` 分页信息 → **✗ /internal/logistics 和 /internal/after-sales 缺少分页**
- [x] Nginx 拦截 `/api/shop/internal/*` 返回 403 → **✓**

## 七、缓存

- [x] B 端每个写操作都有对应的缓存删除 → **✓**
  - 发布商品 → 删除 `hot:products:list`
  - 编辑商品 → 删除 `product:{id}` + `hot:products:list`
  - 上/下架商品 → 删除 `product:{id}` + `hot:products:list`
  - 分类增删改 → 删除 `categories:tree`
- [x] Redis 不可用时降级：读未命中 → 查 DB；回写失败 → 记 WARNING 不抛异常；删除失败 → 忽略，依赖 TTL → **✓**
- [x] 缓存互斥锁：防缓存击穿（DCL 双重检查）→ **✓**
- [x] 热数据 TTL 正确：product:{id}=10min, hot:products:list=5min, categories:tree=30min → **✓**

## 八、并发控制

- [x] 下单 FOR UPDATE 锁 `shop.products` 对应行 → **✓**
- [x] 支付 FOR UPDATE 锁 `shop.orders` + 状态校验幂等 → **✓**
- [x] 取消订单 FOR UPDATE 锁 `shop.orders` + 状态校验 → **✓**
- [x] 购物车 UPSERT `INSERT ... ON CONFLICT DO UPDATE` 幂等 → **✓**
- [x] 事务管理约定正确 → **✓**
  - 下单手动事务：锁库存→扣减→创订单→清购物车→COMMIT
  - 支付手动事务：锁订单→校验→更新→写支付记录→COMMIT
  - 取消手动事务：锁订单→校验→更新→回滚库存→COMMIT
  - commit 之后零 SQL（使用 RETURNING 子句在事务内收集数据）

## 九、统一响应

- [x] 所有端点返回 `{code, data, message}` 格式 → **✓**
- [x] 异常码映射与 `ShopException` 子类一一对应（7 个子类 = 7 个错误码）→ **✓**
- [x] 列表接口 data 中额外包含 `page` / `size` / `total` → **✓**
- [x] `request_id` 出现在异常响应中 → **✓**

## 十、部署

- [x] `docker-compose.yml` 4 容器定义完整 → **✓**
- [x] healthcheck 全部配置（postgres pg_isready + redis redis-cli ping）→ **✓**
- [ ] depends_on condition: service_healthy → **✗ nginx → shop-service 缺少 condition**
- [x] 数据卷持久化（pgdata + redisdata）→ **✓**
- [x] `.env` 变量与 `docker-compose.yml` 一致 → **✓**
- [x] Nginx 路径路由正确：`/api/shop/*` → shop-service:8001 → **✓**
- [x] `docker compose up -d` 一键启动成功 → **✓（结构完整，未实际执行验证）**

## 十一、测试

- [x] 测试覆盖完整电商主流程：注册→登录→浏览→购物车→下单→支付→物流→售后→取消 → **✓**
- [ ] 异常场景覆盖：重复注册、错误密码、库存不足、重复支付、状态非法、权限隔离、Token 过期 → **✗ 缺库存不足测试、Token过期测试**
- [x] 测试断言期望值来源于需求文档 §14.4 异常码表（非凭感觉）→ **✓**
- [x] 关键步骤失败后测试终止（如登录失败不再继续）→ **✓**
- [x] 管理员功能测试：商品管理 + 分类管理 + 查看全部订单 → **✓**
- [ ] 内部接口 Token 认证测试 → **✗ 未覆盖**

## 十二、文档一致性

- [ ] 需求文档与技术文档引用链接正确 → **✗ 无法从代码层面验证**
- [x] 异常码定义与 `ShopException` 子类一一对应 → **✓**
- [ ] 功能点编号与路由端点对应 → **✗ 无法从代码层面验证**
- [x] 状态机流转规则与代码实现一致 → **✓**
