#!/usr/bin/env python
"""
完全清理客户成功中心的所有内容

清理范围：
1. ContentType 记录（customer_success.*）
2. Django 迁移记录（customer_success）
3. 其他相关数据
"""
import os
import sys
from dotenv import load_dotenv
import psycopg2
from urllib.parse import urlparse

# 加载环境变量
load_dotenv()

def get_db_connection():
    """获取数据库连接"""
    database_url = os.getenv('DATABASE_URL', '')
    if not database_url:
        print("❌ 未找到 DATABASE_URL 环境变量")
        sys.exit(1)
    
    # 解析数据库URL
    parsed = urlparse(database_url)
    
    try:
        conn = psycopg2.connect(
            host=parsed.hostname,
            port=parsed.port or 5432,
            user=parsed.username,
            password=parsed.password,
            database=parsed.path[1:] if parsed.path else 'postgres'
        )
        return conn
    except Exception as e:
        print(f"❌ 数据库连接失败: {e}")
        sys.exit(1)

def check_content_types(cursor):
    """检查 ContentType 记录"""
    print("=" * 70)
    print("检查 ContentType 记录")
    print("=" * 70)
    print()
    
    cursor.execute("""
        SELECT app_label, model, id
        FROM django_content_type 
        WHERE app_label = 'customer_success'
        ORDER BY app_label, model;
    """)
    
    content_types = cursor.fetchall()
    
    if content_types:
        print(f"发现 {len(content_types)} 个 customer_success 的 ContentType 记录：")
        for app_label, model, ct_id in content_types:
            print(f"  - {app_label}.{model} (id: {ct_id})")
        print()
        return content_types
    else:
        print("✅ 未发现 customer_success 的 ContentType 记录")
        print()
        return []

def check_migrations(cursor):
    """检查迁移记录"""
    print("=" * 70)
    print("检查 Django 迁移记录")
    print("=" * 70)
    print()
    
    cursor.execute("""
        SELECT app, name, applied
        FROM django_migrations 
        WHERE app = 'customer_success'
        ORDER BY applied;
    """)
    
    migrations = cursor.fetchall()
    
    if migrations:
        print(f"发现 {len(migrations)} 个 customer_success 的迁移记录")
        print("（显示前10条）：")
        for app, name, applied in migrations[:10]:
            print(f"  - {app}.{name} ({applied})")
        if len(migrations) > 10:
            print(f"  ... 还有 {len(migrations) - 10} 条记录")
        print()
        return migrations
    else:
        print("✅ 未发现 customer_success 的迁移记录")
        print()
        return []

def delete_content_types(cursor, content_types):
    """删除 ContentType 记录"""
    if not content_types:
        print("✅ 无需删除 ContentType 记录")
        return True
    
    print("=" * 70)
    print("删除 ContentType 记录")
    print("=" * 70)
    print()
    
    # 先检查是否有其他表引用了这些 ContentType
    ct_ids = [ct[2] for ct in content_types]
    placeholders = ','.join(['%s'] * len(ct_ids))
    
    # 检查是否有审批流程引用了这些 ContentType
    try:
        cursor.execute(f"""
            SELECT COUNT(*) 
            FROM workflow_engine_approvalinstance 
            WHERE content_type_id IN ({placeholders})
        """, ct_ids)
        approval_count = cursor.fetchone()[0]
        if approval_count > 0:
            print(f"⚠️  发现 {approval_count} 条审批流程记录引用了这些 ContentType")
            print("   这些审批记录将被删除或无法正常显示")
            print()
    except Exception as e:
        # 表可能不存在，忽略
        pass
    
    # 检查并删除权限记录（必须先删除，因为权限表引用了 ContentType）
    try:
        cursor.execute(f"""
            SELECT id, COUNT(*) 
            FROM auth_permission 
            WHERE content_type_id IN ({placeholders})
            GROUP BY id
        """, ct_ids)
        permission_ids = [row[0] for row in cursor.fetchall()]
        
        if permission_ids:
            permission_count = len(permission_ids)
            print(f"⚠️  发现 {permission_count} 条权限记录引用了这些 ContentType")
            
            # 先删除角色权限关联
            perm_placeholders = ','.join(['%s'] * len(permission_ids))
            try:
                cursor.execute(f"""
                    DELETE FROM system_role_permissions 
                    WHERE permission_id IN ({perm_placeholders})
                """, permission_ids)
                deleted_role_perms = cursor.rowcount
                if deleted_role_perms > 0:
                    print(f"  ✅ 已删除 {deleted_role_perms} 条角色权限关联")
            except Exception as e:
                print(f"  ⚠️  删除角色权限关联时出错（可能表不存在）: {e}")
            
            # 再删除权限记录
            cursor.execute(f"""
                DELETE FROM auth_permission 
                WHERE content_type_id IN ({placeholders})
            """, ct_ids)
            deleted_permissions = cursor.rowcount
            print(f"  ✅ 已删除 {deleted_permissions} 条权限记录")
            print()
    except Exception as e:
        print(f"⚠️  处理权限记录时出错: {e}")
    
    # 删除 ContentType 记录
    try:
        cursor.execute("""
            DELETE FROM django_content_type 
            WHERE app_label = 'customer_success'
        """)
        deleted_count = cursor.rowcount
        print(f"✅ 已删除 {deleted_count} 个 ContentType 记录")
        return True
    except Exception as e:
        print(f"❌ 删除 ContentType 失败: {e}")
        return False

