# Generated manually

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('production_management', '0005_add_department_business_manager_to_contract'),
    ]

    operations = [
        migrations.AddField(
            model_name='businesscontract',
            name='project_number',
            field=models.CharField(
                blank=True,
                help_text='自动生成：HT-YYYY-NNNN，不可修改。如果关联的商机已有业务委托书，则继承其项目编号',
                max_length=50,
                null=True,
                unique=True,
                verbose_name='项目编号'
            ),
        ),
    ]

