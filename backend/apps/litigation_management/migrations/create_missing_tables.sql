-- 创建诉讼管理模块缺失的表
-- 使用方法：psql -h dbconn.sealosbja.site -p 38013 -U postgres -d postgres -f create_missing_tables.sql

-- 创建 litigation_process 表（先不创建外键）
CREATE TABLE IF NOT EXISTS litigation_process (
    id BIGSERIAL PRIMARY KEY,
    case_id BIGINT NOT NULL,
    process_type VARCHAR(20) NOT NULL,
    process_date DATE,
    status VARCHAR(20) NOT NULL DEFAULT 'pending',
    court_name VARCHAR(200),
    court_address TEXT,
    judge_name VARCHAR(100),
    judge_contact VARCHAR(100),
    trial_location VARCHAR(200),
    trial_result TEXT,
    judgment_number VARCHAR(100),
    judgment_content TEXT,
    judgment_amount NUMERIC(15, 2),
    execution_amount NUMERIC(15, 2),
    execution_status VARCHAR(20),
    execution_result TEXT,
    description TEXT,
    created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    created_by_id BIGINT
);

-- 创建 litigation_document 表（先不创建外键）
CREATE TABLE IF NOT EXISTS litigation_document (
    id BIGSERIAL PRIMARY KEY,
    case_id BIGINT NOT NULL,
    process_id BIGINT,
    document_name VARCHAR(200) NOT NULL,
    document_type VARCHAR(30) NOT NULL,
    document_category VARCHAR(50),
    document_file VARCHAR(100),
    file_size BIGINT,
    description TEXT,
    created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    uploaded_by_id BIGINT
);

-- 创建 litigation_person 表（先不创建外键）
CREATE TABLE IF NOT EXISTS litigation_person (
    id BIGSERIAL PRIMARY KEY,
    case_id BIGINT NOT NULL,
    name VARCHAR(100) NOT NULL,
    person_type VARCHAR(20) NOT NULL,
    law_firm VARCHAR(200),
    license_number VARCHAR(50),
    professional_field VARCHAR(200),
    role VARCHAR(50),
    court_name VARCHAR(200),
    position VARCHAR(100),
    party_type VARCHAR(20),
    contact_phone VARCHAR(20),
    contact_email VARCHAR(100),
    address TEXT,
    rating INTEGER,
    notes TEXT,
    created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP
);

-- 创建 preservation_seal 表（先不创建外键）
CREATE TABLE IF NOT EXISTS preservation_seal (
    id BIGSERIAL PRIMARY KEY,
    case_id BIGINT NOT NULL,
    seal_type VARCHAR(30) NOT NULL,
    seal_amount NUMERIC(15, 2),
    case_number VARCHAR(100),
    court_name VARCHAR(200),
    court_address TEXT,
    start_date DATE NOT NULL,
    end_date DATE NOT NULL,
    renewal_date DATE,
    renewal_deadline DATE,
    status VARCHAR(20) NOT NULL DEFAULT 'active',
    renewal_applied BOOLEAN NOT NULL DEFAULT FALSE,
    renewal_materials TEXT,
    notes TEXT,
    created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP
);

-- 创建 litigation_notification_confirmation 表（先不创建外键）
CREATE TABLE IF NOT EXISTS litigation_notification_confirmation (
    id BIGSERIAL PRIMARY KEY,
    recipient_id BIGINT NOT NULL,
    notification_type VARCHAR(50) NOT NULL,
    title VARCHAR(255) NOT NULL,
    message TEXT NOT NULL,
    action_url VARCHAR(255),
    case_id BIGINT,
    timeline_id BIGINT,
    seal_id BIGINT,
    sent_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    read_at TIMESTAMP,
    confirmed_at TIMESTAMP,
    confirmed_by_id BIGINT,
    status VARCHAR(20) NOT NULL DEFAULT 'sent',
    urgency_level VARCHAR(20) NOT NULL DEFAULT 'medium',
    escalation_level INTEGER NOT NULL DEFAULT 0,
    escalated_to_id BIGINT,
    notification_channels JSONB DEFAULT '[]'::jsonb
);

