"""
编号规则配置模型
用于在数据库中存储和管理编号规则配置
"""
from django.db import models
from django.utils import timezone
from backend.apps.system_management.models import User


class NumberRule(models.Model):
    """
    编号规则配置模型
    
    用于统一管理系统的编号生成规则，支持动态配置和调整
    """
    # 规则基本信息
    code = models.CharField(
        max_length=50,
        unique=True,
        verbose_name='规则代码',
        help_text='唯一标识符，用于在代码中引用此规则'
    )
    name = models.CharField(
        max_length=100,
        verbose_name='规则名称',
        help_text='规则的显示名称'
    )
    description = models.TextField(
        blank=True,
        verbose_name='规则描述',
        help_text='规则的详细说明'
    )
    
    # 编号格式配置
    prefix = models.CharField(
        max_length=50,
        blank=True,
        verbose_name='编号前缀',
        help_text='编号的前缀部分，如"VIH-JF"、"SW"等'
    )
    date_format = models.CharField(
        max_length=20,
        blank=True,
        null=True,
        verbose_name='日期格式',
        help_text='日期格式字符串，如"%Y%m%d"、"%Y"等，留空表示不使用日期'
    )
    seq_length = models.IntegerField(
        default=4,
        verbose_name='序列号长度',
        help_text='序列号的位数，默认4位（0001-9999）'
    )
    
    # 序列号策略
    SEQ_STRATEGY_CHOICES = [
        ('daily', '按日重置'),
        ('monthly', '按月重置'),
        ('yearly', '按年重置'),
        ('global', '全局累计'),
        ('related', '按关联对象分组'),
    ]
    seq_strategy = models.CharField(
        max_length=20,
        choices=SEQ_STRATEGY_CHOICES,
        default='daily',
        verbose_name='序列号策略',
        help_text='序列号的生成策略'
    )
    
    # 关联字段配置（用于related策略）
    related_field = models.CharField(
        max_length=100,
        blank=True,
        null=True,
        verbose_name='关联字段',
        help_text='关联字段名（用于related策略），如"project__project_number"'
    )
    
    # 自定义模板
    template = models.CharField(
        max_length=200,
        blank=True,
        null=True,
        verbose_name='自定义模板',
        help_text='自定义编号模板，如"{prefix}-{date}-{seq:04d}"，留空使用默认格式'
    )
    
    # 应用配置
    model_app = models.CharField(
        max_length=50,
        verbose_name='应用名称',
        help_text='Django应用名称，如"delivery_customer"'
    )
    model_name = models.CharField(
        max_length=50,
        verbose_name='模型名称',
        help_text='模型类名，如"DeliveryRecord"'
    )
    field_name = models.CharField(
        max_length=50,
        default='number',
        verbose_name='字段名称',
        help_text='编号字段名，如"delivery_number"'
    )
    
    # 状态管理
    is_active = models.BooleanField(
        default=True,
        verbose_name='是否启用',
        help_text='是否启用此规则'
    )
    is_default = models.BooleanField(
        default=False,
        verbose_name='是否默认',
        help_text='是否为该模型的默认规则'
    )
    
    # 审计字段
    created_by = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='created_number_rules',
        verbose_name='创建人'
    )
    created_time = models.DateTimeField(
        default=timezone.now,
        verbose_name='创建时间'
    )
    updated_time = models.DateTimeField(
        auto_now=True,
        verbose_name='更新时间'
    )
    updated_by = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='updated_number_rules',
        verbose_name='最后更新人'
    )
    
    class Meta:
        db_table = 'core_number_rule'
        verbose_name = '编号规则'
        verbose_name_plural = '编号规则'
        ordering = ['code']
        indexes = [
            models.Index(fields=['code']),
            models.Index(fields=['model_app', 'model_name']),
            models.Index(fields=['is_active']),
        ]
    
    def __str__(self):
        return f"{self.code} - {self.name}"
    
    def get_number_format_example(self) -> str:
        """获取编号格式示例"""
        from datetime import date
        today = date.today()
        
        example_date = ''
        if self.date_format:
            if self.seq_strategy == 'daily':
                example_date = today.strftime(self.date_format)
            elif self.seq_strategy == 'monthly':
                example_date = today.strftime(self.date_format.replace('%d', ''))
            elif self.seq_strategy == 'yearly':
                example_date = today.strftime(self.date_format.replace('%m', '').replace('%d', ''))
            else:
                example_date = today.strftime(self.date_format)
        
        seq_example = '1'.zfill(self.seq_length)
        
        if self.template:
            return self.template.format(
                prefix=self.prefix,
                date=example_date,
                seq=1,
                seq_formatted=seq_example,
                related='RELATED',
                year=today.strftime('%Y'),
                month=today.strftime('%m'),
                day=today.strftime('%d'),
            )
        else:
            if example_date and self.related_field:
                return f"{self.prefix}-{example_date}-RELATED-{seq_example}"
            elif example_date:
                if self.prefix:
                    return f"{self.prefix}-{example_date}-{seq_example}"
                else:
                    return f"{example_date}{seq_example}"
            elif self.related_field:
                return f"{self.prefix}-RELATED-{seq_example}"
            else:
                if self.prefix:
                    return f"{self.prefix}-{seq_example}"
                else:
                    return seq_example

