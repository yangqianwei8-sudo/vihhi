from django.db import models
from django.utils import timezone
from backend.apps.system_management.models import User

class Client(models.Model):
    """客户模型"""
    CLIENT_LEVELS = [
        ('vip', 'VIP客户'),
        ('important', '重要客户'),
        ('general', '一般客户'),
        ('potential', '潜在客户'),
    ]
    
    CREDIT_LEVELS = [
        ('excellent', '优秀'),
        ('good', '良好'),
        ('normal', '一般'),
        ('poor', '较差'),
        ('bad', '很差'),
    ]
    
    # 商机管理新增分级（战略客户/核心客户/潜力客户/常规客户/培育客户/观察客户）
    GRADE_CHOICES = [
        ('strategic', '战略客户'),
        ('core', '核心客户'),
        ('potential', '潜力客户'),
        ('regular', '常规客户'),
        ('nurturing', '培育客户'),
        ('observing', '观察客户'),
    ]
    
    CLIENT_TYPE_CHOICES = [
        ('developer', '开发商'),
        ('government', '政府单位'),
        ('design_institute', '设计院'),
        ('general_contractor', '总包单位'),
        ('other', '其他'),
    ]
    
    COMPANY_SCALE_CHOICES = [
        ('large', '大型'),
        ('medium', '中型'),
        ('small', '小型'),
    ]
    
    SOURCE_CHOICES = [
        ('self_development', '自主开发'),
        ('customer_referral', '老客户推荐'),
        ('industry_exhibition', '行业展会'),
        ('online_promotion', '网络推广'),
        ('other', '其他'),
    ]
    
    # 基础信息
    name = models.CharField(max_length=200, verbose_name='客户名称')
    short_name = models.CharField(max_length=100, blank=True, verbose_name='客户简称')
    code = models.CharField(max_length=50, unique=True, verbose_name='客户编码')
    unified_credit_code = models.CharField(max_length=50, blank=True, verbose_name='统一信用代码')
    
    # 分类信息
    client_level = models.CharField(max_length=20, choices=CLIENT_LEVELS, default='general', verbose_name='客户等级')
    grade = models.CharField(max_length=20, choices=GRADE_CHOICES, blank=True, null=True, verbose_name='客户分级', help_text='用于商机管理的客户分级')
    credit_level = models.CharField(max_length=20, choices=CREDIT_LEVELS, default='normal', verbose_name='信用等级')
    client_type = models.CharField(max_length=20, choices=CLIENT_TYPE_CHOICES, blank=True, verbose_name='客户类型')
    company_scale = models.CharField(max_length=20, choices=COMPANY_SCALE_CHOICES, blank=True, verbose_name='企业规模')
    industry = models.CharField(max_length=100, blank=True, verbose_name='所属行业')
    region = models.CharField(max_length=100, blank=True, verbose_name='所属区域')
    source = models.CharField(max_length=20, choices=SOURCE_CHOICES, blank=True, verbose_name='客户来源')
    
    # 评分信息（用于自动分级）
    score = models.IntegerField(default=0, verbose_name='客户评分', help_text='0-100分，用于自动计算客户分级')
    
    # 联系信息
    address = models.TextField(blank=True, verbose_name='地址')
    phone = models.CharField(max_length=20, blank=True, verbose_name='电话')
    email = models.CharField(max_length=100, blank=True, verbose_name='邮箱')
    website = models.CharField(max_length=200, blank=True, verbose_name='网站')
    
    # 财务信息
    total_contract_amount = models.DecimalField(max_digits=12, decimal_places=2, default=0, verbose_name='累计合同金额')
    total_payment_amount = models.DecimalField(max_digits=12, decimal_places=2, default=0, verbose_name='累计回款金额')
    
    # 状态信息
    is_active = models.BooleanField(default=True, verbose_name='是否活跃')
    health_score = models.IntegerField(default=0, verbose_name='健康度评分')
    description = models.TextField(blank=True, verbose_name='客户描述')
    
    # 审计字段
    created_by = models.ForeignKey(User, on_delete=models.PROTECT, verbose_name='创建人')
    created_time = models.DateTimeField(default=timezone.now, verbose_name='创建时间')
    updated_time = models.DateTimeField(auto_now=True, verbose_name='更新时间')
    
    class Meta:
        db_table = 'customer_client'
        verbose_name = '客户'
        verbose_name_plural = verbose_name
        ordering = ['-created_time']
    
    def __str__(self):
        return self.name
    
    def calculate_score(self):
        """计算客户评分（0-100分）"""
        from decimal import Decimal
        score = 0
        
        # 企业规模（0-30分）
        if self.company_scale == 'large':
            score += 30
        elif self.company_scale == 'medium':
            score += 15
        elif self.company_scale == 'small':
            score += 5
        
        # 合作历史（0-25分）- 从项目数量判断
        project_count = ClientProject.objects.filter(client=self).count()
        if project_count >= 5:
            score += 25
        elif project_count >= 3:
            score += 15
        elif project_count >= 1:
            score += 8
        
        # 项目规模（0-20分）- 从累计合同金额判断
        if self.total_contract_amount:
            amount = float(self.total_contract_amount)
            if amount >= 10000000:  # 1000万以上
                score += 20
            elif amount >= 5000000:  # 500万以上
                score += 12
            elif amount >= 1000000:  # 100万以上
                score += 6
        
        # 付款信誉（0-15分）- 从回款率判断
        if self.total_contract_amount and float(self.total_contract_amount) > 0:
            payment_rate = (float(self.total_payment_amount) / float(self.total_contract_amount)) * 100
            if payment_rate >= 95:
                score += 15
            elif payment_rate >= 80:
                score += 10
            elif payment_rate >= 60:
                score += 5
        
        # 战略价值（0-10分）- 根据客户类型和等级判断
        if self.client_type == 'government' or self.client_level == 'vip':
            score += 10
        elif self.client_level == 'important':
            score += 6
        elif self.client_level == 'general':
            score += 3
        
        return min(score, 100)  # 最高100分
    
    def calculate_grade(self):
        """根据评分自动计算客户分级"""
        score = self.calculate_score()
        if score >= 80:
            return 'strategic'  # 战略客户
        elif score >= 60:
            return 'core'  # 核心客户
        elif score >= 40:
            return 'potential'  # 潜力客户
        elif score >= 20:
            return 'regular'  # 常规客户
        elif score >= 10:
            return 'nurturing'  # 培育客户
        else:
            return 'observing'  # 观察客户
    
    def save(self, *args, **kwargs):
        # 自动计算评分和分级
        if not self.score or kwargs.get('update_score', False):
            self.score = self.calculate_score()
        if not self.grade or kwargs.get('update_grade', False):
            self.grade = self.calculate_grade()
        super().save(*args, **kwargs)

