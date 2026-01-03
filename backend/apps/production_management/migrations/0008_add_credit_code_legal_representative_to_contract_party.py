# Generated manually

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('production_management', '0007_add_contract_party_model'),
    ]

    operations = [
        migrations.AddField(
            model_name='contractparty',
            name='credit_code',
            field=models.CharField(blank=True, max_length=50, verbose_name='统一社会信用代码'),
        ),
        migrations.AddField(
            model_name='contractparty',
            name='legal_representative',
            field=models.CharField(blank=True, max_length=100, verbose_name='法定代表人'),
        ),
    ]

