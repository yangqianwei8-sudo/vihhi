"""
诉讼管理模块数据模型
"""
from django.db import models
from django.utils import timezone
from django.core.validators import MinValueValidator, MaxValueValidator
from django.core.exceptions import ValidationError
import os

from backend.apps.system_management.models import User, Department
from backend.apps.production_management.models import Project
from backend.apps.customer_management.models import Client
from backend.apps.production_management.models import BusinessContract


def litigation_document_upload_path(instance, filename):
    """诉讼文档上传路径"""
    date_path = timezone.now().strftime('%Y/%m/%d')
    if hasattr(instance, 'case'):
        return f'litigation_documents/{date_path}/{instance.case.case_number}/{filename}'
    return f'litigation_documents/{date_path}/{filename}'


class LitigationCase(models.Model):
    """诉讼案件模型"""
    
    CASE_TYPE_CHOICES = [
        ('contract_dispute', '合同纠纷'),
        ('labor_dispute', '劳动争议'),
        ('ip_dispute', '知识产权'),
        ('tort_dispute', '侵权纠纷'),
        ('other', '其他纠纷'),
    ]
    
    CASE_NATURE_CHOICES = [
        ('plaintiff', '原告'),
        ('defendant', '被告'),
        ('third_party', '第三人'),
        ('other', '其他'),
    ]
    
    STATUS_CHOICES = [
        ('pending_filing', '待立案'),
        ('filed', '已立案'),
        ('trial', '审理中'),
        ('judged', '已判决'),
        ('executing', '执行中'),
        ('closed', '已结案'),
        ('withdrawn', '已撤诉'),
        ('settled', '已和解'),
    ]
    
    PRIORITY_CHOICES = [
        ('low', '低'),
        ('medium', '中'),
        ('high', '高'),
        ('urgent', '紧急'),
    ]
    
    # 基本信息
    case_number = models.CharField('案件编号', max_length=50, unique=True, db_index=True)
    case_name = models.CharField('案件名称', max_length=200)
    case_type = models.CharField('案件类型', max_length=20, choices=CASE_TYPE_CHOICES)
    case_nature = models.CharField('案件性质', max_length=20, choices=CASE_NATURE_CHOICES)
    description = models.TextField('案件描述', blank=True)
    
    # 关联信息
    project = models.ForeignKey(
        Project,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='litigation_cases',
        verbose_name='关联项目'
    )
    client = models.ForeignKey(
        Client,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='litigation_cases',
        verbose_name='关联客户'
    )
    contract = models.ForeignKey(
        BusinessContract,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='litigation_cases',
        verbose_name='关联合同'
    )
    
    # 金额信息
    litigation_amount = models.DecimalField(
        '诉讼标的额',
        max_digits=15,
        decimal_places=2,
        null=True,
        blank=True,
        help_text='诉讼请求的金额'
    )
    dispute_amount = models.DecimalField(
        '争议金额',
        max_digits=15,
        decimal_places=2,
        null=True,
        blank=True,
        help_text='实际争议的金额'
    )
    
    # 状态信息
    status = models.CharField('案件状态', max_length=20, choices=STATUS_CHOICES, default='pending_filing')
    priority = models.CharField('优先级', max_length=10, choices=PRIORITY_CHOICES, default='medium')
    
    # 时间信息
    registration_date = models.DateField('登记日期', default=timezone.now)
    filing_date = models.DateField('立案日期', null=True, blank=True)
    trial_date = models.DateField('开庭日期', null=True, blank=True)
    judgment_date = models.DateField('判决日期', null=True, blank=True)
    execution_date = models.DateField('执行日期', null=True, blank=True)
    closing_date = models.DateField('结案日期', null=True, blank=True)
    
    # 登记信息
    registered_by = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        null=True,
        related_name='registered_litigation_cases',
        verbose_name='登记人'
    )
    registered_department = models.ForeignKey(
        Department,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='litigation_cases',
        verbose_name='登记部门'
    )
    
    # 案件负责人
    case_manager = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='managed_litigation_cases',
        verbose_name='案件负责人'
    )
    
    # 时间戳
    created_at = models.DateTimeField('创建时间', auto_now_add=True)
    updated_at = models.DateTimeField('更新时间', auto_now=True)
    
    class Meta:
        db_table = 'litigation_case'
        verbose_name = '诉讼案件'
        verbose_name_plural = verbose_name
        ordering = ['-registration_date', '-created_at']
        indexes = [
            models.Index(fields=['case_number']),
            models.Index(fields=['status']),
            models.Index(fields=['case_type']),
            models.Index(fields=['priority']),
            models.Index(fields=['registration_date']),
        ]
    
    def __str__(self):
        return f"{self.case_number} - {self.case_name}"
    
    def get_absolute_url(self):
        """获取案件详情页URL"""
        from django.urls import reverse
        return reverse('litigation_pages:case_detail', args=[self.id])
    
    def clean(self):
        """数据验证"""
        super().clean()
        
        # 验证日期逻辑
        if self.filing_date and self.registration_date:
            if self.filing_date < self.registration_date:
                raise ValidationError({'filing_date': '立案日期不能早于登记日期'})
        
        if self.trial_date and self.filing_date:
            if self.trial_date < self.filing_date:
                raise ValidationError({'trial_date': '开庭日期不能早于立案日期'})
        
        if self.judgment_date and self.trial_date:
            if self.judgment_date < self.trial_date:
                raise ValidationError({'judgment_date': '判决日期不能早于开庭日期'})
        
        if self.closing_date:
            if self.registration_date and self.closing_date < self.registration_date:
                raise ValidationError({'closing_date': '结案日期不能早于登记日期'})
        
        # 验证金额
        if self.litigation_amount and self.litigation_amount < 0:
            raise ValidationError({'litigation_amount': '诉讼标的额不能为负数'})
        
        if self.dispute_amount and self.dispute_amount < 0:
            raise ValidationError({'dispute_amount': '争议金额不能为负数'})
    
    def save(self, *args, **kwargs):
        self.full_clean()  # 调用clean方法进行验证
        if not self.case_number:
            self.case_number = self._generate_case_number()
        super().save(*args, **kwargs)
    
    def _generate_case_number(self):
        """生成案件编号：LAW-YYYYMMDD-序列号"""
        from django.db.models import Max
        today = timezone.now().date()
        date_str = today.strftime('%Y%m%d')
        
        # 获取今天的最大序列号
        max_number = LitigationCase.objects.filter(
            case_number__startswith=f'LAW-{date_str}-'
        ).aggregate(Max('case_number'))['case_number__max']
        
        if max_number:
            sequence = int(max_number.split('-')[-1]) + 1
        else:
            sequence = 1
        
        return f'LAW-{date_str}-{sequence:04d}'


