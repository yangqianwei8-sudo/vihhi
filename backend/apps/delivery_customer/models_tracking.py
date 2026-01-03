"""
发文跟踪相关模型
"""
from django.db import models
from django.conf import settings
from django.utils import timezone

from .models import OutgoingDocument, DeliveryMethod


class OutgoingDocumentTracking(models.Model):
    """发文跟踪记录模型 - 每种报送方式创建一条独立的跟踪记录"""
    
    # 跟踪状态
    TRACKING_STATUS_CHOICES = [
        ('pending', '待发送'),
        ('sending', '发送中'),
        ('sent', '已发送'),
        ('in_transit', '运输中'),
        ('delivered', '已送达'),
        ('received', '已接收'),
        ('confirmed', '已确认'),
        ('completed', '已完成'),
        ('failed', '发送失败'),
        ('rejected', '已拒收'),
        ('cancelled', '已取消'),
    ]
    
    # 关联发文
    document = models.ForeignKey(
        OutgoingDocument,
        on_delete=models.CASCADE,
        related_name='tracking_records',
        verbose_name='关联发文',
        db_index=True
    )
    
    # 报送方式
    delivery_method = models.ForeignKey(
        DeliveryMethod,
        on_delete=models.PROTECT,
        related_name='tracking_records',
        verbose_name='报送方式',
        db_index=True
    )
    
    # 跟踪状态
    status = models.CharField(
        '跟踪状态',
        max_length=20,
        choices=TRACKING_STATUS_CHOICES,
        default='pending',
        db_index=True
    )
    
    # 邮件相关字段
    email_subject = models.CharField('邮件主题', max_length=500, blank=True)
    email_to = models.EmailField('收件邮箱', max_length=255, blank=True)
    email_sent_at = models.DateTimeField('邮件发送时间', null=True, blank=True)
    email_read_at = models.DateTimeField('邮件阅读时间', null=True, blank=True)
    email_tracking_id = models.CharField('邮件追踪ID', max_length=200, blank=True)
    email_message_id = models.CharField('邮件消息ID', max_length=500, blank=True, help_text='用于邮件跟踪')
    
    # 快递相关字段
    express_company = models.CharField('快递公司', max_length=100, blank=True)
    express_number = models.CharField('快递单号', max_length=100, blank=True, db_index=True)
    express_status = models.CharField('快递状态', max_length=50, blank=True)
    express_last_update = models.DateTimeField('快递状态更新时间', null=True, blank=True)
    express_tracking_data = models.JSONField('快递跟踪数据', default=dict, blank=True, help_text='存储快递100 API返回的完整跟踪数据')
    
    # 现场送达相关字段
    hand_delivery_location = models.CharField('送达地点', max_length=200, blank=True, help_text='GPS定位地址')
    hand_delivery_latitude = models.DecimalField('纬度', max_digits=10, decimal_places=7, null=True, blank=True)
    hand_delivery_longitude = models.DecimalField('经度', max_digits=10, decimal_places=7, null=True, blank=True)
    hand_delivery_photo = models.ImageField('送达照片', upload_to='outgoing_documents/hand_delivery/%Y/%m/%d/', blank=True, null=True)
    hand_delivery_checkin_at = models.DateTimeField('打卡时间', null=True, blank=True)
    hand_delivery_checkin_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='hand_delivery_checkins',
        verbose_name='送达人',
        db_constraint=True
    )
    
    # 易签宝相关字段
    yisign_contract_id = models.CharField('易签宝合同ID', max_length=200, blank=True)
    yisign_contract_url = models.URLField('易签宝合同链接', max_length=500, blank=True)
    yisign_status = models.CharField('易签宝状态', max_length=50, blank=True, help_text='待签、已签、拒绝、过期等')
    yisign_signed_at = models.DateTimeField('易签宝签署时间', null=True, blank=True)
    yisign_signed_by = models.CharField('易签宝签署人', max_length=100, blank=True)
    yisign_callback_data = models.JSONField('易签宝回调数据', default=dict, blank=True, help_text='存储易签宝网站反馈的数据')
    
    # 短信报送相关字段
    sms_phone = models.CharField('收件手机号', max_length=20, blank=True, db_index=True, help_text='接收短信的手机号码')
    sms_content = models.TextField('短信内容', blank=True, help_text='发送的短信内容')
    sms_sent_at = models.DateTimeField('短信发送时间', null=True, blank=True)
    sms_status = models.CharField('短信状态', max_length=50, blank=True, help_text='发送成功、发送失败等')
    sms_message_id = models.CharField('短信消息ID', max_length=200, blank=True, help_text='短信服务商返回的消息ID，用于跟踪')
    sms_callback_data = models.JSONField('短信回调数据', default=dict, blank=True, help_text='存储短信服务商返回的回调数据')
    
    # 通用跟踪信息
    sent_at = models.DateTimeField('发送时间', null=True, blank=True)
    received_at = models.DateTimeField('接收时间', null=True, blank=True)
    confirmed_at = models.DateTimeField('确认时间', null=True, blank=True)
    completed_at = models.DateTimeField('完成时间', null=True, blank=True)
    
    # 异常信息
    error_message = models.TextField('错误信息', blank=True, help_text='发送失败或异常时的错误信息')
    retry_count = models.IntegerField('重试次数', default=0, help_text='发送失败后的重试次数')
    last_retry_at = models.DateTimeField('最后重试时间', null=True, blank=True)
    
    # 备注
    notes = models.TextField('备注', blank=True)
    
    # 时间信息
    created_at = models.DateTimeField('创建时间', auto_now_add=True, db_index=True)
    updated_at = models.DateTimeField('更新时间', auto_now=True)
    created_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        related_name='created_tracking_records',
        verbose_name='创建人',
        db_constraint=True
    )
    
    class Meta:
        db_table = 'outgoing_document_tracking'
        verbose_name = '发文跟踪记录'
        verbose_name_plural = '发文跟踪记录'
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['document', 'delivery_method']),
            models.Index(fields=['status', 'created_at']),
            models.Index(fields=['express_number']),
        ]
        unique_together = [['document', 'delivery_method']]  # 每个发文每种报送方式只能有一条跟踪记录
    
    def __str__(self):
        return f"{self.document.document_number} - {self.delivery_method.name} - {self.get_status_display()}"
    
    def get_status_display_class(self):
        """获取状态对应的CSS类"""
        status_classes = {
            'pending': 'warning',
            'sending': 'info',
            'sent': 'primary',
            'in_transit': 'info',
            'delivered': 'success',
            'received': 'success',
            'confirmed': 'success',
            'completed': 'success',
            'failed': 'danger',
            'rejected': 'danger',
            'cancelled': 'secondary',
        }
        return status_classes.get(self.status, 'secondary')

