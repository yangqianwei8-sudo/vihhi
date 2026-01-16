from django.db import models
from django.utils import timezone
from decimal import Decimal
from backend.apps.system_management.models import User


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
        db_table = 'settlement_output_value_stage'
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
        db_table = 'settlement_output_value_milestone'
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
        db_table = 'settlement_output_value_event'
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
    project = models.ForeignKey('production_management.Project', on_delete=models.CASCADE, related_name='output_value_records_center',
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
        db_table = 'settlement_output_value_record'
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


class ServiceFeeRate(models.Model):
    """服务费率表配置"""
    contract = models.ForeignKey('production_management.BusinessContract', on_delete=models.CASCADE,
                                related_name='service_fee_rates', verbose_name='关联合同',
                                null=True, blank=True, help_text='如果为空，则为全局费率表')
    min_saving_amount = models.DecimalField(max_digits=12, decimal_places=2, default=0,
                                           verbose_name='节省金额下限', help_text='该费率适用的最小节省金额')
    max_saving_amount = models.DecimalField(max_digits=12, decimal_places=2, null=True, blank=True,
                                           verbose_name='节省金额上限', help_text='该费率适用的最大节省金额（为空表示无上限）')
    service_rate = models.DecimalField(max_digits=5, decimal_places=4, verbose_name='服务费率',
                                      help_text='服务费率，例如：0.15 表示 15%')
    rate_description = models.TextField(blank=True, verbose_name='费率说明')
    order = models.IntegerField(default=0, verbose_name='排序', help_text='用于确定费率匹配优先级')
    is_active = models.BooleanField(default=True, verbose_name='是否启用')
    
    created_by = models.ForeignKey(User, on_delete=models.PROTECT, related_name='created_service_fee_rates',
                                  verbose_name='创建人')
    created_time = models.DateTimeField(default=timezone.now, verbose_name='创建时间')
    updated_time = models.DateTimeField(auto_now=True, verbose_name='更新时间')
    
    class Meta:
        db_table = 'settlement_service_fee_rate'
        verbose_name = '服务费率表'
        verbose_name_plural = verbose_name
        ordering = ['contract', 'order', 'min_saving_amount']
        indexes = [
            models.Index(fields=['contract', 'is_active', 'order']),
            models.Index(fields=['min_saving_amount', 'max_saving_amount']),
        ]
    
    def __str__(self):
        contract_name = self.contract.contract_number if self.contract else '全局'
        if self.max_saving_amount:
            range_str = f"{self.min_saving_amount} ~ {self.max_saving_amount}"
        else:
            range_str = f">= {self.min_saving_amount}"
        return f"{contract_name} - {range_str} - {self.service_rate * 100}%"
    
    def matches_amount(self, amount):
        """判断节省金额是否匹配此费率"""
        if amount < self.min_saving_amount:
            return False
        if self.max_saving_amount and amount > self.max_saving_amount:
            return False
        return True


class SettlementItem(models.Model):
    """结算明细项（从生产管理模块的Opinion逐条生成）"""
    REVIEW_STATUS_CHOICES = [
        ('pending', '待审核'),
        ('approved', '已确认'),
        ('rejected', '已驳回'),
    ]
    
    # 关联信息
    settlement = models.ForeignKey('ProjectSettlement', on_delete=models.CASCADE, related_name='items',
                                  verbose_name='关联结算单')
    opinion_id = models.IntegerField(null=True, blank=True,
                                   verbose_name='关联意见ID',
                                   help_text='从生产管理模块的意见生成（已删除生产质量模块，此字段保留用于历史数据）')
    
    # 基本信息（从Opinion自动带出）
    opinion_number = models.CharField(max_length=50, blank=True, verbose_name='意见编号',
                                     help_text='从Opinion自动带出，创建时自动填充')
    opinion_title = models.CharField(max_length=200, blank=True, verbose_name='意见标题',
                                    help_text='从Opinion自动带出')
    professional_category = models.CharField(max_length=100, blank=True, verbose_name='专业分类')
    location_name = models.CharField(max_length=200, blank=True, verbose_name='部位名称')
    
    # 节省金额信息
    original_saving_amount = models.DecimalField(max_digits=14, decimal_places=2, default=Decimal('0'),
                                                 verbose_name='原始节省金额',
                                                 help_text='从Opinion.saving_amount自动带出')
    adjusted_saving_amount = models.DecimalField(max_digits=14, decimal_places=2, null=True, blank=True,
                                                verbose_name='调整后节省金额', help_text='造价工程师手动调整')
    adjustment_reason = models.TextField(blank=True, verbose_name='调整原因')
    
    # 审核信息
    review_status = models.CharField(max_length=20, choices=REVIEW_STATUS_CHOICES, default='pending',
                                    verbose_name='审核状态')
    reviewed_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True,
                                   related_name='reviewed_settlement_items', verbose_name='审核造价工程师')
    reviewed_time = models.DateTimeField(null=True, blank=True, verbose_name='审核时间')
    review_comment = models.TextField(blank=True, verbose_name='审核意见')
    rejection_reason = models.TextField(blank=True, verbose_name='驳回原因')
    
    # 排序
    order = models.IntegerField(default=0, verbose_name='排序')
    
    created_by = models.ForeignKey(User, on_delete=models.PROTECT, related_name='created_settlement_items',
                                  verbose_name='创建人')
    created_time = models.DateTimeField(default=timezone.now, verbose_name='创建时间')
    updated_time = models.DateTimeField(auto_now=True, verbose_name='更新时间')
    
    class Meta:
        db_table = 'settlement_settlement_item'
        verbose_name = '结算明细项'
        verbose_name_plural = verbose_name
        ordering = ['settlement', 'order', 'created_time']
        indexes = [
            models.Index(fields=['settlement', 'order']),
            models.Index(fields=['opinion_id']),
            models.Index(fields=['review_status']),
        ]
        unique_together = [['settlement', 'opinion_id']]  # 同一结算单中每个意见只能出现一次
    
    def __str__(self):
        return f"{self.settlement.settlement_number} - {self.opinion_number} - {self.opinion_title}"
    
    @property
    def final_saving_amount(self):
        """最终节省金额（审核通过后使用调整后金额，否则为0）"""
        if self.review_status == 'approved':
            return self.adjusted_saving_amount if self.adjusted_saving_amount else self.original_saving_amount
        return Decimal('0')


