from django.db import models
from django.utils import timezone
from django.core.validators import MinValueValidator, MaxValueValidator
import logging
from backend.apps.system_management.models import User
from backend.apps.customer_management.models import Client

logger = logging.getLogger(__name__)

# ==================== 商机管理模块模型 =====================
class BusinessOpportunity(models.Model):
    """商机管理"""
    STATUS_CHOICES = [
        ('potential', '潜在客户'),           # 10%
        ('initial_contact', '初步接触'),     # 30%
        ('requirement_confirmed', '需求确认'), # 50%
        ('quotation', '方案报价'),          # 70%
        ('negotiation', '商务谈判'),         # 90%
        ('won', '赢单'),
        ('lost', '输单'),
        ('cancelled', '已取消'),
    ]
    
    URGENCY_CHOICES = [
        ('normal', '普通'),
        ('urgent', '紧急'),
        ('very_urgent', '特急'),
    ]
    
    OPPORTUNITY_TYPE_CHOICES = [
        ('project_cooperation', '项目合作'),
        ('centralized_procurement', '集中采购'),
    ]
    
    APPROVAL_STATUS_CHOICES = [
        ('pending', '待审批'),
        ('approved', '已审批'),
        ('rejected', '已驳回'),
    ]
    
    # 基本信息
    opportunity_number = models.CharField(max_length=50, unique=True, blank=True, null=True, verbose_name='商机编号', help_text='自动生成：SJ-YYYYMMDD-0000')
    name = models.CharField(max_length=200, verbose_name='商机名称')
    client = models.ForeignKey(Client, on_delete=models.PROTECT, related_name='opportunities', verbose_name='关联客户')
    business_manager = models.ForeignKey(User, on_delete=models.PROTECT, related_name='managed_opportunities', verbose_name='负责商务')
    opportunity_type = models.CharField(max_length=30, choices=OPPORTUNITY_TYPE_CHOICES, blank=True, verbose_name='商机类型')
    service_type = models.ForeignKey('base_data.ServiceType', on_delete=models.SET_NULL, null=True, blank=True, related_name='opportunities', verbose_name='服务类型')
    
    # 项目信息
    project = models.ForeignKey(
        'production_management.Project',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='opportunities',
        verbose_name='关联项目',
        help_text='B3 结构化锚点：商机关联的生产管理项目，便于合同/委托书选择商机时回填'
    )
    project_name = models.CharField(max_length=200, blank=True, verbose_name='项目名称')
    project_address = models.CharField(max_length=500, blank=True, verbose_name='项目地址')
    project_type = models.CharField(max_length=50, blank=True, verbose_name='项目业态', help_text='住宅/综合体/商业/写字楼等')
    building_area = models.DecimalField(max_digits=15, decimal_places=2, null=True, blank=True, verbose_name='建筑面积（平方米）')
    drawing_stage = models.ForeignKey('base_data.DesignStage', on_delete=models.SET_NULL, null=True, blank=True, related_name='opportunities', verbose_name='图纸阶段', db_column='drawing_stage')
    
    # 金额和概率
    estimated_amount = models.DecimalField(max_digits=15, decimal_places=2, default=0, verbose_name='预计金额（万元）')
    success_probability = models.IntegerField(default=10, verbose_name='成功概率（%）', help_text='10/30/50/70/90')
    weighted_amount = models.DecimalField(max_digits=15, decimal_places=2, default=0, verbose_name='加权金额', help_text='预计金额 × 成功概率')
    
    # 状态和时间
    status = models.CharField(max_length=30, choices=STATUS_CHOICES, default='potential', verbose_name='商机状态')
    urgency = models.CharField(max_length=20, choices=URGENCY_CHOICES, default='normal', verbose_name='紧急程度')
    expected_sign_date = models.DateField(null=True, blank=True, verbose_name='预计签约时间')
    actual_sign_date = models.DateField(null=True, blank=True, verbose_name='实际签约日期')
    
    # 审批信息
    approval_status = models.CharField(max_length=20, choices=APPROVAL_STATUS_CHOICES, default='pending', verbose_name='审批状态')
    approver = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True, related_name='approved_opportunities', verbose_name='审批人')
    approved_time = models.DateTimeField(null=True, blank=True, verbose_name='审批时间')
    approval_comment = models.TextField(blank=True, verbose_name='审批意见')
    
    # 赢单/输单信息
    actual_amount = models.DecimalField(max_digits=15, decimal_places=2, null=True, blank=True, verbose_name='实际签约金额（万元）')
    contract_number = models.CharField(max_length=100, blank=True, verbose_name='合同编号')
    win_reason = models.TextField(blank=True, verbose_name='赢单原因')
    loss_reason = models.TextField(blank=True, verbose_name='输单原因')
    
    # 健康度
    health_score = models.IntegerField(default=0, verbose_name='健康度评分', help_text='0-100分')
    
    # 其他信息
    description = models.TextField(blank=True, verbose_name='商机描述')
    notes = models.TextField(blank=True, verbose_name='备注')
    is_active = models.BooleanField(default=True, verbose_name='是否启用')
    
    # 审计字段
    created_by = models.ForeignKey(User, on_delete=models.PROTECT, related_name='created_opportunities', verbose_name='创建人')
    created_time = models.DateTimeField(default=timezone.now, verbose_name='创建时间')
    updated_time = models.DateTimeField(auto_now=True, verbose_name='更新时间')
    
    class Meta:
        db_table = 'business_opportunity'
        verbose_name = '商机'
        verbose_name_plural = verbose_name
        ordering = ['-created_time']
        indexes = [
            models.Index(fields=['opportunity_number']),
            models.Index(fields=['status']),
            models.Index(fields=['business_manager', 'status']),
            models.Index(fields=['expected_sign_date']),
        ]
    
    def __str__(self):
        return f"{self.opportunity_number or '未编号'} - {self.name}"
    
    def save(self, *args, **kwargs):
        # 自动生成商机编号：SJ-YYYYMMDD-0000（连续编号）
        if not self.opportunity_number:
            from django.db.models import Max
            from datetime import datetime
            current_date = datetime.now().strftime('%Y%m%d')
            date_prefix = f'SJ-{current_date}-'
            
            # 查找当天最大编号
            max_opp = BusinessOpportunity.objects.filter(
                opportunity_number__startswith=date_prefix
            ).aggregate(max_num=Max('opportunity_number'))['max_num']
            
            if max_opp:
                try:
                    # 提取最后4位数字作为序号
                    seq = int(max_opp.split('-')[-1]) + 1
                except (ValueError, IndexError):
                    seq = 1
            else:
                seq = 1
            
            self.opportunity_number = f'{date_prefix}{seq:04d}'
        
        # 自动计算加权金额
        if self.estimated_amount and self.success_probability:
            from decimal import Decimal
            self.weighted_amount = (self.estimated_amount * Decimal(self.success_probability)) / 100
        
        # 自动计算健康度（简化版，后续可以完善）
        if not self.health_score or kwargs.get('update_health', False):
            self.health_score = self._calculate_health_score()
        
        super().save(*args, **kwargs)
    
    def _calculate_health_score(self):
        """计算健康度评分"""
        score = 0
        
        # 1. 跟进及时性（25%）
        followup_score = 0
        # 只有在实例有主键时才访问关联关系
        last_followup = None
        if self.pk and hasattr(self, 'followups'):
            try:
                last_followup = self.followups.order_by('-follow_date').first()
            except Exception:
                pass
        if last_followup and last_followup.next_follow_date:
            days_overdue = (timezone.now().date() - last_followup.next_follow_date).days
            if days_overdue <= 0:
                # 及时跟进
                followup_score = 25
            elif days_overdue <= 3:
                # 轻微延迟
                followup_score = 20
            elif days_overdue <= 7:
                # 中度延迟
                followup_score = 12
            else:
                # 严重延迟
                followup_score = 5
        elif last_followup:
            # 有跟进记录但没有下次跟进计划
            days_since_last = (timezone.now().date() - last_followup.follow_date).days
            if days_since_last <= 7:
                followup_score = 20
            elif days_since_last <= 14:
                followup_score = 12
            else:
                followup_score = 5
        else:
            # 没有跟进记录
            created_date = self.created_time.date() if self.created_time else timezone.now().date()
            days_since_created = (timezone.now().date() - created_date).days
            if days_since_created <= 3:
                followup_score = 15
            elif days_since_created <= 7:
                followup_score = 8
            else:
                followup_score = 0
        score += followup_score
        
        # 2. 信息完整性（20%）
        info_score = 0
        required_fields = [
            ('project_name', 5),
            ('project_address', 5),
            ('estimated_amount', 5),
            ('expected_sign_date', 5),
        ]
        for field_name, field_score in required_fields:
            field_value = getattr(self, field_name, None)
            if field_value:
                info_score += field_score
        score += info_score
        
        # 3. 客户互动频次（20%）
        interaction_score = 0
        followup_count = 0
        if self.pk and hasattr(self, 'followups'):
            try:
                followup_count = self.followups.count()
            except Exception:
                pass
        if followup_count >= 5:
            interaction_score = 20
        elif followup_count >= 3:
            interaction_score = 15
        elif followup_count >= 2:
            interaction_score = 10
        elif followup_count >= 1:
            interaction_score = 5
        else:
            interaction_score = 0
        score += interaction_score
        
        # 4. 阶段推进速度（35%）
        progress_score = 0
        days_since_created = (timezone.now().date() - self.created_time.date()).days
        
        # 根据状态和停留时间计算
        if self.status == 'won':
            progress_score = 35
        elif self.status == 'negotiation':
            if days_since_created <= 30:
                progress_score = 35
            elif days_since_created <= 45:
                progress_score = 28
            elif days_since_created <= 60:
                progress_score = 20
            else:
                progress_score = 10
        elif self.status == 'quotation':
            if days_since_created <= 20:
                progress_score = 30
            elif days_since_created <= 30:
                progress_score = 22
            elif days_since_created <= 45:
                progress_score = 15
            else:
                progress_score = 8
        elif self.status == 'requirement_confirmed':
            if days_since_created <= 15:
                progress_score = 25
            elif days_since_created <= 25:
                progress_score = 18
            elif days_since_created <= 35:
                progress_score = 12
            else:
                progress_score = 6
        elif self.status == 'initial_contact':
            if days_since_created <= 10:
                progress_score = 20
            elif days_since_created <= 20:
                progress_score = 15
            elif days_since_created <= 30:
                progress_score = 10
            else:
                progress_score = 5
        elif self.status == 'potential':
            if days_since_created <= 7:
                progress_score = 15
            elif days_since_created <= 14:
                progress_score = 10
            else:
                progress_score = 5
        else:
            progress_score = 5
        score += progress_score
        
        return min(score, 100)
    
    def get_health_analysis(self):
        """获取健康度详细分析"""
        analysis = {
            'total_score': self.health_score,
            'health_level': 'high' if self.health_score >= 80 else ('medium' if self.health_score >= 60 else 'low'),
            'dimensions': {},
            'suggestions': []
        }
        
        # 跟进及时性分析
        last_followup = None
        if self.pk and hasattr(self, 'followups'):
            try:
                last_followup = self.followups.order_by('-follow_date').first()
            except Exception:
                pass
        followup_timeliness = 0
        if last_followup and last_followup.next_follow_date:
            days_overdue = (timezone.now().date() - last_followup.next_follow_date).days
            if days_overdue <= 0:
                followup_timeliness = 100
            elif days_overdue <= 3:
                followup_timeliness = 80
            elif days_overdue <= 7:
                followup_timeliness = 48
            else:
                followup_timeliness = 20
                analysis['suggestions'].append('跟进已超期，建议立即安排跟进')
        elif last_followup:
            days_since_last = (timezone.now().date() - last_followup.follow_date).days
            if days_since_last <= 7:
                followup_timeliness = 80
            elif days_since_last <= 14:
                followup_timeliness = 48
            else:
                followup_timeliness = 20
                analysis['suggestions'].append('长时间未跟进，建议尽快安排跟进')
        else:
            followup_timeliness = 0
            analysis['suggestions'].append('尚未有跟进记录，建议尽快建立首次联系')
        
        analysis['dimensions']['followup_timeliness'] = {
            'score': followup_timeliness,
            'weight': 0.25,
            'label': '跟进及时性'
        }
        
        # 信息完整性分析
        required_fields = ['project_name', 'project_address', 'estimated_amount', 'expected_sign_date']
        filled_fields = sum(1 for field in required_fields if getattr(self, field, None))
        info_completeness = (filled_fields / len(required_fields)) * 100
        if info_completeness < 100:
            missing = [f for f in required_fields if not getattr(self, f, None)]
            analysis['suggestions'].append(f'信息不完整，建议完善：{", ".join(missing)}')
        
        analysis['dimensions']['information_completeness'] = {
            'score': info_completeness,
            'weight': 0.20,
            'label': '信息完整性'
        }
        
        # 客户互动频次分析
        followup_count = 0
        if self.pk and hasattr(self, 'followups'):
            try:
                followup_count = self.followups.count()
            except Exception:
                pass
        if followup_count >= 5:
            interaction_score = 100
        elif followup_count >= 3:
            interaction_score = 75
        elif followup_count >= 2:
            interaction_score = 50
        elif followup_count >= 1:
            interaction_score = 25
        else:
            interaction_score = 0
            analysis['suggestions'].append('客户互动较少，建议增加跟进频次')
        
        analysis['dimensions']['client_interaction'] = {
            'score': interaction_score,
            'weight': 0.20,
            'label': '客户互动频次'
        }
        
        # 阶段推进速度分析
        days_since_created = (timezone.now().date() - self.created_time.date()).days
        progress_score = 0
        if self.status == 'won':
            progress_score = 100
        elif self.status == 'negotiation':
            progress_score = min(100, max(30, 100 - (days_since_created - 30) * 2))
        elif self.status == 'quotation':
            progress_score = min(100, max(25, 100 - (days_since_created - 20) * 3))
        elif self.status == 'requirement_confirmed':
            progress_score = min(100, max(20, 100 - (days_since_created - 15) * 4))
        elif self.status == 'initial_contact':
            progress_score = min(100, max(15, 100 - (days_since_created - 10) * 5))
        else:
            progress_score = min(100, max(10, 100 - days_since_created * 6))
        
        if progress_score < 50:
            analysis['suggestions'].append('阶段推进较慢，建议加快进度或重新评估商机')
        
        analysis['dimensions']['stage_progress'] = {
            'score': progress_score,
            'weight': 0.35,
            'label': '阶段推进速度'
        }
        
        return analysis
    
    @classmethod
    def get_valid_transitions(cls, current_status):
        """获取当前状态可以流转到的状态列表"""
        transitions = {
            'potential': ['initial_contact', 'cancelled'],
            'initial_contact': ['requirement_confirmed', 'potential', 'cancelled'],
            'requirement_confirmed': ['quotation', 'initial_contact', 'cancelled'],
            'quotation': ['negotiation', 'requirement_confirmed', 'cancelled'],
            'negotiation': ['won', 'lost', 'quotation', 'cancelled'],
            'won': [],
            'lost': [],
            'cancelled': [],
        }
        return transitions.get(current_status, [])
    
    def can_transition_to(self, target_status):
        """检查是否可以流转到目标状态"""
        valid_transitions = self.get_valid_transitions(self.status)
        return target_status in valid_transitions
    
    def transition_to(self, target_status, actor=None, comment=''):
        """执行状态流转"""
        if not self.can_transition_to(target_status):
            raise ValueError(f"无法从 {self.get_status_display()} 流转到 {dict(self.STATUS_CHOICES).get(target_status, target_status)}")
        
        old_status = self.status
        self.status = target_status
        self._status_change_actor = actor
        self._status_change_comment = comment
        self.save()
        
        # 记录状态流转日志
        if self.pk:
            OpportunityStatusLog.objects.create(
                opportunity=self,
                from_status=old_status,
                to_status=target_status,
                actor=actor,
                comment=comment,
            )
        
        return True



