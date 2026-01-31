# 将 ServiceType、DesignStage 的外键从 production_management 改为 base_data

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('opportunity_management', '0003_add_missing_columns'),
        ('base_data', '0001_initial'),
    ]

    operations = [
        migrations.AlterField(
            model_name='businessopportunity',
            name='service_type',
            field=models.ForeignKey(
                blank=True,
                null=True,
                on_delete=django.db.models.deletion.SET_NULL,
                related_name='opportunities',
                to='base_data.servicetype',
                verbose_name='服务类型'
            ),
        ),
        migrations.AlterField(
            model_name='businessopportunity',
            name='drawing_stage',
            field=models.ForeignKey(
                blank=True,
                db_column='drawing_stage',
                null=True,
                on_delete=django.db.models.deletion.SET_NULL,
                related_name='opportunities',
                to='base_data.designstage',
                verbose_name='图纸阶段'
            ),
        ),
    ]
