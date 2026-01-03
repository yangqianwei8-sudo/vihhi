# Generated migration for removing ContractServiceContent
# 服务信息功能已删除，彻底清除相关数据库表

from django.db import migrations


def remove_contract_service_content_tables(apps, schema_editor):
    """删除ContractServiceContent相关的数据库表"""
    from django.db import connection
    
    with connection.cursor() as cursor:
        # 删除ManyToMany中间表（如果存在）
        cursor.execute("DROP TABLE IF EXISTS contract_service_content_service_professions CASCADE;")
        # 删除主表
        cursor.execute("DROP TABLE IF EXISTS contract_service_content CASCADE;")


def reverse_remove_tables(apps, schema_editor):
    """反向操作：无法恢复已删除的表"""
    pass


class Migration(migrations.Migration):

    dependencies = [
        ('production_management', '0030_convert_opinion_to_opinion_id'),
    ]

    operations = [
        migrations.RunPython(
            remove_contract_service_content_tables,
            reverse_remove_tables,
        ),
    ]