class OpportunityFollowUp(models.Model):
    """商机跟进记录"""
    FOLLOW_TYPE_CHOICES = [
        ('phone', '电话沟通'),
        ('visit', '上门拜访'),
        ('online_meeting', '线上会议'),
        ('email', '邮件沟通'),
        ('other', '其他'),
    ]
    
    opportunity = models.ForeignKey(BusinessOpportunity, on_delete=models.CASCADE, related_name='followups', verbose_name='商机')
    follow_date = models.DateField(verbose_name='跟进日期')
    follow_type = models.CharField(max_length=20, choices=FOLLOW_TYPE_CHOICES, default='phone', verbose_name='跟进方式')
    participants = models.CharField(max_length=500, blank=True, verbose_name='参与人员')
    content = models.TextField(verbose_name='跟进内容')
    customer_feedback = models.TextField(blank=True, verbose_name='客户反馈')
    next_plan = models.TextField(blank=True, verbose_name='下一步计划')
    next_follow_date = models.DateField(null=True, blank=True, verbose_name='预计下次跟进')
    
    # 审计字段
    created_by = models.ForeignKey(User, on_delete=models.PROTECT, related_name='created_followups', verbose_name='创建人')
    created_time = models.DateTimeField(default=timezone.now, verbose_name='创建时间')
    
    class Meta:
        db_table = 'business_opportunity_followup'
        verbose_name = '商机跟进记录'
        verbose_name_plural = verbose_name
        ordering = ['-follow_date', '-created_time']
    
    def __str__(self):
        return f"{self.opportunity.opportunity_number} - {self.follow_date}"