-- 创建索引
CREATE INDEX IF NOT EXISTS litigation_process_case_id_idx ON litigation_process(case_id);
CREATE INDEX IF NOT EXISTS litigation_process_process_type_idx ON litigation_process(process_type);
CREATE INDEX IF NOT EXISTS litigation_process_status_idx ON litigation_process(status);
CREATE INDEX IF NOT EXISTS litigation_process_process_date_idx ON litigation_process(process_date);

CREATE INDEX IF NOT EXISTS litigation_document_case_id_idx ON litigation_document(case_id);
CREATE INDEX IF NOT EXISTS litigation_document_process_id_idx ON litigation_document(process_id);
CREATE INDEX IF NOT EXISTS litigation_document_document_type_idx ON litigation_document(document_type);

CREATE INDEX IF NOT EXISTS litigation_person_case_id_idx ON litigation_person(case_id);
CREATE INDEX IF NOT EXISTS litigation_person_person_type_idx ON litigation_person(person_type);

CREATE INDEX IF NOT EXISTS preservation_seal_case_id_idx ON preservation_seal(case_id);
CREATE INDEX IF NOT EXISTS preservation_seal_seal_type_idx ON preservation_seal(seal_type);
CREATE INDEX IF NOT EXISTS preservation_seal_status_idx ON preservation_seal(status);
CREATE INDEX IF NOT EXISTS preservation_seal_end_date_idx ON preservation_seal(end_date);

CREATE INDEX IF NOT EXISTS litigation_notification_confirmation_recipient_id_status_idx ON litigation_notification_confirmation(recipient_id, status);
CREATE INDEX IF NOT EXISTS litigation_notification_confirmation_case_id_status_idx ON litigation_notification_confirmation(case_id, status);
CREATE INDEX IF NOT EXISTS litigation_notification_confirmation_sent_at_idx ON litigation_notification_confirmation(sent_at);
CREATE INDEX IF NOT EXISTS litigation_notification_confirmation_notification_type_status_idx ON litigation_notification_confirmation(notification_type, status);