class LitigationProcess(models.Model):
    """诉讼流程模型"""
    
    PROCESS_TYPE_CHOICES = [
        ('filing', '立案'),
        ('trial', '庭审'),
        ('judgment', '判决'),
        ('execution', '执行'),
    ]
    
    STATUS_CHOICES = [
        ('pending', '待处理'),
        ('in_progress', '进行中'),
        ('completed', '已完成'),
        ('cancelled', '已取消'),
    ]
    
    case = models.ForeignKey(
        LitigationCase,
        on_delete=models.CASCADE,
        related_name='processes',
        verbose_name='关联案件'
    )
    process_type = models.CharField('流程类型', max_length=20, choices=PROCESS_TYPE_CHOICES)
    process_date = models.DateField('流程日期')
    status = models.CharField('流程状态', max_length=20, choices=STATUS_CHOICES, default='pending')
    
    # 立案信息
    filing_number = models.CharField('立案号', max_length=100, blank=True)
    court_name = models.CharField('法院名称', max_length=200, blank=True)
    court_address = models.TextField('法院地址', blank=True)
    court_contact = models.CharField('法院联系方式', max_length=100, blank=True)
    judge_name = models.CharField('法官姓名', max_length=100, blank=True)
    
    # 庭审信息
    trial_location = models.CharField('庭审地点', max_length=200, blank=True)
    trial_participants = models.TextField('庭审人员', blank=True)
    trial_result = models.TextField('庭审结果', blank=True)
    trial_notes = models.TextField('庭审记录', blank=True)
    
    # 判决信息
    judgment_number = models.CharField('判决书编号', max_length=100, blank=True)
    judgment_content = models.TextField('判决内容', blank=True)
    judgment_amount = models.DecimalField(
        '判决金额',
        max_digits=15,
        decimal_places=2,
        null=True,
        blank=True
    )
    execution_amount = models.DecimalField(
        '执行金额',
        max_digits=15,
        decimal_places=2,
        null=True,
        blank=True
    )
    interest_amount = models.DecimalField(
        '利息金额',
        max_digits=15,
        decimal_places=2,
        null=True,
        blank=True
    )
    execution_deadline = models.DateField('执行期限', null=True, blank=True)
    
    # 执行信息
    execution_status = models.CharField('执行状态', max_length=50, blank=True)
    execution_result = models.TextField('执行结果', blank=True)
    
    # 备注
    notes = models.TextField('备注', blank=True)
    
    # 时间戳
    created_at = models.DateTimeField('创建时间', auto_now_add=True)
    updated_at = models.DateTimeField('更新时间', auto_now=True)
    created_by = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        null=True,
        related_name='created_litigation_processes',
        verbose_name='创建人'
    )
    
    class Meta:
        db_table = 'litigation_process'
        verbose_name = '诉讼流程'
        verbose_name_plural = verbose_name
        ordering = ['-process_date', '-created_at']
    
    def __str__(self):
        return f"{self.case.case_number} - {self.get_process_type_display()}"
    
    def get_absolute_url(self):
        """获取流程详情页URL"""
        from django.urls import reverse
        return reverse('litigation_pages:process_detail', args=[self.id])


