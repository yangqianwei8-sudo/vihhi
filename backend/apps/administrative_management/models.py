from django.db import models
from django.utils import timezone
from django.db.models import Max, Sum, F, F
from datetime import datetime
from decimal import Decimal
from backend.apps.system_management.models import User, Department


# ==================== 办公用品管理 ====================

class SupplyCategory(models.Model):
    """办公用品分类"""
    name = models.CharField(max_length=100, verbose_name='分类名称')
    code = models.CharField(max_length=50, unique=True, blank=True, verbose_name='分类编码')
    parent = models.ForeignKey('self', on_delete=models.CASCADE, null=True, blank=True, related_name='children', verbose_name='上级分类')
    description = models.TextField(blank=True, verbose_name='分类描述')
    sort_order = models.IntegerField(default=0, verbose_name='排序顺序')
    is_active = models.BooleanField(default=True, verbose_name='是否启用')
    created_time = models.DateTimeField(default=timezone.now, verbose_name='创建时间')
    updated_time = models.DateTimeField(auto_now=True, verbose_name='更新时间')
    
    class Meta:
        db_table = 'admin_supply_category'
        verbose_name = '办公用品分类'
        verbose_name_plural = verbose_name
        ordering = ['sort_order', 'name']
        indexes = [
            models.Index(fields=['code']),
            models.Index(fields=['parent', 'is_active']),
        ]
    
    def __str__(self):
        if self.parent:
            return f"{self.parent.name} > {self.name}"
        return self.name
    
    def save(self, *args, **kwargs):
        if not self.code:
            max_category = SupplyCategory.objects.filter(
                code__startswith='CAT-'
            ).aggregate(max_num=Max('code'))['max_num']
            if max_category:
                try:
                    seq = int(max_category.split('-')[-1]) + 1
                except (ValueError, IndexError):
                    seq = 1
            else:
                seq = 1
            self.code = f'CAT-{seq:05d}'
        super().save(*args, **kwargs)
    
    @property
    def full_path(self):
        """获取完整分类路径"""
        if self.parent:
            return f"{self.parent.full_path} > {self.name}"
        return self.name


class OfficeSupply(models.Model):
    """办公用品"""
    CATEGORY_CHOICES = [
        ('consumable', '消耗品'),
        ('fixed_asset', '固定资产'),
        ('low_value', '低值易耗品'),
    ]
    
    code = models.CharField(max_length=50, unique=True, verbose_name='用品编码')
    name = models.CharField(max_length=200, verbose_name='用品名称')
    category = models.CharField(max_length=20, choices=CATEGORY_CHOICES, default='consumable', verbose_name='分类')  # 保留旧字段以兼容
    supply_category = models.ForeignKey(SupplyCategory, on_delete=models.SET_NULL, null=True, blank=True, related_name='supplies', verbose_name='用品分类')
    unit = models.CharField(max_length=20, default='个', verbose_name='单位')
    specification = models.CharField(max_length=200, blank=True, verbose_name='规格型号')
    brand = models.CharField(max_length=100, blank=True, verbose_name='品牌')
    supplier = models.CharField(max_length=200, blank=True, verbose_name='供应商')
    purchase_price = models.DecimalField(max_digits=10, decimal_places=2, default=0, verbose_name='采购单价')
    current_stock = models.IntegerField(default=0, verbose_name='当前库存')
    min_stock = models.IntegerField(default=0, verbose_name='最低库存')
    max_stock = models.IntegerField(default=0, verbose_name='最高库存')
    storage_location = models.CharField(max_length=200, blank=True, verbose_name='存放位置')
    description = models.TextField(blank=True, verbose_name='描述')
    is_active = models.BooleanField(default=True, verbose_name='是否启用')
    created_by = models.ForeignKey(User, on_delete=models.PROTECT, related_name='created_supplies', verbose_name='创建人')
    created_time = models.DateTimeField(default=timezone.now, verbose_name='创建时间')
    updated_time = models.DateTimeField(auto_now=True, verbose_name='更新时间')
    
    class Meta:
        db_table = 'admin_office_supply'
        verbose_name = '办公用品'
        verbose_name_plural = verbose_name
        ordering = ['-created_time']
        indexes = [
            models.Index(fields=['code']),
            models.Index(fields=['category', 'is_active']),
        ]
    
    def __str__(self):
        return f"{self.code} - {self.name}"
    
    @property
    def is_low_stock(self):
        """是否低库存"""
        return self.current_stock <= self.min_stock if self.min_stock > 0 else False


class SupplyPurchase(models.Model):
    """用品采购"""
    STATUS_CHOICES = [
        ('draft', '草稿'),
        ('pending_approval', '待审批'),
        ('approved', '已批准'),
        ('rejected', '已拒绝'),
        ('purchased', '已采购'),
        ('received', '已收货'),
    ]
    
    purchase_number = models.CharField(max_length=100, unique=True, verbose_name='采购单号')
    purchase_date = models.DateField(default=timezone.now, verbose_name='采购日期')
    supplier = models.CharField(max_length=200, verbose_name='供应商')  # 保留字符串字段以兼容旧数据
    supplier_obj = models.ForeignKey('Supplier', on_delete=models.SET_NULL, null=True, blank=True, related_name='purchases', verbose_name='供应商对象')
    total_amount = models.DecimalField(max_digits=12, decimal_places=2, default=0, verbose_name='采购总金额')
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='draft', verbose_name='状态')
    approver = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True, related_name='approved_purchases', verbose_name='审批人')
    approved_time = models.DateTimeField(null=True, blank=True, verbose_name='审批时间')
    received_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True, related_name='received_purchases', verbose_name='收货人')
    received_time = models.DateTimeField(null=True, blank=True, verbose_name='收货时间')
    notes = models.TextField(blank=True, verbose_name='备注')
    created_by = models.ForeignKey(User, on_delete=models.PROTECT, related_name='created_purchases', verbose_name='创建人')
    created_time = models.DateTimeField(default=timezone.now, verbose_name='创建时间')
    
    class Meta:
        db_table = 'admin_supply_purchase'
        verbose_name = '用品采购'
        verbose_name_plural = verbose_name
        ordering = ['-created_time']
    
    def __str__(self):
        return f"{self.purchase_number} - {self.get_status_display()}"
    
    def save(self, *args, **kwargs):
        if not self.purchase_number:
            current_year = datetime.now().year
            max_purchase = SupplyPurchase.objects.filter(
                purchase_number__startswith=f'ADM-PUR-{current_year}-'
            ).aggregate(max_num=Max('purchase_number'))['max_num']
            if max_purchase:
                try:
                    seq = int(max_purchase.split('-')[-1]) + 1
                except (ValueError, IndexError):
                    seq = 1
            else:
                seq = 1
            self.purchase_number = f'ADM-PUR-{current_year}-{seq:04d}'
        super().save(*args, **kwargs)


class SupplyPurchaseItem(models.Model):
    """采购明细"""
    purchase = models.ForeignKey(SupplyPurchase, on_delete=models.CASCADE, related_name='items', verbose_name='采购单')
    supply = models.ForeignKey(OfficeSupply, on_delete=models.PROTECT, verbose_name='办公用品')
    quantity = models.IntegerField(verbose_name='采购数量')
    unit_price = models.DecimalField(max_digits=10, decimal_places=2, verbose_name='单价')
    total_amount = models.DecimalField(max_digits=10, decimal_places=2, verbose_name='小计金额')
    received_quantity = models.IntegerField(default=0, verbose_name='已收货数量')
    notes = models.TextField(blank=True, verbose_name='备注')
    
    class Meta:
        db_table = 'admin_supply_purchase_item'
        verbose_name = '采购明细'
        verbose_name_plural = verbose_name
    
    def __str__(self):
        return f"{self.purchase.purchase_number} - {self.supply.name}"
    
    def save(self, *args, **kwargs):
        self.total_amount = self.quantity * self.unit_price
        super().save(*args, **kwargs)


# ==================== 供应商管理 ====================

class Supplier(models.Model):
    """供应商"""
    RATING_CHOICES = [
        ('A', 'A级（优秀）'),
        ('B', 'B级（良好）'),
        ('C', 'C级（一般）'),
        ('D', 'D级（较差）'),
    ]
    
    name = models.CharField(max_length=200, unique=True, verbose_name='供应商名称')
    code = models.CharField(max_length=50, unique=True, blank=True, verbose_name='供应商编码')
    contact_person = models.CharField(max_length=100, blank=True, verbose_name='联系人')
    contact_phone = models.CharField(max_length=50, blank=True, verbose_name='联系电话')
    contact_email = models.EmailField(blank=True, verbose_name='联系邮箱')
    address = models.CharField(max_length=500, blank=True, verbose_name='地址')
    tax_id = models.CharField(max_length=50, blank=True, verbose_name='税号')
    bank_name = models.CharField(max_length=200, blank=True, verbose_name='开户银行')
    bank_account = models.CharField(max_length=100, blank=True, verbose_name='银行账号')
    rating = models.CharField(max_length=10, choices=RATING_CHOICES, default='C', verbose_name='供应商评级')
    credit_limit = models.DecimalField(max_digits=12, decimal_places=2, default=0, verbose_name='信用额度')
    payment_terms = models.CharField(max_length=200, blank=True, verbose_name='付款条件')
    description = models.TextField(blank=True, verbose_name='描述')
    is_active = models.BooleanField(default=True, verbose_name='是否启用')
    created_by = models.ForeignKey(User, on_delete=models.PROTECT, related_name='created_suppliers', verbose_name='创建人')
    created_time = models.DateTimeField(default=timezone.now, verbose_name='创建时间')
    updated_time = models.DateTimeField(auto_now=True, verbose_name='更新时间')
    
    class Meta:
        db_table = 'admin_supplier'
        verbose_name = '供应商'
        verbose_name_plural = verbose_name
        ordering = ['name']
        indexes = [
            models.Index(fields=['name', 'is_active']),
            models.Index(fields=['code']),
        ]
    
    def __str__(self):
        return self.name
    
    def save(self, *args, **kwargs):
        if not self.code:
            max_supplier = Supplier.objects.filter(
                code__startswith='SUP-'
            ).aggregate(max_num=Max('code'))['max_num']
            if max_supplier:
                try:
                    seq = int(max_supplier.split('-')[-1]) + 1
                except (ValueError, IndexError):
                    seq = 1
            else:
                seq = 1
            self.code = f'SUP-{seq:05d}'
        super().save(*args, **kwargs)
    
    @property
    def total_purchase_amount(self):
        """累计采购金额"""
        from django.db.models import Sum
        return SupplyPurchase.objects.filter(
            supplier=self.name,
            status__in=['approved', 'purchased', 'received']
        ).aggregate(total=Sum('total_amount'))['total'] or Decimal('0.00')
    
    @property
    def purchase_count(self):
        """采购次数"""
        return SupplyPurchase.objects.filter(
            supplier=self.name,
            status__in=['approved', 'purchased', 'received']
        ).count()


