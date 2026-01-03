-- 手动应用0008迁移的SQL脚本
-- 添加client字段
ALTER TABLE outgoing_document 
ADD COLUMN IF NOT EXISTS client_id BIGINT NULL;

-- 添加client_contact字段
ALTER TABLE outgoing_document 
ADD COLUMN IF NOT EXISTS client_contact_id BIGINT NULL;

-- 添加recipient_email字段
ALTER TABLE outgoing_document 
ADD COLUMN IF NOT EXISTS recipient_email VARCHAR(255) NULL;

-- 添加外键约束（如果表存在）
DO $$
BEGIN
    -- 添加client外键
    IF NOT EXISTS (
        SELECT 1 FROM pg_constraint 
        WHERE conname = 'outgoing_document_client_id_fkey'
    ) THEN
        ALTER TABLE outgoing_document 
        ADD CONSTRAINT outgoing_document_client_id_fkey 
        FOREIGN KEY (client_id) 
        REFERENCES customer_management_client(id) 
        ON DELETE SET NULL;
    END IF;

    -- 添加client_contact外键
    IF NOT EXISTS (
        SELECT 1 FROM pg_constraint 
        WHERE conname = 'outgoing_document_client_contact_id_fkey'
    ) THEN
        ALTER TABLE outgoing_document 
        ADD CONSTRAINT outgoing_document_client_contact_id_fkey 
        FOREIGN KEY (client_contact_id) 
        REFERENCES customer_management_clientcontact(id) 
        ON DELETE SET NULL;
    END IF;
END $$;

-- 更新字段注释
COMMENT ON COLUMN outgoing_document.client_id IS '关联的客户，用于自动填充办公地址';
COMMENT ON COLUMN outgoing_document.client_contact_id IS '从客户管理-人员有关系管理中获取，用于自动填充联系人、联系电话和联系邮箱';
COMMENT ON COLUMN outgoing_document.recipient_email IS '联系邮箱，可从客户联系人中自动填充';
COMMENT ON COLUMN outgoing_document.recipient_contact IS '签约主体代表姓名，可从客户联系人中自动填充';
COMMENT ON COLUMN outgoing_document.recipient_phone IS '联系电话，可从客户联系人中自动填充';
COMMENT ON COLUMN outgoing_document.recipient_address IS '办公地址，可从客户信息中自动填充';

-- 标记迁移为已应用（可选，如果需要）
-- INSERT INTO django_migrations (app, name, applied) 
-- VALUES ('delivery_customer', '0008_add_client_contact_to_outgoing_document', NOW())
-- ON CONFLICT DO NOTHING;

