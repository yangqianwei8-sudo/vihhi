#!/usr/bin/env python
"""
检查所有与 User 模型有外键或多对多关系的模型，确保所有迁移都已正确执行
如果迁移执行不完整，批量创建所有缺失的表
"""
import os
import sys
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'backend.config.settings')
django.setup()

from django.apps import apps
from django.db import models, connection
from django.core.management import call_command
from django.db.migrations.executor import MigrationExecutor
from django.db import connections
from django.conf import settings

def get_user_model():
    """获取 User 模型"""
    try:
        # 首先尝试通过 settings.AUTH_USER_MODEL 获取
        if hasattr(settings, 'AUTH_USER_MODEL'):
            return apps.get_model(settings.AUTH_USER_MODEL)
        # 否则尝试直接获取
        return apps.get_model('system_management', 'User')
    except LookupError:
        print("错误: 无法找到 User 模型")
        sys.exit(1)

def find_user_related_models():
    """查找所有与 User 有关系的模型"""
    User = get_user_model()
    User_table = User._meta.db_table
    all_models = apps.get_models()
    related_models = []
    
    print("=" * 80)
    print("正在查找所有与 User 模型有关系的模型...")
    print("=" * 80)
    
    # 方法1: 通过模型字段检查
    for model in all_models:
        # 跳过 User 模型本身
        if model == User:
            continue
            
        relations = []
        
        try:
            for field in model._meta.get_fields():
                # 检查外键关系
                if isinstance(field, models.ForeignKey):
                    try:
                        related_model = field.related_model
                        # 检查是否指向 User 模型
                        if related_model == User:
                            relations.append({
                                'type': 'ForeignKey',
                                'field': field.name,
                                'related_name': getattr(field, 'related_name', None),
                                'on_delete': field.on_delete.__name__ if hasattr(field.on_delete, '__name__') else str(field.on_delete),
                            })
                    except Exception as e:
                        pass
                
                # 检查多对多关系
                elif isinstance(field, models.ManyToManyField):
                    try:
                        related_model = field.related_model
                        if related_model == User:
                            relations.append({
                                'type': 'ManyToManyField',
                                'field': field.name,
                                'related_name': getattr(field, 'related_name', None),
                            })
                    except Exception as e:
                        pass
        except Exception as e:
            continue
        
        if relations:
            related_models.append({
                'model': model,
                'app_label': model._meta.app_label,
                'model_name': model.__name__,
                'table_name': model._meta.db_table,
                'relations': relations
            })
    
    # 方法2: 通过数据库外键约束检查（补充方法1可能遗漏的）
    print("\n通过数据库外键约束检查补充遗漏的关系...")
    try:
        with connection.cursor() as cursor:
            # 查询所有指向 User 表的外键
            cursor.execute("""
                SELECT 
                    tc.table_name,
                    kcu.column_name,
                    ccu.table_name AS foreign_table_name
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
            
            db_fk_relations = cursor.fetchall()
            
            for table_name, column_name, foreign_table_name in db_fk_relations:
                # 查找对应的模型
                found = False
                for model_info in related_models:
                    if model_info['table_name'] == table_name:
                        # 检查是否已有此字段的关系记录
                        for rel in model_info['relations']:
                            if rel['field'] == column_name:
                                found = True
                                break
                        if not found:
                            # 添加从数据库发现的外键关系
                            model_info['relations'].append({
                                'type': 'ForeignKey',
                                'field': column_name,
                                'related_name': None,
                                'on_delete': 'UNKNOWN',
                                'source': 'database'
                            })
                        found = True
                        break
                
                if not found:
                    # 尝试找到对应的模型
                    for model in all_models:
                        if model._meta.db_table == table_name:
                            related_models.append({
                                'model': model,
                                'app_label': model._meta.app_label,
                                'model_name': model.__name__,
                                'table_name': table_name,
                                'relations': [{
                                    'type': 'ForeignKey',
                                    'field': column_name,
                                    'related_name': None,
                                    'on_delete': 'UNKNOWN',
                                    'source': 'database'
                                }]
                            })
                            break
    except Exception as e:
        print(f"  警告: 数据库外键检查失败: {e}")
    
    return related_models

def check_migration_status():
    """检查迁移状态"""
    print("\n" + "=" * 80)
    print("检查迁移状态...")
    print("=" * 80)
    
    executor = MigrationExecutor(connection)
    plan = executor.migration_plan(executor.loader.graph.leaf_nodes())
    
    unapplied = []
    for migration, backwards in plan:
        if not backwards:
            unapplied.append(migration)
    
    if unapplied:
        print(f"\n发现 {len(unapplied)} 个未应用的迁移:")
        for migration in unapplied:
            print(f"  - {migration.app_label}.{migration.name}")
        return False
    else:
        print("\n✓ 所有迁移都已应用")
        return True

def check_tables_exist(related_models):
    """检查所有相关模型的表是否存在"""
    print("\n" + "=" * 80)
    print("检查所有相关模型的表是否存在...")
    print("=" * 80)
    
    with connection.cursor() as cursor:
        cursor.execute("""
            SELECT table_name 
            FROM information_schema.tables 
            WHERE table_schema = 'public' 
            AND table_type = 'BASE TABLE'
        """)
        existing_tables = {row[0] for row in cursor.fetchall()}
    
    missing_tables = []
    existing_tables_list = []
    
    for model_info in related_models:
        model = model_info['model']
        table_name = model_info['table_name']
        
        if table_name in existing_tables:
            existing_tables_list.append(model_info)
        else:
            missing_tables.append(model_info)
    
    print(f"\n已存在的表: {len(existing_tables_list)}")
    if existing_tables_list:
        for info in existing_tables_list:
            print(f"  ✓ {info['app_label']}.{info['model_name']} -> {info['table_name']}")
    
    print(f"\n缺失的表: {len(missing_tables)}")
    if missing_tables:
        for info in missing_tables:
            print(f"  ✗ {info['app_label']}.{info['model_name']} -> {info['table_name']}")
            for rel in info['relations']:
                print(f"     关系: {rel['type']} - {rel['field']}")
    
    # 检查多对多中间表
    print("\n检查多对多关系的中间表...")
    m2m_missing = []
    
    for model_info in related_models:
        model = model_info['model']
        for rel in model_info['relations']:
            if rel['type'] == 'ManyToManyField':
                try:
                    field = model._meta.get_field(rel['field'])
                    if not field.auto_created:
                        m2m_table = field.remote_field.through._meta.db_table
                        if m2m_table not in existing_tables:
                            m2m_missing.append({
                                'model_info': model_info,
                                'field_name': rel['field'],
                                'table_name': m2m_table
                            })
                except Exception as e:
                    pass
    
    print(f"\n缺失的多对多中间表: {len(m2m_missing)}")
    if m2m_missing:
        for m2m in m2m_missing:
            print(f"  ✗ {m2m['model_info']['app_label']}.{m2m['model_info']['model_name']}.{m2m['field_name']} -> {m2m['table_name']}")
    
    return missing_tables, m2m_missing

def create_missing_tables(missing_tables, m2m_missing):
    """批量创建缺失的表"""
    if not missing_tables and not m2m_missing:
        print("\n✓ 所有表都已存在，无需创建！")
        return
    
    print("\n" + "=" * 80)
    print("开始批量创建缺失的表...")
    print("=" * 80)
    
    created_count = 0
    failed_count = 0
    
    # 创建主表
    for model_info in missing_tables:
        model = model_info['model']
        table_name = model_info['table_name']
        
        try:
            with connection.schema_editor() as schema_editor:
                schema_editor.create_model(model)
            print(f"  ✓ 创建表: {table_name} ({model_info['app_label']}.{model_info['model_name']})")
            created_count += 1
        except Exception as e:
            error_msg = str(e)
            if 'already exists' in error_msg.lower() or 'duplicate' in error_msg.lower():
                print(f"  - 表已存在: {table_name}")
            else:
                print(f"  ✗ 创建表失败: {table_name} - {error_msg}")
                failed_count += 1
    
    # 创建多对多中间表
    for m2m in m2m_missing:
        try:
            model = m2m['model_info']['model']
            field = model._meta.get_field(m2m['field_name'])
            through_model = field.remote_field.through
            
            with connection.schema_editor() as schema_editor:
                schema_editor.create_model(through_model)
            print(f"  ✓ 创建多对多中间表: {m2m['table_name']}")
            created_count += 1
        except Exception as e:
            error_msg = str(e)
            if 'already exists' in error_msg.lower() or 'duplicate' in error_msg.lower():
                print(f"  - 多对多中间表已存在: {m2m['table_name']}")
            else:
                print(f"  ✗ 创建多对多中间表失败: {m2m['table_name']} - {error_msg}")
                failed_count += 1
    
    print(f"\n创建结果:")
    print(f"  成功创建: {created_count} 个表")
    if failed_count > 0:
        print(f"  失败: {failed_count} 个表")

def apply_migrations():
    """应用所有迁移"""
    print("\n" + "=" * 80)
    print("尝试应用所有迁移...")
    print("=" * 80)
    
    try:
        call_command('migrate', verbosity=2, interactive=False)
        print("\n✓ 迁移应用完成")
        return True
    except Exception as e:
        print(f"\n✗ 迁移应用失败: {e}")
        return False

def main():
    """主函数"""
    print("=" * 80)
    print("User 模型关系检查和迁移验证工具")
    print("=" * 80)
    
    # 1. 查找所有与 User 有关系的模型
    related_models = find_user_related_models()
    
    print(f"\n找到 {len(related_models)} 个与 User 有关系的模型:")
    for model_info in related_models:
        print(f"  - {model_info['app_label']}.{model_info['model_name']} ({len(model_info['relations'])} 个关系)")
        for rel in model_info['relations']:
            print(f"      {rel['type']}: {rel['field']}")
    
    # 2. 检查迁移状态
    migrations_ok = check_migration_status()
    
    # 3. 检查表是否存在
    missing_tables, m2m_missing = check_tables_exist(related_models)
    
    # 4. 如果迁移未完全应用，先尝试应用迁移
    if not migrations_ok:
        print("\n检测到未应用的迁移，尝试应用迁移...")
        apply_migrations()
        # 重新检查表
        missing_tables, m2m_missing = check_tables_exist(related_models)
    
    # 5. 如果有缺失的表，批量创建
    if missing_tables or m2m_missing:
        create_missing_tables(missing_tables, m2m_missing)
        
        # 再次检查
        print("\n" + "=" * 80)
        print("最终验证...")
        print("=" * 80)
        missing_tables_final, m2m_missing_final = check_tables_exist(related_models)
        
        if not missing_tables_final and not m2m_missing_final:
            print("\n✓ 所有表都已成功创建！")
        else:
            print(f"\n⚠ 仍有 {len(missing_tables_final)} 个主表和 {len(m2m_missing_final)} 个多对多中间表缺失")
    else:
        print("\n✓ 所有表都已存在，无需创建！")
    
    print("\n" + "=" * 80)
    print("检查完成")
    print("=" * 80)

if __name__ == '__main__':
    main()

