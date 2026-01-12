"""
计划管理模块数据模型
"""
from django.db import models
from django.db.models import Max, Q
from django.db import transaction
from django.utils import timezone
from django.core.validators import MinValueValidator, MaxValueValidator
from backend.apps.system_management.models import User, Department


class StrategicGoal(models.Model):
    """战略目标模型"""
    
    GOAL_TYPE_CHOICES = [
        ('financial', '财务目标'),
        ('market', '市场目标'),
        ('operation', '运营目标'),
        ('innovation', '创新目标'),
        ('talent', '人才目标'),
        ('other', '其他'),
    ]
    
    GOAL_PERIOD_CHOICES = [
        ('annual', '年度目标'),
        ('three_year', '三年目标'),
        ('five_year', '五年目标'),
    ]
    
    STATUS_CHOICES = [
        ('draft', '制定中'),
        ('published', '已发布'),
        ('in_progress', '执行中'),
        ('completed', '已完成'),
        ('cancelled', '已取消'),
    ]
    
    INDICATOR_TYPE_CHOICES = [
        ('numeric', '数值型'),
        ('percentage', '百分比型'),
        ('boolean', '布尔型'),
        ('text', '文本型'),
    ]
    
    # 基本信息
    goal_number = models.CharField(max_length=50, unique=True, verbose_name='目标编号', help_text='格式：GOAL-{YYYYMMDD}-{序列号}')
    name = models.CharField(max_length=200, verbose_name='目标名称')
    goal_type = models.CharField(max_length=20, choices=GOAL_TYPE_CHOICES, verbose_name='目标类型')
    goal_period = models.CharField(max_length=20, choices=GOAL_PERIOD_CHOICES, verbose_name='目标周期')
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='draft', verbose_name='目标状态')
    
    # 目标指标
    indicator_name = models.CharField(max_length=100, verbose_name='目标指标名称')
    indicator_type = models.CharField(max_length=20, choices=INDICATOR_TYPE_CHOICES, verbose_name='指标类型')
    indicator_unit = models.CharField(max_length=20, blank=True, verbose_name='指标单位', help_text='如：万元、%、个、次等')
    target_value = models.DecimalField(max_digits=20, decimal_places=2, verbose_name='目标值')
    current_value = models.DecimalField(max_digits=20, decimal_places=2, default=0, verbose_name='当前值')
    completion_rate = models.DecimalField(max_digits=5, decimal_places=2, default=0, verbose_name='完成率', help_text='百分比，自动计算')
    
    # 责任人信息
    responsible_person = models.ForeignKey(
        User, 
        on_delete=models.PROTECT, 
        related_name='responsible_goals',
        verbose_name='目标负责人'
    )
    participants = models.ManyToManyField(
        User, 
        blank=True, 
        related_name='participated_goals',
        verbose_name='参与人员'
    )
    responsible_department = models.ForeignKey(
        Department,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='goals',
        verbose_name='负责部门'
    )
    
    # 目标描述
    description = models.TextField(max_length=2000, verbose_name='目标描述')
    background = models.TextField(blank=True, verbose_name='目标背景')
    significance = models.TextField(blank=True, verbose_name='目标意义')
    
    # 权重设置
    weight = models.DecimalField(
        max_digits=5, 
        decimal_places=2, 
        validators=[MinValueValidator(0), MaxValueValidator(100)],
        verbose_name='目标权重',
        help_text='范围0-100'
    )
    weight_description = models.TextField(blank=True, verbose_name='权重说明')
    
    # 时间信息
    start_date = models.DateField(verbose_name='开始日期')
    end_date = models.DateField(verbose_name='结束日期')
    duration_days = models.IntegerField(verbose_name='目标周期（天）', help_text='自动计算')
    
    # 关联信息
    parent_goal = models.ForeignKey(
        'self',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='child_goals',
        verbose_name='上级目标',
        help_text='用于目标分解'
    )
    related_projects = models.ManyToManyField(
        'production_management.Project',
        blank=True,
        related_name='related_goals',
        verbose_name='关联项目'
    )
    notes = models.TextField(blank=True, verbose_name='备注')
    
    # 系统字段
    created_by = models.ForeignKey(
        User,
        on_delete=models.PROTECT,
        related_name='created_goals',
        verbose_name='创建人'
    )
    created_time = models.DateTimeField(default=timezone.now, verbose_name='创建时间')
    updated_time = models.DateTimeField(auto_now=True, verbose_name='更新时间')
    
    class Meta:
        db_table = 'plan_strategic_goal'
        verbose_name = '战略目标'
        verbose_name_plural = verbose_name
        ordering = ['-created_time']
        indexes = [
            models.Index(fields=['goal_number']),
            models.Index(fields=['status']),
            models.Index(fields=['goal_type']),
            models.Index(fields=['goal_period']),
            models.Index(fields=['responsible_person']),
            models.Index(fields=['start_date', 'end_date']),
            models.Index(fields=['parent_goal']),
        ]
    
    def __str__(self):
        return f"{self.goal_number} - {self.name}"
    
    def generate_goal_number(self):
        """生成目标编号：GOAL-{YYYYMMDD}-{序列号}"""
        prefix = 'GOAL'
        date_str = timezone.now().strftime('%Y%m%d')
        pattern = f"{prefix}-{date_str}-"
        
        # 使用事务和锁确保线程安全
        with transaction.atomic():
            # 获取当天最大序列号
            max_number = StrategicGoal.objects.filter(
                goal_number__startswith=pattern
            ).aggregate(max_num=Max('goal_number'))['max_num']
            
            if max_number:
                # 提取序列号并加1
                try:
                    seq = int(max_number.split('-')[-1]) + 1
                except (ValueError, IndexError):
                    seq = 1
            else:
                seq = 1
            
            return f"{pattern}{seq:04d}"
    
    def calculate_completion_rate(self):
        """计算完成率"""
        if self.target_value and self.target_value > 0:
            rate = (self.current_value / self.target_value) * 100
            return min(rate, 100)  # 完成率不超过100%
        return 0
    
    def calculate_duration_days(self):
        """计算目标周期（天）"""
        if self.start_date and self.end_date:
            return (self.end_date - self.start_date).days + 1
        return 0
    
    def save(self, *args, **kwargs):
        # 自动生成目标编号
        if not self.goal_number:
            self.goal_number = self.generate_goal_number()
        
        # 自动计算完成率
        self.completion_rate = self.calculate_completion_rate()
        
        # 自动计算周期天数
        self.duration_days = self.calculate_duration_days()
        
        super().save(*args, **kwargs)
    
    def get_valid_transitions(self):
        """获取有效的状态转换"""
        transitions = {
            'draft': ['published', 'cancelled'],
            'published': ['in_progress', 'cancelled'],
            'in_progress': ['completed', 'cancelled'],
            'completed': [],
            'cancelled': [],
        }
        return transitions.get(self.status, [])
    
    def can_transition_to(self, new_status):
        """检查是否可以转换到指定状态"""
        return new_status in self.get_valid_transitions()
    
    def transition_to(self, new_status, user=None):
        """转换状态"""
        if not self.can_transition_to(new_status):
            raise ValueError(f"无法从 {self.get_status_display()} 转换到 {new_status}")
        
        old_status = self.status
        self.status = new_status
        self.save()
        
        # 记录状态转换日志
        GoalStatusLog.objects.create(
            goal=self,
            old_status=old_status,
            new_status=new_status,
            changed_by=user,
            change_reason='状态转换'
        )
    
    def has_related_plans(self):
        """检查是否有关联的计划"""
        return Plan.objects.filter(related_goal=self).exists()
    
    def get_child_goals_count(self):
        """获取下级目标数量"""
        return self.child_goals.count()
    
    def get_all_descendants(self):
        """获取所有下级目标（递归）"""
        descendants = []
        for child in self.child_goals.all():
            descendants.append(child)
            descendants.extend(child.get_all_descendants())
        return descendants


