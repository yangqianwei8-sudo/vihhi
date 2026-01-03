# Generated manually for quotation mode support

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('customer_management', '0008_businessopportunity_client_client_type_and_more'),
    ]

    operations = [
        # 添加报价模式字段
        migrations.AddField(
            model_name='opportunityquotation',
            name='quotation_mode',
            field=models.CharField(
                choices=[
                    ('rate', '纯费率模式'),
                    ('base_fee_rate', '基本费+费率模式'),
                    ('fixed', '包干价模式'),
                    ('segmented', '分段累进模式'),
                    ('min_savings_rate', '最低节省+费率模式'),
                    ('performance_linked', '绩效挂钩模式'),
                    ('hybrid', '混合计价模式'),
                ],
                default='rate',
                help_text='选择报价计算模式',
                max_length=30,
                verbose_name='报价模式'
            ),
        ),
        # 添加模式参数字段（JSON格式）
        migrations.AddField(
            model_name='opportunityquotation',
            name='mode_params',
            field=models.JSONField(
                blank=True,
                default=dict,
                help_text='JSON格式存储报价模式相关参数（费率、基本费、分段配置等）',
                verbose_name='模式参数'
            ),
        ),
        # 添加封顶费字段
        migrations.AddField(
            model_name='opportunityquotation',
            name='cap_fee',
            field=models.DecimalField(
                blank=True,
                decimal_places=2,
                help_text='服务费上限，超过此金额按封顶费计算（可选）',
                max_digits=15,
                null=True,
                verbose_name='封顶费（万元）'
            ),
        ),
        # 添加节省金额字段
        migrations.AddField(
            model_name='opportunityquotation',
            name='saved_amount',
            field=models.DecimalField(
                blank=True,
                decimal_places=2,
                default=0,
                help_text='用于计算服务费的节省金额',
                max_digits=15,
                null=True,
                verbose_name='节省金额（万元）'
            ),
        ),
        # 添加服务费字段
        migrations.AddField(
            model_name='opportunityquotation',
            name='service_fee',
            field=models.DecimalField(
                decimal_places=2,
                default=0,
                help_text='根据报价模式计算的服务费',
                max_digits=15,
                verbose_name='服务费（万元）'
            ),
        ),
        # 添加计算步骤字段（JSON格式）
        migrations.AddField(
            model_name='opportunityquotation',
            name='calculation_steps',
            field=models.JSONField(
                blank=True,
                default=list,
                help_text='JSON格式存储计算过程，用于展示计算明细',
                verbose_name='计算步骤'
            ),
        ),
    ]

