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
        ('half_year', '半年目标'),
        ('quarterly', '季度目标'),
    ]
    
    LEVEL_CHOICES = [
        ('company', '公司目标'),
        ('personal', '个人目标'),
    ]
    
    STATUS_CHOICES = [
        ('draft', '制定中'),
        ('published', '已发布'),
        ('accepted', '已接收'),
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
    level = models.CharField(max_length=20, choices=LEVEL_CHOICES, default='company', verbose_name='目标层级', help_text='company=公司目标, personal=个人目标')
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
    owner = models.ForeignKey(
        User,
        on_delete=models.PROTECT,
        related_name='owned_goals',
        null=True,
        blank=True,
        verbose_name='目标所有者',
        help_text='个人目标必填，公司目标可为空'
    )
    responsible_person = models.ForeignKey(
        User, 
        on_delete=models.PROTECT, 
        related_name='responsible_goals',
        verbose_name='负责人'
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
        verbose_name='所属部门'
    )
    
    # 目标描述
    description = models.TextField(max_length=2000, blank=True, verbose_name='目标描述')
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
    duration_days = models.IntegerField(default=0, verbose_name='目标周期（天）', help_text='自动计算')
    
    # 状态时间戳（P2-1：统一状态机）
    published_at = models.DateTimeField(null=True, blank=True, verbose_name='发布时间', help_text='状态变为 published 时自动记录')
    accepted_at = models.DateTimeField(null=True, blank=True, verbose_name='接收时间', help_text='状态变为 accepted 时自动记录')
    completed_at = models.DateTimeField(null=True, blank=True, verbose_name='完成时间', help_text='状态变为 completed 时自动记录')
    
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
        # 禁用 Django 默认权限（add, change, delete, view）
        # 使用自定义业务权限系统（plan_management.goal.view 等）
        default_permissions = ()
        indexes = [
            models.Index(fields=['goal_number']),
            models.Index(fields=['status']),
            models.Index(fields=['level']),
            models.Index(fields=['owner']),
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
        """
        获取有效的状态转换（P2-1：统一状态机规则）
        
        状态机规则：
        draft → published → accepted → in_progress → completed
                      ↘ cancelled
        
        - draft: 制定中
        - published: 已发布（已下达）
        - accepted: 已接收（员工确认）
        - in_progress: 执行中（自动/人工进入）
        - completed: 已完成（满足完成条件）
        - cancelled: 已取消（可从 draft 或 published 取消）
        """
        transitions = {
            'draft': ['published', 'cancelled'],
            'published': ['accepted', 'cancelled'],
            'accepted': ['in_progress', 'cancelled'],
            'in_progress': ['completed', 'cancelled'],
            'completed': [],
            'cancelled': [],
        }
        return transitions.get(self.status, [])
    
    def can_transition_to(self, new_status):
        """检查是否可以转换到指定状态"""
        return new_status in self.get_valid_transitions()
    
    def transition_to(self, new_status, user=None):
        """
        转换状态（P2-1：统一状态机，自动记录时间戳）
        """
        if not self.can_transition_to(new_status):
            raise ValueError(f"无法从 {self.get_status_display()} 转换到 {new_status}")
        
        old_status = self.status
        now = timezone.now()
        
        # 自动记录状态时间戳
        if new_status == 'published' and not self.published_at:
            self.published_at = now
        elif new_status == 'accepted' and not self.accepted_at:
            self.accepted_at = now
        elif new_status == 'completed' and not self.completed_at:
            self.completed_at = now
        
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
    """计划模型（P2-1：统一模型与状态机）"""
    
    LEVEL_CHOICES = [
        ('company', '公司计划'),
        ('personal', '个人计划'),
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
        ('published', '已发布'),
        ('accepted', '已接收'),
        ('in_progress', '执行中'),
        ('completed', '已完成'),
        ('cancelled', '已取消'),
    ]
    
    # 基本信息
    plan_number = models.CharField(max_length=50, unique=True, verbose_name='计划编号', help_text='格式：PLAN-{YYYYMMDD}-{序列号}')
    name = models.CharField(max_length=200, verbose_name='计划名称')
    level = models.CharField(max_length=20, choices=LEVEL_CHOICES, default='company', verbose_name='计划层级', help_text='company=公司计划, personal=个人计划')
    plan_period = models.CharField(max_length=20, choices=PLAN_PERIOD_CHOICES, verbose_name='计划周期')
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='draft', verbose_name='计划状态')
    
    # 关联战略目标
    related_goal = models.ForeignKey(
        StrategicGoal,
        on_delete=models.PROTECT,
        related_name='related_plans',
        null=True,
        blank=True,
        verbose_name='关联战略目标',
        help_text='选择关联的战略目标（必填）'
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
    acceptance_criteria = models.CharField(
        max_length=2000,
        blank=False,
        verbose_name='验收标准',
        help_text='明确说明如何判定计划完成'
    )
    
    # 时间信息
    start_time = models.DateTimeField(verbose_name='计划开始时间')
    end_time = models.DateTimeField(verbose_name='计划结束时间')
    duration_days = models.IntegerField(default=0, verbose_name='计划周期（天）', help_text='自动计算')
    
    # 状态时间戳（P2-1：统一状态机）
    published_at = models.DateTimeField(null=True, blank=True, verbose_name='发布时间', help_text='状态变为 published 时自动记录')
    accepted_at = models.DateTimeField(null=True, blank=True, verbose_name='接收时间', help_text='状态变为 accepted 时自动记录')
    completed_at = models.DateTimeField(null=True, blank=True, verbose_name='完成时间', help_text='状态变为 completed 时自动记录')
    
    # 责任人信息
    owner = models.ForeignKey(
        User,
        on_delete=models.PROTECT,
        related_name='owned_plans',
        null=True,
        blank=True,
        verbose_name='计划所有者',
        help_text='个人计划必填，公司计划可为空'
    )
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
        verbose_name='所属部门'
    )
    
    
    # 关联信息
    related_project = models.CharField(
        max_length=200,
        blank=True,
        verbose_name='关联项目',
        help_text='项目信息来源于商机管理'
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
    
    # 公司和组织部门（用于数据隔离）
    company = models.ForeignKey(
        'system_management.OurCompany',
        on_delete=models.PROTECT,
        null=True,
        blank=True,
        related_name='plans',
        verbose_name='公司'
    )
    org_department = models.ForeignKey(
        Department,
        on_delete=models.PROTECT,
        null=True,
        blank=True,
        related_name='org_plans',
        verbose_name='部门'
    )
    
    # 进度信息
    progress = models.DecimalField(
        max_digits=5,
        decimal_places=2,
        default=0,
        verbose_name='执行进度',
        help_text='百分比，0-100'
    )
    
    # 风险预警（周计划专用）
    is_overdue = models.BooleanField(default=False, db_index=True, verbose_name='是否逾期', help_text='周计划提交是否逾期')
    overdue_days = models.IntegerField(default=0, verbose_name='逾期天数', help_text='周计划逾期天数')
    risk_level = models.CharField(
        max_length=20,
        choices=[
            ('low', '低风险'),
            ('medium', '中风险'),
            ('high', '高风险'),
            ('critical', '严重风险'),
        ],
        default='low',
        blank=True,
        verbose_name='风险等级',
        help_text='周计划逾期风险等级'
    )
    submission_deadline = models.DateTimeField(
        null=True,
        blank=True,
        verbose_name='提交截止时间',
        help_text='周计划提交截止时间（每周五18:00）'
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
        # 禁用 Django 默认权限（add, change, delete, view）
        # 使用自定义业务权限系统（plan_management.plan.view 等）
        default_permissions = ()
        indexes = [
            models.Index(fields=['plan_number']),
            models.Index(fields=['status']),
            models.Index(fields=['level']),
            models.Index(fields=['owner']),
            models.Index(fields=['plan_period']),
            models.Index(fields=['responsible_person']),
            models.Index(fields=['related_goal']),
            models.Index(fields=['start_time', 'end_time']),
            models.Index(fields=['parent_plan']),
            models.Index(fields=['is_overdue', 'risk_level']),
            models.Index(fields=['plan_period', 'is_overdue']),
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
        
        # 周计划：自动计算提交截止时间（每周五18:00）
        if self.plan_period == 'weekly' and self.start_time:
            if not self.submission_deadline:
                self.submission_deadline = self.calculate_weekly_submission_deadline()
        
        # 检查周计划是否逾期
        if self.plan_period == 'weekly':
            self.check_overdue_status()
        
        # P1: 状态变更必须通过裁决器，不在 save() 中直接设置
        # 新建计划默认状态为 draft（由数据库默认值或表单设置）
        if not self.pk and not self.status:
            self.status = 'draft'
        
        # 修复：确保 plan_type 字段有值（数据库字段仍然存在，需要向后兼容）
        # plan_type 字段已迁移到 level 字段，但数据库表中仍存在该字段且不允许为 null
        # 将 level 的值映射到 plan_type（用于向后兼容）
        from django.db import connection
        
        # 映射 level 到 plan_type
        level_to_plan_type_map = {
            'company': 'company',
            'personal': 'personal',
        }
        plan_type_value = level_to_plan_type_map.get(self.level, 'company')
        
        is_new = not self.pk
        
        # 先保存记录（使用 update_fields 避免触发其他信号）
        update_fields = kwargs.get('update_fields', None)
        super().save(*args, **kwargs)
        
        # 保存后立即更新 plan_type 字段（使用原始 SQL，因为模型中没有这个字段）
        with connection.cursor() as cursor:
            cursor.execute(
                "UPDATE plan_plan SET plan_type = %s WHERE id = %s",
                [plan_type_value, self.pk]
            )
    
    def get_valid_transitions(self):
        """
        获取有效的状态转换（P2-1：统一状态机规则）
        
        状态机规则：
        draft → published → accepted → in_progress → completed
                      ↘ cancelled
        
        - draft: 草稿
        - published: 已发布（已下达，审批通过后）
        - accepted: 已接收（员工确认）
        - in_progress: 执行中（自动/人工进入）
        - completed: 已完成（满足完成条件）
        - cancelled: 已取消（可从 draft 或 published 取消）
        
        注意：draft -> published 必须通过审批流程（PlanDecision）
        """
        transitions = {
            'draft': ['published', 'cancelled'],
            'published': ['accepted', 'cancelled'],
            'accepted': ['in_progress', 'cancelled'],
            'in_progress': ['completed', 'cancelled'],
            'completed': [],
            'cancelled': [],
        }
        return transitions.get(self.status, [])
    
    def can_transition_to(self, new_status):
        """检查是否可以转换到指定状态"""
        return new_status in self.get_valid_transitions()
    
    def transition_to(self, new_status, user=None):
        """
        转换状态（P2-1：统一状态机，自动记录时间戳）
        """
        if not self.can_transition_to(new_status):
            raise ValueError(f"无法从 {self.get_status_display()} 转换到 {new_status}")
        
        old_status = self.status
        now = timezone.now()
        
        # 自动记录状态时间戳
        if new_status == 'published' and not self.published_at:
            self.published_at = now
        elif new_status == 'accepted' and not self.accepted_at:
            self.accepted_at = now
        elif new_status == 'completed' and not self.completed_at:
            self.completed_at = now
        
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
    
    def calculate_weekly_submission_deadline(self):
        """
        计算周计划的提交截止时间（每周五18:00）
        
        规则：
        - 如果计划开始时间是周一，则截止时间是当周周五18:00
        - 如果计划开始时间是其他时间，则截止时间是下一个周五18:00
        """
        if self.plan_period != 'weekly' or not self.start_time:
            return None
        
        from datetime import timedelta
        
        start_date = self.start_time.date()
        # 获取计划开始日期所在周的周一
        days_since_monday = start_date.weekday()  # 0=Monday, 6=Sunday
        monday = start_date - timedelta(days=days_since_monday)
        # 计算当周周五
        friday = monday + timedelta(days=4)  # Monday + 4 days = Friday
        
        # 周五18:00
        from datetime import datetime as dt
        deadline = timezone.make_aware(
            dt.combine(friday, dt.min.time().replace(hour=18, minute=0))
        )
        
        return deadline
    
    def check_overdue_status(self):
        """
        检查周计划是否逾期提交
        
        规则：
        - 只有周计划（plan_period='weekly'）才检查逾期
        - 如果计划状态是 draft 或 published，且已过截止时间，则标记为逾期
        - 如果计划状态是 accepted 或 in_progress，且已过截止时间，则标记为逾期
        """
        if self.plan_period != 'weekly' or not self.submission_deadline:
            return
        
        now = timezone.now()
        
        # 判断是否逾期：状态为 draft 或 published，且已过截止时间
        # 或者状态为 accepted/in_progress，但创建时间在截止时间之后（逾期提交）
        is_overdue = False
        
        if self.status in ['draft', 'published']:
            # 草稿或已发布状态，如果已过截止时间，则逾期
            if now > self.submission_deadline:
                is_overdue = True
        elif self.status in ['accepted', 'in_progress']:
            # 已接收或执行中状态，如果创建时间在截止时间之后，则逾期提交
            if self.created_time and self.created_time > self.submission_deadline:
                is_overdue = True
        
        if is_overdue:
            # 计算逾期天数
            if self.status in ['draft', 'published']:
                # 从截止时间开始计算
                delta = now - self.submission_deadline
            else:
                # 从创建时间开始计算（创建时间在截止时间之后）
                delta = self.created_time - self.submission_deadline
            
            overdue_days = delta.days
            
            # 计算风险等级
            if overdue_days <= 1:
                risk_level = 'low'
            elif overdue_days <= 3:
                risk_level = 'medium'
            elif overdue_days <= 7:
                risk_level = 'high'
            else:
                risk_level = 'critical'
            
            self.is_overdue = True
            self.overdue_days = overdue_days
            self.risk_level = risk_level
        else:
            self.is_overdue = False
            self.overdue_days = 0
            self.risk_level = 'low'
    
    @property
    def plan_type(self):
        """
        向后兼容属性：返回 level 的值
        plan_type 字段已迁移到 level 字段，此属性用于保持向后兼容
        """
        return self.level
    
    def get_plan_type_display(self):
        """
        向后兼容方法：返回 level 的显示值
        plan_type 字段已迁移到 level 字段，此方法用于保持向后兼容
        """
        return self.get_level_display()
    
    @property
    def priority(self):
        """
        向后兼容属性：返回默认优先级
        priority 字段已在迁移 0025 中删除，此属性用于保持向后兼容
        返回默认值 'medium'（中）
        """
        return 'medium'
    
    def get_priority_display(self):
        """
        向后兼容方法：返回优先级的显示值
        priority 字段已在迁移 0025 中删除，此方法用于保持向后兼容
        返回默认值 '中'
        """
        PRIORITY_CHOICES = [
            ('high', '高'),
            ('medium', '中'),
            ('low', '低'),
        ]
        choices_dict = dict(PRIORITY_CHOICES)
        return choices_dict.get(self.priority, '中')


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
    
    def get_old_status_display(self):
        """获取原状态的中文显示（P2-1：统一状态机）"""
        STATUS_CHOICES = [
            ('draft', '草稿'),
            ('published', '已发布'),
            ('accepted', '已接收'),
            ('in_progress', '执行中'),
            ('completed', '已完成'),
            ('cancelled', '已取消'),
        ]
        status_dict = dict(STATUS_CHOICES)
        return status_dict.get(self.old_status, self.old_status)
    
    def get_new_status_display(self):
        """获取新状态的中文显示（P2-1：统一状态机）"""
        STATUS_CHOICES = [
            ('draft', '草稿'),
            ('published', '已发布'),
            ('accepted', '已接收'),
            ('in_progress', '执行中'),
            ('completed', '已完成'),
            ('cancelled', '已取消'),
        ]
        status_dict = dict(STATUS_CHOICES)
        return status_dict.get(self.new_status, self.new_status)


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


class PlanAdjustment(models.Model):
    """计划调整申请（延期/调整）"""
    STATUS_CHOICES = [
        ('pending', '待审批'),
        ('approved', '已批准'),
        ('rejected', '已拒绝'),
    ]
    
    plan = models.ForeignKey(
        Plan,
        on_delete=models.CASCADE,
        related_name='adjustments',
        verbose_name='计划'
    )
    adjustment_reason = models.TextField(verbose_name='调整原因')
    adjustment_content = models.TextField(verbose_name='调整内容')
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='pending', verbose_name='审批状态')
    
    # 调整后的值（如果调整）
    original_end_time = models.DateTimeField(
        default=timezone.now,
        verbose_name='原截止时间',
        help_text='记录调整前的截止时间'
    )
    new_end_time = models.DateTimeField(null=True, blank=True, verbose_name='新截止时间')
    
    # 审批信息
    approved_by = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='approved_plan_adjustments',
        verbose_name='审批人'
    )
    approved_time = models.DateTimeField(null=True, blank=True, verbose_name='审批时间')
    approval_notes = models.TextField(blank=True, verbose_name='审批意见')
    
    # 系统字段
    created_by = models.ForeignKey(
        User,
        on_delete=models.PROTECT,
        related_name='created_plan_adjustments',
        verbose_name='申请人'
    )
    created_time = models.DateTimeField(default=timezone.now, verbose_name='申请时间')
    updated_time = models.DateTimeField(auto_now=True, verbose_name='更新时间')
    
    class Meta:
        db_table = 'plan_plan_adjustment'
        verbose_name = '计划调整申请'
        verbose_name_plural = verbose_name
        ordering = ['-created_time']
        indexes = [
            models.Index(fields=['plan', '-created_time']),
            models.Index(fields=['status']),
        ]
    
    def __str__(self):
        return f"{self.plan.plan_number} - 调整申请 - {self.get_status_display()}"


class PlanInactivityLog(models.Model):
    """计划不作为记录（系统自动生成，不可修改、不可删除）"""
    
    REASON_CHOICES = [
        ('overdue_and_silent', '逾期且无操作'),
        ('overdue_no_progress', '逾期且无进度更新'),
        ('overdue_no_feedback', '逾期且无反馈'),
    ]
    
    plan = models.ForeignKey(
        Plan,
        on_delete=models.CASCADE,
        related_name='inactivity_logs',
        verbose_name='计划'
    )
    
    # 检测时间
    detected_at = models.DateTimeField(default=timezone.now, verbose_name='检测时间')
    
    # 检测区间
    period_start = models.DateTimeField(verbose_name='检测区间开始')
    period_end = models.DateTimeField(verbose_name='检测区间结束')
    
    # 触发原因
    reason = models.CharField(max_length=50, choices=REASON_CHOICES, verbose_name='触发原因')
    reason_detail = models.TextField(blank=True, verbose_name='原因详情')
    
    # 快照（记录当时状态，JSON格式）
    snapshot = models.JSONField(
        default=dict,
        blank=True,
        verbose_name='状态快照',
        help_text='记录检测时的计划状态、责任人等信息'
    )
    
    # 确认状态（是否为系统自动确认的不作为记录）
    is_confirmed = models.BooleanField(
        default=True,
        editable=False,
        verbose_name='系统确认',
        help_text='是否为系统自动确认的不作为记录。当 is_confirmed=True 时，系统已自动确认该期间内责任人无任何行为或反馈。'
    )
    
    class Meta:
        db_table = 'plan_plan_inactivity_log'
        verbose_name = '计划不作为记录'
        verbose_name_plural = verbose_name
        ordering = ['-detected_at']
        indexes = [
            models.Index(fields=['plan', '-detected_at']),
            models.Index(fields=['reason', '-detected_at']),
        ]
        # 防止重复生成：同一计划在同一检测区间内只生成一条记录
        constraints = [
            models.UniqueConstraint(
                fields=['plan', 'period_start', 'period_end', 'reason'],
                name='unique_plan_inactivity_period'
            ),
        ]
    
    def __str__(self):
        return f"{self.plan.plan_number} - {self.get_reason_display()} - {self.detected_at.strftime('%Y-%m-%d')}"
    
    def save(self, *args, **kwargs):
        """重写 save，确保只能由系统创建，不允许修改"""
        if self.pk:
            # 如果记录已存在，不允许修改
            raise ValueError("PlanInactivityLog 记录不允许修改，只能由系统自动生成")
        super().save(*args, **kwargs)
    
    def delete(self, *args, **kwargs):
        """重写 delete，不允许删除"""
        raise ValueError("PlanInactivityLog 记录不允许删除，作为不作为证据永久保存")


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


# PlanApproval 模型已被迁移 0003 删除，不再使用
# 审批功能已由 PlanDecision 模型替代


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


class ApprovalNotification(models.Model):
    """审批通知模型"""
    
    EVENT_CHOICES = [
        ('submit', '提交审批'),
        ('approve', '审批通过'),
        ('reject', '审批驳回'),
        ('cancel', '取消审批'),
        ('draft_timeout', '草稿超时'),
        ('approval_timeout', '审批超时'),
        ('company_goal_published', '公司目标发布'),
        ('personal_goal_published', '个人目标发布'),
        ('goal_accepted', '目标被接收'),
        ('company_plan_published', '公司计划发布'),
        ('personal_plan_published', '个人计划发布'),
        ('plan_accepted', '计划被接收'),
        ('weekly_plan_reminder', '周计划提醒'),
        ('weekly_plan_overdue', '周计划逾期'),
        ('goal_creation', '目标创建待办'),
        ('goal_progress_update', '目标进度更新待办'),
        ('plan_creation', '计划创建待办'),
        ('daily_plan_reminder', '日计划提醒'),
        ('plan_progress_update', '计划进度更新待办'),
        ('progress_update_notify_supervisor', '进度更新通知上级'),
        ('todo_overdue', '待办事项逾期'),
        ('work_summary_generated', '工作总结生成'),
        ('work_summary_supervisor', '工作总结上级通知'),
        ('daily_notification', '每日通知'),
    ]
    
    OBJECT_TYPE_CHOICES = [
        ('plan', '计划'),
        ('goal', '目标'),
        ('todo', '待办'),
        ('summary', '总结'),
        ('notification', '通知'),
    ]
    
    user = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name='approval_notifications',
        verbose_name='接收人'
    )
    title = models.CharField(max_length=200, verbose_name='通知标题')
    content = models.TextField(verbose_name='通知内容')
    object_type = models.CharField(
        max_length=20,
        choices=OBJECT_TYPE_CHOICES,
        verbose_name='对象类型'
    )
    object_id = models.CharField(max_length=50, verbose_name='对象ID')
    event = models.CharField(
        max_length=50,  # 增加长度以支持 personal_goal_published 等长事件名
        choices=EVENT_CHOICES,
        verbose_name='事件类型'
    )
    is_read = models.BooleanField(default=False, verbose_name='是否已读')
    created_at = models.DateTimeField(auto_now_add=True, verbose_name='创建时间')
    
    class Meta:
        db_table = 'plan_approval_notification'
        verbose_name = '审批通知'
        verbose_name_plural = '审批通知'
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['user', 'is_read'], name='plan_approv_user_id_fdf6fe_idx'),
            models.Index(fields=['-created_at'], name='plan_approv_created_ef6d5d_idx'),
            models.Index(fields=['object_type', 'object_id'], name='plan_approv_object__3b2b49_idx'),
        ]
    
    def __str__(self):
        return f"{self.title} - {self.user.username}"