class GoalStatusLog(models.Model):
    """目标状态转换日志"""
    goal = models.ForeignKey(
        StrategicGoal,
        on_delete=models.CASCADE,
        related_name='status_logs',
        verbose_name='目标'
    )
    old_status = models.CharField(max_length=20, verbose_name='原状态')
    new_status = models.CharField(max_length=20, verbose_name='新状态')
    change_reason = models.CharField(max_length=500, blank=True, verbose_name='变更原因')
    changed_by = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='goal_status_changes',
        verbose_name='变更人'
    )
    changed_time = models.DateTimeField(default=timezone.now, verbose_name='变更时间')
    notes = models.TextField(blank=True, verbose_name='备注')
    
    class Meta:
        db_table = 'plan_goal_status_log'
        verbose_name = '目标状态日志'
        verbose_name_plural = verbose_name
        ordering = ['-changed_time']
        indexes = [
            models.Index(fields=['goal', '-changed_time']),
        ]
    
    def __str__(self):
        return f"{self.goal.goal_number} - {self.old_status} → {self.new_status}"


class GoalProgressRecord(models.Model):
    """目标进度记录"""
    goal = models.ForeignKey(
        StrategicGoal,
        on_delete=models.CASCADE,
        related_name='progress_records',
        verbose_name='目标'
    )
    current_value = models.DecimalField(max_digits=20, decimal_places=2, verbose_name='当前值')
    completion_rate = models.DecimalField(max_digits=5, decimal_places=2, verbose_name='完成率')
    progress_description = models.TextField(verbose_name='进度说明')
    recorded_by = models.ForeignKey(
        User,
        on_delete=models.PROTECT,
        related_name='recorded_goal_progress',
        verbose_name='记录人'
    )
    recorded_time = models.DateTimeField(default=timezone.now, verbose_name='记录时间')
    notes = models.TextField(blank=True, verbose_name='备注')
    
    class Meta:
        db_table = 'plan_goal_progress_record'
        verbose_name = '目标进度记录'
        verbose_name_plural = verbose_name
        ordering = ['-recorded_time']
        indexes = [
            models.Index(fields=['goal', '-recorded_time']),
        ]
    
    def __str__(self):
        return f"{self.goal.goal_number} - {self.recorded_time.strftime('%Y-%m-%d')} - {self.completion_rate}%"