class PurchaseContract(models.Model):
    """采购合同"""
    STATUS_CHOICES = [
        ('draft', '草稿'),
        ('pending_approval', '待审批'),
        ('approved', '已批准'),
        ('signed', '已签约'),
        ('executing', '执行中'),
        ('completed', '已完成'),
        ('cancelled', '已取消'),
    ]
    
    contract_number = models.CharField(max_length=100, unique=True, verbose_name='合同编号')
    contract_name = models.CharField(max_length=200, verbose_name='合同名称')
    supplier = models.ForeignKey(Supplier, on_delete=models.PROTECT, related_name='contracts', verbose_name='供应商')
    purchase = models.ForeignKey(SupplyPurchase, on_delete=models.SET_NULL, null=True, blank=True, related_name='contracts', verbose_name='关联采购单')
    contract_amount = models.DecimalField(max_digits=12, decimal_places=2, verbose_name='合同金额')
    signed_date = models.DateField(null=True, blank=True, verbose_name='签约日期')
    start_date = models.DateField(null=True, blank=True, verbose_name='合同开始日期')
    end_date = models.DateField(null=True, blank=True, verbose_name='合同结束日期')
    payment_terms = models.CharField(max_length=200, blank=True, verbose_name='付款条件')
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='draft', verbose_name='状态')
    contract_file = models.FileField(upload_to='purchases/contracts/', null=True, blank=True, verbose_name='合同文件')
    notes = models.TextField(blank=True, verbose_name='备注')
    created_by = models.ForeignKey(User, on_delete=models.PROTECT, related_name='created_purchase_contracts', verbose_name='创建人')
    created_time = models.DateTimeField(default=timezone.now, verbose_name='创建时间')
    updated_time = models.DateTimeField(auto_now=True, verbose_name='更新时间')
    
    class Meta:
        db_table = 'admin_purchase_contract'
        verbose_name = '采购合同'
        verbose_name_plural = verbose_name
        ordering = ['-created_time']
        indexes = [
            models.Index(fields=['contract_number']),
            models.Index(fields=['supplier', 'status']),
            models.Index(fields=['signed_date']),
        ]
    
    def __str__(self):
        return f"{self.contract_number} - {self.contract_name}"
    
    def save(self, *args, **kwargs):
        if not self.contract_number:
            current_year = datetime.now().year
            max_contract = PurchaseContract.objects.filter(
                contract_number__startswith=f'PUR-CON-{current_year}-'
            ).aggregate(max_num=Max('contract_number'))['max_num']
            if max_contract:
                try:
                    seq = int(max_contract.split('-')[-1]) + 1
                except (ValueError, IndexError):
                    seq = 1
            else:
                seq = 1
            self.contract_number = f'PUR-CON-{current_year}-{seq:04d}'
        super().save(*args, **kwargs)
    
    @property
    def paid_amount(self):
        """已付款金额"""
        from django.db.models import Sum
        return PurchasePayment.objects.filter(
            contract=self,
            status='paid'
        ).aggregate(total=Sum('amount'))['total'] or Decimal('0.00')
    
    @property
    def unpaid_amount(self):
        """未付款金额"""
        return self.contract_amount - self.paid_amount


class PurchasePayment(models.Model):
    """采购付款"""
    STATUS_CHOICES = [
        ('pending', '待付款'),
        ('paid', '已付款'),
        ('cancelled', '已取消'),
    ]
    
    PAYMENT_METHOD_CHOICES = [
        ('bank_transfer', '银行转账'),
        ('check', '支票'),
        ('cash', '现金'),
        ('other', '其他'),
    ]
    
    payment_number = models.CharField(max_length=100, unique=True, verbose_name='付款单号')
    contract = models.ForeignKey(PurchaseContract, on_delete=models.PROTECT, related_name='payments', verbose_name='采购合同')
    amount = models.DecimalField(max_digits=12, decimal_places=2, verbose_name='付款金额')
    payment_date = models.DateField(verbose_name='付款日期')
    payment_method = models.CharField(max_length=20, choices=PAYMENT_METHOD_CHOICES, default='bank_transfer', verbose_name='付款方式')
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='pending', verbose_name='状态')
    voucher_number = models.CharField(max_length=100, blank=True, verbose_name='凭证号')
    paid_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True, related_name='paid_purchases', verbose_name='付款人')
    paid_time = models.DateTimeField(null=True, blank=True, verbose_name='付款时间')
    notes = models.TextField(blank=True, verbose_name='备注')
    created_by = models.ForeignKey(User, on_delete=models.PROTECT, related_name='created_purchase_payments', verbose_name='创建人')
    created_time = models.DateTimeField(default=timezone.now, verbose_name='创建时间')
    updated_time = models.DateTimeField(auto_now=True, verbose_name='更新时间')
    
    class Meta:
        db_table = 'admin_purchase_payment'
        verbose_name = '采购付款'
        verbose_name_plural = verbose_name
        ordering = ['-payment_date', '-created_time']
        indexes = [
            models.Index(fields=['payment_number']),
            models.Index(fields=['contract', 'status']),
            models.Index(fields=['payment_date']),
        ]
    
    def __str__(self):
        return f"{self.payment_number} - ¥{self.amount}"
    
    def save(self, *args, **kwargs):
        if not self.payment_number:
            current_date = datetime.now()
            date_str = current_date.strftime('%Y%m%d')
            max_payment = PurchasePayment.objects.filter(
                payment_number__startswith=f'PUR-PAY-{date_str}-'
            ).aggregate(max_num=Max('payment_number'))['max_num']
            if max_payment:
                try:
                    seq = int(max_payment.split('-')[-1]) + 1
                except (ValueError, IndexError):
                    seq = 1
            else:
                seq = 1
            self.payment_number = f'PUR-PAY-{date_str}-{seq:04d}'
        super().save(*args, **kwargs)


class SupplyRequest(models.Model):
    """用品领用申请"""
    STATUS_CHOICES = [
        ('draft', '草稿'),
        ('pending_approval', '待审批'),
        ('approved', '已批准'),
        ('rejected', '已拒绝'),
        ('issued', '已发放'),
    ]
    
    request_number = models.CharField(max_length=100, unique=True, verbose_name='申请单号')
    applicant = models.ForeignKey(User, on_delete=models.PROTECT, related_name='supply_requests', verbose_name='申请人')
    request_date = models.DateField(default=timezone.now, verbose_name='申请日期')
    purpose = models.TextField(blank=True, verbose_name='用途说明')
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='draft', verbose_name='状态')
    approver = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True, related_name='approved_supply_requests', verbose_name='审批人')
    approved_time = models.DateTimeField(null=True, blank=True, verbose_name='审批时间')
    issued_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True, related_name='issued_supply_requests', verbose_name='发放人')
    issued_time = models.DateTimeField(null=True, blank=True, verbose_name='发放时间')
    notes = models.TextField(blank=True, verbose_name='备注')
    created_time = models.DateTimeField(default=timezone.now, verbose_name='创建时间')
    
    class Meta:
        db_table = 'admin_supply_request'
        verbose_name = '用品领用申请'
        verbose_name_plural = verbose_name
        ordering = ['-created_time']
    
    def __str__(self):
        return f"{self.request_number} - {self.applicant.username}"
    
    def save(self, *args, **kwargs):
        if not self.request_number:
            current_year = datetime.now().year
            max_request = SupplyRequest.objects.filter(
                request_number__startswith=f'ADM-REQ-{current_year}-'
            ).aggregate(max_num=Max('request_number'))['max_num']
            if max_request:
                try:
                    seq = int(max_request.split('-')[-1]) + 1
                except (ValueError, IndexError):
                    seq = 1
            else:
                seq = 1
            self.request_number = f'ADM-REQ-{current_year}-{seq:04d}'
        super().save(*args, **kwargs)


class SupplyRequestItem(models.Model):
    """领用明细"""
    request = models.ForeignKey(SupplyRequest, on_delete=models.CASCADE, related_name='items', verbose_name='领用申请')
    supply = models.ForeignKey(OfficeSupply, on_delete=models.PROTECT, verbose_name='办公用品')
    requested_quantity = models.IntegerField(verbose_name='申请数量')
    approved_quantity = models.IntegerField(default=0, verbose_name='批准数量')
    issued_quantity = models.IntegerField(default=0, verbose_name='实际发放数量')
    notes = models.TextField(blank=True, verbose_name='备注')
    
    class Meta:
        db_table = 'admin_supply_request_item'
        verbose_name = '领用明细'
        verbose_name_plural = verbose_name
    
    def __str__(self):
        return f"{self.request.request_number} - {self.supply.name}"


# ==================== 库存盘点管理 ====================

class InventoryCheck(models.Model):
    """库存盘点"""
    STATUS_CHOICES = [
        ('draft', '草稿'),
        ('in_progress', '进行中'),
        ('completed', '已完成'),
        ('approved', '已审核'),
        ('cancelled', '已取消'),
    ]
    
    check_number = models.CharField(max_length=100, unique=True, verbose_name='盘点单号')
    check_date = models.DateField(default=timezone.now, verbose_name='盘点日期')
    check_scope = models.CharField(max_length=200, blank=True, verbose_name='盘点范围')
    check_location = models.CharField(max_length=200, blank=True, verbose_name='盘点地点')
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='draft', verbose_name='状态')
    checker = models.ForeignKey(User, on_delete=models.PROTECT, related_name='inventory_checks', verbose_name='盘点人')
    participants = models.ManyToManyField(User, blank=True, related_name='participated_inventory_checks', verbose_name='参与人员')
    notes = models.TextField(blank=True, verbose_name='备注')
    completed_time = models.DateTimeField(null=True, blank=True, verbose_name='完成时间')
    approver = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True, related_name='approved_inventory_checks', verbose_name='审核人')
    approved_time = models.DateTimeField(null=True, blank=True, verbose_name='审核时间')
    created_time = models.DateTimeField(default=timezone.now, verbose_name='创建时间')
    updated_time = models.DateTimeField(auto_now=True, verbose_name='更新时间')
    
    class Meta:
        db_table = 'admin_inventory_check'
        verbose_name = '库存盘点'
        verbose_name_plural = verbose_name
        ordering = ['-check_date', '-created_time']
        indexes = [
            models.Index(fields=['check_number']),
            models.Index(fields=['check_date', 'status']),
        ]
    
    def __str__(self):
        return f"{self.check_number} - {self.check_date}"
    
    def save(self, *args, **kwargs):
        if not self.check_number:
            current_date = datetime.now()
            date_str = current_date.strftime('%Y%m%d')
            max_check = InventoryCheck.objects.filter(
                check_number__startswith=f'INV-CHK-{date_str}-'
            ).aggregate(max_num=Max('check_number'))['max_num']
            if max_check:
                try:
                    seq = int(max_check.split('-')[-1]) + 1
                except (ValueError, IndexError):
                    seq = 1
            else:
                seq = 1
            self.check_number = f'INV-CHK-{date_str}-{seq:04d}'
        super().save(*args, **kwargs)
    
    @property
    def total_items(self):
        """盘点项总数"""
        return self.items.count()
    
    @property
    def completed_items(self):
        """已完成盘点项数"""
        return self.items.filter(actual_quantity__isnull=False).count()
    
    @property
    def accuracy_rate(self):
        """盘点准确率"""
        if self.total_items == 0:
            return 100.0
        completed = self.completed_items
        if completed == 0:
            return 0.0
        # 计算无差异的项数
        correct_items = self.items.filter(
            actual_quantity__isnull=False
        ).exclude(
            actual_quantity=F('book_quantity')
        ).count()
        return ((completed - correct_items) / completed) * 100 if completed > 0 else 0.0


