# Generated manually for settlement_center output value models

from django.conf import settings
from django.db import migrations, models
import django.db.models.deletion
import django.utils.timezone


class Migration(migrations.Migration):

    initial = True

    dependencies = [
        ('production_management', '0001_initial'),
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
    ]

    operations = [
        migrations.CreateModel(
            name='OutputValueStage',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('name', models.CharField(max_length=100, verbose_name='阶段名称')),
                ('code', models.CharField(max_length=50, unique=True, verbose_name='阶段编码')),
                ('stage_type', models.CharField(choices=[('conversion', '转化阶段'), ('contract', '合同阶段'), ('production', '生产阶段'), ('settlement', '结算阶段'), ('payment', '回款阶段'), ('after_sales', '售后阶段')], max_length=20, verbose_name='阶段类型')),
                ('stage_percentage', models.DecimalField(decimal_places=2, help_text='该阶段占总产值的比例', max_digits=5, verbose_name='阶段产值比例(%)')),
                ('base_amount_type', models.CharField(choices=[('registration_amount', '备案金额'), ('intention_amount', '意向金额'), ('contract_amount', '合同金额'), ('settlement_amount', '结算金额'), ('payment_amount', '回款金额')], max_length=30, verbose_name='计取基数类型')),
                ('description', models.TextField(blank=True, verbose_name='阶段描述')),
                ('order', models.IntegerField(default=0, verbose_name='排序')),
                ('is_active', models.BooleanField(default=True, verbose_name='是否启用')),
                ('created_time', models.DateTimeField(default=django.utils.timezone.now, verbose_name='创建时间')),
                ('updated_time', models.DateTimeField(auto_now=True, verbose_name='更新时间')),
            ],
            options={
                'verbose_name': '产值阶段',
                'verbose_name_plural': '产值阶段',
                'db_table': 'settlement_output_value_stage',
                'ordering': ['order', 'created_time'],
            },
        ),
        migrations.CreateModel(
            name='OutputValueMilestone',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('name', models.CharField(max_length=100, verbose_name='里程碑名称')),
                ('code', models.CharField(max_length=50, verbose_name='里程碑编码')),
                ('milestone_percentage', models.DecimalField(decimal_places=2, help_text='该里程碑在该阶段内的比例', max_digits=5, verbose_name='里程碑产值比例(%)')),
                ('description', models.TextField(blank=True, verbose_name='里程碑描述')),
                ('order', models.IntegerField(default=0, verbose_name='排序')),
                ('is_active', models.BooleanField(default=True, verbose_name='是否启用')),
                ('created_time', models.DateTimeField(default=django.utils.timezone.now, verbose_name='创建时间')),
                ('updated_time', models.DateTimeField(auto_now=True, verbose_name='更新时间')),
                ('stage', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='milestones', to='settlement_center.outputvaluestage', verbose_name='所属阶段')),
            ],
            options={
                'verbose_name': '产值里程碑',
                'verbose_name_plural': '产值里程碑',
                'db_table': 'settlement_output_value_milestone',
                'ordering': ['order', 'created_time'],
                'unique_together': {('stage', 'code')},
            },
        ),
        migrations.CreateModel(
            name='OutputValueEvent',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('name', models.CharField(max_length=100, verbose_name='事件名称')),
                ('code', models.CharField(max_length=50, verbose_name='事件编码')),
                ('event_percentage', models.DecimalField(decimal_places=2, help_text='该事件在该里程碑内的比例', max_digits=5, verbose_name='事件产值比例(%)')),
                ('responsible_role_code', models.CharField(help_text='如：business_manager, project_manager, professional_engineer等', max_length=50, verbose_name='责任岗位编码')),
                ('description', models.TextField(blank=True, verbose_name='事件描述')),
                ('trigger_condition', models.CharField(blank=True, help_text='关联项目流程事件的标识，用于自动触发产值计算', max_length=200, verbose_name='触发条件')),
                ('order', models.IntegerField(default=0, verbose_name='排序')),
                ('is_active', models.BooleanField(default=True, verbose_name='是否启用')),
                ('created_time', models.DateTimeField(default=django.utils.timezone.now, verbose_name='创建时间')),
                ('updated_time', models.DateTimeField(auto_now=True, verbose_name='更新时间')),
                ('milestone', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='events', to='settlement_center.outputvaluemilestone', verbose_name='所属里程碑')),
            ],
            options={
                'verbose_name': '产值事件',
                'verbose_name_plural': '产值事件',
                'db_table': 'settlement_output_value_event',
                'ordering': ['order', 'created_time'],
                'unique_together': {('milestone', 'code')},
            },
        ),
        migrations.CreateModel(
            name='OutputValueRecord',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('base_amount', models.DecimalField(decimal_places=2, max_digits=12, verbose_name='计取基数')),
                ('base_amount_type', models.CharField(max_length=30, verbose_name='基数类型')),
                ('stage_percentage', models.DecimalField(decimal_places=2, max_digits=5, verbose_name='阶段比例(%)')),
                ('milestone_percentage', models.DecimalField(decimal_places=2, max_digits=5, verbose_name='里程碑比例(%)')),
                ('event_percentage', models.DecimalField(decimal_places=2, max_digits=5, verbose_name='事件比例(%)')),
                ('calculated_value', models.DecimalField(decimal_places=2, max_digits=12, verbose_name='计算产值')),
                ('status', models.CharField(choices=[('pending', '待计算'), ('calculated', '已计算'), ('confirmed', '已确认'), ('cancelled', '已取消')], default='calculated', max_length=20, verbose_name='状态')),
                ('calculated_time', models.DateTimeField(default=django.utils.timezone.now, verbose_name='计算时间')),
                ('confirmed_time', models.DateTimeField(blank=True, null=True, verbose_name='确认时间')),
                ('notes', models.TextField(blank=True, verbose_name='备注')),
                ('created_time', models.DateTimeField(default=django.utils.timezone.now, verbose_name='创建时间')),
                ('event', models.ForeignKey(on_delete=django.db.models.deletion.PROTECT, to='settlement_center.outputvalueevent', verbose_name='产值事件')),
                ('milestone', models.ForeignKey(on_delete=django.db.models.deletion.PROTECT, to='settlement_center.outputvaluemilestone', verbose_name='产值里程碑')),
                ('project', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='output_value_records', to='production_management.project', verbose_name='关联项目')),
                ('responsible_user', models.ForeignKey(on_delete=django.db.models.deletion.PROTECT, related_name='output_value_records', to=settings.AUTH_USER_MODEL, verbose_name='责任人')),
                ('stage', models.ForeignKey(on_delete=django.db.models.deletion.PROTECT, to='settlement_center.outputvaluestage', verbose_name='产值阶段')),
                ('confirmed_by', models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='confirmed_output_values', to=settings.AUTH_USER_MODEL, verbose_name='确认人')),
            ],
            options={
                'verbose_name': '产值计算记录',
                'verbose_name_plural': '产值计算记录',
                'db_table': 'settlement_output_value_record',
                'ordering': ['-calculated_time'],
            },
        ),
        migrations.AddIndex(
            model_name='outputvaluerecord',
            index=models.Index(fields=['project', 'status'], name='settlement__project_c8d1e8_idx'),
        ),
        migrations.AddIndex(
            model_name='outputvaluerecord',
            index=models.Index(fields=['responsible_user', 'status'], name='settlement__respons_fb41b4_idx'),
        ),
        migrations.AddIndex(
            model_name='outputvaluerecord',
            index=models.Index(fields=['calculated_time'], name='settlement__calcula_3f6c51_idx'),
        ),
    ]
