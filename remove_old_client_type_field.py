#!/usr/bin/env python
"""
删除旧的 client_type VARCHAR 字段
"""
import os
import sys
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'backend.config.settings')
django.setup()

from django.db import connection, transaction


def remove_old_client_type_field():
    """删除旧的 client_type VARCHAR 字段"""
    with connection.cursor() as cursor:
        with transaction.atomic():
            print("=" * 60)
            print("删除旧的 client_type VARCHAR 字段...")
            print("=" * 60)
            
            # 1. 检查字段是否存在
            print("\n1. 检查字段...")
            cursor.execute("""
                SELECT column_name, data_type, is_nullable
                FROM information_schema.columns 
                WHERE table_name = 'customer_client' 
                AND column_name = 'client_type'
                AND data_type = 'character varying';
            """)
            
            field_info = cursor.fetchone()
            if not field_info:
                print("   ✓ 旧的 client_type VARCHAR 字段不存在，无需删除")
                return True
            
            print(f"   发现字段: {field_info[0]} ({field_info[1]}, NULL={field_info[2]})")
            
            # 2. 检查是否有数据
            print("\n2. 检查数据...")
            cursor.execute("""
                SELECT COUNT(*) FROM customer_client 
                WHERE client_type IS NOT NULL AND client_type != '';
            """)
            data_count = cursor.fetchone()[0]
            print(f"   发现 {data_count} 条记录有 client_type 数据")
            
            if data_count > 0:
                print("   ⚠️  警告：有数据存在，但新字段 client_type_id 应该已经包含这些信息")
                print("   继续删除旧字段...")
            
            # 3. 删除旧字段
            print("\n3. 删除旧字段...")
            try:
                cursor.execute("""
                    ALTER TABLE customer_client 
                    DROP COLUMN IF EXISTS client_type;
                """)
                print("   ✓ 已删除旧的 client_type VARCHAR 字段")
            except Exception as e:
                print(f"   ❌ 删除失败: {e}")
                return False
            
            # 4. 验证
            print("\n4. 验证删除结果...")
            cursor.execute("""
                SELECT column_name 
                FROM information_schema.columns 
                WHERE table_name = 'customer_client' 
                AND column_name = 'client_type'
                AND data_type = 'character varying';
            """)
            
            remaining = cursor.fetchone()
            if remaining:
                print("   ❌ 字段仍然存在")
                return False
            else:
                print("   ✓ 字段已成功删除")
                
                # 检查新字段
                cursor.execute("""
                    SELECT column_name, data_type, is_nullable
                    FROM information_schema.columns 
                    WHERE table_name = 'customer_client' 
                    AND column_name = 'client_type_id';
                """)
                new_field = cursor.fetchone()
                if new_field:
                    print(f"\n✓ 新字段 client_type_id 存在: {new_field[1]}, NULL={new_field[2]}")
                
                print("\n" + "=" * 60)
                print("修复完成！")
                print("=" * 60)
                return True


if __name__ == '__main__':
    try:
        success = remove_old_client_type_field()
        sys.exit(0 if success else 1)
    except Exception as e:
        print(f"\n❌ 执行失败: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)

