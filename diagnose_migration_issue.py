#!/usr/bin/env python
"""
诊断迁移依赖问题
"""
import os
import sys
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'backend.config.settings')
django.setup()

from django.apps import apps
from django.db import connection

print("=" * 70)
print("诊断迁移依赖问题")
print("=" * 70)

# 1. 检查应用是否已安装
print("\n1. 检查已安装的应用:")
installed_apps = [app.label for app in apps.get_app_configs()]
print(f"   已安装的应用数量: {len(installed_apps)}")
if 'permission_management' in installed_apps:
    print("   ✓ permission_management 应用已安装")
    app_config = apps.get_app_config('permission_management')
    print(f"     应用名称: {app_config.name}")
    print(f"     应用标签: {app_config.label}")
    print(f"     应用路径: {app_config.path}")
else:
    print("   ✗ permission_management 应用未安装")
    print(f"   已安装的应用: {', '.join(sorted(installed_apps))}")

# 2. 检查模型是否存在
print("\n2. 检查模型:")
try:
    from backend.apps.permission_management.models import PermissionItem
    print("   ✓ PermissionItem 模型可以导入")
    print(f"     模型名称: {PermissionItem.__name__}")
    print(f"     表名: {PermissionItem._meta.db_table}")
except Exception as e:
    print(f"   ✗ PermissionItem 模型无法导入: {e}")

# 3. 检查数据库中的迁移记录
print("\n3. 检查数据库迁移记录:")
cursor = connection.cursor()
cursor.execute("""
    SELECT app, name, applied 
    FROM django_migrations 
    WHERE app = 'permission_management'
    ORDER BY applied
""")
rows = cursor.fetchall()
if rows:
    print(f"   找到 {len(rows)} 条 permission_management 迁移记录:")
    for app, name, applied in rows:
        print(f"     - {app}.{name} (应用时间: {applied})")
else:
    print("   ⚠️  没有找到 permission_management 的迁移记录")

# 4. 检查 system_management 的迁移记录
print("\n4. 检查 system_management 迁移记录:")
cursor.execute("""
    SELECT app, name, applied 
    FROM django_migrations 
    WHERE app = 'system_management'
    ORDER BY applied
""")
rows = cursor.fetchall()
if rows:
    print(f"   找到 {len(rows)} 条 system_management 迁移记录:")
    for app, name, applied in rows[:5]:  # 只显示前5条
        print(f"     - {app}.{name}")
    if len(rows) > 5:
        print(f"     ... 还有 {len(rows) - 5} 条")
    
    # 检查 0007 是否已应用
    has_0007 = any(name == '0007_alter_role_custom_permissions' for _, name, _ in rows)
    if has_0007:
        print("   ✓ 0007_alter_role_custom_permissions 已应用")
    else:
        print("   ✗ 0007_alter_role_custom_permissions 未应用")

# 5. 检查表是否存在
print("\n5. 检查数据库表:")
cursor.execute("""
    SELECT table_name 
    FROM information_schema.tables 
    WHERE table_schema = 'public' 
    AND table_name IN ('system_permission_item', 'system_role')
    ORDER BY table_name
""")
tables = [row[0] for row in cursor.fetchall()]
if 'system_permission_item' in tables:
    print("   ✓ system_permission_item 表存在")
else:
    print("   ✗ system_permission_item 表不存在")

if 'system_role' in tables:
    print("   ✓ system_role 表存在")
else:
    print("   ✗ system_role 表不存在")

print("\n" + "=" * 70)
print("诊断完成")
print("=" * 70)