class InventoryCheckItem(models.Model):
    """库存盘点明细"""
    inventory_check = models.ForeignKey(InventoryCheck, on_delete=models.CASCADE, related_name='items', verbose_name='盘点单', db_column='check_id')
    supply = models.ForeignKey(OfficeSupply, on_delete=models.PROTECT, related_name='check_items', verbose_name='用品')
    book_quantity = models.IntegerField(verbose_name='账面数量')
    actual_quantity = models.IntegerField(null=True, blank=True, verbose_name='实际数量')
    difference = models.IntegerField(default=0, verbose_name='差异数量')
    difference_amount = models.DecimalField(max_digits=10, decimal_places=2, default=0, verbose_name='差异金额')
    notes = models.TextField(blank=True, verbose_name='备注')
    checked_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True, related_name='checked_items', verbose_name='盘点人')
    checked_time = models.DateTimeField(null=True, blank=True, verbose_name='盘点时间')
    
    class Meta:
        db_table = 'admin_inventory_check_item'
        verbose_name = '库存盘点明细'
        verbose_name_plural = verbose_name
        ordering = ['supply__code']
        indexes = [
            models.Index(fields=['inventory_check', 'supply']),
        ]
    
    def __str__(self):
        return f"{self.inventory_check.check_number} - {self.supply.name}"
    
    def save(self, *args, **kwargs):
        if self.actual_quantity is not None and self.book_quantity is not None:
            self.difference = self.actual_quantity - self.book_quantity
            self.difference_amount = Decimal(self.difference) * self.supply.purchase_price
        super().save(*args, **kwargs)
    
    @property
    def is_surplus(self):
        """是否盘盈"""
        return self.difference > 0
    
    @property
    def is_shortage(self):
        """是否盘亏"""
        return self.difference < 0


class InventoryAdjust(models.Model):
    """库存调整"""
    STATUS_CHOICES = [
        ('draft', '草稿'),
        ('pending_approval', '待审批'),
        ('approved', '已批准'),
        ('rejected', '已拒绝'),
        ('executed', '已执行'),
    ]
    
    adjust_number = models.CharField(max_length=100, unique=True, verbose_name='调整单号')
    adjust_date = models.DateField(default=timezone.now, verbose_name='调整日期')
    reason = models.TextField(verbose_name='调整原因')
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='draft', verbose_name='状态')
    approver = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True, related_name='approved_inventory_adjusts', verbose_name='审批人')
    approved_time = models.DateTimeField(null=True, blank=True, verbose_name='审批时间')
    executed_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True, related_name='executed_inventory_adjusts', verbose_name='执行人')
    executed_time = models.DateTimeField(null=True, blank=True, verbose_name='执行时间')
    notes = models.TextField(blank=True, verbose_name='备注')
    created_by = models.ForeignKey(User, on_delete=models.PROTECT, related_name='created_inventory_adjusts', verbose_name='创建人')
    created_time = models.DateTimeField(default=timezone.now, verbose_name='创建时间')
    updated_time = models.DateTimeField(auto_now=True, verbose_name='更新时间')
    
    class Meta:
        db_table = 'admin_inventory_adjust'
        verbose_name = '库存调整'
        verbose_name_plural = verbose_name
        ordering = ['-adjust_date', '-created_time']
        indexes = [
            models.Index(fields=['adjust_number']),
            models.Index(fields=['adjust_date', 'status']),
        ]
    
    def __str__(self):
        return f"{self.adjust_number} - {self.adjust_date}"
    
    def save(self, *args, **kwargs):
        if not self.adjust_number:
            current_date = datetime.now()
            date_str = current_date.strftime('%Y%m%d')
            max_adjust = InventoryAdjust.objects.filter(
                adjust_number__startswith=f'INV-ADJ-{date_str}-'
            ).aggregate(max_num=Max('adjust_number'))['max_num']
            if max_adjust:
                try:
                    seq = int(max_adjust.split('-')[-1]) + 1
                except (ValueError, IndexError):
                    seq = 1
            else:
                seq = 1
            self.adjust_number = f'INV-ADJ-{date_str}-{seq:04d}'
        super().save(*args, **kwargs)


class InventoryAdjustItem(models.Model):
    """库存调整明细"""
    adjust = models.ForeignKey(InventoryAdjust, on_delete=models.CASCADE, related_name='items', verbose_name='调整单')
    supply = models.ForeignKey(OfficeSupply, on_delete=models.PROTECT, related_name='adjust_items', verbose_name='用品')
    adjust_quantity = models.IntegerField(verbose_name='调整数量')  # 正数为增加，负数为减少
    adjust_amount = models.DecimalField(max_digits=10, decimal_places=2, default=0, verbose_name='调整金额')
    notes = models.TextField(blank=True, verbose_name='备注')
    
    class Meta:
        db_table = 'admin_inventory_adjust_item'
        verbose_name = '库存调整明细'
        verbose_name_plural = verbose_name
        ordering = ['supply__code']
        indexes = [
            models.Index(fields=['adjust', 'supply']),
        ]
    
    def __str__(self):
        return f"{self.adjust.adjust_number} - {self.supply.name}"
    
    def save(self, *args, **kwargs):
        self.adjust_amount = Decimal(self.adjust_quantity) * self.supply.purchase_price
        super().save(*args, **kwargs)


# ==================== 会议室管理 ====================

class MeetingRoom(models.Model):
    """会议室"""
    STATUS_CHOICES = [
        ('available', '可用'),
        ('maintenance', '维护中'),
        ('unavailable', '不可用'),
    ]
    
    code = models.CharField(max_length=50, unique=True, verbose_name='会议室编号')
    name = models.CharField(max_length=200, verbose_name='会议室名称')
    location = models.CharField(max_length=200, blank=True, verbose_name='位置')
    capacity = models.IntegerField(default=0, verbose_name='容纳人数')
    equipment = models.JSONField(default=list, blank=True, verbose_name='设备清单')
    facilities = models.TextField(blank=True, verbose_name='设施说明')
    hourly_rate = models.DecimalField(max_digits=10, decimal_places=2, default=0, verbose_name='时租费用')
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='available', verbose_name='状态')
    description = models.TextField(blank=True, verbose_name='描述')
    is_active = models.BooleanField(default=True, verbose_name='是否启用')
    created_time = models.DateTimeField(default=timezone.now, verbose_name='创建时间')
    
    class Meta:
        db_table = 'admin_meeting_room'
        verbose_name = '会议室'
        verbose_name_plural = verbose_name
        ordering = ['code']
        indexes = [
            models.Index(fields=['code', 'status']),
        ]
    
    def __str__(self):
        return f"{self.code} - {self.name}"


class MeetingRoomBooking(models.Model):
    """会议室预订"""
    STATUS_CHOICES = [
        ('pending', '待确认'),
        ('confirmed', '已确认'),
        ('cancelled', '已取消'),
        ('completed', '已完成'),
    ]
    
    booking_number = models.CharField(max_length=100, unique=True, verbose_name='预订单号')
    room = models.ForeignKey(MeetingRoom, on_delete=models.PROTECT, related_name='bookings', verbose_name='会议室')
    booker = models.ForeignKey(User, on_delete=models.PROTECT, related_name='meeting_bookings', verbose_name='预订人')
    booking_date = models.DateField(verbose_name='预订日期')
    start_time = models.TimeField(verbose_name='开始时间')
    end_time = models.TimeField(verbose_name='结束时间')
    meeting_topic = models.CharField(max_length=200, blank=True, verbose_name='会议主题')
    attendees_count = models.IntegerField(default=0, verbose_name='参会人数')
    attendees = models.ManyToManyField(User, blank=True, related_name='attended_meetings', verbose_name='参会人员')
    equipment_needed = models.JSONField(default=list, blank=True, verbose_name='所需设备')
    special_requirements = models.TextField(blank=True, verbose_name='特殊需求')
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='pending', verbose_name='状态')
    cancelled_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True, related_name='cancelled_bookings', verbose_name='取消人')
    cancelled_time = models.DateTimeField(null=True, blank=True, verbose_name='取消时间')
    cancelled_reason = models.TextField(blank=True, verbose_name='取消原因')
    actual_start_time = models.DateTimeField(null=True, blank=True, verbose_name='实际开始时间')
    actual_end_time = models.DateTimeField(null=True, blank=True, verbose_name='实际结束时间')
    created_time = models.DateTimeField(default=timezone.now, verbose_name='创建时间')
    
    class Meta:
        db_table = 'admin_meeting_room_booking'
        verbose_name = '会议室预订'
        verbose_name_plural = verbose_name
        ordering = ['-booking_date', '-start_time']
        indexes = [
            models.Index(fields=['room', 'booking_date', 'start_time']),
            models.Index(fields=['status']),
        ]
    
    def __str__(self):
        return f"{self.booking_number} - {self.room.name} ({self.booking_date})"
    
    def save(self, *args, **kwargs):
        if not self.booking_number:
            current_year = datetime.now().year
            max_booking = MeetingRoomBooking.objects.filter(
                booking_number__startswith=f'ADM-BOOK-{current_year}-'
            ).aggregate(max_num=Max('booking_number'))['max_num']
            if max_booking:
                try:
                    seq = int(max_booking.split('-')[-1]) + 1
                except (ValueError, IndexError):
                    seq = 1
            else:
                seq = 1
            self.booking_number = f'ADM-BOOK-{current_year}-{seq:04d}'
        super().save(*args, **kwargs)


