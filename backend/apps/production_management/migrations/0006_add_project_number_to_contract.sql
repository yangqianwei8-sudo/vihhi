-- Migration: 0006_add_project_number_to_contract
-- 添加project_number字段到business_contract表

BEGIN;

-- Add field project_number to businesscontract
ALTER TABLE "business_contract" ADD COLUMN "project_number" VARCHAR(50) NULL UNIQUE;

COMMIT;

