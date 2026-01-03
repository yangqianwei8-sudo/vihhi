-- 人员信息变更申请表迁移SQL
-- 迁移编号：0046_add_contact_info_change

-- 创建人员信息变更申请表
CREATE TABLE IF NOT EXISTS customer_contact_info_change (
    id BIGSERIAL PRIMARY KEY,
    change_type VARCHAR(30) NOT NULL,
    change_reason TEXT NOT NULL,
    change_content JSONB DEFAULT '{}'::jsonb NOT NULL,
    approval_status VARCHAR(20) DEFAULT 'draft' NOT NULL,
    created_time TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP NOT NULL,
    approved_time TIMESTAMP WITH TIME ZONE NULL,
    updated_time TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP NOT NULL,
    approval_instance_id BIGINT NULL,
    contact_id BIGINT NOT NULL,
    created_by_id BIGINT NOT NULL,
    CONSTRAINT customer_contact_info_change_contact_id_fk 
        FOREIGN KEY (contact_id) 
        REFERENCES customer_contact(id) 
        ON DELETE CASCADE,
    CONSTRAINT customer_contact_info_change_created_by_id_fk 
        FOREIGN KEY (created_by_id) 
        REFERENCES system_user(id) 
        ON DELETE RESTRICT,
    CONSTRAINT customer_contact_info_change_approval_instance_id_fk 
        FOREIGN KEY (approval_instance_id) 
        REFERENCES workflow_approval_instance(id) 
        ON DELETE SET NULL,
    CONSTRAINT customer_contact_info_change_change_type_check 
        CHECK (change_type IN ('basic_info', 'contact_info', 'career_info', 'education_info', 'relationship_info', 'other')),
    CONSTRAINT customer_contact_info_change_approval_status_check 
        CHECK (approval_status IN ('draft', 'pending', 'approved', 'rejected', 'withdrawn'))
);

-- 创建索引
CREATE INDEX IF NOT EXISTS customer_co_contact_6a8f5a_idx 
    ON customer_contact_info_change(contact_id, approval_status);
CREATE INDEX IF NOT EXISTS customer_co_change__a1b2c3_idx 
    ON customer_contact_info_change(change_type);
CREATE INDEX IF NOT EXISTS customer_co_created_4d5e6f_idx 
    ON customer_contact_info_change(created_time);

-- 添加表注释
COMMENT ON TABLE customer_contact_info_change IS '人员信息变更申请表';
COMMENT ON COLUMN customer_contact_info_change.change_type IS '变更类型';
COMMENT ON COLUMN customer_contact_info_change.change_reason IS '变更原因';
COMMENT ON COLUMN customer_contact_info_change.change_content IS '变更内容（JSON格式存储变更前后的值）';
COMMENT ON COLUMN customer_contact_info_change.approval_status IS '审批状态';
COMMENT ON COLUMN customer_contact_info_change.approval_instance_id IS '审批实例ID';
COMMENT ON COLUMN customer_contact_info_change.contact_id IS '关联联系人ID';
COMMENT ON COLUMN customer_contact_info_change.created_by_id IS '创建人ID';