class Meeting(models.Model):
    """会议"""
    MEETING_TYPE_CHOICES = [
        ('internal', '内部会议'),
        ('external', '外部会议'),
        ('video', '视频会议'),
        ('other', '其他'),
    ]
    
    STATUS_CHOICES = [
        ('scheduled', '待开始'),
        ('in_progress', '进行中'),
        ('completed', '已结束'),
        ('cancelled', '已取消'),
    ]
    
    meeting_number = models.CharField(max_length=100, unique=True, verbose_name='会议编号')
    title = models.CharField(max_length=200, verbose_name='会议主题')
    meeting_type = models.CharField(max_length=20, choices=MEETING_TYPE_CHOICES, default='internal', verbose_name='会议类型')
    room = models.ForeignKey(MeetingRoom, on_delete=models.SET_NULL, null=True, blank=True, related_name='meetings', verbose_name='会议室')
    meeting_date = models.DateField(verbose_name='会议日期')
    start_time = models.TimeField(verbose_name='开始时间')
    end_time = models.TimeField(verbose_name='结束时间')
    duration = models.IntegerField(default=60, verbose_name='会议时长（分钟）')
    organizer = models.ForeignKey(User, on_delete=models.PROTECT, related_name='organized_meetings', verbose_name='组织人')
    attendees = models.ManyToManyField(User, blank=True, related_name='attended_meetings_list', verbose_name='参会人员')
    agenda = models.TextField(blank=True, verbose_name='会议议程')
    attachment = models.FileField(upload_to='meetings/attachments/', null=True, blank=True, verbose_name='会议附件')
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='scheduled', verbose_name='状态')
    cancelled_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True, related_name='cancelled_meetings', verbose_name='取消人')
    cancelled_time = models.DateTimeField(null=True, blank=True, verbose_name='取消时间')
    cancelled_reason = models.TextField(blank=True, verbose_name='取消原因')
    actual_start_time = models.DateTimeField(null=True, blank=True, verbose_name='实际开始时间')
    actual_end_time = models.DateTimeField(null=True, blank=True, verbose_name='实际结束时间')
    created_by = models.ForeignKey(User, on_delete=models.PROTECT, related_name='created_meetings', verbose_name='创建人')
    created_time = models.DateTimeField(default=timezone.now, verbose_name='创建时间')
    updated_time = models.DateTimeField(auto_now=True, verbose_name='更新时间')
    
    class Meta:
        db_table = 'admin_meeting'
        verbose_name = '会议'
        verbose_name_plural = verbose_name
        ordering = ['-meeting_date', '-start_time']
        indexes = [
            models.Index(fields=['meeting_number']),
            models.Index(fields=['meeting_date', 'status']),
            models.Index(fields=['room', 'meeting_date', 'start_time']),
        ]
    
    def __str__(self):
        return f"{self.meeting_number} - {self.title}"
    
    def save(self, *args, **kwargs):
        if not self.meeting_number:
            current_date = datetime.now()
            date_str = current_date.strftime('%Y%m%d')
            max_meeting = Meeting.objects.filter(
                meeting_number__startswith=f'MEET-{date_str}-'
            ).aggregate(max_num=Max('meeting_number'))['max_num']
            if max_meeting:
                try:
                    seq = int(max_meeting.split('-')[-1]) + 1
                except (ValueError, IndexError):
                    seq = 1
            else:
                seq = 1
            self.meeting_number = f'MEET-{date_str}-{seq:04d}'
        super().save(*args, **kwargs)
    
    @property
    def is_conflict(self):
        """检查是否有时间冲突"""
        if not self.room or not self.meeting_date:
            return False
        
        # 检查同一会议室、同一日期、同一时间段是否有其他会议或预订
        # 检查其他会议
        conflicts = Meeting.objects.filter(
            room=self.room,
            meeting_date=self.meeting_date,
            status__in=['scheduled', 'in_progress'],
        ).exclude(id=self.id if self.id else None)
        
        # 检查会议室预订
        bookings = MeetingRoomBooking.objects.filter(
            room=self.room,
            booking_date=self.meeting_date,
            status__in=['pending', 'confirmed'],
        )
        
        # 检查时间是否重叠
        for meeting in conflicts:
            if (self.start_time < meeting.end_time and self.end_time > meeting.start_time):
                return True
        
        for booking in bookings:
            if (self.start_time < booking.end_time and self.end_time > booking.start_time):
                return True
        
        return False


class MeetingRecord(models.Model):
    """会议记录"""
    meeting = models.OneToOneField(Meeting, on_delete=models.CASCADE, related_name='record', verbose_name='会议')
    minutes = models.TextField(verbose_name='会议纪要')
    resolutions = models.TextField(blank=True, verbose_name='会议决议')
    action_items = models.JSONField(default=list, blank=True, verbose_name='待办事项')
    attachment = models.FileField(upload_to='meetings/records/', null=True, blank=True, verbose_name='会议记录附件')
    recorder = models.ForeignKey(User, on_delete=models.PROTECT, related_name='recorded_meetings', verbose_name='记录人')
    record_time = models.DateTimeField(default=timezone.now, verbose_name='记录时间')
    created_time = models.DateTimeField(default=timezone.now, verbose_name='创建时间')
    updated_time = models.DateTimeField(auto_now=True, verbose_name='更新时间')
    
    class Meta:
        db_table = 'admin_meeting_record'
        verbose_name = '会议记录'
        verbose_name_plural = verbose_name
        ordering = ['-record_time']
    
    def __str__(self):
        return f"{self.meeting.meeting_number} - 会议记录"


class MeetingResolution(models.Model):
    """会议决议跟踪"""
    STATUS_CHOICES = [
        ('pending', '待执行'),
        ('in_progress', '执行中'),
        ('completed', '已完成'),
        ('cancelled', '已取消'),
    ]
    
    record = models.ForeignKey(MeetingRecord, on_delete=models.CASCADE, related_name='resolution_items', verbose_name='会议记录')
    resolution_content = models.TextField(verbose_name='决议内容')
    responsible_user = models.ForeignKey(User, on_delete=models.PROTECT, related_name='responsible_resolutions', verbose_name='负责人')
    due_date = models.DateField(null=True, blank=True, verbose_name='截止日期')
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='pending', verbose_name='状态')
    completion_notes = models.TextField(blank=True, verbose_name='完成说明')
    completed_time = models.DateTimeField(null=True, blank=True, verbose_name='完成时间')
    created_time = models.DateTimeField(default=timezone.now, verbose_name='创建时间')
    
    class Meta:
        db_table = 'admin_meeting_resolution'
        verbose_name = '会议决议'
        verbose_name_plural = verbose_name
        ordering = ['-created_time']
    
    def __str__(self):
        return f"{self.record.meeting.meeting_number} - {self.resolution_content[:50]}"


# ==================== 用车管理 ====================

class Vehicle(models.Model):
    """车辆"""
    VEHICLE_TYPE_CHOICES = [
        ('car', '轿车'),
        ('suv', 'SUV'),
        ('van', '面包车'),
        ('truck', '货车'),
    ]
    
    FUEL_TYPE_CHOICES = [
        ('gasoline', '汽油'),
        ('diesel', '柴油'),
        ('electric', '电动'),
        ('hybrid', '混合动力'),
    ]
    
    STATUS_CHOICES = [
        ('available', '可用'),
        ('in_use', '使用中'),
        ('maintenance', '维护中'),
        ('retired', '已报废'),
    ]
    
    plate_number = models.CharField(max_length=20, unique=True, verbose_name='车牌号')
    brand = models.CharField(max_length=100, verbose_name='品牌型号')
    vehicle_type = models.CharField(max_length=20, choices=VEHICLE_TYPE_CHOICES, default='car', verbose_name='车辆类型')
    color = models.CharField(max_length=50, blank=True, verbose_name='颜色')
    purchase_date = models.DateField(null=True, blank=True, verbose_name='购买日期')
    purchase_price = models.DecimalField(max_digits=12, decimal_places=2, default=0, verbose_name='购买价格')
    current_mileage = models.IntegerField(default=0, verbose_name='当前里程数')
    fuel_type = models.CharField(max_length=20, choices=FUEL_TYPE_CHOICES, default='gasoline', verbose_name='燃料类型')
    driver = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True, related_name='assigned_vehicles', verbose_name='专职司机')
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='available', verbose_name='状态')
    insurance_expiry = models.DateField(null=True, blank=True, verbose_name='保险到期日')
    annual_inspection_date = models.DateField(null=True, blank=True, verbose_name='年检日期')
    description = models.TextField(blank=True, verbose_name='描述')
    is_active = models.BooleanField(default=True, verbose_name='是否启用')
    created_time = models.DateTimeField(default=timezone.now, verbose_name='创建时间')
    
    class Meta:
        db_table = 'admin_vehicle'
        verbose_name = '车辆'
        verbose_name_plural = verbose_name
        ordering = ['plate_number']
        indexes = [
            models.Index(fields=['plate_number', 'status']),
        ]
    
    def __str__(self):
        return f"{self.plate_number} - {self.brand}"