class QuotationRule(models.Model):
    """报价规则配置"""
    RULE_TYPE_CHOICES = [
        ('rate', '费率'),
        ('unit_price', '单价'),
        ('fixed', '固定金额'),
    ]
    
    name = models.CharField(max_length=100, verbose_name='规则名称')
    rule_type = models.CharField(max_length=20, choices=RULE_TYPE_CHOICES, verbose_name='规则类型')
    project_type = models.CharField(max_length=50, blank=True, verbose_name='项目业态')
    service_type = models.CharField(max_length=50, blank=True, verbose_name='服务类型')
    structure_type = models.CharField(max_length=50, blank=True, verbose_name='结构形式')
    
    # 规则参数（JSON格式存储复杂规则）
    rule_params = models.JSONField(default=dict, verbose_name='规则参数', help_text='存储费率、单价等参数')
    
    # 适用范围
    min_area = models.DecimalField(max_digits=15, decimal_places=2, null=True, blank=True, verbose_name='最小面积')
    max_area = models.DecimalField(max_digits=15, decimal_places=2, null=True, blank=True, verbose_name='最大面积')
    
    # 调整系数
    adjustment_factor = models.DecimalField(max_digits=5, decimal_places=2, default=1.0, verbose_name='调整系数')
    
    # 状态
    is_active = models.BooleanField(default=True, verbose_name='是否启用')
    description = models.TextField(blank=True, verbose_name='规则说明')
    
    # 审计字段
    created_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, related_name='created_quotation_rules', verbose_name='创建人')
    created_time = models.DateTimeField(default=timezone.now, verbose_name='创建时间')
    updated_time = models.DateTimeField(auto_now=True, verbose_name='更新时间')
    
    class Meta:
        db_table = 'business_quotation_rule'
        verbose_name = '报价规则'
        verbose_name_plural = verbose_name
        ordering = ['-created_time']
    
    def __str__(self):
        return self.name



