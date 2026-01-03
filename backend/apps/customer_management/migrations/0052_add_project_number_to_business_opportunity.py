# Generated manually

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('customer_management', '0051_remove_filter_collapse_feature'),
    ]

    operations = [
        migrations.AddField(
            model_name='businessopportunity',
            name='project_number',
            field=models.CharField(
                blank=True,
                help_text='赢单后自动生成：HT-YYYY-NNNN，不可修改',
                max_length=50,
                null=True,
                unique=True,
                verbose_name='项目编号'
            ),
        ),
    ]

