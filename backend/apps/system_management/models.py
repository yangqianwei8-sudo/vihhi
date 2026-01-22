from django.db import models
from django.contrib.auth.models import AbstractUser
from django.utils import timezone
from django.conf import settings


class User(AbstractUser):
    """扩展用户模型"""
    USER_TYPE_CHOICES = [
        ('internal', '咨询单位'),
        ('client_owner', '委托单位'),
        ('design_partner', '设计单位'),
        ('control_partner', '过控单位'),
    ]

    phone = models.CharField(max_length=20, blank=True, verbose_name='手机号')
    department = models.ForeignKey(
        'Department',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='members',
        verbose_name='部门'
    )
    position = models.CharField(max_length=100, blank=True, verbose_name='职位')
    user_type = models.CharField(max_length=20, choices=USER_TYPE_CHOICES, default='internal', verbose_name='用户类型')
    client_type = models.CharField(max_length=50, blank=True, verbose_name='客户类型备注')
    avatar = models.ImageField(upload_to='avatars/', null=True, blank=True, verbose_name='头像')
    roles = models.ManyToManyField('Role', blank=True, related_name='users', verbose_name='系统角色')
    profile_completed = models.BooleanField(default=False, verbose_name='资料已完善')
    is_active = models.BooleanField(default=True, verbose_name='是否激活')
    created_time = models.DateTimeField(default=timezone.now, verbose_name='创建时间')
    updated_time = models.DateTimeField(auto_now=True, verbose_name='更新时间')
    notification_preferences = models.JSONField(default=dict, blank=True, verbose_name='通知偏好')

    class Meta:
        db_table = 'system_user'
        verbose_name = '用户'
        verbose_name_plural = verbose_name

    def __str__(self):
        return f"{self.username} - {self.get_full_name()}"

    def get_notification_preferences(self):
        default_prefs = {
            "inbox": True,
            "email": False,
            "wecom": False,
        }
        incoming = self.notification_preferences or {}
        merged = {**default_prefs, **incoming}
        # Ensure boolean casting
        return {key: bool(merged.get(key)) for key in default_prefs.keys()}


class Department(models.Model):
    """部门架构"""
    name = models.CharField(max_length=100, verbose_name='部门名称')
    code = models.CharField(max_length=50, unique=True, verbose_name='部门编码')
    parent = models.ForeignKey('self', on_delete=models.CASCADE, null=True, blank=True, verbose_name='上级部门')
    leader = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True, 
                              related_name='leading_departments', verbose_name='部门负责人')  # 添加了 related_name
    description = models.TextField(blank=True, verbose_name='部门描述')
    order = models.IntegerField(default=0, verbose_name='排序')
    is_active = models.BooleanField(default=True, verbose_name='是否启用')
    created_time = models.DateTimeField(default=timezone.now, verbose_name='创建时间')
    
    class Meta:
        db_table = 'system_department'
        verbose_name = '部门'
        verbose_name_plural = verbose_name
    
    def __str__(self):
        return self.name

class Role(models.Model):
    """角色表"""
    name = models.CharField(max_length=100, verbose_name='角色名称')
    code = models.CharField(max_length=50, unique=True, verbose_name='角色编码')
    custom_permissions = models.ManyToManyField(
        'permission_management.PermissionItem',
        blank=True,
        related_name='roles',
        verbose_name='业务权限'
    )
    description = models.TextField(blank=True, verbose_name='角色描述')
    is_active = models.BooleanField(default=True, verbose_name='是否启用')
    created_time = models.DateTimeField(default=timezone.now, verbose_name='创建时间')
    
    class Meta:
        db_table = 'system_role'
        verbose_name = '角色'
        verbose_name_plural = verbose_name
    
    def __str__(self):
        return self.name


class RegistrationRequest(models.Model):
    """用户注册申请"""
    CLIENT_TYPE_CHOICES = [
        ('service_provider', '服务单位'),
        ('client_owner', '委托单位'),
        ('design_partner', '设计单位'),
    ]

    STATUS_PENDING = 'pending'
    STATUS_APPROVED = 'approved'
    STATUS_REJECTED = 'rejected'
    STATUS_CHOICES = [
        (STATUS_PENDING, '待审核'),
        (STATUS_APPROVED, '已通过'),
        (STATUS_REJECTED, '已拒绝'),
    ]

    phone = models.CharField(max_length=20, unique=True, verbose_name='手机号')
    username = models.CharField(max_length=150, unique=True, verbose_name='登录账号')
    client_type = models.CharField(max_length=20, choices=CLIENT_TYPE_CHOICES, verbose_name='账户类型')
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default=STATUS_PENDING, verbose_name='审核状态')
    encoded_password = models.CharField(max_length=128, verbose_name='加密密码')
    submitted_time = models.DateTimeField(default=timezone.now, verbose_name='提交时间')
    processed_time = models.DateTimeField(null=True, blank=True, verbose_name='处理时间')
    processed_by = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='processed_registrations',
        verbose_name='审核人'
    )
    feedback = models.TextField(blank=True, verbose_name='审核意见')

    class Meta:
        db_table = 'system_registration_request'
        verbose_name = '注册申请'
        verbose_name_plural = verbose_name
        ordering = ['-submitted_time']

    def __str__(self):
        return f"{self.username} - {self.get_status_display()}"

