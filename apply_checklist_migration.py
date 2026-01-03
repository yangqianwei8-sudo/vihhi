#!/usr/bin/env python
"""应用客户沟通准备清单迁移脚本"""
import os
import sys
import django

# 设置Django环境
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'backend.config.settings')
django.setup()

from django.core.management import call_command
from django.db import connection

def check_migration_status():
    """检查迁移状态"""
    cursor = connection.cursor()
    cursor.execute("""
        SELECT COUNT(*) FROM django_migrations 
        WHERE app='customer_success' AND name='0025_add_communication_checklist'
    """)
    result = cursor.fetchone()
    return result[0] > 0 if result else False

def check_table_exists():
    """检查表是否存在"""
    cursor = connection.cursor()
    # 根据数据库类型检查表
    db_backend = connection.vendor
    if db_backend == 'postgresql':
        cursor.execute("""
            SELECT EXISTS (
                SELECT FROM information_schema.tables 
                WHERE table_name = 'customer_communication_checklist'
            )
        """)
    elif db_backend == 'sqlite':
        cursor.execute("""
            SELECT name FROM sqlite_master 
            WHERE type='table' AND name='customer_communication_checklist'
        """)
    else:
        # MySQL
        cursor.execute("""
            SELECT COUNT(*) FROM information_schema.tables 
            WHERE table_schema = DATABASE() AND table_name = 'customer_communication_checklist'
        """)
    
    result = cursor.fetchone()
    if db_backend == 'postgresql':
        return result[0] if result else False
    elif db_backend == 'sqlite':
        return result is not None
    else:
        return result[0] > 0 if result else False

if __name__ == '__main__':
    print("=" * 60)
    print("客户沟通准备清单迁移检查")
    print("=" * 60)
    
    # 检查迁移状态
    migration_applied = check_migration_status()
    print(f"迁移记录状态: {'已应用' if migration_applied else '未应用'}")
    
    # 检查表是否存在
    table_exists = check_table_exists()
    print(f"数据表状态: {'已存在' if table_exists else '不存在'}")
    
    print("\n" + "=" * 60)
    
    if migration_applied and table_exists:
        print("✓ 迁移已完成，表已创建")
        sys.exit(0)
    elif not migration_applied:
        print("正在应用迁移...")
        try:
            # 先确保所有应用的迁移都已应用
            print("步骤1: 应用所有应用的迁移...")
            call_command('migrate', verbosity=1, interactive=False)
            
            # 然后应用我们的特定迁移
            print("\n步骤2: 应用客户沟通准备清单迁移...")
            call_command('migrate', 'customer_success', '0025_add_communication_checklist', verbosity=2)
            print("✓ 迁移应用成功")
            
            # 再次检查
            migration_applied = check_migration_status()
            table_exists = check_table_exists()
            
            if migration_applied and table_exists:
                print("✓ 验证成功：迁移已应用，表已创建")
            else:
                print("⚠ 警告：迁移可能未完全应用")
                print(f"   迁移记录: {'已应用' if migration_applied else '未应用'}")
                print(f"   数据表: {'已存在' if table_exists else '不存在'}")
        except Exception as e:
            print(f"✗ 迁移失败: {str(e)}")
            import traceback
            traceback.print_exc()
            sys.exit(1)
    else:
        print("⚠ 状态异常：表存在但迁移记录不存在")
        sys.exit(1)