class ProjectSettlement(models.Model):
    """项目结算"""
    STATUS_CHOICES = [
        ('draft', '草稿'),
        ('submitted', '已提交'),
        ('client_review', '甲方初审中'),
        ('client_feedback', '甲方反馈'),
        ('reconciliation', '对账中'),
        ('confirmed', '已确认'),
        ('cancelled', '已取消'),
    ]
    
    SETTLEMENT_TYPE_CHOICES = [
        ('interim', '阶段结算'),
        ('final', '最终结算'),
    ]
    
    # 关联信息
    project = models.ForeignKey('production_management.Project', on_delete=models.PROTECT, 
                               related_name='settlements_center', verbose_name='关联项目',
                               help_text='仅显示状态为"已完工"的项目')
    contract = models.ForeignKey('production_management.BusinessContract', on_delete=models.SET_NULL,
                                null=True, blank=True, related_name='project_settlements',
                                verbose_name='关联合同')
    service_fee_scheme = models.ForeignKey('ServiceFeeSettlementScheme', on_delete=models.SET_NULL,
                                          null=True, blank=True, related_name='project_settlements',
                                          verbose_name='服务费结算方案',
                                          help_text='可选，如果设置则使用此方案计算服务费，否则使用合同费率表')
    
    # 基本信息
    settlement_number = models.CharField(max_length=100, unique=True, verbose_name='结算单号',
                                        help_text='格式：VIH-JS-{项目编号}-{序列号}')
    settlement_type = models.CharField(max_length=20, choices=SETTLEMENT_TYPE_CHOICES, 
                                      default='interim', verbose_name='结算类型')
    settlement_period_start = models.DateField(null=True, blank=True, verbose_name='结算周期开始日期',
                                               help_text='新增时必填，历史数据可为空')
    settlement_period_end = models.DateField(null=True, blank=True, verbose_name='结算周期结束日期',
                                             help_text='新增时必填，历史数据可为空')
    settlement_date = models.DateField(verbose_name='结算日期', help_text='默认当前日期')
    
    # 节省金额汇总（自动计算）
    original_total_saving = models.DecimalField(max_digits=14, decimal_places=2, default=0,
                                                verbose_name='原始节省总额',
                                                help_text='自动计算所有Opinion原始节省金额总和')
    reviewed_total_saving = models.DecimalField(max_digits=14, decimal_places=2, default=0,
                                                verbose_name='审核后节省总额',
                                                help_text='自动计算所有已确认意见的调整后节省金额总和')
    saving_adjustment_diff = models.DecimalField(max_digits=14, decimal_places=2, default=0,
                                                 verbose_name='调整差额',
                                                 help_text='自动计算：审核后节省总额 - 原始节省总额')
    
    # 服务费计算（基于节省金额）
    fee_base_amount = models.DecimalField(max_digits=14, decimal_places=2, default=0,
                                         verbose_name='取费基数', help_text='等于审核后节省总额，只读')
    service_fee_rate = models.DecimalField(max_digits=5, decimal_places=4, null=True, blank=True,
                                          verbose_name='服务费率', help_text='从合同费率表自动匹配')
    service_fee_amount = models.DecimalField(max_digits=14, decimal_places=2, default=0,
                                            verbose_name='服务费金额', help_text='自动计算：取费基数 × 服务费率')
    base_service_fee = models.DecimalField(max_digits=12, decimal_places=2, default=0,
                                          verbose_name='基础服务费', help_text='从合同模块同步的固定服务费（如有）')
    total_settlement_amount = models.DecimalField(max_digits=14, decimal_places=2, default=0,
                                                  verbose_name='结算总金额',
                                                  help_text='自动计算：基础服务费 + 服务费金额')
    
    # 合同金额信息（用于参考）
    contract_amount = models.DecimalField(max_digits=12, decimal_places=2, default=0,
                                         verbose_name='合同金额', help_text='用于参考')
    tax_rate = models.DecimalField(max_digits=5, decimal_places=2, default=6.00,
                                  verbose_name='税率(%)', help_text='默认6%，用于税额计算')
    tax_amount = models.DecimalField(max_digits=12, decimal_places=2, default=0, verbose_name='税额')
    settlement_amount_tax = models.DecimalField(max_digits=14, decimal_places=2, default=0,
                                                verbose_name='结算总金额（含税）',
                                                help_text='结算总金额 + 税额')
    
    # 产值统计（从产值管理模块获取）
    total_output_value = models.DecimalField(max_digits=12, decimal_places=2, default=0,
                                            verbose_name='累计产值', help_text='项目累计计算的产值')
    confirmed_output_value = models.DecimalField(max_digits=12, decimal_places=2, default=0,
                                                verbose_name='确认产值', help_text='本次结算确认的产值')
    
    # 状态和流程
    status = models.CharField(max_length=30, choices=STATUS_CHOICES, default='draft', verbose_name='状态')
    submitted_by = models.ForeignKey(User, on_delete=models.PROTECT, null=True, blank=True,
                                    related_name='submitted_settlements', verbose_name='提交人')
    submitted_time = models.DateTimeField(null=True, blank=True, verbose_name='提交时间')
    
    # 甲方初审信息
    client_reviewer = models.CharField(max_length=100, blank=True, verbose_name='甲方初审人')
    client_reviewed_time = models.DateTimeField(null=True, blank=True, verbose_name='甲方初审时间')
    client_review_comment = models.TextField(blank=True, verbose_name='甲方初审意见')
    client_feedback_comment = models.TextField(blank=True, verbose_name='甲方反馈意见')
    client_feedback_time = models.DateTimeField(null=True, blank=True, verbose_name='甲方反馈时间')
    
    # 对账信息
    reconciliation_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True,
                                         related_name='reconciled_settlements', verbose_name='对账人')
    reconciliation_time = models.DateTimeField(null=True, blank=True, verbose_name='对账时间')
    reconciliation_comment = models.TextField(blank=True, verbose_name='对账说明')
    
    # 确认信息
    confirmed_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True,
                                    related_name='confirmed_settlements', verbose_name='确认人')
    confirmed_time = models.DateTimeField(null=True, blank=True, verbose_name='确认时间')
    
    # 附件和备注
    settlement_file = models.FileField(upload_to='settlements/%Y/%m/', null=True, blank=True,
                                      verbose_name='结算文件')
    description = models.TextField(blank=True, verbose_name='结算说明')
    notes = models.TextField(blank=True, verbose_name='备注')
    
    created_by = models.ForeignKey(User, on_delete=models.PROTECT, related_name='created_settlements',
                                  verbose_name='创建人')
    created_time = models.DateTimeField(default=timezone.now, verbose_name='创建时间')
    updated_time = models.DateTimeField(auto_now=True, verbose_name='更新时间')
    
    class Meta:
        db_table = 'settlement_project_settlement'
        verbose_name = '项目结算'
        verbose_name_plural = verbose_name
        ordering = ['-settlement_date', '-created_time']
        indexes = [
            models.Index(fields=['settlement_number']),
            models.Index(fields=['project', 'status']),
            models.Index(fields=['settlement_date']),
            models.Index(fields=['status']),
        ]
    
    def __str__(self):
        return f"{self.settlement_number} - {self.project.name}"
    
    def save(self, *args, **kwargs):
        from django.db.models import Sum, Max
        from datetime import date
        
        # 自动生成结算单号（格式：VIH-JS-{项目编号}-{序列号}）
        if not self.settlement_number and self.project_id:
            project_number = self.project.project_number
            # 查找该项目下已有的最大结算单号
            max_settlement = ProjectSettlement.objects.filter(
                settlement_number__startswith=f'VIH-JS-{project_number}-'
            ).aggregate(max_num=Max('settlement_number'))['max_num']
            
            if max_settlement:
                try:
                    # 提取序列号，格式：VIH-JS-{项目编号}-{序列号}
                    seq_str = max_settlement.split('-')[-1]
                    seq = int(seq_str) + 1
                except (ValueError, IndexError):
                    seq = 1
            else:
                seq = 1
            self.settlement_number = f'VIH-JS-{project_number}-{seq:04d}'
        
        # 如果没有结算日期，默认为当前日期
        if not self.settlement_date:
            self.settlement_date = date.today()
        
        # 自动计算节省金额汇总（从明细项计算）
        if self.pk:
            # 原始节省总额（所有Opinion的原始节省金额）
            original_total = self.items.aggregate(total=Sum('original_saving_amount'))['total'] or Decimal('0')
            self.original_total_saving = original_total
            
            # 审核后节省总额（仅计算已确认的明细项的调整后节省金额）
            reviewed_total = self.items.filter(review_status='approved').aggregate(
                total=Sum('adjusted_saving_amount')
            )['total']
            if not reviewed_total:
                reviewed_total = self.items.filter(review_status='approved').aggregate(
                    total=Sum('original_saving_amount')
                )['total'] or Decimal('0')
            self.reviewed_total_saving = reviewed_total
            
            # 调整差额
            self.saving_adjustment_diff = self.reviewed_total_saving - self.original_total_saving
            
            # 服务费计算
            self.fee_base_amount = self.reviewed_total_saving
            
            # 优先使用服务费结算方案，否则使用合同费率表
            if self.service_fee_scheme_id and self.service_fee_scheme.is_active:
                # 使用新的结算方案计算服务费
                self._calculate_service_fee_by_scheme()
            else:
                # 使用旧的费率表方式
                if self.contract_id:
                    fee_rate = self._match_service_fee_rate(self.reviewed_total_saving)
                    if fee_rate:
                        self.service_fee_rate = fee_rate.service_rate
                        
                        # 从合同获取基础服务费（如果合同模型中有此字段）
                        if hasattr(self.contract, 'base_service_fee'):
                            self.base_service_fee = self.contract.base_service_fee or Decimal('0')
                
                # 计算服务费金额
                if self.service_fee_rate and self.fee_base_amount:
                    self.service_fee_amount = self.fee_base_amount * self.service_fee_rate
                else:
                    self.service_fee_amount = Decimal('0')
            
            # 计算结算总金额
            self.total_settlement_amount = self.base_service_fee + self.service_fee_amount
            
            # 计算税额和含税金额
            if self.total_settlement_amount:
                self.tax_amount = self.total_settlement_amount * (self.tax_rate / 100)
                self.settlement_amount_tax = self.total_settlement_amount + self.tax_amount
        
        super().save(*args, **kwargs)
    
    def _match_service_fee_rate(self, saving_amount):
        """根据节省金额匹配服务费率"""
        if not self.contract_id:
            return None
        
        # 优先从合同关联的费率表中查找
        rates = ServiceFeeRate.objects.filter(
            contract=self.contract,
            is_active=True,
            min_saving_amount__lte=saving_amount
        ).exclude(
            max_saving_amount__lt=saving_amount
        ).order_by('order', 'min_saving_amount')
        
        if rates.exists():
            return rates.first()
        
        # 如果没有合同关联的费率，查找全局费率表
        global_rates = ServiceFeeRate.objects.filter(
            contract__isnull=True,
            is_active=True,
            min_saving_amount__lte=saving_amount
        ).exclude(
            max_saving_amount__lt=saving_amount
        ).order_by('order', 'min_saving_amount')
        
        if global_rates.exists():
            return global_rates.first()
        
        return None
    
    def _calculate_service_fee_by_scheme(self):
        """使用服务费结算方案计算服务费"""
        if not self.service_fee_scheme_id or not self.service_fee_scheme.is_active:
            return
        
        from backend.apps.settlement_center.services import (
            calculate_service_fee_by_scheme,
            get_project_area_by_type
        )
        
        # 获取服务面积（如果需要）
        service_area = None
        if self.service_fee_scheme.settlement_method in ['fixed_unit', 'combined']:
            area_type = (
                self.service_fee_scheme.area_type or 
                self.service_fee_scheme.combined_fixed_area_type
            )
            if area_type and self.project_id:
                service_area = get_project_area_by_type(self.project, area_type)
        
        # 获取单价封顶明细（如果需要）
        unit_cap_details = None
        if (self.service_fee_scheme.has_cap_fee and 
            self.service_fee_scheme.cap_type == 'unit_cap'):
            unit_cap_details = []
            for detail in self.service_fee_scheme.unit_cap_details.all():
                # 从项目中获取该单体的面积（这里简化处理，实际可能需要更复杂的逻辑）
                area = service_area if service_area else Decimal('0')
                unit_cap_details.append({
                    'unit_name': detail.unit_name,
                    'area': area,
                    'cap_unit_price': detail.cap_unit_price
                })
        
        # 计算服务费
        result = calculate_service_fee_by_scheme(
            scheme=self.service_fee_scheme,
            saving_amount=self.reviewed_total_saving,
            service_area=service_area,
            unit_cap_details=unit_cap_details
        )
        
        # 更新服务费相关字段
        # 如果是组合方式，分离固定部分和按实结算部分
        if self.service_fee_scheme.settlement_method == 'combined':
            self.base_service_fee = result['fixed_part']
            self.service_fee_amount = result['actual_part']  # 只包含按实结算部分
        else:
            # 非组合方式，service_fee_amount包含全部，base_service_fee为0或从合同获取
            self.service_fee_amount = result['final_fee']
            if not self.base_service_fee and self.contract_id:
                if hasattr(self.contract, 'base_service_fee'):
                    self.base_service_fee = self.contract.base_service_fee or Decimal('0')
    
    def calculate_service_fee(self):
        """手动触发服务费计算（用于外部调用）"""
        if self.pk:
            self._calculate_service_fee_by_scheme() if (
                self.service_fee_scheme_id and self.service_fee_scheme.is_active
            ) else self._recalculate_service_fee_by_rate()
            self.save()
    
    def _recalculate_service_fee_by_rate(self):
        """使用费率表重新计算服务费（旧方式）"""
        if self.contract_id:
            fee_rate = self._match_service_fee_rate(self.reviewed_total_saving)
            if fee_rate:
                self.service_fee_rate = fee_rate.service_rate
                if hasattr(self.contract, 'base_service_fee'):
                    self.base_service_fee = self.contract.base_service_fee or Decimal('0')
        
        if self.service_fee_rate and self.fee_base_amount:
            self.service_fee_amount = self.fee_base_amount * self.service_fee_rate
        else:
            self.service_fee_amount = Decimal('0')


