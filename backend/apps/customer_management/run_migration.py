#!/usr/bin/env python
"""
客户管理模块数据库迁移脚本
由于系统存在依赖问题，直接执行SQL来创建表
"""

import os
import sys
import django

# 设置Django环境
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))))
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'backend.config.settings')
django.setup()

from django.db import connection
from django.core.management import call_command
import subprocess

def execute_sql(sql):
    """执行SQL语句"""
    with connection.cursor() as cursor:
        try:
            cursor.execute(sql)
            connection.commit()
            print(f"✓ SQL执行成功")
            return True
        except Exception as e:
            connection.rollback()
            print(f"✗ SQL执行失败: {str(e)}")
            return False

def main():
    """主函数"""
    print("=" * 60)
    print("客户管理模块数据库迁移")
    print("=" * 60)
    
    # 方法1：尝试使用Django migrate命令
    print("\n[方法1] 尝试使用Django migrate命令...")
    try:
        result = subprocess.run(
            ['python', 'manage.py', 'migrate', 'customer_success'],
            cwd=os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))),
            capture_output=True,
            text=True,
            timeout=60
        )
        if result.returncode == 0:
            print("✓ Django migrate命令执行成功")
            print(result.stdout)
            return
        else:
            print("✗ Django migrate命令执行失败（这是预期的，由于依赖问题）")
            print("错误信息:", result.stderr[:500])
    except Exception as e:
        print(f"✗ 执行失败: {str(e)}")
    
    # 方法2：生成SQL并提示手动执行
    print("\n[方法2] 生成迁移SQL...")
    try:
        result = subprocess.run(
            ['python', 'manage.py', 'sqlmigrate', 'customer_success', '0018'],
            cwd=os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))),
            capture_output=True,
            text=True,
            timeout=60
        )
        if result.returncode == 0:
            sql_content = result.stdout
            print("✓ SQL生成成功")
            print("\n生成的SQL已保存，请查看以下文件或手动执行：")
            print("1. 运行: python manage.py sqlmigrate customer_success 0018")
            print("2. 将输出保存到文件并手动执行")
            
            # 保存SQL到文件
            sql_file = os.path.join(os.path.dirname(__file__), 'migrations', '0018_migration.sql')
            os.makedirs(os.path.dirname(sql_file), exist_ok=True)
            with open(sql_file, 'w', encoding='utf-8') as f:
                f.write(sql_content)
            print(f"3. SQL已保存到: {sql_file}")
        else:
            print("✗ SQL生成失败")
            print("错误信息:", result.stderr[:500])
    except Exception as e:
        print(f"✗ 执行失败: {str(e)}")
    
    print("\n" + "=" * 60)
    print("迁移说明：")
    print("1. 由于系统依赖问题，建议直接执行SQL")
    print("2. 或者先解决permission_management的依赖问题")
    print("3. 然后运行: python manage.py migrate customer_success")
    print("=" * 60)

if __name__ == '__main__':
    main()