-- 创建外键约束（在所有表创建后）
DO $$ 
BEGIN
    -- litigation_process 外键
    IF NOT EXISTS (SELECT 1 FROM pg_constraint WHERE conname = 'litigation_process_case_id_fk') THEN
        ALTER TABLE litigation_process ADD CONSTRAINT litigation_process_case_id_fk 
        FOREIGN KEY (case_id) REFERENCES litigation_case(id) ON DELETE CASCADE DEFERRABLE INITIALLY DEFERRED;
    END IF;
    
    IF NOT EXISTS (SELECT 1 FROM pg_constraint WHERE conname = 'litigation_process_created_by_id_fk') THEN
        ALTER TABLE litigation_process ADD CONSTRAINT litigation_process_created_by_id_fk 
        FOREIGN KEY (created_by_id) REFERENCES system_user(id) ON DELETE SET NULL DEFERRABLE INITIALLY DEFERRED;
    END IF;
    
    -- litigation_document 外键
    IF NOT EXISTS (SELECT 1 FROM pg_constraint WHERE conname = 'litigation_document_case_id_fk') THEN
        ALTER TABLE litigation_document ADD CONSTRAINT litigation_document_case_id_fk 
        FOREIGN KEY (case_id) REFERENCES litigation_case(id) ON DELETE CASCADE DEFERRABLE INITIALLY DEFERRED;
    END IF;
    
    IF NOT EXISTS (SELECT 1 FROM pg_constraint WHERE conname = 'litigation_document_process_id_fk') THEN
        ALTER TABLE litigation_document ADD CONSTRAINT litigation_document_process_id_fk 
        FOREIGN KEY (process_id) REFERENCES litigation_process(id) ON DELETE SET NULL DEFERRABLE INITIALLY DEFERRED;
    END IF;
    
    IF NOT EXISTS (SELECT 1 FROM pg_constraint WHERE conname = 'litigation_document_uploaded_by_id_fk') THEN
        ALTER TABLE litigation_document ADD CONSTRAINT litigation_document_uploaded_by_id_fk 
        FOREIGN KEY (uploaded_by_id) REFERENCES system_user(id) ON DELETE SET NULL DEFERRABLE INITIALLY DEFERRED;
    END IF;
    
    -- litigation_person 外键
    IF NOT EXISTS (SELECT 1 FROM pg_constraint WHERE conname = 'litigation_person_case_id_fk') THEN
        ALTER TABLE litigation_person ADD CONSTRAINT litigation_person_case_id_fk 
        FOREIGN KEY (case_id) REFERENCES litigation_case(id) ON DELETE CASCADE DEFERRABLE INITIALLY DEFERRED;
    END IF;
    
    -- preservation_seal 外键
    IF NOT EXISTS (SELECT 1 FROM pg_constraint WHERE conname = 'preservation_seal_case_id_fk') THEN
        ALTER TABLE preservation_seal ADD CONSTRAINT preservation_seal_case_id_fk 
        FOREIGN KEY (case_id) REFERENCES litigation_case(id) ON DELETE CASCADE DEFERRABLE INITIALLY DEFERRED;
    END IF;
    
    -- litigation_notification_confirmation 外键
    IF NOT EXISTS (SELECT 1 FROM pg_constraint WHERE conname = 'litigation_notification_confirmation_recipient_id_fk') THEN
        ALTER TABLE litigation_notification_confirmation ADD CONSTRAINT litigation_notification_confirmation_recipient_id_fk 
        FOREIGN KEY (recipient_id) REFERENCES system_user(id) ON DELETE CASCADE DEFERRABLE INITIALLY DEFERRED;
    END IF;
    
    IF NOT EXISTS (SELECT 1 FROM pg_constraint WHERE conname = 'litigation_notification_confirmation_case_id_fk') THEN
        ALTER TABLE litigation_notification_confirmation ADD CONSTRAINT litigation_notification_confirmation_case_id_fk 
        FOREIGN KEY (case_id) REFERENCES litigation_case(id) ON DELETE CASCADE DEFERRABLE INITIALLY DEFERRED;
    END IF;
    
    IF NOT EXISTS (SELECT 1 FROM pg_constraint WHERE conname = 'litigation_notification_confirmation_timeline_id_fk') THEN
        ALTER TABLE litigation_notification_confirmation ADD CONSTRAINT litigation_notification_confirmation_timeline_id_fk 
        FOREIGN KEY (timeline_id) REFERENCES litigation_timeline(id) ON DELETE SET NULL DEFERRABLE INITIALLY DEFERRED;
    END IF;
    
    IF NOT EXISTS (SELECT 1 FROM pg_constraint WHERE conname = 'litigation_notification_confirmation_seal_id_fk') THEN
        ALTER TABLE litigation_notification_confirmation ADD CONSTRAINT litigation_notification_confirmation_seal_id_fk 
        FOREIGN KEY (seal_id) REFERENCES preservation_seal(id) ON DELETE SET NULL DEFERRABLE INITIALLY DEFERRED;
    END IF;
    
    IF NOT EXISTS (SELECT 1 FROM pg_constraint WHERE conname = 'litigation_notification_confirmation_confirmed_by_id_fk') THEN
        ALTER TABLE litigation_notification_confirmation ADD CONSTRAINT litigation_notification_confirmation_confirmed_by_id_fk 
        FOREIGN KEY (confirmed_by_id) REFERENCES system_user(id) ON DELETE SET NULL DEFERRABLE INITIALLY DEFERRED;
    END IF;
    
    IF NOT EXISTS (SELECT 1 FROM pg_constraint WHERE conname = 'litigation_notification_confirmation_escalated_to_id_fk') THEN
        ALTER TABLE litigation_notification_confirmation ADD CONSTRAINT litigation_notification_confirmation_escalated_to_id_fk 
        FOREIGN KEY (escalated_to_id) REFERENCES system_user(id) ON DELETE SET NULL DEFERRABLE INITIALLY DEFERRED;
    END IF;
END $$;

-- 创建索引
CREATE INDEX IF NOT EXISTS litigation_notification_confirmation_recipient_id_status_idx ON litigation_notification_confirmation(recipient_id, status);
CREATE INDEX IF NOT EXISTS litigation_notification_confirmation_case_id_status_idx ON litigation_notification_confirmation(case_id, status);
CREATE INDEX IF NOT EXISTS litigation_notification_confirmation_sent_at_idx ON litigation_notification_confirmation(sent_at);
CREATE INDEX IF NOT EXISTS litigation_notification_confirmation_notification_type_status_idx ON litigation_notification_confirmation(notification_type, status);

