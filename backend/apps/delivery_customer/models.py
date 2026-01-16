from django.db import models
from django.conf import settings
from django.core.validators import FileExtensionValidator
from django.utils import timezone
import os

from backend.apps.production_management.models import Project
from backend.apps.customer_management.models import Client, ClientContact


def delivery_file_upload_path(instance, filename):
    """文件上传路径"""
    date_path = instance.uploaded_at.strftime('%Y/%m/%d') if instance.uploaded_at else 'unknown'
    return f'delivery_files/{date_path}/{instance.delivery_record.delivery_number}/{filename}'


class DeliveryRecord(models.Model):
    """交付记录模型"""
    
    # 交付方式
    DELIVERY_METHOD_CHOICES = [
        ('email', '邮件'),
        ('express', '快递'),
        ('hand_delivery', '送达'),
    ]
    
    # 交付状态
    STATUS_CHOICES = [
        ('draft', '草稿'),
        ('submitted', '已报送'),
        ('pending_approval', '待审核'),
        ('approving', '审核中'),
        ('approved', '审核通过'),
        ('rejected', '审核驳回'),
        ('in_transit', '运输中'),
        ('delivered', '已送达'),
        ('sent', '已发送'),
        ('received', '已接收'),
        ('confirmed', '已确认'),
        ('feedback_received', '已反馈'),
        ('archived', '已归档'),
        ('failed', '发送失败'),
        ('cancelled', '已取消'),
        ('overdue', '已逾期'),
    ]
    
    PRIORITY_CHOICES = [
        ('low', '低'),
        ('normal', '普通'),
        ('high', '高'),
        ('urgent', '紧急'),
    ]
    
    # 基本信息
    delivery_number = models.CharField('交付单号', max_length=50, unique=True, db_index=True)
    title = models.CharField('交付标题', max_length=200)
    description = models.TextField('交付说明', blank=True)
    
    # 交付方式
    delivery_method = models.CharField(
        max_length=20, 
        choices=DELIVERY_METHOD_CHOICES, 
        default='email',
        verbose_name='交付方式'
    )
    
    # 关联信息
    project = models.ForeignKey(
        Project, 
        on_delete=models.SET_NULL, 
        null=True, 
        blank=True,
        related_name='delivery_records',
        verbose_name='关联项目',
        db_constraint=True
    )
    client = models.ForeignKey(
        Client,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='delivery_records',
        verbose_name='关联客户',
        db_constraint=True
    )
    
    # 收件人信息（通用）
    recipient_name = models.CharField('收件人姓名', max_length=100)
    recipient_phone = models.CharField('收件人电话', max_length=20, blank=True)
    recipient_email = models.EmailField('收件人邮箱', max_length=255, blank=True)
    recipient_address = models.TextField('收件地址', blank=True, help_text='快递/送达时使用')
    
    # 邮件相关（仅邮件交付方式使用）
    cc_emails = models.TextField('抄送邮箱', blank=True, help_text='多个邮箱用逗号分隔')
    bcc_emails = models.TextField('密送邮箱', blank=True, help_text='多个邮箱用逗号分隔')
    email_subject = models.CharField('邮件主题', max_length=500, blank=True)
    email_message = models.TextField('邮件正文', blank=True, help_text='支持HTML格式')
    use_template = models.BooleanField('使用模板', default=True)
    template_name = models.CharField('模板名称', max_length=100, blank=True)
    
    # 快递相关（仅快递交付方式使用）
    express_company = models.CharField('快递公司', max_length=100, blank=True, help_text='如：顺丰、圆通等')
    express_number = models.CharField('快递单号', max_length=100, blank=True, db_index=True)
    express_fee = models.DecimalField('快递费用', max_digits=10, decimal_places=2, null=True, blank=True)
    
    # 送达相关（仅送达交付方式使用）
    delivery_person = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='hand_delivered_records',
        verbose_name='送达人',
        db_constraint=True
    )
    delivery_notes = models.TextField('送达备注', blank=True)
    
    # 状态信息
    status = models.CharField('状态', max_length=20, choices=STATUS_CHOICES, default='draft', db_index=True)
    priority = models.CharField('优先级', max_length=20, choices=PRIORITY_CHOICES, default='normal')
    
    # 时间信息
    scheduled_delivery_time = models.DateTimeField('计划交付时间', null=True, blank=True)
    submitted_at = models.DateTimeField('报送时间', null=True, blank=True)
    sent_at = models.DateTimeField('发送时间', null=True, blank=True)
    delivered_at = models.DateTimeField('送达时间', null=True, blank=True)
    received_at = models.DateTimeField('接收时间', null=True, blank=True)
    confirmed_at = models.DateTimeField('确认时间', null=True, blank=True)
    archived_at = models.DateTimeField('归档时间', null=True, blank=True)
    deadline = models.DateTimeField('交付期限', null=True, blank=True, db_index=True, help_text='交付截止日期，用于逾期判断')
    created_at = models.DateTimeField('创建时间', auto_now_add=True, db_index=True)
    updated_at = models.DateTimeField('更新时间', auto_now=True)
    
    # 操作人信息
    created_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        related_name='created_deliveries',
        verbose_name='创建人',
        db_constraint=True
    )
    sent_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='sent_deliveries',
        verbose_name='发送人',
        db_constraint=True
    )
    
    # 错误信息
    error_message = models.TextField('错误信息', blank=True)
    retry_count = models.IntegerField('重试次数', default=0)
    max_retries = models.IntegerField('最大重试次数', default=3)
    
    # 反馈信息
    feedback_received = models.BooleanField('已收到反馈', default=False)
    feedback_content = models.TextField('反馈内容', blank=True)
    feedback_time = models.DateTimeField('反馈时间', null=True, blank=True)
    feedback_by = models.CharField('反馈人', max_length=100, blank=True)
    
    # 归档信息
    auto_archive_enabled = models.BooleanField('自动归档', default=True)
    archive_condition = models.CharField(
        '归档条件', 
        max_length=50, 
        default='confirmed',
        choices=[
            ('confirmed', '客户确认后'),
            ('feedback_received', '收到反馈后'),
            ('days_after_delivered', '送达后N天'),
        ],
    )
    archive_days = models.IntegerField('归档天数', default=7)
    
    # 风险预警
    is_overdue = models.BooleanField('是否逾期', default=False, db_index=True)
    overdue_days = models.IntegerField('逾期天数', default=0)
    risk_level = models.CharField(
        '风险等级',
        max_length=20,
        choices=[
            ('low', '低风险'),
            ('medium', '中风险'),
            ('high', '高风险'),
            ('critical', '严重风险'),
        ],
        default='low',
        blank=True
    )
    warning_sent = models.BooleanField('已发送预警', default=False)
    warning_times = models.IntegerField('预警次数', default=0)
    
    # 统计信息
    file_count = models.IntegerField('文件数量', default=0)
    total_file_size = models.BigIntegerField('文件总大小(字节)', default=0)
    
    # 备注
    notes = models.TextField('备注', blank=True)
    
    class Meta:
        db_table = 'delivery_record'
        verbose_name = '交付记录'
        verbose_name_plural = '交付记录'
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['status', '-created_at']),
            models.Index(fields=['project', '-created_at']),
            models.Index(fields=['client', '-created_at']),
            models.Index(fields=['delivery_number']),
            models.Index(fields=['is_overdue', 'risk_level']),
            models.Index(fields=['deadline']),
        ]
    
    def __str__(self):
        return f"{self.delivery_number} - {self.title}"
    
    def generate_delivery_number(self):
        """生成交付单号：VIH-JF-{YYYYMMDD}-{序列号}"""
        from django.db import transaction
        from django.db.models import Max
        
        prefix = 'VIH-JF'
        date_str = timezone.now().strftime('%Y%m%d')
        pattern = f"{prefix}-{date_str}-"
        
        # 使用事务和锁确保线程安全
        with transaction.atomic():
            # 获取当天最大序列号
            max_number = DeliveryRecord.objects.filter(
                delivery_number__startswith=pattern
            ).aggregate(max_num=Max('delivery_number'))['max_num']
            
            if max_number:
                # 提取序列号并加1
                try:
                    seq = int(max_number.split('-')[-1]) + 1
                except (ValueError, IndexError):
                    seq = 1
            else:
                seq = 1
            
            return f"{pattern}{seq:04d}"
    
    def save(self, *args, **kwargs):
        if not self.delivery_number:
            self.delivery_number = self.generate_delivery_number()
        
        # 优化：只在 deadline 或 status 变化时检查逾期
        need_check_overdue = True
        if self.pk:
            try:
                old = DeliveryRecord.objects.get(pk=self.pk)
                # 如果 deadline 和 status 都没有变化，跳过逾期检查
                if (old.deadline == self.deadline and 
                    old.status == self.status and 
                    old.is_overdue == self.is_overdue):
                    need_check_overdue = False
            except DeliveryRecord.DoesNotExist:
                pass
        
        # 检查是否逾期
        if need_check_overdue and self.deadline and self.status not in ['archived', 'confirmed', 'cancelled']:
            now = timezone.now()
            if now > self.deadline:
                self.is_overdue = True
                delta = now - self.deadline
                self.overdue_days = delta.days
                
                # 计算风险等级
                if self.overdue_days <= 3:
                    self.risk_level = 'low'
                elif self.overdue_days <= 7:
                    self.risk_level = 'medium'
                elif self.overdue_days <= 15:
                    self.risk_level = 'high'
                else:
                    self.risk_level = 'critical'
                
                if self.status != 'overdue':
                    self.status = 'overdue'
            else:
                self.is_overdue = False
                self.overdue_days = 0
                self.risk_level = 'low'
        
        super().save(*args, **kwargs)
    
    def check_auto_archive(self):
        """检查是否满足自动归档条件"""
        if not self.auto_archive_enabled or self.status == 'archived':
            return False
        
        if self.archive_condition == 'confirmed' and self.status == 'confirmed':
            return True
        elif self.archive_condition == 'feedback_received' and self.feedback_received:
            return True
        elif self.archive_condition == 'days_after_delivered' and self.delivered_at:
            days_passed = (timezone.now() - self.delivered_at).days
            if days_passed >= self.archive_days:
                return True
        
        return False
    
    def archive(self):
        """归档交付记录"""
        self.status = 'archived'
        self.archived_at = timezone.now()
        self.save()