class DataDictionary(models.Model):
    """数据字典"""
    DICT_TYPE_CHOICES = [
        ('project', '项目相关'),
        ('resource', '资源相关'),
        ('finance', '财务相关'),
        ('customer', '客户相关'),
        ('system', '系统配置'),
    ]
    
    name = models.CharField(max_length=100, verbose_name='字典名称')
    code = models.CharField(max_length=100, unique=True, verbose_name='字典编码')
    value = models.CharField(max_length=200, verbose_name='字典值')
    dict_type = models.CharField(max_length=20, choices=DICT_TYPE_CHOICES, verbose_name='字典类型')
    parent = models.ForeignKey('self', on_delete=models.CASCADE, null=True, blank=True, verbose_name='父级字典')
    order = models.IntegerField(default=0, verbose_name='排序')
    description = models.TextField(blank=True, verbose_name='描述')
    is_active = models.BooleanField(default=True, verbose_name='是否启用')
    created_time = models.DateTimeField(default=timezone.now, verbose_name='创建时间')
    
    class Meta:
        db_table = 'system_data_dictionary'
        verbose_name = '数据字典'
        verbose_name_plural = verbose_name
        ordering = ['dict_type', 'order', 'id']
    
    def __str__(self):
        return f"{self.name} ({self.code})"

class SystemConfig(models.Model):
    """系统配置表"""
    key = models.CharField(max_length=100, unique=True, verbose_name='配置键')
    value = models.TextField(verbose_name='配置值')
    description = models.TextField(blank=True, verbose_name='配置描述')
    is_encrypted = models.BooleanField(default=False, verbose_name='是否加密')
    created_time = models.DateTimeField(default=timezone.now, verbose_name='创建时间')
    updated_time = models.DateTimeField(auto_now=True, verbose_name='更新时间')
    
    class Meta:
        db_table = 'system_config'
        verbose_name = '系统配置'
        verbose_name_plural = verbose_name
    
    def __str__(self):
        return self.key


class OurCompany(models.Model):
    """我方主体信息"""
    company_name = models.CharField(max_length=200, unique=True, verbose_name='主体名称')
    credit_code = models.CharField(max_length=50, blank=True, verbose_name='统一社会信用代码')
    legal_representative = models.CharField(max_length=100, blank=True, verbose_name='法定代表人')
    registered_address = models.CharField(max_length=500, blank=True, verbose_name='注册地址')
    order = models.IntegerField(default=0, verbose_name='排序', help_text='数字越小越靠前')
    is_active = models.BooleanField(default=True, verbose_name='是否启用')
    created_time = models.DateTimeField(default=timezone.now, verbose_name='创建时间')
    updated_time = models.DateTimeField(auto_now=True, verbose_name='更新时间')
    
    class Meta:
        db_table = 'system_our_company'
        verbose_name = '我方主体信息'
        verbose_name_plural = verbose_name
        ordering = ['order', 'id']
    
    def __str__(self):
        return self.company_name


class SystemFeedback(models.Model):
    """系统反馈模型"""
    
    FEEDBACK_TYPE_CHOICES = [
        ('bug', '问题报告'),
        ('suggestion', '功能建议'),
        ('complaint', '投诉建议'),
        ('praise', '表扬反馈'),
        ('other', '其他'),
    ]
    
    STATUS_CHOICES = [
        ('pending', '待处理'),
        ('processing', '处理中'),
        ('resolved', '已解决'),
        ('closed', '已关闭'),
    ]
    
    PRIORITY_CHOICES = [
        ('low', '低'),
        ('medium', '中'),
        ('high', '高'),
        ('urgent', '紧急'),
    ]
    
    # 反馈基本信息
    feedback_type = models.CharField('反馈类型', max_length=20, choices=FEEDBACK_TYPE_CHOICES)
    title = models.CharField('反馈标题', max_length=200)
    content = models.TextField('反馈内容')
    
    # 提交人信息（自动获取登录用户）
    submitted_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        related_name='submitted_feedbacks',
        verbose_name='提交人',
        db_constraint=True
    )
    submitted_at = models.DateTimeField('提交时间', auto_now_add=True, db_index=True)
    
    # 处理信息
    status = models.CharField('处理状态', max_length=20, choices=STATUS_CHOICES, default='pending', db_index=True)
    processed_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='processed_feedbacks',
        verbose_name='处理人',
        db_constraint=True
    )
    processed_at = models.DateTimeField('处理时间', null=True, blank=True)
    process_comment = models.TextField('处理意见', blank=True)
    
    # 附件支持
    attachment = models.FileField('附件', upload_to='feedback_attachments/%Y/%m/', blank=True, null=True)
    
    # 优先级
    priority = models.CharField(
        '优先级',
        max_length=10,
        choices=PRIORITY_CHOICES,
        default='medium'
    )
    
    # 关联信息（可选，用于关联到具体业务）
    related_module = models.CharField('关联模块', max_length=50, blank=True)
    related_url = models.URLField('关联页面', blank=True)
    
    class Meta:
        db_table = 'system_feedback'
        verbose_name = '系统反馈'
        verbose_name_plural = '系统反馈'
        ordering = ['-submitted_at']
        indexes = [
            models.Index(fields=['status', '-submitted_at']),
            models.Index(fields=['submitted_by', '-submitted_at']),
            models.Index(fields=['feedback_type', '-submitted_at']),
        ]
    
    def __str__(self):
        return f"{self.get_feedback_type_display()} - {self.title}"
