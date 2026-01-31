#!/usr/bin/env python
"""
Django迁移优化脚本
提供迁移压缩、依赖检查、状态检查等功能
"""
import os
import sys
import argparse
import django

# 设置项目路径
script_dir = os.path.dirname(os.path.abspath(__file__))
project_root = os.path.dirname(script_dir)
sys.path.insert(0, project_root)

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'backend.config.settings')
django.setup()

from django.db import connection
from django.db.migrations.loader import MigrationLoader
from django.core.management import call_command
from django.utils import timezone


def check_migration_status():
    """检查迁移状态"""
    print("=" * 70)
    print("检查迁移状态")
    print("=" * 70)
    
    loader = MigrationLoader(connection)
    
    # 检查循环依赖
    try:
        loader.graph.ensure_not_cyclic()
        print("✓ 无循环依赖")
    except Exception as e:
        print(f"✗ 发现循环依赖: {e}")
        return False
    
    # 统计迁移状态
    total = 0
    applied = 0
    unapplied = 0
    squashed = 0
    
    for (app_label, migration_name), migration in loader.graph.nodes.items():
        total += 1
        if loader.applied_migrations.get((app_label, migration_name)):
            applied += 1
        else:
            unapplied += 1
        # 检查是否是压缩迁移
        if hasattr(migration, 'replaces') and migration.replaces:
            squashed += 1
    
    print(f"\n迁移统计:")
    print(f"  总迁移数: {total}")
    print(f"  已应用: {applied}")
    print(f"  未应用: {unapplied}")
    print(f"  压缩迁移: {squashed}")
    
    return True


def check_migration_dependencies():
    """检查迁移依赖关系"""
    print("=" * 70)
    print("检查迁移依赖关系")
    print("=" * 70)
    
    loader = MigrationLoader(connection)
    issues = []
    
    for (app_label, migration_name), migration in loader.graph.nodes.items():
        for dep_app, dep_name in migration.dependencies:
            if dep_app != app_label:
                # __first__ 是Django的特殊依赖标记，表示依赖应用的第一个迁移，这是正常的
                if dep_name == '__first__':
                    continue
                # 检查依赖的迁移是否存在
                if (dep_app, dep_name) not in loader.graph.nodes:
                    issues.append(f"{app_label}.{migration_name} 依赖不存在的迁移 {dep_app}.{dep_name}")
    
    if issues:
        print("✗ 发现依赖问题:")
        for issue in issues:
            print(f"  - {issue}")
        return False
    else:
        print("✓ 所有迁移依赖关系正确")
        return True


def list_squashable_apps():
    """列出可以压缩的应用"""
    print("=" * 70)
    print("查找可以压缩的应用")
    print("=" * 70)
    
    loader = MigrationLoader(connection)
    squashable = []
    
    app_migrations = {}
    for (app_label, migration_name), migration in loader.graph.nodes.items():
        if app_label not in app_migrations:
            app_migrations[app_label] = []
        app_migrations[app_label].append(migration_name)
    
    for app_label, migrations in app_migrations.items():
        # 过滤掉压缩迁移
        regular_migrations = [m for m in migrations if 'squashed' not in m]
        if len(regular_migrations) > 10:
            # 检查是否都已应用
            all_applied = all(
                loader.applied_migrations.get((app_label, m))
                for m in regular_migrations
            )
            if all_applied:
                squashable.append({
                    'app': app_label,
                    'count': len(regular_migrations),
                    'migrations': sorted(regular_migrations)[:5]  # 只显示前5个
                })
    
    if squashable:
        print("\n可以压缩的应用:")
        for item in squashable:
            print(f"\n  {item['app']}:")
            print(f"    迁移文件数: {item['count']}")
            print(f"    示例迁移: {', '.join(item['migrations'])}")
    else:
        print("\n未找到可以压缩的应用（迁移文件数>10且都已应用）")
    
    return squashable


def squash_migrations(app_label, start, end):
    """压缩迁移"""
    print("=" * 70)
    print(f"压缩迁移: {app_label} ({start} - {end})")
    print("=" * 70)
    
    try:
        call_command('squashmigrations', app_label, start, end, verbosity=2)
        print(f"\n✓ 成功压缩 {app_label} 的迁移")
        return True
    except Exception as e:
        print(f"\n✗ 压缩失败: {e}")
        return False


def optimize_migration(app_label, migration_name):
    """优化单个迁移"""
    print("=" * 70)
    print(f"优化迁移: {app_label}.{migration_name}")
    print("=" * 70)
    
    try:
        call_command('optimizemigration', app_label, migration_name, verbosity=2)
        print(f"\n✓ 成功优化 {app_label}.{migration_name}")
        return True
    except Exception as e:
        print(f"\n✗ 优化失败: {e}")
        return False


def main():
    parser = argparse.ArgumentParser(description='Django迁移优化工具')
    parser.add_argument('action', choices=['check', 'dependencies', 'list-squashable', 'squash', 'optimize'],
                       help='操作类型')
    parser.add_argument('--app', help='应用名称（用于squash和optimize）')
    parser.add_argument('--start', help='起始迁移（用于squash）')
    parser.add_argument('--end', help='结束迁移（用于squash）')
    parser.add_argument('--migration', help='迁移名称（用于optimize）')
    
    args = parser.parse_args()
    
    if args.action == 'check':
        check_migration_status()
    elif args.action == 'dependencies':
        check_migration_dependencies()
    elif args.action == 'list-squashable':
        list_squashable_apps()
    elif args.action == 'squash':
        if not all([args.app, args.start, args.end]):
            print("错误: squash操作需要 --app, --start, --end 参数")
            sys.exit(1)
        squash_migrations(args.app, args.start, args.end)
    elif args.action == 'optimize':
        if not all([args.app, args.migration]):
            print("错误: optimize操作需要 --app, --migration 参数")
            sys.exit(1)
        optimize_migration(args.app, args.migration)


if __name__ == '__main__':
    main()

