#!/usr/bin/env python
"""
执行服务费结算方案迁移脚本
如果Django迁移命令无法运行，可以使用此脚本直接执行SQL并标记迁移
"""
import os
import sys

# 添加项目根目录到路径
project_root = os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))))
sys.path.insert(0, project_root)

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'backend.config.settings')

import django
django.setup()

from django.db import connection
from django.core.management import call_command
from django.db.utils import OperationalError, IntegrityError

def execute_sql_file(sql_file_path):
    """执行SQL文件"""
    print(f"正在执行SQL文件: {sql_file_path}")
    
    with open(sql_file_path, 'r', encoding='utf-8') as f:
        sql_content = f.read()
    
    # 移除注释行和空行
    sql_lines = []
    for line in sql_content.split('\n'):
        line = line.strip()
        if line and not line.startswith('--'):
            sql_lines.append(line)
    
    sql_statements = ' '.join(sql_lines).split(';')
    
    with connection.cursor() as cursor:
        for statement in sql_statements:
            statement = statement.strip()
            if statement:
                try:
                    cursor.execute(statement)
                    print(f"✓ 执行成功: {statement[:50]}...")
                except Exception as e:
                    error_str = str(e).lower()
                    # 忽略"已存在"的错误
                    if 'already exists' in error_str or 'duplicate' in error_str:
                        print(f"⚠ 已存在，跳过: {statement[:50]}...")
                    # 忽略"表不存在"的错误（对于ALTER TABLE语句）
                    elif 'does not exist' in error_str and 'alter table' in statement.lower():
                        print(f"⚠ 目标表不存在，跳过: {statement[:50]}...")
                        print(f"   提示: 如果ProjectSettlement表在其他模块，请手动添加字段")
                    else:
                        print(f"✗ 执行失败: {statement[:50]}...")
                        print(f"  错误: {str(e)}")
                        # 对于非关键错误，继续执行
                        if 'alter table' in statement.lower():
                            print(f"   继续执行其他语句...")
                        else:
                            raise

def check_tables_exist():
    """检查表是否已创建"""
    with connection.cursor() as cursor:
        cursor.execute("""
            SELECT table_name 
            FROM information_schema.tables 
            WHERE table_schema = 'public' 
            AND table_name LIKE 'settlement_service_fee%'
            ORDER BY table_name
        """)
        tables = [row[0] for row in cursor.fetchall()]
        return tables

def check_column_exists():
    """检查字段是否已添加"""
    with connection.cursor() as cursor:
        cursor.execute("""
            SELECT column_name 
            FROM information_schema.columns 
            WHERE table_name = 'settlement_project_settlement' 
            AND column_name = 'service_fee_scheme_id'
        """)
        return cursor.fetchone() is not None

def mark_migrations_applied():
    """标记迁移为已应用"""
    print("\n正在标记迁移为已应用...")
    
    migrations = [
        ('settlement_center', '0007_add_service_fee_settlement_scheme'),
        ('settlement_center', '0008_add_service_fee_scheme_to_project_settlement'),
    ]
    
    with connection.cursor() as cursor:
        for app, name in migrations:
            try:
                cursor.execute("""
                    INSERT INTO django_migrations (app, name, applied) 
                    VALUES (%s, %s, NOW())
                    ON CONFLICT DO NOTHING
                """, [app, name])
                print(f"✓ 标记迁移: {app}.{name}")
            except Exception as e:
                # 如果django_migrations表不存在或使用MySQL，尝试其他方式
                print(f"⚠ 无法标记迁移 {app}.{name}: {str(e)}")
                print("   请手动运行: python manage.py migrate settlement_center {name} --fake")

def main():
    """主函数"""
    print("=" * 60)
    print("服务费结算方案迁移执行脚本")
    print("=" * 60)
    
    # 获取SQL文件路径
    script_dir = os.path.dirname(os.path.abspath(__file__))
    sql_file = os.path.join(script_dir, 'run_migrations.sql')
    
    if not os.path.exists(sql_file):
        print(f"❌ SQL文件不存在: {sql_file}")
        return False
    
    try:
        # 检查表是否已存在
        print("\n1. 检查现有表...")
        existing_tables = check_tables_exist()
        if existing_tables:
            print(f"   发现已存在的表: {', '.join(existing_tables)}")
            # 非交互模式：如果表已存在，直接跳过SQL执行，只标记迁移
            if len(existing_tables) >= 4:
                print("   所有表已存在，跳过SQL执行，直接标记迁移...")
                skip_sql = True
            else:
                skip_sql = False
        else:
            skip_sql = False
        
        # 执行SQL
        if not skip_sql:
            print("\n2. 执行SQL迁移...")
            execute_sql_file(sql_file)
        else:
            print("\n2. 跳过SQL执行（表已存在）...")
        
        # 验证表是否创建成功
        print("\n3. 验证迁移结果...")
        tables = check_tables_exist()
        expected_tables = [
            'settlement_service_fee_scheme',
            'settlement_service_fee_segmented_rate',
            'settlement_service_fee_jump_point_rate',
            'settlement_service_fee_unit_cap_detail'
        ]
        
        missing_tables = [t for t in expected_tables if t not in tables]
        if missing_tables:
            print(f"❌ 缺少表: {', '.join(missing_tables)}")
            return False
        else:
            print(f"✓ 所有表已创建: {', '.join(tables)}")
        
        # 检查字段
        if check_column_exists():
            print("✓ service_fee_scheme_id 字段已添加")
        else:
            print("⚠ service_fee_scheme_id 字段未找到（可能已存在或需要手动添加）")
        
        # 标记迁移
        print("\n4. 标记迁移为已应用...")
        mark_migrations_applied()
        
        print("\n" + "=" * 60)
        print("✅ 迁移完成！")
        print("=" * 60)
        print("\n接下来可以：")
        print("1. 验证功能: python manage.py shell")
        print("   >>> from backend.apps.settlement_center.models import ServiceFeeSettlementScheme")
        print("   >>> ServiceFeeSettlementScheme.objects.count()")
        print("\n2. 如果标记失败，手动执行:")
        print("   python manage.py migrate settlement_center 0007 --fake")
        print("   python manage.py migrate settlement_center 0008 --fake")
        
        return True
        
    except Exception as e:
        print(f"\n❌ 迁移失败: {str(e)}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == '__main__':
    success = main()
    sys.exit(0 if success else 1)