class DeliveryFile(models.Model):
    """交付文件模型"""
    
    FILE_TYPE_CHOICES = [
        ('report', '报告'),
        ('drawing', '图纸'),
        ('document', '文档'),
        ('data', '数据文件'),
        ('image', '图片'),
        ('other', '其他'),
    ]
    
    # 关联信息
    delivery_record = models.ForeignKey(
        DeliveryRecord,
        on_delete=models.CASCADE,
        related_name='files',
        verbose_name='交付记录',
        db_constraint=True
    )
    
    # 文件信息
    file = models.FileField(
        '文件',
        upload_to=delivery_file_upload_path,
        validators=[
            FileExtensionValidator(
                allowed_extensions=['pdf', 'doc', 'docx', 'xls', 'xlsx', 'ppt', 'pptx', 
                                  'dwg', 'dgn', 'jpg', 'jpeg', 'png', 'zip', 'rar', '7z']
            )
        ],
        max_length=500
    )
    file_name = models.CharField('原始文件名', max_length=255)
    file_type = models.CharField('文件类型', max_length=20, choices=FILE_TYPE_CHOICES, default='other')
    file_size = models.BigIntegerField('文件大小(字节)')
    file_extension = models.CharField('文件扩展名', max_length=20, blank=True)
    mime_type = models.CharField('MIME类型', max_length=100, blank=True)
    
    # 文件描述
    description = models.CharField('文件描述', max_length=500, blank=True)
    version = models.CharField('版本号', max_length=50, blank=True)
    
    # 时间信息
    uploaded_at = models.DateTimeField('上传时间', auto_now_add=True, db_index=True)
    uploaded_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        related_name='uploaded_delivery_files',
        verbose_name='上传人',
        db_constraint=True
    )
    
    # 文件状态
    is_deleted = models.BooleanField('已删除', default=False)
    deleted_at = models.DateTimeField('删除时间', null=True, blank=True)
    
    class Meta:
        db_table = 'delivery_file'
        verbose_name = '交付文件'
        verbose_name_plural = '交付文件'
        ordering = ['uploaded_at']
        indexes = [
            models.Index(fields=['delivery_record', 'uploaded_at']),
        ]
    
    def __str__(self):
        return f"{self.file_name} ({self.delivery_record.delivery_number})"
    
    def get_file_size_display(self):
        """格式化文件大小"""
        size = self.file_size
        for unit in ['B', 'KB', 'MB', 'GB']:
            if size < 1024.0:
                return f"{size:.2f} {unit}"
            size /= 1024.0
        return f"{size:.2f} TB"
    
    def save(self, *args, **kwargs):
        if self.file:
            self.file_size = self.file.size
            self.file_extension = os.path.splitext(self.file_name)[1][1:].lower()
        super().save(*args, **kwargs)


