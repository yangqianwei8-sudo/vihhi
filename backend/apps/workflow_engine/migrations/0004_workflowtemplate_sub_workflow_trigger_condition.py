# Generated manually to fix sub_workflow_trigger_condition field
# This migration handles the case where the field may already exist in the database

from django.db import migrations, models
import django.contrib.postgres.fields


class Migration(migrations.Migration):

    dependencies = [
        ('workflow_engine', '0003_workflowtemplate_applicable_models'),
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
                                AND column_name = 'sub_workflow_trigger_condition'
                            ) THEN
                                ALTER TABLE workflow_template 
                                ADD COLUMN sub_workflow_trigger_condition jsonb DEFAULT '{}' NOT NULL;
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
                                AND column_name = 'sub_workflow_trigger_condition'
                                AND is_nullable = 'YES'
                            ) THEN
                                -- 更新 NULL 值为空对象
                                UPDATE workflow_template 
                                SET sub_workflow_trigger_condition = '{}'::jsonb 
                                WHERE sub_workflow_trigger_condition IS NULL;
                                
                                -- 设置默认值
                                ALTER TABLE workflow_template 
                                ALTER COLUMN sub_workflow_trigger_condition SET DEFAULT '{}'::jsonb;
                                
                                -- 设置为不允许 NULL
                                ALTER TABLE workflow_template 
                                ALTER COLUMN sub_workflow_trigger_condition SET NOT NULL;
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
                                AND column_name = 'sub_workflow_trigger_condition'
                                AND is_nullable = 'NO'
                                AND column_default IS NULL
                            ) THEN
                                -- 更新 NULL 值为空对象（虽然理论上不应该有 NULL）
                                UPDATE workflow_template 
                                SET sub_workflow_trigger_condition = '{}'::jsonb 
                                WHERE sub_workflow_trigger_condition IS NULL;
                                
                                -- 设置默认值
                                ALTER TABLE workflow_template 
                                ALTER COLUMN sub_workflow_trigger_condition SET DEFAULT '{}'::jsonb;
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
                    name='sub_workflow_trigger_condition',
                    field=models.JSONField(
                        blank=True,
                        default=dict,
                        help_text='子工作流触发的条件配置，JSON格式',
                        verbose_name='子工作流触发条件',
                    ),
                ),
            ],
        ),
    ]