class OpportunityQuotation(models.Model):
    """商机报价"""
    VERSION_TYPE_CHOICES = [
        ('draft', '初稿报价'),
        ('customer', '客户报价'),
        ('final', '最终报价'),
    ]
    
    # 报价模式选择（7种模式）
    QUOTATION_MODE_CHOICES = [
        ('rate', '纯费率模式'),
        ('base_fee_rate', '基本费+费率模式'),
        ('fixed', '包干价模式'),
        ('segmented', '分段累进模式'),
        ('min_savings_rate', '最低节省+费率模式'),
        ('performance_linked', '绩效挂钩模式'),
        ('hybrid', '混合计价模式'),
    ]
    
    opportunity = models.ForeignKey(BusinessOpportunity, on_delete=models.CASCADE, related_name='quotations', verbose_name='商机')
    version_type = models.CharField(max_length=20, choices=VERSION_TYPE_CHOICES, default='draft', verbose_name='版本类型')
    version_number = models.IntegerField(default=1, verbose_name='版本号')
    
    # 报价模式（新增）
    quotation_mode = models.CharField(
        max_length=30, 
        choices=QUOTATION_MODE_CHOICES, 
        default='rate', 
        verbose_name='报价模式',
        help_text='选择报价计算模式'
    )
    mode_params = models.JSONField(
        default=dict, 
        blank=True, 
        verbose_name='模式参数',
        help_text='JSON格式存储报价模式相关参数（费率、基本费、分段配置等）'
    )
    cap_fee = models.DecimalField(
        max_digits=15, 
        decimal_places=2, 
        null=True, 
        blank=True, 
        verbose_name='封顶费（万元）',
        help_text='服务费上限，超过此金额按封顶费计算（可选）'
    )
    saved_amount = models.DecimalField(
        max_digits=15, 
        decimal_places=2, 
        null=True, 
        blank=True, 
        default=0,
        verbose_name='节省金额（万元）',
        help_text='用于计算服务费的节省金额'
    )
    
    # 报价参数（保留原有字段以保持兼容性）
    building_area = models.DecimalField(max_digits=15, decimal_places=2, null=True, blank=True, verbose_name='建筑面积（平方米）')
    project_type = models.CharField(max_length=50, blank=True, verbose_name='项目业态')
    service_type = models.CharField(max_length=50, blank=True, verbose_name='服务类型')
    structure_type = models.CharField(max_length=50, blank=True, verbose_name='结构形式')
    
    # 报价结果（保留原有字段，同时支持新模式）
    base_quotation = models.DecimalField(max_digits=15, decimal_places=2, default=0, verbose_name='基准报价（万元）', help_text='旧版报价字段，保留兼容性')
    adjustment_factor = models.DecimalField(max_digits=5, decimal_places=2, default=1.0, verbose_name='调整系数', help_text='旧版报价字段，保留兼容性')
    service_fee = models.DecimalField(
        max_digits=15, 
        decimal_places=2, 
        default=0, 
        verbose_name='服务费（万元）',
        help_text='根据报价模式计算的服务费'
    )
    final_quotation = models.DecimalField(
        max_digits=15, 
        decimal_places=2, 
        default=0, 
        verbose_name='最终报价（万元）',
        help_text='最终报价金额（兼容旧版：base_quotation × adjustment_factor；新版：service_fee）'
    )
    calculation_steps = models.JSONField(
        default=list, 
        blank=True, 
        verbose_name='计算步骤',
        help_text='JSON格式存储计算过程，用于展示计算明细'
    )
    quotation_note = models.TextField(blank=True, verbose_name='报价说明')
    
    # 使用的规则（保留兼容性）
    quotation_rule = models.ForeignKey(QuotationRule, on_delete=models.SET_NULL, null=True, blank=True, verbose_name='使用的报价规则', help_text='旧版报价规则，保留兼容性')
    
    # 文件
    quotation_file = models.FileField(upload_to='quotations/%Y/%m/', blank=True, null=True, verbose_name='报价文件')
    
    # 审计字段
    created_by = models.ForeignKey(User, on_delete=models.PROTECT, related_name='created_quotations', verbose_name='创建人')
    created_time = models.DateTimeField(default=timezone.now, verbose_name='创建时间')
    updated_time = models.DateTimeField(auto_now=True, verbose_name='更新时间')
    
    class Meta:
        db_table = 'business_opportunity_quotation'
        verbose_name = '商机报价'
        verbose_name_plural = verbose_name
        ordering = ['-version_number', '-created_time']
        unique_together = [['opportunity', 'version_number']]
    
    def __str__(self):
        return f"{self.opportunity.opportunity_number} - {self.get_version_type_display()} v{self.version_number}"
    
    def save(self, *args, **kwargs):
        # 如果使用新模式，通过计算引擎计算服务费
        if self.quotation_mode and self.saved_amount:
            try:
                from backend.apps.opportunity_management.services.quotation_calculator import QuotationCalculator
                calculator = QuotationCalculator()
                result = calculator.calculate(
                    mode=self.quotation_mode,
                    saved_amount=float(self.saved_amount),
                    mode_params=self.mode_params or {},
                    cap_fee=float(self.cap_fee) if self.cap_fee else None
                )
                self.service_fee = result['service_fee']
                self.calculation_steps = result.get('calculation_steps', [])
                self.final_quotation = self.service_fee
            except Exception as e:
                # 如果计算失败，记录错误但不阻止保存
                import logging
                logger = logging.getLogger(__name__)
                logger.error(f'报价计算失败: {str(e)}')
                # 保留旧版计算逻辑作为降级方案
                if self.base_quotation and self.adjustment_factor:
                    from decimal import Decimal
                    self.final_quotation = self.base_quotation * Decimal(str(self.adjustment_factor))
        else:
            # 兼容旧版计算逻辑
            if self.base_quotation and self.adjustment_factor:
                from decimal import Decimal
                self.final_quotation = self.base_quotation * Decimal(str(self.adjustment_factor))
        
        super().save(*args, **kwargs)



