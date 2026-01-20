# Generated migration to fix column name mismatch
# This fixes the issue where SQL script created columns with different names than Django model expects

from django.db import migrations


def rename_columns_if_exist(apps, schema_editor):
    """重命名列（如果存在）"""
    db_alias = schema_editor.connection.alias
    
    # 检查并重命名 title -> notification_title
    with schema_editor.connection.cursor() as cursor:
        # 检查 title 列是否存在
        cursor.execute("""
            SELECT column_name 
            FROM information_schema.columns 
            WHERE table_name='litigation_notification_confirmation' 
            AND column_name='title'
        """)
        if cursor.fetchone():
            # 检查 notification_title 是否已存在
            cursor.execute("""
                SELECT column_name 
                FROM information_schema.columns 
                WHERE table_name='litigation_notification_confirmation' 
                AND column_name='notification_title'
            """)
            if not cursor.fetchone():
                # 重命名 title 为 notification_title
                cursor.execute("""
                    ALTER TABLE litigation_notification_confirmation 
                    RENAME COLUMN title TO notification_title
                """)
        
        # 检查并重命名 message -> notification_content
        cursor.execute("""
            SELECT column_name 
            FROM information_schema.columns 
            WHERE table_name='litigation_notification_confirmation' 
            AND column_name='message'
        """)
        if cursor.fetchone():
            # 检查 notification_content 是否已存在
            cursor.execute("""
                SELECT column_name 
                FROM information_schema.columns 
                WHERE table_name='litigation_notification_confirmation' 
                AND column_name='notification_content'
            """)
            if not cursor.fetchone():
                # 重命名 message 为 notification_content
                cursor.execute("""
                    ALTER TABLE litigation_notification_confirmation 
                    RENAME COLUMN message TO notification_content
                """)


def reverse_rename(apps, schema_editor):
    """反向操作：将列名改回（如果需要回滚）"""
    db_alias = schema_editor.connection.alias
    
    with schema_editor.connection.cursor() as cursor:
        # 检查并重命名 notification_title -> title
        cursor.execute("""
            SELECT column_name 
            FROM information_schema.columns 
            WHERE table_name='litigation_notification_confirmation' 
            AND column_name='notification_title'
        """)
        if cursor.fetchone():
            cursor.execute("""
                SELECT column_name 
                FROM information_schema.columns 
                WHERE table_name='litigation_notification_confirmation' 
                AND column_name='title'
            """)
            if not cursor.fetchone():
                cursor.execute("""
                    ALTER TABLE litigation_notification_confirmation 
                    RENAME COLUMN notification_title TO title
                """)
        
        # 检查并重命名 notification_content -> message
        cursor.execute("""
            SELECT column_name 
            FROM information_schema.columns 
            WHERE table_name='litigation_notification_confirmation' 
            AND column_name='notification_content'
        """)
        if cursor.fetchone():
            cursor.execute("""
                SELECT column_name 
                FROM information_schema.columns 
                WHERE table_name='litigation_notification_confirmation' 
                AND column_name='message'
            """)
            if not cursor.fetchone():
                cursor.execute("""
                    ALTER TABLE litigation_notification_confirmation 
                    RENAME COLUMN notification_content TO message
                """)


class Migration(migrations.Migration):

    dependencies = [
        ('litigation_management', '0003_alter_litigationcase_contract_and_more'),
    ]

    operations = [
        migrations.RunPython(rename_columns_if_exist, reverse_rename),
    ]