class VehicleBooking(models.Model):
    """用车申请"""
    STATUS_CHOICES = [
        ('draft', '草稿'),
        ('pending_approval', '待审批'),
        ('approved', '已批准'),
        ('rejected', '已拒绝'),
        ('in_use', '使用中'),
        ('completed', '已完成'),
        ('cancelled', '已取消'),
    ]
    
    booking_number = models.CharField(max_length=100, unique=True, verbose_name='申请单号')
    vehicle = models.ForeignKey(Vehicle, on_delete=models.PROTECT, related_name='bookings', verbose_name='车辆')
    applicant = models.ForeignKey(User, on_delete=models.PROTECT, related_name='vehicle_bookings', verbose_name='申请人')
    driver = models.ForeignKey(User, on_delete=models.PROTECT, related_name='driven_vehicle_bookings', verbose_name='驾驶员')
    booking_date = models.DateField(default=timezone.now, verbose_name='申请日期')
    start_time = models.DateTimeField(verbose_name='用车开始时间')
    end_time = models.DateTimeField(verbose_name='预计结束时间')
    destination = models.CharField(max_length=200, blank=True, verbose_name='目的地')
    purpose = models.TextField(verbose_name='用车事由')
    passenger_count = models.IntegerField(default=1, verbose_name='乘车人数')
    mileage_before = models.IntegerField(null=True, blank=True, verbose_name='出发里程数')
    mileage_after = models.IntegerField(null=True, blank=True, verbose_name='返回里程数')
    fuel_cost = models.DecimalField(max_digits=10, decimal_places=2, default=0, verbose_name='燃油费用')
    parking_fee = models.DecimalField(max_digits=10, decimal_places=2, default=0, verbose_name='停车费用')
    toll_fee = models.DecimalField(max_digits=10, decimal_places=2, default=0, verbose_name='过路费用')
    other_cost = models.DecimalField(max_digits=10, decimal_places=2, default=0, verbose_name='其他费用')
    total_cost = models.DecimalField(max_digits=10, decimal_places=2, default=0, verbose_name='总费用')
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='draft', verbose_name='状态')
    approver = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True, related_name='approved_vehicle_bookings', verbose_name='审批人')
    approved_time = models.DateTimeField(null=True, blank=True, verbose_name='审批时间')
    actual_start_time = models.DateTimeField(null=True, blank=True, verbose_name='实际开始时间')
    actual_end_time = models.DateTimeField(null=True, blank=True, verbose_name='实际结束时间')
    notes = models.TextField(blank=True, verbose_name='备注')
    created_time = models.DateTimeField(default=timezone.now, verbose_name='创建时间')
    
    class Meta:
        db_table = 'admin_vehicle_booking'
        verbose_name = '用车申请'
        verbose_name_plural = verbose_name
        ordering = ['-booking_date', '-start_time']
        indexes = [
            models.Index(fields=['vehicle', 'start_time', 'end_time']),
            models.Index(fields=['status']),
        ]
    
    def __str__(self):
        return f"{self.booking_number} - {self.vehicle.plate_number}"
    
    def save(self, *args, **kwargs):
        if not self.booking_number:
            current_year = datetime.now().year
            max_booking = VehicleBooking.objects.filter(
                booking_number__startswith=f'ADM-VEH-{current_year}-'
            ).aggregate(max_num=Max('booking_number'))['max_num']
            if max_booking:
                try:
                    seq = int(max_booking.split('-')[-1]) + 1
                except (ValueError, IndexError):
                    seq = 1
            else:
                seq = 1
            self.booking_number = f'ADM-VEH-{current_year}-{seq:04d}'
        self.total_cost = self.fuel_cost + self.parking_fee + self.toll_fee + self.other_cost
        super().save(*args, **kwargs)
    
    @property
    def actual_mileage(self):
        """实际行驶里程"""
        if self.mileage_before and self.mileage_after:
            return self.mileage_after - self.mileage_before
        return None


class VehicleMaintenance(models.Model):
    """车辆维护记录"""
    MAINTENANCE_TYPE_CHOICES = [
        ('daily', '日常保养'),
        ('regular', '定期保养'),
        ('repair', '维修'),
        ('inspection', '年检'),
        ('insurance', '保险'),
        ('other', '其他'),
    ]
    
    vehicle = models.ForeignKey(Vehicle, on_delete=models.CASCADE, related_name='maintenances', verbose_name='车辆')
    maintenance_type = models.CharField(max_length=20, choices=MAINTENANCE_TYPE_CHOICES, default='daily', verbose_name='维护类型')
    maintenance_date = models.DateField(default=timezone.now, verbose_name='维护日期')
    maintenance_items = models.TextField(verbose_name='维护项目')
    cost = models.DecimalField(max_digits=10, decimal_places=2, default=0, verbose_name='维护费用')
    service_provider = models.CharField(max_length=200, blank=True, verbose_name='维护单位')
    description = models.TextField(blank=True, verbose_name='维护说明')
    next_maintenance_date = models.DateField(null=True, blank=True, verbose_name='下次维护日期')
    next_maintenance_mileage = models.IntegerField(null=True, blank=True, verbose_name='下次维护里程数')
    performed_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True, related_name='performed_vehicle_maintenances', verbose_name='执行人')
    created_time = models.DateTimeField(default=timezone.now, verbose_name='创建时间')
    
    class Meta:
        db_table = 'admin_vehicle_maintenance'
        verbose_name = '车辆维护记录'
        verbose_name_plural = verbose_name
        ordering = ['-maintenance_date']
        indexes = [
            models.Index(fields=['vehicle', 'maintenance_date']),
            models.Index(fields=['maintenance_type', 'maintenance_date']),
        ]
    
    def __str__(self):
        return f"{self.vehicle.plate_number} - {self.get_maintenance_type_display()} - {self.maintenance_date}"
    
    @property
    def is_overdue(self):
        """是否逾期"""
        if self.next_maintenance_date:
            return timezone.now().date() > self.next_maintenance_date
        return False


# ==================== 接待管理 ====================

class ReceptionRecord(models.Model):
    """接待记录"""
    RECEPTION_TYPE_CHOICES = [
        ('business_meeting', '商务会谈'),
        ('visit', '参观访问'),
        ('inspection', '视察检查'),
        ('interview', '面试'),
        ('other', '其他'),
    ]
    
    RECEPTION_LEVEL_CHOICES = [
        ('vip', 'VIP'),
        ('important', '重要'),
        ('general', '一般'),
    ]
    
    CATERING_CHOICES = [
        ('none', '无'),
        ('tea', '茶水'),
        ('breakfast', '早餐'),
        ('lunch', '午餐'),
        ('dinner', '晚餐'),
    ]
    
    STATUS_CHOICES = [
        ('draft', '草稿'),
        ('pending_approval', '待审批'),
        ('approved', '已批准'),
        ('rejected', '已拒绝'),
        ('arranged', '已安排'),
        ('completed', '已完成'),
        ('cancelled', '已取消'),
    ]
    
    record_number = models.CharField(max_length=100, unique=True, verbose_name='接待单号')
    visitor_name = models.CharField(max_length=100, verbose_name='访客姓名')
    visitor_company = models.CharField(max_length=200, blank=True, verbose_name='访客单位')
    visitor_position = models.CharField(max_length=100, blank=True, verbose_name='访客职位')
    visitor_phone = models.CharField(max_length=20, blank=True, verbose_name='访客电话')
    visitor_count = models.IntegerField(default=1, verbose_name='访客人数')
    reception_date = models.DateField(default=timezone.now, verbose_name='接待日期')
    reception_time = models.TimeField(verbose_name='接待时间')
    expected_duration = models.IntegerField(default=60, verbose_name='预计时长（分钟）')
    reception_type = models.CharField(max_length=20, choices=RECEPTION_TYPE_CHOICES, default='business_meeting', verbose_name='接待类型')
    reception_level = models.CharField(max_length=20, choices=RECEPTION_LEVEL_CHOICES, default='general', verbose_name='接待级别')
    host = models.ForeignKey(User, on_delete=models.PROTECT, related_name='hosted_receptions', verbose_name='接待人')
    participants = models.ManyToManyField(User, blank=True, related_name='participated_receptions', verbose_name='陪同人员')
    meeting_topic = models.CharField(max_length=200, blank=True, verbose_name='会议主题')
    meeting_location = models.CharField(max_length=200, blank=True, verbose_name='会议地点')
    catering_arrangement = models.CharField(max_length=20, choices=CATERING_CHOICES, default='none', verbose_name='餐饮安排')
    accommodation_arrangement = models.BooleanField(default=False, verbose_name='住宿安排')
    reception_budget = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True, verbose_name='接待预算')
    gifts_exchanged = models.TextField(blank=True, verbose_name='礼品交换情况')
    outcome = models.TextField(blank=True, verbose_name='接待结果/成果')
    feedback = models.TextField(blank=True, verbose_name='接待反馈')
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='draft', verbose_name='状态')
    approver = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True, related_name='approved_receptions', verbose_name='审批人')
    approved_time = models.DateTimeField(null=True, blank=True, verbose_name='审批时间')
    approval_notes = models.TextField(blank=True, verbose_name='审批意见')
    notes = models.TextField(blank=True, verbose_name='备注')
    created_by = models.ForeignKey(User, on_delete=models.PROTECT, related_name='created_receptions', verbose_name='创建人')
    created_time = models.DateTimeField(default=timezone.now, verbose_name='创建时间')
    updated_time = models.DateTimeField(auto_now=True, verbose_name='更新时间')
    
    class Meta:
        db_table = 'admin_reception_record'
        verbose_name = '接待记录'
        verbose_name_plural = verbose_name
        ordering = ['-reception_date', '-reception_time']
        indexes = [
            models.Index(fields=['reception_date', 'host']),
            models.Index(fields=['status', 'reception_date']),
        ]
    
    def __str__(self):
        return f"{self.record_number} - {self.visitor_name}"
    
    def save(self, *args, **kwargs):
        if not self.record_number:
            current_year = datetime.now().year
            max_record = ReceptionRecord.objects.filter(
                record_number__startswith=f'ADM-REC-{current_year}-'
            ).aggregate(max_num=Max('record_number'))['max_num']
            if max_record:
                try:
                    seq = int(max_record.split('-')[-1]) + 1
                except (ValueError, IndexError):
                    seq = 1
            else:
                seq = 1
            self.record_number = f'ADM-REC-{current_year}-{seq:04d}'
        super().save(*args, **kwargs)
    
    @property
    def total_expense(self):
        """总费用"""
        return self.expenses.aggregate(total=Sum('amount'))['total'] or Decimal('0')


class ReceptionExpense(models.Model):
    """接待费用"""
    EXPENSE_TYPE_CHOICES = [
        ('catering', '餐饮'),
        ('accommodation', '住宿'),
        ('transport', '交通'),
        ('gift', '礼品'),
        ('venue', '场地'),
        ('other', '其他'),
    ]
    
    STATUS_CHOICES = [
        ('pending', '待报销'),
        ('submitted', '已提交'),
        ('approved', '已批准'),
        ('rejected', '已拒绝'),
    ]
    
    reception = models.ForeignKey(ReceptionRecord, on_delete=models.CASCADE, related_name='expenses', verbose_name='接待记录')
    expense_type = models.CharField(max_length=20, choices=EXPENSE_TYPE_CHOICES, default='catering', verbose_name='费用类型')
    expense_date = models.DateField(default=timezone.now, verbose_name='费用日期')
    amount = models.DecimalField(max_digits=10, decimal_places=2, verbose_name='金额')
    description = models.TextField(blank=True, verbose_name='费用说明')
    invoice_number = models.CharField(max_length=100, blank=True, verbose_name='发票号码')
    invoice_file = models.FileField(upload_to='reception_expenses/invoices/', null=True, blank=True, verbose_name='发票文件')
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='pending', verbose_name='报销状态')
    created_time = models.DateTimeField(default=timezone.now, verbose_name='创建时间')
    
    class Meta:
        db_table = 'admin_reception_expense'
        verbose_name = '接待费用'
        verbose_name_plural = verbose_name
        ordering = ['-expense_date']
    
    def __str__(self):
        return f"{self.reception.record_number} - {self.get_expense_type_display()} - {self.amount}"


# ==================== 公告通知管理 ====================

