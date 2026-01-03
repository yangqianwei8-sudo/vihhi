# Generated manually

from django.db import migrations, models
import django.utils.timezone


class Migration(migrations.Migration):

    dependencies = [
        ('system_management', '0001_initial'),
    ]

    operations = [
        migrations.CreateModel(
            name='OurCompany',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('company_name', models.CharField(max_length=200, unique=True, verbose_name='主体名称')),
                ('credit_code', models.CharField(blank=True, max_length=50, verbose_name='统一社会信用代码')),
                ('legal_representative', models.CharField(blank=True, max_length=100, verbose_name='法定代表人')),
                ('registered_address', models.CharField(blank=True, max_length=500, verbose_name='注册地址')),
                ('order', models.IntegerField(default=0, help_text='数字越小越靠前', verbose_name='排序')),
                ('is_active', models.BooleanField(default=True, verbose_name='是否启用')),
                ('created_time', models.DateTimeField(default=django.utils.timezone.now, verbose_name='创建时间')),
                ('updated_time', models.DateTimeField(auto_now=True, verbose_name='更新时间')),
            ],
            options={
                'verbose_name': '我方主体信息',
                'verbose_name_plural': '我方主体信息',
                'db_table': 'system_our_company',
                'ordering': ['order', 'id'],
            },
        ),
    ]