class DeliveryFeedback(models.Model):
    """交付反馈模型"""
    
    FEEDBACK_TYPE_CHOICES = [
        ('received', '已接收'),
        ('confirmed', '已确认'),
        ('question', '有疑问'),
        ('revision', '需要修改'),
        ('approved', '已批准'),
        ('rejected', '已拒绝'),
    ]
    
    delivery_record = models.ForeignKey(
        DeliveryRecord,
        on_delete=models.CASCADE,
        related_name='feedbacks',
        verbose_name='交付记录',
        db_constraint=True
    )
    
    feedback_type = models.CharField('反馈类型', max_length=20, choices=FEEDBACK_TYPE_CHOICES)
    content = models.TextField('反馈内容')
    feedback_by = models.CharField('反馈人', max_length=100)
    feedback_email = models.EmailField('反馈人邮箱', blank=True)
    feedback_phone = models.CharField('反馈人电话', max_length=20, blank=True)
    
    created_at = models.DateTimeField('反馈时间', auto_now_add=True, db_index=True)
    is_read = models.BooleanField('已读', default=False)
    read_at = models.DateTimeField('阅读时间', null=True, blank=True)
    read_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='read_feedbacks',
        verbose_name='阅读人',
        db_constraint=True
    )
    
    class Meta:
        db_table = 'delivery_feedback'
        verbose_name = '交付反馈'
        verbose_name_plural = '交付反馈'
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['delivery_record', '-created_at']),
        ]
    
    def __str__(self):
        return f"{self.delivery_record.delivery_number} - {self.get_feedback_type_display()}"


