from django.db import models
from django.contrib.auth import get_user_model
from django.utils import timezone
from decimal import Decimal

User = get_user_model()


class AccountSubject(models.Model):
    """会计科目"""
    TYPE_CHOICES = [
        ('asset', '资产'),
        ('liability', '负债'),
        ('equity', '所有者权益'),
        ('revenue', '收入'),
        ('expense', '费用'),
        ('cost', '成本'),
    ]
    
    DIRECTION_CHOICES = [
        ('debit', '借方'),
        ('credit', '贷方'),
    ]
    
    code = models.CharField(max_length=50, unique=True, verbose_name='科目编码')
    name = models.CharField(max_length=100, verbose_name='科目名称')
    parent = models.ForeignKey('self', on_delete=models.CASCADE, null=True, blank=True, related_name='children', verbose_name='上级科目')
    subject_type = models.CharField(max_length=20, choices=TYPE_CHOICES, verbose_name='科目类型')
    direction = models.CharField(max_length=10, choices=DIRECTION_CHOICES, verbose_name='余额方向')
    level = models.IntegerField(default=1, verbose_name='科目级别')
    is_active = models.BooleanField(default=True, verbose_name='是否启用')
    description = models.TextField(blank=True, verbose_name='备注说明')
    created_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, related_name='created_account_subjects', verbose_name='创建人')
    created_time = models.DateTimeField(default=timezone.now, verbose_name='创建时间')
    
    class Meta:
        db_table = 'financial_account_subject'
        verbose_name = '会计科目'
        verbose_name_plural = verbose_name
        ordering = ['code']
        indexes = [
            models.Index(fields=['code']),
            models.Index(fields=['subject_type']),
        ]
    
    def __str__(self):
        return f"{self.code} - {self.name}"


class Voucher(models.Model):
    """记账凭证"""
    STATUS_CHOICES = [
        ('draft', '草稿'),
        ('submitted', '已提交'),
        ('approved', '已审核'),
        ('posted', '已过账'),
        ('rejected', '已拒绝'),
    ]
    
    voucher_number = models.CharField(max_length=50, unique=True, verbose_name='凭证字号')
    voucher_date = models.DateField(verbose_name='凭证日期')
    attachment_count = models.IntegerField(default=0, verbose_name='附件数')
    total_debit = models.DecimalField(max_digits=15, decimal_places=2, default=Decimal('0.00'), verbose_name='借方合计')
    total_credit = models.DecimalField(max_digits=15, decimal_places=2, default=Decimal('0.00'), verbose_name='贷方合计')
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='draft', verbose_name='状态')
    preparer = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, related_name='prepared_vouchers', verbose_name='制单人')
    reviewer = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True, related_name='reviewed_vouchers', verbose_name='审核人')
    reviewed_time = models.DateTimeField(null=True, blank=True, verbose_name='审核时间')
    posted_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True, related_name='posted_vouchers', verbose_name='过账人')
    posted_time = models.DateTimeField(null=True, blank=True, verbose_name='过账时间')
    notes = models.TextField(blank=True, verbose_name='备注')
    created_time = models.DateTimeField(default=timezone.now, verbose_name='创建时间')
    updated_time = models.DateTimeField(auto_now=True, verbose_name='更新时间')
    
    class Meta:
        db_table = 'financial_voucher'
        verbose_name = '记账凭证'
        verbose_name_plural = verbose_name
        ordering = ['-voucher_date', '-voucher_number']
        indexes = [
            models.Index(fields=['voucher_number']),
            models.Index(fields=['voucher_date']),
            models.Index(fields=['status']),
        ]
    
    def __str__(self):
        return f"{self.voucher_number} - {self.voucher_date}"