class GoalAdjustment(models.Model):
    """目标调整申请"""
    STATUS_CHOICES = [
        ('pending', '待审批'),
        ('approved', '已批准'),
        ('rejected', '已拒绝'),
    ]
    
    goal = models.ForeignKey(
        StrategicGoal,
        on_delete=models.CASCADE,
        related_name='adjustments',
        verbose_name='目标'
    )
    adjustment_reason = models.TextField(verbose_name='调整原因')
    adjustment_content = models.TextField(verbose_name='调整内容')
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='pending', verbose_name='审批状态')
    
    # 调整后的值（如果调整）
    new_target_value = models.DecimalField(
        max_digits=20, 
        decimal_places=2, 
        null=True, 
        blank=True,
        verbose_name='新目标值'
    )
    new_end_date = models.DateField(null=True, blank=True, verbose_name='新结束日期')
    
    # 审批信息
    approved_by = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='approved_goal_adjustments',
        verbose_name='审批人'
    )
    approved_time = models.DateTimeField(null=True, blank=True, verbose_name='审批时间')
    approval_notes = models.TextField(blank=True, verbose_name='审批意见')
    
    # 系统字段
    created_by = models.ForeignKey(
        User,
        on_delete=models.PROTECT,
        related_name='created_goal_adjustments',
        verbose_name='申请人'
    )
    created_time = models.DateTimeField(default=timezone.now, verbose_name='申请时间')
    updated_time = models.DateTimeField(auto_now=True, verbose_name='更新时间')
    
    class Meta:
        db_table = 'plan_goal_adjustment'
        verbose_name = '目标调整申请'
        verbose_name_plural = verbose_name
        ordering = ['-created_time']
        indexes = [
            models.Index(fields=['goal', '-created_time']),
            models.Index(fields=['status']),
        ]
    
    def __str__(self):
        return f"{self.goal.goal_number} - 调整申请 - {self.get_status_display()}"


