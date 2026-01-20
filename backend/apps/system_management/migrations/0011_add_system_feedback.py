# Generated manually

from django.db import migrations, models
import django.db.models.deletion
import django.utils.timezone


class Migration(migrations.Migration):

    dependencies = [
        ('system_management', '0010_remove_role_user_type'),
    ]

    operations = [
        migrations.CreateModel(
            name='SystemFeedback',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('feedback_type', models.CharField(choices=[('bug', '问题报告'), ('suggestion', '功能建议'), ('complaint', '投诉建议'), ('praise', '表扬反馈'), ('other', '其他')], max_length=20, verbose_name='反馈类型')),
                ('title', models.CharField(max_length=200, verbose_name='反馈标题')),
                ('content', models.TextField(verbose_name='反馈内容')),
                ('submitted_at', models.DateTimeField(auto_now_add=True, db_index=True, verbose_name='提交时间')),
                ('status', models.CharField(choices=[('pending', '待处理'), ('processing', '处理中'), ('resolved', '已解决'), ('closed', '已关闭')], db_index=True, default='pending', max_length=20, verbose_name='处理状态')),
                ('processed_at', models.DateTimeField(blank=True, null=True, verbose_name='处理时间')),
                ('process_comment', models.TextField(blank=True, verbose_name='处理意见')),
                ('attachment', models.FileField(blank=True, null=True, upload_to='feedback_attachments/%Y/%m/', verbose_name='附件')),
                ('priority', models.CharField(choices=[('low', '低'), ('medium', '中'), ('high', '高'), ('urgent', '紧急')], default='medium', max_length=10, verbose_name='优先级')),
                ('related_module', models.CharField(blank=True, max_length=50, verbose_name='关联模块')),
                ('related_url', models.URLField(blank=True, verbose_name='关联页面')),
                ('processed_by', models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='processed_feedbacks', to='system_management.user', verbose_name='处理人')),
                ('submitted_by', models.ForeignKey(null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='submitted_feedbacks', to='system_management.user', verbose_name='提交人')),
            ],
            options={
                'verbose_name': '系统反馈',
                'verbose_name_plural': '系统反馈',
                'db_table': 'system_feedback',
                'ordering': ['-submitted_at'],
            },
        ),
        migrations.AddIndex(
            model_name='systemfeedback',
            index=models.Index(fields=['status', '-submitted_at'], name='system_fee_status_8a3f2d_idx'),
        ),
        migrations.AddIndex(
            model_name='systemfeedback',
            index=models.Index(fields=['submitted_by', '-submitted_at'], name='system_fee_submitt_9c4e5f_idx'),
        ),
        migrations.AddIndex(
            model_name='systemfeedback',
            index=models.Index(fields=['feedback_type', '-submitted_at'], name='system_fee_feedbac_7b8d9e_idx'),
        ),
    ]
