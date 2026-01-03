-- Migration: 0005_add_department_business_manager_to_contract
-- 添加部门、商务经理和关联商机字段到business_contract表

BEGIN;

-- Add field opportunity to businesscontract
ALTER TABLE "business_contract" ADD COLUMN "opportunity_id" bigint NULL;
ALTER TABLE "business_contract" ADD CONSTRAINT "business_contract_opportunity_id_63314f6f_fk_business_" FOREIGN KEY ("opportunity_id") REFERENCES "business_opportunity"("id") DEFERRABLE INITIALLY DEFERRED;
CREATE INDEX "business_contract_opportunity_id_63314f6f" ON "business_contract" ("opportunity_id");

-- Add field department to businesscontract
ALTER TABLE "business_contract" ADD COLUMN "department_id" bigint NULL;
ALTER TABLE "business_contract" ADD CONSTRAINT "business_contract_department_id_ed91fa91_fk_system_de" FOREIGN KEY ("department_id") REFERENCES "system_department"("id") DEFERRABLE INITIALLY DEFERRED;
CREATE INDEX "business_contract_department_id_ed91fa91" ON "business_contract" ("department_id");

-- Add field business_manager to businesscontract
ALTER TABLE "business_contract" ADD COLUMN "business_manager_id" bigint NULL;
ALTER TABLE "business_contract" ADD CONSTRAINT "business_contract_business_manager_id_e2afd2d7_fk_system_us" FOREIGN KEY ("business_manager_id") REFERENCES "system_user"("id") DEFERRABLE INITIALLY DEFERRED;
CREATE INDEX "business_contract_business_manager_id_e2afd2d7" ON "business_contract" ("business_manager_id");

COMMIT;

