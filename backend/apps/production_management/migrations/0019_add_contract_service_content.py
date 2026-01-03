# Generated migration for ContractServiceContent

from django.db import migrations, models
import django.db.models.deletion
import django.utils.timezone


class Migration(migrations.Migration):

    dependencies = [
        ('production_management', '0018_add_settlement_and_after_sales_node_types'),
    ]

    operations = [
        migrations.CreateModel(
            name='ContractServiceContent',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('building_area', models.DecimalField(blank=True, decimal_places=2, max_digits=12, null=True, verbose_name='建筑面积（㎡）')),
                ('description', models.TextField(blank=True, verbose_name='服务内容描述')),
                ('order', models.IntegerField(default=0, help_text='数字越小越靠前', verbose_name='排序')),
                ('is_active', models.BooleanField(default=True, verbose_name='是否启用')),
                ('created_time', models.DateTimeField(default=django.utils.timezone.now, verbose_name='创建时间')),
                ('updated_time', models.DateTimeField(auto_now=True, verbose_name='更新时间')),
                ('business_type', models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='contract_service_contents', to='production_management.businesstype', verbose_name='项目业态')),
                ('contract', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='service_contents', to='production_management.businesscontract', verbose_name='合同')),
                ('design_stage', models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='contract_service_contents', to='production_management.designstage', verbose_name='图纸阶段')),
                ('service_type', models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='contract_service_contents', to='production_management.servicetype', verbose_name='服务类型')),
            ],
            options={
                'verbose_name': '合同服务内容',
                'verbose_name_plural': '合同服务内容',
                'db_table': 'contract_service_content',
                'ordering': ['order', 'id'],
            },
        ),
        migrations.AddIndex(
            model_name='contractservicecontent',
            index=models.Index(fields=['contract', 'is_active'], name='contract_se_contract_idx'),
        ),
        migrations.AddField(
            model_name='contractservicecontent',
            name='service_professions',
            field=models.ManyToManyField(blank=True, related_name='contract_service_contents', to='production_management.serviceprofession', verbose_name='服务专业'),
        ),
    ]

