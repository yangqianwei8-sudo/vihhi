#!/usr/bin/env python
"""
独立的迁移执行脚本
绕过Django迁移系统的依赖检查，直接执行SQL并标记迁移为已应用

使用方法:
    python scripts/run_migration_standalone.py <app_name> <migration_name> [选项]
    
示例:
    python scripts/run_migration_standalone.py delivery_customer 0001
    python scripts/run_migration_standalone.py customer_success 0020 --fake
    python scripts/run_migration_standalone.py delivery_customer 0001 --sql-only --output migration.sql
    
选项:
    --fake: 只标记迁移为已应用，不执行SQL
    --sql-only: 只生成SQL，不执行
    --output FILE: 指定SQL输出文件路径
    --force: 强制执行，即使迁移已应用
"""
import os
import sys
import argparse
from pathlib import Path

# 添加项目根目录到Python路径
BASE_DIR = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(BASE_DIR))

import django

# 设置Django环境
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'backend.config.settings')
django.setup()

from django.core.management import call_command


def main():
    parser = argparse.ArgumentParser(
        description='独立执行Django迁移，绕过依赖检查',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
示例:
  # 执行迁移
  python scripts/run_migration_standalone.py delivery_customer 0001
  
  # 只标记为已应用（不执行SQL）
  python scripts/run_migration_standalone.py delivery_customer 0001 --fake
  
  # 只生成SQL文件
  python scripts/run_migration_standalone.py delivery_customer 0001 --sql-only --output migration.sql
  
  # 强制执行（即使已应用）
  python scripts/run_migration_standalone.py delivery_customer 0001 --force
        """
    )
    
    parser.add_argument('app_name', help='应用名称（如 delivery_customer）')
    parser.add_argument('migration_name', help='迁移名称（如 0001_initial）')
    parser.add_argument('--fake', action='store_true', help='只标记迁移为已应用，不执行SQL')
    parser.add_argument('--sql-only', action='store_true', help='只生成SQL，不执行')
    parser.add_argument('--output', type=str, help='SQL输出文件路径')
    parser.add_argument('--force', action='store_true', help='强制执行，即使迁移已应用')
    
    args = parser.parse_args()
    
    # 构建命令参数
    cmd_args = [args.app_name, args.migration_name]
    cmd_options = {}
    
    if args.fake:
        cmd_options['fake'] = True
    if args.sql_only:
        cmd_options['sql_only'] = True
    if args.output:
        cmd_options['output'] = args.output
    if args.force:
        cmd_options['force'] = True
    
    # 调用Django管理命令
    try:
        call_command('migrate_standalone', *cmd_args, **cmd_options)
        sys.exit(0)
    except Exception as e:
        print(f'\n❌ 执行失败: {e}', file=sys.stderr)
        import traceback
        traceback.print_exc()
        sys.exit(1)


if __name__ == '__main__':
    main()

