from django.db import models
from django.conf import settings
from django.core.validators import FileExtensionValidator
from django.utils import timezone
import os

from backend.apps.production_management.models import Project
from backend.apps.customer_management.models import Client, ClientContact


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