class DeliveryTracking(models.Model):
    """交付跟踪记录模型"""
    
    TRACKING_EVENT_CHOICES = [
        ('submitted', '已报送'),
        ('sent', '已发送/已寄出'),
        ('in_transit', '运输中'),
        ('out_for_delivery', '派送中'),
        ('delivered', '已送达'),
        ('received', '已接收'),
        ('confirmed', '已确认'),
        ('feedback', '收到反馈'),
        ('archived', '已归档'),
    ]
    
    delivery_record = models.ForeignKey(
        DeliveryRecord,
        on_delete=models.CASCADE,
        related_name='tracking_records',
        verbose_name='交付记录',
        db_constraint=True
    )
    
    event_type = models.CharField('事件类型', max_length=20, choices=TRACKING_EVENT_CHOICES)
    event_description = models.CharField('事件描述', max_length=500)
    location = models.CharField('位置', max_length=200, blank=True, help_text='快递跟踪时使用')
    operator = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='tracking_operations',
        verbose_name='操作人',
        db_constraint=True
    )
    event_time = models.DateTimeField('事件时间', auto_now_add=True, db_index=True)
    notes = models.TextField('备注', blank=True)
    
    class Meta:
        db_table = 'delivery_tracking'
        verbose_name = '交付跟踪记录'
        verbose_name_plural = '交付跟踪记录'
        ordering = ['-event_time']
        indexes = [
            models.Index(fields=['delivery_record', '-event_time']),
        ]
    
    def __str__(self):
        return f"{self.delivery_record.delivery_number} - {self.get_event_type_display()}"


