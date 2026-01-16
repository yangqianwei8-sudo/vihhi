# Generated manually for litigation_management

from django.conf import settings
from django.db import migrations, models
import django.db.models.deletion
import django.utils.timezone


class Migration(migrations.Migration):

    initial = True

    dependencies = [
        ('customer_management', '0001_initial_squashed_0015_remove_client_blacklist_details_remove_client_code_and_more'),
        ('production_management', '0001_initial'),
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
    ]

    operations = [
        migrations.CreateModel(
            name='LitigationCase',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('case_number', models.CharField(db_index=True, max_length=50, unique=True, verbose_name='案件编号')),
                ('case_name', models.CharField(max_length=200, verbose_name='案件名称')),
                ('case_type', models.CharField(choices=[('contract_dispute', '合同纠纷'), ('labor_dispute', '劳动争议'), ('ip_dispute', '知识产权'), ('tort_dispute', '侵权纠纷'), ('other', '其他纠纷')], max_length=20, verbose_name='案件类型')),
                ('case_nature', models.CharField(choices=[('plaintiff', '原告'), ('defendant', '被告'), ('third_party', '第三人'), ('other', '其他')], max_length=20, verbose_name='案件性质')),
                ('description', models.TextField(blank=True, verbose_name='案件描述')),
                ('litigation_amount', models.DecimalField(blank=True, decimal_places=2, help_text='诉讼请求的金额', max_digits=15, null=True, verbose_name='诉讼标的额')),
                ('dispute_amount', models.DecimalField(blank=True, decimal_places=2, help_text='实际争议的金额', max_digits=15, null=True, verbose_name='争议金额')),
                ('status', models.CharField(choices=[('pending_filing', '待立案'), ('filed', '已立案'), ('trial', '审理中'), ('judged', '已判决'), ('executing', '执行中'), ('closed', '已结案'), ('withdrawn', '已撤诉'), ('settled', '已和解')], default='pending_filing', max_length=20, verbose_name='案件状态')),
                ('priority', models.CharField(choices=[('low', '低'), ('medium', '中'), ('high', '高'), ('urgent', '紧急')], default='medium', max_length=10, verbose_name='优先级')),
                ('registration_date', models.DateField(default=django.utils.timezone.now, verbose_name='登记日期')),
                ('filing_date', models.DateField(blank=True, null=True, verbose_name='立案日期')),
                ('trial_date', models.DateField(blank=True, null=True, verbose_name='开庭日期')),
                ('judgment_date', models.DateField(blank=True, null=True, verbose_name='判决日期')),
                ('execution_date', models.DateField(blank=True, null=True, verbose_name='执行日期')),
                ('closing_date', models.DateField(blank=True, null=True, verbose_name='结案日期')),
                ('created_at', models.DateTimeField(auto_now_add=True, verbose_name='创建时间')),
                ('updated_at', models.DateTimeField(auto_now=True, verbose_name='更新时间')),
                ('case_manager', models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='managed_litigation_cases', to=settings.AUTH_USER_MODEL, verbose_name='案件负责人')),
                ('client', models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='litigation_cases', to='customer_management.client', verbose_name='关联客户')),
                ('contract', models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='litigation_cases', to='production_management.businesscontract', verbose_name='关联合同')),
                ('project', models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='litigation_cases', to='production_management.project', verbose_name='关联项目')),
                ('registered_by', models.ForeignKey(null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='registered_litigation_cases', to=settings.AUTH_USER_MODEL, verbose_name='登记人')),
                ('registered_department', models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='litigation_cases', to='system_management.department', verbose_name='登记部门')),
            ],
            options={
                'verbose_name': '诉讼案件',
                'verbose_name_plural': '诉讼案件',
                'db_table': 'litigation_case',
                'ordering': ['-registration_date', '-created_at'],
            },
        ),
        migrations.AddIndex(
            model_name='litigationcase',
            index=models.Index(fields=['case_number'], name='litigation__case_nu_idx'),
        ),
        migrations.AddIndex(
            model_name='litigationcase',
            index=models.Index(fields=['status'], name='litigation__status_idx'),
        ),
        migrations.AddIndex(
            model_name='litigationcase',
            index=models.Index(fields=['case_type'], name='litigation__case_ty_idx'),
        ),
        migrations.AddIndex(
            model_name='litigationcase',
            index=models.Index(fields=['priority'], name='litigation__priorit_idx'),
        ),
        migrations.AddIndex(
            model_name='litigationcase',
            index=models.Index(fields=['registration_date'], name='litigation__registr_idx'),
        ),
    ]

