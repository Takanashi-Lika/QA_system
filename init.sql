-- ============================================================================
-- PostgreSQL Database Initialization Script
-- Auto-executed on container first start
-- ============================================================================

-- 1. pgvector Extension
-- ============================================================================
CREATE EXTENSION IF NOT EXISTS vector;

-- ============================================================================
-- 2. shop Schema (9 tables)
-- ============================================================================
CREATE SCHEMA IF NOT EXISTS shop;

-- 2.1 shop.categories
CREATE TABLE shop.categories (
    id          SERIAL PRIMARY KEY,
    name        VARCHAR(100) NOT NULL,
    parent_id   INTEGER REFERENCES shop.categories(id),
    sort_order  INTEGER DEFAULT 0,
    created_at  TIMESTAMPTZ DEFAULT NOW()
);

-- 2.2 shop.products
CREATE TABLE shop.products (
    id          SERIAL PRIMARY KEY,
    name        VARCHAR(255) NOT NULL,
    description TEXT,
    price       DECIMAL(10,2) NOT NULL,
    image_url   VARCHAR(500),
    stock       INTEGER NOT NULL CHECK (stock >= 0),
    category_id INTEGER REFERENCES shop.categories(id),
    status      VARCHAR(20) DEFAULT 'on_sale',
    created_at  TIMESTAMPTZ DEFAULT NOW(),
    updated_at  TIMESTAMPTZ DEFAULT NOW()
);

-- 2.3 shop.users
CREATE TABLE shop.users (
    id          SERIAL PRIMARY KEY,
    email       VARCHAR(255) NOT NULL UNIQUE,
    password    VARCHAR(255) NOT NULL,
    nickname    VARCHAR(100),
    role        VARCHAR(20) DEFAULT 'user',
    address     TEXT,
    created_at  TIMESTAMPTZ DEFAULT NOW(),
    updated_at  TIMESTAMPTZ DEFAULT NOW()
);

-- 2.4 shop.cart_items
CREATE TABLE shop.cart_items (
    id          SERIAL PRIMARY KEY,
    user_id     INTEGER NOT NULL REFERENCES shop.users(id),
    product_id  INTEGER NOT NULL REFERENCES shop.products(id),
    quantity    INTEGER NOT NULL CHECK (quantity > 0),
    created_at  TIMESTAMPTZ DEFAULT NOW(),
    UNIQUE (user_id, product_id)
);

-- 2.5 shop.orders
CREATE TABLE shop.orders (
    id            SERIAL PRIMARY KEY,
    user_id       INTEGER NOT NULL REFERENCES shop.users(id),
    total_amount  DECIMAL(10,2) NOT NULL,
    status        VARCHAR(20) DEFAULT 'pending',
    address       TEXT,
    created_at    TIMESTAMPTZ DEFAULT NOW(),
    paid_at       TIMESTAMPTZ,
    cancelled_at  TIMESTAMPTZ
);

-- 2.6 shop.order_items
CREATE TABLE shop.order_items (
    id           SERIAL PRIMARY KEY,
    order_id     INTEGER NOT NULL REFERENCES shop.orders(id),
    product_id   INTEGER NOT NULL,
    product_name VARCHAR(255) NOT NULL,
    price        DECIMAL(10,2) NOT NULL,
    quantity     INTEGER NOT NULL,
    created_at   TIMESTAMPTZ DEFAULT NOW()
);

-- 2.7 shop.payment_records
CREATE TABLE shop.payment_records (
    id          SERIAL PRIMARY KEY,
    order_id    INTEGER NOT NULL REFERENCES shop.orders(id),
    amount      DECIMAL(10,2) NOT NULL,
    method      VARCHAR(50) DEFAULT 'mock',
    status      VARCHAR(20) DEFAULT 'success',
    created_at  TIMESTAMPTZ DEFAULT NOW()
);

-- 2.8 shop.logistics_records
CREATE TABLE shop.logistics_records (
    id                  SERIAL PRIMARY KEY,
    order_id            INTEGER NOT NULL REFERENCES shop.orders(id),
    tracking_number     VARCHAR(100),
    carrier             VARCHAR(50) DEFAULT 'SF-Express',
    status              VARCHAR(30) DEFAULT 'picked_up',
    current_location    VARCHAR(255),
    estimated_delivery  TIMESTAMPTZ,
    timeline            JSONB DEFAULT '[]',
    created_at          TIMESTAMPTZ DEFAULT NOW(),
    updated_at          TIMESTAMPTZ DEFAULT NOW()
);

-- 2.9 shop.after_sale_requests
CREATE TABLE shop.after_sale_requests (
    id          SERIAL PRIMARY KEY,
    user_id     INTEGER NOT NULL REFERENCES shop.users(id),
    order_id    INTEGER NOT NULL REFERENCES shop.orders(id),
    type        VARCHAR(20) NOT NULL,
    reason      TEXT,
    status      VARCHAR(20) DEFAULT 'pending',
    created_at  TIMESTAMPTZ DEFAULT NOW(),
    updated_at  TIMESTAMPTZ DEFAULT NOW()
);

