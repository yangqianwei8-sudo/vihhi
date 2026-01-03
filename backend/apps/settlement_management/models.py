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
        db_table = 'settlement_management_output_value_stage'
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
        db_table = 'settlement_management_output_value_milestone'
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
        db_table = 'settlement_management_output_value_event'
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
    responsible_user = models.ForeignKey(User, on_delete=models.PROTECT, related_name='output_value_records_management',
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
                                    related_name='confirmed_output_values_management', verbose_name='确认人')
    notes = models.TextField(blank=True, verbose_name='备注')
    created_time = models.DateTimeField(default=timezone.now, verbose_name='创建时间')
    
    class Meta:
        db_table = 'settlement_management_output_value_record'
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
                                related_name='service_fee_rates_management', verbose_name='关联合同',
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
    
    created_by = models.ForeignKey(User, on_delete=models.PROTECT, related_name='created_service_fee_rates_management',
                                  verbose_name='创建人')
    created_time = models.DateTimeField(default=timezone.now, verbose_name='创建时间')
    updated_time = models.DateTimeField(auto_now=True, verbose_name='更新时间')
    
    class Meta:
        db_table = 'settlement_management_service_fee_rate'
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
                                   related_name='reviewed_settlement_items_management', verbose_name='审核造价工程师')
    reviewed_time = models.DateTimeField(null=True, blank=True, verbose_name='审核时间')
    review_comment = models.TextField(blank=True, verbose_name='审核意见')
    rejection_reason = models.TextField(blank=True, verbose_name='驳回原因')
    
    # 排序
    order = models.IntegerField(default=0, verbose_name='排序')
    
    created_by = models.ForeignKey(User, on_delete=models.PROTECT, related_name='created_settlement_items_management',
                                  verbose_name='创建人')
    created_time = models.DateTimeField(default=timezone.now, verbose_name='创建时间')
    updated_time = models.DateTimeField(auto_now=True, verbose_name='更新时间')
    
    class Meta:
        db_table = 'settlement_management_settlement_item'
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
                               related_name='settlements', verbose_name='关联项目',
                               help_text='仅显示状态为"已完工"的项目')
    contract = models.ForeignKey('production_management.BusinessContract', on_delete=models.SET_NULL,
                                null=True, blank=True, related_name='project_settlements_management',
                                verbose_name='关联合同')
    
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
                                    related_name='submitted_settlements_management', verbose_name='提交人')
    submitted_time = models.DateTimeField(null=True, blank=True, verbose_name='提交时间')
    
    # 甲方初审信息
    client_reviewer = models.CharField(max_length=100, blank=True, verbose_name='甲方初审人')
    client_reviewed_time = models.DateTimeField(null=True, blank=True, verbose_name='甲方初审时间')
    client_review_comment = models.TextField(blank=True, verbose_name='甲方初审意见')
    client_feedback_comment = models.TextField(blank=True, verbose_name='甲方反馈意见')
    client_feedback_time = models.DateTimeField(null=True, blank=True, verbose_name='甲方反馈时间')
    
    # 对账信息
    reconciliation_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True,
                                         related_name='reconciled_settlements_management', verbose_name='对账人')
    reconciliation_time = models.DateTimeField(null=True, blank=True, verbose_name='对账时间')
    reconciliation_comment = models.TextField(blank=True, verbose_name='对账说明')
    
    # 确认信息
    confirmed_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True,
                                    related_name='confirmed_settlements_management', verbose_name='确认人')
    confirmed_time = models.DateTimeField(null=True, blank=True, verbose_name='确认时间')
    
    # 附件和备注
    settlement_file = models.FileField(upload_to='settlements/%Y/%m/', null=True, blank=True,
                                      verbose_name='结算文件')
    description = models.TextField(blank=True, verbose_name='结算说明')
    notes = models.TextField(blank=True, verbose_name='备注')
    
    created_by = models.ForeignKey(User, on_delete=models.PROTECT, related_name='created_settlements_management',
                                  verbose_name='创建人')
    created_time = models.DateTimeField(default=timezone.now, verbose_name='创建时间')
    updated_time = models.DateTimeField(auto_now=True, verbose_name='更新时间')
    
    class Meta:
        db_table = 'settlement_management_project_settlement'
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
            
            # 如果有关联合同，从合同费率表匹配服务费率
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
                                related_name='contract_settlements_management', verbose_name='关联合同')
    
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
                                    related_name='submitted_contract_settlements_management', verbose_name='提交人')
    submitted_time = models.DateTimeField(null=True, blank=True, verbose_name='提交时间')
    
    # 审核信息
    approver = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True,
                                related_name='approved_contract_settlements_management', verbose_name='审核人')
    approved_time = models.DateTimeField(null=True, blank=True, verbose_name='审核时间')
    review_comment = models.TextField(blank=True, verbose_name='审核意见')
    
    # 确认信息
    confirmed_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True,
                                    related_name='confirmed_contract_settlements_management', verbose_name='确认人')
    confirmed_time = models.DateTimeField(null=True, blank=True, verbose_name='确认时间')
    
    # 附件和备注
    settlement_file = models.FileField(upload_to='contract_settlements/%Y/%m/', null=True, blank=True,
                                      verbose_name='结算文件')
    invoice_number = models.CharField(max_length=100, blank=True, verbose_name='发票号码')
    description = models.TextField(blank=True, verbose_name='结算说明')
    notes = models.TextField(blank=True, verbose_name='备注')
    
    created_by = models.ForeignKey(User, on_delete=models.PROTECT, related_name='created_contract_settlements_management',
                                  verbose_name='创建人')
    created_time = models.DateTimeField(default=timezone.now, verbose_name='创建时间')
    updated_time = models.DateTimeField(auto_now=True, verbose_name='更新时间')
    
    class Meta:
        db_table = 'settlement_management_contract_settlement'
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
    confirmed_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True, related_name='confirmed_payments_management', verbose_name='确认人')
    confirmed_time = models.DateTimeField(null=True, blank=True, verbose_name='确认时间')
    
    # 备注
    notes = models.TextField(blank=True, verbose_name='备注')
    created_by = models.ForeignKey(User, on_delete=models.PROTECT, related_name='created_payments_management', verbose_name='创建人')
    created_time = models.DateTimeField(default=timezone.now, verbose_name='创建时间')
    
    class Meta:
        db_table = 'settlement_management_payment_record'
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
            from backend.apps.production_management.models import PaymentPlan
            try:
                return PaymentPlan.objects.get(id=self.payment_plan_id)
            except PaymentPlan.DoesNotExist:
                return None
        elif self.payment_plan_type == 'business':
            from backend.apps.production_management.models import BusinessPaymentPlan
            try:
                return BusinessPaymentPlan.objects.get(id=self.payment_plan_id)
            except BusinessPaymentPlan.DoesNotExist:
                return None
        return None
