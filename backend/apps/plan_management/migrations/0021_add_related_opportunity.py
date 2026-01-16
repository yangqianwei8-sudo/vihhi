# Generated manually

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('plan_management', '0020_auto_20260116_0006'),
        ('customer_management', '__latest__'),
    ]

    operations = [
        migrations.AddField(
            model_name='plan',
            name='related_opportunity',
            field=models.ForeignKey(
                blank=True,
                help_text='关联到商机，通过商机获取项目信息',
                null=True,
                on_delete=django.db.models.deletion.SET_NULL,
                related_name='related_plans',
                to='customer_management.businessopportunity',
                verbose_name='关联商机'
            ),
        ),
    ]
