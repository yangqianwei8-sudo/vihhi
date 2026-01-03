-- API接口管理模块数据库表创建脚本
-- 执行此脚本将创建以下表：
-- 1. api_external_system - 外部系统表
-- 2. api_interface - API接口表
-- 3. api_call_log - API调用日志表
-- 4. api_test_record - API测试记录表

BEGIN;

-- 创建外部系统表
CREATE TABLE IF NOT EXISTS api_external_system (
    id BIGSERIAL PRIMARY KEY,
    name VARCHAR(200) NOT NULL UNIQUE,
    code VARCHAR(50) UNIQUE,
    description TEXT,
    base_url VARCHAR(200) NOT NULL,
    contact_person VARCHAR(100),
    contact_phone VARCHAR(50),
    contact_email VARCHAR(254),
    status VARCHAR(20) NOT NULL DEFAULT 'active',
    is_active BOOLEAN NOT NULL DEFAULT TRUE,
    created_time TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_time TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT CURRENT_TIMESTAMP,
    created_by_id BIGINT NOT NULL,
    CONSTRAINT api_external_system_created_by_fk 
        FOREIGN KEY (created_by_id) 
        REFERENCES auth_user(id) 
        ON DELETE RESTRICT
);

-- 创建API接口表
CREATE TABLE IF NOT EXISTS api_interface (
    id BIGSERIAL PRIMARY KEY,
    name VARCHAR(200) NOT NULL,
    code VARCHAR(100) UNIQUE,
    url VARCHAR(500) NOT NULL,
    method VARCHAR(10) NOT NULL DEFAULT 'GET',
    auth_type VARCHAR(20) NOT NULL DEFAULT 'none',
    auth_config JSONB DEFAULT '{}',
    request_headers JSONB DEFAULT '{}',
    request_params JSONB DEFAULT '{}',
    request_body_schema JSONB DEFAULT '{}',
    response_schema JSONB DEFAULT '{}',
    description TEXT,
    timeout INTEGER NOT NULL DEFAULT 30,
    retry_count INTEGER NOT NULL DEFAULT 0,
    status VARCHAR(20) NOT NULL DEFAULT 'active',
    is_active BOOLEAN NOT NULL DEFAULT TRUE,
    version VARCHAR(20) NOT NULL DEFAULT '1.0',
    created_time TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_time TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT CURRENT_TIMESTAMP,
    external_system_id BIGINT NOT NULL,
    created_by_id BIGINT NOT NULL,
    CONSTRAINT api_interface_external_system_fk 
        FOREIGN KEY (external_system_id) 
        REFERENCES api_external_system(id) 
        ON DELETE CASCADE,
    CONSTRAINT api_interface_created_by_fk 
        FOREIGN KEY (created_by_id) 
        REFERENCES auth_user(id) 
        ON DELETE RESTRICT
);

-- 创建API调用日志表
CREATE TABLE IF NOT EXISTS api_call_log (
    id BIGSERIAL PRIMARY KEY,
    request_url VARCHAR(500) NOT NULL,
    request_method VARCHAR(10) NOT NULL,
    request_headers JSONB DEFAULT '{}',
    request_params JSONB DEFAULT '{}',
    request_body TEXT,
    response_status INTEGER,
    response_headers JSONB DEFAULT '{}',
    response_body TEXT,
    status VARCHAR(20) NOT NULL,
    error_message TEXT,
    duration DOUBLE PRECISION,
    called_time TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT CURRENT_TIMESTAMP,
    api_interface_id BIGINT NOT NULL,
    called_by_id BIGINT,
    CONSTRAINT api_call_log_api_interface_fk 
        FOREIGN KEY (api_interface_id) 
        REFERENCES api_interface(id) 
        ON DELETE CASCADE,
    CONSTRAINT api_call_log_called_by_fk 
        FOREIGN KEY (called_by_id) 
        REFERENCES auth_user(id) 
        ON DELETE SET NULL
);

-- 创建API测试记录表
CREATE TABLE IF NOT EXISTS api_test_record (
    id BIGSERIAL PRIMARY KEY,
    test_name VARCHAR(200) NOT NULL,
    test_params JSONB DEFAULT '{}',
    test_body TEXT,
    expected_status INTEGER,
    expected_response TEXT,
    actual_status INTEGER,
    actual_response TEXT,
    status VARCHAR(20) NOT NULL DEFAULT 'pending',
    error_message TEXT,
    test_duration DOUBLE PRECISION,
    tested_time TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT CURRENT_TIMESTAMP,
    api_interface_id BIGINT NOT NULL,
    tested_by_id BIGINT,
    CONSTRAINT api_test_record_api_interface_fk 
        FOREIGN KEY (api_interface_id) 
        REFERENCES api_interface(id) 
        ON DELETE CASCADE,
    CONSTRAINT api_test_record_tested_by_fk 
        FOREIGN KEY (tested_by_id) 
        REFERENCES auth_user(id) 
        ON DELETE SET NULL
);

-- 创建索引
CREATE INDEX IF NOT EXISTS api_externa_code_123abc_idx ON api_external_system(code, status);
CREATE INDEX IF NOT EXISTS api_externa_name_456def_idx ON api_external_system(name, is_active);
CREATE INDEX IF NOT EXISTS api_interfa_code_789ghi_idx ON api_interface(code, status);
CREATE INDEX IF NOT EXISTS api_interfa_externa_jkl012_idx ON api_interface(external_system_id, is_active);
CREATE INDEX IF NOT EXISTS api_interfa_method_mno345_idx ON api_interface(method, status);
CREATE INDEX IF NOT EXISTS api_call_lo_api_int_pqr678_idx ON api_call_log(api_interface_id, called_time);
CREATE INDEX IF NOT EXISTS api_call_lo_status_stu901_idx ON api_call_log(status, called_time);
CREATE INDEX IF NOT EXISTS api_call_lo_called__vwx234_idx ON api_call_log(called_by_id, called_time);
CREATE INDEX IF NOT EXISTS api_test_re_api_int_yza567_idx ON api_test_record(api_interface_id, tested_time);
CREATE INDEX IF NOT EXISTS api_test_re_status_bcd890_idx ON api_test_record(status, tested_time);

-- 插入迁移记录（如果不存在）
INSERT INTO django_migrations (app, name, applied) 
VALUES ('api_management', '0001_initial', CURRENT_TIMESTAMP)
ON CONFLICT (app, name) DO NOTHING;

COMMIT;

-- 验证表是否创建成功
SELECT 
    'api_external_system' as table_name,
    CASE WHEN EXISTS (SELECT 1 FROM information_schema.tables WHERE table_name = 'api_external_system') 
         THEN '✓ 已创建' 
         ELSE '✗ 未创建' 
    END as status
UNION ALL
SELECT 
    'api_interface' as table_name,
    CASE WHEN EXISTS (SELECT 1 FROM information_schema.tables WHERE table_name = 'api_interface') 
         THEN '✓ 已创建' 
         ELSE '✗ 未创建' 
    END as status
UNION ALL
SELECT 
    'api_call_log' as table_name,
    CASE WHEN EXISTS (SELECT 1 FROM information_schema.tables WHERE table_name = 'api_call_log') 
         THEN '✓ 已创建' 
         ELSE '✗ 未创建' 
    END as status
UNION ALL
SELECT 
    'api_test_record' as table_name,
    CASE WHEN EXISTS (SELECT 1 FROM information_schema.tables WHERE table_name = 'api_test_record') 
         THEN '✓ 已创建' 
         ELSE '✗ 未创建' 
    END as status;
