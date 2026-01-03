-- SQL migration for BusinessExpenseApplication
-- 由于迁移依赖链问题，直接执行SQL创建表

-- 创建业务费申请表
CREATE TABLE IF NOT EXISTS customer_business_expense_application (
    id BIGSERIAL PRIMARY KEY,
    application_number VARCHAR(100) UNIQUE NOT NULL,
    client_id BIGINT NOT NULL REFERENCES customer_client(id) ON DELETE CASCADE,
    expense_type VARCHAR(30) NOT NULL,
    amount NUMERIC(12, 2) NOT NULL CHECK (amount >= 0.01),
    expense_date DATE NOT NULL,
    description TEXT NOT NULL,
    attachment VARCHAR(100),
    approval_status VARCHAR(20) NOT NULL DEFAULT 'draft',
    approval_instance_id BIGINT REFERENCES workflow_approval_instance(id) ON DELETE SET NULL,
    created_by_id BIGINT NOT NULL REFERENCES system_user(id) ON DELETE RESTRICT,
    created_time TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT NOW(),
    approved_time TIMESTAMP WITH TIME ZONE,
    updated_time TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT NOW()
);

-- 创建关联联系人中间表
CREATE TABLE IF NOT EXISTS customer_business_expense_application_related_contacts (
    id BIGSERIAL PRIMARY KEY,
    businessexpenseapplication_id BIGINT NOT NULL REFERENCES customer_business_expense_application(id) ON DELETE CASCADE,
    clientcontact_id BIGINT NOT NULL REFERENCES customer_contact(id) ON DELETE CASCADE,
    UNIQUE(businessexpenseapplication_id, clientcontact_id)
);

-- 创建索引
CREATE INDEX IF NOT EXISTS customer_bu_client__idx ON customer_business_expense_application(client_id, approval_status);
CREATE INDEX IF NOT EXISTS customer_bu_expense__idx ON customer_business_expense_application(expense_date);
CREATE INDEX IF NOT EXISTS customer_bu_applica_idx ON customer_business_expense_application(application_number);
CREATE INDEX IF NOT EXISTS customer_bu_approval_idx ON customer_business_expense_application(approval_instance_id);
CREATE INDEX IF NOT EXISTS customer_bu_created_by_idx ON customer_business_expense_application(created_by_id);
CREATE INDEX IF NOT EXISTS customer_bu_related_contacts_idx ON customer_business_expense_application_related_contacts(businessexpenseapplication_id);
CREATE INDEX IF NOT EXISTS customer_bu_contact_idx ON customer_business_expense_application_related_contacts(clientcontact_id);

-- 添加注释
COMMENT ON TABLE customer_business_expense_application IS '业务费申请';
COMMENT ON COLUMN customer_business_expense_application.application_number IS '申请单号（自动生成）';
COMMENT ON COLUMN customer_business_expense_application.client_id IS '关联客户';
COMMENT ON COLUMN customer_business_expense_application.expense_type IS '费用类型';
COMMENT ON COLUMN customer_business_expense_application.amount IS '费用金额';
COMMENT ON COLUMN customer_business_expense_application.expense_date IS '费用发生日期';
COMMENT ON COLUMN customer_business_expense_application.description IS '费用说明';
COMMENT ON COLUMN customer_business_expense_application.attachment IS '附件';
COMMENT ON COLUMN customer_business_expense_application.approval_status IS '审批状态';
COMMENT ON COLUMN customer_business_expense_application.approval_instance_id IS '审批实例';