class ContractSettlement(models.Model):
    """合同结算"""
    STATUS_CHOICES = [
        ('draft', '草稿'),
        ('submitted', '已提交'),
        ('approved', '已批准'),
        ('rejected', '已拒绝'),
        ('confirmed', '已确认'),
        ('cancelled', '已取消'),
    ]
    
    # 关联信息
    contract = models.ForeignKey('production_management.BusinessContract', on_delete=models.PROTECT,
                                related_name='contract_settlements', verbose_name='关联合同')
    
    # 基本信息
    settlement_number = models.CharField(max_length=100, unique=True, verbose_name='结算单号')
    settlement_date = models.DateField(verbose_name='结算日期')
    settlement_batch = models.IntegerField(default=1, verbose_name='结算批次',
                                          help_text='同一合同的第几次结算')
    
    # 金额信息
    contract_amount = models.DecimalField(max_digits=12, decimal_places=2, verbose_name='合同金额')
    previous_settlement_amount = models.DecimalField(max_digits=12, decimal_places=2, default=0,
                                                    verbose_name='已结算金额', help_text='本次结算前已结算的金额')
    this_settlement_amount = models.DecimalField(max_digits=12, decimal_places=2, verbose_name='本次结算金额')
    total_settlement_amount = models.DecimalField(max_digits=12, decimal_places=2, verbose_name='累计结算金额',
                                                 help_text='本次结算后的累计结算金额')
    tax_rate = models.DecimalField(max_digits=5, decimal_places=2, default=6.00, verbose_name='税率(%)')
    tax_amount = models.DecimalField(max_digits=12, decimal_places=2, default=0, verbose_name='税额')
    settlement_amount_tax = models.DecimalField(max_digits=12, decimal_places=2, verbose_name='结算金额（含税）')
    
    # 状态和流程
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='draft', verbose_name='状态')
    submitted_by = models.ForeignKey(User, on_delete=models.PROTECT, null=True, blank=True,
                                    related_name='submitted_contract_settlements', verbose_name='提交人')
    submitted_time = models.DateTimeField(null=True, blank=True, verbose_name='提交时间')
    
    # 审核信息
    approver = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True,
                                related_name='approved_contract_settlements', verbose_name='审核人')
    approved_time = models.DateTimeField(null=True, blank=True, verbose_name='审核时间')
    review_comment = models.TextField(blank=True, verbose_name='审核意见')
    
    # 确认信息
    confirmed_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True,
                                    related_name='confirmed_contract_settlements', verbose_name='确认人')
    confirmed_time = models.DateTimeField(null=True, blank=True, verbose_name='确认时间')
    
    # 附件和备注
    settlement_file = models.FileField(upload_to='contract_settlements/%Y/%m/', null=True, blank=True,
                                      verbose_name='结算文件')
    invoice_number = models.CharField(max_length=100, blank=True, verbose_name='发票号码')
    description = models.TextField(blank=True, verbose_name='结算说明')
    notes = models.TextField(blank=True, verbose_name='备注')
    
    created_by = models.ForeignKey(User, on_delete=models.PROTECT, related_name='created_contract_settlements',
                                  verbose_name='创建人')
    created_time = models.DateTimeField(default=timezone.now, verbose_name='创建时间')
    updated_time = models.DateTimeField(auto_now=True, verbose_name='更新时间')
    
    class Meta:
        db_table = 'settlement_contract_settlement'
        verbose_name = '合同结算'
        verbose_name_plural = verbose_name
        ordering = ['-settlement_date', '-settlement_batch']
        indexes = [
            models.Index(fields=['settlement_number']),
            models.Index(fields=['contract', 'status']),
            models.Index(fields=['settlement_date']),
            models.Index(fields=['contract', 'settlement_batch']),
        ]
        unique_together = [['contract', 'settlement_batch']]
    
    def __str__(self):
        return f"{self.settlement_number} - {self.contract.contract_number} - 第{self.settlement_batch}批"
    
    def save(self, *args, **kwargs):
        # 自动生成结算单号
        if not self.settlement_number:
            from django.db.models import Max
            from datetime import datetime
            current_year = datetime.now().year
            max_settlement = ContractSettlement.objects.filter(
                settlement_number__startswith=f'CONTRACT-SETTLE-{current_year}-'
            ).aggregate(max_num=Max('settlement_number'))['max_num']
            
            if max_settlement:
                try:
                    seq = int(max_settlement.split('-')[-1]) + 1
                except (ValueError, IndexError):
                    seq = 1
            else:
                seq = 1
            self.settlement_number = f'CONTRACT-SETTLE-{current_year}-{seq:04d}'
        
        # 自动计算累计结算金额
        if not self.total_settlement_amount:
            self.total_settlement_amount = self.previous_settlement_amount + self.this_settlement_amount
        
        # 自动计算税额和含税金额
        if not self.tax_amount and self.this_settlement_amount:
            self.tax_amount = self.this_settlement_amount * (self.tax_rate / 100)
        if not self.settlement_amount_tax and self.this_settlement_amount:
            self.settlement_amount_tax = self.this_settlement_amount + (self.tax_amount or Decimal('0'))
        
        super().save(*args, **kwargs)