class LitigationDocument(models.Model):
    """诉讼文档模型"""
    
    DOCUMENT_TYPE_CHOICES = [
        ('complaint', '起诉状'),
        ('defense', '答辩状'),
        ('evidence', '证据材料'),
        ('legal_document', '法律文书'),
        ('other', '其他文档'),
    ]
    
    case = models.ForeignKey(
        LitigationCase,
        on_delete=models.CASCADE,
        related_name='documents',
        verbose_name='关联案件'
    )
    process = models.ForeignKey(
        LitigationProcess,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='documents',
        verbose_name='关联流程'
    )
    document_name = models.CharField('文档名称', max_length=200)
    document_type = models.CharField('文档类型', max_length=20, choices=DOCUMENT_TYPE_CHOICES)
    document_file = models.FileField('文档文件', upload_to=litigation_document_upload_path)
    file_size = models.BigIntegerField('文件大小（字节）', null=True, blank=True)
    
    # 版本管理
    version = models.CharField('版本号', max_length=20, default='1.0')
    is_latest = models.BooleanField('是否最新版本', default=True)
    
    # 备注
    description = models.TextField('文档描述', blank=True)
    
    # 时间戳
    uploaded_at = models.DateTimeField('上传时间', auto_now_add=True)
    uploaded_by = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        null=True,
        related_name='uploaded_litigation_documents',
        verbose_name='上传人'
    )
    
    class Meta:
        db_table = 'litigation_document'
        verbose_name = '诉讼文档'
        verbose_name_plural = verbose_name
        ordering = ['-uploaded_at']
    
    def clean(self):
        """数据验证"""
        super().clean()
        
        # 验证文档类型和文件扩展名的匹配
        if self.document_file:
            file_ext = os.path.splitext(self.document_file.name)[1].lower()
            allowed_extensions = {
                'contract': ['.pdf', '.doc', '.docx'],
                'evidence': ['.pdf', '.jpg', '.jpeg', '.png', '.doc', '.docx'],
                'judgment': ['.pdf', '.doc', '.docx'],
                'application': ['.pdf', '.doc', '.docx'],
                'other': ['.pdf', '.doc', '.docx', '.xls', '.xlsx', '.jpg', '.jpeg', '.png'],
            }
            
            allowed = allowed_extensions.get(self.document_type, allowed_extensions['other'])
            if file_ext not in allowed:
                raise ValidationError({
                    'document_file': f'文档类型为{self.get_document_type_display()}时，文件扩展名必须是: {", ".join(allowed)}'
                })
    
    def __str__(self):
        return f"{self.case.case_number} - {self.document_name}"
    
    def get_absolute_url(self):
        """获取文档详情页URL"""
        from django.urls import reverse
        return reverse('litigation_pages:document_detail', args=[self.id])
    
    def save(self, *args, **kwargs):
        self.full_clean()  # 调用clean方法进行验证
        if self.document_file and not self.file_size:
            self.file_size = self.document_file.size
        super().save(*args, **kwargs)


