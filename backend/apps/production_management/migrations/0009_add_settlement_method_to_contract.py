# -*- coding: utf-8 -*-
# Generated manually for adding settlement_method field to BusinessContract

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('production_management', '0008_add_credit_code_legal_representative_to_contract_party'),
    ]

    operations = [
        migrations.AddField(
            model_name='businesscontract',
            name='settlement_method',
            field=models.CharField(
                blank=True,
                choices=[
                    ('fixed_total', '固定总价'),
                    ('fixed_unit', '固定单价'),
                    ('cumulative_commission', '累计提成'),
                    ('segmented_commission', '分段递增提成'),
                    ('jump_point_commission', '跳点提成'),
                    ('combined', '固定价款 + 按实结算'),
                ],
                help_text='合同的结算方式，与结算中心保持一致',
                max_length=30,
                null=True,
                verbose_name='结算方式',
            ),
        ),
    ]

