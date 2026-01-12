"""
账户模块数据模型
"""
from django.db import models
from django.conf import settings


class UserProfile(models.Model):
    """用户扩展信息模型"""
    user = models.OneToOneField(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='profile',
        verbose_name='用户'
    )
    mobile = models.CharField(max_length=30, blank=True, default='', verbose_name='手机号')
    job_title = models.CharField(max_length=100, blank=True, default='', verbose_name='职位')
    is_enabled = models.BooleanField(
        default=True,
        help_text='是否允许登录内部系统（离职/冻结）',
        verbose_name='是否启用'
    )
    updated_at = models.DateTimeField(auto_now=True, verbose_name='更新时间')
    
    company = models.ForeignKey(
        'org.Company',
        on_delete=models.PROTECT,
        null=True,
        blank=True,
        verbose_name='公司'
    )
    department = models.ForeignKey(
        'org.Department',
        on_delete=models.PROTECT,
        null=True,
        blank=True,
        verbose_name='部门'
    )
    
    class Meta:
        db_table = 'accounts_user_profile'
        verbose_name = '用户扩展信息'
        verbose_name_plural = verbose_name
    
    def __str__(self):
        return f"{self.user.username} - {self.company.name if self.company else '未设置公司'}"