class OpportunityApproval(models.Model):
    """商机审批记录"""
    APPROVAL_RESULT_CHOICES = [
        ('approved', '通过'),
        ('rejected', '驳回'),
        ('pending', '待审核'),
    ]
    
    opportunity = models.ForeignKey(BusinessOpportunity, on_delete=models.CASCADE, related_name='approvals', verbose_name='商机')
    approver = models.ForeignKey(User, on_delete=models.PROTECT, related_name='opportunity_approvals', verbose_name='审核人')
    approval_level = models.IntegerField(default=1, verbose_name='审核层级', help_text='1=商务部经理, 2=商务总监, 3=总经理')
    result = models.CharField(max_length=20, choices=APPROVAL_RESULT_CHOICES, default='pending', verbose_name='审核结果')
    comment = models.TextField(blank=True, verbose_name='审核意见')
    approval_time = models.DateTimeField(null=True, blank=True, verbose_name='审核时间')
    created_time = models.DateTimeField(default=timezone.now, verbose_name='创建时间')
    
    class Meta:
        db_table = 'business_opportunity_approval'
        verbose_name = '商机审批记录'
        verbose_name_plural = verbose_name
        ordering = ['approval_level', '-created_time']
    
    def __str__(self):
        return f"{self.opportunity.opportunity_number} - {self.approver.username} - {self.get_result_display()}"



