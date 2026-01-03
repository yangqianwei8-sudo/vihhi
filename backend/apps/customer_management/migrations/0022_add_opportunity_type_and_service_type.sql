-- 手动SQL脚本：添加商机类型和服务类型字段
-- 如果无法运行Django迁移，可以手动执行此SQL脚本
-- 适用于PostgreSQL数据库

-- 检查并添加商机类型字段（如果不存在）
DO $$ 
BEGIN
    IF NOT EXISTS (
        SELECT 1 FROM information_schema.columns 
        WHERE table_name = 'business_opportunity' 
        AND column_name = 'opportunity_type'
    ) THEN
        ALTER TABLE "business_opportunity" 
        ADD COLUMN "opportunity_type" varchar(30) NULL;
    END IF;
END $$;

-- 检查并添加服务类型外键字段（如果不存在）
DO $$ 
BEGIN
    IF NOT EXISTS (
        SELECT 1 FROM information_schema.columns 
        WHERE table_name = 'business_opportunity' 
        AND column_name = 'service_type_id'
    ) THEN
        ALTER TABLE "business_opportunity" 
        ADD COLUMN "service_type_id" bigint NULL;
    END IF;
END $$;

-- 检查并添加外键约束（如果不存在）
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

-- 创建索引（如果不存在）
CREATE INDEX IF NOT EXISTS "business_opportunity_opportunity_type_idx" 
ON "business_opportunity" ("opportunity_type");

CREATE INDEX IF NOT EXISTS "business_opportunity_service_type_id_idx" 
ON "business_opportunity" ("service_type_id");

