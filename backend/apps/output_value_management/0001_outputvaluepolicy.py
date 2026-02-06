# 请将此文件移动到 migrations/ 目录下并重命名为 0001_outputvaluepolicy.py 后执行 makemigrations/migrate
# 若 migrations 目录不存在，请先创建：mkdir -p backend/apps/output_value_management/migrations

from django.db import migrations, models
import django.db.models.deletion
import django.utils.timezone


class Migration(migrations.Migration):

    initial = True

    dependencies = [
        ('system_management', '0016_role_company_unique_code'),
    ]

    operations = [
        migrations.CreateModel(
            name='OutputValuePolicy',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('name', models.CharField(default='V1 默认口径', max_length=100, verbose_name='口径名称')),
                ('service_type_weights', models.JSONField(default=dict, help_text='JSON：{ "转化阶段": "0.02", "conversion": "0.02", ... }，绝对折算率', verbose_name='服务类型权重')),
                ('stage_weight', models.DecimalField(decimal_places=4, default='1.0', max_digits=10, help_text='V1 默认 1.0', verbose_name='阶段权重')),
                ('event_modifier_min', models.DecimalField(decimal_places=4, default='0.2', max_digits=10, verbose_name='事件修正系数下限')),
                ('event_modifier_max', models.DecimalField(decimal_places=4, default='1.2', max_digits=10, verbose_name='事件修正系数上限')),
                ('confidence_high_threshold', models.DecimalField(decimal_places=4, default='0.30', max_digits=10, help_text='milestone_weight >= 此值视为 high', verbose_name='confidence 高阈值')),
                ('enabled', models.BooleanField(default=True, verbose_name='是否生效')),
                ('effective_from', models.DateTimeField(blank=True, null=True, verbose_name='生效起始时间（可选）')),
                ('updated_at', models.DateTimeField(auto_now=True, verbose_name='更新时间')),
                ('created_at', models.DateTimeField(default=django.utils.timezone.now, verbose_name='创建时间')),
                ('updated_by', models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='+', to='system_management.user', verbose_name='最后修改人')),
            ],
            options={
                'verbose_name': '产值口径配置',
                'verbose_name_plural': '产值口径配置',
                'db_table': 'output_value_policy',
                'ordering': ['-updated_at'],
            },
        ),
        migrations.AddConstraint(
            model_name='outputvaluepolicy',
            constraint=models.UniqueConstraint(condition=models.Q(('enabled', True)), fields=('enabled',), name='output_value_policy_single_enabled'),
        ),
    ]
