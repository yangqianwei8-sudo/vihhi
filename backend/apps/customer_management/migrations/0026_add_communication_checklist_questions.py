# Generated manually for communication checklist questions management

from django.conf import settings
from django.db import migrations, models
import django.db.models.deletion
import django.utils.timezone


class Migration(migrations.Migration):

    dependencies = [
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
        ('customer_management', '0025_add_communication_checklist'),
    ]

    operations = [
        migrations.CreateModel(
            name='CommunicationChecklistQuestion',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('part', models.CharField(choices=[('part1', '第一部分：客户与项目背景信息'), ('part2', '第二部分：沟通目标与内容准备'), ('part3', '第三部分：沟通策略与风险预案'), ('part4', '第四部分：后勤与状态')], max_length=20, verbose_name='所属部分')),
                ('order', models.IntegerField(help_text='同一部分内的问题排序，数字越小越靠前', verbose_name='排序序号')),
                ('question_text', models.CharField(max_length=500, verbose_name='问题内容')),
                ('question_code', models.CharField(help_text='用于标识问题的唯一代码，如 part1_q1_client_info', max_length=50, unique=True, verbose_name='问题代码')),
                ('is_active', models.BooleanField(default=True, verbose_name='是否启用')),
                ('created_time', models.DateTimeField(default=django.utils.timezone.now, verbose_name='创建时间')),
                ('updated_time', models.DateTimeField(auto_now=True, verbose_name='更新时间')),
            ],
            options={
                'verbose_name': '沟通清单问题模板',
                'verbose_name_plural': '沟通清单问题模板',
                'db_table': 'communication_checklist_question',
                'ordering': ['part', 'order'],
            },
        ),
        migrations.CreateModel(
            name='CommunicationChecklistAnswer',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('answer', models.CharField(choices=[('yes', '是'), ('no', '否'), ('unknown', '不清楚')], default='unknown', max_length=20, verbose_name='答案')),
                ('note_before', models.TextField(blank=True, verbose_name='沟通前说明')),
                ('note_after', models.TextField(blank=True, verbose_name='沟通后说明')),
                ('created_time', models.DateTimeField(default=django.utils.timezone.now, verbose_name='创建时间')),
                ('updated_time', models.DateTimeField(auto_now=True, verbose_name='更新时间')),
                ('checklist', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='answers', to='customer_management.customercommunicationchecklist', verbose_name='关联清单')),
                ('question', models.ForeignKey(on_delete=django.db.models.deletion.PROTECT, related_name='answers', to='customer_management.communicationchecklistquestion', verbose_name='关联问题')),
            ],
            options={
                'verbose_name': '沟通清单答案',
                'verbose_name_plural': '沟通清单答案',
                'db_table': 'communication_checklist_answer',
                'unique_together': {('checklist', 'question')},
            },
        ),
        migrations.AddIndex(
            model_name='communicationchecklistquestion',
            index=models.Index(fields=['part', 'order'], name='comm_check_q_part_order_idx'),
        ),
        migrations.AddIndex(
            model_name='communicationchecklistquestion',
            index=models.Index(fields=['is_active'], name='comm_check_q_is_active_idx'),
        ),
        migrations.AddIndex(
            model_name='communicationchecklistanswer',
            index=models.Index(fields=['checklist', 'question'], name='comm_check_a_checklist_question_idx'),
        ),
    ]

