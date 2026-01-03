#!/usr/bin/env python
"""
标记settlement相关迁移为已应用
"""
import os
import sys
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'backend.config.settings')
django.setup()

from django.db import connection
from django.utils import timezone

migrations_to_mark = [
    ('settlement_management', '0002_alter_contractsettlement_approver_and_more'),
    ('settlement_center', '0006_alter_outputvaluerecord_project_and_more'),
]

cursor = connection.cursor()
for app, name in migrations_to_mark:
    cursor.execute("""
        INSERT INTO django_migrations (app, name, applied)
        VALUES (%s, %s, %s)
        ON CONFLICT DO NOTHING
    """, [app, name, timezone.now()])
    connection.commit()
    print(f'✓ 已标记 {app}.{name} 为已应用')

print('\n✓ 完成！')

