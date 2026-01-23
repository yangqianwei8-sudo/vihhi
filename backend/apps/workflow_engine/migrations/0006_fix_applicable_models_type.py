# Generated migration to fix applicable_models field type
# Convert from character varying to text[] array

from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('workflow_engine', '0005_workflowtemplate_form_filter_conditions'),
    ]

    operations = [
        migrations.RunSQL(
            sql=[
                """
                DO $$
                BEGIN
                    -- 检查字段类型
                    IF EXISTS (
                        SELECT 1 FROM information_schema.columns 
                        WHERE table_name = 'workflow_template' 
                        AND column_name = 'applicable_models'
                        AND data_type = 'character varying'
                    ) THEN
                        -- 1. 创建一个临时列来存储数组数据
                        ALTER TABLE workflow_template 
                        ADD COLUMN applicable_models_temp text[];
                        
                        -- 2. 将现有字符串数据转换为数组
                        -- 如果字段为空或NULL，设置为空数组
                        -- 如果有值，尝试解析为数组（假设是JSON格式或逗号分隔）
                        UPDATE workflow_template 
                        SET applicable_models_temp = CASE
                            WHEN applicable_models IS NULL OR applicable_models = '' THEN '{}'
                            WHEN applicable_models LIKE '[%]' THEN 
                                -- 如果是JSON数组格式，使用JSON解析
                                ARRAY(SELECT json_array_elements_text(applicable_models::json))
                            ELSE 
                                -- 如果是逗号分隔的字符串，转换为数组
                                string_to_array(applicable_models, ',')
                        END;
                        
                        -- 3. 删除旧列
                        ALTER TABLE workflow_template 
                        DROP COLUMN applicable_models;
                        
                        -- 4. 重命名临时列为原列名
                        ALTER TABLE workflow_template 
                        RENAME COLUMN applicable_models_temp TO applicable_models;
                        
                        -- 5. 设置默认值和约束
                        ALTER TABLE workflow_template 
                        ALTER COLUMN applicable_models SET DEFAULT '{}',
                        ALTER COLUMN applicable_models SET NOT NULL;
                    END IF;
                END $$;
                """,
            ],
            reverse_sql=[
                """
                DO $$
                BEGIN
                    -- 反向操作：将数组转换回字符串
                    IF EXISTS (
                        SELECT 1 FROM information_schema.columns 
                        WHERE table_name = 'workflow_template' 
                        AND column_name = 'applicable_models'
                        AND data_type = 'ARRAY'
                    ) THEN
                        -- 创建临时列
                        ALTER TABLE workflow_template 
                        ADD COLUMN applicable_models_temp character varying;
                        
                        -- 将数组转换为逗号分隔的字符串
                        UPDATE workflow_template 
                        SET applicable_models_temp = array_to_string(applicable_models, ',');
                        
                        -- 删除数组列
                        ALTER TABLE workflow_template 
                        DROP COLUMN applicable_models;
                        
                        -- 重命名
                        ALTER TABLE workflow_template 
                        RENAME COLUMN applicable_models_temp TO applicable_models;
                    END IF;
                END $$;
                """,
            ],
        ),
    ]
