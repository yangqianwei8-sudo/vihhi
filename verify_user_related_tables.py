#!/usr/bin/env python
"""
快速验证所有与 User 相关的表是否都已创建
"""
import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'backend.config.settings')
django.setup()

from django.db import connection
from django.apps import apps

def verify_tables():
    """验证所有与 User 相关的表"""
    User = apps.get_model('system_management', 'User')
    User_table = User._meta.db_table
    
    print("=" * 80)
    print("验证所有与 User 相关的表")
    print("=" * 80)
    
    # 获取所有表
    with connection.cursor() as cursor:
        cursor.execute("""
            SELECT table_name 
            FROM information_schema.tables 
            WHERE table_schema = 'public' 
            AND table_type = 'BASE TABLE'
        """)
        all_tables = {row[0] for row in cursor.fetchall()}
    
    # 查找所有与 User 有关系的模型
    all_models = apps.get_models()
    related_tables = []
    
    for model in all_models:
        if model == User:
            continue
        
        try:
            for field in model._meta.get_fields():
                if isinstance(field, (models.ForeignKey, models.ManyToManyField)):
                    try:
                        if field.related_model == User:
                            related_tables.append({
                                'table': model._meta.db_table,
                                'app': model._meta.app_label,
                                'model': model.__name__,
                                'type': 'ForeignKey' if isinstance(field, models.ForeignKey) else 'ManyToManyField'
                            })
                            break
                    except:
                        pass
        except:
            pass
    
    # 检查数据库外键
    with connection.cursor() as cursor:
        cursor.execute("""
            SELECT DISTINCT tc.table_name
            FROM information_schema.table_constraints AS tc
            JOIN information_schema.key_column_usage AS kcu
                ON tc.constraint_name = kcu.constraint_name
                AND tc.table_schema = kcu.table_schema
            JOIN information_schema.constraint_column_usage AS ccu
                ON ccu.constraint_name = tc.constraint_name
                AND ccu.table_schema = tc.table_schema
            WHERE tc.constraint_type = 'FOREIGN KEY'
                AND ccu.table_name = %s
                AND tc.table_schema = 'public'
        """, [User_table])
        
        fk_tables = {row[0] for row in cursor.fetchall()}
    
    # 合并所有相关表
    all_related_tables = set()
    for item in related_tables:
        all_related_tables.add(item['table'])
    all_related_tables.update(fk_tables)
    
    print(f"\n找到 {len(all_related_tables)} 个相关表")
    print("\n检查表是否存在:")
    print("-" * 80)
    
    missing = []
    existing = []
    
    for table in sorted(all_related_tables):
        if table in all_tables:
            existing.append(table)
            print(f"  ✓ {table}")
        else:
            missing.append(table)
            print(f"  ✗ {table} (缺失)")
    
    # 检查多对多中间表
    print("\n检查多对多中间表:")
    print("-" * 80)
    
    m2m_missing = []
    m2m_existing = []
    
    for model in all_models:
        if model == User:
            continue
        try:
            for field in model._meta.get_fields():
                if isinstance(field, models.ManyToManyField) and field.related_model == User:
                    if not field.auto_created:
                        try:
                            m2m_table = field.remote_field.through._meta.db_table
                            if m2m_table in all_tables:
                                m2m_existing.append(m2m_table)
                                print(f"  ✓ {m2m_table}")
                            else:
                                m2m_missing.append(m2m_table)
                                print(f"  ✗ {m2m_table} (缺失)")
                        except:
                            pass
        except:
            pass
    
    print("\n" + "=" * 80)
    print("验证结果:")
    print("=" * 80)
    print(f"主表: {len(existing)} 个存在, {len(missing)} 个缺失")
    print(f"多对多中间表: {len(m2m_existing)} 个存在, {len(m2m_missing)} 个缺失")
    
    if missing or m2m_missing:
        print("\n⚠ 发现缺失的表，请运行 check_user_related_models_migration.py 进行修复")
        return False
    else:
        print("\n✓ 所有表都已存在！")
        return True

if __name__ == '__main__':
    from django.db import models
    verify_tables()

