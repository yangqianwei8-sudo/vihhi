#!/usr/bin/env python
"""
直接删除业务委托书服务内容字段的脚本
绕过Django迁移系统的依赖问题
"""
import os
import sys
import django

# 设置Django环境
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'backend.config.settings')
django.setup()

from django.db import connection

def remove_service_content_fields():
    """删除业务委托书表中的服务内容字段"""
    with connection.cursor() as cursor:
        # 获取实际的表名
        from backend.apps.customer_management.models import AuthorizationLetter
        table_name = AuthorizationLetter._meta.db_table
        print(f"表名: {table_name}")
        
        # 检查表是否存在
        cursor.execute("""
            SELECT EXISTS (
                SELECT FROM information_schema.tables 
                WHERE table_schema = 'public' 
                AND table_name = %s
            );
        """, [table_name])
        table_exists = cursor.fetchone()[0]
        
        if not table_exists:
            print(f"表 {table_name} 不存在，跳过删除操作")
            return
        
        # 检查字段是否存在并删除
        fields_to_remove = ['drawing_stage_id', 'service_types', 'service_professions']
        
        for field in fields_to_remove:
            # 检查字段是否存在
            cursor.execute("""
                SELECT EXISTS (
                    SELECT FROM information_schema.columns 
                    WHERE table_schema = 'public' 
                    AND table_name = %s
                    AND column_name = %s
                );
            """, [table_name, field])
            
            field_exists = cursor.fetchone()[0]
            
            if field_exists:
                try:
                    if field == 'drawing_stage_id':
                        # 查找并删除外键约束
                        cursor.execute("""
                            SELECT constraint_name 
                            FROM information_schema.table_constraints 
                            WHERE table_schema = 'public' 
                            AND table_name = %s 
                            AND constraint_type = 'FOREIGN KEY'
                            AND constraint_name LIKE %s
                        """, [table_name, f'%{field}%'])
                        
                        constraint = cursor.fetchone()
                        if constraint:
                            constraint_name = constraint[0]
                            cursor.execute(f"""
                                ALTER TABLE {table_name} 
                                DROP CONSTRAINT IF EXISTS {constraint_name};
                            """)
                            print(f"✓ 已删除外键约束: {constraint_name}")
                    
                    # 删除字段
                    cursor.execute(f"""
                        ALTER TABLE {table_name} 
                        DROP COLUMN IF EXISTS {field};
                    """)
                    print(f"✓ 已删除字段: {field}")
                except Exception as e:
                    print(f"✗ 删除字段 {field} 时出错: {e}")
            else:
                print(f"○ 字段 {field} 不存在，跳过")
        
        print("\n所有字段删除操作完成！")

if __name__ == '__main__':
    print("开始删除业务委托书服务内容字段...")
    print("=" * 50)
    remove_service_content_fields()
    print("=" * 50)
    print("操作完成！")

