-- Migration: 0026_remove_contract_party_model
-- 删除contract_party表

BEGIN;

-- 删除contract_party表（CASCADE会自动删除相关的外键约束和索引）
DROP TABLE IF EXISTS contract_party CASCADE;

COMMIT;

