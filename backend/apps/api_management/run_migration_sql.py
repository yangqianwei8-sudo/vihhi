#!/usr/bin/env python
"""
直接执行SQL创建API管理模块的表
绕过Django迁移系统的依赖问题
"""
import os
import sys

# 添加项目根目录到Python路径
script_dir = os.path.dirname(os.path.abspath(__file__))
# 从 backend/apps/api_management/run_migration_sql.py 到项目根目录
project_root = os.path.abspath(os.path.join(script_dir, '../../../../'))
if project_root not in sys.path:
    sys.path.insert(0, project_root)

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
    in_comment = False
    for line in sql_content.split('\n'):
        line = line.strip()
        # 跳过空行
        if not line:
            continue
        # 跳过单行注释
        if line.startswith('--'):
            continue
        # 跳过BEGIN和COMMIT
        if line.upper() in ['BEGIN', 'COMMIT']:
            continue
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
    
    for sql in sql_statements:
        if sql.strip():
            try:
                cursor.execute(sql)
                success_count += 1
                # 只显示表名，不显示完整SQL
                if 'CREATE TABLE' in sql.upper():
                    table_name = sql.split('(')[0].split()[-1] if '(' in sql else 'unknown'
                    print(f"✅ 创建表: {table_name}")
                elif 'CREATE INDEX' in sql.upper():
                    index_name = sql.split()[2] if len(sql.split()) > 2 else 'unknown'
                    print(f"✅ 创建索引: {index_name}")
                elif 'INSERT INTO' in sql.upper():
                    print(f"✅ 插入迁移记录")
            except Exception as e:
                error_count += 1
                # 如果是表已存在的错误，忽略
                error_msg = str(e).lower()
                if 'already exists' in error_msg or 'duplicate' in error_msg or 'already exists' in error_msg:
                    if 'CREATE TABLE' in sql.upper():
                        table_name = sql.split('(')[0].split()[-1] if '(' in sql else 'unknown'
                        print(f"⚠️  表已存在，跳过: {table_name}")
                    elif 'CREATE INDEX' in sql.upper():
                        print(f"⚠️  索引已存在，跳过")
                    else:
                        print(f"⚠️  已存在，跳过")
                    success_count += 1
                    error_count -= 1
                else:
                    print(f"❌ 执行失败")
                    print(f"   错误: {e}")
                    print(f"   SQL: {sql[:100]}...")
    
    # 提交事务
    try:
        connection.commit()
        print(f"\n✅ 迁移完成！成功: {success_count}, 失败: {error_count}")
    except Exception as e:
        connection.rollback()
        print(f"\n❌ 提交失败: {e}")
        return False
    
    return error_count == 0

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

if __name__ == '__main__':
    # 获取SQL文件路径
    script_dir = os.path.dirname(os.path.abspath(__file__))
    sql_file = os.path.join(script_dir, 'migrations', 'create_tables.sql')
    
    if not os.path.exists(sql_file):
        print(f"❌ SQL文件不存在: {sql_file}")
        sys.exit(1)
    
    print("🚀 开始创建API管理模块的数据库表...")
    print(f"📄 SQL文件: {sql_file}\n")
    
    # 检查现有表
    existing_tables = check_tables()
    if existing_tables:
        print(f"⚠️  发现已存在的表: {', '.join(existing_tables)}")
        response = input("是否继续？(y/n): ")
        if response.lower() != 'y':
            print("已取消")
            sys.exit(0)
    
    # 执行SQL
    success = execute_sql_file(sql_file)
    
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
    
    if success and len(tables) >= len(expected_tables):
        print("\n🎉 迁移成功完成！")
        print("\n📝 下一步：")
        print("  1. 访问 Django 后台管理: /admin/")
        print("  2. 在 'API接口管理' 模块下添加外部系统和API接口")
        sys.exit(0)
    else:
        print("\n⚠️  迁移可能未完全成功，请检查错误信息")
        sys.exit(1)