# ==================== 回款管理模块 ====================

class PaymentRecord(models.Model):
    """回款记录（实际回款）"""
    PAYMENT_METHOD_CHOICES = [
        ('bank_transfer', '银行转账'),
        ('cash', '现金'),
        ('check', '支票'),
        ('acceptance', '承兑汇票'),
        ('other', '其他'),
    ]
    
    # 关联回款计划（支持项目回款计划和商务回款计划）
    payment_plan_id = models.IntegerField(verbose_name='回款计划ID')
    payment_plan_type = models.CharField(
        max_length=50, 
        choices=[
            ('project', '项目回款计划'),
            ('business', '商务回款计划'),
        ],
        verbose_name='回款计划类型'
    )
    
    # 回款信息
    payment_number = models.CharField(max_length=100, unique=True, verbose_name='回款单号')
    payment_amount = models.DecimalField(max_digits=12, decimal_places=2, verbose_name='回款金额')
    payment_date = models.DateField(verbose_name='回款日期')
    payment_method = models.CharField(max_length=20, choices=PAYMENT_METHOD_CHOICES, verbose_name='回款方式')
    
    # 财务信息
    invoice_number = models.CharField(max_length=100, blank=True, verbose_name='发票号码')
    bank_account = models.CharField(max_length=200, blank=True, verbose_name='收款账户')
    receipt_voucher = models.FileField(upload_to='payment_receipts/', null=True, blank=True, verbose_name='收款凭证')
    
    # 状态和审核
    status = models.CharField(
        max_length=20,
        choices=[
            ('pending', '待确认'),
            ('confirmed', '已确认'),
            ('rejected', '已拒绝'),
        ],
        default='pending',
        verbose_name='状态'
    )
    confirmed_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True, related_name='confirmed_payments', verbose_name='确认人')
    confirmed_time = models.DateTimeField(null=True, blank=True, verbose_name='确认时间')
    
    # 备注
    notes = models.TextField(blank=True, verbose_name='备注')
    created_by = models.ForeignKey(User, on_delete=models.PROTECT, related_name='created_payments', verbose_name='创建人')
    created_time = models.DateTimeField(default=timezone.now, verbose_name='创建时间')
    
    class Meta:
        db_table = 'settlement_payment_record'
        verbose_name = '回款记录'
        verbose_name_plural = verbose_name
        ordering = ['-payment_date', '-created_time']
        indexes = [
            models.Index(fields=['payment_plan_type', 'payment_plan_id']),
            models.Index(fields=['payment_number']),
            models.Index(fields=['payment_date']),
            models.Index(fields=['status']),
        ]
    
    def __str__(self):
        return f"{self.payment_number} - ¥{self.payment_amount}"
    
    def save(self, *args, **kwargs):
        # 自动生成回款单号
        if not self.payment_number:
            from django.db.models import Max
            from datetime import datetime
            current_year = datetime.now().year
            max_payment = PaymentRecord.objects.filter(
                payment_number__startswith=f'PAY-{current_year}-'
            ).aggregate(max_num=Max('payment_number'))['max_num']
            
            if max_payment:
                try:
                    seq = int(max_payment.split('-')[-1]) + 1
                except (ValueError, IndexError):
                    seq = 1
            else:
                seq = 1
            
            self.payment_number = f'PAY-{current_year}-{seq:04d}'
        
        super().save(*args, **kwargs)
    
    def get_payment_plan(self):
        """获取关联的回款计划对象"""
        if self.payment_plan_type == 'project':
            # 项目回款计划模型已删除，返回None
            return None
        elif self.payment_plan_type == 'business':
            from backend.apps.production_management.models import BusinessPaymentPlan
            try:
                return BusinessPaymentPlan.objects.get(id=self.payment_plan_id)
            except BusinessPaymentPlan.DoesNotExist:
                return None
        return None


