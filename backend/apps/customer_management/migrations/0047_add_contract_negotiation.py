# Generated migration for ContractNegotiation model

from django.conf import settings
from django.db import migrations, models
import django.db.models.deletion
import django.utils.timezone


class Migration(migrations.Migration):

    dependencies = [
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
        ('customer_management', '0046_add_contact_info_change'),
        ('production_management', '0001_initial'),
    ]

    operations = [
        migrations.CreateModel(
            name='ContractNegotiation',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('negotiation_number', models.CharField(blank=True, help_text='自动生成：NT-YYYY-NNNN', max_length=100, null=True, unique=True, verbose_name='洽谈编号')),
                ('negotiation_type', models.CharField(choices=[('price', '价格洽谈'), ('terms', '条款洽谈'), ('schedule', '进度洽谈'), ('payment', '付款方式洽谈'), ('other', '其他洽谈')], default='other', max_length=20, verbose_name='洽谈类型')),
                ('status', models.CharField(choices=[('ongoing', '进行中'), ('completed', '已完成'), ('suspended', '已暂停'), ('cancelled', '已取消')], default='ongoing', max_length=20, verbose_name='洽谈状态')),
                ('title', models.CharField(max_length=200, verbose_name='洽谈主题')),
                ('content', models.TextField(help_text='详细记录洽谈过程中的讨论内容、双方意见等', verbose_name='洽谈内容')),
                ('client_participants', models.TextField(blank=True, help_text='客户方参与洽谈的人员，多个用逗号分隔', verbose_name='客户参与人员')),
                ('negotiation_date', models.DateField(default=django.utils.timezone.now, verbose_name='洽谈日期')),
                ('negotiation_start_time', models.TimeField(blank=True, null=True, verbose_name='开始时间')),
                ('negotiation_end_time', models.TimeField(blank=True, null=True, verbose_name='结束时间')),
                ('next_negotiation_date', models.DateField(blank=True, null=True, verbose_name='下次洽谈日期')),
                ('result_summary', models.TextField(blank=True, help_text='本次洽谈达成的共识、待解决问题等', verbose_name='洽谈结果摘要')),
                ('agreed_items', models.TextField(blank=True, help_text='双方已达成一致的事项', verbose_name='已达成事项')),
                ('pending_items', models.TextField(blank=True, help_text='需要进一步讨论或解决的问题', verbose_name='待解决事项')),
                ('attachments', models.TextField(blank=True, help_text='洽谈过程中涉及的文档、资料等', verbose_name='附件说明')),
                ('notes', models.TextField(blank=True, verbose_name='备注')),
                ('created_time', models.DateTimeField(default=django.utils.timezone.now, verbose_name='创建时间')),
                ('updated_time', models.DateTimeField(auto_now=True, verbose_name='更新时间')),
                ('client', models.ForeignKey(blank=True, help_text='如果未关联合同，则必须填写客户', null=True, on_delete=django.db.models.deletion.PROTECT, related_name='contract_negotiations', to='customer_management.client', verbose_name='客户')),
                ('contract', models.ForeignKey(blank=True, help_text='可选，如果洽谈时合同尚未创建可留空', null=True, on_delete=django.db.models.deletion.CASCADE, related_name='negotiations', to='production_management.businesscontract', verbose_name='关联合同')),
                ('created_by', models.ForeignKey(on_delete=django.db.models.deletion.PROTECT, related_name='created_contract_negotiations', to=settings.AUTH_USER_MODEL, verbose_name='创建人')),
                ('participants', models.ManyToManyField(related_name='participated_negotiations', to=settings.AUTH_USER_MODEL, verbose_name='参与人员')),
                ('project', models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='contract_negotiations', to='production_management.project', verbose_name='关联项目')),
            ],
            options={
                'verbose_name': '合同洽谈记录',
                'verbose_name_plural': '合同洽谈记录',
                'db_table': 'business_contract_negotiation',
                'ordering': ['-negotiation_date', '-created_time'],
            },
        ),
        migrations.AddIndex(
            model_name='contractnegotiation',
            index=models.Index(fields=['contract'], name='business_co_contrac_idx'),
        ),
        migrations.AddIndex(
            model_name='contractnegotiation',
            index=models.Index(fields=['client'], name='business_co_client_idx'),
        ),
        migrations.AddIndex(
            model_name='contractnegotiation',
            index=models.Index(fields=['negotiation_date'], name='business_co_negotia_idx'),
        ),
        migrations.AddIndex(
            model_name='contractnegotiation',
            index=models.Index(fields=['status'], name='business_co_status_idx'),
        ),
    ]

