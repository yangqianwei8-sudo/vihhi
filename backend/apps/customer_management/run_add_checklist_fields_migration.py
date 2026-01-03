#!/usr/bin/env python
"""添加沟通清单字段到VisitPlan模型的迁移脚本"""
import os
import sys
from pathlib import Path
import django
from django.db import connection

# Add project root to Python path
BASE_DIR = Path(__file__).resolve().parent.parent.parent.parent
sys.path.insert(0, str(BASE_DIR))

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'backend.config.settings')
django.setup()

def add_checklist_fields():
    print("\n============================================================")
    print("开始添加沟通清单字段到 customer_visit_plan 表...")
    print("============================================================")
    
    cursor = connection.cursor()
    success_count = 0
    error_count = 0
    
    try:
        # 添加 communication_checklist 字段
        try:
            cursor.execute("""
                ALTER TABLE customer_visit_plan 
                ADD COLUMN IF NOT EXISTS communication_checklist TEXT;
            """)
            print("✅ communication_checklist 字段添加成功")
            success_count += 1
        except Exception as e:
            if 'already exists' in str(e).lower() or 'duplicate' in str(e).lower():
                print("⚠️  communication_checklist 字段已存在，跳过")
                success_count += 1
            else:
                print(f"❌ communication_checklist 字段添加失败: {e}")
                error_count += 1
        
        # 添加 checklist_prepared 字段
        try:
            cursor.execute("""
                ALTER TABLE customer_visit_plan 
                ADD COLUMN IF NOT EXISTS checklist_prepared BOOLEAN DEFAULT FALSE;
            """)
            print("✅ checklist_prepared 字段添加成功")
            success_count += 1
        except Exception as e:
            if 'already exists' in str(e).lower() or 'duplicate' in str(e).lower():
                print("⚠️  checklist_prepared 字段已存在，跳过")
                success_count += 1
            else:
                print(f"❌ checklist_prepared 字段添加失败: {e}")
                error_count += 1
        
        # 添加 checklist_prepared_time 字段
        try:
            cursor.execute("""
                ALTER TABLE customer_visit_plan 
                ADD COLUMN IF NOT EXISTS checklist_prepared_time TIMESTAMP NULL;
            """)
            print("✅ checklist_prepared_time 字段添加成功")
            success_count += 1
        except Exception as e:
            if 'already exists' in str(e).lower() or 'duplicate' in str(e).lower():
                print("⚠️  checklist_prepared_time 字段已存在，跳过")
                success_count += 1
            else:
                print(f"❌ checklist_prepared_time 字段添加失败: {e}")
                error_count += 1
        
        connection.commit()
        print(f"\n============================================================")
        print(f"✅ 迁移完成！成功: {success_count}, 失败: {error_count}")
        print(f"============================================================")
        return error_count == 0
    except Exception as e:
        print(f"\n❌ 迁移执行失败: {e}", file=sys.stderr)
        connection.rollback()
        return False

def mark_migration_applied():
    print("\n正在标记迁移为已应用...")
    try:
        from django.db.migrations.recorder import MigrationRecorder
        recorder = MigrationRecorder(connection)
        if not recorder.migration_applied('customer_success', '0030_add_communication_checklist_fields_to_visit_plan'):
            recorder.record_applied('customer_success', '0030_add_communication_checklist_fields_to_visit_plan')
            print("✅ 迁移 0030_add_communication_checklist_fields_to_visit_plan 已标记为已应用")
        else:
            print("ℹ️  迁移 0030_add_communication_checklist_fields_to_visit_plan 已是已应用状态")
    except Exception as e:
        print(f"⚠️  标记迁移失败（不影响功能）: {e}")

if __name__ == '__main__':
    if add_checklist_fields():
        mark_migration_applied()
    print("\n✅ 迁移完成！")

