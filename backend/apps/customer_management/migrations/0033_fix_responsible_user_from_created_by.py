# Generated migration to fix responsible_user field
# 将所有客户的 responsible_user 设置为 created_by（创建人）

from django.db import migrations


def fix_responsible_user(apps, schema_editor):
    """将客户的 responsible_user 设置为 created_by"""
    Client = apps.get_model('customer_management', 'Client')
    
    # 获取所有有 created_by 的客户
    clients = Client.objects.filter(created_by__isnull=False).select_related('created_by')
    
    updated_count = 0
    for client in clients.iterator(chunk_size=100):
        # 如果 responsible_user 为空或与 created_by 不同，则更新
        if client.created_by and (not client.responsible_user or client.responsible_user_id != client.created_by_id):
            client.responsible_user = client.created_by
            client.save(update_fields=['responsible_user'])
            updated_count += 1
    
    print(f'已修复 {updated_count} 个客户的负责人字段')


def reverse_fix_responsible_user(apps, schema_editor):
    """回滚操作：不做任何处理（因为无法确定原始值）"""
    pass


class Migration(migrations.Migration):

    dependencies = [
        ('customer_management', '0032_authorizationletter'),
    ]

    operations = [
        migrations.RunPython(
            fix_responsible_user,
            reverse_fix_responsible_user,
        ),
    ]