class DeliveryApproval(models.Model):
    """交付审核模型"""
    
    APPROVAL_RESULT_CHOICES = [
        ('pending', '待审核'),
        ('approved', '审核通过'),
        ('rejected', '审核驳回'),
    ]
    
    delivery_record = models.ForeignKey(
        DeliveryRecord,
        on_delete=models.CASCADE,
        related_name='approvals',
        verbose_name='交付记录',
        db_constraint=True
    )
    
    approver = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        related_name='delivery_approvals',
        verbose_name='审核人',
        db_constraint=True
    )
    
    approval_level = models.IntegerField('审核级别', default=1, help_text='多级审核时使用，数字越大级别越高')
    result = models.CharField(
        '审核结果',
        max_length=20,
        choices=APPROVAL_RESULT_CHOICES,
        default='pending',
        db_index=True
    )
    
    comment = models.TextField('审核意见', blank=True)
    
    approval_time = models.DateTimeField('审核时间', null=True, blank=True, db_index=True)
    created_at = models.DateTimeField('创建时间', auto_now_add=True, db_index=True)
    
    # 转交相关
    transferred_from = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='delivery_transferred_approvals',
        verbose_name='转交人',
        db_constraint=True
    )
    transferred_to = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='received_approvals',
        verbose_name='转交至',
        db_constraint=True
    )
    
    class Meta:
        db_table = 'delivery_approval'
        verbose_name = '交付审核'
        verbose_name_plural = '交付审核'
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['delivery_record', '-created_at']),
            models.Index(fields=['approver', '-created_at']),
            models.Index(fields=['result', '-created_at']),
        ]
    
    def __str__(self):
        return f"{self.delivery_record.delivery_number} - {self.get_result_display()}"


class ExpressCompany(models.Model):
    """快递公司模型"""
    
    # 基本信息
    name = models.CharField('快递公司名称', max_length=100, unique=True, db_index=True, help_text='如：顺丰、圆通等')
    code = models.CharField('快递公司代码', max_length=50, blank=True, help_text='快递100等API使用的代码')
    alias = models.CharField('别名', max_length=200, blank=True, help_text='多个别名用逗号分隔，如：顺丰速运,SF')
    
    # 联系方式
    contact_phone = models.CharField('联系电话', max_length=20, blank=True)
    contact_email = models.EmailField('联系邮箱', max_length=255, blank=True)
    website = models.URLField('官网', max_length=255, blank=True)
    
    # 状态信息
    is_active = models.BooleanField('是否启用', default=True, db_index=True, help_text='禁用后不会在创建交付时显示')
    is_default = models.BooleanField('是否默认', default=False, help_text='设为默认后，创建快递交付时自动选中')
    
    # 排序
    sort_order = models.IntegerField('排序', default=0, db_index=True, help_text='数字越小越靠前')
    
    # 备注
    notes = models.TextField('备注', blank=True)
    
    # 时间信息
    created_at = models.DateTimeField('创建时间', auto_now_add=True, db_index=True)
    updated_at = models.DateTimeField('更新时间', auto_now=True)
    created_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        related_name='created_express_companies',
        verbose_name='创建人',
        db_constraint=True
    )
    
    class Meta:
        db_table = 'express_company'
        verbose_name = '快递公司'
        verbose_name_plural = '快递公司'
        ordering = ['sort_order', 'name']
        indexes = [
            models.Index(fields=['is_active', 'sort_order']),
            models.Index(fields=['is_default', '-created_at']),
        ]
    
    def __str__(self):
        return self.name
    
    def get_aliases_list(self):
        """获取别名列表"""
        if not self.alias:
            return []
        return [a.strip() for a in self.alias.split(',') if a.strip()]
    
    def get_company_code(self):
        """获取快递公司代码（用于API查询）"""
        if self.code:
            return self.code
        # 如果没有设置代码，尝试从express_service中获取
        from .express_service import ExpressQueryService
        return ExpressQueryService.get_company_code(self.name)


