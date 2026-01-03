# Generated migration for adding strategic and intent contract types

from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('production_management', '0020_rename_contract_se_contract_idx_contract_se_contrac_35b26d_idx'),
    ]

    operations = [
        # Note: This migration records the addition of new contract type choices
        # ('strategic', '战略合同') and ('intent', '意向合同') to BusinessContract.CONTRACT_TYPE_CHOICES
        # No database schema changes are required as choices are Python-level constraints only
        # The actual changes are in the model definition in models.py
    ]

