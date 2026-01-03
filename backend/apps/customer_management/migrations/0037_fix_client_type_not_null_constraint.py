# Generated migration to fix client_type NOT NULL constraint

from django.db import migrations, models
import django.db.models.deletion


def ensure_client_type_not_null(apps, schema_editor):
    """确保所有现有客户都有 client_type"""
    Client = apps.get_model('customer_management', 'Client')
    ClientType = apps.get_model('customer_management', 'ClientType')
    
    # 获取默认客户类型（第一个激活的类型）
    default_client_type = ClientType.objects.filter(is_active=True).order_by('display_order', 'id').first()
    
    if default_client_type:
        # 为所有没有 client_type 的客户设置默认值
        Client.objects.filter(client_type__isnull=True).update(client_type=default_client_type)


class Migration(migrations.Migration):

    dependencies = [
        ('customer_management', '0036_authorizationlettertemplate_and_more'),
    ]

    operations = [
        # 先确保所有现有客户都有 client_type
        migrations.RunPython(
            ensure_client_type_not_null,
            migrations.RunPython.noop,  # 回滚时不做任何操作
        ),
        # 修改 client_type 字段，不允许 null
        migrations.AlterField(
            model_name='client',
            name='client_type',
            field=models.ForeignKey(
                on_delete=django.db.models.deletion.PROTECT,
                related_name='clients',
                to='customer_management.clienttype',
                verbose_name='客户类型',
                null=False,
                blank=False,
            ),
        ),
    ]