class Announcement(models.Model):
    """公告通知"""
    CATEGORY_CHOICES = [
        ('system', '系统公告'),
        ('notice', '通知'),
        ('policy', '政策制度'),
        ('culture', '企业文化'),
        ('other', '其他'),
    ]
    
    PRIORITY_CHOICES = [
        ('urgent', '紧急'),
        ('important', '重要'),
        ('normal', '普通'),
    ]
    
    TARGET_SCOPE_CHOICES = [
        ('all', '全部'),
        ('department', '指定部门'),
        ('specific_roles', '指定角色'),
        ('specific_users', '指定用户'),
    ]
    
    title = models.CharField(max_length=200, verbose_name='标题')
    content = models.TextField(verbose_name='内容')
    category = models.CharField(max_length=20, choices=CATEGORY_CHOICES, default='notice', verbose_name='分类')
    priority = models.CharField(max_length=20, choices=PRIORITY_CHOICES, default='normal', verbose_name='优先级')
    target_scope = models.CharField(max_length=20, choices=TARGET_SCOPE_CHOICES, default='all', verbose_name='发布范围')
    target_departments = models.ManyToManyField(Department, blank=True, related_name='announcements', verbose_name='目标部门')
    target_roles = models.ManyToManyField('system_management.Role', blank=True, related_name='announcements', verbose_name='目标角色')
    target_users = models.ManyToManyField(User, blank=True, related_name='targeted_announcements', verbose_name='目标用户')
    publish_date = models.DateField(default=timezone.now, verbose_name='发布日期')
    expiry_date = models.DateField(null=True, blank=True, verbose_name='失效日期')
    is_top = models.BooleanField(default=False, verbose_name='是否置顶')
    is_popup = models.BooleanField(default=False, verbose_name='是否弹窗提醒')
    attachment = models.FileField(upload_to='announcements/', null=True, blank=True, verbose_name='附件')
    view_count = models.IntegerField(default=0, verbose_name='查看次数')
    publisher = models.ForeignKey(User, on_delete=models.PROTECT, related_name='published_announcements', verbose_name='发布人')
    publish_time = models.DateTimeField(default=timezone.now, verbose_name='发布时间')
    is_active = models.BooleanField(default=True, verbose_name='是否启用')
    created_time = models.DateTimeField(default=timezone.now, verbose_name='创建时间')
    
    class Meta:
        db_table = 'admin_announcement'
        verbose_name = '公告通知'
        verbose_name_plural = verbose_name
        ordering = ['-is_top', '-publish_date', '-publish_time']
        indexes = [
            models.Index(fields=['category', 'is_active']),
            models.Index(fields=['publish_date', 'expiry_date']),
        ]
    
    def __str__(self):
        return self.title


class AnnouncementRead(models.Model):
    """阅读记录"""
    announcement = models.ForeignKey(Announcement, on_delete=models.CASCADE, related_name='read_records', verbose_name='公告')
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='read_announcements', verbose_name='阅读用户')
    read_time = models.DateTimeField(default=timezone.now, verbose_name='阅读时间')
    
    class Meta:
        db_table = 'admin_announcement_read'
        verbose_name = '公告阅读记录'
        verbose_name_plural = verbose_name
        unique_together = [['announcement', 'user']]
        ordering = ['-read_time']
    
    def __str__(self):
        return f"{self.announcement.title} - {self.user.username}"


# ==================== 印章管理 ====================

class Seal(models.Model):
    """印章"""
    SEAL_TYPE_CHOICES = [
        ('company_seal', '公司公章'),
        ('contract_seal', '合同专用章'),
        ('financial_seal', '财务专用章'),
        ('personnel_seal', '人事专用章'),
        ('other', '其他'),
    ]
    
    STATUS_CHOICES = [
        ('available', '可用'),
        ('borrowed', '借用中'),
        ('lost', '遗失'),
        ('destroyed', '销毁'),
    ]
    
    seal_number = models.CharField(max_length=50, unique=True, verbose_name='印章编号')
    seal_name = models.CharField(max_length=200, verbose_name='印章名称')
    seal_type = models.CharField(max_length=20, choices=SEAL_TYPE_CHOICES, default='company_seal', verbose_name='印章类型')
    keeper = models.ForeignKey(User, on_delete=models.PROTECT, related_name='kept_seals', verbose_name='保管人')
    storage_location = models.CharField(max_length=200, blank=True, verbose_name='存放位置')
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='available', verbose_name='状态')
    description = models.TextField(blank=True, verbose_name='描述')
    is_active = models.BooleanField(default=True, verbose_name='是否启用')
    created_time = models.DateTimeField(default=timezone.now, verbose_name='创建时间')
    
    class Meta:
        db_table = 'admin_seal'
        verbose_name = '印章'
        verbose_name_plural = verbose_name
        ordering = ['seal_number']
        indexes = [
            models.Index(fields=['seal_number', 'status']),
        ]
    
    def __str__(self):
        return f"{self.seal_number} - {self.seal_name}"


class SealBorrowing(models.Model):
    """印章借用"""
    STATUS_CHOICES = [
        ('pending_approval', '待审批'),
        ('approved', '已批准'),
        ('rejected', '已拒绝'),
        ('borrowed', '借用中'),
        ('returned', '已归还'),
        ('overdue', '逾期'),
    ]
    
    borrowing_number = models.CharField(max_length=100, unique=True, verbose_name='借用单号')
    seal = models.ForeignKey(Seal, on_delete=models.PROTECT, related_name='borrowings', verbose_name='印章')
    borrower = models.ForeignKey(User, on_delete=models.PROTECT, related_name='seal_borrowings', verbose_name='借用人')
    borrowing_date = models.DateField(default=timezone.now, verbose_name='借用日期')
    borrowing_reason = models.TextField(verbose_name='借用事由')
    expected_return_date = models.DateField(verbose_name='预计归还日期')
    actual_return_date = models.DateField(null=True, blank=True, verbose_name='实际归还日期')
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='pending_approval', verbose_name='状态')
    approver = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True, related_name='approved_seal_borrowings', verbose_name='审批人')
    approved_time = models.DateTimeField(null=True, blank=True, verbose_name='审批时间')
    return_received_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True, related_name='received_seal_returns', verbose_name='归还接收人')
    notes = models.TextField(blank=True, verbose_name='备注')
    created_time = models.DateTimeField(default=timezone.now, verbose_name='创建时间')
    
    class Meta:
        db_table = 'admin_seal_borrowing'
        verbose_name = '印章借用'
        verbose_name_plural = verbose_name
        ordering = ['-borrowing_date']
        indexes = [
            models.Index(fields=['seal', 'status']),
        ]
    
    def __str__(self):
        return f"{self.borrowing_number} - {self.seal.seal_name}"
    
    def save(self, *args, **kwargs):
        if not self.borrowing_number:
            current_year = datetime.now().year
            max_borrowing = SealBorrowing.objects.filter(
                borrowing_number__startswith=f'ADM-SEA-{current_year}-'
            ).aggregate(max_num=Max('borrowing_number'))['max_num']
            if max_borrowing:
                try:
                    seq = int(max_borrowing.split('-')[-1]) + 1
                except (ValueError, IndexError):
                    seq = 1
            else:
                seq = 1
            self.borrowing_number = f'ADM-SEA-{current_year}-{seq:04d}'
        super().save(*args, **kwargs)
    
    @property
    def is_overdue(self):
        """是否逾期"""
        if self.status == 'borrowed' and self.expected_return_date:
            return timezone.now().date() > self.expected_return_date
        return False


class SealUsage(models.Model):
    """用印记录"""
    USAGE_TYPE_CHOICES = [
        ('contract', '合同'),
        ('agreement', '协议'),
        ('certificate', '证明'),
        ('document', '文件'),
        ('other', '其他'),
    ]
    
    usage_number = models.CharField(max_length=100, unique=True, verbose_name='用印单号')
    seal = models.ForeignKey(Seal, on_delete=models.PROTECT, related_name='usages', verbose_name='印章')
    borrowing = models.ForeignKey(SealBorrowing, on_delete=models.SET_NULL, null=True, blank=True, related_name='usages', verbose_name='关联借用')
    usage_type = models.CharField(max_length=20, choices=USAGE_TYPE_CHOICES, default='document', verbose_name='用印类型')
    usage_date = models.DateField(default=timezone.now, verbose_name='用印日期')
    usage_time = models.DateTimeField(default=timezone.now, verbose_name='用印时间')
    usage_reason = models.TextField(verbose_name='用印事由')
    usage_count = models.IntegerField(default=1, verbose_name='用印份数')
    document_name = models.CharField(max_length=200, blank=True, verbose_name='文件名称')
    document_file = models.FileField(upload_to='seal_usage/documents/', null=True, blank=True, verbose_name='用印文件')
    used_by = models.ForeignKey(User, on_delete=models.PROTECT, related_name='seal_usages', verbose_name='用印人')
    witness = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True, related_name='witnessed_seal_usages', verbose_name='见证人')
    notes = models.TextField(blank=True, verbose_name='备注')
    created_time = models.DateTimeField(default=timezone.now, verbose_name='创建时间')
    
    class Meta:
        db_table = 'admin_seal_usage'
        verbose_name = '用印记录'
        verbose_name_plural = verbose_name
        ordering = ['-usage_date', '-usage_time']
        indexes = [
            models.Index(fields=['seal', 'usage_date']),
            models.Index(fields=['usage_type', 'usage_date']),
        ]
    
    def __str__(self):
        return f"{self.usage_number} - {self.seal.seal_name}"
    
    def save(self, *args, **kwargs):
        if not self.usage_number:
            current_date = datetime.now()
            date_str = current_date.strftime('%Y%m%d')
            max_usage = SealUsage.objects.filter(
                usage_number__startswith=f'SEAL-USE-{date_str}-'
            ).aggregate(max_num=Max('usage_number'))['max_num']
            if max_usage:
                try:
                    seq = int(max_usage.split('-')[-1]) + 1
                except (ValueError, IndexError):
                    seq = 1
            else:
                seq = 1
            self.usage_number = f'SEAL-USE-{date_str}-{seq:04d}'
        super().save(*args, **kwargs)


class SealUsageFile(models.Model):
    """用印文件"""
    usage = models.ForeignKey(
        SealUsage,
        on_delete=models.CASCADE,
        related_name='files',
        verbose_name='用印记录'
    )
    file = models.FileField(
        upload_to='seal_usage/documents/',
        verbose_name='文件'
    )
    file_name = models.CharField(max_length=200, blank=True, verbose_name='文件名称')
    uploaded_time = models.DateTimeField(default=timezone.now, verbose_name='上传时间')
    uploaded_by = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='uploaded_seal_usage_files',
        verbose_name='上传人'
    )
    
    class Meta:
        db_table = 'admin_seal_usage_file'
        verbose_name = '用印文件'
        verbose_name_plural = verbose_name
        ordering = ['-uploaded_time']
        indexes = [
            models.Index(fields=['usage', 'uploaded_time']),
        ]
    
    def __str__(self):
        return f"{self.usage.usage_number} - {self.file_name or self.file.name}"
    
    def save(self, *args, **kwargs):
        # 如果没有设置文件名称，使用文件名
        if not self.file_name and self.file:
            self.file_name = self.file.name
        super().save(*args, **kwargs)


