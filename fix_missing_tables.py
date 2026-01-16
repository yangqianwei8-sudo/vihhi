#!/usr/bin/env python
"""快速检查并创建缺失的表"""
import os, django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'backend.config.settings')
django.setup()

from django.apps import apps
from django.db import models, connection

User = apps.get_model('system_management', 'User')

# 快速查找相关模型
related_models = set()
for model in apps.get_models():
    try:
        for field in model._meta.get_fields():
            if isinstance(field, (models.ForeignKey, models.ManyToManyField)):
                try:
                    if field.related_model == User:
                        related_models.add(model)
                        break
                except: pass
    except: pass

# 批量查询所有表
with connection.cursor() as cursor:
    cursor.execute("SELECT table_name FROM information_schema.tables WHERE table_schema = 'public'")
    existing_tables = {row[0] for row in cursor.fetchall()}

# 检查并创建缺失的主表
missing_main = [(m, m._meta.db_table) for m in related_models if m._meta.db_table not in existing_tables]
if missing_main:
    print(f"创建 {len(missing_main)} 个缺失的主表...")
    for model, table in missing_main:
        try:
            with connection.schema_editor() as se:
                se.create_model(model)
            print(f"  ✓ {table}")
        except Exception as e:
            print(f"  ✗ {table}: {e}")

# 检查并创建缺失的 M2M 表
missing_m2m = []
for model in related_models:
    try:
        for field in model._meta.get_fields():
            if isinstance(field, models.ManyToManyField) and field.related_model == User and not field.auto_created:
                m2m_table = field.remote_field.through._meta.db_table
                if m2m_table not in existing_tables:
                    missing_m2m.append((model, field, m2m_table))
    except: pass

if missing_m2m:
    print(f"\n创建 {len(missing_m2m)} 个缺失的多对多中间表...")
    for model, field, m2m_table in missing_m2m:
        try:
            model1, model2 = model, field.related_model
            f1, f2 = model1._meta.model_name.lower(), model2._meta.model_name.lower()
            with connection.cursor() as c:
                c.execute(f"""
                    CREATE TABLE IF NOT EXISTS {m2m_table} (
                        {f1}_id BIGINT NOT NULL, {f2}_id BIGINT NOT NULL,
                        CONSTRAINT {m2m_table}_pkey PRIMARY KEY ({f1}_id, {f2}_id),
                        CONSTRAINT {m2m_table}_{f1}_fk FOREIGN KEY ({f1}_id) 
                            REFERENCES {model1._meta.db_table}(id) ON DELETE CASCADE,
                        CONSTRAINT {m2m_table}_{f2}_fk FOREIGN KEY ({f2}_id) 
                            REFERENCES {model2._meta.db_table}(id) ON DELETE CASCADE
                    )
                """)
            print(f"  ✓ {m2m_table}")
        except Exception as e:
            print(f"  ✗ {m2m_table}: {e}")

if not missing_main and not missing_m2m:
    print("✓ 所有表都已存在！")





