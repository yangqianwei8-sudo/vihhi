-- 手动添加定位字段到 customer_relationship 表
-- 如果迁移系统无法正常工作，可以直接执行此 SQL

-- 添加纬度字段
ALTER TABLE "customer_relationship" 
ADD COLUMN IF NOT EXISTS "latitude" NUMERIC(10, 7) NULL;

-- 添加经度字段
ALTER TABLE "customer_relationship" 
ADD COLUMN IF NOT EXISTS "longitude" NUMERIC(10, 7) NULL;

-- 添加定位地址字段
ALTER TABLE "customer_relationship" 
ADD COLUMN IF NOT EXISTS "location_address" VARCHAR(500) NULL;

-- 添加注释（PostgreSQL语法）
COMMENT ON COLUMN "customer_relationship"."latitude" IS '纬度';
COMMENT ON COLUMN "customer_relationship"."longitude" IS '经度';
COMMENT ON COLUMN "customer_relationship"."location_address" IS '定位地址';

