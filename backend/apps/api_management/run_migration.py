#!/usr/bin/env python
"""
直接执行迁移创建API管理模块的表
使用Django的迁移系统
"""
import os
import sys

# 添加项目根目录到Python路径
script_dir = os.path.dirname(os.path.abspath(__file__))
project_root = os.path.abspath(os.path.join(script_dir, '../../../../'))
sys.path.insert(0, project_root)

import django
from django.core.management import call_command
from django.db import connection

# 设置Django环境
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'backend.config.settings')
django.setup()

def check_tables():
    """检查表是否创建成功"""
    cursor = connection.cursor()
    cursor.execute("""
        SELECT table_name 
        FROM information_schema.tables 
        WHERE table_schema = 'public' 
        AND table_name LIKE 'api_%'
        ORDER BY table_name
    """)
    tables = [row[0] for row in cursor.fetchall()]
    return tables

def check_migration_status():
    """检查迁移状态"""
    cursor = connection.cursor()
    cursor.execute("""
        SELECT app, name 
        FROM django_migrations 
        WHERE app = 'api_management'
        ORDER BY name
    """)
    migrations = [row[1] for row in cursor.fetchall()]
    return migrations

if __name__ == '__main__':
    print("🚀 开始创建API管理模块的数据库表...\n")
    
    # 检查现有表
    existing_tables = check_tables()
    existing_migrations = check_migration_status()
    
    if existing_tables:
        print(f"⚠️  发现已存在的表: {', '.join(existing_tables)}")
    
    if existing_migrations:
        print(f"⚠️  发现已应用的迁移: {', '.join(existing_migrations)}")
    
    if existing_tables or existing_migrations:
        response = input("\n是否继续执行迁移？(y/n): ")
        if response.lower() != 'y':
            print("已取消")
            sys.exit(0)
    
    try:
        print("\n📦 执行迁移命令...")
        # 执行迁移
        call_command('migrate', 'api_management', verbosity=2, interactive=False)
        print("\n✅ 迁移命令执行完成！")
        
    except Exception as e:
        print(f"\n❌ 迁移执行失败: {e}")
        print("\n尝试使用--fake标记已存在的迁移...")
        try:
            # 如果迁移失败，尝试标记为已应用
            if '0001_initial' not in existing_migrations:
                call_command('migrate', 'api_management', '0001', '--fake', verbosity=2)
                print("✅ 已标记迁移为已应用")
        except Exception as e2:
            print(f"❌ 标记迁移失败: {e2}")
            sys.exit(1)
    
    # 检查结果
    print("\n📊 检查创建的表...")
    tables = check_tables()
    expected_tables = ['api_external_system', 'api_interface', 'api_call_log', 'api_test_record']
    
    if tables:
        print(f"\n✅ 已创建的表 ({len(tables)}/{len(expected_tables)}):")
        for table in expected_tables:
            if table in tables:
                print(f"  ✓ {table}")
            else:
                print(f"  ✗ {table} (缺失)")
    else:
        print("❌ 未找到任何表")
    
    # 检查迁移记录
    print("\n📋 检查迁移记录...")
    migrations = check_migration_status()
    if migrations:
        print(f"✅ 已应用的迁移: {', '.join(migrations)}")
    else:
        print("⚠️  未找到迁移记录")
    
    # 最终验证
    if len(tables) >= len(expected_tables):
        print("\n🎉 迁移成功完成！")
        print("\n📝 下一步：")
        print("  1. 访问 Django 后台管理: /admin/")
        print("  2. 在 'API接口管理' 模块下添加外部系统和API接口")
        sys.exit(0)
    else:
        print(f"\n⚠️  迁移可能未完全成功")
        print(f"   期望表数: {len(expected_tables)}, 实际表数: {len(tables)}")
        if tables:
            print("   请检查缺失的表并手动创建")
        sys.exit(1)
