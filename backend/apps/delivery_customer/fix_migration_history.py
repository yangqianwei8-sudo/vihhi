#!/usr/bin/env python
"""
修复delivery_customer模块的迁移历史不一致问题

问题：0008迁移被标记为已应用，但它依赖的0003迁移可能未应用
解决方案：检查并修复迁移历史记录
"""
import os
import sys

project_root = os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))))
sys.path.insert(0, project_root)

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'backend.config.settings')

import django
django.setup()

from django.db import connection
from django.core.management import call_command

def check_migration_status():
    """检查迁移状态"""
    print("=" * 60)
    print("检查delivery_customer迁移状态")
    print("=" * 60)
    
    with connection.cursor() as cursor:
        # 获取所有delivery_customer的迁移记录
        cursor.execute("""
            SELECT app, name, applied 
            FROM django_migrations 
            WHERE app = 'delivery_customer' 
            ORDER BY applied
        """)
        migrations = cursor.fetchall()
        
        print(f"\n已应用的迁移 ({len(migrations)} 个):")
        for app, name, applied in migrations:
            print(f"  ✓ {name} - {applied}")
        
        return migrations

def check_migration_dependencies():
    """检查迁移依赖关系"""
    print("\n" + "=" * 60)
    print("检查迁移依赖关系")
    print("=" * 60)
    
    # 0008的依赖
    migration_0008_deps = [
        'delivery_customer.0003_alter_deliveryrecord_project_and_more',
        'delivery_customer.0007_add_project_to_outgoing_document',
    ]
    
    with connection.cursor() as cursor:
        cursor.execute("""
            SELECT name FROM django_migrations 
            WHERE app = 'delivery_customer'
        """)
        applied_migrations = {row[0] for row in cursor.fetchall()}
        
        print("\n0008迁移的依赖:")
        for dep in migration_0008_deps:
            dep_name = dep.split('.')[-1]
            if dep_name in applied_migrations:
                print(f"  ✓ {dep_name} - 已应用")
            else:
                print(f"  ✗ {dep_name} - 未应用")
        
        return applied_migrations, migration_0008_deps

def fix_migration_history():
    """修复迁移历史"""
    print("\n" + "=" * 60)
    print("修复迁移历史")
    print("=" * 60)
    
    migrations = check_migration_status()
    applied_migrations, deps = check_migration_dependencies()
    
    # 检查0008是否已应用
    migration_0008 = '0008_add_client_contact_to_outgoing_document'
    migration_0003 = '0003_alter_deliveryrecord_project_and_more'
    migration_0007 = '0007_add_project_to_outgoing_document'
    
    has_0008 = migration_0008 in [m[1] for m in migrations]
    has_0003 = migration_0003 in [m[1] for m in migrations]
    has_0007 = migration_0007 in [m[1] for m in migrations]
    
    print(f"\n当前状态:")
    print(f"  0003: {'✓ 已应用' if has_0003 else '✗ 未应用'}")
    print(f"  0007: {'✓ 已应用' if has_0007 else '✗ 未应用'}")
    print(f"  0008: {'✓ 已应用' if has_0008 else '✗ 未应用'}")
    
    if has_0008 and (not has_0003 or not has_0007):
        print("\n⚠️ 发现问题：0008已应用，但依赖的迁移未应用")
        print("\n解决方案选项:")
        print("  1. 删除0008的记录，先应用0003和0007，再应用0008")
        print("  2. Fake应用0003和0007（如果表已存在）")
        
        # 非交互模式：自动选择方案2（fake应用），因为表可能已存在
        choice = "2"
        print(f"\n自动选择方案2: Fake应用缺失的迁移（非交互模式）")
        
        if choice == "1":
            # 删除0008的记录
            with connection.cursor() as cursor:
                cursor.execute("""
                    DELETE FROM django_migrations 
                    WHERE app = 'delivery_customer' 
                    AND name = %s
                """, [migration_0008])
                print(f"\n✓ 已删除 {migration_0008} 的迁移记录")
                print("\n接下来请运行:")
                print("  python manage.py migrate delivery_customer")
        elif choice == "2":
            # Fake应用缺失的迁移
            with connection.cursor() as cursor:
                if not has_0003:
                    cursor.execute("""
                        INSERT INTO django_migrations (app, name, applied) 
                        VALUES ('delivery_customer', %s, NOW())
                        ON CONFLICT DO NOTHING
                    """, [migration_0003])
                    print(f"✓ Fake应用 {migration_0003}")
                
                if not has_0007:
                    cursor.execute("""
                        INSERT INTO django_migrations (app, name, applied) 
                        VALUES ('delivery_customer', %s, NOW())
                        ON CONFLICT DO NOTHING
                    """, [migration_0007])
                    print(f"✓ Fake应用 {migration_0007}")
                
                print("\n✓ 迁移历史已修复")
                print("\n现在可以运行:")
                print("  python manage.py migrate settlement_center")
        else:
            print("无效的选择")
            return False
    elif not has_0003 and not has_0007 and not has_0008:
        print("\n所有迁移都未应用，这是正常的")
        print("可以运行: python manage.py migrate delivery_customer")
    else:
        print("\n✓ 迁移历史正常，没有发现不一致问题")
    
    return True

if __name__ == '__main__':
    try:
        success = fix_migration_history()
        if success:
            print("\n" + "=" * 60)
            print("✅ 完成！")
            print("=" * 60)
        sys.exit(0 if success else 1)
    except Exception as e:
        print(f"\n❌ 错误: {str(e)}")
        import traceback
        traceback.print_exc()
        sys.exit(1)

