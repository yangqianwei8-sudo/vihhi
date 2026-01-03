-- 创建文件模板表
CREATE TABLE IF NOT EXISTS "file_template" (
    "id" BIGSERIAL NOT NULL PRIMARY KEY,
    "name" VARCHAR(100) NOT NULL,
    "code" VARCHAR(50) NOT NULL DEFAULT '',
    "stage" VARCHAR(20) NOT NULL,
    "category_id" BIGINT NULL,
    "template_file" VARCHAR(100) NULL,
    "description" TEXT NOT NULL DEFAULT '',
    "sort_order" INTEGER NOT NULL DEFAULT 0,
    "is_active" BOOLEAN NOT NULL DEFAULT true,
    "created_at" TIMESTAMP WITH TIME ZONE NOT NULL,
    "updated_at" TIMESTAMP WITH TIME ZONE NOT NULL,
    "created_by_id" BIGINT NULL,
    CONSTRAINT "file_template_stage_check" CHECK ("stage" IN ('conversion', 'contract', 'production', 'settlement', 'payment', 'after_sales', 'litigation')),
    CONSTRAINT "file_template_category_id_fkey" FOREIGN KEY ("category_id") REFERENCES "file_category" ("id") ON DELETE SET NULL DEFERRABLE INITIALLY DEFERRED,
    CONSTRAINT "file_template_created_by_id_fkey" FOREIGN KEY ("created_by_id") REFERENCES "system_user" ("id") ON DELETE SET NULL DEFERRABLE INITIALLY DEFERRED,
    CONSTRAINT "file_template_stage_name_unique" UNIQUE ("stage", "name")
);

-- 创建索引
CREATE INDEX IF NOT EXISTS "file_template_stage_sort_order_idx" ON "file_template" ("stage", "sort_order");
CREATE INDEX IF NOT EXISTS "file_template_stage_is_active_idx" ON "file_template" ("stage", "is_active");
CREATE INDEX IF NOT EXISTS "file_template_created_at_idx" ON "file_template" ("created_at");
CREATE INDEX IF NOT EXISTS "file_template_category_id_idx" ON "file_template" ("category_id");
CREATE INDEX IF NOT EXISTS "file_template_created_by_id_idx" ON "file_template" ("created_by_id");