def delete_migrations(cursor, migrations):
    """删除迁移记录"""
    if not migrations:
        print("✅ 无需删除迁移记录")
        return True
    
    print("=" * 70)
    print("删除 Django 迁移记录")
    print("=" * 70)
    print()
    
    try:
        cursor.execute("""
            DELETE FROM django_migrations 
            WHERE app = 'customer_success'
        """)
        deleted_count = cursor.rowcount
        print(f"✅ 已删除 {deleted_count} 个迁移记录")
        print()
        print("⚠️  注意：删除迁移记录后，如果需要重新创建表，需要重新运行迁移")
        return True
    except Exception as e:
        print(f"❌ 删除迁移记录失败: {e}")
        return False

def check_other_references(cursor):
    """检查其他可能的引用"""
    print("=" * 70)
    print("检查其他可能的引用")
    print("=" * 70)
    print()
    
    # 检查审批流程
    try:
        cursor.execute("""
            SELECT COUNT(*) 
            FROM workflow_engine_approvalinstance 
            WHERE content_type_id IN (
                SELECT id FROM django_content_type 
                WHERE app_label = 'customer_success'
            )
        """)
        count = cursor.fetchone()[0]
        if count > 0:
            print(f"⚠️  发现 {count} 条审批流程记录引用了 customer_success 的 ContentType")
            print("   这些记录可能需要处理")
    except Exception:
        # 表可能不存在，忽略
        pass
    
    print()

def main():
    """主函数"""
    print("=" * 70)
    print("完全清理客户成功中心")
    print("=" * 70)
    print()
    print("清理范围：")
    print("  1. ContentType 记录（customer_success.*）")
    print("  2. Django 迁移记录（customer_success）")
    print("  3. 其他相关数据")
    print()
    print("⚠️  警告：此操作将删除所有 customer_success 相关的元数据！")
    print()
    
    # 确认
    confirm = input("确认清理？请输入 'YES' 继续: ")
    if confirm != 'YES':
        print("❌ 操作已取消")
        return
    
    print()
    
    conn = None
    try:
        # 连接数据库
        conn = get_db_connection()
        conn.autocommit = True
        cursor = conn.cursor()
        
        # 步骤1: 检查 ContentType
        content_types = check_content_types(cursor)
        
        # 步骤2: 检查迁移记录
        migrations = check_migrations(cursor)
        
        # 步骤3: 检查其他引用
        check_other_references(cursor)
        
        # 步骤4: 删除 ContentType
        if content_types:
            if not delete_content_types(cursor, content_types):
                print("❌ 删除 ContentType 失败")
                return
        
        # 步骤5: 删除迁移记录
        if migrations:
            if not delete_migrations(cursor, migrations):
                print("❌ 删除迁移记录失败")
                return
        
        print()
        print("=" * 70)
        print("✅ 清理完成")
        print("=" * 70)
        print()
        print("清理内容：")
        if content_types:
            print(f"  ✅ 删除了 {len(content_types)} 个 ContentType 记录")
        if migrations:
            print(f"  ✅ 删除了 {len(migrations)} 个迁移记录")
        
    except Exception as e:
        print()
        print("=" * 70)
        print(f"❌ 操作失败: {e}")
        print("=" * 70)
        import traceback
        traceback.print_exc()
        sys.exit(1)
    finally:
        if conn:
            conn.close()

if __name__ == '__main__':
    main()