class OpportunityStatusLog(models.Model):
    """商机状态流转日志"""
    opportunity = models.ForeignKey(BusinessOpportunity, on_delete=models.CASCADE, related_name='status_logs', verbose_name='商机')
    from_status = models.CharField(max_length=30, choices=BusinessOpportunity.STATUS_CHOICES, blank=True, verbose_name='原状态')
    to_status = models.CharField(max_length=30, choices=BusinessOpportunity.STATUS_CHOICES, verbose_name='目标状态')
    actor = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True, related_name='opportunity_status_actions', verbose_name='操作人')
    comment = models.TextField(blank=True, verbose_name='备注说明')
    created_time = models.DateTimeField(default=timezone.now, verbose_name='操作时间')
    
    class Meta:
        db_table = 'business_opportunity_status_log'
        verbose_name = '商机状态流转日志'
        verbose_name_plural = verbose_name
        ordering = ['-created_time']
    
    def __str__(self):
        from_label = dict(BusinessOpportunity.STATUS_CHOICES).get(self.from_status, '未知')
        to_label = dict(BusinessOpportunity.STATUS_CHOICES).get(self.to_status, '未知')
        return f"{self.opportunity.opportunity_number} - {from_label} → {to_label}"


class BusinessNegotiation(models.Model):
    """商务洽谈记录"""
    NEGOTIATION_TYPE_CHOICES = [
        ('phone', '电话沟通'),
        ('meeting', '会议洽谈'),
        ('visit', '上门拜访'),
        ('email', '邮件沟通'),
        ('online', '线上会议'),
        ('other', '其他'),
    ]
    
    opportunity = models.ForeignKey(
        BusinessOpportunity, 
        on_delete=models.CASCADE, 
        related_name='negotiations', 
        verbose_name='关联商机'
    )
    negotiation_date = models.DateField(verbose_name='洽谈日期')
    negotiation_type = models.CharField(
        max_length=20, 
        choices=NEGOTIATION_TYPE_CHOICES, 
        verbose_name='洽谈类型'
    )
    participants = models.CharField(
        max_length=500, 
        blank=True, 
        verbose_name='参与人员',
        help_text='参与洽谈的人员，多个用逗号分隔'
    )
    content = models.TextField(verbose_name='洽谈内容')
    client_feedback = models.TextField(blank=True, verbose_name='客户反馈')
    next_plan = models.TextField(blank=True, verbose_name='下一步计划')
    discussed_amount = models.DecimalField(
        max_digits=15, 
        decimal_places=2, 
        null=True, 
        blank=True, 
        verbose_name='讨论金额（万元）'
    )
    payment_terms = models.TextField(blank=True, verbose_name='付款条件')
    contract_terms = models.TextField(blank=True, verbose_name='合同条款')
    
    # 审计字段
    created_by = models.ForeignKey(
        User, 
        on_delete=models.PROTECT, 
        related_name='created_negotiations', 
        verbose_name='创建人'
    )
    created_time = models.DateTimeField(default=timezone.now, verbose_name='创建时间')
    updated_time = models.DateTimeField(auto_now=True, verbose_name='更新时间')
    
    class Meta:
        db_table = 'business_negotiation'
        verbose_name = '商务洽谈记录'
        verbose_name_plural = verbose_name
        ordering = ['-negotiation_date', '-created_time']
    
    def __str__(self):
        return f"{self.opportunity.name} - {self.negotiation_date} - {self.get_negotiation_type_display()}"



