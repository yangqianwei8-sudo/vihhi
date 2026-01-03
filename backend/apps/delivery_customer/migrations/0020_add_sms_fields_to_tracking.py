# Generated migration to add SMS fields to OutgoingDocumentTracking
# 为发文跟踪记录添加短信相关字段

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('delivery_customer', '0019_add_sms_delivery_method'),
    ]

    operations = [
        migrations.AddField(
            model_name='outgoingdocumenttracking',
            name='sms_phone',
            field=models.CharField(blank=True, db_index=True, help_text='接收短信的手机号码', max_length=20, verbose_name='收件手机号'),
        ),
        migrations.AddField(
            model_name='outgoingdocumenttracking',
            name='sms_content',
            field=models.TextField(blank=True, help_text='发送的短信内容', verbose_name='短信内容'),
        ),
        migrations.AddField(
            model_name='outgoingdocumenttracking',
            name='sms_sent_at',
            field=models.DateTimeField(blank=True, help_text='短信发送时间', null=True, verbose_name='短信发送时间'),
        ),
        migrations.AddField(
            model_name='outgoingdocumenttracking',
            name='sms_status',
            field=models.CharField(blank=True, help_text='发送成功、发送失败等', max_length=50, verbose_name='短信状态'),
        ),
        migrations.AddField(
            model_name='outgoingdocumenttracking',
            name='sms_message_id',
            field=models.CharField(blank=True, help_text='短信服务商返回的消息ID，用于跟踪', max_length=200, verbose_name='短信消息ID'),
        ),
        migrations.AddField(
            model_name='outgoingdocumenttracking',
            name='sms_callback_data',
            field=models.JSONField(blank=True, default=dict, help_text='存储短信服务商返回的回调数据', verbose_name='短信回调数据'),
        ),
    ]