class ClientContact(models.Model):
    """客户联系人"""
    client = models.ForeignKey(Client, on_delete=models.CASCADE, related_name='contacts', verbose_name='客户')
    name = models.CharField(max_length=100, verbose_name='联系人姓名')
    position = models.CharField(max_length=100, blank=True, verbose_name='职位')
    department = models.CharField(max_length=100, blank=True, verbose_name='部门')
    phone = models.CharField(max_length=20, blank=True, verbose_name='手机')
    telephone = models.CharField(max_length=20, blank=True, verbose_name='电话')
    email = models.CharField(max_length=100, blank=True, verbose_name='邮箱')
    wechat = models.CharField(max_length=100, blank=True, verbose_name='微信')
    is_primary = models.BooleanField(default=False, verbose_name='是否主要联系人')
    notes = models.TextField(blank=True, verbose_name='备注')
    created_time = models.DateTimeField(default=timezone.now, verbose_name='创建时间')
    
    class Meta:
        db_table = 'customer_contact'
        verbose_name = '客户联系人'
        verbose_name_plural = verbose_name

class ClientProject(models.Model):
    """客户项目关联（统计用）"""
    client = models.ForeignKey(Client, on_delete=models.CASCADE, verbose_name='客户')
    project = models.ForeignKey('project_center.Project', on_delete=models.CASCADE, verbose_name='项目')
    service_type = models.CharField(max_length=50, verbose_name='服务类型')
    contract_amount = models.DecimalField(max_digits=12, decimal_places=2, verbose_name='合同金额')
    start_date = models.DateField(verbose_name='开始日期')
    end_date = models.DateField(verbose_name='结束日期')
    status = models.CharField(max_length=20, verbose_name='项目状态')
    created_time = models.DateTimeField(default=timezone.now, verbose_name='创建时间')
    
    class Meta:
        db_table = 'customer_client_project'
        verbose_name = '客户项目'
        verbose_name_plural = verbose_name


