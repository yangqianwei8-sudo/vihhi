# Generated manually

from django.db import migrations


def check_and_delete_model(apps, schema_editor):
    """检查表是否存在，如果存在则删除，然后删除模型定义"""
    from django.db import connection
    with connection.cursor() as cursor:
        # 检查表是否存在
        cursor.execute("""
            SELECT EXISTS (
                SELECT FROM information_schema.tables 
                WHERE table_schema = 'public' 
                AND table_name = 'customer_contact_info_change'
            );
        """)
        table_exists = cursor.fetchone()[0]
        
        if table_exists:
            # 如果表存在，删除它
            try:
                cursor.execute('DROP TABLE IF EXISTS "customer_contact_info_change" CASCADE;')
            except Exception as e:
                # 如果删除失败，记录但不抛出异常
                print(f'警告：删除表 customer_contact_info_change 时出错: {e}')


def reverse_delete_model(apps, schema_editor):
    """反向操作：不执行任何操作（因为表已经被删除）"""
    pass


class Migration(migrations.Migration):

    dependencies = [
        ('customer_management', '0049_remove_contractchange_approved_by_and_more'),
    ]

    operations = [
        # 先尝试删除表（如果存在）
        migrations.RunPython(check_and_delete_model, reverse_delete_model),
        # 然后删除模型定义（即使表不存在，也要从Django的迁移状态中移除）
        # 使用SeparateDatabaseAndState来分离数据库操作和状态操作
        migrations.SeparateDatabaseAndState(
            database_operations=[
                # 数据库操作：什么都不做（表可能已经不存在）
            ],
            state_operations=[
                # 状态操作：从迁移状态中删除模型
                migrations.DeleteModel(
                    name='ContactInfoChange',
                ),
            ],
        ),
    ]

