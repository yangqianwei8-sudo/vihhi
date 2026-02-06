# 产值管理模块模型
# 从settlement_center迁移而来

from django.db import models
from django.db.models import Q
from django.utils import timezone
from backend.apps.system_management.models import User


class OutputValuePolicy(models.Model):
    """
    产值口径配置（唯一权威）。
    全系统仅允许一条 enabled=True 的 policy 生效；计算内核从本表读取所有可变口径。
    """
    name = models.CharField(max_length=100, default='V1 默认口径', verbose_name='口径名称')
    # 服务类型权重：JSON { "code": "0.02", "name": "0.02" }，支持 code/name 双键
    service_type_weights = models.JSONField(
        default=dict,
        verbose_name='服务类型权重',
        help_text='JSON：{ "转化阶段": "0.02", "conversion": "0.02", ... }，绝对折算率',
    )
    stage_weight = models.DecimalField(
        max_digits=10, decimal_places=4, default='1.0',
        verbose_name='阶段权重', help_text='V1 默认 1.0',
    )
    event_modifier_min = models.DecimalField(
        max_digits=10, decimal_places=4, default='0.2',
        verbose_name='事件修正系数下限',
    )
    event_modifier_max = models.DecimalField(
        max_digits=10, decimal_places=4, default='1.2',
        verbose_name='事件修正系数上限',
    )
    confidence_high_threshold = models.DecimalField(
        max_digits=10, decimal_places=4, default='0.30',
        verbose_name='confidence 高阈值', help_text='milestone_weight >= 此值视为 high',
    )
    enabled = models.BooleanField(default=True, verbose_name='是否生效')
    effective_from = models.DateTimeField(null=True, blank=True, verbose_name='生效起始时间（可选）')
    updated_by = models.ForeignKey(
        User, on_delete=models.SET_NULL, null=True, blank=True,
        related_name='+', verbose_name='最后修改人',
    )
    updated_at = models.DateTimeField(auto_now=True, verbose_name='更新时间')
    created_at = models.DateTimeField(default=timezone.now, verbose_name='创建时间')

    class Meta:
        db_table = 'output_value_policy'
        verbose_name = '产值口径配置'
        verbose_name_plural = verbose_name
        ordering = ['-updated_at']
        constraints = [
            models.UniqueConstraint(
                fields=['enabled'],
                condition=Q(enabled=True),
                name='output_value_policy_single_enabled',
            ),
        ]

    def __str__(self):
        return f'{self.name} (enabled={self.enabled})'

    @classmethod
    def get_active(cls):
        """
        返回当前唯一生效的口径配置。未配置时抛出 RuntimeError，提示在 Admin 配置。
        """
        policy = cls.objects.filter(enabled=True).first()
        if not policy:
            raise RuntimeError(
                '未配置产值口径：请在 Django Admin → 产值管理 → 产值口径配置 中新增一条并勾选「是否生效」。'
                '或执行：python manage.py seed_output_value_policy'
            )
        return policy

    def save(self, *args, **kwargs):
        if self.enabled:
            OutputValuePolicy.objects.filter(enabled=True).exclude(pk=self.pk).update(enabled=False)
        super().save(*args, **kwargs)


class OutputValueStage(models.Model):
    """产值阶段模型"""
    STAGE_TYPE_CHOICES = [
        ('conversion', '转化阶段'),
        ('contract', '合同阶段'),
        ('production', '生产阶段'),
        ('settlement', '结算阶段'),
        ('payment', '回款阶段'),
        ('after_sales', '售后阶段'),
    ]
    
    BASE_AMOUNT_CHOICES = [
        ('registration_amount', '备案金额'),
        ('intention_amount', '意向金额'),
        ('contract_amount', '合同金额'),
        ('settlement_amount', '结算金额'),
        ('payment_amount', '回款金额'),
    ]
    
    name = models.CharField(max_length=100, verbose_name='阶段名称')
    code = models.CharField(max_length=50, unique=True, verbose_name='阶段编码')
    stage_type = models.CharField(max_length=20, choices=STAGE_TYPE_CHOICES, verbose_name='阶段类型')
    stage_percentage = models.DecimalField(max_digits=5, decimal_places=2, verbose_name='阶段产值比例(%)', 
                                          help_text='该阶段占总产值的比例')
    base_amount_type = models.CharField(max_length=30, choices=BASE_AMOUNT_CHOICES, verbose_name='计取基数类型')
    description = models.TextField(blank=True, verbose_name='阶段描述')
    order = models.IntegerField(default=0, verbose_name='排序')
    is_active = models.BooleanField(default=True, verbose_name='是否启用')
    created_time = models.DateTimeField(default=timezone.now, verbose_name='创建时间')
    updated_time = models.DateTimeField(auto_now=True, verbose_name='更新时间')
    
    class Meta:
        db_table = 'settlement_output_value_stage'  # 保持原有表名，避免数据迁移
        verbose_name = '产值阶段'
        verbose_name_plural = verbose_name
        ordering = ['order', 'created_time']
    
    def __str__(self):
        return f"{self.name} ({self.stage_percentage}%)"