# ==================== 服务费结算方案模块 ====================

class ServiceFeeSettlementSchemeQuerySet(models.QuerySet):
    """服务费结算方案查询集"""
    
    def active(self):
        """返回启用的方案"""
        return self.filter(is_active=True)
    
    def by_contract(self, contract_id):
        """根据合同ID过滤"""
        return self.filter(contract_id=contract_id)
    
    def by_project(self, project_id):
        """根据项目ID过滤"""
        return self.filter(project_id=project_id)
    
    def global_schemes(self):
        """返回全局方案（未关联合同和项目）"""
        return self.filter(contract__isnull=True, project__isnull=True)
    
    def by_method(self, method):
        """根据结算方式过滤"""
        return self.filter(settlement_method=method)
    
    def default_schemes(self):
        """返回默认方案"""
        return self.filter(is_default=True, is_active=True)
    
    def with_relations(self):
        """预加载关联对象"""
        return self.select_related('contract', 'project', 'created_by').prefetch_related(
            'segmented_rates', 'jump_point_rates', 'unit_cap_details'
        )


class ServiceFeeSettlementSchemeManager(models.Manager):
    """服务费结算方案管理器"""
    
    def get_queryset(self):
        return ServiceFeeSettlementSchemeQuerySet(self.model, using=self._db)
    
    def active(self):
        return self.get_queryset().active()
    
    def by_contract(self, contract_id):
        return self.get_queryset().by_contract(contract_id)
    
    def by_project(self, project_id):
        return self.get_queryset().by_project(project_id)
    
    def global_schemes(self):
        return self.get_queryset().global_schemes()
    
    def by_method(self, method):
        return self.get_queryset().by_method(method)
    
    def default_schemes(self):
        return self.get_queryset().default_schemes()
    
    def with_relations(self):
        return self.get_queryset().with_relations()