class BusinessContract(models.Model):
    """商务合同信息"""
    CONTRACT_TYPE_CHOICES = [
        ('framework', '框架合同'),
        ('project', '项目合同'),
        ('supplement', '补充协议'),
        ('change', '变更协议'),
        ('termination', '终止协议'),
        ('other', '其他'),
    ]
    
    CONTRACT_STATUS_CHOICES = [
        ('draft', '草稿'),
        ('pending_review', '待审核'),
        ('reviewing', '审核中'),
        ('signed', '已签订'),
        ('effective', '已生效'),
        ('executing', '执行中'),
        ('completed', '已完成'),
        ('terminated', '已终止'),
        ('cancelled', '已取消'),
    ]
    
    # 关联信息
    project = models.ForeignKey('project_center.Project', on_delete=models.CASCADE, related_name='contracts', null=True, blank=True, verbose_name='关联项目')
    client = models.ForeignKey(Client, on_delete=models.PROTECT, related_name='contracts', null=True, blank=True, verbose_name='客户')
    parent_contract = models.ForeignKey('self', on_delete=models.CASCADE, null=True, blank=True, related_name='sub_contracts', verbose_name='主合同', help_text='用于补充协议、变更协议关联主合同')
    
    # 基本信息
    contract_number = models.CharField(max_length=100, unique=True, blank=True, null=True, verbose_name='合同编号', help_text='唯一标识，留空将自动生成（格式：VIH-CON-YYYY-NNNN）')
    contract_name = models.CharField(max_length=200, blank=True, verbose_name='合同名称', help_text='如未填写，将使用合同编号')
    contract_type = models.CharField(max_length=20, choices=CONTRACT_TYPE_CHOICES, default='project', verbose_name='合同类型')
    status = models.CharField(max_length=20, choices=CONTRACT_STATUS_CHOICES, default='draft', verbose_name='合同状态')
    
    # 金额信息
    contract_amount = models.DecimalField(max_digits=12, decimal_places=2, null=True, blank=True, verbose_name='合同金额（含税）')
    contract_amount_tax = models.DecimalField(max_digits=12, decimal_places=2, null=True, blank=True, verbose_name='合同税额')
    contract_amount_excl_tax = models.DecimalField(max_digits=12, decimal_places=2, null=True, blank=True, verbose_name='合同金额（不含税）')
    tax_rate = models.DecimalField(max_digits=5, decimal_places=2, default=6.00, verbose_name='税率(%)', help_text='默认6%，可调整')
    settlement_amount = models.DecimalField(max_digits=12, decimal_places=2, default=0, verbose_name='已结算金额')
    payment_amount = models.DecimalField(max_digits=12, decimal_places=2, default=0, verbose_name='已回款金额')
    unpaid_amount = models.DecimalField(max_digits=12, decimal_places=2, null=True, blank=True, verbose_name='未回款金额', help_text='自动计算：合同金额-已回款金额')
    
    # 时间信息
    contract_date = models.DateField(null=True, blank=True, verbose_name='合同签订日期')
    effective_date = models.DateField(null=True, blank=True, verbose_name='合同生效日期')
    start_date = models.DateField(null=True, blank=True, verbose_name='合同开始日期')
    end_date = models.DateField(null=True, blank=True, verbose_name='合同结束日期')
    contract_period = models.IntegerField(null=True, blank=True, verbose_name='合同期限（天）', help_text='自动计算：结束日期-开始日期')
    
    # 双方信息
    party_a_name = models.CharField(max_length=200, blank=True, verbose_name='甲方名称')
    party_a_contact = models.CharField(max_length=100, blank=True, verbose_name='甲方联系人')
    party_b_name = models.CharField(max_length=200, blank=True, verbose_name='乙方名称', default='四川维海科技有限公司')
    party_b_contact = models.CharField(max_length=100, blank=True, verbose_name='乙方联系人')
    signed_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True, related_name='signed_contracts', verbose_name='合同签订人')
    approved_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True, related_name='approved_contracts', verbose_name='合同审批人')
    
    # 其他信息
    description = models.TextField(blank=True, verbose_name='合同描述')
    notes = models.TextField(blank=True, verbose_name='备注')
    is_active = models.BooleanField(default=True, verbose_name='是否启用')
    
    # 审计字段
    created_by = models.ForeignKey(User, on_delete=models.PROTECT, related_name='created_contracts', null=True, blank=True, verbose_name='创建人')
    created_time = models.DateTimeField(default=timezone.now, verbose_name='创建时间')
    updated_time = models.DateTimeField(auto_now=True, verbose_name='更新时间')

    class Meta:
        db_table = 'business_contract'
        verbose_name = '商务合同'
        verbose_name_plural = verbose_name
        ordering = ['-created_time']
        indexes = [
            models.Index(fields=['contract_number']),
            models.Index(fields=['status', 'contract_type']),
            models.Index(fields=['contract_date']),
        ]

    def __str__(self):
        contract_num = self.contract_number or '未生成编号'
        contract_name = self.contract_name or '未命名合同'
        return f"{contract_num} - {contract_name}"
    
    def save(self, *args, **kwargs):
        # 自动生成合同编号（如果没有提供）
        if not self.contract_number:
            from django.db.models import Max
            from datetime import datetime
            current_year = datetime.now().year
            # 查找当年最大的合同编号
            max_contract = BusinessContract.objects.filter(
                contract_number__startswith=f'VIH-CON-{current_year}-'
            ).aggregate(max_num=Max('contract_number'))['max_num']
            
            if max_contract:
                # 提取序号并加1
                try:
                    seq = int(max_contract.split('-')[-1]) + 1
                except (ValueError, IndexError):
                    seq = 1
            else:
                seq = 1
            
            self.contract_number = f'VIH-CON-{current_year}-{seq:04d}'
        
        # 如果没有合同名称，使用合同编号
        if not self.contract_name:
            self.contract_name = self.contract_number
        
        # 自动计算不含税金额和税额
        if self.contract_amount:
            tax_rate_decimal = (self.tax_rate or 0) / 100
            if tax_rate_decimal > 0:
                self.contract_amount_excl_tax = self.contract_amount / (1 + tax_rate_decimal)
                self.contract_amount_tax = self.contract_amount - self.contract_amount_excl_tax
            else:
                self.contract_amount_excl_tax = self.contract_amount
                self.contract_amount_tax = 0
        
        # 自动计算未回款金额
        if self.contract_amount:
            self.unpaid_amount = (self.contract_amount or 0) - (self.payment_amount or 0)
        
        # 自动计算合同期限
        if self.start_date and self.end_date:
            from datetime import timedelta
            self.contract_period = (self.end_date - self.start_date).days
        
        # 记录状态变更
        # 注意：ContractStatusLog 在文件后面定义，但 Python 允许在方法执行时引用
        if self.pk:  # 只记录已存在的合同的状态变更
            try:
                old_instance = BusinessContract.objects.get(pk=self.pk)
                if old_instance.status != self.status:
                    # 使用字符串引用避免循环导入问题
                    from django.apps import apps
                    ContractStatusLog = apps.get_model('customer_success', 'ContractStatusLog')
                    ContractStatusLog.objects.create(
                        contract=self,
                        from_status=old_instance.status,
                        to_status=self.status,
                        actor=getattr(self, '_status_change_actor', None),
                        comment=getattr(self, '_status_change_comment', ''),
                    )
            except (BusinessContract.DoesNotExist, Exception):
                # 忽略错误，避免状态记录失败影响合同保存
                import logging
                logger = logging.getLogger(__name__)
                logger.warning(f'记录合同状态变更失败: {self.id if self.pk else "新建"}')
                pass
        
        super().save(*args, **kwargs)
    
    @classmethod
    def get_valid_transitions(cls, current_status):
        """获取当前状态可以流转到的状态列表"""
        transitions = {
            'draft': ['pending_review', 'cancelled'],
            'pending_review': ['reviewing', 'draft', 'cancelled'],
            'reviewing': ['signed', 'pending_review', 'cancelled'],
            'signed': ['effective', 'cancelled'],
            'effective': ['executing', 'terminated'],
            'executing': ['completed', 'terminated', 'cancelled'],
            'completed': [],
            'terminated': [],
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
            raise ValueError(f"无法从 {self.get_status_display()} 流转到 {dict(self.CONTRACT_STATUS_CHOICES).get(target_status, target_status)}")
        
        old_status = self.status
        self.status = target_status
        self._status_change_actor = actor
        self._status_change_comment = comment
        self.save()
        
        return True


class BusinessPaymentPlan(models.Model):
    """商务合同回款计划"""
    STATUS_CHOICES = [
        ('pending', '待回款'),
        ('partial', '部分回款'),
        ('completed', '已完成'),
        ('overdue', '已逾期'),
        ('cancelled', '已取消'),
    ]

    contract = models.ForeignKey(BusinessContract, on_delete=models.CASCADE, related_name='payment_plans', verbose_name='合同')
    phase_name = models.CharField(max_length=100, verbose_name='回款阶段')
    phase_description = models.TextField(blank=True, verbose_name='阶段描述')
    planned_amount = models.DecimalField(max_digits=12, decimal_places=2, verbose_name='计划金额')
    planned_date = models.DateField(verbose_name='计划日期')
    actual_amount = models.DecimalField(max_digits=12, decimal_places=2, null=True, blank=True, verbose_name='实际金额')
    actual_date = models.DateField(null=True, blank=True, verbose_name='实际日期')
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='pending', verbose_name='状态')
    trigger_condition = models.CharField(max_length=100, blank=True, verbose_name='触发条件')
    condition_detail = models.CharField(max_length=200, blank=True, verbose_name='付款条件详情')
    notes = models.TextField(blank=True, verbose_name='备注')
    created_time = models.DateTimeField(default=timezone.now, verbose_name='创建时间')
    updated_time = models.DateTimeField(auto_now=True, verbose_name='更新时间')

    class Meta:
        db_table = 'business_payment_plan'
        verbose_name = '商务回款计划'
        verbose_name_plural = verbose_name
        ordering = ['planned_date']

    def __str__(self):
        return f"{self.contract_id} - {self.phase_name}"