class GoalAlignmentRecord(models.Model):
    """目标对齐度记录"""
    parent_goal = models.ForeignKey(
        StrategicGoal,
        on_delete=models.CASCADE,
        related_name='child_alignment_records',
        verbose_name='上级目标'
    )
    child_goal = models.ForeignKey(
        StrategicGoal,
        on_delete=models.CASCADE,
        related_name='parent_alignment_records',
        verbose_name='下级目标'
    )
    alignment_score = models.DecimalField(
        max_digits=5,
        decimal_places=2,
        verbose_name='对齐度评分',
        help_text='0-100分'
    )
    alignment_analysis = models.TextField(blank=True, verbose_name='对齐度分析')
    suggestions = models.TextField(blank=True, verbose_name='提升建议')
    recorded_time = models.DateTimeField(default=timezone.now, verbose_name='记录时间')
    
    class Meta:
        db_table = 'plan_goal_alignment_record'
        verbose_name = '目标对齐度记录'
        verbose_name_plural = verbose_name
        unique_together = [['parent_goal', 'child_goal']]
        indexes = [
            models.Index(fields=['parent_goal', 'child_goal']),
        ]
    
    def __str__(self):
        return f"{self.parent_goal.goal_number} ↔ {self.child_goal.goal_number} - {self.alignment_score}分"


# 在文件末尾添加，确保Plan模型在StrategicGoal之后定义
# Plan模型定义在上面已添加


# ==================== 计划管理模型 ====================