class VoucherEntry(models.Model):
    """凭证分录"""
    voucher = models.ForeignKey(Voucher, on_delete=models.CASCADE, related_name='entries', verbose_name='凭证')
    line_number = models.IntegerField(verbose_name='行号')
    account_subject = models.ForeignKey(AccountSubject, on_delete=models.PROTECT, related_name='voucher_entries', verbose_name='会计科目')
    summary = models.CharField(max_length=200, verbose_name='摘要')
    debit_amount = models.DecimalField(max_digits=15, decimal_places=2, default=Decimal('0.00'), verbose_name='借方金额')
    credit_amount = models.DecimalField(max_digits=15, decimal_places=2, default=Decimal('0.00'), verbose_name='贷方金额')
    created_time = models.DateTimeField(default=timezone.now, verbose_name='创建时间')
    
    class Meta:
        db_table = 'financial_voucher_entry'
        verbose_name = '凭证分录'
        verbose_name_plural = verbose_name
        ordering = ['voucher', 'line_number']
        unique_together = [['voucher', 'line_number']]
    
    def __str__(self):
        return f"{self.voucher.voucher_number} - {self.line_number}行"


class Ledger(models.Model):
    """总账"""
    account_subject = models.ForeignKey(AccountSubject, on_delete=models.PROTECT, related_name='ledger_entries', verbose_name='会计科目')
    period_year = models.IntegerField(verbose_name='会计年度')
    period_month = models.IntegerField(verbose_name='会计期间')
    period_date = models.DateField(verbose_name='日期')
    opening_balance = models.DecimalField(max_digits=15, decimal_places=2, default=Decimal('0.00'), verbose_name='期初余额')
    period_debit = models.DecimalField(max_digits=15, decimal_places=2, default=Decimal('0.00'), verbose_name='本期借方')
    period_credit = models.DecimalField(max_digits=15, decimal_places=2, default=Decimal('0.00'), verbose_name='本期贷方')
    closing_balance = models.DecimalField(max_digits=15, decimal_places=2, default=Decimal('0.00'), verbose_name='期末余额')
    created_time = models.DateTimeField(default=timezone.now, verbose_name='创建时间')
    
    class Meta:
        db_table = 'financial_ledger'
        verbose_name = '总账'
        verbose_name_plural = verbose_name
        ordering = ['account_subject', 'period_date']
        unique_together = [['account_subject', 'period_year', 'period_month', 'period_date']]
        indexes = [
            models.Index(fields=['account_subject', 'period_date']),
            models.Index(fields=['period_year', 'period_month']),
        ]
    
    def __str__(self):
        return f"{self.account_subject} - {self.period_date}"


class Budget(models.Model):
    """预算管理"""
    STATUS_CHOICES = [
        ('draft', '草稿'),
        ('approved', '已批准'),
        ('executing', '执行中'),
        ('completed', '已完成'),
        ('cancelled', '已取消'),
    ]
    
    budget_number = models.CharField(max_length=50, unique=True, verbose_name='预算编号')
    name = models.CharField(max_length=200, verbose_name='预算名称')
    budget_year = models.IntegerField(verbose_name='预算年度')
    budget_amount = models.DecimalField(max_digits=15, decimal_places=2, verbose_name='预算金额')
    used_amount = models.DecimalField(max_digits=15, decimal_places=2, default=Decimal('0.00'), verbose_name='已用金额')
    remaining_amount = models.DecimalField(max_digits=15, decimal_places=2, default=Decimal('0.00'), verbose_name='剩余金额')
    department = models.ForeignKey('system_management.Department', on_delete=models.SET_NULL, null=True, blank=True, related_name='budgets', verbose_name='所属部门')
    account_subject = models.ForeignKey(AccountSubject, on_delete=models.PROTECT, null=True, blank=True, related_name='budgets', verbose_name='预算科目')
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='draft', verbose_name='状态')
    approver = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True, related_name='approved_budgets', verbose_name='审批人')
    approved_time = models.DateTimeField(null=True, blank=True, verbose_name='审批时间')
    start_date = models.DateField(verbose_name='开始日期')
    end_date = models.DateField(verbose_name='结束日期')
    description = models.TextField(blank=True, verbose_name='备注说明')
    created_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, related_name='created_budgets', verbose_name='创建人')
    created_time = models.DateTimeField(default=timezone.now, verbose_name='创建时间')
    
    class Meta:
        db_table = 'financial_budget'
        verbose_name = '预算管理'
        verbose_name_plural = verbose_name
        ordering = ['-budget_year', '-created_time']
        indexes = [
            models.Index(fields=['budget_number']),
            models.Index(fields=['budget_year']),
            models.Index(fields=['status']),
        ]
    
    def __str__(self):
        return f"{self.budget_number} - {self.name}"


