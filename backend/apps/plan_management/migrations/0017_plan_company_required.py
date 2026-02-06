# P0-5: Plan.company 改为必填（回填已完成后再执行）

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('plan_management', '0016_add_choice_indicator_type'),
    ]

    operations = [
        migrations.AlterField(
            model_name='plan',
            name='company',
            field=models.ForeignKey(
                on_delete=django.db.models.deletion.PROTECT,
                related_name='plans',
                to='system_management.ourcompany',
                verbose_name='公司',
            ),
        ),
    ]
