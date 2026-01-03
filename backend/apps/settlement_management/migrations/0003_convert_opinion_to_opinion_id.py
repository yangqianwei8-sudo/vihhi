# Generated manually - 将opinion外键字段改为opinion_id IntegerField
# 已删除production_quality模块，需要将外键字段改为存储ID的IntegerField

from django.db import migrations, models


def convert_opinion_to_opinion_id_forward(apps, schema_editor):
    """删除外键约束（如果存在）"""
    from django.db import connection
    
    with connection.cursor() as cursor:
        # 先检查约束是否存在
        try:
            cursor.execute("""
                SELECT constraint_name 
                FROM information_schema.table_constraints 
                WHERE table_name = 'settlement_management_settlementitem' 
                AND constraint_type = 'FOREIGN KEY'
                AND constraint_name LIKE '%opinion_id%'
            """)
            constraints = cursor.fetchall()
            
            for constraint in constraints:
                constraint_name = constraint[0]
                try:
                    cursor.execute(f"""
                        ALTER TABLE settlement_management_settlementitem 
                        DROP CONSTRAINT IF EXISTS {constraint_name}
                    """)
                except Exception as e:
                    # 如果删除失败，继续尝试下一个
                    pass
        except Exception as e:
            # 如果查询失败，尝试直接删除（可能约束不存在）
            try:
                cursor.execute("""
                    ALTER TABLE settlement_management_settlementitem 
                    DROP CONSTRAINT IF EXISTS settlement_management_settlementitem_opinion_id_fkey
                """)
            except:
                pass


def convert_opinion_to_opinion_id_reverse(apps, schema_editor):
    """反向操作：不执行任何操作"""
    pass


class Migration(migrations.Migration):

    dependencies = [
        ('settlement_management', '0002_alter_contractsettlement_approver_and_more'),
    ]

    operations = [
        migrations.SeparateDatabaseAndState(
            database_operations=[
                migrations.RunPython(
                    convert_opinion_to_opinion_id_forward,
                    convert_opinion_to_opinion_id_reverse,
                ),
            ],
            state_operations=[
                migrations.AlterField(
                    model_name='settlementitem',
                    name='opinion_id',
                    field=models.IntegerField(null=True, blank=True, verbose_name='关联意见ID', help_text='从生产管理模块的意见生成（已删除生产质量模块，此字段保留用于历史数据）'),
                ),
            ],
        ),
    ]