-- ============================================================================
-- 3. shop Schema Indexes
-- ============================================================================
CREATE INDEX idx_products_category ON shop.products(category_id);
CREATE INDEX idx_products_status ON shop.products(status);
CREATE INDEX idx_orders_user ON shop.orders(user_id);
CREATE INDEX idx_orders_status ON shop.orders(status);
CREATE INDEX idx_orders_pending_time ON shop.orders(created_at) WHERE status = 'pending';
CREATE INDEX idx_logistics_order ON shop.logistics_records(order_id);
CREATE INDEX idx_after_sale_user ON shop.after_sale_requests(user_id);
CREATE INDEX idx_after_sale_order ON shop.after_sale_requests(order_id);

-- ============================================================================
-- 4. customer_service Schema (3 tables)
-- ============================================================================
CREATE SCHEMA IF NOT EXISTS customer_service;

-- 4.1 customer_service.faq_embeddings
CREATE TABLE customer_service.faq_embeddings (
    id        SERIAL PRIMARY KEY,
    question  TEXT NOT NULL,
    answer    TEXT NOT NULL,
    embedding vector(1024),
    metadata  JSONB DEFAULT '{}'
);

-- 4.2 customer_service.conversations
CREATE TABLE customer_service.conversations (
    id          TEXT PRIMARY KEY,
    user_id     TEXT,
    title       TEXT,
    status      TEXT DEFAULT 'active',
    created_at  TIMESTAMPTZ DEFAULT NOW(),
    updated_at  TIMESTAMPTZ DEFAULT NOW()
);

-- 4.3 customer_service.messages
CREATE TABLE customer_service.messages (
    id               SERIAL PRIMARY KEY,
    conversation_id  TEXT NOT NULL REFERENCES customer_service.conversations(id),
    role             TEXT NOT NULL CHECK (role IN ('user', 'assistant', 'system')),
    content          TEXT NOT NULL,
    turn_number      INTEGER NOT NULL,
    metadata         JSONB,
    created_at       TIMESTAMPTZ DEFAULT NOW()
);

-- HNSW index for vector similarity search
CREATE INDEX idx_faq_embedding ON customer_service.faq_embeddings USING hnsw (embedding vector_cosine_ops);

-- Index for message retrieval by conversation
CREATE INDEX idx_messages_conv ON customer_service.messages(conversation_id, turn_number);

-- ============================================================================
-- 5. Seed Data
-- ============================================================================

-- 5.1 Admin Account (password: admin123)
INSERT INTO shop.users (email, password, nickname, role)
VALUES (
    'admin@shop.local',
    '$2b$12$r64TPhy01JNT0M69w7If3uDAxnQPxIu6UWFE99IgrqI/2X5UeW2xC',
    'Admin',
    'admin'
);

-- 5.2 Categories (4 parent + 5 child)
INSERT INTO shop.categories (id, name, parent_id, sort_order) VALUES
    (1, '智能门锁',       NULL, 1),
    (2, '智能摄像头',     NULL, 2),
    (3, '智能网关',       NULL, 3),
    (4, '智能家居配件',   NULL, 4),
    (5, '指纹锁',         1,    1),
    (6, '人脸识别锁',     1,    2),
    (7, '室内摄像头',     2,    1),
    (8, '室外摄像头',     2,    2),
    (9, '网关配件',       3,    1);

-- Advance sequence to avoid conflict with manual IDs
SELECT setval('shop.categories_id_seq', 9);

-- 5.3 Products (10 on_sale products)
INSERT INTO shop.products (name, description, price, image_url, stock, category_id, status) VALUES
    ('X1 智能指纹门锁',        '高端指纹识别门锁，支持APP远程开锁，0.3秒快速识别',             1299.00, '/images/products/x1.jpg',     50, 5, 'on_sale'),
    ('X2 3D人脸识别门锁',      '3D结构光人脸识别，防照片/视频攻击，全自动锁体',              2599.00, '/images/products/x2.jpg',     30, 6, 'on_sale'),
    ('C1 智能室内摄像头',      '1080P高清画质，双向语音通话，AI人形检测',                     299.00, '/images/products/c1.jpg',     100, 7, 'on_sale'),
    ('C2 智能室外摄像头',      'IP66防水防尘，全彩夜视，AI区域报警',                          499.00, '/images/products/c2.jpg',     60, 8, 'on_sale'),
    ('G1 智能家庭网关',        'Zigbee 3.0协议，最大连接128个设备，支持HomeKit',            599.00, '/images/products/g1.jpg',     40, 3, 'on_sale'),
    ('G2 智能中枢网关',        'Wi-Fi 6 + Zigbee + BLE Mesh三模，本地AI引擎',             1299.00, '/images/products/g2.jpg',     20, 3, 'on_sale'),
    ('A1 门窗传感器',          '即时感知门窗开关状态，低功耗设计，电池续航2年',                99.00, '/images/products/a1.jpg',     100, 4, 'on_sale'),
    ('A2 人体传感器',          '红外人体移动检测，110°广角探测，光照度感应',                 129.00, '/images/products/a2.jpg',     80, 4, 'on_sale'),
    ('A3 智能开关面板',        '双路控制，支持定时与联动场景，LED背光',                       199.00, '/images/products/a3.jpg',     60, 4, 'on_sale'),
    ('P1 网关电源适配器',      '12V/2A电源适配器，兼容G1/G2系列网关',                         59.00, '/images/products/p1.jpg',     100, 9, 'on_sale');

-- 5.4 Logistics / After-Sale Demo Data
-- NOTE: Demo data for logistics_records and after_sale_requests is created
-- at runtime by the application (via /c-endpoint or seed scripts), as they
-- depend on valid order_id/user_id references.