class LitigationExpense(models.Model):
    """诉讼费用模型"""
    
    EXPENSE_TYPE_CHOICES = [
        ('litigation_fee', '诉讼费'),
        ('lawyer_fee', '律师费'),
        ('appraisal_fee', '鉴定费'),
        ('travel_fee', '差旅费'),
        ('other', '其他费用'),
    ]
    
    PAYMENT_METHOD_CHOICES = [
        ('cash', '现金'),
        ('transfer', '转账'),
        ('check', '支票'),
        ('other', '其他'),
    ]
    
    PAYMENT_STATUS_CHOICES = [
        ('pending', '待支付'),
        ('paid', '已支付'),
        ('reimbursed', '已报销'),
        ('written_off', '已核销'),
    ]
    
    case = models.ForeignKey(
        LitigationCase,
        on_delete=models.CASCADE,
        related_name='expenses',
        verbose_name='关联案件'
    )
    project = models.ForeignKey(
        Project,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='litigation_expenses',
        verbose_name='关联项目'
    )
    expense_name = models.CharField('费用名称', max_length=200)
    expense_type = models.CharField('费用类型', max_length=20, choices=EXPENSE_TYPE_CHOICES)
    amount = models.DecimalField('费用金额', max_digits=12, decimal_places=2)
    expense_date = models.DateField('费用日期', default=timezone.now)
    description = models.TextField('费用说明', blank=True)
    
    # 支付信息
    payment_method = models.CharField('支付方式', max_length=20, choices=PAYMENT_METHOD_CHOICES, blank=True)
    payment_status = models.CharField('支付状态', max_length=20, choices=PAYMENT_STATUS_CHOICES, default='pending')
    invoice_file = models.FileField('发票文件', upload_to='litigation_invoices/%Y/%m/%d/', blank=True)
    
    # 报销信息
    REIMBURSEMENT_STATUS_CHOICES = [
        ('pending', '待审批'),
        ('approved', '已通过'),
        ('rejected', '已驳回'),
    ]
    
    reimbursement_applied = models.BooleanField('已申请报销', default=False)
    reimbursement_status = models.CharField('报销状态', max_length=20, choices=REIMBURSEMENT_STATUS_CHOICES, blank=True)
    
    # 时间戳
    created_at = models.DateTimeField('创建时间', auto_now_add=True)
    updated_at = models.DateTimeField('更新时间', auto_now=True)
    created_by = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        null=True,
        related_name='created_litigation_expenses',
        verbose_name='创建人'
    )
    
    class Meta:
        db_table = 'litigation_expense'
        verbose_name = '诉讼费用'
        verbose_name_plural = verbose_name
        ordering = ['-expense_date', '-created_at']
    
    def clean(self):
        """数据验证"""
        super().clean()
        
        # 验证金额
        if self.amount and self.amount < 0:
            raise ValidationError({'amount': '费用金额不能为负数'})
        
        # 验证日期
        if self.expense_date and self.case:
            if self.case.registration_date and self.expense_date < self.case.registration_date:
                raise ValidationError({'expense_date': '费用日期不能早于案件登记日期'})
    
    def save(self, *args, **kwargs):
        self.full_clean()  # 调用clean方法进行验证
        super().save(*args, **kwargs)
    
    def __str__(self):
        return f"{self.case.case_number} - {self.expense_name} - ¥{self.amount}"
    
    def get_absolute_url(self):
        """获取费用详情页URL"""
        from django.urls import reverse
        return reverse('litigation_pages:expense_detail', args=[self.id])


