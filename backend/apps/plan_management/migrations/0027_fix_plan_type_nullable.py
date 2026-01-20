# Generated manually to fix plan_type null constraint issue

from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('plan_management', '0026_remove_plan_budget_field'),
    ]

    operations = [
        # 允许 plan_type 字段为 null，或设置默认值
        # 注意：plan_type 字段已在 P2-1 迁移中被 level 字段替代，但数据库表中仍存在
        # 使用原始 SQL 修改表结构，因为模型中没有这个字段
        migrations.RunSQL(
            # 允许 plan_type 为 null 并设置默认值
            sql=[
                "ALTER TABLE plan_plan ALTER COLUMN plan_type DROP NOT NULL;",
                "ALTER TABLE plan_plan ALTER COLUMN plan_type SET DEFAULT 'company';",
            ],
            reverse_sql=[
                "ALTER TABLE plan_plan ALTER COLUMN plan_type SET NOT NULL;",
                "ALTER TABLE plan_plan ALTER COLUMN plan_type DROP DEFAULT;",
            ],
        ),
        # 为现有记录设置 plan_type 默认值（基于 level 字段）
        migrations.RunSQL(
            sql=[
                """
                UPDATE plan_plan 
                SET plan_type = CASE 
                    WHEN level = 'personal' THEN 'personal'
                    WHEN level = 'company' THEN 'company'
                    ELSE 'company'
                END
                WHERE plan_type IS NULL;
                """,
            ],
            reverse_sql=migrations.RunSQL.noop,
        ),
    ]
