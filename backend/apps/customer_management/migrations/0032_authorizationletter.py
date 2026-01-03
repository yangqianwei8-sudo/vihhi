# Generated manually for AuthorizationLetter model

from django.conf import settings
from django.db import migrations, models
import django.db.models.deletion
import django.utils.timezone


class Migration(migrations.Migration):

    dependencies = [
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
        ('customer_management', '0031_remove_customercommunicationchecklist_client_and_more'),
        ('permission_management', '0001_initial'),  # 确保permission_management已初始化
        ('production_management', '0001_initial'),  # 使用具体迁移名称，避免__first__解析问题
    ]

    operations = [
        migrations.CreateModel(
            name='AuthorizationLetter',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('letter_number', models.CharField(blank=True, help_text='自动生成：VIH-AUTH-YYYY-NNNN', max_length=50, null=True, unique=True, verbose_name='委托书编号')),
                ('project_name', models.CharField(max_length=200, verbose_name='项目名称')),
                ('provisional_price', models.DecimalField(blank=True, decimal_places=2, max_digits=15, null=True, verbose_name='暂定价款（元）')),
                ('letter_date', models.DateField(default=django.utils.timezone.now, verbose_name='委托日期')),
                ('status', models.CharField(choices=[('draft', '草稿'), ('submitted', '已提交'), ('confirmed', '已确认'), ('cancelled', '已作废')], default='draft', max_length=20, verbose_name='委托书状态')),
                ('client_name', models.CharField(max_length=200, verbose_name='单位名称')),
                ('client_representative', models.CharField(blank=True, max_length=100, verbose_name='单位代表')),
                ('client_phone', models.CharField(blank=True, max_length=50, verbose_name='联系电话')),
                ('client_email', models.EmailField(blank=True, max_length=254, verbose_name='电子邮箱')),
                ('client_address', models.CharField(blank=True, max_length=500, verbose_name='收件地址')),
                ('trustee_name', models.CharField(default='四川维海科技有限公司', max_length=200, verbose_name='服务单位')),
                ('trustee_representative', models.CharField(blank=True, help_text='例如：田霞', max_length=100, verbose_name='单位代表')),
                ('trustee_phone', models.CharField(blank=True, help_text='例如：13666287899/02883574973', max_length=50, verbose_name='联系电话')),
                ('trustee_email', models.EmailField(blank=True, help_text='例如：whkj@vihgroup.com.cn', max_length=254, verbose_name='电子邮箱')),
                ('trustee_address', models.CharField(blank=True, help_text='例如：四川省成都市武侯区武科西一路瑞景产业园1号楼5A01', max_length=500, verbose_name='收件地址')),
                ('design_stages', models.JSONField(blank=True, default=list, help_text='方案阶段、施工图阶段、施工阶段', verbose_name='设计阶段')),
                ('result_optimization_scopes', models.JSONField(blank=True, default=list, verbose_name='结果优化范围')),
                ('process_optimization_scopes', models.JSONField(blank=True, default=list, verbose_name='过程优化范围')),
                ('detailed_review_scopes', models.JSONField(blank=True, default=list, verbose_name='精细化审图范围')),
                ('result_optimization_rate', models.DecimalField(blank=True, decimal_places=2, help_text='10-15%', max_digits=5, null=True, verbose_name='结果优化费率（%）')),
                ('process_optimization_rate', models.DecimalField(blank=True, decimal_places=2, help_text='10-15%', max_digits=5, null=True, verbose_name='过程优化费率（%）')),
                ('detailed_review_unit_price_min', models.DecimalField(blank=True, decimal_places=2, help_text='1.5元/平方米', max_digits=10, null=True, verbose_name='精细化审图单价下限（元/平方米）')),
                ('detailed_review_unit_price_max', models.DecimalField(blank=True, decimal_places=2, help_text='3.0元/平方米', max_digits=10, null=True, verbose_name='精细化审图单价上限（元/平方米）')),
                ('fee_determination_principle', models.TextField(blank=True, verbose_name='服务费确定原则说明')),
                ('settlement_review_process', models.TextField(blank=True, verbose_name='结算审核流程说明')),
                ('payment_schedule', models.JSONField(blank=True, default=dict, help_text='三阶段付款：20%、30%、100%', verbose_name='付款计划')),
                ('supplementary_agreement', models.TextField(blank=True, verbose_name='补充约定')),
                ('start_date', models.DateField(blank=True, null=True, verbose_name='开始日期')),
                ('end_date', models.DateField(blank=True, null=True, verbose_name='结束日期')),
                ('duration_days', models.IntegerField(blank=True, help_text='自动计算', null=True, verbose_name='委托期限（天）')),
                ('notes', models.TextField(blank=True, verbose_name='备注')),
                ('created_time', models.DateTimeField(default=django.utils.timezone.now, verbose_name='创建时间')),
                ('updated_time', models.DateTimeField(auto_now=True, verbose_name='更新时间')),
                ('created_by', models.ForeignKey(on_delete=django.db.models.deletion.PROTECT, related_name='created_authorization_letters', to=settings.AUTH_USER_MODEL, verbose_name='创建人')),
                ('opportunity', models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='authorization_letters', to='customer_management.businessopportunity', verbose_name='关联商机')),
                ('project', models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='authorization_letters', to='production_management.project', verbose_name='关联项目')),
            ],
            options={
                'verbose_name': '业务委托书',
                'verbose_name_plural': '业务委托书',
                'db_table': 'business_authorization_letter',
                'ordering': ['-created_time'],
            },
        ),
        migrations.AddIndex(
            model_name='authorizationletter',
            index=models.Index(fields=['letter_number'], name='business_au_letter__idx'),
        ),
        migrations.AddIndex(
            model_name='authorizationletter',
            index=models.Index(fields=['status'], name='business_au_status_idx'),
        ),
        migrations.AddIndex(
            model_name='authorizationletter',
            index=models.Index(fields=['client_name'], name='business_au_client__idx'),
        ),
        migrations.AddIndex(
            model_name='authorizationletter',
            index=models.Index(fields=['opportunity'], name='business_au_opportun_idx'),
        ),
        migrations.AddIndex(
            model_name='authorizationletter',
            index=models.Index(fields=['letter_date'], name='business_au_letter__idx2'),
        ),
    ]

