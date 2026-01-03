#!/usr/bin/env python
"""
手动应用0008迁移的脚本
执行SQL来添加client、client_contact和recipient_email字段到outgoing_document表
"""
import os
import sys
import django

# 设置Django环境
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'backend.config.settings')
django.setup()

from django.db import connection

def apply_migration():
    """执行迁移SQL"""
    sql_script = """
    -- 添加client字段
    ALTER TABLE outgoing_document 
    ADD COLUMN IF NOT EXISTS client_id BIGINT NULL;

    -- 添加client_contact字段
    ALTER TABLE outgoing_document 
    ADD COLUMN IF NOT EXISTS client_contact_id BIGINT NULL;

    -- 添加recipient_email字段
    ALTER TABLE outgoing_document 
    ADD COLUMN IF NOT EXISTS recipient_email VARCHAR(255) NULL;

    -- 添加外键约束
    DO $$
    BEGIN
        -- 添加client外键
        IF NOT EXISTS (
            SELECT 1 FROM pg_constraint 
            WHERE conname = 'outgoing_document_client_id_fkey'
        ) THEN
            ALTER TABLE outgoing_document 
            ADD CONSTRAINT outgoing_document_client_id_fkey 
            FOREIGN KEY (client_id) 
            REFERENCES customer_client(id) 
            ON DELETE SET NULL;
        END IF;

        -- 添加client_contact外键
        IF NOT EXISTS (
            SELECT 1 FROM pg_constraint 
            WHERE conname = 'outgoing_document_client_contact_id_fkey'
        ) THEN
            ALTER TABLE outgoing_document 
            ADD CONSTRAINT outgoing_document_client_contact_id_fkey 
            FOREIGN KEY (client_contact_id) 
            REFERENCES customer_contact(id) 
            ON DELETE SET NULL;
        END IF;
    END $$;

    -- 更新字段注释
    COMMENT ON COLUMN outgoing_document.client_id IS '关联的客户，用于自动填充办公地址';
    COMMENT ON COLUMN outgoing_document.client_contact_id IS '从客户管理-人员有关系管理中获取，用于自动填充联系人、联系电话和联系邮箱';
    COMMENT ON COLUMN outgoing_document.recipient_email IS '联系邮箱，可从客户联系人中自动填充';
    COMMENT ON COLUMN outgoing_document.recipient_contact IS '签约主体代表姓名，可从客户联系人中自动填充';
    COMMENT ON COLUMN outgoing_document.recipient_phone IS '联系电话，可从客户联系人中自动填充';
    COMMENT ON COLUMN outgoing_document.recipient_address IS '办公地址，可从客户信息中自动填充';
    """
    
    try:
        with connection.cursor() as cursor:
            # 执行SQL脚本
            cursor.execute(sql_script)
            print("✅ 迁移SQL执行成功！")
            
            # 标记迁移为已应用
            mark_migration_sql = """
            INSERT INTO django_migrations (app, name, applied) 
            VALUES ('delivery_customer', '0008_add_client_contact_to_outgoing_document', NOW())
            ON CONFLICT DO NOTHING;
            """
            try:
                cursor.execute(mark_migration_sql)
                print("✅ 迁移记录已标记为已应用")
            except Exception as e:
                print(f"⚠️  标记迁移记录时出现警告（可忽略）: {e}")
            
            connection.commit()
            print("\n✅ 所有操作完成！")
            print("\n已添加的字段：")
            print("  - client_id (关联客户)")
            print("  - client_contact_id (签约主体代表)")
            print("  - recipient_email (联系邮箱)")
            print("\n字段已自动填充功能已启用！")
            
    except Exception as e:
        print(f"❌ 执行迁移时出错: {e}")
        connection.rollback()
        raise

if __name__ == '__main__':
    print("开始应用0008迁移...")
    print("=" * 50)
    apply_migration()

