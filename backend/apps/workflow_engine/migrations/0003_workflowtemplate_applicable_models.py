# Generated manually to fix applicable_models field
# This migration handles the case where the field may already exist in the database

from django.db import migrations, models
import django.contrib.postgres.fields


class Migration(migrations.Migration):

    dependencies = [
        ('workflow_engine', '0002_alter_approvalinstance_content_type_and_more'),
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
                                AND column_name = 'applicable_models'
                            ) THEN
                                ALTER TABLE workflow_template 
                                ADD COLUMN applicable_models text[] DEFAULT '{}' NOT NULL;
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
                                AND column_name = 'applicable_models'
                                AND is_nullable = 'YES'
                            ) THEN
                                -- 更新 NULL 值为空数组
                                UPDATE workflow_template 
                                SET applicable_models = '{}' 
                                WHERE applicable_models IS NULL;
                                
                                -- 设置默认值
                                ALTER TABLE workflow_template 
                                ALTER COLUMN applicable_models SET DEFAULT '{}';
                                
                                -- 设置为不允许 NULL
                                ALTER TABLE workflow_template 
                                ALTER COLUMN applicable_models SET NOT NULL;
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
                                AND column_name = 'applicable_models'
                                AND is_nullable = 'NO'
                                AND column_default IS NULL
                            ) THEN
                                -- 更新 NULL 值为空数组（虽然理论上不应该有 NULL）
                                UPDATE workflow_template 
                                SET applicable_models = '{}' 
                                WHERE applicable_models IS NULL;
                                
                                -- 设置默认值
                                ALTER TABLE workflow_template 
                                ALTER COLUMN applicable_models SET DEFAULT '{}';
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
                    name='applicable_models',
                    field=django.contrib.postgres.fields.ArrayField(
                        base_field=models.CharField(max_length=100),
                        blank=True,
                        default=list,
                        help_text='指定此流程适用的业务模型，例如：businesscontract（合同）、businessopportunity（商机）、project（项目）等',
                        size=None,
                        verbose_name='适用模型',
                    ),
                ),
            ],
        ),
    ]
