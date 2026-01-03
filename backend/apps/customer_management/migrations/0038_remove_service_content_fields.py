# Generated manually

from django.db import migrations


def check_and_remove_fields(apps, schema_editor):
    """安全地删除字段，如果字段存在则删除"""
    from django.db import connection
    
    with connection.cursor() as cursor:
        # 检查并删除 drawing_stage 字段
        cursor.execute("""
            SELECT column_name 
            FROM information_schema.columns 
            WHERE table_name='business_authorization_letter' 
            AND column_name='drawing_stage'
        """)
        if cursor.fetchone():
            cursor.execute("ALTER TABLE business_authorization_letter DROP COLUMN IF EXISTS drawing_stage")
        
        # 检查并删除 service_professions 字段
        cursor.execute("""
            SELECT column_name 
            FROM information_schema.columns 
            WHERE table_name='business_authorization_letter' 
            AND column_name='service_professions'
        """)
        if cursor.fetchone():
            cursor.execute("ALTER TABLE business_authorization_letter DROP COLUMN IF EXISTS service_professions")
        
        # 检查并删除 service_types 字段
        cursor.execute("""
            SELECT column_name 
            FROM information_schema.columns 
            WHERE table_name='business_authorization_letter' 
            AND column_name='service_types'
        """)
        if cursor.fetchone():
            cursor.execute("ALTER TABLE business_authorization_letter DROP COLUMN IF EXISTS service_types")


def reverse_remove_fields(apps, schema_editor):
    """回滚操作（如果需要）"""
    pass


class Migration(migrations.Migration):

    dependencies = [
        ('customer_management', '0037_fix_client_type_not_null_constraint'),
        ('permission_management', '0001_initial'),  # 添加permission_management依赖，解决system_management.Role的依赖问题
    ]

    operations = [
        migrations.RunPython(check_and_remove_fields, reverse_remove_fields),
    ]