class ServiceFeeSettlementScheme(models.Model):
    """服务项目服务费结算方案"""
    
    SETTLEMENT_METHOD_CHOICES = [
        ('fixed_total', '固定总价'),
        ('fixed_unit', '固定单价'),
        ('cumulative_commission', '累计提成'),
        ('segmented_commission', '分段递增提成'),
        ('jump_point_commission', '跳点提成'),
        ('combined', '固定价款 + 按实结算'),
    ]
    
    AREA_TYPE_CHOICES = [
        ('drawing_building_area', '图纸建筑面积'),
        ('drawing_structure_area', '图纸结构面积'),
        ('planning_building_area', '报规建筑面积'),
        ('completion_building_area', '竣工建筑面积'),
        ('survey_area', '测绘面积'),
    ]
    
    CAP_TYPE_CHOICES = [
        ('total_cap', '总价封顶'),
        ('unit_cap', '单价封顶'),
        ('no_cap', '不设置封顶'),
    ]
    
    # 基本信息
    name = models.CharField('方案名称', max_length=200, help_text='结算方案的名称')
    code = models.CharField('方案代码', max_length=50, unique=True, blank=True, null=True, 
                          help_text='可选，用于系统识别')
    description = models.TextField('方案描述', blank=True)
    
    # 关联信息
    contract = models.ForeignKey('production_management.BusinessContract', 
                                 on_delete=models.CASCADE,
                                 related_name='service_fee_schemes',
                                 verbose_name='关联合同',
                                 null=True, blank=True,
                                 help_text='如果为空，则为全局方案模板')
    project = models.ForeignKey('production_management.Project',
                               on_delete=models.SET_NULL,
                               null=True, blank=True,
                               related_name='service_fee_schemes',
                               verbose_name='关联项目',
                               help_text='可选，用于项目特定的结算方案')
    
    # 结算方式
    settlement_method = models.CharField(max_length=30, 
                                        choices=SETTLEMENT_METHOD_CHOICES,
                                        verbose_name='结算方式')
    
    # ========== 方式一：固定价款 ==========
    # 1.1 固定总价
    fixed_total_price = models.DecimalField('固定总价', max_digits=14, decimal_places=2,
                                            null=True, blank=True,
                                            help_text='方式一：固定总价')
    
    # 1.2 固定单价
    fixed_unit_price = models.DecimalField('固定单价', max_digits=12, decimal_places=2,
                                          null=True, blank=True,
                                          help_text='方式一：固定单价（元/平方米）')
    area_scale = models.DecimalField('面积规模', max_digits=15, decimal_places=2,
                                    null=True, blank=True,
                                    help_text='面积规模（平方米），从服务内容移到结算方式')
    area_type = models.CharField('面积类型', max_length=30, choices=AREA_TYPE_CHOICES,
                                 blank=True, null=True,
                                 help_text='方式一：固定单价时使用的面积类型')
    
    # ========== 方式二：按实结算 ==========
    # 2.1 累计提成
    cumulative_rate = models.DecimalField('累计提成系数(%)', max_digits=5, decimal_places=2,
                                         null=True, blank=True,
                                         help_text='方式二：累计提成的取费系数，例如：10.5 表示 10.5%')
    
    # 2.2 分段递增提成（通过关联表 ServiceFeeSegmentedRate 存储）
    # 2.3 跳点提成（通过关联表 ServiceFeeJumpPointRate 存储）
    
    # ========== 方式三：组合方式 ==========
    # 组合方式时，需要同时配置固定部分和按实结算部分
    combined_fixed_method = models.CharField('组合-固定部分方式', max_length=20,
                                            choices=[('fixed_total', '固定总价'), ('fixed_unit', '固定单价')],
                                            blank=True, null=True,
                                            help_text='方式三：固定部分采用的方式')
    combined_fixed_total = models.DecimalField('组合-固定总价', max_digits=14, decimal_places=2,
                                              null=True, blank=True,
                                              help_text='方式三：固定部分为固定总价时的金额')
    combined_fixed_unit = models.DecimalField('组合-固定单价', max_digits=12, decimal_places=2,
                                             null=True, blank=True,
                                             help_text='方式三：固定部分为固定单价时的单价')
    combined_fixed_area_type = models.CharField('组合-固定面积类型', max_length=30,
                                                choices=AREA_TYPE_CHOICES,
                                                blank=True, null=True,
                                                help_text='方式三：固定部分为固定单价时的面积类型')
    combined_actual_method = models.CharField('组合-按实结算方式', max_length=30,
                                              choices=[
                                                  ('cumulative_commission', '累计提成'),
                                                  ('segmented_commission', '分段递增提成'),
                                                  ('jump_point_commission', '跳点提成'),
                                              ],
                                              blank=True, null=True,
                                              help_text='方式三：按实结算部分采用的方式')
    combined_cumulative_rate = models.DecimalField('组合-累计提成系数(%)', max_digits=5, decimal_places=2,
                                                   null=True, blank=True,
                                                   help_text='方式三：按实结算部分为累计提成时的系数')
    combined_deduct_fixed = models.BooleanField('组合-按实结算是否扣除固定部分', default=False,
                                               help_text='方式三：按实结算计算时是否应扣除固定价款部分')
    
    # ========== 服务费与封顶费 ==========
    # 服务费
    service_fee = models.DecimalField('服务费', max_digits=14, decimal_places=2,
                                     null=True, blank=True,
                                     help_text='服务费金额（元）')
    
    # 封顶费（改为直接输入数字）
    cap_fee = models.DecimalField('封顶费', max_digits=14, decimal_places=2,
                                  null=True, blank=True,
                                  help_text='封顶费金额（元）')
    # 保留原有字段以兼容旧数据
    has_cap_fee = models.BooleanField('是否设置封顶费', default=False)
    cap_type = models.CharField('封顶费类型', max_length=20, choices=CAP_TYPE_CHOICES,
                               blank=True, null=True,
                               help_text='总价封顶或单价封顶（已废弃，使用cap_fee）')
    total_cap_amount = models.DecimalField('总价封顶金额', max_digits=14, decimal_places=2,
                                          null=True, blank=True,
                                          help_text='封顶费为总价封顶时的金额（已废弃，使用cap_fee）')
    # 单价封顶通过关联表 ServiceFeeUnitCapDetail 存储各单体的封顶单价
    
    # 保底费
    has_minimum_fee = models.BooleanField('是否设置保底费', default=False)
    minimum_fee_amount = models.DecimalField('保底费金额', max_digits=14, decimal_places=2,
                                            null=True, blank=True,
                                            help_text='保底费金额')
    
    # 状态和排序
    is_active = models.BooleanField('是否启用', default=True, db_index=True)
    is_default = models.BooleanField('是否默认', default=False,
                                     help_text='设为默认后，创建结算时自动选中')
    sort_order = models.IntegerField('排序', default=0, help_text='数字越小越靠前')
    
    # 时间信息
    created_by = models.ForeignKey(User, on_delete=models.PROTECT,
                                   related_name='created_service_fee_schemes',
                                   verbose_name='创建人')
    created_time = models.DateTimeField('创建时间', default=timezone.now, db_index=True)
    updated_time = models.DateTimeField('更新时间', auto_now=True)
    
    # 自定义管理器
    objects = ServiceFeeSettlementSchemeManager()
    
    class Meta:
        db_table = 'settlement_service_fee_scheme'
        verbose_name = '服务费结算方案'
        verbose_name_plural = '服务费结算方案'
        ordering = ['sort_order', '-created_time']
        indexes = [
            models.Index(fields=['contract', 'is_active']),
            models.Index(fields=['project', 'is_active']),
            models.Index(fields=['settlement_method', 'is_active']),
            models.Index(fields=['is_default', 'is_active']),
        ]
    
    def __str__(self):
        contract_name = self.contract.contract_number if self.contract else '全局'
        return f"{contract_name} - {self.name} ({self.get_settlement_method_display()})"
    
    def clean(self):
        """模型验证"""
        from django.core.exceptions import ValidationError
        
        # 根据结算方式验证必填字段
        if self.settlement_method == 'fixed_total':
            if not self.fixed_total_price:
                raise ValidationError({'fixed_total_price': '固定总价方式必须填写固定总价'})
        
        elif self.settlement_method == 'fixed_unit':
            if not self.fixed_unit_price:
                raise ValidationError({'fixed_unit_price': '固定单价方式必须填写固定单价'})
            if not self.area_type:
                raise ValidationError({'area_type': '固定单价方式必须选择面积类型'})
        
        elif self.settlement_method == 'cumulative_commission':
            if not self.cumulative_rate:
                raise ValidationError({'cumulative_rate': '累计提成方式必须填写取费系数'})
        
        elif self.settlement_method == 'segmented_commission':
            # 分段递增提成需要至少一个分段配置
            if self.pk:
                if not self.segmented_rates.filter(is_active=True).exists():
                    raise ValidationError('分段递增提成方式必须至少配置一个分段')
        
        elif self.settlement_method == 'jump_point_commission':
            # 跳点提成需要至少一个跳点配置
            if self.pk:
                if not self.jump_point_rates.filter(is_active=True).exists():
                    raise ValidationError('跳点提成方式必须至少配置一个跳点')
        
        elif self.settlement_method == 'combined':
            if not self.combined_fixed_method:
                raise ValidationError({'combined_fixed_method': '组合方式必须选择固定部分方式'})
            if not self.combined_actual_method:
                raise ValidationError({'combined_actual_method': '组合方式必须选择按实结算部分方式'})
            
            # 验证固定部分
            if self.combined_fixed_method == 'fixed_total' and not self.combined_fixed_total:
                raise ValidationError({'combined_fixed_total': '组合方式固定部分为固定总价时必须填写金额'})
            elif self.combined_fixed_method == 'fixed_unit':
                if not self.combined_fixed_unit:
                    raise ValidationError({'combined_fixed_unit': '组合方式固定部分为固定单价时必须填写单价'})
                if not self.combined_fixed_area_type:
                    raise ValidationError({'combined_fixed_area_type': '组合方式固定部分为固定单价时必须选择面积类型'})
            
            # 验证按实结算部分
            if self.combined_actual_method == 'cumulative_commission' and not self.combined_cumulative_rate:
                raise ValidationError({'combined_cumulative_rate': '组合方式按实结算部分为累计提成时必须填写系数'})
            elif self.combined_actual_method == 'segmented_commission':
                if self.pk and not self.segmented_rates.filter(is_active=True).exists():
                    raise ValidationError('组合方式按实结算部分为分段递增提成时必须至少配置一个分段')
            elif self.combined_actual_method == 'jump_point_commission':
                if self.pk and not self.jump_point_rates.filter(is_active=True).exists():
                    raise ValidationError('组合方式按实结算部分为跳点提成时必须至少配置一个跳点')
        
        # 验证封顶费
        if self.has_cap_fee:
            if not self.cap_type or self.cap_type == 'no_cap':
                raise ValidationError({'cap_type': '设置封顶费时必须选择封顶费类型'})
            if self.cap_type == 'total_cap' and not self.total_cap_amount:
                raise ValidationError({'total_cap_amount': '总价封顶时必须填写封顶金额'})
            elif self.cap_type == 'unit_cap':
                if self.pk and not self.unit_cap_details.exists():
                    raise ValidationError('单价封顶时必须至少配置一个单体明细')
        
        # 验证保底费
        if self.has_minimum_fee and not self.minimum_fee_amount:
            raise ValidationError({'minimum_fee_amount': '设置保底费时必须填写保底费金额'})
    
    def save(self, *args, **kwargs):
        """保存前进行验证"""
        self.full_clean()
        super().save(*args, **kwargs)
    
    def calculate_settlement_fee(self, saving_amount=None, service_area=None, 
                                 unit_cap_details=None):
        """计算结算服务费
        
        Args:
            saving_amount: 节省金额（按实结算时使用）
            service_area: 服务面积（固定单价时使用）
            unit_cap_details: 单价封顶明细列表，格式：[{'unit_name': '单体名称', 'area': 面积, 'cap_unit_price': 封顶单价}]
        
        Returns:
            Decimal: 计算出的结算价
        """
        from decimal import Decimal
        
        settlement_price = Decimal('0')
        
        # 方式一：固定价款
        if self.settlement_method == 'fixed_total':
            settlement_price = self.fixed_total_price or Decimal('0')
        
        elif self.settlement_method == 'fixed_unit':
            if service_area and self.fixed_unit_price:
                settlement_price = Decimal(str(service_area)) * self.fixed_unit_price
        
        # 方式二：按实结算
        elif self.settlement_method == 'cumulative_commission':
            if saving_amount and self.cumulative_rate:
                settlement_price = Decimal(str(saving_amount)) * (self.cumulative_rate / 100)
        
        elif self.settlement_method == 'segmented_commission':
            if saving_amount:
                settlement_price = self._calculate_segmented_commission(saving_amount)
        
        elif self.settlement_method == 'jump_point_commission':
            if saving_amount:
                settlement_price = self._calculate_jump_point_commission(saving_amount)
        
        # 方式三：组合方式
        elif self.settlement_method == 'combined':
            # 固定部分
            fixed_part = Decimal('0')
            if self.combined_fixed_method == 'fixed_total':
                fixed_part = self.combined_fixed_total or Decimal('0')
            elif self.combined_fixed_method == 'fixed_unit':
                if service_area and self.combined_fixed_unit:
                    fixed_part = Decimal(str(service_area)) * self.combined_fixed_unit
            
            # 按实结算部分
            actual_part = Decimal('0')
            if saving_amount:
                if self.combined_actual_method == 'cumulative_commission':
                    if self.combined_cumulative_rate:
                        base_amount = saving_amount
                        if self.combined_deduct_fixed:
                            base_amount = max(Decimal('0'), saving_amount - fixed_part)
                        actual_part = base_amount * (self.combined_cumulative_rate / 100)
                
                elif self.combined_actual_method == 'segmented_commission':
                    base_amount = saving_amount
                    if self.combined_deduct_fixed:
                        base_amount = max(Decimal('0'), saving_amount - fixed_part)
                    actual_part = self._calculate_segmented_commission(base_amount)
                
                elif self.combined_actual_method == 'jump_point_commission':
                    base_amount = saving_amount
                    if self.combined_deduct_fixed:
                        base_amount = max(Decimal('0'), saving_amount - fixed_part)
                    actual_part = self._calculate_jump_point_commission(base_amount)
            
            settlement_price = fixed_part + actual_part
        
        # 应用封顶费和保底费
        final_fee = self._apply_cap_and_minimum(settlement_price, service_area, unit_cap_details)
        
        return final_fee
    
    def _calculate_segmented_commission(self, saving_amount):
        """计算分段递增提成"""
        from decimal import Decimal
        result = Decimal('0')
        saving = Decimal(str(saving_amount))
        
        # 获取分段配置，按阈值从小到大排序
        segments = self.segmented_rates.filter(is_active=True).order_by('threshold')
        
        previous_threshold = Decimal('0')
        for segment in segments:
            threshold = segment.threshold
            rate = segment.rate / 100  # 转换为小数
            
            if saving <= previous_threshold:
                break
            
            if saving <= threshold:
                # 当前分段
                segment_amount = saving - previous_threshold
                result += segment_amount * rate
                break
            else:
                # 完整分段
                segment_amount = threshold - previous_threshold
                result += segment_amount * rate
                previous_threshold = threshold
        
        # 处理最后一个分段（无上限）
        if segments.exists():
            last_segment = segments.last()
            if saving > last_segment.threshold:
                remaining = saving - last_segment.threshold
                result += remaining * (last_segment.rate / 100)
        
        return result
    
    def _calculate_jump_point_commission(self, saving_amount):
        """计算跳点提成"""
        from decimal import Decimal
        saving = Decimal(str(saving_amount))
        
        # 获取跳点配置，按阈值从小到大排序
        jump_points = self.jump_point_rates.filter(is_active=True).order_by('threshold')
        
        # 找到节省金额所属的阈值区间
        for jump_point in jump_points:
            if saving <= jump_point.threshold:
                # 使用该阈值对应的系数
                return saving * (jump_point.rate / 100)
        
        # 如果超过所有阈值，使用最后一个跳点的系数
        if jump_points.exists():
            last_jump = jump_points.last()
            return saving * (last_jump.rate / 100)
        
        return Decimal('0')
    
    def _apply_cap_and_minimum(self, settlement_price, service_area=None, unit_cap_details=None):
        """应用封顶费和保底费"""
        from decimal import Decimal
        
        result = settlement_price
        
        # 计算封顶费
        cap_fee = None
        if self.has_cap_fee:
            if self.cap_type == 'total_cap':
                cap_fee = self.total_cap_amount or Decimal('0')
            elif self.cap_type == 'unit_cap' and unit_cap_details:
                # 计算单价封顶：Σ（各单体优化面积 × 对应单体封顶单价）
                cap_fee = Decimal('0')
                for detail in unit_cap_details:
                    area = Decimal(str(detail.get('area', 0)))
                    cap_unit_price = Decimal(str(detail.get('cap_unit_price', 0)))
                    cap_fee += area * cap_unit_price
        
        # 应用保底费
        if self.has_minimum_fee and self.minimum_fee_amount:
            result = max(result, self.minimum_fee_amount)
        
        # 应用封顶费
        if cap_fee is not None:
            result = min(result, cap_fee)
        
        return result
    
    def get_segmented_rates_ordered(self):
        """获取排序后的分段递增提成配置"""
        return self.segmented_rates.filter(is_active=True).order_by('order', 'threshold')
    
    def get_jump_point_rates_ordered(self):
        """获取排序后的跳点提成配置"""
        return self.jump_point_rates.filter(is_active=True).order_by('order', 'threshold')
    
    def get_unit_cap_details_ordered(self):
        """获取排序后的单价封顶费明细"""
        return self.unit_cap_details.all().order_by('order', 'unit_name')
    
    def is_used(self):
        """检查方案是否被使用（关联了结算单）"""
        return self.project_settlements.exists()
    
    def get_usage_count(self):
        """获取方案使用次数"""
        return self.project_settlements.count()
    
    def can_delete(self):
        """检查方案是否可以删除"""
        return not self.is_used() and not self.is_default


