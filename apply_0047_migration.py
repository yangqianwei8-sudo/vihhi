#!/usr/bin/env python
"""
执行合同洽谈记录迁移脚本
迁移编号：0047_add_contract_negotiation
"""

import os
import sys
import django

# 设置Django环境
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'backend.config.settings')
django.setup()

from django.db import connection

def apply_migration():
    """执行迁移SQL"""
    sql_file = os.path.join(
        os.path.dirname(__file__),
        'backend/apps/customer_management/migrations/0047_add_contract_negotiation.sql'
    )
    
    if not os.path.exists(sql_file):
        print(f"错误：找不到SQL文件 {sql_file}")
        return False
    
    print(f"读取SQL文件: {sql_file}")
    with open(sql_file, 'r', encoding='utf-8') as f:
        sql_content = f.read()
    
    # 移除注释和空行，分割SQL语句
    sql_statements = []
    current_statement = []
    
    for line in sql_content.split('\n'):
        line = line.strip()
        # 跳过注释和空行
        if line.startswith('--') or not line:
            continue
        current_statement.append(line)
        # 如果行以分号结尾，表示一个完整的SQL语句
        if line.endswith(';'):
            sql_statements.append(' '.join(current_statement))
            current_statement = []
    
    # 执行SQL语句
    print(f"准备执行 {len(sql_statements)} 条SQL语句...")
    
    try:
        with connection.cursor() as cursor:
            for i, sql in enumerate(sql_statements, 1):
                if sql.strip():
                    print(f"执行SQL {i}/{len(sql_statements)}: {sql[:50]}...")
                    try:
                        cursor.execute(sql)
                        print(f"  ✓ 成功")
                    except Exception as e:
                        # 如果表已存在或其他非致命错误，继续执行
                        if 'already exists' in str(e).lower() or 'duplicate' in str(e).lower():
                            print(f"  ⚠ 跳过（已存在）: {str(e)[:100]}")
                        else:
                            print(f"  ✗ 错误: {str(e)}")
                            raise
        
        # 提交事务
        connection.commit()
        print("\n✅ 迁移执行成功！")
        return True
        
    except Exception as e:
        print(f"\n❌ 迁移执行失败: {str(e)}")
        connection.rollback()
        return False

if __name__ == '__main__':
    print("=" * 60)
    print("合同洽谈记录迁移脚本")
    print("迁移编号：0047_add_contract_negotiation")
    print("=" * 60)
    print()
    
    # 检查数据库连接
    try:
        with connection.cursor() as cursor:
            cursor.execute("SELECT version();")
            db_version = cursor.fetchone()[0]
            print(f"数据库连接成功: {db_version[:50]}...")
    except Exception as e:
        print(f"❌ 数据库连接失败: {str(e)}")
        print("\n请检查数据库配置：")
        print("1. 确保数据库服务正在运行")
        print("2. 检查 DATABASE_URL 环境变量")
        print("3. 检查 backend/config/settings.py 中的数据库配置")
        sys.exit(1)
    
    print()
    
    # 执行迁移
    success = apply_migration()
    
    if success:
        print("\n" + "=" * 60)
        print("迁移完成！")
        print("=" * 60)
        print("\n下一步：")
        print("1. 验证表是否创建成功")
        print("2. 测试合同洽谈记录功能")
        print("3. 访问 /business/contracts/negotiation/ 查看列表")
        sys.exit(0)
    else:
        print("\n" + "=" * 60)
        print("迁移失败，请检查错误信息")
        print("=" * 60)
        sys.exit(1)

