# 商机结构化锚点：添加 project FK，为 B3 铺路

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('opportunity_management', '0006_create_business_bidding_quotation'),
        ('production_management', '0001_initial'),
    ]

    operations = [
        migrations.AddField(
            model_name='businessopportunity',
            name='project',
            field=models.ForeignKey(
                blank=True,
                null=True,
                on_delete=django.db.models.deletion.SET_NULL,
                related_name='opportunities',
                to='production_management.project',
                verbose_name='关联项目'
            ),
        ),
    ]