class LitigationPerson(models.Model):
    """诉讼人员模型"""
    
    PERSON_TYPE_CHOICES = [
        ('lawyer', '律师'),
        ('judge', '法官'),
        ('party', '当事人'),
    ]
    
    case = models.ForeignKey(
        LitigationCase,
        on_delete=models.CASCADE,
        related_name='persons',
        verbose_name='关联案件'
    )
    person_type = models.CharField('人员类型', max_length=20, choices=PERSON_TYPE_CHOICES)
    name = models.CharField('姓名', max_length=100)
    
    # 律师信息
    law_firm = models.CharField('律师事务所', max_length=200, blank=True)
    license_number = models.CharField('执业证号', max_length=100, blank=True)
    specialty = models.CharField('专业领域', max_length=200, blank=True)
    
    # 法官信息
    court_name = models.CharField('法院名称', max_length=200, blank=True)
    position = models.CharField('职务', max_length=100, blank=True)
    
    # 当事人信息
    party_type = models.CharField('当事人类型', max_length=20, blank=True, help_text='自然人/法人/其他组织')
    
    # 联系信息
    contact_phone = models.CharField('联系电话', max_length=20, blank=True)
    contact_email = models.EmailField('联系邮箱', max_length=255, blank=True)
    address = models.TextField('地址', blank=True)
    
    # 角色信息
    role = models.CharField('角色', max_length=100, blank=True, help_text='代理角色、审理角色、当事人角色等')
    
    # 评价信息
    rating = models.IntegerField('评价', null=True, blank=True, validators=[MinValueValidator(1), MaxValueValidator(5)])
    evaluation = models.TextField('评价内容', blank=True)
    
    # 时间戳
    created_at = models.DateTimeField('创建时间', auto_now_add=True)
    updated_at = models.DateTimeField('更新时间', auto_now=True)
    
    class Meta:
        db_table = 'litigation_person'
        verbose_name = '诉讼人员'
        verbose_name_plural = verbose_name
        ordering = ['person_type', 'name']
    
    def __str__(self):
        return f"{self.get_person_type_display()} - {self.name}"
    
    def get_absolute_url(self):
        """获取人员详情页URL"""
        from django.urls import reverse
        return reverse('litigation_pages:person_detail', args=[self.id])


class LitigationTimeline(models.Model):
    """诉讼时间节点模型"""
    
    TIMELINE_TYPE_CHOICES = [
        ('filing', '立案时间'),
        ('trial', '庭审时间'),
        ('judgment', '判决时间'),
        ('execution', '执行时间'),
        ('preservation_renewal', '保全续封时间'),
        ('appeal_deadline', '上诉期限'),
        ('evidence_deadline', '举证期限'),
        ('defense_deadline', '答辩期限'),
        ('other', '其他时间'),
    ]
    
    STATUS_CHOICES = [
        ('pending', '待处理'),
        ('in_progress', '处理中'),
        ('completed', '已完成'),
        ('delayed', '已延期'),
        ('cancelled', '已取消'),
    ]
    
    case = models.ForeignKey(
        LitigationCase,
        on_delete=models.CASCADE,
        related_name='timelines',
        verbose_name='关联案件'
    )
    timeline_name = models.CharField('节点名称', max_length=200)
    timeline_type = models.CharField('节点类型', max_length=30, choices=TIMELINE_TYPE_CHOICES)
    timeline_date = models.DateTimeField('节点时间')
    description = models.TextField('节点说明', blank=True)
    status = models.CharField('节点状态', max_length=20, choices=STATUS_CHOICES, default='pending')
    
    # 提醒设置
    reminder_enabled = models.BooleanField('启用提醒', default=True)
    reminder_days_before = models.JSONField('提前提醒天数', default=list, help_text='如：[7, 3, 1] 表示提前7天、3天、1天提醒')
    reminder_sent = models.JSONField('已发送提醒', default=list, help_text='记录已发送的提醒日期')
    
    # 确认信息
    confirmed_by = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='confirmed_litigation_timelines',
        verbose_name='确认人'
    )
    confirmed_at = models.DateTimeField('确认时间', null=True, blank=True)
    
    # 时间戳
    created_at = models.DateTimeField('创建时间', auto_now_add=True)
    updated_at = models.DateTimeField('更新时间', auto_now=True)
    created_by = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        null=True,
        related_name='created_litigation_timelines',
        verbose_name='创建人'
    )
    
    class Meta:
        db_table = 'litigation_timeline'
        verbose_name = '诉讼时间节点'
        verbose_name_plural = verbose_name
        ordering = ['timeline_date']
        indexes = [
            models.Index(fields=['timeline_date']),
            models.Index(fields=['timeline_type']),
            models.Index(fields=['status']),
        ]
    
    def clean(self):
        """数据验证"""
        super().clean()
        
        # 验证日期
        if self.timeline_date and self.case:
            if self.case.registration_date:
                timeline_date_only = self.timeline_date.date() if hasattr(self.timeline_date, 'date') else self.timeline_date
                if timeline_date_only < self.case.registration_date:
                    raise ValidationError({'timeline_date': '时间节点日期不能早于案件登记日期'})
        
        # 验证提醒天数设置
        if self.reminder_days_before:
            if not isinstance(self.reminder_days_before, list):
                raise ValidationError({'reminder_days_before': '提前提醒天数必须是列表格式'})
            for day in self.reminder_days_before:
                if not isinstance(day, int) or day < 0:
                    raise ValidationError({'reminder_days_before': '提前提醒天数必须是大于等于0的整数'})
    
    def save(self, *args, **kwargs):
        self.full_clean()  # 调用clean方法进行验证
        super().save(*args, **kwargs)
    
    def __str__(self):
        return f"{self.case.case_number} - {self.timeline_name}"
    
    def get_absolute_url(self):
        """获取时间节点详情页URL"""
        from django.urls import reverse
        return reverse('litigation_pages:timeline_detail', args=[self.id])


