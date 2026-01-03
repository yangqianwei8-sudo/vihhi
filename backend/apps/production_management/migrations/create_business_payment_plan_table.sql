-- 创建 business_payment_plan 表的SQL脚本
-- 如果表不存在，执行此脚本创建表

CREATE TABLE IF NOT EXISTS business_payment_plan (
    id BIGSERIAL PRIMARY KEY,
    phase_name VARCHAR(100) NOT NULL,
    phase_description TEXT,
    planned_amount NUMERIC(12, 2) NOT NULL,
    planned_date DATE NOT NULL,
    actual_amount NUMERIC(12, 2),
    actual_date DATE,
    status VARCHAR(20) NOT NULL DEFAULT 'pending',
    trigger_condition VARCHAR(100),
    condition_detail VARCHAR(200),
    notes TEXT,
    created_time TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_time TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT CURRENT_TIMESTAMP,
    contract_id BIGINT NOT NULL,
    CONSTRAINT business_payment_plan_contract_id_fkey 
        FOREIGN KEY (contract_id) 
        REFERENCES production_management_businesscontract(id) 
        ON DELETE CASCADE
);

-- 创建索引
CREATE INDEX IF NOT EXISTS business_payment_plan_contract_id_idx 
    ON business_payment_plan(contract_id);
CREATE INDEX IF NOT EXISTS business_payment_plan_status_idx 
    ON business_payment_plan(status);
CREATE INDEX IF NOT EXISTS business_payment_plan_planned_date_idx 
    ON business_payment_plan(planned_date);

-- 添加注释
COMMENT ON TABLE business_payment_plan IS '商务回款计划';
COMMENT ON COLUMN business_payment_plan.phase_name IS '回款阶段';
COMMENT ON COLUMN business_payment_plan.planned_amount IS '计划金额';
COMMENT ON COLUMN business_payment_plan.planned_date IS '计划日期';
COMMENT ON COLUMN business_payment_plan.actual_amount IS '实际金额';
COMMENT ON COLUMN business_payment_plan.actual_date IS '实际日期';
COMMENT ON COLUMN business_payment_plan.status IS '状态：pending-待回款, partial-部分回款, completed-已完成, overdue-已逾期, cancelled-已取消';

