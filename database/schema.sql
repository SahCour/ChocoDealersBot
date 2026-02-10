-- ============================================
-- CHOCODEALERS WAREHOUSE MANAGEMENT SYSTEM
-- PostgreSQL Database Schema
-- Version: 1.0
-- Date: 2026-02-10
-- ============================================

-- Enable UUID extension
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";

-- ============================================
-- 1. USERS & PERMISSIONS
-- ============================================

CREATE TYPE user_role AS ENUM ('ADMIN', 'MANAGER', 'STAFF');
CREATE TYPE user_status AS ENUM ('ACTIVE', 'INACTIVE', 'SUSPENDED');

CREATE TABLE users (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    telegram_id BIGINT UNIQUE NOT NULL,
    username VARCHAR(255),
    first_name VARCHAR(255),
    last_name VARCHAR(255),
    role user_role NOT NULL DEFAULT 'STAFF',
    status user_status NOT NULL DEFAULT 'ACTIVE',
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    last_login TIMESTAMP WITH TIME ZONE
);

-- Role permissions matrix (stored as JSONB for flexibility)
CREATE TABLE role_permissions (
    role user_role PRIMARY KEY,
    permissions JSONB NOT NULL,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

-- Insert default permissions
INSERT INTO role_permissions (role, permissions) VALUES
('ADMIN', '{"can_view_inventory": true, "can_add_sale": true, "can_add_production": true, "can_add_purchase": true, "can_view_reports": true, "can_manage_users": true, "can_sync_square": true, "can_sync_sheets": true}'),
('MANAGER', '{"can_view_inventory": true, "can_add_sale": true, "can_add_production": true, "can_add_purchase": true, "can_view_reports": true, "can_manage_users": false, "can_sync_square": true, "can_sync_sheets": true}'),
('STAFF', '{"can_view_inventory": true, "can_add_sale": true, "can_add_production": false, "can_add_purchase": false, "can_view_reports": false, "can_manage_users": false, "can_sync_square": false, "can_sync_sheets": false}');

-- ============================================
-- 2. PRODUCTS (SKU)
-- ============================================

CREATE TYPE product_category AS ENUM (
    'ICE_CREAM', 'TRUFFLE', 'BAR_SMALL', 'BAR_LARGE',
    'BEAN_TO_BAR', 'SYMPHONY', 'DESSERT', 'HALVA',
    'BONBON', 'OTHER', 'SET'
);

CREATE TABLE products (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    sku VARCHAR(50) UNIQUE NOT NULL,
    name VARCHAR(255) NOT NULL,
    category product_category NOT NULL,
    weight_g DECIMAL(8,2),
    cocoa_percent VARCHAR(20),
    retail_price_thb DECIMAL(10,2) NOT NULL,
    cogs_thb DECIMAL(10,2) NOT NULL,
    gross_margin_thb DECIMAL(10,2) GENERATED ALWAYS AS (retail_price_thb - cogs_thb) STORED,
    gross_margin_percent DECIMAL(5,2) GENERATED ALWAYS AS (((retail_price_thb - cogs_thb) / retail_price_thb) * 100) STORED,
    square_item_id VARCHAR(255), -- Square POS Item ID
    is_active BOOLEAN DEFAULT true,
    notes TEXT,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

-- ============================================
-- 3. INGREDIENTS
-- ============================================

CREATE TYPE ingredient_category AS ENUM (
    'CACAO_BASE', 'NUTS_SEEDS', 'DAIRY_ALT',
    'COFFEE', 'TEA', 'PACKAGING', 'SPICES', 'OTHER'
);

CREATE TYPE ingredient_unit AS ENUM ('kg', 'L', 'pc', 'btl');

CREATE TABLE ingredients (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    code VARCHAR(50) UNIQUE NOT NULL, -- e.g., ING-001
    name VARCHAR(255) NOT NULL,
    category ingredient_category NOT NULL,
    price_per_unit_thb DECIMAL(10,2) NOT NULL,
    unit ingredient_unit NOT NULL,
    supplier VARCHAR(255),
    notes TEXT,
    is_active BOOLEAN DEFAULT true,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

-- ============================================
-- 4. INVENTORY - PRODUCTS
-- ============================================

CREATE TABLE inventory_products (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    product_id UUID REFERENCES products(id) ON DELETE CASCADE,
    quantity INTEGER NOT NULL DEFAULT 0,
    min_stock_level INTEGER DEFAULT 10,
    max_stock_level INTEGER DEFAULT 100,
    location VARCHAR(255) DEFAULT 'Main Warehouse',
    last_count_at TIMESTAMP WITH TIME ZONE,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    CONSTRAINT positive_quantity CHECK (quantity >= 0)
);

-- ============================================
-- 5. INVENTORY - INGREDIENTS
-- ============================================

CREATE TABLE inventory_ingredients (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    ingredient_id UUID REFERENCES ingredients(id) ON DELETE CASCADE,
    quantity_kg DECIMAL(12,3) NOT NULL DEFAULT 0, -- Unified to kg for simplicity
    min_stock_level_kg DECIMAL(12,3) DEFAULT 1,
    max_stock_level_kg DECIMAL(12,3) DEFAULT 50,
    location VARCHAR(255) DEFAULT 'Main Warehouse',
    expiry_date DATE,
    last_count_at TIMESTAMP WITH TIME ZONE,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    CONSTRAINT positive_quantity_ing CHECK (quantity_kg >= 0)
);

-- ============================================
-- 6. SALES TRANSACTIONS
-- ============================================

CREATE TYPE sale_source AS ENUM ('TELEGRAM_BOT', 'SQUARE_POS', 'MANUAL');
CREATE TYPE payment_method AS ENUM ('CASH', 'CARD', 'BANK_TRANSFER', 'CRYPTO', 'OTHER');

CREATE TABLE sales (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    product_id UUID REFERENCES products(id) ON DELETE RESTRICT,
    quantity INTEGER NOT NULL,
    unit_price_thb DECIMAL(10,2) NOT NULL,
    total_price_thb DECIMAL(10,2) GENERATED ALWAYS AS (quantity * unit_price_thb) STORED,
    discount_thb DECIMAL(10,2) DEFAULT 0,
    final_price_thb DECIMAL(10,2),
    source sale_source NOT NULL DEFAULT 'TELEGRAM_BOT',
    payment_method payment_method,
    square_transaction_id VARCHAR(255), -- Square Payment ID
    created_by UUID REFERENCES users(id),
    customer_name VARCHAR(255),
    customer_telegram_id BIGINT,
    notes TEXT,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    CONSTRAINT positive_quantity_sale CHECK (quantity > 0)
);

-- ============================================
-- 7. PRODUCTION BATCHES
-- ============================================

CREATE TYPE production_status AS ENUM ('PLANNED', 'IN_PROGRESS', 'COMPLETED', 'CANCELLED');

CREATE TABLE production (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    product_id UUID REFERENCES products(id) ON DELETE RESTRICT,
    batch_number VARCHAR(100) UNIQUE,
    quantity_produced INTEGER NOT NULL,
    production_date DATE NOT NULL DEFAULT CURRENT_DATE,
    status production_status NOT NULL DEFAULT 'PLANNED',
    cost_materials_thb DECIMAL(10,2),
    cost_labor_thb DECIMAL(10,2),
    total_cost_thb DECIMAL(10,2),
    created_by UUID REFERENCES users(id),
    notes TEXT,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    completed_at TIMESTAMP WITH TIME ZONE,
    CONSTRAINT positive_quantity_prod CHECK (quantity_produced > 0)
);

-- Production ingredients usage (deduction tracking)
CREATE TABLE production_ingredients_used (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    production_id UUID REFERENCES production(id) ON DELETE CASCADE,
    ingredient_id UUID REFERENCES ingredients(id) ON DELETE RESTRICT,
    quantity_used_kg DECIMAL(12,3) NOT NULL,
    cost_thb DECIMAL(10,2),
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

-- ============================================
-- 8. PURCHASES (INGREDIENT PROCUREMENT)
-- ============================================

CREATE TYPE purchase_status AS ENUM ('ORDERED', 'RECEIVED', 'CANCELLED');

CREATE TABLE purchases (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    ingredient_id UUID REFERENCES ingredients(id) ON DELETE RESTRICT,
    quantity_kg DECIMAL(12,3) NOT NULL,
    unit_price_thb DECIMAL(10,2) NOT NULL,
    total_price_thb DECIMAL(10,2) GENERATED ALWAYS AS (quantity_kg * unit_price_thb) STORED,
    supplier VARCHAR(255),
    purchase_date DATE NOT NULL DEFAULT CURRENT_DATE,
    expected_delivery_date DATE,
    status purchase_status NOT NULL DEFAULT 'ORDERED',
    invoice_number VARCHAR(100),
    created_by UUID REFERENCES users(id),
    notes TEXT,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    received_at TIMESTAMP WITH TIME ZONE,
    CONSTRAINT positive_quantity_purch CHECK (quantity_kg > 0)
);

-- ============================================
-- 9. SQUARE SYNC LOG
-- ============================================

CREATE TYPE sync_type AS ENUM ('INVENTORY', 'SALES', 'PRODUCTS', 'FULL');
CREATE TYPE sync_status AS ENUM ('SUCCESS', 'FAILED', 'IN_PROGRESS');

CREATE TABLE square_sync_log (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    sync_type sync_type NOT NULL,
    sync_status sync_status NOT NULL,
    started_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    completed_at TIMESTAMP WITH TIME ZONE,
    records_synced INTEGER,
    error_message TEXT,
    triggered_by UUID REFERENCES users(id)
);

-- ============================================
-- 10. GOOGLE SHEETS SYNC LOG
-- ============================================

CREATE TABLE sheets_sync_log (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    sheet_name VARCHAR(255) NOT NULL,
    sync_direction VARCHAR(20), -- 'TO_SHEETS', 'FROM_SHEETS', 'BIDIRECTIONAL'
    sync_status sync_status NOT NULL,
    started_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    completed_at TIMESTAMP WITH TIME ZONE,
    records_synced INTEGER,
    error_message TEXT,
    triggered_by UUID REFERENCES users(id)
);

-- ============================================
-- 11. AUDIT LOG (All changes tracking)
-- ============================================

CREATE TYPE action_type AS ENUM (
    'CREATE', 'UPDATE', 'DELETE',
    'SALE', 'PRODUCTION', 'PURCHASE',
    'INVENTORY_ADJUST', 'SYNC'
);

CREATE TABLE audit_log (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    user_id UUID REFERENCES users(id),
    action action_type NOT NULL,
    table_name VARCHAR(100) NOT NULL,
    record_id UUID,
    old_data JSONB,
    new_data JSONB,
    ip_address INET,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

-- ============================================
-- INDEXES for Performance
-- ============================================

CREATE INDEX idx_users_telegram_id ON users(telegram_id);
CREATE INDEX idx_users_role ON users(role);
CREATE INDEX idx_products_sku ON products(sku);
CREATE INDEX idx_products_category ON products(category);
CREATE INDEX idx_ingredients_code ON ingredients(code);
CREATE INDEX idx_sales_created_at ON sales(created_at);
CREATE INDEX idx_sales_product_id ON sales(product_id);
CREATE INDEX idx_production_status ON production(status);
CREATE INDEX idx_purchases_status ON purchases(status);
CREATE INDEX idx_audit_log_user_id ON audit_log(user_id);
CREATE INDEX idx_audit_log_created_at ON audit_log(created_at);

-- ============================================
-- TRIGGERS for Updated_at
-- ============================================

CREATE OR REPLACE FUNCTION update_updated_at_column()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = CURRENT_TIMESTAMP;
    RETURN NEW;
END;
$$ language 'plpgsql';

CREATE TRIGGER update_users_updated_at BEFORE UPDATE ON users
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

CREATE TRIGGER update_products_updated_at BEFORE UPDATE ON products
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

CREATE TRIGGER update_ingredients_updated_at BEFORE UPDATE ON ingredients
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

CREATE TRIGGER update_inventory_products_updated_at BEFORE UPDATE ON inventory_products
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

CREATE TRIGGER update_inventory_ingredients_updated_at BEFORE UPDATE ON inventory_ingredients
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

-- ============================================
-- VIEWS for Common Queries
-- ============================================

-- Low stock alerts
CREATE VIEW low_stock_products AS
SELECT
    p.sku,
    p.name,
    ip.quantity,
    ip.min_stock_level,
    (ip.min_stock_level - ip.quantity) AS shortage
FROM inventory_products ip
JOIN products p ON ip.product_id = p.id
WHERE ip.quantity < ip.min_stock_level
ORDER BY shortage DESC;

CREATE VIEW low_stock_ingredients AS
SELECT
    i.code,
    i.name,
    ii.quantity_kg,
    ii.min_stock_level_kg,
    (ii.min_stock_level_kg - ii.quantity_kg) AS shortage_kg
FROM inventory_ingredients ii
JOIN ingredients i ON ii.ingredient_id = i.id
WHERE ii.quantity_kg < ii.min_stock_level_kg
ORDER BY shortage_kg DESC;

-- Sales summary by product
CREATE VIEW sales_summary AS
SELECT
    p.sku,
    p.name,
    COUNT(s.id) AS total_sales,
    SUM(s.quantity) AS total_quantity_sold,
    SUM(s.total_price_thb) AS total_revenue_thb,
    AVG(s.unit_price_thb) AS avg_price_thb,
    MAX(s.created_at) AS last_sale_date
FROM sales s
JOIN products p ON s.product_id = p.id
GROUP BY p.id, p.sku, p.name
ORDER BY total_revenue_thb DESC;

-- Production efficiency
CREATE VIEW production_summary AS
SELECT
    p.sku,
    p.name,
    COUNT(pr.id) AS total_batches,
    SUM(pr.quantity_produced) AS total_produced,
    AVG(pr.total_cost_thb / pr.quantity_produced) AS avg_cost_per_unit,
    MAX(pr.production_date) AS last_production_date
FROM production pr
JOIN products p ON pr.product_id = p.id
WHERE pr.status = 'COMPLETED'
GROUP BY p.id, p.sku, p.name
ORDER BY total_produced DESC;

-- ============================================
-- INITIAL DATA SEEDING (Optional)
-- ============================================

-- Default admin user (update telegram_id with your actual ID)
-- INSERT INTO users (telegram_id, username, first_name, role)
-- VALUES (123456789, 'admin', 'Admin', 'ADMIN');

COMMENT ON DATABASE chocodealers IS 'Warehouse Management System for Chocodealers Chocolate Shop';