# ==================== 固定资产管理 ====================

class FixedAsset(models.Model):
    """固定资产"""
    CATEGORY_CHOICES = [
        ('computer', '电脑设备'),
        ('furniture', '办公家具'),
        ('equipment', '办公设备'),
        ('vehicle', '车辆'),
        ('other', '其他'),
    ]
    
    DEPRECIATION_METHOD_CHOICES = [
        ('straight_line', '直线法'),
        ('accelerated', '加速折旧法'),
    ]
    
    STATUS_CHOICES = [
        ('in_use', '使用中'),
        ('idle', '闲置'),
        ('maintenance', '维护中'),
        ('disposed', '已处置'),
    ]
    
    asset_number = models.CharField(max_length=100, unique=True, verbose_name='资产编号')
    asset_name = models.CharField(max_length=200, verbose_name='资产名称')
    category = models.CharField(max_length=20, choices=CATEGORY_CHOICES, default='computer', verbose_name='资产类别')
    brand = models.CharField(max_length=100, blank=True, verbose_name='品牌')
    model = models.CharField(max_length=100, blank=True, verbose_name='型号')
    specification = models.CharField(max_length=200, blank=True, verbose_name='规格')
    purchase_date = models.DateField(null=True, blank=True, verbose_name='购买日期')
    purchase_price = models.DecimalField(max_digits=12, decimal_places=2, default=0, verbose_name='购买价格')
    supplier = models.CharField(max_length=200, blank=True, verbose_name='供应商')
    warranty_period = models.IntegerField(default=0, verbose_name='保修期（月）')
    warranty_expiry = models.DateField(null=True, blank=True, verbose_name='保修到期日')
    current_user = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True, related_name='used_assets', verbose_name='当前使用人')
    current_location = models.CharField(max_length=200, blank=True, verbose_name='当前位置')
    department = models.ForeignKey(Department, on_delete=models.PROTECT, related_name='assets', verbose_name='所属部门')
    depreciation_method = models.CharField(max_length=20, choices=DEPRECIATION_METHOD_CHOICES, default='straight_line', verbose_name='折旧方法')
    depreciation_rate = models.DecimalField(max_digits=5, decimal_places=2, default=0, verbose_name='折旧率')
    net_value = models.DecimalField(max_digits=12, decimal_places=2, default=0, verbose_name='净值')
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='in_use', verbose_name='状态')
    description = models.TextField(blank=True, verbose_name='描述')
    is_active = models.BooleanField(default=True, verbose_name='是否启用')
    created_time = models.DateTimeField(default=timezone.now, verbose_name='创建时间')
    
    class Meta:
        db_table = 'admin_fixed_asset'
        verbose_name = '固定资产'
        verbose_name_plural = verbose_name
        ordering = ['-created_time']
        indexes = [
            models.Index(fields=['asset_number', 'status']),
            models.Index(fields=['category', 'department']),
        ]
    
    def __str__(self):
        return f"{self.asset_number} - {self.asset_name}"
    
    def save(self, *args, **kwargs):
        if not self.asset_number:
            current_year = datetime.now().year
            max_asset = FixedAsset.objects.filter(
                asset_number__startswith=f'ADM-ASSET-{current_year}-'
            ).aggregate(max_num=Max('asset_number'))['max_num']
            if max_asset:
                try:
                    seq = int(max_asset.split('-')[-1]) + 1
                except (ValueError, IndexError):
                    seq = 1
            else:
                seq = 1
            self.asset_number = f'ADM-ASSET-{current_year}-{seq:04d}'
        super().save(*args, **kwargs)


class AssetTransfer(models.Model):
    """资产转移"""
    STATUS_CHOICES = [
        ('pending_approval', '待审批'),
        ('approved', '已批准'),
        ('rejected', '已拒绝'),
        ('completed', '已完成'),
    ]
    
    transfer_number = models.CharField(max_length=100, unique=True, verbose_name='转移单号')
    asset = models.ForeignKey(FixedAsset, on_delete=models.PROTECT, related_name='transfers', verbose_name='资产')
    from_user = models.ForeignKey(User, on_delete=models.PROTECT, related_name='transferred_from_assets', verbose_name='原使用人')
    to_user = models.ForeignKey(User, on_delete=models.PROTECT, related_name='transferred_to_assets', verbose_name='新使用人')
    from_location = models.CharField(max_length=200, blank=True, verbose_name='原位置')
    to_location = models.CharField(max_length=200, blank=True, verbose_name='新位置')
    transfer_date = models.DateField(default=timezone.now, verbose_name='转移日期')
    transfer_reason = models.TextField(verbose_name='转移原因')
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='pending_approval', verbose_name='状态')
    approver = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True, related_name='approved_asset_transfers', verbose_name='审批人')
    approved_time = models.DateTimeField(null=True, blank=True, verbose_name='审批时间')
    completed_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True, related_name='completed_asset_transfers', verbose_name='完成人')
    completed_time = models.DateTimeField(null=True, blank=True, verbose_name='完成时间')
    notes = models.TextField(blank=True, verbose_name='备注')
    created_time = models.DateTimeField(default=timezone.now, verbose_name='创建时间')
    
    class Meta:
        db_table = 'admin_asset_transfer'
        verbose_name = '资产转移'
        verbose_name_plural = verbose_name
        ordering = ['-transfer_date']
    
    def __str__(self):
        return f"{self.transfer_number} - {self.asset.asset_name}"
    
    def save(self, *args, **kwargs):
        if not self.transfer_number:
            current_year = datetime.now().year
            max_transfer = AssetTransfer.objects.filter(
                transfer_number__startswith=f'ADM-TRF-{current_year}-'
            ).aggregate(max_num=Max('transfer_number'))['max_num']
            if max_transfer:
                try:
                    seq = int(max_transfer.split('-')[-1]) + 1
                except (ValueError, IndexError):
                    seq = 1
            else:
                seq = 1
            self.transfer_number = f'ADM-TRF-{current_year}-{seq:04d}'
        super().save(*args, **kwargs)


class AssetMaintenance(models.Model):
    """资产维护"""
    MAINTENANCE_TYPE_CHOICES = [
        ('repair', '维修'),
        ('upgrade', '升级'),
        ('inspection', '检查'),
        ('cleaning', '清洁'),
    ]
    
    asset = models.ForeignKey(FixedAsset, on_delete=models.CASCADE, related_name='maintenances', verbose_name='资产')
    maintenance_date = models.DateField(default=timezone.now, verbose_name='维护日期')
    maintenance_type = models.CharField(max_length=20, choices=MAINTENANCE_TYPE_CHOICES, default='repair', verbose_name='维护类型')
    service_provider = models.CharField(max_length=200, blank=True, verbose_name='服务商')
    cost = models.DecimalField(max_digits=10, decimal_places=2, default=0, verbose_name='维护费用')
    description = models.TextField(verbose_name='维护描述')
    next_maintenance_date = models.DateField(null=True, blank=True, verbose_name='下次维护日期')
    performed_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True, related_name='performed_maintenances', verbose_name='执行人')
    created_time = models.DateTimeField(default=timezone.now, verbose_name='创建时间')
    
    class Meta:
        db_table = 'admin_asset_maintenance'
        verbose_name = '资产维护'
        verbose_name_plural = verbose_name
        ordering = ['-maintenance_date']
    
    def __str__(self):
        return f"{self.asset.asset_name} - {self.get_maintenance_type_display()} ({self.maintenance_date})"


# ==================== 差旅管理 ====================

class TravelApplication(models.Model):
    """差旅申请"""
    TRAVEL_METHOD_CHOICES = [
        ('plane', '飞机'),
        ('train', '火车'),
        ('bus', '汽车'),
        ('self_drive', '自驾'),
        ('other', '其他'),
    ]
    
    STATUS_CHOICES = [
        ('draft', '草稿'),
        ('pending_approval', '待审批'),
        ('approved', '已批准'),
        ('rejected', '已拒绝'),
        ('in_progress', '进行中'),
        ('completed', '已完成'),
        ('cancelled', '已取消'),
    ]
    
    application_number = models.CharField(max_length=100, unique=True, verbose_name='申请单号')
    applicant = models.ForeignKey(User, on_delete=models.PROTECT, related_name='travel_applications', verbose_name='申请人')
    application_date = models.DateField(default=timezone.now, verbose_name='申请日期')
    travel_reason = models.TextField(verbose_name='差旅事由')
    destination = models.CharField(max_length=200, verbose_name='差旅目的地')
    start_date = models.DateField(verbose_name='开始时间')
    end_date = models.DateField(verbose_name='结束时间')
    travel_days = models.IntegerField(default=1, verbose_name='差旅天数')
    travelers = models.ManyToManyField(User, related_name='traveled_applications', verbose_name='差旅人员')
    travel_method = models.CharField(max_length=20, choices=TRAVEL_METHOD_CHOICES, default='plane', verbose_name='差旅方式')
    travel_budget = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True, verbose_name='差旅预算')
    department = models.ForeignKey(Department, on_delete=models.SET_NULL, null=True, blank=True, related_name='travel_applications', verbose_name='申请部门')
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='draft', verbose_name='状态')
    approver = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True, related_name='approved_travel_applications', verbose_name='审批人')
    approved_time = models.DateTimeField(null=True, blank=True, verbose_name='审批时间')
    approval_notes = models.TextField(blank=True, verbose_name='审批意见')
    notes = models.TextField(blank=True, verbose_name='备注')
    created_time = models.DateTimeField(default=timezone.now, verbose_name='创建时间')
    updated_time = models.DateTimeField(auto_now=True, verbose_name='更新时间')
    
    class Meta:
        db_table = 'admin_travel_application'
        verbose_name = '差旅申请'
        verbose_name_plural = verbose_name
        ordering = ['-application_date', '-created_time']
        indexes = [
            models.Index(fields=['applicant', 'status']),
            models.Index(fields=['start_date', 'end_date']),
        ]
    
    def __str__(self):
        return f"{self.application_number} - {self.destination}"
    
    def save(self, *args, **kwargs):
        if not self.application_number:
            current_date = datetime.now()
            date_str = current_date.strftime('%Y%m%d')
            max_app = TravelApplication.objects.filter(
                application_number__startswith=f'TRAVEL-{date_str}-'
            ).aggregate(max_num=Max('application_number'))['max_num']
            if max_app:
                try:
                    seq = int(max_app.split('-')[-1]) + 1
                except (ValueError, IndexError):
                    seq = 1
            else:
                seq = 1
            self.application_number = f'TRAVEL-{date_str}-{seq:04d}'
        
        # 自动计算差旅天数
        if self.start_date and self.end_date:
            delta = self.end_date - self.start_date
            self.travel_days = max(1, delta.days + 1)
        
        super().save(*args, **kwargs)


