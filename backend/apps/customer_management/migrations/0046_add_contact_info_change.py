# Generated manually

from django.conf import settings
from django.db import migrations, models
import django.db.models.deletion
import django.utils.timezone


class Migration(migrations.Migration):

    dependencies = [
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
        ('workflow_engine', '0001_initial'),
        ('customer_management', '0045_add_business_expense_application'),
    ]

    operations = [
        migrations.CreateModel(
            name='ContactInfoChange',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('change_type', models.CharField(choices=[('basic_info', '基本信息'), ('contact_info', '联系方式'), ('career_info', '职业信息'), ('education_info', '教育信息'), ('relationship_info', '关系信息'), ('other', '其他信息')], max_length=30, verbose_name='变更类型')),
                ('change_reason', models.TextField(help_text='请说明变更的原因和依据', verbose_name='变更原因')),
                ('change_content', models.JSONField(default=dict, help_text='存储变更的字段和对应的旧值、新值', verbose_name='变更内容')),
                ('approval_status', models.CharField(choices=[('draft', '草稿'), ('pending', '待审批'), ('approved', '已通过'), ('rejected', '已驳回'), ('withdrawn', '已撤回')], default='draft', max_length=20, verbose_name='审批状态')),
                ('created_time', models.DateTimeField(default=django.utils.timezone.now, verbose_name='创建时间')),
                ('approved_time', models.DateTimeField(blank=True, null=True, verbose_name='审批通过时间')),
                ('updated_time', models.DateTimeField(auto_now=True, verbose_name='更新时间')),
                ('approval_instance', models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='contact_info_changes', to='workflow_engine.approvalinstance', verbose_name='审批实例')),
                ('contact', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='info_changes', to='customer_management.clientcontact', verbose_name='关联联系人')),
                ('created_by', models.ForeignKey(on_delete=django.db.models.deletion.PROTECT, related_name='created_contact_info_changes', to=settings.AUTH_USER_MODEL, verbose_name='创建人')),
            ],
            options={
                'verbose_name': '人员信息变更申请',
                'verbose_name_plural': '人员信息变更申请',
                'db_table': 'customer_contact_info_change',
                'ordering': ['-created_time'],
            },
        ),
        migrations.AddIndex(
            model_name='contactinfochange',
            index=models.Index(fields=['contact', 'approval_status'], name='customer_co_contact_6a8f5a_idx'),
        ),
        migrations.AddIndex(
            model_name='contactinfochange',
            index=models.Index(fields=['change_type'], name='customer_co_change__a1b2c3_idx'),
        ),
        migrations.AddIndex(
            model_name='contactinfochange',
            index=models.Index(fields=['created_time'], name='customer_co_created_4d5e6f_idx'),
        ),
    ]