class Plan(models.Model):
    """计划模型"""
    
    PLAN_TYPE_CHOICES = [
        ('personal', '个人计划'),
        ('department', '部门计划'),
        ('company', '公司计划'),
        ('project', '项目计划'),
    ]
    
    PLAN_PERIOD_CHOICES = [
        ('daily', '日计划'),
        ('weekly', '周计划'),
        ('monthly', '月计划'),
        ('quarterly', '季度计划'),
        ('yearly', '年计划'),
    ]
    
    STATUS_CHOICES = [
        ('draft', '草稿'),
        ('in_progress', '执行中'),
        ('completed', '已完成'),
        ('cancelled', '已取消'),
    ]
    
    PRIORITY_CHOICES = [
        ('high', '高'),
        ('medium', '中'),
        ('low', '低'),
    ]
    
    # 基本信息
    plan_number = models.CharField(max_length=50, unique=True, verbose_name='计划编号', help_text='格式：PLAN-{YYYYMMDD}-{序列号}')
    name = models.CharField(max_length=200, verbose_name='计划名称')
    plan_type = models.CharField(max_length=20, choices=PLAN_TYPE_CHOICES, verbose_name='计划类型')
    plan_period = models.CharField(max_length=20, choices=PLAN_PERIOD_CHOICES, verbose_name='计划周期')
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='draft', verbose_name='计划状态')
    
    # 关联战略目标
    related_goal = models.ForeignKey(
        StrategicGoal,
        on_delete=models.PROTECT,
        related_name='related_plans',
        verbose_name='关联战略目标',
        help_text='必填，选择关联的战略目标'
    )
    alignment_score = models.DecimalField(
        max_digits=5,
        decimal_places=2,
        default=0,
        verbose_name='目标对齐度',
        help_text='0-100分，自动计算'
    )
    contribution_score = models.DecimalField(
        max_digits=5,
        decimal_places=2,
        default=0,
        verbose_name='贡献度评估',
        help_text='0-100分，评估计划对战略目标的贡献度'
    )
    
    # 计划内容
    content = models.TextField(max_length=5000, verbose_name='计划内容', help_text='支持富文本')
    plan_objective = models.TextField(max_length=1000, verbose_name='计划目标')
    description = models.TextField(blank=True, verbose_name='计划描述')
    
    # 时间信息
    start_time = models.DateTimeField(verbose_name='计划开始时间')
    end_time = models.DateTimeField(verbose_name='计划结束时间')
    duration_days = models.IntegerField(verbose_name='计划周期（天）', help_text='自动计算')
    
    # 责任人信息
    responsible_person = models.ForeignKey(
        User,
        on_delete=models.PROTECT,
        related_name='responsible_plans',
        verbose_name='计划负责人'
    )
    participants = models.ManyToManyField(
        User,
        blank=True,
        related_name='participated_plans',
        verbose_name='协作人员'
    )
    collaboration_plan = models.TextField(
        blank=True,
        verbose_name='协作计划',
        help_text='如果选择了协作人员，必须填写协作计划'
    )
    responsible_department = models.ForeignKey(
        Department,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='plans',
        verbose_name='负责部门'
    )
    
    # 优先级和预算
    priority = models.CharField(max_length=10, choices=PRIORITY_CHOICES, default='medium', verbose_name='计划优先级')
    budget = models.DecimalField(
        max_digits=15,
        decimal_places=2,
        null=True,
        blank=True,
        verbose_name='计划预算',
        help_text='单位：元'
    )
    
    # 关联信息
    related_project = models.ForeignKey(
        'production_management.Project',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='related_plans',
        verbose_name='关联项目'
    )
    parent_plan = models.ForeignKey(
        'self',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='child_plans',
        verbose_name='父计划',
        help_text='用于计划分解'
    )
    notes = models.TextField(blank=True, verbose_name='备注')
    
    # 进度信息
    progress = models.DecimalField(
        max_digits=5,
        decimal_places=2,
        default=0,
        verbose_name='执行进度',
        help_text='百分比，0-100'
    )
    
    # 系统字段
    created_by = models.ForeignKey(
        User,
        on_delete=models.PROTECT,
        related_name='created_plans',
        verbose_name='创建人'
    )
    created_time = models.DateTimeField(default=timezone.now, verbose_name='创建时间')
    updated_time = models.DateTimeField(auto_now=True, verbose_name='更新时间')
    
    class Meta:
        db_table = 'plan_plan'
        verbose_name = '计划'
        verbose_name_plural = verbose_name
        ordering = ['-created_time']
        indexes = [
            models.Index(fields=['plan_number']),
            models.Index(fields=['status']),
            models.Index(fields=['plan_type']),
            models.Index(fields=['plan_period']),
            models.Index(fields=['responsible_person']),
            models.Index(fields=['related_goal']),
            models.Index(fields=['start_time', 'end_time']),
            models.Index(fields=['parent_plan']),
        ]
    
    def __str__(self):
        return f"{self.plan_number} - {self.name}"
    
    def generate_plan_number(self):
        """生成计划编号：PLAN-{YYYYMMDD}-{序列号}"""
        prefix = 'PLAN'
        date_str = timezone.now().strftime('%Y%m%d')
        pattern = f"{prefix}-{date_str}-"
        
        # 使用事务和锁确保线程安全
        with transaction.atomic():
            # 获取当天最大序列号
            max_number = Plan.objects.filter(
                plan_number__startswith=pattern
            ).aggregate(max_num=Max('plan_number'))['max_num']
            
            if max_number:
                # 提取序列号并加1
                try:
                    seq = int(max_number.split('-')[-1]) + 1
                except (ValueError, IndexError):
                    seq = 1
            else:
                seq = 1
            
            return f"{pattern}{seq:04d}"
    
    def calculate_duration_days(self):
        """计算计划周期（天）"""
        if self.start_time and self.end_time:
            return (self.end_time.date() - self.start_time.date()).days + 1
        return 0
    
    def calculate_alignment_score(self):
        """计算目标对齐度（简化版，后续可完善）"""
        # TODO: 实现更复杂的对齐度计算算法
        # 目前返回默认值，后续可以根据计划目标与战略目标的匹配度计算
        return 0
    
    def determine_status(self):
        """根据实际情况自动判断计划状态"""
        now = timezone.now()
        
        # 如果计划已完成（进度100%），状态为已完成
        if self.progress >= 100:
            return 'completed'
        
        # 如果计划已取消，保持取消状态
        if self.status == 'cancelled':
            return 'cancelled'
        
        # P1: 简化状态判断，不包含审批流程
        # 如果计划正在执行中，根据时间判断是否需要调整
        if self.status == 'in_progress':
            if self.end_time and now > self.end_time:
                # 已过结束时间，如果进度100%则完成，否则保持执行中
                if self.progress >= 100:
                    return 'completed'
                return 'in_progress'
            return 'in_progress'
        
        # 新建计划时，根据时间判断初始状态
        if not self.pk:  # 新建计划
            if self.start_time:
                if now >= self.start_time:
                    # 开始时间已过，直接进入执行中（P1 不包含审批流程）
                    return 'in_progress'
                else:
                    # 开始时间未到，设置为草稿
                    return 'draft'
            else:
                # 开始时间未设置，默认为草稿
                return 'draft'
        
        # 其他情况保持原状态
        return self.status or 'draft'
    
    def save(self, *args, **kwargs):
        # 自动生成计划编号
        if not self.plan_number:
            self.plan_number = self.generate_plan_number()
        
        # 自动计算周期天数
        self.duration_days = self.calculate_duration_days()
        
        # 自动计算对齐度（如果未设置）
        if self.alignment_score == 0:
            self.alignment_score = self.calculate_alignment_score()
        
        # P1: 状态变更必须通过裁决器，不在 save() 中直接设置
        # 新建计划默认状态为 draft（由数据库默认值或表单设置）
        if not self.pk and not self.status:
            self.status = 'draft'
        
        super().save(*args, **kwargs)
    
    def get_valid_transitions(self):
        """获取有效的状态转换（P1：只支持 4 状态）"""
        transitions = {
            'draft': ['in_progress', 'cancelled'],
            'in_progress': ['completed', 'cancelled'],
            'completed': [],
            'cancelled': [],
        }
        return transitions.get(self.status, [])
    
    def can_transition_to(self, new_status):
        """检查是否可以转换到指定状态"""
        return new_status in self.get_valid_transitions()
    
    def transition_to(self, new_status, user=None):
        """转换状态"""
        if not self.can_transition_to(new_status):
            raise ValueError(f"无法从 {self.get_status_display()} 转换到 {new_status}")
        
        old_status = self.status
        self.status = new_status
        self.save()
        
        # 记录状态转换日志
        PlanStatusLog.objects.create(
            plan=self,
            old_status=old_status,
            new_status=new_status,
            changed_by=user,
            change_reason='状态转换'
        )
    
    def get_child_plans_count(self):
        """获取下级计划数量"""
        return self.child_plans.count()
    
    def get_all_descendants(self):
        """获取所有下级计划（递归）"""
        descendants = []
        for child in self.child_plans.all():
            descendants.append(child)
            descendants.extend(child.get_all_descendants())
        return descendants


