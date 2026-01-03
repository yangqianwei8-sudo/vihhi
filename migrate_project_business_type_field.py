#!/usr/bin/env python
"""
将 Project 表的 business_type 字段从字符串类型迁移为外键类型
"""
import os
import sys
import django

# 设置Django环境
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'backend.config.settings')
django.setup()

from django.db import connection, transaction

def migrate_business_type_field():
    """将 business_type 字段从字符串迁移为外键"""
    with connection.cursor() as cursor:
        with transaction.atomic():
            print("=" * 60)
            print("开始迁移 Project.business_type 字段...")
            print("=" * 60)
            
            # 1. 检查当前字段类型
            print("\n1. 检查当前字段类型...")
            cursor.execute("""
                SELECT column_name, data_type, character_maximum_length
                FROM information_schema.columns 
                WHERE table_name = 'production_management_project' 
                AND column_name = 'business_type';
            """)
            result = cursor.fetchone()
            
            if not result:
                print("   ❌ 未找到 business_type 字段")
                return
            
            column_name, data_type, max_length = result
            print(f"   📋 当前字段类型: {data_type} (最大长度: {max_length})")
            
            if data_type in ['integer', 'bigint']:
                print("   ✅ 字段已经是外键类型，无需迁移")
                return
            
            if data_type not in ['character varying', 'varchar']:
                print(f"   ⚠️  意外的字段类型: {data_type}")
                return
            
            # 2. 获取 BusinessType 映射
            print("\n2. 获取 BusinessType 映射...")
            cursor.execute("""
                SELECT id, code FROM production_management_business_type;
            """)
            code_to_id = {code: id for id, code in cursor.fetchall()}
            print(f"   ✅ 找到 {len(code_to_id)} 个业态类型")
            for code, id in code_to_id.items():
                print(f"      - {code}: {id}")
            
            # 3. 统计需要迁移的数据
            print("\n3. 统计需要迁移的数据...")
            cursor.execute("""
                SELECT business_type, COUNT(*) 
                FROM production_management_project 
                WHERE business_type IS NOT NULL AND business_type != ''
                GROUP BY business_type;
            """)
            stats = cursor.fetchall()
            total_count = sum(count for _, count in stats)
            print(f"   📊 需要迁移的项目数量: {total_count}")
            for code, count in stats:
                status = "✅" if code in code_to_id else "❌"
                print(f"      {status} {code}: {count} 个项目")
            
            # 4. 创建临时字段
            print("\n4. 创建临时外键字段...")
            try:
                cursor.execute("""
                    ALTER TABLE production_management_project 
                    ADD COLUMN business_type_new_id BIGINT NULL;
                """)
                print("   ✅ 临时字段创建成功")
            except Exception as e:
                if 'already exists' in str(e).lower() or 'duplicate' in str(e).lower():
                    print("   ⚠️  临时字段已存在，继续使用")
                else:
                    raise
            
            # 5. 迁移数据
            print("\n5. 迁移数据...")
            migrated_count = 0
            skipped_count = 0
            
            for code, bt_id in code_to_id.items():
                cursor.execute("""
                    UPDATE production_management_project 
                    SET business_type_new_id = %s 
                    WHERE business_type = %s;
                """, [bt_id, code])
                count = cursor.rowcount
                if count > 0:
                    migrated_count += count
                    print(f"   ✅ {code}: 迁移了 {count} 个项目")
            
            # 统计未匹配的数据
            cursor.execute("""
                SELECT COUNT(*) 
                FROM production_management_project 
                WHERE business_type IS NOT NULL 
                AND business_type != '' 
                AND business_type_new_id IS NULL;
            """)
            skipped_count = cursor.fetchone()[0]
            
            if skipped_count > 0:
                print(f"   ⚠️  有 {skipped_count} 个项目的业态代码无法匹配，将保持为空")
                # 显示无法匹配的代码
                cursor.execute("""
                    SELECT DISTINCT business_type 
                    FROM production_management_project 
                    WHERE business_type IS NOT NULL 
                    AND business_type != '' 
                    AND business_type_new_id IS NULL;
                """)
                unmapped_codes = [row[0] for row in cursor.fetchall()]
                print(f"      无法匹配的代码: {', '.join(unmapped_codes)}")
            
            print(f"\n   📊 迁移统计: 成功 {migrated_count} 个，跳过 {skipped_count} 个")
            
            # 6. 删除旧字段
            print("\n6. 删除旧字段...")
            try:
                cursor.execute("""
                    ALTER TABLE production_management_project 
                    DROP COLUMN business_type;
                """)
                print("   ✅ 旧字段删除成功")
            except Exception as e:
                print(f"   ⚠️  删除旧字段时出错: {e}")
                raise
            
            # 7. 重命名新字段
            print("\n7. 重命名新字段...")
            try:
                cursor.execute("""
                    ALTER TABLE production_management_project 
                    RENAME COLUMN business_type_new_id TO business_type;
                """)
                print("   ✅ 字段重命名成功")
            except Exception as e:
                print(f"   ⚠️  重命名字段时出错: {e}")
                raise
            
            # 8. 添加外键约束
            print("\n8. 添加外键约束...")
            try:
                cursor.execute("""
                    ALTER TABLE production_management_project 
                    ADD CONSTRAINT production_management_project_business_type_fk 
                    FOREIGN KEY (business_type) 
                    REFERENCES production_management_business_type(id) 
                    ON DELETE SET NULL;
                """)
                print("   ✅ 外键约束添加成功")
            except Exception as e:
                if 'already exists' in str(e).lower() or 'duplicate' in str(e).lower():
                    print("   ⚠️  外键约束已存在")
                else:
                    print(f"   ⚠️  添加外键约束时出错: {e}")
                    # 外键约束不是必须的，可以继续
            
            # 9. 添加索引（如果不存在）
            print("\n9. 添加索引...")
            try:
                cursor.execute("""
                    CREATE INDEX IF NOT EXISTS production_management_project_business_type_idx 
                    ON production_management_project(business_type);
                """)
                print("   ✅ 索引创建成功")
            except Exception as e:
                print(f"   ⚠️  创建索引时出错: {e}")
            
            print("\n" + "=" * 60)
            print("✅ 字段迁移完成！")
            print("=" * 60)
            
            # 10. 验证迁移结果
            print("\n10. 验证迁移结果...")
            cursor.execute("""
                SELECT column_name, data_type 
                FROM information_schema.columns 
                WHERE table_name = 'production_management_project' 
                AND column_name = 'business_type';
            """)
            result = cursor.fetchone()
            if result:
                column_name, data_type = result
                print(f"   ✅ 字段类型: {data_type}")
                
                # 统计有业态的项目数量
                cursor.execute("""
                    SELECT COUNT(*) 
                    FROM production_management_project 
                    WHERE business_type IS NOT NULL;
                """)
                count = cursor.fetchone()[0]
                print(f"   ✅ 有业态的项目数量: {count}")

if __name__ == '__main__':
    try:
        migrate_business_type_field()
    except Exception as e:
        print(f"\n❌ 迁移失败: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)