class IncomingDocument(models.Model):
    """收文模型"""
    
    STATUS_CHOICES = [
        ('draft', '草稿'),
        ('registered', '已登记'),
        ('processing', '处理中'),
        ('completed', '已完成'),
        ('archived', '已归档'),
    ]
    
    PRIORITY_CHOICES = [
        ('low', '低'),
        ('normal', '普通'),
        ('high', '高'),
        ('urgent', '紧急'),
    ]
    
    STAGE_CHOICES = [
        ('conversion', '转化阶段'),
        ('contract', '合同阶段'),
        ('production', '生产阶段'),
        ('settlement', '结算阶段'),
        ('payment', '回款阶段'),
        ('after_sales', '售后阶段'),
        ('litigation', '诉讼阶段'),
    ]
    
    # 基本信息
    document_number = models.CharField('收文编号', max_length=50, unique=True, db_index=True)
    title = models.CharField('文件标题', max_length=200)
    sender = models.CharField('发文单位', max_length=200)
    sender_contact = models.CharField('联系人', max_length=100, blank=True)
    sender_phone = models.CharField('联系电话', max_length=20, blank=True)
    
    # 文件信息
    document_date = models.DateField('文件日期', null=True, blank=True)
    receive_date = models.DateField('收文日期', null=True, blank=True)
    document_type = models.CharField('文件类型', max_length=50, blank=True)
    
    # 内容
    content = models.TextField('文件内容', blank=True)
    summary = models.TextField('摘要', blank=True)
    
    # 状态和优先级
    status = models.CharField('状态', max_length=20, choices=STATUS_CHOICES, default='draft', db_index=True)
    priority = models.CharField('优先级', max_length=20, choices=PRIORITY_CHOICES, default='normal')
    
    # 阶段和文件分类
    stage = models.CharField('阶段', max_length=20, choices=STAGE_CHOICES, blank=True, null=True, db_index=True, help_text='文件所属阶段')
    file_category = models.ForeignKey(
        'FileCategory',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='incoming_documents',
        verbose_name='文件分类',
        help_text='关联的文件分类',
        db_constraint=True
    )
    
    # 处理信息
    handler = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='handled_incoming_documents',
        verbose_name='处理人',
        db_constraint=True
    )
    handle_notes = models.TextField('处理意见', blank=True)
    completed_at = models.DateTimeField('完成时间', null=True, blank=True)
    
    # 附件
    attachment = models.FileField('附件', upload_to='incoming_documents/%Y/%m/%d/', blank=True, null=True)
    
    # 备注
    notes = models.TextField('备注', blank=True)
    
    # 时间信息
    created_at = models.DateTimeField('创建时间', auto_now_add=True, db_index=True)
    updated_at = models.DateTimeField('更新时间', auto_now=True)
    created_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        related_name='created_incoming_documents',
        verbose_name='创建人',
        db_constraint=True
    )
    
    class Meta:
        db_table = 'incoming_document'
        verbose_name = '收文'
        verbose_name_plural = '收文'
        ordering = ['-receive_date', '-created_at']
        indexes = [
            models.Index(fields=['status', '-receive_date']),
            models.Index(fields=['handler', '-created_at']),
            models.Index(fields=['stage']),
        ]
    
    def __str__(self):
        return f"{self.document_number} - {self.title}"


