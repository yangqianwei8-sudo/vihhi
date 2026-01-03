# Generated manually

from django.db import migrations, models
import django.db.models.deletion
import django.utils.timezone


class Migration(migrations.Migration):

    dependencies = [
        ('production_management', '0006_add_project_number_to_contract'),
    ]

    operations = [
        migrations.CreateModel(
            name='ContractParty',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('party_type', models.CharField(choices=[('party_a', '甲方'), ('party_b', '乙方'), ('party_c', '丙方'), ('other', '其他')], default='party_a', max_length=20, verbose_name='主体类型')),
                ('party_name', models.CharField(max_length=200, verbose_name='主体名称')),
                ('party_contact', models.CharField(blank=True, max_length=100, verbose_name='联系人')),
                ('contact_phone', models.CharField(blank=True, max_length=20, verbose_name='联系电话')),
                ('contact_email', models.EmailField(blank=True, max_length=254, verbose_name='联系邮箱')),
                ('address', models.CharField(blank=True, max_length=500, verbose_name='地址')),
                ('order', models.IntegerField(default=0, help_text='数字越小越靠前', verbose_name='排序')),
                ('is_active', models.BooleanField(default=True, verbose_name='是否启用')),
                ('created_time', models.DateTimeField(default=django.utils.timezone.now, verbose_name='创建时间')),
                ('updated_time', models.DateTimeField(auto_now=True, verbose_name='更新时间')),
                ('contract', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='parties', to='production_management.businesscontract', verbose_name='合同')),
            ],
            options={
                'verbose_name': '合同签约主体',
                'verbose_name_plural': '合同签约主体',
                'db_table': 'contract_party',
                'ordering': ['order', 'id'],
            },
        ),
        migrations.AddIndex(
            model_name='contractparty',
            index=models.Index(fields=['contract', 'is_active'], name='contract_pa_contract_idx'),
        ),
    ]

