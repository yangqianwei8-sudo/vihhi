# Generated manually for adding delivery_methods field to OutgoingDocument

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('delivery_customer', '0005_add_stage_category_to_documents'),
    ]

    operations = [
        migrations.AddField(
            model_name='outgoingdocument',
            name='delivery_methods',
            field=models.CharField(
                blank=True,
                help_text='多选：邮件、快递、送达、易签宝，用逗号分隔',
                max_length=200,
                verbose_name='报送方式',
            ),
        ),
    ]