class ContractFile(models.Model):
    """合同文件"""
    FILE_TYPE_CHOICES = [
        ('original', '合同原件'),
        ('scanned', '合同扫描件'),
        ('attachment', '合同附件'),
        ('supplement', '补充协议'),
        ('change', '变更协议'),
        ('termination', '终止协议'),
        ('other', '其他文件'),
    ]
    
    contract = models.ForeignKey(BusinessContract, on_delete=models.CASCADE, related_name='files', verbose_name='合同')
    file_type = models.CharField(max_length=20, choices=FILE_TYPE_CHOICES, default='scanned', verbose_name='文件类型')
    file_name = models.CharField(max_length=200, verbose_name='文件名称')
    file = models.FileField(upload_to='contracts/%Y/%m/', verbose_name='文件')
    file_size = models.IntegerField(null=True, blank=True, verbose_name='文件大小（字节）')
    version = models.CharField(max_length=20, default='1.0', verbose_name='版本号')
    description = models.TextField(blank=True, verbose_name='文件描述')
    uploaded_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True, related_name='uploaded_contract_files', verbose_name='上传人')
    uploaded_time = models.DateTimeField(default=timezone.now, verbose_name='上传时间')
    
    class Meta:
        db_table = 'business_contract_file'
        verbose_name = '合同文件'
        verbose_name_plural = verbose_name
        ordering = ['-uploaded_time']
    
    def __str__(self):
        return f"{self.contract.contract_number} - {self.file_name}"