class PreservationSeal(models.Model):
    """保全续封模型"""
    
    SEAL_TYPE_CHOICES = [
        ('property', '财产保全'),
        ('evidence', '证据保全'),
        ('behavior', '行为保全'),
        ('other', '其他保全'),
    ]
    
    STATUS_CHOICES = [
        ('active', '有效'),
        ('expired', '已到期'),
        ('renewed', '已续封'),
        ('released', '已解除'),
    ]
    
    case = models.ForeignKey(
        LitigationCase,
        on_delete=models.CASCADE,
        related_name='preservation_seals',
        verbose_name='关联案件'
    )
    seal_type = models.CharField('保全类型', max_length=20, choices=SEAL_TYPE_CHOICES)
    seal_amount = models.DecimalField('保全金额', max_digits=15, decimal_places=2, null=True, blank=True)
    seal_number = models.CharField('保全案号', max_length=100, blank=True)
    court_name = models.CharField('法院名称', max_length=200)
    
    # 期限信息
    start_date = models.DateField('保全开始日期')
    end_date = models.DateField('保全到期日期')
    renewal_date = models.DateField('续封日期', null=True, blank=True)
    renewal_deadline = models.DateField('续封截止日期', null=True, blank=True, help_text='续封申请截止日期')
    
    # 状态信息
    status = models.CharField('保全状态', max_length=20, choices=STATUS_CHOICES, default='active')
    
    # 续封信息
    renewal_applied = models.BooleanField('已申请续封', default=False)
    renewal_materials = models.TextField('续封所需材料', blank=True)
    
    # 备注
    notes = models.TextField('备注', blank=True)
    
    # 时间戳
    created_at = models.DateTimeField('创建时间', auto_now_add=True)
    updated_at = models.DateTimeField('更新时间', auto_now=True)
    created_by = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        null=True,
        related_name='created_preservation_seals',
        verbose_name='创建人'
    )
    
    class Meta:
        db_table = 'preservation_seal'
        verbose_name = '保全续封'
        verbose_name_plural = verbose_name
        ordering = ['-end_date']
    
    def __str__(self):
        return f"{self.case.case_number} - {self.get_seal_type_display()} - {self.end_date}"
    
    def get_absolute_url(self):
        """获取保全续封详情页URL"""
        from django.urls import reverse
        return reverse('litigation_pages:preservation_detail', args=[self.id])


