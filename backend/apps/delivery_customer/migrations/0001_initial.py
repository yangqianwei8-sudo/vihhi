# Generated migration file for delivery_customer app

from django.conf import settings
from django.db import migrations, models
import django.db.models.deletion
import django.core.validators
import backend.apps.delivery_customer.models


class Migration(migrations.Migration):

    initial = True

    dependencies = [
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
        ('production_management', '0001_initial'),
        ('customer_management', '0001_initial_squashed_0015_remove_client_blacklist_details_remove_client_code_and_more'),
    ]

    operations = [
        migrations.CreateModel(
            name='DeliveryRecord',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('delivery_number', models.CharField(db_index=True, max_length=50, unique=True, verbose_name='交付单号')),
                ('title', models.CharField(max_length=200, verbose_name='交付标题')),
                ('description', models.TextField(blank=True, verbose_name='交付说明')),
                ('delivery_method', models.CharField(choices=[('email', '邮件'), ('express', '快递'), ('hand_delivery', '送达')], default='email', max_length=20, verbose_name='交付方式')),
                ('recipient_name', models.CharField(max_length=100, verbose_name='收件人姓名')),
                ('recipient_phone', models.CharField(blank=True, max_length=20, verbose_name='收件人电话')),
                ('recipient_email', models.EmailField(blank=True, max_length=255, verbose_name='收件人邮箱')),
                ('recipient_address', models.TextField(blank=True, help_text='快递/送达时使用', verbose_name='收件地址')),
                ('cc_emails', models.TextField(blank=True, help_text='多个邮箱用逗号分隔', verbose_name='抄送邮箱')),
                ('bcc_emails', models.TextField(blank=True, help_text='多个邮箱用逗号分隔', verbose_name='密送邮箱')),
                ('email_subject', models.CharField(blank=True, max_length=500, verbose_name='邮件主题')),
                ('email_message', models.TextField(blank=True, help_text='支持HTML格式', verbose_name='邮件正文')),
                ('use_template', models.BooleanField(default=True, verbose_name='使用模板')),
                ('template_name', models.CharField(blank=True, max_length=100, verbose_name='模板名称')),
                ('express_company', models.CharField(blank=True, help_text='如：顺丰、圆通等', max_length=100, verbose_name='快递公司')),
                ('express_number', models.CharField(blank=True, db_index=True, max_length=100, verbose_name='快递单号')),
                ('express_fee', models.DecimalField(blank=True, decimal_places=2, max_digits=10, null=True, verbose_name='快递费用')),
                ('delivery_notes', models.TextField(blank=True, verbose_name='送达备注')),
                ('status', models.CharField(choices=[('draft', '草稿'), ('submitted', '已报送'), ('in_transit', '运输中'), ('delivered', '已送达'), ('sent', '已发送'), ('received', '已接收'), ('confirmed', '已确认'), ('feedback_received', '已反馈'), ('archived', '已归档'), ('failed', '发送失败'), ('cancelled', '已取消'), ('overdue', '已逾期')], db_index=True, default='draft', max_length=20, verbose_name='状态')),
                ('priority', models.CharField(choices=[('low', '低'), ('normal', '普通'), ('high', '高'), ('urgent', '紧急')], default='normal', max_length=20, verbose_name='优先级')),
                ('scheduled_delivery_time', models.DateTimeField(blank=True, null=True, verbose_name='计划交付时间')),
                ('submitted_at', models.DateTimeField(blank=True, null=True, verbose_name='报送时间')),
                ('sent_at', models.DateTimeField(blank=True, null=True, verbose_name='发送时间')),
                ('delivered_at', models.DateTimeField(blank=True, null=True, verbose_name='送达时间')),
                ('received_at', models.DateTimeField(blank=True, null=True, verbose_name='接收时间')),
                ('confirmed_at', models.DateTimeField(blank=True, null=True, verbose_name='确认时间')),
                ('archived_at', models.DateTimeField(blank=True, null=True, verbose_name='归档时间')),
                ('deadline', models.DateTimeField(blank=True, db_index=True, help_text='交付截止日期，用于逾期判断', null=True, verbose_name='交付期限')),
                ('created_at', models.DateTimeField(auto_now_add=True, db_index=True, verbose_name='创建时间')),
                ('updated_at', models.DateTimeField(auto_now=True, verbose_name='更新时间')),
                ('error_message', models.TextField(blank=True, verbose_name='错误信息')),
                ('retry_count', models.IntegerField(default=0, verbose_name='重试次数')),
                ('max_retries', models.IntegerField(default=3, verbose_name='最大重试次数')),
                ('feedback_received', models.BooleanField(default=False, verbose_name='已收到反馈')),
                ('feedback_content', models.TextField(blank=True, verbose_name='反馈内容')),
                ('feedback_time', models.DateTimeField(blank=True, null=True, verbose_name='反馈时间')),
                ('feedback_by', models.CharField(blank=True, max_length=100, verbose_name='反馈人')),
                ('auto_archive_enabled', models.BooleanField(default=True, verbose_name='自动归档')),
                ('archive_condition', models.CharField(choices=[('confirmed', '客户确认后'), ('feedback_received', '收到反馈后'), ('days_after_delivered', '送达后N天')], default='confirmed', max_length=50, verbose_name='归档条件')),
                ('archive_days', models.IntegerField(default=7, verbose_name='归档天数')),
                ('is_overdue', models.BooleanField(db_index=True, default=False, verbose_name='是否逾期')),
                ('overdue_days', models.IntegerField(default=0, verbose_name='逾期天数')),
                ('risk_level', models.CharField(blank=True, choices=[('low', '低风险'), ('medium', '中风险'), ('high', '高风险'), ('critical', '严重风险')], default='low', max_length=20, verbose_name='风险等级')),
                ('warning_sent', models.BooleanField(default=False, verbose_name='已发送预警')),
                ('warning_times', models.IntegerField(default=0, verbose_name='预警次数')),
                ('file_count', models.IntegerField(default=0, verbose_name='文件数量')),
                ('total_file_size', models.BigIntegerField(default=0, verbose_name='文件总大小(字节)')),
                ('notes', models.TextField(blank=True, verbose_name='备注')),
                ('client', models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='delivery_records', to='customer_management.client', verbose_name='关联客户')),
                ('created_by', models.ForeignKey(null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='created_deliveries', to=settings.AUTH_USER_MODEL, verbose_name='创建人')),
                ('delivery_person', models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='hand_delivered_records', to=settings.AUTH_USER_MODEL, verbose_name='送达人')),
                ('project', models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='delivery_records', to='production_management.project', verbose_name='关联项目')),
                ('sent_by', models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='sent_deliveries', to=settings.AUTH_USER_MODEL, verbose_name='发送人')),
            ],
            options={
                'verbose_name': '交付记录',
                'verbose_name_plural': '交付记录',
                'db_table': 'delivery_record',
                'ordering': ['-created_at'],
            },
        ),
        migrations.CreateModel(
            name='DeliveryFile',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('file', models.FileField(max_length=500, upload_to=backend.apps.delivery_customer.models.delivery_file_upload_path, validators=[django.core.validators.FileExtensionValidator(allowed_extensions=['pdf', 'doc', 'docx', 'xls', 'xlsx', 'ppt', 'pptx', 'dwg', 'dgn', 'jpg', 'jpeg', 'png', 'zip', 'rar', '7z'])], verbose_name='文件')),
                ('file_name', models.CharField(max_length=255, verbose_name='原始文件名')),
                ('file_type', models.CharField(choices=[('report', '报告'), ('drawing', '图纸'), ('document', '文档'), ('data', '数据文件'), ('image', '图片'), ('other', '其他')], default='other', max_length=20, verbose_name='文件类型')),
                ('file_size', models.BigIntegerField(verbose_name='文件大小(字节)')),
                ('file_extension', models.CharField(blank=True, max_length=20, verbose_name='文件扩展名')),
                ('mime_type', models.CharField(blank=True, max_length=100, verbose_name='MIME类型')),
                ('description', models.CharField(blank=True, max_length=500, verbose_name='文件描述')),
                ('version', models.CharField(blank=True, max_length=50, verbose_name='版本号')),
                ('uploaded_at', models.DateTimeField(auto_now_add=True, db_index=True, verbose_name='上传时间')),
                ('is_deleted', models.BooleanField(default=False, verbose_name='已删除')),
                ('deleted_at', models.DateTimeField(blank=True, null=True, verbose_name='删除时间')),
                ('delivery_record', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='files', to='delivery_customer.deliveryrecord', verbose_name='交付记录')),
                ('uploaded_by', models.ForeignKey(null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='uploaded_delivery_files', to=settings.AUTH_USER_MODEL, verbose_name='上传人')),
            ],
            options={
                'verbose_name': '交付文件',
                'verbose_name_plural': '交付文件',
                'db_table': 'delivery_file',
                'ordering': ['uploaded_at'],
            },
        ),
        migrations.CreateModel(
            name='DeliveryFeedback',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('feedback_type', models.CharField(choices=[('received', '已接收'), ('confirmed', '已确认'), ('question', '有疑问'), ('revision', '需要修改'), ('approved', '已批准'), ('rejected', '已拒绝')], max_length=20, verbose_name='反馈类型')),
                ('content', models.TextField(verbose_name='反馈内容')),
                ('feedback_by', models.CharField(max_length=100, verbose_name='反馈人')),
                ('feedback_email', models.EmailField(blank=True, max_length=254, verbose_name='反馈人邮箱')),
                ('feedback_phone', models.CharField(blank=True, max_length=20, verbose_name='反馈人电话')),
                ('created_at', models.DateTimeField(auto_now_add=True, db_index=True, verbose_name='反馈时间')),
                ('is_read', models.BooleanField(default=False, verbose_name='已读')),
                ('read_at', models.DateTimeField(blank=True, null=True, verbose_name='阅读时间')),
                ('delivery_record', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='feedbacks', to='delivery_customer.deliveryrecord', verbose_name='交付记录')),
                ('read_by', models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='read_feedbacks', to=settings.AUTH_USER_MODEL, verbose_name='阅读人')),
            ],
            options={
                'verbose_name': '交付反馈',
                'verbose_name_plural': '交付反馈',
                'db_table': 'delivery_feedback',
                'ordering': ['-created_at'],
            },
        ),
        migrations.CreateModel(
            name='DeliveryTracking',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('event_type', models.CharField(choices=[('submitted', '已报送'), ('sent', '已发送/已寄出'), ('in_transit', '运输中'), ('out_for_delivery', '派送中'), ('delivered', '已送达'), ('received', '已接收'), ('confirmed', '已确认'), ('feedback', '收到反馈'), ('archived', '已归档')], max_length=20, verbose_name='事件类型')),
                ('event_description', models.CharField(max_length=500, verbose_name='事件描述')),
                ('location', models.CharField(blank=True, help_text='快递跟踪时使用', max_length=200, verbose_name='位置')),
                ('event_time', models.DateTimeField(auto_now_add=True, db_index=True, verbose_name='事件时间')),
                ('notes', models.TextField(blank=True, verbose_name='备注')),
                ('delivery_record', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='tracking_records', to='delivery_customer.deliveryrecord', verbose_name='交付记录')),
                ('operator', models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='tracking_operations', to=settings.AUTH_USER_MODEL, verbose_name='操作人')),
            ],
            options={
                'verbose_name': '交付跟踪记录',
                'verbose_name_plural': '交付跟踪记录',
                'db_table': 'delivery_tracking',
                'ordering': ['-event_time'],
            },
        ),
        migrations.AddIndex(
            model_name='deliverytracking',
            index=models.Index(fields=['delivery_record', '-event_time'], name='delivery_tr_deliver_idx'),
        ),
        migrations.AddIndex(
            model_name='deliveryrecord',
            index=models.Index(fields=['status', '-created_at'], name='delivery_re_status_idx'),
        ),
        migrations.AddIndex(
            model_name='deliveryrecord',
            index=models.Index(fields=['project', '-created_at'], name='delivery_re_project_idx'),
        ),
        migrations.AddIndex(
            model_name='deliveryrecord',
            index=models.Index(fields=['client', '-created_at'], name='delivery_re_client_idx'),
        ),
        migrations.AddIndex(
            model_name='deliveryrecord',
            index=models.Index(fields=['is_overdue', 'risk_level'], name='delivery_re_is_over_idx'),
        ),
        migrations.AddIndex(
            model_name='deliveryfile',
            index=models.Index(fields=['delivery_record', 'uploaded_at'], name='delivery_fi_deliver_idx'),
        ),
        migrations.AddIndex(
            model_name='deliveryfeedback',
            index=models.Index(fields=['delivery_record', '-created_at'], name='delivery_fe_deliver_idx'),
        ),
    ]