class PlanStatusLog(models.Model):
    """计划状态转换日志"""
    plan = models.ForeignKey(
        Plan,
        on_delete=models.CASCADE,
        related_name='status_logs',
        verbose_name='计划'
    )
    old_status = models.CharField(max_length=20, verbose_name='原状态')
    new_status = models.CharField(max_length=20, verbose_name='新状态')
    change_reason = models.CharField(max_length=500, blank=True, verbose_name='变更原因')
    changed_by = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='plan_status_changes',
        verbose_name='变更人'
    )
    changed_time = models.DateTimeField(default=timezone.now, verbose_name='变更时间')
    notes = models.TextField(blank=True, verbose_name='备注')
    
    class Meta:
        db_table = 'plan_plan_status_log'
        verbose_name = '计划状态日志'
        verbose_name_plural = verbose_name
        ordering = ['-changed_time']
        indexes = [
            models.Index(fields=['plan', '-changed_time']),
        ]
    
    def __str__(self):
        return f"{self.plan.plan_number} - {self.old_status} → {self.new_status}"


class PlanProgressRecord(models.Model):
    """计划进度记录"""
    plan = models.ForeignKey(
        Plan,
        on_delete=models.CASCADE,
        related_name='progress_records',
        verbose_name='计划'
    )
    progress = models.DecimalField(max_digits=5, decimal_places=2, verbose_name='进度百分比')
    progress_description = models.TextField(verbose_name='进度说明')
    execution_result = models.TextField(blank=True, verbose_name='执行结果')
    execution_issues = models.TextField(blank=True, verbose_name='执行问题')
    recorded_by = models.ForeignKey(
        User,
        on_delete=models.PROTECT,
        related_name='recorded_plan_progress',
        verbose_name='记录人'
    )
    recorded_time = models.DateTimeField(default=timezone.now, verbose_name='记录时间')
    notes = models.TextField(blank=True, verbose_name='备注')
    
    class Meta:
        db_table = 'plan_plan_progress_record'
        verbose_name = '计划进度记录'
        verbose_name_plural = verbose_name
        ordering = ['-recorded_time']
        indexes = [
            models.Index(fields=['plan', '-recorded_time']),
        ]
    
    def __str__(self):
        return f"{self.plan.plan_number} - {self.recorded_time.strftime('%Y-%m-%d')} - {self.progress}%"


