# Generated manually

from django.conf import settings
from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
        ('system_management', '0001_initial'),
        ('customer_management', '0001_initial_squashed_0015_remove_client_blacklist_details_remove_client_code_and_more'),
        ('production_management', '0004_create_design_stage_model'),
    ]

    operations = [
        migrations.AddField(
            model_name='businesscontract',
            name='opportunity',
            field=models.ForeignKey(
                blank=True,
                null=True,
                on_delete=django.db.models.deletion.SET_NULL,
                related_name='contracts',
                to='customer_management.businessopportunity',
                verbose_name='关联商机'
            ),
        ),
        migrations.AddField(
            model_name='businesscontract',
            name='department',
            field=models.ForeignKey(
                blank=True,
                help_text='默认填写人的部门',
                null=True,
                on_delete=django.db.models.deletion.SET_NULL,
                related_name='contracts',
                to='system_management.department',
                verbose_name='部门'
            ),
        ),
        migrations.AddField(
            model_name='businesscontract',
            name='business_manager',
            field=models.ForeignKey(
                blank=True,
                help_text='默认为填写人',
                null=True,
                on_delete=django.db.models.deletion.SET_NULL,
                related_name='managed_contracts',
                to=settings.AUTH_USER_MODEL,
                verbose_name='商务经理'
            ),
        ),
    ]

