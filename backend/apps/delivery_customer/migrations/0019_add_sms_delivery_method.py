# Generated migration to add SMS delivery method
# 添加短信报送方式

from django.db import migrations, models


def add_sms_delivery_method(apps, schema_editor):
    """添加短信报送方式"""
    DeliveryMethod = apps.get_model('delivery_customer', 'DeliveryMethod')
    
    # 检查是否已存在，避免重复添加
    if not DeliveryMethod.objects.filter(code='sms').exists():
        # 获取当前最大排序值（使用简单的查询）
        existing_methods = DeliveryMethod.objects.all()
        max_sort_order = max([m.sort_order for m in existing_methods], default=0)
        
        DeliveryMethod.objects.create(
            name='短信报送',
            code='sms',
            description='通过阿里云短信服务发送短信通知客户，及时告知文件已发送',
            sort_order=max_sort_order + 10,  # 放在最后
            is_active=True,
            created_by=None,  # 系统创建，不指定创建人
        )


def remove_sms_delivery_method(apps, schema_editor):
    """移除短信报送方式"""
    DeliveryMethod = apps.get_model('delivery_customer', 'DeliveryMethod')
    DeliveryMethod.objects.filter(code='sms').delete()


class Migration(migrations.Migration):

    dependencies = [
        ('delivery_customer', '0018_outgoingdocumenttracking_express_reject_detail_and_more'),
    ]

    operations = [
        migrations.RunPython(
            add_sms_delivery_method,
            reverse_code=remove_sms_delivery_method,
        ),
    ]