class OutgoingDocument(models.Model):
    """发文模型"""
    
    STATUS_CHOICES = [
        ('draft', '草稿'),
        ('reviewing', '审核中'),
        ('approved', '已批准'),
        ('sent', '已发出'),
        ('completed', '已完成'),
        ('archived', '已归档'),
    ]
    
    PRIORITY_CHOICES = [
        ('low', '低'),
        ('normal', '普通'),
        ('high', '高'),
        ('urgent', '紧急'),
    ]
    
    STAGE_CHOICES = [
        ('conversion', '转化阶段'),
        ('contract', '合同阶段'),
        ('production', '生产阶段'),
        ('settlement', '结算阶段'),
        ('payment', '回款阶段'),
        ('after_sales', '售后阶段'),
        ('litigation', '诉讼阶段'),
    ]
    
    # 基本信息
    document_number = models.CharField('发文编号', max_length=50, unique=True, db_index=True)
    project = models.ForeignKey(
        Project,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='outgoing_documents',
        verbose_name='关联项目',
        db_constraint=True
    )
    client = models.ForeignKey(
        Client,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='outgoing_documents',
        verbose_name='关联客户',
        db_constraint=True,
        help_text='关联的客户，用于自动填充办公地址'
    )
    client_contact = models.ForeignKey(
        ClientContact,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='outgoing_documents',
        verbose_name='签约主体代表',
        db_constraint=True,
        help_text='从客户管理-人员有关系管理中获取，用于自动填充联系人、联系电话和联系邮箱'
    )
    title = models.CharField('文件标题', max_length=200)
    recipient = models.CharField('收文单位', max_length=200)
    recipient_contact = models.CharField('联系人', max_length=100, blank=True, help_text='签约主体代表姓名，可从客户联系人中自动填充')
    recipient_phone = models.CharField('联系电话', max_length=20, blank=True, help_text='可从客户联系人中自动填充')
    recipient_email = models.EmailField('联系邮箱', max_length=255, blank=True, help_text='可从客户联系人中自动填充')
    recipient_address = models.TextField('收文地址', blank=True, help_text='办公地址，可从客户信息中自动填充')
    
    # 文件信息
    document_date = models.DateField('文件日期', null=True, blank=True)
    send_date = models.DateField('发文日期', null=True, blank=True)
    document_type = models.CharField('文件类型', max_length=50, blank=True)
    
    # 内容
    content = models.TextField('文件内容', blank=True)
    summary = models.TextField('摘要', blank=True)
    
    # 状态和优先级
    status = models.CharField('状态', max_length=20, choices=STATUS_CHOICES, default='draft', db_index=True)
    priority = models.CharField('优先级', max_length=20, choices=PRIORITY_CHOICES, default='normal')
    
    # 阶段和文件分类
    stage = models.CharField('阶段', max_length=20, choices=STAGE_CHOICES, blank=True, null=True, db_index=True, help_text='文件所属阶段')
    file_category = models.ForeignKey(
        'FileCategory',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='outgoing_documents',
        verbose_name='文件分类',
        help_text='关联的文件分类',
        db_constraint=True
    )
    
    # 审核信息
    reviewer = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='reviewed_outgoing_documents',
        verbose_name='审核人',
        db_constraint=True
    )
    review_notes = models.TextField('审核意见', blank=True)
    reviewed_at = models.DateTimeField('审核时间', null=True, blank=True)
    
    # 发送信息
    sender = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='sent_outgoing_documents',
        verbose_name='发送人',
        db_constraint=True
    )
    send_method = models.CharField('发送方式', max_length=50, blank=True, help_text='如：快递、邮件、送达等')
    delivery_methods = models.CharField('报送方式', max_length=200, blank=True, help_text='多选：邮件、快递、送达、易签宝，用逗号分隔')
    sent_at = models.DateTimeField('发送时间', null=True, blank=True)
    
    # 附件
    attachment = models.FileField('附件', upload_to='outgoing_documents/%Y/%m/%d/', blank=True, null=True)
    
    # 备注
    notes = models.TextField('备注', blank=True)
    
    # 时间信息
    created_at = models.DateTimeField('创建时间', auto_now_add=True, db_index=True)
    updated_at = models.DateTimeField('更新时间', auto_now=True)
    created_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        related_name='created_outgoing_documents',
        verbose_name='创建人',
        db_constraint=True
    )
    
    class Meta:
        db_table = 'outgoing_document'
        verbose_name = '发文'
        verbose_name_plural = '发文'
        ordering = ['-send_date', '-created_at']
        indexes = [
            models.Index(fields=['status', '-send_date']),
            models.Index(fields=['reviewer', '-created_at']),
            models.Index(fields=['stage']),
        ]
    
    def __str__(self):
        return f"{self.document_number} - {self.title}"
    
    def populate_from_client_contact(self):
        """从客户联系人中自动填充签约主体代表、联系电话和联系邮箱"""
        if self.client_contact:
            if not self.recipient_contact:
                self.recipient_contact = self.client_contact.name
            if not self.recipient_phone:
                self.recipient_phone = self.client_contact.phone
            if not self.recipient_email:
                self.recipient_email = self.client_contact.email
    
    def populate_from_client(self):
        """从客户信息中自动填充办公地址"""
        if self.client:
            if not self.recipient_address:
                self.recipient_address = self.client.office_address
    
    def populate_from_project(self):
        """从关联项目中自动填充客户信息"""
        if self.project and not self.client:
            # 尝试从项目中获取客户
            if hasattr(self.project, 'client') and self.project.client:
                self.client = self.project.client
    
    def save(self, *args, **kwargs):
        # 如果有关联项目但没有关联客户，尝试从项目中获取
        self.populate_from_project()
        
        # 从客户联系人中自动填充信息
        self.populate_from_client_contact()
        
        # 从客户信息中自动填充办公地址
        self.populate_from_client()
        
        super().save(*args, **kwargs)


