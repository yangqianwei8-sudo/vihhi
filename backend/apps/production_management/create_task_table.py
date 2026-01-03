#!/usr/bin/env python
"""
直接执行SQL创建生产管理模块的项目任务表
绕过Django迁移系统的依赖问题
"""
import os
import sys
from urllib.parse import urlparse

# 添加项目根目录到Python路径
script_dir = os.path.dirname(os.path.abspath(__file__))
project_root = os.path.abspath(os.path.join(script_dir, '../../../'))
sys.path.insert(0, project_root)

# 使用 psycopg2 直接连接数据库
try:
    import psycopg2
    from psycopg2.extensions import ISOLATION_LEVEL_AUTOCOMMIT
except ImportError:
    print("❌ 需要安装 psycopg2: pip install psycopg2-binary")
    sys.exit(1)

# 从环境变量或默认值获取数据库连接信息
database_url = os.getenv('DATABASE_URL', '').strip()
if not database_url:
    # 使用默认开发数据库
    database_url = "postgresql://postgres:zdg7xx28@dbconn.sealosbja.site:38013/postgres"

# 解析数据库URL
parsed = urlparse(database_url)
db_config = {
    'host': parsed.hostname,
    'port': parsed.port or 5432,
    'database': parsed.path.lstrip('/').split('?')[0],
    'user': parsed.username,
    'password': parsed.password,
}

def execute_sql_file(sql_file_path, db_config):
    """执行SQL文件"""
    # 连接数据库
    conn = psycopg2.connect(**db_config)
    conn.set_isolation_level(ISOLATION_LEVEL_AUTOCOMMIT)
    cursor = conn.cursor()
    
    try:
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
        
        # 按分号分割SQL语句（但保留DO块）
        sql_statements = []
        current_statement = []
        in_do_block = False
        
        for line in sql_lines:
            current_statement.append(line)
            
            # 检测DO块开始
            if 'DO $$' in line.upper():
                in_do_block = True
            
            # 检测DO块结束
            if in_do_block and 'END $$;' in line:
                in_do_block = False
                sql_statements.append(' '.join(current_statement))
                current_statement = []
            elif not in_do_block and line.endswith(';'):
                sql_statements.append(' '.join(current_statement))
                current_statement = []
        
        # 执行每个SQL语句
        success_count = 0
        error_count = 0
        
        for sql in sql_statements:
            if sql.strip():
                try:
                    cursor.execute(sql)
                    success_count += 1
                    print(f"✅ 执行成功: {sql[:50]}...")
                except Exception as e:
                    # 如果是表已存在的错误，忽略
                    if 'already exists' in str(e).lower() or 'duplicate' in str(e).lower():
                        print(f"⚠️  已存在，跳过: {sql[:50]}...")
                        success_count += 1
                    else:
                        error_count += 1
                        print(f"❌ 执行失败: {sql[:50]}...")
                        print(f"   错误信息: {str(e)}")
        
        return error_count == 0
    finally:
        cursor.close()
        conn.close()

def check_table(db_config):
    """检查表是否创建成功"""
    conn = psycopg2.connect(**db_config)
    cursor = conn.cursor()
    try:
        cursor.execute("""
            SELECT table_name 
            FROM information_schema.tables 
            WHERE table_schema = 'public' 
            AND table_name = 'production_management_task'
        """)
        result = cursor.fetchone()
        return result is not None
    finally:
        cursor.close()
        conn.close()

if __name__ == '__main__':
    # 获取SQL文件路径
    script_dir = os.path.dirname(os.path.abspath(__file__))
    sql_file = os.path.join(script_dir, 'migrations', 'create_task_table.sql')
    
    if not os.path.exists(sql_file):
        print(f"❌ SQL文件不存在: {sql_file}")
        sys.exit(1)
    
    print("🚀 开始创建生产管理模块的项目任务表...")
    print(f"📄 SQL文件: {sql_file}")
    print(f"📊 数据库: {db_config['host']}:{db_config['port']}/{db_config['database']}\n")
    
    # 检查现有表
    if check_table(db_config):
        print("⚠️  表 production_management_task 已存在")
        response = input("是否继续（将尝试添加缺失的索引和外键）？(y/n): ")
        if response.lower() != 'y':
            print("已取消")
            sys.exit(0)
    
    # 执行SQL
    success = execute_sql_file(sql_file, db_config)
    
    # 检查结果
    print("\n📊 检查创建的表...")
    if check_table(db_config):
        print("✅ 表 production_management_task 已创建")
        
        # 检查索引
        conn = psycopg2.connect(**db_config)
        cursor = conn.cursor()
        try:
            cursor.execute("""
                SELECT indexname 
                FROM pg_indexes 
                WHERE tablename = 'production_management_task'
            """)
            indexes = [row[0] for row in cursor.fetchall()]
            print(f"📋 已创建的索引: {', '.join(indexes) if indexes else '无'}")
        finally:
            cursor.close()
            conn.close()
        
        print("\n🎉 迁移成功完成！")
        sys.exit(0)
    else:
        print("❌ 表创建失败，请检查错误信息")
        sys.exit(1)