class LitigationNotificationConfirmation(models.Model):
    """诉讼通知确认模型"""
    
    CONFIRMATION_STATUS_CHOICES = [
        ('pending', '待确认'),
        ('confirmed', '已确认'),
        ('read_unconfirmed', '已读未确认'),
        ('escalated', '已升级'),
    ]
    
    NOTIFICATION_TYPE_CHOICES = [
        ('trial_reminder', '开庭提醒'),
        ('preservation_renewal', '保全续封提醒'),
        ('appeal_deadline', '上诉期限提醒'),
        ('evidence_deadline', '举证期限提醒'),
        ('defense_deadline', '答辩期限提醒'),
        ('other', '其他提醒'),
    ]
    
    # 通知信息
    notification_type = models.CharField('通知类型', max_length=30, choices=NOTIFICATION_TYPE_CHOICES)
    notification_title = models.CharField('通知标题', max_length=200)
    notification_content = models.TextField('通知内容')
    
    # 关联信息
    case = models.ForeignKey(
        LitigationCase,
        on_delete=models.CASCADE,
        related_name='notification_confirmations',
        verbose_name='关联案件'
    )
    timeline = models.ForeignKey(
        LitigationTimeline,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='notification_confirmations',
        verbose_name='关联时间节点'
    )
    seal = models.ForeignKey(
        PreservationSeal,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='notification_confirmations',
        verbose_name='关联保全续封'
    )
    
    # 接收人信息
    recipient = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name='litigation_notification_confirmations',
        verbose_name='接收人'
    )
    
    # 确认状态
    status = models.CharField('确认状态', max_length=20, choices=CONFIRMATION_STATUS_CHOICES, default='pending')
    confirmed_at = models.DateTimeField('确认时间', null=True, blank=True)
    confirmed_by = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='confirmed_litigation_notifications',
        verbose_name='确认人'
    )
    
    # 通知发送信息
    sent_at = models.DateTimeField('发送时间', auto_now_add=True)
    sent_via_system = models.BooleanField('系统通知', default=True)
    sent_via_email = models.BooleanField('邮件通知', default=False)
    sent_via_sms = models.BooleanField('短信通知', default=False)
    
    # 升级信息
    escalated_at = models.DateTimeField('升级时间', null=True, blank=True)
    escalated_to = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='escalated_litigation_notifications',
        verbose_name='升级通知对象'
    )
    escalation_level = models.IntegerField('升级级别', default=0, help_text='0=未升级，1=二次提醒，2=通知上级，3=电话通知')
    
    # 紧急程度
    urgency_level = models.CharField('紧急程度', max_length=10, choices=[
        ('normal', '一般'),
        ('important', '重要'),
        ('urgent', '紧急'),
    ], default='normal')
    
    # 时间戳
    created_at = models.DateTimeField('创建时间', auto_now_add=True)
    updated_at = models.DateTimeField('更新时间', auto_now=True)
    
    class Meta:
        db_table = 'litigation_notification_confirmation'
        verbose_name = '诉讼通知确认'
        verbose_name_plural = verbose_name
        ordering = ['-sent_at']
        indexes = [
            models.Index(fields=['recipient', 'status']),
            models.Index(fields=['case', 'status']),
            models.Index(fields=['sent_at']),
            models.Index(fields=['notification_type', 'status']),
        ]
    
    def __str__(self):
        return f"{self.notification_title} - {self.recipient.username} ({self.get_status_display()})"
    
    def get_absolute_url(self):
        """获取确认详情页URL"""
        from django.urls import reverse
        return reverse('litigation_pages:notification_confirm', args=[self.id])
    
    def confirm(self, user):
        """确认通知"""
        self.status = 'confirmed'
        self.confirmed_at = timezone.now()
        self.confirmed_by = user
        self.save(update_fields=['status', 'confirmed_at', 'confirmed_by', 'updated_at'])
    
    def mark_as_read(self):
        """标记为已读但未确认"""
        if self.status == 'pending':
            self.status = 'read_unconfirmed'
            self.save(update_fields=['status', 'updated_at'])
    
    def escalate(self, escalated_to_user=None, level=None):
        """升级通知"""
        if level is None:
            level = self.escalation_level + 1
        
        self.status = 'escalated'
        self.escalated_at = timezone.now()
        self.escalation_level = level
        
        if escalated_to_user:
            self.escalated_to = escalated_to_user
        
        self.save(update_fields=['status', 'escalated_at', 'escalated_to', 'escalation_level', 'updated_at'])
    
    def clean(self):
        """数据验证"""
        super().clean()
        
        # 验证日期逻辑
        if self.end_date and self.start_date:
            if self.end_date < self.start_date:
                raise ValidationError({'end_date': '到期日期不能早于开始日期'})
        
        if self.renewal_date and self.end_date:
            if self.renewal_date < self.end_date:
                raise ValidationError({'renewal_date': '续封日期不能早于到期日期'})
        
        # 验证金额
        if self.seal_amount and self.seal_amount < 0:
            raise ValidationError({'seal_amount': '保全金额不能为负数'})
    
    def save(self, *args, **kwargs):
        self.full_clean()  # 调用clean方法进行验证
        super().save(*args, **kwargs)
    
    def is_expiring_soon(self, days=7):
        """检查是否即将到期"""
        from datetime import timedelta
        today = timezone.now().date()
        return self.end_date <= today + timedelta(days=days) and self.status == 'active'