class ContractApproval(models.Model):
    """合同审核记录"""
    APPROVAL_RESULT_CHOICES = [
        ('approved', '通过'),
        ('rejected', '驳回'),
        ('pending', '待审核'),
    ]
    
    contract = models.ForeignKey(BusinessContract, on_delete=models.CASCADE, related_name='approvals', verbose_name='合同')
    approver = models.ForeignKey(User, on_delete=models.PROTECT, related_name='contract_approvals', verbose_name='审核人')
    approval_level = models.IntegerField(default=1, verbose_name='审核层级', help_text='1=商务经理, 2=部门经理, 3=总经理')
    result = models.CharField(max_length=20, choices=APPROVAL_RESULT_CHOICES, default='pending', verbose_name='审核结果')
    comment = models.TextField(blank=True, verbose_name='审核意见')
    approval_time = models.DateTimeField(null=True, blank=True, verbose_name='审核时间')
    created_time = models.DateTimeField(default=timezone.now, verbose_name='创建时间')
    
    class Meta:
        db_table = 'business_contract_approval'
        verbose_name = '合同审核记录'
        verbose_name_plural = verbose_name
        ordering = ['approval_level', '-created_time']
    
    def __str__(self):
        return f"{self.contract.contract_number} - {self.approver.username} - {self.get_result_display()}"