class OpportunityFiling(models.Model):
    """商机备案记录"""
    FILING_TYPE_CHOICES = [
        ('initial', '初始备案'),
        ('update', '更新备案'),
        ('supplement', '补充备案'),
        ('other', '其他'),
    ]
    
    opportunity = models.ForeignKey(
        BusinessOpportunity, 
        on_delete=models.CASCADE, 
        related_name='filings', 
        verbose_name='关联商机'
    )
    filing_date = models.DateField(verbose_name='备案日期')
    filing_type = models.CharField(
        max_length=20, 
        choices=FILING_TYPE_CHOICES, 
        verbose_name='备案类型'
    )
    filing_number = models.CharField(
        max_length=100, 
        blank=True, 
        verbose_name='备案编号',
        help_text='系统自动生成或手动输入'
    )
    filing_content = models.TextField(verbose_name='备案内容')
    filing_purpose = models.TextField(blank=True, verbose_name='备案目的')
    filing_notes = models.TextField(blank=True, verbose_name='备注说明')
    
    # 审计字段
    created_by = models.ForeignKey(
        User, 
        on_delete=models.PROTECT, 
        related_name='created_filings', 
        verbose_name='创建人'
    )
    created_time = models.DateTimeField(default=timezone.now, verbose_name='创建时间')
    updated_time = models.DateTimeField(auto_now=True, verbose_name='更新时间')
    
    class Meta:
        db_table = 'business_opportunity_filing'
        verbose_name = '商机备案记录'
        verbose_name_plural = verbose_name
        ordering = ['-filing_date', '-created_time']
    
    def __str__(self):
        return f"{self.opportunity.name} - {self.filing_date} - {self.get_filing_type_display()}"
    
    def save(self, *args, **kwargs):
        # 如果备案编号为空，自动生成
        if not self.filing_number:
            from datetime import datetime
            date_str = datetime.now().strftime('%Y%m%d')
            count = OpportunityFiling.objects.filter(
                filing_date__year=datetime.now().year,
                filing_date__month=datetime.now().month,
                filing_date__day=datetime.now().day
            ).count()


class BiddingQuotation(models.Model):
    """投标报价记录"""
    STATUS_CHOICES = [
        ('draft', '草稿'),
        ('preparing', '准备中'),
        ('submitted', '已提交'),
        ('won', '中标'),
        ('lost', '未中标'),
        ('cancelled', '已取消'),
    ]
    
    opportunity = models.ForeignKey(
        BusinessOpportunity, 
        on_delete=models.CASCADE, 
        related_name='bidding_quotations', 
        verbose_name='关联商机'
    )
    bidding_number = models.CharField(
        max_length=100, 
        blank=True, 
        verbose_name='投标编号',
        help_text='系统自动生成或手动输入'
    )
    bidding_date = models.DateField(verbose_name='投标日期')
    submission_deadline = models.DateField(verbose_name='提交截止日期')
    status = models.CharField(
        max_length=20, 
        choices=STATUS_CHOICES, 
        default='draft', 
        verbose_name='状态'
    )
    
    # 招标要求
    tender_requirements = models.TextField(verbose_name='招标要求', help_text='根据招标文件填写的要求')
    
    # 技术标信息（JSON格式存储）
    technical_proposal = models.JSONField(
        default=dict, 
        blank=True, 
        verbose_name='技术标信息',
        help_text='技术方案、技术能力、技术团队等信息'
    )
    
    # 商务标信息（JSON格式存储）
    commercial_proposal = models.JSONField(
        default=dict, 
        blank=True, 
        verbose_name='商务标信息',
        help_text='报价、付款方式、服务承诺等商务信息'
    )
    
    # 类似业绩（关联已完成项目）
    similar_projects = models.ManyToManyField(
        'production_management.Project',
        blank=True,
        related_name='bidding_quotations',
        verbose_name='类似业绩',
        help_text='选择类似的项目作为业绩证明'
    )
    
    # 人员证书（关联员工档案中的证书）
    personnel_certificates = models.JSONField(
        default=list,
        blank=True,
        verbose_name='人员证书',
        help_text='JSON格式存储选中的员工证书信息'
    )
    
    # 公司证件（JSON格式存储）
    company_certificates = models.JSONField(
        default=list,
        blank=True,
        verbose_name='公司证件',
        help_text='JSON格式存储公司资质证书、营业执照等信息'
    )
    
    # 投标文件
    bidding_documents = models.JSONField(
        default=list,
        blank=True,
        verbose_name='投标文件',
        help_text='JSON格式存储上传的投标文件列表'
    )
    
    # 备注
    notes = models.TextField(blank=True, verbose_name='备注说明')
    
    # 审计字段
    created_by = models.ForeignKey(
        User, 
        on_delete=models.PROTECT, 
        related_name='created_bidding_quotations', 
        verbose_name='创建人'
    )
    created_time = models.DateTimeField(default=timezone.now, verbose_name='创建时间')
    updated_time = models.DateTimeField(auto_now=True, verbose_name='更新时间')
    
    class Meta:
        db_table = 'business_bidding_quotation'
        verbose_name = '投标报价记录'
        verbose_name_plural = verbose_name
        ordering = ['-bidding_date', '-created_time']
    
    def __str__(self):
        return f"{self.opportunity.name} - {self.bidding_date} - {self.get_status_display()}"
    
    def save(self, *args, **kwargs):
        # 如果投标编号为空，自动生成
        if not self.bidding_number:
            from datetime import datetime
            date_str = datetime.now().strftime('%Y%m%d')
            count = BiddingQuotation.objects.filter(
                bidding_date__year=datetime.now().year,
                bidding_date__month=datetime.now().month,
                bidding_date__day=datetime.now().day
            ).count()
            self.bidding_number = f"BID-{date_str}-{count + 1:04d}"
        super().save(*args, **kwargs)


