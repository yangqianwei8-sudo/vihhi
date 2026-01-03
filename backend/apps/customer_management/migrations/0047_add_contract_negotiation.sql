-- 合同洽谈记录表迁移SQL
-- 迁移编号：0047_add_contract_negotiation

-- 创建合同洽谈记录表
CREATE TABLE IF NOT EXISTS business_contract_negotiation (
    id BIGSERIAL PRIMARY KEY,
    negotiation_number VARCHAR(100) NULL UNIQUE,
    negotiation_type VARCHAR(20) DEFAULT 'other' NOT NULL,
    status VARCHAR(20) DEFAULT 'ongoing' NOT NULL,
    title VARCHAR(200) NOT NULL,
    content TEXT NOT NULL,
    client_participants TEXT DEFAULT '' NOT NULL,
    negotiation_date DATE DEFAULT CURRENT_DATE NOT NULL,
    negotiation_start_time TIME NULL,
    negotiation_end_time TIME NULL,
    next_negotiation_date DATE NULL,
    result_summary TEXT DEFAULT '' NOT NULL,
    agreed_items TEXT DEFAULT '' NOT NULL,
    pending_items TEXT DEFAULT '' NOT NULL,
    attachments TEXT DEFAULT '' NOT NULL,
    notes TEXT DEFAULT '' NOT NULL,
    created_time TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP NOT NULL,
    updated_time TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP NOT NULL,
    client_id BIGINT NULL,
    contract_id BIGINT NULL,
    created_by_id BIGINT NOT NULL,
    project_id BIGINT NULL,
    CONSTRAINT business_contract_negotiation_client_id_fk 
        FOREIGN KEY (client_id) 
        REFERENCES customer_client(id) 
        ON DELETE RESTRICT,
    CONSTRAINT business_contract_negotiation_contract_id_fk 
        FOREIGN KEY (contract_id) 
        REFERENCES business_contract(id) 
        ON DELETE CASCADE,
    CONSTRAINT business_contract_negotiation_created_by_id_fk 
        FOREIGN KEY (created_by_id) 
        REFERENCES system_user(id) 
        ON DELETE RESTRICT,
    CONSTRAINT business_contract_negotiation_project_id_fk 
        FOREIGN KEY (project_id) 
        REFERENCES production_management_project(id) 
        ON DELETE SET NULL,
    CONSTRAINT business_contract_negotiation_negotiation_type_check 
        CHECK (negotiation_type IN ('price', 'terms', 'schedule', 'payment', 'other')),
    CONSTRAINT business_contract_negotiation_status_check 
        CHECK (status IN ('ongoing', 'completed', 'suspended', 'cancelled'))
);

-- 创建参与人员多对多关系表
CREATE TABLE IF NOT EXISTS business_contract_negotiation_participants (
    id BIGSERIAL PRIMARY KEY,
    contractnegotiation_id BIGINT NOT NULL,
    user_id BIGINT NOT NULL,
    CONSTRAINT business_contract_negotiation_participants_contractnegotiation_id_fk 
        FOREIGN KEY (contractnegotiation_id) 
        REFERENCES business_contract_negotiation(id) 
        ON DELETE CASCADE,
    CONSTRAINT business_contract_negotiation_participants_user_id_fk 
        FOREIGN KEY (user_id) 
        REFERENCES system_user(id) 
        ON DELETE CASCADE,
    CONSTRAINT business_contract_negotiation_participants_contractnegotiation_id_user_id_uniq 
        UNIQUE (contractnegotiation_id, user_id)
);

-- 创建索引
CREATE INDEX IF NOT EXISTS business_co_contrac_idx 
    ON business_contract_negotiation(contract_id);
CREATE INDEX IF NOT EXISTS business_co_client_idx 
    ON business_contract_negotiation(client_id);
CREATE INDEX IF NOT EXISTS business_co_negotia_idx 
    ON business_contract_negotiation(negotiation_date);
CREATE INDEX IF NOT EXISTS business_co_status_idx 
    ON business_contract_negotiation(status);
CREATE INDEX IF NOT EXISTS business_contract_negotiation_participants_contractnegotiation_id_idx 
    ON business_contract_negotiation_participants(contractnegotiation_id);
CREATE INDEX IF NOT EXISTS business_contract_negotiation_participants_user_id_idx 
    ON business_contract_negotiation_participants(user_id);

-- 添加表注释
COMMENT ON TABLE business_contract_negotiation IS '合同洽谈记录';
COMMENT ON COLUMN business_contract_negotiation.negotiation_number IS '洽谈编号（自动生成：NT-YYYY-NNNN）';
COMMENT ON COLUMN business_contract_negotiation.negotiation_type IS '洽谈类型';
COMMENT ON COLUMN business_contract_negotiation.status IS '洽谈状态';
COMMENT ON COLUMN business_contract_negotiation.title IS '洽谈主题';
COMMENT ON COLUMN business_contract_negotiation.content IS '洽谈内容';
COMMENT ON COLUMN business_contract_negotiation.client_participants IS '客户参与人员';
COMMENT ON COLUMN business_contract_negotiation.negotiation_date IS '洽谈日期';
COMMENT ON COLUMN business_contract_negotiation.next_negotiation_date IS '下次洽谈日期';
COMMENT ON COLUMN business_contract_negotiation.result_summary IS '洽谈结果摘要';
COMMENT ON COLUMN business_contract_negotiation.agreed_items IS '已达成事项';
COMMENT ON COLUMN business_contract_negotiation.pending_items IS '待解决事项';