# ==================== 报销管理 ====================

class ExpenseReimbursement(models.Model):
    """报销申请"""
    EXPENSE_TYPE_CHOICES = [
        ('travel', '差旅费'),
        ('business_entertainment', '业务招待费'),
        ('office_supplies', '办公用品费'),
        ('communication', '通讯费'),
        ('other', '其他'),
    ]
    
    STATUS_CHOICES = [
        ('draft', '草稿'),
        ('pending_approval', '待审批'),
        ('finance_review', '财务审核中'),
        ('approved', '已批准'),
        ('rejected', '已拒绝'),
        ('paid', '已支付'),
    ]
    
    PAYMENT_METHOD_CHOICES = [
        ('cash', '现金'),
        ('bank_transfer', '银行转账'),
        ('alipay', '支付宝'),
        ('wechat', '微信支付'),
    ]
    
    reimbursement_number = models.CharField(max_length=100, unique=True, verbose_name='报销单号')
    travel_application = models.ForeignKey('TravelApplication', on_delete=models.SET_NULL, null=True, blank=True, related_name='reimbursements', verbose_name='关联差旅申请')
    applicant = models.ForeignKey(User, on_delete=models.PROTECT, related_name='expense_reimbursements', verbose_name='申请人')
    application_date = models.DateField(default=timezone.now, verbose_name='申请日期')
    expense_type = models.CharField(max_length=30, choices=EXPENSE_TYPE_CHOICES, default='other', verbose_name='报销类型')
    total_amount = models.DecimalField(max_digits=12, decimal_places=2, default=0, verbose_name='报销总金额')
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='draft', verbose_name='状态')
    approver = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True, related_name='approved_expenses', verbose_name='审批人')
    approved_time = models.DateTimeField(null=True, blank=True, verbose_name='审批时间')
    finance_reviewer = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True, related_name='reviewed_expenses', verbose_name='财务审核人')
    finance_reviewed_time = models.DateTimeField(null=True, blank=True, verbose_name='财务审核时间')
    payment_date = models.DateField(null=True, blank=True, verbose_name='支付日期')
    payment_method = models.CharField(max_length=20, choices=PAYMENT_METHOD_CHOICES, blank=True, verbose_name='支付方式')
    notes = models.TextField(blank=True, verbose_name='备注')
    created_time = models.DateTimeField(default=timezone.now, verbose_name='创建时间')
    
    class Meta:
        db_table = 'admin_expense_reimbursement'
        verbose_name = '报销申请'
        verbose_name_plural = verbose_name
        ordering = ['-application_date', '-created_time']
        indexes = [
            models.Index(fields=['applicant', 'status']),
        ]
    
    def __str__(self):
        return f"{self.reimbursement_number} - {self.applicant.username}"
    
    def save(self, *args, **kwargs):
        if not self.reimbursement_number:
            current_year = datetime.now().year
            max_expense = ExpenseReimbursement.objects.filter(
                reimbursement_number__startswith=f'ADM-EXP-{current_year}-'
            ).aggregate(max_num=Max('reimbursement_number'))['max_num']
            if max_expense:
                try:
                    seq = int(max_expense.split('-')[-1]) + 1
                except (ValueError, IndexError):
                    seq = 1
            else:
                seq = 1
            self.reimbursement_number = f'ADM-EXP-{current_year}-{seq:04d}'
        super().save(*args, **kwargs)


class ExpenseItem(models.Model):
    """费用明细"""
    EXPENSE_TYPE_CHOICES = [
        ('travel', '差旅'),
        ('accommodation', '住宿'),
        ('meal', '餐饮'),
        ('transport', '交通'),
        ('other', '其他'),
    ]
    
    reimbursement = models.ForeignKey(ExpenseReimbursement, on_delete=models.CASCADE, related_name='items', verbose_name='报销申请')
    expense_date = models.DateField(verbose_name='费用日期')
    expense_type = models.CharField(max_length=20, choices=EXPENSE_TYPE_CHOICES, default='other', verbose_name='费用类型')
    description = models.TextField(verbose_name='费用说明')
    amount = models.DecimalField(max_digits=10, decimal_places=2, verbose_name='金额')
    invoice_number = models.CharField(max_length=100, blank=True, verbose_name='发票号码')
    attachment = models.FileField(upload_to='expense_attachments/', null=True, blank=True, verbose_name='附件')
    notes = models.TextField(blank=True, verbose_name='备注')
    
    class Meta:
        db_table = 'admin_expense_item'
        verbose_name = '费用明细'
        verbose_name_plural = verbose_name
        ordering = ['expense_date']
    
    def __str__(self):
        return f"{self.reimbursement.reimbursement_number} - {self.get_expense_type_display()} - {self.amount}"


# ==================== 行政事务管理 ====================

class AdministrativeAffair(models.Model):
    """行政事务"""
    AFFAIR_TYPE_CHOICES = [
        ('daily', '日常事务'),
        ('special', '专项事务'),
        ('urgent', '紧急事务'),
        ('other', '其他'),
    ]
    
    STATUS_CHOICES = [
        ('pending', '待处理'),
        ('in_progress', '处理中'),
        ('completed', '已完成'),
        ('cancelled', '已取消'),
    ]
    
    PRIORITY_CHOICES = [
        ('low', '低'),
        ('normal', '普通'),
        ('high', '高'),
        ('urgent', '紧急'),
    ]
    
    affair_number = models.CharField(max_length=100, unique=True, verbose_name='事务编号')
    title = models.CharField(max_length=200, verbose_name='事务标题')
    affair_type = models.CharField(max_length=20, choices=AFFAIR_TYPE_CHOICES, default='daily', verbose_name='事务类型')
    content = models.TextField(verbose_name='事务内容')
    priority = models.CharField(max_length=20, choices=PRIORITY_CHOICES, default='normal', verbose_name='优先级')
    responsible_user = models.ForeignKey(User, on_delete=models.PROTECT, related_name='responsible_affairs', verbose_name='负责人')
    participants = models.ManyToManyField(User, blank=True, related_name='participated_affairs', verbose_name='参与人')
    planned_start_time = models.DateTimeField(verbose_name='计划开始时间')
    planned_end_time = models.DateTimeField(verbose_name='计划完成时间')
    actual_start_time = models.DateTimeField(null=True, blank=True, verbose_name='实际开始时间')
    actual_end_time = models.DateTimeField(null=True, blank=True, verbose_name='实际完成时间')
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='pending', verbose_name='状态')
    progress = models.IntegerField(default=0, verbose_name='处理进度（%）')
    processing_notes = models.TextField(blank=True, verbose_name='处理说明')
    completion_notes = models.TextField(blank=True, verbose_name='完成说明')
    attachment = models.FileField(upload_to='affairs/attachments/', null=True, blank=True, verbose_name='事务附件')
    created_by = models.ForeignKey(User, on_delete=models.PROTECT, related_name='created_affairs', verbose_name='创建人')
    created_time = models.DateTimeField(default=timezone.now, verbose_name='创建时间')
    updated_time = models.DateTimeField(auto_now=True, verbose_name='更新时间')
    
    class Meta:
        db_table = 'admin_administrative_affair'
        verbose_name = '行政事务'
        verbose_name_plural = verbose_name
        ordering = ['-created_time']
        indexes = [
            models.Index(fields=['affair_number']),
            models.Index(fields=['status', 'priority']),
            models.Index(fields=['responsible_user', 'status']),
            models.Index(fields=['planned_start_time', 'planned_end_time']),
        ]
    
    def __str__(self):
        return f"{self.affair_number} - {self.title}"
    
    def save(self, *args, **kwargs):
        if not self.affair_number:
            current_date = datetime.now()
            date_str = current_date.strftime('%Y%m%d')
            max_affair = AdministrativeAffair.objects.filter(
                affair_number__startswith=f'ADMIN-{date_str}-'
            ).aggregate(max_num=Max('affair_number'))['max_num']
            if max_affair:
                try:
                    seq = int(max_affair.split('-')[-1]) + 1
                except (ValueError, IndexError):
                    seq = 1
            else:
                seq = 1
            self.affair_number = f'ADMIN-{date_str}-{seq:04d}'
        super().save(*args, **kwargs)
    
    @property
    def is_overdue(self):
        """是否逾期"""
        if self.status in ['completed', 'cancelled']:
            return False
        if self.planned_end_time and timezone.now() > self.planned_end_time:
            return True
        return False
    
    @property
    def days_remaining(self):
        """剩余天数"""
        if self.status in ['completed', 'cancelled']:
            return 0
        if self.planned_end_time:
            delta = self.planned_end_time - timezone.now()
            return max(0, delta.days)
        return None


class AffairStatusHistory(models.Model):
    """事务状态历史记录"""
    affair = models.ForeignKey(AdministrativeAffair, on_delete=models.CASCADE, related_name='status_history', verbose_name='事务')
    old_status = models.CharField(max_length=20, blank=True, verbose_name='原状态')
    new_status = models.CharField(max_length=20, verbose_name='新状态')
    operator = models.ForeignKey(User, on_delete=models.PROTECT, related_name='affair_status_changes', verbose_name='操作人')
    operation_time = models.DateTimeField(default=timezone.now, verbose_name='操作时间')
    notes = models.TextField(blank=True, verbose_name='备注')
    
    class Meta:
        db_table = 'admin_affair_status_history'
        verbose_name = '事务状态历史'
        verbose_name_plural = verbose_name
        ordering = ['-operation_time']
    
    def __str__(self):
        return f"{self.affair.affair_number} - {self.old_status} -> {self.new_status}"


class AffairProgressRecord(models.Model):
    """事务进度记录"""
    affair = models.ForeignKey(AdministrativeAffair, on_delete=models.CASCADE, related_name='progress_records', verbose_name='事务')
    progress = models.IntegerField(verbose_name='进度（%）')
    record_time = models.DateTimeField(default=timezone.now, verbose_name='记录时间')
    recorder = models.ForeignKey(User, on_delete=models.PROTECT, related_name='affair_progress_records', verbose_name='记录人')
    notes = models.TextField(blank=True, verbose_name='进度说明')
    attachment = models.FileField(upload_to='affairs/progress/', null=True, blank=True, verbose_name='进度附件')
    
    class Meta:
        db_table = 'admin_affair_progress_record'
        verbose_name = '事务进度记录'
        verbose_name_plural = verbose_name
        ordering = ['-record_time']
    
    def __str__(self):
        return f"{self.affair.affair_number} - {self.progress}% ({self.record_time})"

