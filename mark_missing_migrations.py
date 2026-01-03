#!/usr/bin/env python
"""
标记缺失的迁移为已应用
用于修复迁移历史不一致问题
"""
import os
import sys
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'backend.config.settings')
django.setup()

from django.db import connection
from django.utils import timezone

# 需要标记的迁移列表（按顺序）
migrations_to_mark = [
    ('customer_management', '0002_initial'),
    ('customer_management', '0003_businesscontract_businesspaymentplan'),
    ('customer_management', '0004_copy_contracts'),
    ('customer_management', '0005_contractapproval_contractchange_contractfile_and_more'),
    ('customer_management', '0006_alter_businesscontract_contract_number'),
    ('customer_management', '0007_contractstatuslog'),
    ('customer_management', '0008_businessopportunity_client_client_type_and_more'),
    ('customer_management', '0009_add_legal_risk_fields'),
    ('customer_management', '0010_client_consumption_limit_count_and_more'),
    ('customer_management', '0011_remove_client_address_remove_client_email_and_more'),
    ('customer_management', '0012_add_quotation_mode_fields'),
    ('customer_management', '0013_add_qixinbao_fields_remove_short_name'),
    ('customer_management', '0014_merge_20251126_1419'),
    ('customer_management', '0015_remove_client_blacklist_details_remove_client_code_and_more'),
]

def mark_migrations():
    cursor = connection.cursor()
    marked = []
    skipped = []
    
    for app, name in migrations_to_mark:
        # 检查是否已存在
        cursor.execute("""
            SELECT COUNT(*) FROM django_migrations 
            WHERE app = %s AND name = %s
        """, [app, name])
        
        if cursor.fetchone()[0] > 0:
            skipped.append((app, name))
            print(f"⏭️  跳过（已存在）: {app}.{name}")
        else:
            cursor.execute("""
                INSERT INTO django_migrations (app, name, applied)
                VALUES (%s, %s, %s)
            """, [app, name, timezone.now()])
            connection.commit()
            marked.append((app, name))
            print(f"✓ 已标记: {app}.{name}")
    
    print(f"\n总结:")
    print(f"  已标记: {len(marked)} 个迁移")
    print(f"  已跳过: {len(skipped)} 个迁移")
    
    return len(marked) > 0

if __name__ == '__main__':
    print("=" * 70)
    print("标记缺失的迁移为已应用")
    print("=" * 70)
    print()
    
    mark_migrations()
    
    print("\n✓ 完成！")