class PlanIssue(models.Model):
    """计划问题模型"""
    SEVERITY_CHOICES = [
        ('critical', '严重'),
        ('high', '高'),
        ('medium', '中'),
        ('low', '低'),
    ]
    
    STATUS_CHOICES = [
        ('open', '待处理'),
        ('in_progress', '处理中'),
        ('resolved', '已解决'),
        ('closed', '已关闭'),
    ]
    
    plan = models.ForeignKey(
        Plan,
        on_delete=models.CASCADE,
        related_name='issues',
        verbose_name='计划'
    )
    title = models.CharField(max_length=200, verbose_name='问题标题')
    description = models.TextField(verbose_name='问题描述')
    severity = models.CharField(max_length=20, choices=SEVERITY_CHOICES, default='medium', verbose_name='严重程度')
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='open', verbose_name='问题状态')
    solution = models.TextField(blank=True, verbose_name='解决方案')
    
    # 责任人
    assigned_to = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='assigned_plan_issues',
        verbose_name='负责人'
    )
    
    # 时间信息
    discovered_time = models.DateTimeField(default=timezone.now, verbose_name='发现时间')
    resolved_time = models.DateTimeField(null=True, blank=True, verbose_name='解决时间')
    
    # 系统字段
    created_by = models.ForeignKey(
        User,
        on_delete=models.PROTECT,
        related_name='created_plan_issues',
        verbose_name='创建人'
    )
    created_time = models.DateTimeField(default=timezone.now, verbose_name='创建时间')
    updated_time = models.DateTimeField(auto_now=True, verbose_name='更新时间')
    
    class Meta:
        db_table = 'plan_plan_issue'
        verbose_name = '计划问题'
        verbose_name_plural = verbose_name
        ordering = ['-created_time']
        indexes = [
            models.Index(fields=['plan', '-created_time']),
            models.Index(fields=['status']),
            models.Index(fields=['severity']),
        ]
    
    def __str__(self):
        return f"{self.plan.plan_number} - {self.title}"


