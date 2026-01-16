# Generated manually

from django.db import migrations, models


def migrate_related_project_data(apps, schema_editor):
    """迁移数据：如果有外键值，转换为项目名称"""
    Plan = apps.get_model('plan_management', 'Plan')
    # 由于我们要删除外键，先保存项目名称（如果有的话）
    # 这里暂时跳过数据迁移，因为我们要改为从商机获取
    pass


class Migration(migrations.Migration):

    dependencies = [
        ('plan_management', '0021_add_related_opportunity'),
    ]

    operations = [
        # 1. 删除 related_opportunity 字段（之前错误添加的）
        migrations.RemoveField(
            model_name='plan',
            name='related_opportunity',
        ),
        # 2. 使用 SQL 直接修改字段类型（因为 Django 不支持直接修改外键为 CharField）
        migrations.RunSQL(
            # 删除外键约束和索引
            sql=[
                "ALTER TABLE plan_plan DROP CONSTRAINT IF EXISTS plan_plan_related_project_id_fkey;",
                "DROP INDEX IF EXISTS plan_plan_related_project_id_idx;",
                # 添加新列（临时）
                "ALTER TABLE plan_plan ADD COLUMN related_project_new VARCHAR(200) DEFAULT '';",
                # 删除旧列
                "ALTER TABLE plan_plan DROP COLUMN IF EXISTS related_project_id;",
                # 重命名新列
                "ALTER TABLE plan_plan RENAME COLUMN related_project_new TO related_project;",
            ],
            reverse_sql=[
                "ALTER TABLE plan_plan RENAME COLUMN related_project TO related_project_id;",
                "ALTER TABLE plan_plan ALTER COLUMN related_project_id TYPE bigint USING NULL;",
                "CREATE INDEX IF NOT EXISTS plan_plan_related_project_id_idx ON plan_plan(related_project_id);",
            ]
        ),
    ]
