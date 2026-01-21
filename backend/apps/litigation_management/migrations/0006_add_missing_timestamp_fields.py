# Generated migration to add missing timestamp fields
# This fixes the issue where columns escalated_at, created_at, updated_at do not exist

from django.db import migrations


def add_missing_timestamp_fields(apps, schema_editor):
    """添加缺失的时间戳字段（如果不存在）"""
    db_alias = schema_editor.connection.alias
    
    with schema_editor.connection.cursor() as cursor:
        # 需要添加的字段列表
        fields_to_add = [
            ('escalated_at', 'TIMESTAMP NULL'),
            ('created_at', 'TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP'),
            ('updated_at', 'TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP'),
        ]
        
        for field_name, field_def in fields_to_add:
            # 检查字段是否存在
            cursor.execute("""
                SELECT column_name 
                FROM information_schema.columns 
                WHERE table_name='litigation_notification_confirmation' 
                AND column_name=%s
            """, [field_name])
            if not cursor.fetchone():
                # 添加字段
                cursor.execute(f"""
                    ALTER TABLE litigation_notification_confirmation 
                    ADD COLUMN {field_name} {field_def}
                """)
                print(f"已添加 {field_name} 字段到 litigation_notification_confirmation 表")
            else:
                print(f"{field_name} 字段已存在，跳过")


def reverse_add_missing_timestamp_fields(apps, schema_editor):
    """反向操作：删除字段（如果需要回滚）"""
    db_alias = schema_editor.connection.alias
    
    with schema_editor.connection.cursor() as cursor:
        # 需要删除的字段列表
        fields_to_remove = ['escalated_at', 'created_at', 'updated_at']
        
        for field_name in fields_to_remove:
            # 检查字段是否存在
            cursor.execute("""
                SELECT column_name 
                FROM information_schema.columns 
                WHERE table_name='litigation_notification_confirmation' 
                AND column_name=%s
            """, [field_name])
            if cursor.fetchone():
                # 删除字段
                cursor.execute(f"""
                    ALTER TABLE litigation_notification_confirmation 
                    DROP COLUMN {field_name}
                """)


class Migration(migrations.Migration):

    dependencies = [
        ('litigation_management', '0005_add_sent_via_system_field'),
    ]

    operations = [
        migrations.RunPython(add_missing_timestamp_fields, reverse_add_missing_timestamp_fields),
    ]