class ServiceFeeSegmentedRate(models.Model):
    """分段递增提成配置"""
    scheme = models.ForeignKey(ServiceFeeSettlementScheme,
                               on_delete=models.CASCADE,
                               related_name='segmented_rates',
                               verbose_name='关联结算方案')
    threshold = models.DecimalField('分段阈值', max_digits=14, decimal_places=2,
                                    help_text='该分段的上限阈值，例如：500000 表示50万元')
    rate = models.DecimalField('取费系数(%)', max_digits=5, decimal_places=2,
                              help_text='该分段对应的取费系数，例如：10.5 表示 10.5%')
    description = models.TextField('分段说明', blank=True)
    order = models.IntegerField('排序', default=0, help_text='数字越小越靠前')
    is_active = models.BooleanField('是否启用', default=True)
    
    created_time = models.DateTimeField('创建时间', default=timezone.now)
    updated_time = models.DateTimeField('更新时间', auto_now=True)
    
    class Meta:
        db_table = 'settlement_service_fee_segmented_rate'
        verbose_name = '分段递增提成配置'
        verbose_name_plural = '分段递增提成配置'
        ordering = ['scheme', 'order', 'threshold']
        indexes = [
            models.Index(fields=['scheme', 'is_active', 'order']),
        ]
    
    def __str__(self):
        return f"{self.scheme.name} - 阈值: {self.threshold} - 系数: {self.rate}%"
    
    def clean(self):
        """模型验证"""
        from django.core.exceptions import ValidationError
        
        if self.threshold < 0:
            raise ValidationError({'threshold': '分段阈值不能为负数'})
        
        if self.rate < 0 or self.rate > 100:
            raise ValidationError({'rate': '取费系数必须在0-100之间'})
    
    def save(self, *args, **kwargs):
        """保存前进行验证"""
        self.full_clean()
        super().save(*args, **kwargs)