class CustomerRequirementCommunication(models.Model):
    """客户需求沟通登记模型"""
    
    COMMUNICATION_TYPE_CHOICES = [
        ('phone', '电话沟通'),
        ('meeting', '会议沟通'),
        ('email', '邮件沟通'),
        ('site_visit', '现场拜访'),
        ('online', '线上沟通'),
        ('other', '其他'),
    ]
    
    PRIORITY_CHOICES = [
        ('low', '低'),
        ('normal', '普通'),
        ('high', '高'),
        ('urgent', '紧急'),
    ]
    
    STATUS_CHOICES = [
        ('draft', '草稿'),
        ('submitted', '已提交'),
        ('processing', '处理中'),
        ('completed', '已完成'),
        ('cancelled', '已取消'),
    ]
    
    # 关联信息
    opportunity = models.ForeignKey(
        BusinessOpportunity,
        on_delete=models.CASCADE,
        related_name='requirement_communications',
        verbose_name='关联商机'
    )
    client = models.ForeignKey(
        Client,
        on_delete=models.PROTECT,
        related_name='requirement_communications',
        verbose_name='关联客户'
    )
    
    # 基本信息
    communication_number = models.CharField(
        max_length=50,
        unique=True,
        blank=True,
        null=True,
        verbose_name='沟通编号',
        help_text='自动生成：XQ-YYYYMMDD-0000'
    )
    title = models.CharField(max_length=200, verbose_name='沟通主题')
    communication_type = models.CharField(
        max_length=20,
        choices=COMMUNICATION_TYPE_CHOICES,
        default='meeting',
        verbose_name='沟通方式'
    )
    communication_date = models.DateTimeField(verbose_name='沟通时间')
    location = models.CharField(max_length=200, blank=True, verbose_name='沟通地点')
    
    # 参与人员
    our_participants = models.ManyToManyField(
        User,
        related_name='requirement_communications_participated',
        blank=True,
        verbose_name='我方参与人员'
    )
    client_participants = models.CharField(
        max_length=500,
        blank=True,
        verbose_name='客户参与人员',
        help_text='多个人员用逗号分隔'
    )
    
    # 需求信息
    requirement_description = models.TextField(verbose_name='需求描述')
    requirement_details = models.TextField(blank=True, verbose_name='需求详情')
    technical_requirements = models.TextField(blank=True, verbose_name='技术要求')
    business_requirements = models.TextField(blank=True, verbose_name='商务要求')
    budget_range = models.CharField(max_length=200, blank=True, verbose_name='预算范围')
    timeline_requirement = models.CharField(max_length=200, blank=True, verbose_name='时间要求')
    
    # 沟通结果
    communication_result = models.TextField(blank=True, verbose_name='沟通结果')
    next_action = models.TextField(blank=True, verbose_name='下一步行动')
    next_action_date = models.DateField(null=True, blank=True, verbose_name='下次行动时间')
    
    # 优先级和状态
    priority = models.CharField(
        max_length=20,
        choices=PRIORITY_CHOICES,
        default='normal',
        verbose_name='优先级'
    )
    status = models.CharField(
        max_length=20,
        choices=STATUS_CHOICES,
        default='draft',
        verbose_name='状态'
    )
    
    # 附件和备注
    attachments = models.TextField(blank=True, verbose_name='附件说明', help_text='附件文件列表，用逗号分隔')
    notes = models.TextField(blank=True, verbose_name='备注')
    
    # 审计字段
    created_by = models.ForeignKey(
        User,
        on_delete=models.PROTECT,
        related_name='created_requirement_communications',
        verbose_name='创建人'
    )
    created_time = models.DateTimeField(default=timezone.now, verbose_name='创建时间')
    updated_time = models.DateTimeField(auto_now=True, verbose_name='更新时间')
    
    class Meta:
        db_table = 'customer_requirement_communication'
        verbose_name = '客户需求沟通登记'
        verbose_name_plural = verbose_name
        ordering = ['-communication_date', '-created_time']
        indexes = [
            models.Index(fields=['opportunity', '-communication_date']),
            models.Index(fields=['client', '-communication_date']),
            models.Index(fields=['status', '-communication_date']),
            models.Index(fields=['communication_number']),
        ]
    
    def __str__(self):
        return f"{self.title} - {self.opportunity.name if self.opportunity else '未关联商机'}"
    
    def save(self, *args, **kwargs):
        # 自动生成沟通编号：XQ-YYYYMMDD-0000（连续编号）
        if not self.communication_number:
            from django.db.models import Max
            from datetime import datetime
            current_date = datetime.now().strftime('%Y%m%d')
            date_prefix = f'XQ-{current_date}-'
            
            # 查找当天最大编号
            max_comm = CustomerRequirementCommunication.objects.filter(
                communication_number__startswith=date_prefix
            ).aggregate(max_num=Max('communication_number'))['max_num']
            
            if max_comm:
                try:
                    # 提取最后4位数字作为序号
                    seq = int(max_comm.split('-')[-1]) + 1
                except (ValueError, IndexError):
                    seq = 1
            else:
                seq = 1
            
            self.communication_number = f'{date_prefix}{seq:04d}'
        
        super().save(*args, **kwargs)


