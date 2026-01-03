#!/usr/bin/env python
"""
直接标记 customer_success 的迁移为已应用
绕过 Django 迁移状态构建时的应用识别问题
"""
import os
import sys

script_dir = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, script_dir)

import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'backend.config.settings')
django.setup()

from django.db import connection
from django.utils import timezone

def mark_migrations_applied():
    """标记迁移为已应用"""
    cursor = connection.cursor()
    
    migrations_to_mark = [
        ('customer_success', '0030_add_communication_checklist_fields_to_visit_plan'),
        ('customer_success', '0031_remove_customercommunicationchecklist_client_and_more'),
        ('customer_success', '0032_authorizationletter'),
    ]
    
    print("=" * 70)
    print("标记 customer_success 迁移为已应用")
    print("=" * 70)
    
    for app, migration_name in migrations_to_mark:
        # 检查是否已存在
        cursor.execute("""
            SELECT COUNT(*) FROM django_migrations 
            WHERE app = %s AND name = %s
        """, [app, migration_name])
        
        exists = cursor.fetchone()[0] > 0
        
        if not exists:
            cursor.execute("""
                INSERT INTO django_migrations (app, name, applied)
                VALUES (%s, %s, %s)
            """, [app, migration_name, timezone.now()])
            print(f"✓ 标记迁移: {app}.{migration_name}")
        else:
            print(f"- 迁移已存在: {app}.{migration_name}")
    
    connection.commit()
    print("\n" + "=" * 70)
    print("完成！")
    print("=" * 70)
    print("\n注意：这只是标记迁移为已应用，不会执行实际的数据库操作。")
    print("如果表已经存在，这是安全的。如果表不存在，需要先创建表。")

if __name__ == '__main__':
    mark_migrations_applied()

