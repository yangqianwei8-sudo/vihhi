from django.db import models
from django.utils import timezone
from django.db.models import Max
from datetime import datetime
from backend.apps.system_management.models import User


class ExternalSystem(models.Model):
    """外部系统"""
    STATUS_CHOICES = [
        ('active', '启用'),
        ('inactive', '停用'),
    ]
    
    name = models.CharField(max_length=200, unique=True, verbose_name='系统名称')
    code = models.CharField(max_length=50, unique=True, blank=True, verbose_name='系统编码')
    description = models.TextField(blank=True, verbose_name='系统描述')
    base_url = models.URLField(verbose_name='基础URL')
    contact_person = models.CharField(max_length=100, blank=True, verbose_name='联系人')
    contact_phone = models.CharField(max_length=50, blank=True, verbose_name='联系电话')
    contact_email = models.EmailField(blank=True, verbose_name='联系邮箱')
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='active', verbose_name='状态')
    is_active = models.BooleanField(default=True, verbose_name='是否启用')
    created_by = models.ForeignKey(User, on_delete=models.PROTECT, related_name='created_external_systems', verbose_name='创建人')
    created_time = models.DateTimeField(default=timezone.now, verbose_name='创建时间')
    updated_time = models.DateTimeField(auto_now=True, verbose_name='更新时间')
    
    class Meta:
        db_table = 'api_external_system'
        verbose_name = '外部系统'
        verbose_name_plural = verbose_name
        ordering = ['name']
        indexes = [
            models.Index(fields=['code', 'status']),
            models.Index(fields=['name', 'is_active']),
        ]
    
    def __str__(self):
        return self.name
    
    def save(self, *args, **kwargs):
        if not self.code:
            max_system = ExternalSystem.objects.filter(
                code__startswith='SYS-'
            ).aggregate(max_num=Max('code'))['max_num']
            if max_system:
                try:
                    seq = int(max_system.split('-')[-1]) + 1
                except (ValueError, IndexError):
                    seq = 1
            else:
                seq = 1
            self.code = f'SYS-{seq:05d}'
        super().save(*args, **kwargs)
    
    @property
    def api_count(self):
        """API接口数量"""
        return self.api_interfaces.filter(is_active=True).count()


class ApiInterface(models.Model):
    """API接口"""
    METHOD_CHOICES = [
        ('GET', 'GET'),
        ('POST', 'POST'),
        ('PUT', 'PUT'),
        ('PATCH', 'PATCH'),
        ('DELETE', 'DELETE'),
    ]
    
    AUTH_TYPE_CHOICES = [
        ('none', '无认证'),
        ('api_key', 'API Key'),
        ('bearer_token', 'Bearer Token'),
        ('basic_auth', 'Basic Auth'),
        ('oauth2', 'OAuth2'),
        ('custom', '自定义'),
    ]
    
    STATUS_CHOICES = [
        ('active', '启用'),
        ('inactive', '停用'),
        ('deprecated', '已废弃'),
    ]
    
    name = models.CharField(max_length=200, verbose_name='接口名称')
    code = models.CharField(max_length=100, unique=True, blank=True, verbose_name='接口编码')
    external_system = models.ForeignKey(ExternalSystem, on_delete=models.CASCADE, related_name='api_interfaces', verbose_name='所属系统')
    url = models.CharField(max_length=500, verbose_name='接口URL')
    method = models.CharField(max_length=10, choices=METHOD_CHOICES, default='GET', verbose_name='请求方法')
    auth_type = models.CharField(max_length=20, choices=AUTH_TYPE_CHOICES, default='none', verbose_name='认证方式')
    auth_config = models.JSONField(default=dict, blank=True, verbose_name='认证配置')
    request_headers = models.JSONField(default=dict, blank=True, verbose_name='请求头')
    request_params = models.JSONField(default=dict, blank=True, verbose_name='请求参数')
    request_body_schema = models.JSONField(default=dict, blank=True, verbose_name='请求体结构')
    response_schema = models.JSONField(default=dict, blank=True, verbose_name='响应结构')
    description = models.TextField(blank=True, verbose_name='接口描述')
    timeout = models.IntegerField(default=30, verbose_name='超时时间（秒）')
    retry_count = models.IntegerField(default=0, verbose_name='重试次数')
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='active', verbose_name='状态')
    is_active = models.BooleanField(default=True, verbose_name='是否启用')
    version = models.CharField(max_length=20, default='1.0', verbose_name='版本号')
    created_by = models.ForeignKey(User, on_delete=models.PROTECT, related_name='created_api_interfaces', verbose_name='创建人')
    created_time = models.DateTimeField(default=timezone.now, verbose_name='创建时间')
    updated_time = models.DateTimeField(auto_now=True, verbose_name='更新时间')
    
    class Meta:
        db_table = 'api_interface'
        verbose_name = 'API接口'
        verbose_name_plural = verbose_name
        ordering = ['-created_time']
        indexes = [
            models.Index(fields=['code', 'status']),
            models.Index(fields=['external_system', 'is_active']),
            models.Index(fields=['method', 'status']),
        ]
    
    def __str__(self):
        return f"{self.external_system.name} - {self.name}"
    
    def save(self, *args, **kwargs):
        if not self.code:
            system_prefix = self.external_system.code if self.external_system else 'API'
            max_api = ApiInterface.objects.filter(
                code__startswith=f'{system_prefix}-'
            ).aggregate(max_num=Max('code'))['max_num']
            if max_api:
                try:
                    seq = int(max_api.split('-')[-1]) + 1
                except (ValueError, IndexError):
                    seq = 1
            else:
                seq = 1
            self.code = f'{system_prefix}-{seq:05d}'
        super().save(*args, **kwargs)
    
    @property
    def full_url(self):
        """完整URL"""
        if self.url.startswith('http://') or self.url.startswith('https://'):
            return self.url
        return f"{self.external_system.base_url.rstrip('/')}/{self.url.lstrip('/')}"


