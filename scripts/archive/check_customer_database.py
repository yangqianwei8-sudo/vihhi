#!/usr/bin/env python
"""
检查客户成功中心数据库中的信息
"""
import os
import sys
import django

# 设置Django环境
script_dir = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.dirname(script_dir))

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'backend.config.settings')

try:
    django.setup()
except Exception as e:
    print(f"⚠️  Django 设置失败: {e}")
    print("尝试直接连接数据库...")
    import psycopg2
    from dotenv import load_dotenv
    load_dotenv()
    import os
    
    # 从环境变量获取数据库连接信息
    database_url = os.getenv('DATABASE_URL', '')
    if not database_url:
        print("❌ 未找到 DATABASE_URL 环境变量")
        sys.exit(1)
    
    # 解析数据库URL
    # postgresql://user:password@host:port/database
    from urllib.parse import urlparse
    parsed = urlparse(database_url)
    
    conn = psycopg2.connect(
        host=parsed.hostname,
        port=parsed.port or 5432,
        user=parsed.username,
        password=parsed.password,
        database=parsed.path[1:] if parsed.path else 'postgres'
    )
    cursor = conn.cursor()
    
    print("=" * 70)
    print("客户成功中心数据库信息检查")
    print("=" * 70)
    print()
    
    # 检查所有 customer_ 开头的表
    print("📊 客户相关表列表:")
    print("-" * 70)
    cursor.execute("""
        SELECT table_name 
        FROM information_schema.tables 
        WHERE table_schema = 'public' 
        AND table_name LIKE 'customer_%'
        ORDER BY table_name;
    """)
    
    tables = cursor.fetchall()
    total_records = 0
    
    for table in tables:
        table_name = table[0]
        try:
            cursor.execute(f'SELECT COUNT(*) FROM "{table_name}"')
            count = cursor.fetchone()[0]
            total_records += count
            status = "✅" if count > 0 else "⚪"
            print(f'{status} {table_name:50} {count:>10} 条记录')
        except Exception as e:
            print(f'❌ {table_name:50} 查询失败: {str(e)[:30]}')
    
    print("-" * 70)
    print(f"{'总计':50} {total_records:>10} 条记录")
    print()
    
    # 检查主要表的数据
    print("📋 主要表数据详情:")
    print("-" * 70)
    
    main_tables = [
        'customer_client',
        'customer_client_type',
        'customer_client_grade',
        'customer_contact',
        'customer_relationship',
    ]
    
    for table in main_tables:
        try:
            cursor.execute(f'SELECT COUNT(*) FROM "{table}"')
            count = cursor.fetchone()[0]
            if count > 0:
                print(f'  {table:40} {count:>10} 条记录')
        except:
            pass
    
    print()
    
    # 检查 ContentType
    print("📋 ContentType 记录检查:")
    print("-" * 70)
    try:
        cursor.execute("""
            SELECT app_label, model, COUNT(*) 
            FROM django_content_type 
            WHERE app_label IN ('customer_success', 'customer_management')
            GROUP BY app_label, model
            ORDER BY app_label, model;
        """)
        
        content_types = cursor.fetchall()
        if content_types:
            for app_label, model, count in content_types:
                print(f'  {app_label}.{model}')
        else:
            print("  未找到 customer_success 或 customer_management 的 ContentType 记录")
    except Exception as e:
        print(f"  查询失败: {e}")
    
    print()
    
    # 检查迁移记录
    print("📋 Django 迁移记录:")
    print("-" * 70)
    try:
        cursor.execute("""
            SELECT app, COUNT(*) as count 
            FROM django_migrations 
            WHERE app IN ('customer_success', 'customer_management')
            GROUP BY app
            ORDER BY app;
        """)
        
        migrations = cursor.fetchall()
        for app, count in migrations:
            print(f'  {app:30} {count:>5} 个迁移记录')
    except Exception as e:
        print(f"  查询失败: {e}")
    
    conn.close()
    sys.exit(0)

# 如果 Django 设置成功，使用 Django ORM
from django.db import connection
from django.contrib.contenttypes.models import ContentType

print("=" * 70)
print("客户成功中心数据库信息检查")
print("=" * 70)
print()

cursor = connection.cursor()

# 检查所有 customer_ 开头的表
print("📊 客户相关表列表:")
print("-" * 70)
cursor.execute("""
    SELECT table_name 
    FROM information_schema.tables 
    WHERE table_schema = 'public' 
    AND table_name LIKE 'customer_%'
    ORDER BY table_name;
""")

tables = cursor.fetchall()
total_records = 0

for table in tables:
    table_name = table[0]
    try:
        cursor.execute(f'SELECT COUNT(*) FROM "{table_name}"')
        count = cursor.fetchone()[0]
        total_records += count
        status = "✅" if count > 0 else "⚪"
        print(f'{status} {table_name:50} {count:>10} 条记录')
    except Exception as e:
        print(f'❌ {table_name:50} 查询失败')

print("-" * 70)
print(f"{'总计':50} {total_records:>10} 条记录")
print()

# 检查 ContentType
print("📋 ContentType 记录检查:")
print("-" * 70)
cs_types = ContentType.objects.filter(app_label='customer_success')
print(f'customer_success 的 ContentType 记录数: {cs_types.count()}')
if cs_types.count() > 0:
    for ct in cs_types[:10]:
        print(f'  - {ct.app_label}.{ct.model} (id: {ct.id})')

cm_types = ContentType.objects.filter(app_label='customer_management')
print(f'\ncustomer_management 的 ContentType 记录数: {cm_types.count()}')

print()
print("✅ 检查完成")