class FileCategory(models.Model):
    """文件分类模型"""
    
    STAGE_CHOICES = [
        ('conversion', '转化阶段'),
        ('contract', '合同阶段'),
        ('production', '生产阶段'),
        ('settlement', '结算阶段'),
        ('payment', '回款阶段'),
        ('after_sales', '售后阶段'),
        ('litigation', '诉讼阶段'),
    ]
    
    # 基本信息
    name = models.CharField('分类名称', max_length=100)
    code = models.CharField('分类代码', max_length=50, blank=True, help_text='可选，用于系统识别')
    stage = models.CharField('所属阶段', max_length=20, choices=STAGE_CHOICES, db_index=True)
    description = models.TextField('分类描述', blank=True)
    
    # 排序和状态
    sort_order = models.IntegerField('排序', default=0, help_text='数字越小越靠前')
    is_active = models.BooleanField('是否启用', default=True, db_index=True)
    
    # 时间信息
    created_at = models.DateTimeField('创建时间', auto_now_add=True, db_index=True)
    updated_at = models.DateTimeField('更新时间', auto_now=True)
    created_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        related_name='created_file_categories',
        verbose_name='创建人',
        db_constraint=True
    )
    
    class Meta:
        db_table = 'file_category'
        verbose_name = '文件分类'
        verbose_name_plural = '文件分类'
        ordering = ['stage', 'sort_order', 'name']
        indexes = [
            models.Index(fields=['stage', 'sort_order']),
            models.Index(fields=['stage', 'is_active']),
        ]
        unique_together = [['stage', 'name']]  # 同一阶段内分类名称唯一
    
    def __str__(self):
        return f"{self.get_stage_display()} - {self.name}"


def file_template_upload_path(instance, filename):
    """文件模板上传路径"""
    date_path = instance.created_at.strftime('%Y/%m/%d') if instance.created_at else 'unknown'
    return f'file_templates/{date_path}/{instance.stage}/{filename}'


class FileTemplate(models.Model):
    """文件模板模型"""
    
    STAGE_CHOICES = [
        ('conversion', '转化阶段'),
        ('contract', '合同阶段'),
        ('production', '生产阶段'),
        ('settlement', '结算阶段'),
        ('payment', '回款阶段'),
        ('after_sales', '售后阶段'),
        ('litigation', '诉讼阶段'),
    ]
    
    # 基本信息
    name = models.CharField('模板名称', max_length=100)
    code = models.CharField('模板代码', max_length=50, blank=True, help_text='可选，用于系统识别')
    stage = models.CharField('所属阶段', max_length=20, choices=STAGE_CHOICES, db_index=True)
    category = models.ForeignKey(
        'FileCategory',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='templates',
        verbose_name='关联分类',
        help_text='可选，关联到文件分类'
    )
    
    # 模板文件
    template_file = models.FileField(
        '模板文件',
        upload_to=file_template_upload_path,
        null=True,
        blank=True,
        help_text='上传模板文件（Word、Excel、PDF等）'
    )
    description = models.TextField('模板描述', blank=True)
    
    # 排序和状态
    sort_order = models.IntegerField('排序', default=0, help_text='数字越小越靠前')
    is_active = models.BooleanField('是否启用', default=True, db_index=True)
    
    # 时间信息
    created_at = models.DateTimeField('创建时间', auto_now_add=True, db_index=True)
    updated_at = models.DateTimeField('更新时间', auto_now=True)
    created_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        related_name='created_file_templates',
        verbose_name='创建人',
        db_constraint=True
    )
    
    class Meta:
        db_table = 'file_template'
        verbose_name = '文件模板'
        verbose_name_plural = '文件模板'
        ordering = ['stage', 'sort_order', 'name']
        indexes = [
            models.Index(fields=['stage', 'sort_order']),
            models.Index(fields=['stage', 'is_active']),
        ]
        unique_together = [['stage', 'name']]  # 同一阶段内模板名称唯一
    
    def __str__(self):
        return f"{self.get_stage_display()} - {self.name}"
