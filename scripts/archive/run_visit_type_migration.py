#!/usr/bin/env python
"""
直接执行SQL添加拜访类型字段
绕过Django迁移系统的依赖问题
"""
import os
import sys

# 添加项目根目录到Python路径
script_dir = os.path.dirname(os.path.abspath(__file__))
project_root = os.path.abspath(os.path.join(script_dir, '../../../'))
sys.path.insert(0, project_root)

import django

# 设置Django环境
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'backend.config.settings')
django.setup()

from django.db import connection
from django.core.management import call_command

def execute_migration():
    """执行迁移"""
    cursor = connection.cursor()
    
    print("=" * 60)
    print("开始添加拜访类型字段...")
    print("=" * 60)
    
    # SQL语句
    sql_statements = [
        # 添加visit_type字段
        """
        ALTER TABLE customer_relationship 
        ADD COLUMN IF NOT EXISTS visit_type VARCHAR(20) 
        CHECK (visit_type IN ('cooperation', 'contract', 'settlement', 'payment', 'production', 'other') OR visit_type IS NULL);
        """,
        
        # 添加注释
        """
        COMMENT ON COLUMN customer_relationship.visit_type IS '拜访类型：仅当记录类型为拜访记录时使用';
        """,
    ]
    
    success_count = 0
    error_count = 0
    
    for sql in sql_statements:
        sql_clean = ' '.join(sql.split())
        if not sql_clean:
            continue
            
        try:
            cursor.execute(sql_clean)
            success_count += 1
            print(f"✅ 执行成功")
        except Exception as e:
            error_msg = str(e).lower()
            # 如果是字段已存在的错误，忽略
            if 'already exists' in error_msg or 'duplicate' in error_msg or 'column' in error_msg and 'already' in error_msg:
                print(f"⚠️  字段已存在，跳过")
                success_count += 1
                error_count -= 1
            else:
                error_count += 1
                print(f"❌ 执行失败: {e}")
                print(f"   SQL: {sql_clean[:100]}...")
    
    # 提交事务
    try:
        connection.commit()
        print(f"\n{'=' * 60}")
        print(f"✅ 迁移完成！成功: {success_count}, 失败: {error_count}")
        print(f"{'=' * 60}")
    except Exception as e:
        connection.rollback()
        print(f"\n❌ 提交失败: {e}")
        return False
    
    # 标记迁移为已应用
    if error_count == 0:
        try:
            print("\n正在标记迁移为已应用...")
            call_command('migrate', 'customer_success', '0029', '--fake', verbosity=0)
            print("✅ 迁移已标记为已应用")
        except Exception as e:
            print(f"⚠️  标记迁移失败（不影响功能）: {e}")
            print("   您可以稍后手动运行: python manage.py migrate customer_success 0029 --fake")
    
    return error_count == 0

def check_field():
    """检查字段是否添加成功"""
    cursor = connection.cursor()
    
    # 检查visit_type字段
    cursor.execute("""
        SELECT column_name, data_type, is_nullable
        FROM information_schema.columns 
        WHERE table_schema = 'public' 
        AND table_name = 'customer_relationship'
        AND column_name = 'visit_type'
    """)
    field_info = cursor.fetchone()
    
    return field_info is not None

if __name__ == '__main__':
    print("开始添加拜访类型字段...\n")
    
    # 执行迁移
    success = execute_migration()
    
    if success:
        # 检查字段
        print("\n检查迁移结果...")
        field_exists = check_field()
        
        if field_exists:
            print("✅ visit_type 字段已添加")
        else:
            print("❌ visit_type 字段未添加")
        
        print("\n✅ 迁移完成！")
    else:
        print("\n❌ 迁移失败，请检查错误信息")
        sys.exit(1)

