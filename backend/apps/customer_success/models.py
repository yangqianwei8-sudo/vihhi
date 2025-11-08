from django.db import models
from django.utils import timezone
from backend.apps.system_management.models import User

class Client(models.Model):
    """客户模型"""
    CLIENT_LEVELS = [
        ('vip', 'VIP客户'),
        ('important', '重要客户'),
        ('general', '一般客户'),
        ('potential', '潜在客户'),
    ]
    
    CREDIT_LEVELS = [
        ('excellent', '优秀'),
        ('good', '良好'),
        ('normal', '一般'),
        ('poor', '较差'),
        ('bad', '很差'),
    ]
    
    # 基础信息
    name = models.CharField(max_length=200, verbose_name='客户名称')
    short_name = models.CharField(max_length=100, blank=True, verbose_name='客户简称')
    code = models.CharField(max_length=50, unique=True, verbose_name='客户编码')
    
    # 分类信息
    client_level = models.CharField(max_length=20, choices=CLIENT_LEVELS, default='general', verbose_name='客户等级')
    credit_level = models.CharField(max_length=20, choices=CREDIT_LEVELS, default='normal', verbose_name='信用等级')
    industry = models.CharField(max_length=100, blank=True, verbose_name='所属行业')
    
    # 联系信息
    address = models.TextField(blank=True, verbose_name='地址')
    phone = models.CharField(max_length=20, blank=True, verbose_name='电话')
    email = models.CharField(max_length=100, blank=True, verbose_name='邮箱')
    website = models.CharField(max_length=200, blank=True, verbose_name='网站')
    
    # 财务信息
    total_contract_amount = models.DecimalField(max_digits=12, decimal_places=2, default=0, verbose_name='累计合同金额')
    total_payment_amount = models.DecimalField(max_digits=12, decimal_places=2, default=0, verbose_name='累计回款金额')
    
    # 状态信息
    is_active = models.BooleanField(default=True, verbose_name='是否活跃')
    health_score = models.IntegerField(default=0, verbose_name='健康度评分')
    description = models.TextField(blank=True, verbose_name='客户描述')
    
    # 审计字段
    created_by = models.ForeignKey(User, on_delete=models.PROTECT, verbose_name='创建人')
    created_time = models.DateTimeField(default=timezone.now, verbose_name='创建时间')
    updated_time = models.DateTimeField(auto_now=True, verbose_name='更新时间')
    
    class Meta:
        db_table = 'customer_client'
        verbose_name = '客户'
        verbose_name_plural = verbose_name
        ordering = ['-created_time']
    
    def __str__(self):
        return self.name

class ClientContact(models.Model):
    """客户联系人"""
    client = models.ForeignKey(Client, on_delete=models.CASCADE, related_name='contacts', verbose_name='客户')
    name = models.CharField(max_length=100, verbose_name='联系人姓名')
    position = models.CharField(max_length=100, blank=True, verbose_name='职位')
    department = models.CharField(max_length=100, blank=True, verbose_name='部门')
    phone = models.CharField(max_length=20, blank=True, verbose_name='手机')
    telephone = models.CharField(max_length=20, blank=True, verbose_name='电话')
    email = models.CharField(max_length=100, blank=True, verbose_name='邮箱')
    wechat = models.CharField(max_length=100, blank=True, verbose_name='微信')
    is_primary = models.BooleanField(default=False, verbose_name='是否主要联系人')
    notes = models.TextField(blank=True, verbose_name='备注')
    created_time = models.DateTimeField(default=timezone.now, verbose_name='创建时间')
    
    class Meta:
        db_table = 'customer_contact'
        verbose_name = '客户联系人'
        verbose_name_plural = verbose_name

class ClientProject(models.Model):
    """客户项目关联（统计用）"""
    client = models.ForeignKey(Client, on_delete=models.CASCADE, verbose_name='客户')
    project = models.ForeignKey('project_center.Project', on_delete=models.CASCADE, verbose_name='项目')
    service_type = models.CharField(max_length=50, verbose_name='服务类型')
    contract_amount = models.DecimalField(max_digits=12, decimal_places=2, verbose_name='合同金额')
    start_date = models.DateField(verbose_name='开始日期')
    end_date = models.DateField(verbose_name='结束日期')
    status = models.CharField(max_length=20, verbose_name='项目状态')
    created_time = models.DateTimeField(default=timezone.now, verbose_name='创建时间')
    
    class Meta:
        db_table = 'customer_client_project'
        verbose_name = '客户项目'
        verbose_name_plural = verbose_name
