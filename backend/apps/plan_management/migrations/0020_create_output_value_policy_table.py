# 因 output_value_management 所在环境无法新建 migrations 目录时的建表迁移
# 表归属 output_value_management.OutputValuePolicy，由本迁移代为创建

from django.db import migrations


def create_output_value_policy_table(apps, schema_editor):
    # PostgreSQL: 创建产值口径配置表，与 OutputValuePolicy 模型一致
    schema_editor.execute("""
        CREATE TABLE IF NOT EXISTS output_value_policy (
            id BIGSERIAL PRIMARY KEY,
            name VARCHAR(100) NOT NULL DEFAULT 'V1 默认口径',
            service_type_weights JSONB NOT NULL DEFAULT '{}',
            stage_weight NUMERIC(10, 4) NOT NULL DEFAULT 1.0,
            event_modifier_min NUMERIC(10, 4) NOT NULL DEFAULT 0.2,
            event_modifier_max NUMERIC(10, 4) NOT NULL DEFAULT 1.2,
            confidence_high_threshold NUMERIC(10, 4) NOT NULL DEFAULT 0.30,
            enabled BOOLEAN NOT NULL DEFAULT true,
            effective_from TIMESTAMP WITH TIME ZONE NULL,
            updated_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT NOW(),
            created_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT NOW(),
            updated_by_id INTEGER NULL REFERENCES system_user(id) ON DELETE SET NULL
        );
    """)
    # 全系统仅允许一条 enabled=true
    schema_editor.execute("""
        CREATE UNIQUE INDEX IF NOT EXISTS output_value_policy_single_enabled
        ON output_value_policy (enabled) WHERE enabled = true;
    """)


def drop_output_value_policy_table(apps, schema_editor):
    schema_editor.execute("DROP INDEX IF EXISTS output_value_policy_single_enabled;")
    schema_editor.execute("DROP TABLE IF EXISTS output_value_policy;")


class Migration(migrations.Migration):

    dependencies = [
        ('plan_management', '0019_gate_audit_completion_fact_event'),
        ('system_management', '0016_role_company_unique_code'),
    ]

    operations = [
        migrations.RunPython(create_output_value_policy_table, drop_output_value_policy_table),
    ]