class ApiCallLog(models.Model):
    """API调用日志"""
    STATUS_CHOICES = [
        ('success', '成功'),
        ('failed', '失败'),
        ('timeout', '超时'),
    ]
    
    api_interface = models.ForeignKey(ApiInterface, on_delete=models.CASCADE, related_name='call_logs', verbose_name='API接口')
    request_url = models.CharField(max_length=500, verbose_name='请求URL')
    request_method = models.CharField(max_length=10, verbose_name='请求方法')
    request_headers = models.JSONField(default=dict, blank=True, verbose_name='请求头')
    request_params = models.JSONField(default=dict, blank=True, verbose_name='请求参数')
    request_body = models.TextField(blank=True, verbose_name='请求体')
    response_status = models.IntegerField(null=True, blank=True, verbose_name='响应状态码')
    response_headers = models.JSONField(default=dict, blank=True, verbose_name='响应头')
    response_body = models.TextField(blank=True, verbose_name='响应体')
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, verbose_name='调用状态')
    error_message = models.TextField(blank=True, verbose_name='错误信息')
    duration = models.FloatField(null=True, blank=True, verbose_name='耗时（秒）')
    called_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True, related_name='api_calls', verbose_name='调用人')
    called_time = models.DateTimeField(default=timezone.now, verbose_name='调用时间')
    
    class Meta:
        db_table = 'api_call_log'
        verbose_name = 'API调用日志'
        verbose_name_plural = verbose_name
        ordering = ['-called_time']
        indexes = [
            models.Index(fields=['api_interface', 'called_time']),
            models.Index(fields=['status', 'called_time']),
            models.Index(fields=['called_by', 'called_time']),
        ]
    
    def __str__(self):
        return f"{self.api_interface.name} - {self.get_status_display()} - {self.called_time}"


class ApiTestRecord(models.Model):
    """API测试记录"""
    STATUS_CHOICES = [
        ('pending', '待测试'),
        ('success', '成功'),
        ('failed', '失败'),
    ]
    
    api_interface = models.ForeignKey(ApiInterface, on_delete=models.CASCADE, related_name='test_records', verbose_name='API接口')
    test_name = models.CharField(max_length=200, verbose_name='测试名称')
    test_params = models.JSONField(default=dict, blank=True, verbose_name='测试参数')
    test_body = models.TextField(blank=True, verbose_name='测试请求体')
    expected_status = models.IntegerField(null=True, blank=True, verbose_name='期望状态码')
    expected_response = models.TextField(blank=True, verbose_name='期望响应')
    actual_status = models.IntegerField(null=True, blank=True, verbose_name='实际状态码')
    actual_response = models.TextField(blank=True, verbose_name='实际响应')
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='pending', verbose_name='测试状态')
    error_message = models.TextField(blank=True, verbose_name='错误信息')
    test_duration = models.FloatField(null=True, blank=True, verbose_name='测试耗时（秒）')
    tested_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True, related_name='api_tests', verbose_name='测试人')
    tested_time = models.DateTimeField(default=timezone.now, verbose_name='测试时间')
    
    class Meta:
        db_table = 'api_test_record'
        verbose_name = 'API测试记录'
        verbose_name_plural = verbose_name
        ordering = ['-tested_time']
        indexes = [
            models.Index(fields=['api_interface', 'tested_time']),
            models.Index(fields=['status', 'tested_time']),
        ]
    
    def __str__(self):
        return f"{self.api_interface.name} - {self.test_name} - {self.get_status_display()}"