class Invoice(models.Model):
    """发票管理"""
    TYPE_CHOICES = [
        ('incoming', '进项发票'),
        ('outgoing', '销项发票'),
    ]
    
    STATUS_CHOICES = [
        ('draft', '草稿'),
        ('issued', '已开具'),
        ('verified', '已认证'),
        ('cancelled', '已作废'),
    ]
    
    invoice_number = models.CharField(max_length=100, verbose_name='发票号码')
    invoice_code = models.CharField(max_length=50, verbose_name='发票代码')
    invoice_type = models.CharField(max_length=20, choices=TYPE_CHOICES, verbose_name='发票类型')
    invoice_date = models.DateField(verbose_name='开票日期')
    amount = models.DecimalField(max_digits=15, decimal_places=2, verbose_name='发票金额')
    tax_amount = models.DecimalField(max_digits=15, decimal_places=2, default=Decimal('0.00'), verbose_name='税额')
    total_amount = models.DecimalField(max_digits=15, decimal_places=2, verbose_name='价税合计')
    customer_name = models.CharField(max_length=200, blank=True, verbose_name='客户名称')
    supplier_name = models.CharField(max_length=200, blank=True, verbose_name='供应商名称')
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='draft', verbose_name='状态')
    verified_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True, related_name='verified_invoices', verbose_name='认证人')
    verified_time = models.DateTimeField(null=True, blank=True, verbose_name='认证时间')
    attachment = models.FileField(upload_to='invoices/', blank=True, null=True, verbose_name='发票附件')
    notes = models.TextField(blank=True, verbose_name='备注')
    created_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, related_name='created_invoices', verbose_name='创建人')
    created_time = models.DateTimeField(default=timezone.now, verbose_name='创建时间')
    
    class Meta:
        db_table = 'financial_invoice'
        verbose_name = '发票管理'
        verbose_name_plural = verbose_name
        ordering = ['-invoice_date', '-invoice_number']
        unique_together = [['invoice_number', 'invoice_code']]
        indexes = [
            models.Index(fields=['invoice_number']),
            models.Index(fields=['invoice_date']),
            models.Index(fields=['invoice_type']),
            models.Index(fields=['status']),
        ]
    
    def __str__(self):
        return f"{self.invoice_number} - {self.total_amount}"


class FundFlow(models.Model):
    """资金流水"""
    TYPE_CHOICES = [
        ('income', '收入'),
        ('expense', '支出'),
        ('transfer', '转账'),
    ]
    
    flow_number = models.CharField(max_length=50, unique=True, verbose_name='流水号')
    flow_date = models.DateField(verbose_name='发生日期')
    flow_type = models.CharField(max_length=20, choices=TYPE_CHOICES, verbose_name='流水类型')
    amount = models.DecimalField(max_digits=15, decimal_places=2, verbose_name='金额')
    account_name = models.CharField(max_length=100, verbose_name='账户名称')
    counterparty = models.CharField(max_length=200, blank=True, verbose_name='对方单位')
    summary = models.CharField(max_length=200, verbose_name='摘要')
    project = models.ForeignKey('project_center.Project', on_delete=models.SET_NULL, null=True, blank=True, related_name='fund_flows', verbose_name='关联项目')
    voucher = models.ForeignKey(Voucher, on_delete=models.SET_NULL, null=True, blank=True, related_name='fund_flows', verbose_name='关联凭证')
    created_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, related_name='created_fund_flows', verbose_name='创建人')
    created_time = models.DateTimeField(default=timezone.now, verbose_name='创建时间')
    
    class Meta:
        db_table = 'financial_fund_flow'
        verbose_name = '资金流水'
        verbose_name_plural = verbose_name
        ordering = ['-flow_date', '-flow_number']
        indexes = [
            models.Index(fields=['flow_number']),
            models.Index(fields=['flow_date']),
            models.Index(fields=['flow_type']),
        ]
    
    def __str__(self):
        return f"{self.flow_number} - {self.amount}"