class PlanApproval(models.Model):
    """计划审批记录"""
    STATUS_CHOICES = [
        ('pending', '待审批'),
        ('approved', '已批准'),
        ('rejected', '已拒绝'),
    ]
    
    plan = models.ForeignKey(
        Plan,
        on_delete=models.CASCADE,
        related_name='approvals',
        verbose_name='计划'
    )
    approval_node = models.CharField(max_length=100, verbose_name='审批节点')
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='pending', verbose_name='审批状态')
    approval_opinion = models.TextField(verbose_name='审批意见')
    approval_notes = models.TextField(blank=True, verbose_name='审批说明')
    
    # 审批人
    approved_by = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='approved_plans',
        verbose_name='审批人'
    )
    approved_time = models.DateTimeField(null=True, blank=True, verbose_name='审批时间')
    
    # 系统字段
    created_time = models.DateTimeField(default=timezone.now, verbose_name='创建时间')
    updated_time = models.DateTimeField(auto_now=True, verbose_name='更新时间')
    
    class Meta:
        db_table = 'plan_plan_approval'
        verbose_name = '计划审批记录'
        verbose_name_plural = verbose_name
        ordering = ['-created_time']
        indexes = [
            models.Index(fields=['plan', '-created_time']),
            models.Index(fields=['status']),
        ]
    
    def __str__(self):
        return f"{self.plan.plan_number} - {self.approval_node} - {self.get_status_display()}"


class PlanDecision(models.Model):
    """计划决策记录（P1 轻量审批模型）"""
    
    REQUEST_TYPES = [
        ('start', '启动计划'),
        ('cancel', '取消计划'),
    ]
    
    DECISION_CHOICES = [
        ('approve', '通过'),
        ('reject', '驳回'),
    ]
    
    # 关联计划
    plan = models.ForeignKey(
        Plan,
        on_delete=models.CASCADE,
        related_name='decisions',
        verbose_name='计划'
    )
    
    # 请求类型（拆分为两段）
    request_type = models.CharField(
        max_length=20,
        choices=REQUEST_TYPES,
        verbose_name='请求类型'
    )
    
    # 决策结果（pending 时为空）
    decision = models.CharField(
        max_length=20,
        choices=DECISION_CHOICES,
        null=True,
        blank=True,
        verbose_name='决策结果'
    )
    
    # 请求信息
    requested_by = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        null=True,
        related_name='requested_plan_decisions',
        verbose_name='请求人'
    )
    requested_at = models.DateTimeField(
        auto_now_add=True,
        verbose_name='请求时间'
    )
    
    # 决策信息（pending 判定：decided_at is null）
    decided_by = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='decided_plan_decisions',
        verbose_name='决策人'
    )
    decided_at = models.DateTimeField(
        null=True,
        blank=True,
        verbose_name='决策时间'
    )
    
    # 原因/说明
    reason = models.TextField(
        blank=True,
        verbose_name='原因说明'
    )
    
    class Meta:
        db_table = 'plan_decision'
        verbose_name = '计划决策记录'
        verbose_name_plural = verbose_name
        ordering = ['-requested_at']
        # 约束：同一 plan + request_type 同时只能存在 1 条 pending
        constraints = [
            models.UniqueConstraint(
                fields=['plan', 'request_type'],
                condition=models.Q(decided_at__isnull=True),
                name='unique_pending_decision_per_plan_request_type'
            )
        ]
        indexes = [
            models.Index(fields=['plan', '-requested_at']),
            models.Index(fields=['request_type', 'decided_at']),
        ]
    
    @property
    def is_pending(self):
        """判断是否为待处理状态"""
        return self.decided_at is None
    
    def __str__(self):
        decision_text = self.get_decision_display() if self.decision else '待处理'
        return f"{self.plan.plan_number} - {self.get_request_type_display()} - {decision_text}"

