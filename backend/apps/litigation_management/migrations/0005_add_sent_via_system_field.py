# Generated migration to add missing notification fields
# This fixes the issue where columns litigation_notification_confirmation.sent_via_* do not exist

from django.db import migrations


def add_missing_notification_fields(apps, schema_editor):
    """添加缺失的通知相关字段（如果不存在）"""
    db_alias = schema_editor.connection.alias
    
    with schema_editor.connection.cursor() as cursor:
        # 需要添加的字段列表
        fields_to_add = [
            ('sent_via_system', 'BOOLEAN NOT NULL DEFAULT TRUE'),
            ('sent_via_email', 'BOOLEAN NOT NULL DEFAULT FALSE'),
            ('sent_via_sms', 'BOOLEAN NOT NULL DEFAULT FALSE'),
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


def reverse_add_missing_notification_fields(apps, schema_editor):
    """反向操作：删除字段（如果需要回滚）"""
    db_alias = schema_editor.connection.alias
    
    with schema_editor.connection.cursor() as cursor:
        # 需要删除的字段列表
        fields_to_remove = ['sent_via_system', 'sent_via_email', 'sent_via_sms']
        
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
        ('litigation_management', '0004_fix_notification_confirmation_column_names'),
    ]

    operations = [
        migrations.RunPython(add_missing_notification_fields, reverse_add_missing_notification_fields),
    ]

