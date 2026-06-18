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

-- 5.2 Categories (6 parent + 10 child)
INSERT INTO shop.categories (id, name, parent_id, sort_order) VALUES
    (1, '智能门锁',       NULL, 1),
    (2, '智能摄像头',     NULL, 2),
    (3, '智能网关',       NULL, 3),
    (4, '智能灯具',       NULL, 4),
    (5, '智能窗帘',       NULL, 5),
    (6, '传感器',         NULL, 6),
    (7, '指纹锁',         1,    1),
    (8, '人脸识别锁',     1,    2),
    (9, '室内摄像头',     2,    1),
    (10,'室外摄像头',    2,    2),
    (11,'网关配件',      3,    1),
    (12,'吸顶灯',        4,    1),
    (13,'氛围灯',        4,    2),
    (14,'电动窗帘',      5,    1),
    (15,'门磁传感器',    6,    1),
    (16,'人体传感器',    6,    2);

SELECT setval('shop.categories_id_seq', 16);

-- 5.3 Products (25 on_sale products)
INSERT INTO shop.products (name, description, price, image_url, stock, category_id, status) VALUES
    ('X1 智能指纹门锁',        '高端指纹识别门锁，支持APP远程开锁，0.3秒快速识别',             1299.00, '/products/x1-fingerprint-lock.png',     50, 7, 'on_sale'),
    ('X2 3D人脸识别门锁',      '3D结构光人脸识别，防照片/视频攻击，全自动锁体',              2599.00, '/products/x2-face-lock.png',     30, 8, 'on_sale'),
    ('X3 智能猫眼门锁',        '1080P猫眼摄像头+指纹锁二合一，门外画面实时查看',            1899.00, '/products/x3-cat-eye-lock.png',     25, 8, 'on_sale'),
    ('C1 智能室内摄像头',      '2K高清画质，双向语音通话，AI人形检测，360°旋转',              329.00, '/products/c1-indoor-camera.png',     80, 9, 'on_sale'),
    ('C2 智能室外摄像头',      'IP66防水防尘，全彩夜视，AI区域报警，4K超清',                    599.00, '',     40, 10, 'on_sale'),
    ('C3 迷你无线摄像头',      '磁吸安装，电池供电，PIR人体感应，1080P高清',                    199.00, '',     100, 9, 'on_sale'),
    ('G1 智能家庭网关',        'Zigbee 3.0协议，最大连接128个设备，支持HomeKit',              599.00, '/products/g1-home-gateway.png',     35, 3, 'on_sale'),
    ('G2 智能中枢网关',        'Wi-Fi 6 + Zigbee + BLE Mesh三模，本地AI引擎',               1299.00, '/products/g2-hub-gateway.png',     15, 3, 'on_sale'),
    ('D1 吸顶灯 客厅版',       '智能吸顶灯，无极调光调色，支持语音控制，适用20-30㎡',          499.00, '/products/d1-living-ceiling-light.png',     30, 12, 'on_sale'),
    ('D2 吸顶灯 卧室版',       '智能吸顶灯，无极调光调色，定时开关，适用10-15㎡',              299.00, '/products/d2-bedroom-ceiling-light.png',     40, 12, 'on_sale'),
    ('D3 智能灯带 2米',        'RGB全彩灯带，音乐律动模式，APP控制，背面自带背胶',             129.00, '/products/d3-smart-light-strip.png',     80, 13, 'on_sale'),
    ('D4 智能床头灯',          '无极调光，触控+语音双控，定时关灯，柔光护眼',                   199.00, '/products/d4-bedside-lamp.png',     50, 13, 'on_sale'),
    ('Z1 智能电动窗帘电机',    '静音电机，支持手拉启动，定时开合，语音控制',                    699.00, '/products/z1-curtain-motor.png',     20, 14, 'on_sale'),
    ('Z2 智能卷帘电机',        '适合卷帘/百叶窗，内置锂电池，免布线安装',                       499.00, '/products/z2-roller-motor.png',     25, 14, 'on_sale'),
    ('T1 门窗传感器',          '即时感知门窗开关，低功耗设计，纽扣电池续航2年',                  99.00, '/products/t1-door-window-sensor.png',     100, 15, 'on_sale'),
    ('T2 人体移动传感器',      '红外人体移动检测，110°广角，光照度感应，休眠唤醒',             129.00, '/products/t2-motion-sensor.png',     60, 16, 'on_sale'),
    ('T3 温湿度传感器',        '高精度温湿度监测，±0.2℃精度，联动空调/加湿器',                149.00, '/products/t3-temp-humidity-sensor.png',     40, 16, 'on_sale'),
    ('T4 水浸传感器',          '0.5mm浸水感应，IP67防尘防水，联动关阀，厨房卫生间必备',         79.00, '/products/t4-water-leak-sensor.png',     55, 15, 'on_sale'),
    ('T5 烟雾报警器',          '光电式烟雾探测，85分贝声光报警，APP远程提醒',                   169.00, '/products/t5-smoke-alarm.png',     35, 16, 'on_sale'),
    ('P1 网关电源适配器',      '12V/2A电源适配器，兼容G1/G2系列网关',                           59.00, '/products/p1-gateway-power-adapter.png',     100, 11, 'on_sale'),
    ('P2 Zigbee信号中继器',    '即插即用信号中继，扩展覆盖范围，适配所有Zigbee设备',           89.00, '',     45, 11, 'on_sale'),
    ('X1S 指纹锁青春版',       '入门级指纹锁，指纹+密码+钥匙三合一，续航12个月',              699.00, '',     60, 7, 'on_sale'),
    ('D5 智能灯泡 E27',        'E27通用螺口，1600万色可调，10W等效60W，语音控制',              69.00, '',     120, 13, 'on_sale'),
    ('Z3 窗帘伴侣',            '适配现有窗帘轨道，即挂即用，Type-C充电，续航6个月',             349.00, '',     30, 14, 'on_sale'),
    ('G3 迷你网关',            'USB供电迷你网关，即插即用，适合小型公寓/单间',                  199.00, '',     45, 3, 'on_sale');

SELECT setval('shop.products_id_seq', 25);

-- 5.4 Logistics / After-Sale Demo Data
-- NOTE: Demo data for logistics_records and after_sale_requests is created
-- at runtime by the application (via /c-endpoint or seed scripts), as they
-- depend on valid order_id/user_id references.
