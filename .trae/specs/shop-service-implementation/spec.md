# 电商平台 Shop-Service 实现 Spec

## Why
项目当前仅有 RAG 检索原型（CLI 工具），缺少完整的电商业务支撑。需基于已有的《需求设计文档 v5.4》和《技术设计方案 v2.1》，构建覆盖用户→商品→订单→支付→物流→售后的完整电商服务（shop-service），并预留内部接口供外部 AI 客服服务集成。

## What Changes
- 新建 shop-service 项目骨架（目录结构、Dockerfile、依赖配置）
- 实现基础设施层（数据库连接池、Redis 客户端、APScheduler、中间件、日志系统、异常树）
- 实现 C 端业务模块（用户注册登录、商品浏览搜索、购物车、下单支付、订单管理、物流追踪、售后申请）
- 实现 B 端业务模块（分类管理、商品管理、订单查看）
- 实现内部查询接口（7 个 `/internal/*` 端点供外部 AI 客服调用）
- 实现主入口 main.py（FastAPI lifespan + 路由挂载 + 健康检查）
- 实现部署配置（Nginx 配置、init.sql 建表+种子数据、Docker Compose 编排）
- 编写端到端集成测试脚本
- **BREAKING**: 将现有 `main.py`（RAG CLI）重命名/迁移，新的 `main.py` 为 shop-service 入口

## Impact
- Affected specs: 无（首个 spec）
- Affected code: 整个项目目录结构需重新组织，现有 `main.py`/`rag/`/`model/` 作为历史代码保留

## ADDED Requirements

### Requirement: 项目骨架搭建
系统 SHALL 创建符合技术方案 §2.3 约定的目录结构（shop-service/apps/domain/infrastructure/middleware/common），包含 Dockerfile、requirements.txt、.env。

#### Scenario: 骨架就绪
- **WHEN** 执行骨架创建任务
- **THEN** 所有目录及 `__init__.py`、Dockerfile、requirements.txt、.env 均就绪

### Requirement: 数据库初始化
系统 SHALL 通过 `init.sql` 完成 PostgreSQL 建表（shop schema 8 张核心表 + customer_service schema 3 张表）及预置种子数据（管理员账号、9 个分类、10 个商品），含所需索引（部分索引 `idx_orders_pending_time`）和 pgvector 扩展。

#### Scenario: 建表成功
- **WHEN** PostgreSQL 容器首次启动
- **THEN** `docker-entrypoint-initdb.d/init.sql` 自动执行，全部表、索引、种子数据就绪

### Requirement: 基础设施层
系统 SHALL 实现 ThreadedConnectionPool（min=2, max=10）、Redis 客户端（Cache-Aside 模式封装）、APScheduler BackgroundScheduler、RequestIDMiddleware + RequestLogMiddleware + 全局异常处理器、统一 Logger（stdout + RequestIDFilter）、7 子类异常树。

#### Scenario: 基础设施完整
- **WHEN** shop-service 启动
- **THEN** lifespan 中 DB 连接池、Redis 客户端、Scheduler 全部初始化成功，中间件链正常工作

### Requirement: C 端业务功能
系统 SHALL 实现全部 19 个 P0 C 端功能点（FC1~FC19），覆盖用户注册/登录/JWT、商品浏览/搜索/详情（含 Redis 缓存）、购物车 CRUD（UPSERT 幂等）、下单（FOR UPDATE 事务锁库存）、支付（幂等）、取消订单（回滚库存）、订单列表/详情、物流追踪、售后申请/查询。

#### Scenario: 完整购物流程
- **WHEN** 用户注册→登录→浏览商品→加入购物车→创建订单→模拟支付
- **THEN** 每步均返回正确响应，订单状态从 pending→paid，购物车被清空，库存被正确扣减

### Requirement: B 端业务功能
系统 SHALL 实现全部 7 个 P0 B 端功能点（FB1~FB7），覆盖分类管理（二级树增删改查）、商品管理（CRUD+上下架，含缓存删除）、查看全部订单。FB8（售后审核）为 P1，仅保留接口。

#### Scenario: 管理员管理商品
- **WHEN** 管理员登录→创建分类→发布商品→编辑商品→上下架
- **THEN** 每步返回正确响应，每次写操作后相关 Redis 缓存被正确删除

### Requirement: 内部查询接口
系统 SHALL 实现 7 个 `/internal/*` GET 端点，供外部 AI 客服通过 `X-Internal-Token` 认证调用，按 `user_id` 过滤确保数据隔离，统一返回 `{code, data, message}` 格式。

#### Scenario: AI 服务查询用户订单
- **WHEN** AI 服务携带 `X-Internal-Token` 调用 `GET /internal/orders?user_id=42`
- **THEN** 返回该用户订单列表，无 `X-Internal-Token` 则返回 401

### Requirement: 定时任务
系统 SHALL 通过 APScheduler 每 5 分钟扫描超时 pending 订单（>30 分钟），逐条独立事务取消并回滚库存（FOR UPDATE + 二次校验防竞态）。

#### Scenario: 超时订单自动取消
- **WHEN** 订单创建超过 30 分钟仍未支付
- **THEN** 下一个定时任务周期自动取消该订单，库存回滚，日志记录

### Requirement: 容器化部署
系统 SHALL 提供 Docker Compose 编排（4 容器：nginx + shop-service + postgres + redis），含健康检查、日志轮转、数据卷持久化。`docker compose up -d` 一键启动。

#### Scenario: 一键部署
- **WHEN** 执行 `docker compose up -d`
- **THEN** 4 个容器全部成功启动，`/health` 返回 200

### Requirement: 端到端测试
系统 SHALL 提供集成测试脚本，覆盖完整电商主流程（13 个测试模块，≥35 条断言），测试断言期望值来源于需求文档验收规则和异常码定义。

#### Scenario: 全流程测试通过
- **WHEN** 执行测试脚本
- **THEN** 所有测试模块均通过，注册、登录、商品浏览、购物车、下单、支付、取消、物流、售后、管理员功能、权限隔离全部验证
