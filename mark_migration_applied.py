#!/usr/bin/env python
"""
直接在数据库中标记迁移为已应用
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

def mark_migration_applied():
    """标记迁移为已应用"""
    cursor = connection.cursor()
    
    migrations_to_mark = [
        ('customer_success', '0014_merge_20251126_1419'),
        ('customer_success', '0015_remove_client_blacklist_details_remove_client_code_and_more'),
    ]
    
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
    print("\n完成！")

if __name__ == '__main__':
    mark_migration_applied()