class TodoTask(models.Model):
    """待办事项模型"""
    
    TASK_TYPE_CHOICES = [
        ('goal_creation', '目标创建'),
        ('goal_decomposition', '目标分解'),
        ('goal_progress_update', '目标进度更新'),
        ('plan_creation', '计划创建'),
        ('plan_decomposition_weekly', '周计划分解'),
        ('plan_decomposition_daily', '日计划分解'),
        ('plan_progress_update', '计划进度更新'),
    ]
    
    STATUS_CHOICES = [
        ('pending', '待处理'),
        ('completed', '已完成'),
        ('overdue', '已逾期'),
        ('cancelled', '已取消'),
    ]
    
    OBJECT_TYPE_CHOICES = [
        ('goal', '目标'),
        ('plan', '计划'),
        ('todo', '待办'),
    ]
    
    task_type = models.CharField(max_length=50, choices=TASK_TYPE_CHOICES, verbose_name='待办类型')
    user = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name='todo_tasks',
        verbose_name='负责人'
    )
    title = models.CharField(max_length=200, verbose_name='待办标题')
    description = models.TextField(blank=True, verbose_name='待办描述')
    related_object_type = models.CharField(
        max_length=20,
        choices=OBJECT_TYPE_CHOICES,
        null=True,
        blank=True,
        verbose_name='关联对象类型'
    )
    related_object_id = models.CharField(max_length=50, null=True, blank=True, verbose_name='关联对象ID')
    deadline = models.DateTimeField(verbose_name='截止时间')
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='pending', verbose_name='状态')
    is_overdue = models.BooleanField(default=False, verbose_name='是否逾期')
    overdue_days = models.IntegerField(default=0, verbose_name='逾期天数')
    completed_at = models.DateTimeField(null=True, blank=True, verbose_name='完成时间')
    auto_generated = models.BooleanField(default=True, verbose_name='是否系统自动生成')
    created_at = models.DateTimeField(auto_now_add=True, verbose_name='创建时间')
    updated_at = models.DateTimeField(auto_now=True, verbose_name='更新时间')
    
    class Meta:
        db_table = 'plan_todo_task'
        verbose_name = '待办事项'
        verbose_name_plural = '待办事项'
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['user', 'status'], name='plan_todo_user_status_idx'),
            models.Index(fields=['deadline'], name='plan_todo_deadline_idx'),
            models.Index(fields=['related_object_type', 'related_object_id'], name='plan_todo_object_idx'),
            models.Index(fields=['task_type', 'status'], name='plan_todo_type_status_idx'),
        ]
    
    def __str__(self):
        return f"{self.title} - {self.user.username}"
    
    def check_overdue(self):
        """检查并更新逾期状态"""
        if self.status in ['completed', 'cancelled']:
            return False
        
        now = timezone.now()
        if now > self.deadline:
            self.is_overdue = True
            self.overdue_days = (now.date() - self.deadline.date()).days
            if self.status == 'pending':
                self.status = 'overdue'
            return True
        return False


