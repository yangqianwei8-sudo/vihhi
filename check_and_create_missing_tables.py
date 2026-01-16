#!/usr/bin/env python
"""
检查所有与 User 模型有关系的模型，并批量创建缺失的表
"""
import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'backend.config.settings')
django.setup()

from django.apps import apps
from django.db import models, connection

def check_and_create_missing_tables():
    """检查并创建所有缺失的表"""
    
    # 获取 User 模型
    User = apps.get_model('system_management', 'User')
    
    print('正在查找所有与 User 有关系的模型...')
    # 查找所有与 User 有关系的模型
    all_models = apps.get_models()
    related_models = set()
    
    for model in all_models:
        try:
            for field in model._meta.get_fields():
                if isinstance(field, (models.ForeignKey, models.ManyToManyField)):
                    try:
                        if field.related_model == User:
                            related_models.add(model)
                            break  # 找到关系就跳出，避免重复检查
                    except:
                        pass  # 跳过无法访问的字段
        except:
            pass  # 跳过无法访问的模型
    
    print(f'找到 {len(related_models)} 个相关模型')
    print('=' * 80)
    print('检查所有相关模型的表是否存在')
    print('=' * 80)
    
    missing_tables = []
    existing_tables = []
    
    # 批量查询所有表名
    with connection.cursor() as cursor:
        # 一次性查询所有表名
        cursor.execute("""
            SELECT table_name 
            FROM information_schema.tables 
            WHERE table_schema = 'public' 
            AND table_type = 'BASE TABLE'
        """)
        existing_table_names = {row[0] for row in cursor.fetchall()}
        
        # 快速检查每个模型
        for model in related_models:
            table_name = model._meta.db_table
            if table_name in existing_table_names:
                existing_tables.append((model, table_name))
            else:
                missing_tables.append((model, table_name))
    
    print(f'\n已存在的表: {len(existing_tables)}')
    print(f'缺失的表: {len(missing_tables)}')
    
    if missing_tables:
        print('\n缺失的表列表:')
        for model, table_name in missing_tables:
            print(f'  ✗ {model._meta.app_label}.{model.__name__} -> {table_name}')
    
    # 检查多对多关系的中间表
    print(f'\n检查多对多关系的中间表...')
    m2m_tables_missing = []
    m2m_tables_existing = []
    
    with connection.cursor() as cursor:
        # 使用已查询的表名集合，避免重复查询
        for model in related_models:
            try:
                for field in model._meta.get_fields():
                    if isinstance(field, models.ManyToManyField) and field.related_model == User:
                        if not field.auto_created:
                            try:
                                m2m_table = field.remote_field.through._meta.db_table
                                if m2m_table in existing_table_names:
                                    m2m_tables_existing.append((model, field.name, m2m_table))
                                else:
                                    m2m_tables_missing.append((model, field.name, m2m_table))
                            except:
                                pass
            except:
                pass
    
    print(f'\n已存在的多对多中间表: {len(m2m_tables_existing)}')
    print(f'缺失的多对多中间表: {len(m2m_tables_missing)}')
    
    if m2m_tables_missing:
        print('\n缺失的多对多中间表列表:')
        for model, field_name, table_name in m2m_tables_missing:
            print(f'  ✗ {model._meta.app_label}.{model.__name__}.{field_name} -> {table_name}')
    
    print(f'\n总结:')
    print(f'  缺失的主表: {len(missing_tables)}')
    print(f'  缺失的多对多中间表: {len(m2m_tables_missing)}')
    
    # 创建缺失的表
    if missing_tables or m2m_tables_missing:
        print('\n' + '=' * 80)
        print('开始创建缺失的表...')
        print('=' * 80)
        
        # 创建缺失的主表
        created_main_tables = 0
        failed_main_tables = []
        
        for model, table_name in missing_tables:
            try:
                with connection.schema_editor() as schema_editor:
                    schema_editor.create_model(model)
                print(f'  ✓ 创建主表: {table_name}')
                created_main_tables += 1
            except Exception as e:
                if 'already exists' in str(e).lower() or 'duplicate' in str(e).lower():
                    print(f'  - 主表已存在: {table_name}')
                else:
                    print(f'  ✗ 创建主表失败: {table_name} - {e}')
                    failed_main_tables.append((table_name, str(e)))
        
        # 创建缺失的多对多中间表
        created_m2m_tables = 0
        failed_m2m_tables = []
        
        for model, field_name, m2m_table in m2m_tables_missing:
            try:
                field = model._meta.get_field(field_name)
                model1 = model
                model2 = field.related_model
                
                # 获取字段名（Django 的命名规则）
                field1_name = model1._meta.model_name.lower()
                field2_name = model2._meta.model_name.lower()
                
                with connection.cursor() as cursor:
                    cursor.execute(f'''
                        CREATE TABLE IF NOT EXISTS {m2m_table} (
                            {field1_name}_id BIGINT NOT NULL,
                            {field2_name}_id BIGINT NOT NULL,
                            CONSTRAINT {m2m_table}_pkey PRIMARY KEY ({field1_name}_id, {field2_name}_id),
                            CONSTRAINT {m2m_table}_{field1_name}_fk 
                                FOREIGN KEY ({field1_name}_id) 
                                REFERENCES {model1._meta.db_table}(id) 
                                ON DELETE CASCADE,
                            CONSTRAINT {m2m_table}_{field2_name}_fk 
                                FOREIGN KEY ({field2_name}_id) 
                                REFERENCES {model2._meta.db_table}(id) 
                                ON DELETE CASCADE
                        )
                    ''')
                print(f'  ✓ 创建多对多中间表: {m2m_table}')
                created_m2m_tables += 1
            except Exception as e:
                if 'already exists' in str(e).lower() or 'duplicate' in str(e).lower():
                    print(f'  - 多对多中间表已存在: {m2m_table}')
                else:
                    print(f'  ✗ 创建多对多中间表失败: {m2m_table} - {e}')
                    failed_m2m_tables.append((m2m_table, str(e)))
        
        print(f'\n创建结果:')
        print(f'  成功创建主表: {created_main_tables}')
        print(f'  成功创建多对多中间表: {created_m2m_tables}')
        if failed_main_tables:
            print(f'  失败的主表: {len(failed_main_tables)}')
            for table_name, error in failed_main_tables:
                print(f'    - {table_name}: {error}')
        if failed_m2m_tables:
            print(f'  失败的多对多中间表: {len(failed_m2m_tables)}')
            for table_name, error in failed_m2m_tables:
                print(f'    - {table_name}: {error}')
    else:
        print('\n✓ 所有表都已存在，无需创建！')

if __name__ == '__main__':
    check_and_create_missing_tables()

