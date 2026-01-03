-- 服务费结算方案模块迁移SQL
-- 如果遇到迁移历史不一致问题，可以手动执行此SQL脚本

-- 迁移 0007: 创建服务费结算方案相关表
-- 注意：请根据实际数据库类型调整SQL语法（PostgreSQL/MySQL等）

-- 创建主表：settlement_service_fee_scheme
CREATE TABLE IF NOT EXISTS settlement_service_fee_scheme (
    id BIGSERIAL PRIMARY KEY,
    name VARCHAR(200) NOT NULL,
    code VARCHAR(50) UNIQUE,
    description TEXT,
    contract_id BIGINT REFERENCES business_contract(id) ON DELETE CASCADE,
    project_id BIGINT REFERENCES production_management_project(id) ON DELETE SET NULL,
    settlement_method VARCHAR(30) NOT NULL,
    fixed_total_price NUMERIC(14, 2),
    fixed_unit_price NUMERIC(12, 2),
    area_type VARCHAR(30),
    cumulative_rate NUMERIC(5, 2),
    combined_fixed_method VARCHAR(20),
    combined_fixed_total NUMERIC(14, 2),
    combined_fixed_unit NUMERIC(12, 2),
    combined_fixed_area_type VARCHAR(30),
    combined_actual_method VARCHAR(30),
    combined_cumulative_rate NUMERIC(5, 2),
    combined_deduct_fixed BOOLEAN DEFAULT FALSE,
    has_cap_fee BOOLEAN DEFAULT FALSE,
    cap_type VARCHAR(20),
    total_cap_amount NUMERIC(14, 2),
    has_minimum_fee BOOLEAN DEFAULT FALSE,
    minimum_fee_amount NUMERIC(14, 2),
    is_active BOOLEAN DEFAULT TRUE,
    is_default BOOLEAN DEFAULT FALSE,
    sort_order INTEGER DEFAULT 0,
    created_by_id BIGINT NOT NULL REFERENCES system_user(id) ON DELETE RESTRICT,
    created_time TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    updated_time TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

-- 创建索引
CREATE INDEX IF NOT EXISTS settlement__contract_idx ON settlement_service_fee_scheme(contract_id, is_active);
CREATE INDEX IF NOT EXISTS settlement__project_idx ON settlement_service_fee_scheme(project_id, is_active);
CREATE INDEX IF NOT EXISTS settlement__method_idx ON settlement_service_fee_scheme(settlement_method, is_active);
CREATE INDEX IF NOT EXISTS settlement__default_idx ON settlement_service_fee_scheme(is_default, is_active);
CREATE INDEX IF NOT EXISTS settlement_service_fee_scheme_created_time_idx ON settlement_service_fee_scheme(created_time);

-- 创建分段递增提成配置表
CREATE TABLE IF NOT EXISTS settlement_service_fee_segmented_rate (
    id BIGSERIAL PRIMARY KEY,
    scheme_id BIGINT NOT NULL REFERENCES settlement_service_fee_scheme(id) ON DELETE CASCADE,
    threshold NUMERIC(14, 2) NOT NULL,
    rate NUMERIC(5, 2) NOT NULL,
    description TEXT,
    "order" INTEGER DEFAULT 0,
    is_active BOOLEAN DEFAULT TRUE,
    created_time TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    updated_time TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX IF NOT EXISTS settlement__scheme_idx ON settlement_service_fee_segmented_rate(scheme_id, is_active, "order");

-- 创建跳点提成配置表
CREATE TABLE IF NOT EXISTS settlement_service_fee_jump_point_rate (
    id BIGSERIAL PRIMARY KEY,
    scheme_id BIGINT NOT NULL REFERENCES settlement_service_fee_scheme(id) ON DELETE CASCADE,
    threshold NUMERIC(14, 2) NOT NULL,
    rate NUMERIC(5, 2) NOT NULL,
    description TEXT,
    "order" INTEGER DEFAULT 0,
    is_active BOOLEAN DEFAULT TRUE,
    created_time TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    updated_time TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX IF NOT EXISTS settlement__scheme_jump_idx ON settlement_service_fee_jump_point_rate(scheme_id, is_active, "order");

-- 创建单价封顶费明细表
CREATE TABLE IF NOT EXISTS settlement_service_fee_unit_cap_detail (
    id BIGSERIAL PRIMARY KEY,
    scheme_id BIGINT NOT NULL REFERENCES settlement_service_fee_scheme(id) ON DELETE CASCADE,
    unit_name VARCHAR(200) NOT NULL,
    cap_unit_price NUMERIC(12, 2) NOT NULL,
    description TEXT,
    "order" INTEGER DEFAULT 0,
    created_time TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    updated_time TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX IF NOT EXISTS settlement__scheme_unit_idx ON settlement_service_fee_unit_cap_detail(scheme_id, "order");

-- 迁移 0008: 添加service_fee_scheme字段到ProjectSettlement表
ALTER TABLE settlement_project_settlement 
ADD COLUMN IF NOT EXISTS service_fee_scheme_id BIGINT REFERENCES settlement_service_fee_scheme(id) ON DELETE SET NULL;

CREATE INDEX IF NOT EXISTS settlement_project_settlement_service_fee_scheme_id_idx 
ON settlement_project_settlement(service_fee_scheme_id);

-- 记录迁移历史（如果使用Django迁移系统）
-- INSERT INTO django_migrations (app, name, applied) 
-- VALUES ('settlement_center', '0007_add_service_fee_settlement_scheme', NOW())
-- ON CONFLICT DO NOTHING;

-- INSERT INTO django_migrations (app, name, applied) 
-- VALUES ('settlement_center', '0008_add_service_fee_scheme_to_project_settlement', NOW())
-- ON CONFLICT DO NOTHING;

