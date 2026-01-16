#!/usr/bin/env python
"""
独立脚本：修复 customer_client 表的 client_type 字段约束
此脚本可以直接运行，不依赖 Django 迁移系统
"""
import os
import sys
import django

# 设置 Django 环境
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'backend.config.settings')
django.setup()

from django.db import connection, transaction
from backend.apps.customer_management.models import Client, ClientType


def fix_client_type_constraint():
    """修复 client_type 字段约束"""
    with connection.cursor() as cursor:
        with transaction.atomic():
            print("=" * 60)
            print("开始修复 client_type 字段约束...")
            print("=" * 60)
            
            # 1. 检查是否有 client_type 为 NULL 的记录
            print("\n1. 检查现有数据...")
            cursor.execute("""
                SELECT COUNT(*) FROM customer_client 
                WHERE client_type_id IS NULL;
            """)
            null_count = cursor.fetchone()[0]
            print(f"   发现 {null_count} 条 client_type 为 NULL 的记录")
            
            # 2. 获取默认客户类型
            print("\n2. 获取默认客户类型...")
            default_client_type = ClientType.objects.filter(is_active=True).order_by('display_order', 'id').first()
            if not default_client_type:
                print("   ❌ 错误：没有可用的客户类型！")
                print("   请先运行迁移 0035 初始化客户类型数据，或手动创建客户类型。")
                return False
            
            print(f"   默认客户类型: {default_client_type.id} - {default_client_type.name}")
            
            # 3. 为所有 NULL 记录设置默认值
            if null_count > 0:
                print(f"\n3. 为 {null_count} 条记录设置默认客户类型...")
                cursor.execute("""
                    UPDATE customer_client 
                    SET client_type_id = %s 
                    WHERE client_type_id IS NULL;
                """, [default_client_type.id])
                print(f"   ✓ 已更新 {null_count} 条记录")
            else:
                print("\n3. 所有记录都已设置 client_type，跳过更新")
            
            # 4. 检查数据库约束
            print("\n4. 检查数据库约束...")
            cursor.execute("""
                SELECT 
                    column_name, 
                    is_nullable, 
                    data_type,
                    column_default
                FROM information_schema.columns 
                WHERE table_name = 'customer_client' 
                AND column_name = 'client_type_id';
            """)
            column_info = cursor.fetchone()
            
            if column_info:
                column_name, is_nullable, data_type, column_default = column_info
                print(f"   字段名: {column_name}")
                print(f"   数据类型: {data_type}")
                print(f"   允许 NULL: {is_nullable}")
                print(f"   默认值: {column_default}")
                
                # 5. 如果允许 NULL，修改为不允许 NULL
                if is_nullable == 'YES':
                    print("\n5. 修改约束：不允许 NULL...")
                    try:
                        # 先确保没有 NULL 值
                        cursor.execute("""
                            SELECT COUNT(*) FROM customer_client 
                            WHERE client_type_id IS NULL;
                        """)
                        remaining_nulls = cursor.fetchone()[0]
                        
                        if remaining_nulls > 0:
                            print(f"   ⚠️  警告：仍有 {remaining_nulls} 条记录为 NULL，无法设置 NOT NULL 约束")
                            print("   请先解决这些记录的问题")
                            return False
                        
                        # 修改约束
                        cursor.execute("""
                            ALTER TABLE customer_client 
                            ALTER COLUMN client_type_id SET NOT NULL;
                        """)
                        print("   ✓ 已设置 NOT NULL 约束")
                    except Exception as e:
                        print(f"   ⚠️  修改约束时出错: {e}")
                        print("   这可能是因为约束已存在或其他原因")
                else:
                    print("\n5. 约束已正确设置（不允许 NULL），无需修改")
            else:
                print("   ⚠️  警告：未找到 client_type_id 字段")
                print("   可能需要先运行迁移 0034 将 client_type 改为外键")
                return False
            
            # 6. 验证修复结果
            print("\n6. 验证修复结果...")
            cursor.execute("""
                SELECT COUNT(*) FROM customer_client 
                WHERE client_type_id IS NULL;
            """)
            final_null_count = cursor.fetchone()[0]
            
            if final_null_count == 0:
                print("   ✓ 验证通过：所有记录的 client_type_id 都不为 NULL")
                print("\n" + "=" * 60)
                print("修复完成！")
                print("=" * 60)
                return True
            else:
                print(f"   ❌ 验证失败：仍有 {final_null_count} 条记录为 NULL")
                return False


if __name__ == '__main__':
    try:
        success = fix_client_type_constraint()
        sys.exit(0 if success else 1)
    except Exception as e:
        print(f"\n❌ 执行失败: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)

