"""
组织架构模块数据模型
"""
from django.db import models


class Company(models.Model):
    """公司模型"""
    name = models.CharField(max_length=200, unique=True)
    code = models.CharField(max_length=50, unique=True)
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        db_table = 'org_company'
        verbose_name = '公司'
        verbose_name_plural = verbose_name
    
    def __str__(self):
        return self.name


class Department(models.Model):
    """部门模型（用于业务组织标签和公司数据隔离）"""
    name = models.CharField(max_length=200)
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    
    company = models.ForeignKey(
        Company,
        on_delete=models.PROTECT,
        related_name='departments',
        verbose_name='公司'
    )
    parent = models.ForeignKey(
        'self',
        on_delete=models.PROTECT,
        null=True,
        blank=True,
        related_name='children',
        verbose_name='上级部门'
    )
    
    class Meta:
        db_table = 'org_department'
        verbose_name = '部门'
        verbose_name_plural = verbose_name
        unique_together = [('company', 'name', 'parent')]
    
    def __str__(self):
        return f"{self.company.name} - {self.name}"

