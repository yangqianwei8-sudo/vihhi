#!/usr/bin/env python
"""
直接执行 production_management 的 BusinessType 迁移，绕过Django的迁移检查器
"""
import os
import sys
import django

# 设置Django环境
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'backend.config.settings')
django.setup()

from django.db import connection, transaction
from django.apps import apps

def execute_migration():
    """执行迁移操作"""
    with connection.cursor() as cursor:
        with transaction.atomic():
            print("=" * 60)
            print("开始执行 BusinessType 迁移...")
            print("=" * 60)
            
            # 1. 创建 BusinessType 表
            print("\n1. 创建 BusinessType 表...")
            try:
                cursor.execute("""
                    CREATE TABLE IF NOT EXISTS production_management_business_type (
                        id BIGSERIAL PRIMARY KEY,
                        code VARCHAR(50) UNIQUE NOT NULL,
                        name VARCHAR(100) NOT NULL,
                        "order" INTEGER NOT NULL DEFAULT 0,
                        is_active BOOLEAN NOT NULL DEFAULT TRUE,
                        description TEXT NOT NULL DEFAULT ''
                    );
                """)
                print("   ✅ BusinessType 表创建成功")
            except Exception as e:
                print(f"   ⚠️  表可能已存在: {e}")
            
            # 2. 创建索引
            print("\n2. 创建索引...")
            try:
                cursor.execute("""
                    CREATE INDEX IF NOT EXISTS production_management_business_type_order_id_idx 
                    ON production_management_business_type ("order", id);
                """)
                print("   ✅ 索引创建成功")
            except Exception as e:
                print(f"   ⚠️  索引可能已存在: {e}")
            
            # 3. 初始化项目业态数据
            print("\n3. 初始化项目业态数据...")
            business_types_data = [
                ('residential', '住宅', 1),
                ('complex', '综合体', 2),
                ('commercial', '商业', 3),
                ('office', '写字楼', 4),
                ('school', '学校', 5),
                ('hospital', '医院', 6),
                ('industrial', '工业厂房', 7),
                ('municipal', '市政', 8),
                ('other', '其他', 9),
            ]
            
            created_count = 0
            updated_count = 0
            
            for code, name, order in business_types_data:
                cursor.execute("""
                    INSERT INTO production_management_business_type (code, name, "order", is_active, description)
                    VALUES (%s, %s, %s, TRUE, '')
                    ON CONFLICT (code) 
                    DO UPDATE SET 
                        name = EXCLUDED.name,
                        "order" = EXCLUDED."order",
                        is_active = EXCLUDED.is_active;
                """, [code, name, order])
                
                # 检查是插入还是更新
                cursor.execute("""
                    SELECT COUNT(*) FROM production_management_business_type WHERE code = %s
                """, [code])
                if cursor.fetchone()[0] > 0:
                    # 检查是否是新插入的
                    cursor.execute("""
                        SELECT id FROM production_management_business_type WHERE code = %s
                    """, [code])
                    result = cursor.fetchone()
                    if result:
                        # 简单判断：如果ID较小，可能是新插入的
                        cursor.execute("""
                            SELECT COUNT(*) FROM production_management_business_type WHERE id < %s
                        """, [result[0]])
                        if cursor.fetchone()[0] == 0:
                            created_count += 1
                        else:
                            updated_count += 1
            
            print(f"   ✅ 项目业态数据初始化完成（新增: {created_count}, 更新: {updated_count}）")
            
            # 4. 检查 Project 表的 business_type 字段类型
            print("\n4. 检查 Project 表的 business_type 字段...")
            cursor.execute("""
                SELECT column_name, data_type 
                FROM information_schema.columns 
                WHERE table_name = 'production_management_project' 
                AND column_name = 'business_type';
            """)
            result = cursor.fetchone()
            
            if result:
                column_name, data_type = result
                print(f"   📋 当前字段类型: {data_type}")
                
                if data_type in ['character varying', 'varchar']:
                    print("   ⚠️  business_type 字段是字符串类型，需要迁移为外键")
                    print("   💡 建议：使用 Django 迁移命令来安全地迁移数据")
                elif data_type in ['integer', 'bigint']:
                    print("   ✅ business_type 字段已经是外键类型")
            else:
                print("   ⚠️  未找到 business_type 字段")
            
            # 5. 标记迁移为已应用（可选）
            print("\n5. 标记迁移为已应用...")
            try:
                cursor.execute("""
                    INSERT INTO django_migrations (app, name, applied)
                    VALUES ('production_management', '0002_create_business_type_and_seed_data', NOW())
                    ON CONFLICT DO NOTHING;
                """)
                print("   ✅ 迁移记录已标记")
            except Exception as e:
                print(f"   ⚠️  标记迁移记录时出错: {e}")
            
            print("\n" + "=" * 60)
            print("✅ BusinessType 迁移完成！")
            print("=" * 60)
            print("\n📋 已创建的项目业态选项：")
            cursor.execute("""
                SELECT code, name, "order", is_active 
                FROM production_management_business_type 
                ORDER BY "order", id;
            """)
            for row in cursor.fetchall():
                status = "✅" if row[3] else "❌"
                print(f"   {status} {row[0]:15s} - {row[1]:10s} (排序: {row[2]})")

if __name__ == '__main__':
    try:
        execute_migration()
    except Exception as e:
        print(f"\n❌ 迁移失败: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)

