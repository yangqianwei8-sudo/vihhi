# Generated manually

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('customer_management', '0028_add_visit_four_step_process'),
    ]

    operations = [
        migrations.AddField(
            model_name='customerrelationship',
            name='visit_type',
            field=models.CharField(
                blank=True,
                choices=[
                    ('cooperation', '合作洽谈'),
                    ('contract', '合同洽谈'),
                    ('settlement', '结算洽谈'),
                    ('payment', '回款洽谈'),
                    ('production', '生产洽谈'),
                    ('other', '其他'),
                ],
                help_text='仅当记录类型为拜访记录时使用',
                max_length=20,
                null=True,
                verbose_name='拜访类型'
            ),
        ),
    ]