class ContractChange(models.Model):
    """合同变更记录"""
    CHANGE_TYPE_CHOICES = [
        ('amount', '金额变更'),
        ('period', '期限变更'),
        ('terms', '条款变更'),
        ('party', '双方变更'),
        ('other', '其他变更'),
    ]
    
    contract = models.ForeignKey(BusinessContract, on_delete=models.CASCADE, related_name='changes', verbose_name='合同')
    change_type = models.CharField(max_length=20, choices=CHANGE_TYPE_CHOICES, verbose_name='变更类型')
    change_reason = models.TextField(verbose_name='变更原因')
    before_content = models.TextField(blank=True, verbose_name='变更前内容')
    after_content = models.TextField(verbose_name='变更后内容')
    change_amount = models.DecimalField(max_digits=12, decimal_places=2, null=True, blank=True, verbose_name='变更金额', help_text='金额变更时填写')
    change_date = models.DateField(default=timezone.now, verbose_name='变更日期')
    approved_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True, related_name='approved_contract_changes', verbose_name='审批人')
    notes = models.TextField(blank=True, verbose_name='备注')
    created_by = models.ForeignKey(User, on_delete=models.PROTECT, related_name='created_contract_changes', verbose_name='创建人')
    created_time = models.DateTimeField(default=timezone.now, verbose_name='创建时间')
    
    class Meta:
        db_table = 'business_contract_change'
        verbose_name = '合同变更记录'
        verbose_name_plural = verbose_name
        ordering = ['-created_time']
    
    def __str__(self):
        return f"{self.contract.contract_number} - {self.get_change_type_display()} - {self.change_date}"


class ContractStatusLog(models.Model):
    """合同状态流转日志"""
    contract = models.ForeignKey(BusinessContract, on_delete=models.CASCADE, related_name='status_logs', verbose_name='合同')
    from_status = models.CharField(max_length=20, choices=BusinessContract.CONTRACT_STATUS_CHOICES, blank=True, verbose_name='原状态')
    to_status = models.CharField(max_length=20, choices=BusinessContract.CONTRACT_STATUS_CHOICES, verbose_name='目标状态')
    actor = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True, related_name='contract_status_actions', verbose_name='操作人')
    comment = models.TextField(blank=True, verbose_name='备注说明')
    created_time = models.DateTimeField(default=timezone.now, verbose_name='操作时间')
    
    class Meta:
        db_table = 'business_contract_status_log'
        verbose_name = '合同状态流转日志'
        verbose_name_plural = verbose_name
        ordering = ['-created_time']
    
    def __str__(self):
        from_label = dict(BusinessContract.CONTRACT_STATUS_CHOICES).get(self.from_status, '未知')
        to_label = dict(BusinessContract.CONTRACT_STATUS_CHOICES).get(self.to_status, '未知')
        return f"{self.contract.contract_number} - {from_label} → {to_label}"


