-- 创建沟通清单问题管理相关的表
-- 迁移: 0026_add_communication_checklist_questions

-- 创建问题模板表
CREATE TABLE IF NOT EXISTS communication_checklist_question (
    id BIGSERIAL PRIMARY KEY,
    part VARCHAR(20) NOT NULL,
    "order" INTEGER NOT NULL,
    question_text VARCHAR(500) NOT NULL,
    question_code VARCHAR(50) NOT NULL UNIQUE,
    is_active BOOLEAN NOT NULL DEFAULT TRUE,
    created_time TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_time TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT CURRENT_TIMESTAMP
);

-- 创建答案表
CREATE TABLE IF NOT EXISTS communication_checklist_answer (
    id BIGSERIAL PRIMARY KEY,
    checklist_id BIGINT NOT NULL,
    question_id BIGINT NOT NULL,
    answer VARCHAR(20) NOT NULL DEFAULT 'unknown',
    note_before TEXT NOT NULL DEFAULT '',
    note_after TEXT NOT NULL DEFAULT '',
    created_time TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_time TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT CURRENT_TIMESTAMP,
    CONSTRAINT communication_checklist_answer_checklist_id_fkey 
        FOREIGN KEY (checklist_id) 
        REFERENCES customer_communication_checklist(id) 
        ON DELETE CASCADE,
    CONSTRAINT communication_checklist_answer_question_id_fkey 
        FOREIGN KEY (question_id) 
        REFERENCES communication_checklist_question(id) 
        ON DELETE RESTRICT,
    CONSTRAINT communication_checklist_answer_checklist_question_unique 
        UNIQUE (checklist_id, question_id)
);

-- 创建索引
CREATE INDEX IF NOT EXISTS comm_check_q_part_order_idx 
    ON communication_checklist_question(part, "order");

CREATE INDEX IF NOT EXISTS comm_check_q_is_active_idx 
    ON communication_checklist_question(is_active);

CREATE INDEX IF NOT EXISTS comm_check_a_checklist_question_idx 
    ON communication_checklist_answer(checklist_id, question_id);

-- 添加表注释
COMMENT ON TABLE communication_checklist_question IS '沟通清单问题模板';
COMMENT ON TABLE communication_checklist_answer IS '沟通清单答案';

