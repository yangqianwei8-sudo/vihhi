#!/usr/bin/env python
"""
系统迁移状态检查脚本
检查所有应用的迁移状态，识别潜在问题
"""
import os
import sys
import django

# 设置Django环境
script_dir = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, script_dir)
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'backend.config.settings')
django.setup()

from django.core.management import call_command
from django.db import connection
from io import StringIO
import re

def check_migration_status():
    """检查所有应用的迁移状态"""
    print("=" * 60)
    print("系统迁移状态检查")
    print("=" * 60)
    print()
    
    # 获取所有已安装的应用
    from django.apps import apps
    installed_apps = [app.label for app in apps.get_app_configs() 
                     if app.label.startswith('backend.apps.') or 
                        app.label in ['admin', 'auth', 'contenttypes', 'sessions']]
    
    # 检查迁移状态
    output = StringIO()
    call_command('showmigrations', stdout=output, no_color=True)
    migration_output = output.getvalue()
    
    print("📋 迁移状态概览:")
    print("-" * 60)
    
    # 解析迁移输出
    app_migrations = {}
    current_app = None
    
    for line in migration_output.split('\n'):
        line = line.strip()
        if not line:
            continue
        
        # 检查是否是应用名称
        if not line.startswith('[') and not line.startswith(' '):
            current_app = line
            app_migrations[current_app] = {'applied': [], 'pending': []}
        elif line.startswith('[X]'):
            # 已应用的迁移
            migration_name = line[3:].strip()
            if current_app:
                app_migrations[current_app]['applied'].append(migration_name)
        elif line.startswith('[ ]'):
            # 未应用的迁移
            migration_name = line[3:].strip()
            if current_app:
                app_migrations[current_app]['pending'].append(migration_name)
    
    # 统计信息
    total_apps = len([app for app in app_migrations.keys() if app_migrations[app]['applied'] or app_migrations[app]['pending']])
    apps_with_pending = [app for app in app_migrations.keys() if app_migrations[app]['pending']]
    
    print(f"总应用数: {total_apps}")
    print(f"有未应用迁移的应用数: {len(apps_with_pending)}")
    print()
    
    # 显示有未应用迁移的应用
    if apps_with_pending:
        print("⚠️  有未应用迁移的应用:")
        print("-" * 60)
        for app in apps_with_pending:
            pending_count = len(app_migrations[app]['pending'])
            applied_count = len(app_migrations[app]['applied'])
            print(f"  {app}:")
            print(f"    - 已应用: {applied_count}")
            print(f"    - 未应用: {pending_count}")
            if pending_count <= 5:
                for migration in app_migrations[app]['pending']:
                    print(f"      • {migration}")
            print()
    else:
        print("✅ 所有迁移都已应用")
        print()
    
    # 检查数据库中的迁移记录
    print("📊 数据库迁移记录检查:")
    print("-" * 60)
    cursor = connection.cursor()
    cursor.execute("""
        SELECT app, COUNT(*) as count 
        FROM django_migrations 
        GROUP BY app 
        ORDER BY app
    """)
    
    db_migrations = {}
    for row in cursor.fetchall():
        app, count = row
        db_migrations[app] = count
    
    print(f"数据库中的迁移记录数: {sum(db_migrations.values())}")
    print(f"涉及的应用数: {len(db_migrations)}")
    print()
    
    # 检查表是否存在
    print("🗄️  表存在性检查（部分关键表）:")
    print("-" * 60)
    
    key_tables = [
        'delivery_record',
        'delivery_file',
        'delivery_feedback',
        'delivery_tracking',
        'system_permission_item',
        'system_user',
        'system_role',
    ]
    
    cursor.execute("""
        SELECT table_name 
        FROM information_schema.tables 
        WHERE table_schema = 'public' 
        AND table_name IN %s
    """, (tuple(key_tables),))
    
    existing_tables = {row[0] for row in cursor.fetchall()}
    
    for table in key_tables:
        status = "✅" if table in existing_tables else "❌"
        print(f"  {status} {table}")
    
    print()
    
    # 检查迁移依赖问题
    print("🔗 迁移依赖检查:")
    print("-" * 60)
    print("提示: 运行 'python fix_migration_dependencies.py' 进行详细检查")
    print()
    
    # 总结
    print("=" * 60)
    print("检查完成")
    print("=" * 60)
    print()
    print("💡 建议:")
    if apps_with_pending:
        print("  1. 运行 'python manage.py migrate' 应用未应用的迁移")
    print("  2. 运行 'python fix_migration_dependencies.py' 检查迁移依赖")
    print("  3. 查看 'docs/系统迁移问题全面检查报告.md' 了解详细信息")
    print()

if __name__ == '__main__':
    try:
        check_migration_status()
    except Exception as e:
        print(f"❌ 检查过程中出现错误: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)

