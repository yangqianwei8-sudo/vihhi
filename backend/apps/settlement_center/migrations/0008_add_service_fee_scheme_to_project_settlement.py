# Generated manually for adding service_fee_scheme to ProjectSettlement

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('settlement_center', '0007_add_service_fee_settlement_scheme'),
    ]

    operations = [
        migrations.AddField(
            model_name='projectsettlement',
            name='service_fee_scheme',
            field=models.ForeignKey(
                blank=True,
                help_text='可选，如果设置则使用此方案计算服务费，否则使用合同费率表',
                null=True,
                on_delete=django.db.models.deletion.SET_NULL,
                related_name='project_settlements',
                to='settlement_center.servicefeesettlementscheme',
                verbose_name='服务费结算方案'
            ),
        ),
    ]