# ==================== 商机管理模块 ====================

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
    
    APPROVAL_STATUS_CHOICES = [
        ('pending', '待审批'),
        ('approved', '已审批'),
        ('rejected', '已驳回'),
    ]
    
    # 基本信息
    opportunity_number = models.CharField(max_length=50, unique=True, blank=True, null=True, verbose_name='商机编号', help_text='自动生成：OPP-YYYY-NNNN')
    name = models.CharField(max_length=200, verbose_name='商机名称')
    client = models.ForeignKey(Client, on_delete=models.PROTECT, related_name='opportunities', verbose_name='关联客户')
    business_manager = models.ForeignKey(User, on_delete=models.PROTECT, related_name='managed_opportunities', verbose_name='负责商务')
    
    # 项目信息
    project_name = models.CharField(max_length=200, blank=True, verbose_name='项目名称')
    project_address = models.CharField(max_length=500, blank=True, verbose_name='项目地址')
    project_type = models.CharField(max_length=50, blank=True, verbose_name='项目业态', help_text='住宅/综合体/商业/写字楼等')
    building_area = models.DecimalField(max_digits=15, decimal_places=2, null=True, blank=True, verbose_name='建筑面积（平方米）')
    drawing_stage = models.CharField(max_length=50, blank=True, verbose_name='图纸阶段')
    
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
        # 自动生成商机编号
        if not self.opportunity_number:
            from django.db.models import Max
            from datetime import datetime
            current_year = datetime.now().year
            max_opp = BusinessOpportunity.objects.filter(
                opportunity_number__startswith=f'OPP-{current_year}-'
            ).aggregate(max_num=Max('opportunity_number'))['max_num']
            
            if max_opp:
                try:
                    seq = int(max_opp.split('-')[-1]) + 1
                except (ValueError, IndexError):
                    seq = 1
            else:
                seq = 1
            
            self.opportunity_number = f'OPP-{current_year}-{seq:04d}'
        
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
        
        # 跟进及时性（25%）
        # 这里简化处理，实际应该根据最近跟进时间计算
        score += 25
        
        # 信息完整性（20%）
        if self.project_name and self.project_address and self.estimated_amount:
            score += 20
        elif self.project_name or self.project_address:
            score += 10
        
        # 客户互动频次（20%）
        followup_count = self.followups.count() if hasattr(self, 'followups') else 0
        if followup_count >= 5:
            score += 20
        elif followup_count >= 3:
            score += 12
        elif followup_count >= 1:
            score += 6
        
        # 阶段推进速度（35%）
        # 根据状态和创建时间计算
        days_since_created = (timezone.now().date() - self.created_time.date()).days
        if self.status == 'won':
            score += 35
        elif self.status == 'negotiation' and days_since_created <= 30:
            score += 30
        elif self.status == 'quotation' and days_since_created <= 20:
            score += 25
        elif self.status == 'requirement_confirmed' and days_since_created <= 15:
            score += 20
        else:
            score += 10
        
        return min(score, 100)
    
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
    
    opportunity = models.ForeignKey(BusinessOpportunity, on_delete=models.CASCADE, related_name='quotations', verbose_name='商机')
    version_type = models.CharField(max_length=20, choices=VERSION_TYPE_CHOICES, default='draft', verbose_name='版本类型')
    version_number = models.IntegerField(default=1, verbose_name='版本号')
    
    # 报价参数
    building_area = models.DecimalField(max_digits=15, decimal_places=2, null=True, blank=True, verbose_name='建筑面积（平方米）')
    project_type = models.CharField(max_length=50, blank=True, verbose_name='项目业态')
    service_type = models.CharField(max_length=50, blank=True, verbose_name='服务类型')
    structure_type = models.CharField(max_length=50, blank=True, verbose_name='结构形式')
    
    # 报价结果
    base_quotation = models.DecimalField(max_digits=15, decimal_places=2, default=0, verbose_name='基准报价（万元）')
    adjustment_factor = models.DecimalField(max_digits=5, decimal_places=2, default=1.0, verbose_name='调整系数')
    final_quotation = models.DecimalField(max_digits=15, decimal_places=2, default=0, verbose_name='最终报价（万元）')
    quotation_note = models.TextField(blank=True, verbose_name='报价说明')
    
    # 使用的规则
    quotation_rule = models.ForeignKey(QuotationRule, on_delete=models.SET_NULL, null=True, blank=True, verbose_name='使用的报价规则')
    
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
        # 自动计算最终报价
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