class WorkSummary(models.Model):
    """工作总结模型"""
    
    SUMMARY_TYPE_CHOICES = [
        ('weekly', '周报'),
        ('monthly', '月报'),
    ]
    
    summary_type = models.CharField(max_length=20, choices=SUMMARY_TYPE_CHOICES, verbose_name='总结类型')
    user = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name='work_summaries',
        verbose_name='员工'
    )
    period_start = models.DateField(verbose_name='周期开始日期')
    period_end = models.DateField(verbose_name='周期结束日期')
    goal_progress_summary = models.JSONField(default=dict, verbose_name='目标进度汇总')
    plan_completion_summary = models.JSONField(default=dict, verbose_name='计划完成汇总')
    achievements = models.JSONField(default=list, verbose_name='成就亮点')
    risk_items = models.JSONField(default=list, verbose_name='风险项')
    sent_to_supervisor = models.BooleanField(default=False, verbose_name='是否已发送给上级')
    created_at = models.DateTimeField(auto_now_add=True, verbose_name='创建时间')
    
    class Meta:
        db_table = 'plan_work_summary'
        verbose_name = '工作总结'
        verbose_name_plural = '工作总结'
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['user', 'summary_type'], name='plan_work_user_type_idx'),
            models.Index(fields=['period_start', 'period_end'], name='plan_work_period_idx'),
        ]
    
    def __str__(self):
        return f"{self.get_summary_type_display()} - {self.user.username} ({self.period_start} ~ {self.period_end})"

