#!/usr/bin/env python
"""
直接执行SQL添加模板文件字段到业务委托书模板表
"""
import os
import sys

# 添加项目根目录到Python路径
script_dir = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, script_dir)

import django

# 设置Django环境
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'backend.config.settings')
django.setup()

from django.db import connection

def execute_sql():
    """执行SQL添加字段"""
    cursor = connection.cursor()
    
    try:
        # 检查字段是否已存在
        cursor.execute("""
            SELECT column_name 
            FROM information_schema.columns 
            WHERE table_name = 'business_authorization_letter_template' 
            AND column_name = 'template_file'
        """)
        
        if cursor.fetchone():
            print("✓ 字段 template_file 已存在，跳过")
        else:
            print("正在添加 template_file 字段...")
            cursor.execute("""
                ALTER TABLE "business_authorization_letter_template" 
                ADD COLUMN "template_file" varchar(500) NULL;
            """)
            print("✓ 添加 template_file 字段成功")
        
        # 检查 template_file_name 字段
        cursor.execute("""
            SELECT column_name 
            FROM information_schema.columns 
            WHERE table_name = 'business_authorization_letter_template' 
            AND column_name = 'template_file_name'
        """)
        
        if cursor.fetchone():
            print("✓ 字段 template_file_name 已存在，跳过")
        else:
            print("正在添加 template_file_name 字段...")
            cursor.execute("""
                ALTER TABLE "business_authorization_letter_template" 
                ADD COLUMN "template_file_name" varchar(255) NOT NULL DEFAULT '';
            """)
            print("✓ 添加 template_file_name 字段成功")
        
        # 检查 template_file_size 字段
        cursor.execute("""
            SELECT column_name 
            FROM information_schema.columns 
            WHERE table_name = 'business_authorization_letter_template' 
            AND column_name = 'template_file_size'
        """)
        
        if cursor.fetchone():
            print("✓ 字段 template_file_size 已存在，跳过")
        else:
            print("正在添加 template_file_size 字段...")
            cursor.execute("""
                ALTER TABLE "business_authorization_letter_template" 
                ADD COLUMN "template_file_size" bigint NULL;
            """)
            print("✓ 添加 template_file_size 字段成功")
        
        # 提交事务
        connection.commit()
        print("\n✓ 所有操作完成！")
        
    except Exception as e:
        connection.rollback()
        print(f"\n✗ 添加字段失败: {e}")
        import traceback
        traceback.print_exc()
        return False
    
    return True

if __name__ == '__main__':
    print("=" * 60)
    print("添加模板文件字段脚本")
    print("=" * 60)
    success = execute_sql()
    if success:
        print("\n✓ 脚本执行成功！")
        sys.exit(0)
    else:
        print("\n✗ 脚本执行失败！")
        sys.exit(1)

