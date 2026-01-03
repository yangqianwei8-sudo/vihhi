# Generated manually
# 
# 注意：此迁移由于迁移依赖链问题，表已通过SQL直接创建
# 表：customer_business_expense_application
# 
# 如果需要回滚，执行：
# DROP TABLE IF EXISTS customer_business_expense_application_related_contacts;
# DROP TABLE IF EXISTS customer_business_expense_application;
# DELETE FROM django_migrations WHERE app = 'customer_management' AND name = '0045_add_business_expense_application';

from django.db import migrations, models
import django.db.models.deletion
import django.core.validators
from django.conf import settings


class Migration(migrations.Migration):

    dependencies = [
        ('customer_management', '0044_add_tracking_cycle_days'),
        ('workflow_engine', '0001_initial'),
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
    ]

    operations = [
        migrations.CreateModel(
            name='BusinessExpenseApplication',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('application_number', models.CharField(help_text='自动生成', max_length=100, unique=True, verbose_name='申请单号')),
                ('expense_type', models.CharField(choices=[('entertainment', '招待费'), ('gift', '礼品费'), ('travel', '差旅费'), ('meal', '餐费'), ('transportation', '交通费'), ('communication', '通讯费'), ('other', '其他费用')], max_length=30, verbose_name='费用类型')),
                ('amount', models.DecimalField(decimal_places=2, max_digits=12, validators=[django.core.validators.MinValueValidator(0.01)], verbose_name='费用金额')),
                ('expense_date', models.DateField(verbose_name='费用发生日期')),
                ('description', models.TextField(verbose_name='费用说明')),
                ('attachment', models.FileField(blank=True, help_text='支持上传发票、凭证等', null=True, upload_to='business_expenses/%Y/%m/', verbose_name='附件')),
                ('approval_status', models.CharField(choices=[('draft', '草稿'), ('pending', '待审批'), ('approved', '已通过'), ('rejected', '已驳回'), ('withdrawn', '已撤回')], default='draft', max_length=20, verbose_name='审批状态')),
                ('created_time', models.DateTimeField(auto_now_add=True, verbose_name='创建时间')),
                ('approved_time', models.DateTimeField(blank=True, null=True, verbose_name='审批通过时间')),
                ('updated_time', models.DateTimeField(auto_now=True, verbose_name='更新时间')),
                ('approval_instance', models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='business_expense_applications', to='workflow_engine.approvalinstance', verbose_name='审批实例')),
                ('client', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='business_expense_applications', to='customer_management.client', verbose_name='关联客户')),
                ('created_by', models.ForeignKey(on_delete=django.db.models.deletion.PROTECT, related_name='created_business_expense_applications', to=settings.AUTH_USER_MODEL, verbose_name='创建人')),
            ],
            options={
                'verbose_name': '业务费申请',
                'verbose_name_plural': '业务费申请',
                'db_table': 'customer_business_expense_application',
                'ordering': ['-created_time'],
            },
        ),
        migrations.CreateModel(
            name='BusinessExpenseApplicationRelatedContacts',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('businessexpenseapplication', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='customer_management.businessexpenseapplication')),
                ('clientcontact', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='customer_management.clientcontact')),
            ],
            options={
                'db_table': 'customer_business_expense_application_related_contacts',
            },
        ),
        migrations.AddIndex(
            model_name='businessexpenseapplication',
            index=models.Index(fields=['client', 'approval_status'], name='customer_bu_client__idx'),
        ),
        migrations.AddIndex(
            model_name='businessexpenseapplication',
            index=models.Index(fields=['expense_date'], name='customer_bu_expense__idx'),
        ),
        migrations.AddIndex(
            model_name='businessexpenseapplication',
            index=models.Index(fields=['application_number'], name='customer_bu_applica_idx'),
        ),
        migrations.AddField(
            model_name='businessexpenseapplication',
            name='related_contacts',
            field=models.ManyToManyField(blank=True, related_name='business_expense_applications', to='customer_management.clientcontact', verbose_name='关联的客户人员'),
        ),
    ]

