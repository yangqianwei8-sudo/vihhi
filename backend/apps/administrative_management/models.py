from django.db import models
from django.utils import timezone
from django.db.models import Max
from datetime import datetime
from backend.apps.system_management.models import User, Department


# ==================== 办公用品管理 ====================

class OfficeSupply(models.Model):
    """办公用品"""
    CATEGORY_CHOICES = [
        ('consumable', '消耗品'),
        ('fixed_asset', '固定资产'),
        ('low_value', '低值易耗品'),
    ]
    
    code = models.CharField(max_length=50, unique=True, verbose_name='用品编码')
    name = models.CharField(max_length=200, verbose_name='用品名称')
    category = models.CharField(max_length=20, choices=CATEGORY_CHOICES, default='consumable', verbose_name='分类')
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
    supplier = models.CharField(max_length=200, verbose_name='供应商')
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
    gifts_exchanged = models.TextField(blank=True, verbose_name='礼品交换情况')
    outcome = models.TextField(blank=True, verbose_name='接待结果/成果')
    notes = models.TextField(blank=True, verbose_name='备注')
    created_by = models.ForeignKey(User, on_delete=models.PROTECT, related_name='created_receptions', verbose_name='创建人')
    created_time = models.DateTimeField(default=timezone.now, verbose_name='创建时间')
    
    class Meta:
        db_table = 'admin_reception_record'
        verbose_name = '接待记录'
        verbose_name_plural = verbose_name
        ordering = ['-reception_date', '-reception_time']
        indexes = [
            models.Index(fields=['reception_date', 'host']),
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


class ReceptionExpense(models.Model):
    """接待费用"""
    EXPENSE_TYPE_CHOICES = [
        ('catering', '餐饮'),
        ('accommodation', '住宿'),
        ('transport', '交通'),
        ('gift', '礼品'),
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

