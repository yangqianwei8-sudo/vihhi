#!/usr/bin/env python
"""
客户管理模块数据库迁移执行脚本
直接执行SQL来创建表，绕过Django迁移系统的依赖问题
"""
import os
import sys

# 添加项目根目录到Python路径
script_dir = os.path.dirname(os.path.abspath(__file__))
# 从 backend/apps/customer_success/execute_migration.py 到项目根目录
project_root = os.path.abspath(os.path.join(script_dir, '../../../..'))
if project_root not in sys.path:
    sys.path.insert(0, project_root)
os.chdir(project_root)

import django

# 设置Django环境
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'backend.config.settings')
django.setup()

from django.db import connection

def execute_sql_file(sql_file_path):
    """执行SQL文件"""
    with open(sql_file_path, 'r', encoding='utf-8') as f:
        sql_content = f.read()
    
    # 移除注释和BEGIN/COMMIT
    sql_lines = []
    for line in sql_content.split('\n'):
        line = line.strip()
        # 跳过注释和空行
        if line and not line.startswith('--'):
            # 跳过BEGIN和COMMIT
            if line.upper() not in ['BEGIN', 'COMMIT']:
                sql_lines.append(line)
    
    # 按分号分割SQL语句
    sql_statements = []
    current_statement = []
    for line in sql_lines:
        current_statement.append(line)
        if line.endswith(';'):
            sql_statements.append(' '.join(current_statement))
            current_statement = []
    
    # 执行每个SQL语句
    cursor = connection.cursor()
    success_count = 0
    error_count = 0
    skipped_count = 0
    
    print(f"\n开始执行 {len(sql_statements)} 条SQL语句...\n")
    
    for i, sql in enumerate(sql_statements, 1):
        if sql.strip():
            try:
                cursor.execute(sql)
                success_count += 1
                if i % 10 == 0:
                    print(f"  已执行 {i}/{len(sql_statements)} 条SQL...")
            except Exception as e:
                error_msg = str(e).lower()
                # 如果是表已存在的错误，忽略
                if 'already exists' in error_msg or 'duplicate' in error_msg or 'relation' in error_msg and 'already exists' in error_msg:
                    skipped_count += 1
                    if i % 10 == 0:
                        print(f"  已处理 {i}/{len(sql_statements)} 条SQL（跳过已存在的对象）...")
                else:
                    error_count += 1
                    print(f"  ❌ SQL执行失败 ({i}/{len(sql_statements)}): {sql[:80]}...")
                    print(f"     错误: {e}")
    
    # 提交事务
    try:
        connection.commit()
        print(f"\n✅ 迁移完成！")
        print(f"   成功: {success_count}")
        print(f"   跳过（已存在）: {skipped_count}")
        print(f"   失败: {error_count}")
        return error_count == 0
    except Exception as e:
        connection.rollback()
        print(f"\n❌ 提交失败: {e}")
        return False

def check_tables():
    """检查表是否创建成功"""
    cursor = connection.cursor()
    cursor.execute("""
        SELECT table_name 
        FROM information_schema.tables 
        WHERE table_schema = 'public' 
        AND (table_name LIKE 'customer_%' OR table_name LIKE 'business_%')
        AND table_name NOT LIKE 'customer_lead%'
        ORDER BY table_name
    """)
    tables = [row[0] for row in cursor.fetchall()]
    return tables

if __name__ == '__main__':
    # 获取SQL文件路径
    script_dir = os.path.dirname(os.path.abspath(__file__))
    sql_file = os.path.join(script_dir, 'migrations', '0018_migration.sql')
    
    if not os.path.exists(sql_file):
        print(f"❌ SQL文件不存在: {sql_file}")
        sys.exit(1)
    
    print("=" * 60)
    print("客户管理模块数据库迁移")
    print("=" * 60)
    print(f"📄 SQL文件: {sql_file}\n")
    
    # 检查现有表
    existing_tables = check_tables()
    if existing_tables:
        print(f"⚠️  发现已存在的相关表: {len(existing_tables)} 个")
        print("   继续执行将跳过已存在的对象...\n")
    
    # 执行SQL
    success = execute_sql_file(sql_file)
    
    # 检查结果
    print("\n📊 检查创建的表...")
    tables = check_tables()
    expected_tables = [
        'customer_client',
        'customer_contact',
        'customer_contact_education',
        'customer_contact_work_experience',
        'customer_contact_job_change',
        'customer_contact_cooperation',
        'customer_contact_tracking',
        'customer_relationship',
        'customer_relationship_upgrade',
        'customer_client_project',
    ]
    
    if tables:
        print(f"✅ 已创建/存在的表: {len(tables)} 个")
        for table in expected_tables:
            if table in tables:
                print(f"  ✓ {table}")
            else:
                print(f"  ✗ {table} (缺失)")
    else:
        print("❌ 未找到任何表")
    
    if success:
        print("\n🎉 迁移成功完成！")
        print("\n下一步：")
        print("1. 标记迁移为已应用: python manage.py migrate customer_success 0018 --fake")
        print("2. 运行权限初始化: python manage.py seed_permissions")
        sys.exit(0)
    else:
        print("\n⚠️  迁移可能未完全成功，请检查错误信息")
        sys.exit(1)

