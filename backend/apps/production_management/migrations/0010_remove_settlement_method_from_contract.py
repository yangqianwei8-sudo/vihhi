# -*- coding: utf-8 -*-
# Generated manually for removing settlement_method field from BusinessContract

from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('production_management', '0009_add_settlement_method_to_contract'),
    ]

    operations = [
        migrations.RemoveField(
            model_name='businesscontract',
            name='settlement_method',
        ),
    ]

