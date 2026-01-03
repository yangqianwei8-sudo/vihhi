-- 简化版SQL脚本：添加商机类型和服务类型字段
-- 直接执行，适用于PostgreSQL数据库

-- 添加商机类型字段
ALTER TABLE "business_opportunity" 
ADD COLUMN IF NOT EXISTS "opportunity_type" varchar(30) NULL;

-- 添加服务类型外键字段
ALTER TABLE "business_opportunity" 
ADD COLUMN IF NOT EXISTS "service_type_id" bigint NULL;

-- 添加外键约束（如果不存在）
DO $$ 
BEGIN
    IF NOT EXISTS (
        SELECT 1 FROM information_schema.table_constraints 
        WHERE constraint_name = 'business_opportunity_service_type_id_fk'
        AND table_name = 'business_opportunity'
    ) THEN
        ALTER TABLE "business_opportunity" 
        ADD CONSTRAINT "business_opportunity_service_type_id_fk" 
        FOREIGN KEY ("service_type_id") 
        REFERENCES "production_management_service_type" ("id") 
        DEFERRABLE INITIALLY DEFERRED;
    END IF;
END $$;

-- 创建索引
CREATE INDEX IF NOT EXISTS "business_opportunity_opportunity_type_idx" 
ON "business_opportunity" ("opportunity_type");

CREATE INDEX IF NOT EXISTS "business_opportunity_service_type_id_idx" 
ON "business_opportunity" ("service_type_id");