class OutputValueMilestone(models.Model):
    """产值里程碑模型"""
    stage = models.ForeignKey(OutputValueStage, on_delete=models.CASCADE, related_name='milestones', 
                              verbose_name='所属阶段')
    name = models.CharField(max_length=100, verbose_name='里程碑名称')
    code = models.CharField(max_length=50, verbose_name='里程碑编码')
    milestone_percentage = models.DecimalField(max_digits=5, decimal_places=2, verbose_name='里程碑产值比例(%)',
                                              help_text='该里程碑在该阶段内的比例')
    description = models.TextField(blank=True, verbose_name='里程碑描述')
    order = models.IntegerField(default=0, verbose_name='排序')
    is_active = models.BooleanField(default=True, verbose_name='是否启用')
    created_time = models.DateTimeField(default=timezone.now, verbose_name='创建时间')
    updated_time = models.DateTimeField(auto_now=True, verbose_name='更新时间')
    
    class Meta:
        db_table = 'settlement_output_value_milestone'  # 保持原有表名，避免数据迁移
        verbose_name = '产值里程碑'
        verbose_name_plural = verbose_name
        ordering = ['order', 'created_time']
        unique_together = [['stage', 'code']]
    
    def __str__(self):
        return f"{self.stage.name} - {self.name} ({self.milestone_percentage}%)"


class OutputValueEvent(models.Model):
    """产值事件模型"""
    milestone = models.ForeignKey(OutputValueMilestone, on_delete=models.CASCADE, related_name='events',
                                  verbose_name='所属里程碑')
    name = models.CharField(max_length=100, verbose_name='事件名称')
    code = models.CharField(max_length=50, verbose_name='事件编码')
    event_percentage = models.DecimalField(max_digits=5, decimal_places=2, verbose_name='事件产值比例(%)',
                                          help_text='该事件在该里程碑内的比例')
    responsible_role_code = models.CharField(max_length=50, verbose_name='责任岗位编码',
                                            help_text='如：business_manager, project_manager, professional_engineer等')
    description = models.TextField(blank=True, verbose_name='事件描述')
    # 用于关联项目流程中的事件
    trigger_condition = models.CharField(max_length=200, blank=True, verbose_name='触发条件',
                                        help_text='关联项目流程事件的标识，用于自动触发产值计算')
    order = models.IntegerField(default=0, verbose_name='排序')
    is_active = models.BooleanField(default=True, verbose_name='是否启用')
    created_time = models.DateTimeField(default=timezone.now, verbose_name='创建时间')
    updated_time = models.DateTimeField(auto_now=True, verbose_name='更新时间')
    
    class Meta:
        db_table = 'settlement_output_value_event'  # 保持原有表名，避免数据迁移
        verbose_name = '产值事件'
        verbose_name_plural = verbose_name
        ordering = ['order', 'created_time']
        unique_together = [['milestone', 'code']]
    
    def __str__(self):
        return f"{self.milestone.stage.name} - {self.milestone.name} - {self.name} ({self.event_percentage}%)"
    
    def calculate_value(self, base_amount):
        """计算事件产值
        Args:
            base_amount: 计取基数（备案金额、合同金额等）
        Returns:
            计算后的产值金额
        """
        stage_pct = self.milestone.stage.stage_percentage / 100
        milestone_pct = self.milestone.milestone_percentage / 100
        event_pct = self.event_percentage / 100
        
        return base_amount * stage_pct * milestone_pct * event_pct


class OutputValueRecord(models.Model):
    """产值计算记录模型"""
    project = models.ForeignKey('production_management.Project', on_delete=models.CASCADE, related_name='output_value_records',
                               verbose_name='关联项目')
    stage = models.ForeignKey(OutputValueStage, on_delete=models.PROTECT, verbose_name='产值阶段')
    milestone = models.ForeignKey(OutputValueMilestone, on_delete=models.PROTECT, verbose_name='产值里程碑')
    event = models.ForeignKey(OutputValueEvent, on_delete=models.PROTECT, verbose_name='产值事件')
    responsible_user = models.ForeignKey(User, on_delete=models.PROTECT, related_name='output_value_records',
                                        verbose_name='责任人')
    
    # 计算相关字段
    base_amount = models.DecimalField(max_digits=12, decimal_places=2, verbose_name='计取基数')
    base_amount_type = models.CharField(max_length=30, verbose_name='基数类型')
    stage_percentage = models.DecimalField(max_digits=5, decimal_places=2, verbose_name='阶段比例(%)')
    milestone_percentage = models.DecimalField(max_digits=5, decimal_places=2, verbose_name='里程碑比例(%)')
    event_percentage = models.DecimalField(max_digits=5, decimal_places=2, verbose_name='事件比例(%)')
    calculated_value = models.DecimalField(max_digits=12, decimal_places=2, verbose_name='计算产值')
    
    # 状态和记录
    status = models.CharField(max_length=20, choices=[
        ('pending', '待计算'),
        ('calculated', '已计算'),
        ('confirmed', '已确认'),
        ('cancelled', '已取消'),
    ], default='calculated', verbose_name='状态')
    calculated_time = models.DateTimeField(default=timezone.now, verbose_name='计算时间')
    confirmed_time = models.DateTimeField(null=True, blank=True, verbose_name='确认时间')
    confirmed_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True,
                                    related_name='confirmed_output_values', verbose_name='确认人')
    notes = models.TextField(blank=True, verbose_name='备注')
    created_time = models.DateTimeField(default=timezone.now, verbose_name='创建时间')
    
    class Meta:
        db_table = 'settlement_output_value_record'  # 保持原有表名，避免数据迁移
        verbose_name = '产值计算记录'
        verbose_name_plural = verbose_name
        ordering = ['-calculated_time']
        indexes = [
            models.Index(fields=['project', 'status']),
            models.Index(fields=['responsible_user', 'status']),
            models.Index(fields=['calculated_time']),
        ]
    
    def __str__(self):
        return f"{self.project.project_number} - {self.event.name} - {self.calculated_value}"