class ServiceFeeJumpPointRate(models.Model):
    """跳点提成配置"""
    scheme = models.ForeignKey(ServiceFeeSettlementScheme,
                              on_delete=models.CASCADE,
                              related_name='jump_point_rates',
                              verbose_name='关联结算方案')
    threshold = models.DecimalField('跳点阈值', max_digits=14, decimal_places=2,
                                   help_text='当节省金额超过此阈值时，全部节省金额适用该系数')
    rate = models.DecimalField('取费系数(%)', max_digits=5, decimal_places=2,
                              help_text='该阈值对应的取费系数，例如：15.0 表示 15%')
    description = models.TextField('跳点说明', blank=True)
    order = models.IntegerField('排序', default=0, help_text='数字越小越靠前')
    is_active = models.BooleanField('是否启用', default=True)
    
    created_time = models.DateTimeField('创建时间', default=timezone.now)
    updated_time = models.DateTimeField('更新时间', auto_now=True)
    
    class Meta:
        db_table = 'settlement_service_fee_jump_point_rate'
        verbose_name = '跳点提成配置'
        verbose_name_plural = '跳点提成配置'
        ordering = ['scheme', 'order', 'threshold']
        indexes = [
            models.Index(fields=['scheme', 'is_active', 'order']),
        ]
    
    def __str__(self):
        return f"{self.scheme.name} - 阈值: {self.threshold} - 系数: {self.rate}%"
    
    def clean(self):
        """模型验证"""
        from django.core.exceptions import ValidationError
        
        if self.threshold < 0:
            raise ValidationError({'threshold': '跳点阈值不能为负数'})
        
        if self.rate < 0 or self.rate > 100:
            raise ValidationError({'rate': '取费系数必须在0-100之间'})
    
    def save(self, *args, **kwargs):
        """保存前进行验证"""
        self.full_clean()
        super().save(*args, **kwargs)


class ServiceFeeUnitCapDetail(models.Model):
    """单价封顶费计算明细（各单体信息）"""
    scheme = models.ForeignKey(ServiceFeeSettlementScheme,
                              on_delete=models.CASCADE,
                              related_name='unit_cap_details',
                              verbose_name='关联结算方案')
    unit_name = models.CharField('单体名称', max_length=200,
                                help_text='单体名称，例如：1#楼、2#楼等')
    cap_unit_price = models.DecimalField('封顶单价', max_digits=12, decimal_places=2,
                                        help_text='该单体的封顶单价（元/平方米）')
    description = models.TextField('备注', blank=True)
    order = models.IntegerField('排序', default=0, help_text='数字越小越靠前')
    
    created_time = models.DateTimeField('创建时间', default=timezone.now)
    updated_time = models.DateTimeField('更新时间', auto_now=True)
    
    class Meta:
        db_table = 'settlement_service_fee_unit_cap_detail'
        verbose_name = '单价封顶费明细'
        verbose_name_plural = '单价封顶费明细'
        ordering = ['scheme', 'order', 'unit_name']
        indexes = [
            models.Index(fields=['scheme', 'order']),
        ]
    
    def __str__(self):
        return f"{self.scheme.name} - {self.unit_name} - 封顶单价: {self.cap_unit_price}元/㎡"
    
    def clean(self):
        """模型验证"""
        from django.core.exceptions import ValidationError
        
        if self.cap_unit_price < 0:
            raise ValidationError({'cap_unit_price': '封顶单价不能为负数'})
    
    def save(self, *args, **kwargs):
        """保存前进行验证"""
        self.full_clean()
        super().save(*args, **kwargs)


class SettlementMethod(models.Model):
    """结算方式配置"""
    SETTLEMENT_METHOD_CHOICES = [
        ('fixed_total', '总价包干'),
        ('fixed_unit', '单价包干'),
        ('segmented_commission', '分段递增提成'),
        ('segmented_commission_simple', '分段提成'),
        ('jump_point_commission', '跳点提成'),
        ('cumulative_commission', '累计提成'),
    ]
    
    name = models.CharField(max_length=100, verbose_name='结算方式名称')
    code = models.CharField(max_length=50, unique=True, verbose_name='结算方式代码', 
                           choices=SETTLEMENT_METHOD_CHOICES,
                           help_text='系统识别代码，不可重复')
    description = models.TextField(blank=True, verbose_name='描述说明')
    sort_order = models.IntegerField(default=0, verbose_name='排序顺序')
    is_active = models.BooleanField(default=True, verbose_name='是否启用')
    created_time = models.DateTimeField(default=timezone.now, verbose_name='创建时间')
    updated_time = models.DateTimeField(auto_now=True, verbose_name='更新时间')
    
    class Meta:
        db_table = 'settlement_settlement_method'
        verbose_name = '结算方式'
        verbose_name_plural = verbose_name
        ordering = ['sort_order', 'name']
        indexes = [
            models.Index(fields=['code']),
            models.Index(fields=['is_active', 'sort_order']),
        ]
    
    def __str__(self):
        return self.name
    
    def get_code_display(self):
        """获取代码对应的显示名称"""
        return dict(self.SETTLEMENT_METHOD_CHOICES).get(self.code, self.code)
