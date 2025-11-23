from django.db import models
from django.utils import timezone


class PermissionItem(models.Model):
    """业务权限点"""
    MODULE_CHOICES = [
        ('项目中心', '项目中心'),
        ('结算中心', '结算中心'),
        ('生产质量', '生产质量'),
        ('客户成功', '客户成功'),
        ('人事管理', '人事管理'),
        ('风险管理', '风险管理'),
        ('系统管理', '系统管理'),
        ('权限管理', '权限管理'),
        ('资源标准', '资源标准'),
        ('任务协作', '任务协作'),
        ('交付客户', '交付客户'),
    ]
    
    module = models.CharField(max_length=100, choices=MODULE_CHOICES, verbose_name='功能模块')
    action = models.CharField(max_length=100, verbose_name='操作代码')
    code = models.CharField(max_length=150, unique=True, verbose_name='权限编码')
    name = models.CharField(max_length=150, verbose_name='权限名称')
    description = models.TextField(blank=True, verbose_name='描述')
    is_active = models.BooleanField(default=True, verbose_name='是否启用')
    created_time = models.DateTimeField(default=timezone.now, verbose_name='创建时间')

    class Meta:
        db_table = 'system_permission_item'  # 使用原表名，避免数据迁移
        verbose_name = '业务权限点'
        verbose_name_plural = verbose_name
        ordering = ['module', 'action']

    def __str__(self):
        return f"{self.code} - {self.name}"
    
    def get_module_display_name(self):
        """获取模块显示名称"""
        return self.module  # 现在 module 本身就是中文，直接返回
