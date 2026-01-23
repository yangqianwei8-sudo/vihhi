# Generated manually to add form_filter_conditions field
# This migration handles the case where the field may already exist in the database

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('workflow_engine', '0004_workflowtemplate_sub_workflow_trigger_condition'),
    ]

    operations = [
        # 使用 SeparateDatabaseAndState 来分别处理数据库和迁移状态
        migrations.SeparateDatabaseAndState(
            # 数据库操作：确保字段在数据库中正确设置
            database_operations=[
                migrations.RunSQL(
                    sql=[
                        # 如果字段不存在，添加字段
                        """
                        DO $$
                        BEGIN
                            IF NOT EXISTS (
                                SELECT 1 FROM information_schema.columns 
                                WHERE table_name = 'workflow_template' 
                                AND column_name = 'form_filter_conditions'
                            ) THEN
                                ALTER TABLE workflow_template 
                                ADD COLUMN form_filter_conditions jsonb DEFAULT '{}' NOT NULL;
                            END IF;
                        END $$;
                        """,
                        # 如果字段存在但允许 NULL，修改为不允许 NULL 并设置默认值
                        """
                        DO $$
                        BEGIN
                            IF EXISTS (
                                SELECT 1 FROM information_schema.columns 
                                WHERE table_name = 'workflow_template' 
                                AND column_name = 'form_filter_conditions'
                                AND is_nullable = 'YES'
                            ) THEN
                                -- 更新 NULL 值为空对象
                                UPDATE workflow_template 
                                SET form_filter_conditions = '{}'::jsonb 
                                WHERE form_filter_conditions IS NULL;
                                
                                -- 设置默认值
                                ALTER TABLE workflow_template 
                                ALTER COLUMN form_filter_conditions SET DEFAULT '{}'::jsonb;
                                
                                -- 设置为不允许 NULL
                                ALTER TABLE workflow_template 
                                ALTER COLUMN form_filter_conditions SET NOT NULL;
                            END IF;
                        END $$;
                        """,
                        # 如果字段存在但不允许 NULL 但没有默认值，设置默认值
                        """
                        DO $$
                        BEGIN
                            IF EXISTS (
                                SELECT 1 FROM information_schema.columns 
                                WHERE table_name = 'workflow_template' 
                                AND column_name = 'form_filter_conditions'
                                AND is_nullable = 'NO'
                                AND column_default IS NULL
                            ) THEN
                                -- 更新 NULL 值为空对象（虽然理论上不应该有 NULL）
                                UPDATE workflow_template 
                                SET form_filter_conditions = '{}'::jsonb 
                                WHERE form_filter_conditions IS NULL;
                                
                                -- 设置默认值
                                ALTER TABLE workflow_template 
                                ALTER COLUMN form_filter_conditions SET DEFAULT '{}'::jsonb;
                            END IF;
                        END $$;
                        """,
                    ],
                    reverse_sql=migrations.RunSQL.noop,
                ),
            ],
            # 迁移状态操作：将字段添加到迁移状态
            state_operations=[
                migrations.AddField(
                    model_name='workflowtemplate',
                    name='form_filter_conditions',
                    field=models.JSONField(
                        blank=True,
                        default=dict,
                        help_text='针对所选模型的具体表单筛选条件，JSON格式。例如：{"businesscontract": {"contract_type": ["sales", "purchase"]}}',
                        verbose_name='表单筛选条件',
                    ),
                ),
            ],
        ),
    ]
