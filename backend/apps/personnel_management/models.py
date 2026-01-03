from django.db import models
from django.utils import timezone
from django.db.models import Max
from datetime import datetime
from decimal import Decimal
from backend.apps.system_management.models import User, Department


# ==================== 员工档案 ====================

class Employee(models.Model):
    """员工档案"""
    GENDER_CHOICES = [
        ('male', '男'),
        ('female', '女'),
        ('other', '其他'),
    ]
    
    STATUS_CHOICES = [
        ('active', '在职'),
        ('on_leave', '请假'),
        ('suspended', '停职'),
        ('resigned', '离职'),
    ]
    
    employee_number = models.CharField(max_length=50, unique=True, verbose_name='员工编号')
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='employee_profile', null=True, blank=True, verbose_name='系统账号')
    name = models.CharField(max_length=100, verbose_name='姓名')
    gender = models.CharField(max_length=10, choices=GENDER_CHOICES, verbose_name='性别')
    id_number = models.CharField(max_length=18, unique=True, verbose_name='身份证号')
    birthday = models.DateField(null=True, blank=True, verbose_name='出生日期')
    phone = models.CharField(max_length=20, verbose_name='手机号')
    email = models.EmailField(blank=True, verbose_name='邮箱')
    department = models.ForeignKey(Department, on_delete=models.SET_NULL, null=True, related_name='employees', verbose_name='部门')
    position = models.CharField(max_length=100, verbose_name='职位')
    job_title = models.CharField(max_length=100, blank=True, verbose_name='职称')
    entry_date = models.DateField(verbose_name='入职日期')
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='active', verbose_name='状态')
    resignation_date = models.DateField(null=True, blank=True, verbose_name='离职日期')
    address = models.CharField(max_length=500, blank=True, verbose_name='住址')
    emergency_contact = models.CharField(max_length=100, blank=True, verbose_name='紧急联系人')
    emergency_phone = models.CharField(max_length=20, blank=True, verbose_name='紧急联系电话')
    avatar = models.ImageField(upload_to='employee_avatars/', null=True, blank=True, verbose_name='头像')
    resume = models.FileField(upload_to='employee_resumes/', null=True, blank=True, verbose_name='简历')
    notes = models.TextField(blank=True, verbose_name='备注')
    created_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, related_name='created_employees', verbose_name='创建人')
    created_time = models.DateTimeField(default=timezone.now, verbose_name='创建时间')
    updated_time = models.DateTimeField(auto_now=True, verbose_name='更新时间')
    
    class Meta:
        db_table = 'personnel_employee'
        verbose_name = '员工档案'
        verbose_name_plural = verbose_name
        ordering = ['-entry_date']
        indexes = [
            models.Index(fields=['employee_number']),
            models.Index(fields=['status']),
            models.Index(fields=['department']),
        ]
    
    def __str__(self):
        return f"{self.employee_number} - {self.name}"


# ==================== 考勤管理 ====================

class Attendance(models.Model):
    """考勤记录"""
    TYPE_CHOICES = [
        ('check_in', '上班打卡'),
        ('check_out', '下班打卡'),
        ('late', '迟到'),
        ('early_leave', '早退'),
        ('absent', '缺勤'),
        ('overtime', '加班'),
    ]
    
    employee = models.ForeignKey(Employee, on_delete=models.CASCADE, related_name='attendances', verbose_name='员工')
    attendance_date = models.DateField(verbose_name='考勤日期')
    check_in_time = models.TimeField(null=True, blank=True, verbose_name='上班时间')
    check_out_time = models.TimeField(null=True, blank=True, verbose_name='下班时间')
    attendance_type = models.CharField(max_length=20, choices=TYPE_CHOICES, default='check_in', verbose_name='考勤类型')
    work_hours = models.DecimalField(max_digits=5, decimal_places=2, default=Decimal('0.00'), verbose_name='工作时长（小时）')
    overtime_hours = models.DecimalField(max_digits=5, decimal_places=2, default=Decimal('0.00'), verbose_name='加班时长（小时）')
    is_late = models.BooleanField(default=False, verbose_name='是否迟到')
    is_early_leave = models.BooleanField(default=False, verbose_name='是否早退')
    is_absent = models.BooleanField(default=False, verbose_name='是否缺勤')
    notes = models.TextField(blank=True, verbose_name='备注')
    created_time = models.DateTimeField(default=timezone.now, verbose_name='创建时间')
    
    class Meta:
        db_table = 'personnel_attendance'
        verbose_name = '考勤记录'
        verbose_name_plural = verbose_name
        ordering = ['-attendance_date', '-created_time']
        unique_together = [['employee', 'attendance_date']]
        indexes = [
            models.Index(fields=['employee', 'attendance_date']),
            models.Index(fields=['attendance_date']),
        ]
    
    def __str__(self):
        return f"{self.employee.name} - {self.attendance_date}"


# ==================== 请假管理 ====================

class Leave(models.Model):
    """请假申请"""
    TYPE_CHOICES = [
        ('annual', '年假'),
        ('sick', '病假'),
        ('personal', '事假'),
        ('marriage', '婚假'),
        ('maternity', '产假'),
        ('paternity', '陪产假'),
        ('bereavement', '丧假'),
        ('other', '其他'),
    ]
    
    STATUS_CHOICES = [
        ('draft', '草稿'),
        ('pending', '待审批'),
        ('approved', '已批准'),
        ('rejected', '已拒绝'),
        ('cancelled', '已取消'),
    ]
    
    leave_number = models.CharField(max_length=100, unique=True, verbose_name='请假单号')
    employee = models.ForeignKey(Employee, on_delete=models.CASCADE, related_name='leaves', verbose_name='员工')
    leave_type = models.CharField(max_length=20, choices=TYPE_CHOICES, verbose_name='请假类型')
    start_date = models.DateField(verbose_name='开始日期')
    end_date = models.DateField(verbose_name='结束日期')
    days = models.DecimalField(max_digits=5, decimal_places=2, verbose_name='请假天数')
    reason = models.TextField(verbose_name='请假事由')
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='draft', verbose_name='状态')
    approver = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True, related_name='approved_leaves', verbose_name='审批人')
    approved_time = models.DateTimeField(null=True, blank=True, verbose_name='审批时间')
    reject_reason = models.TextField(blank=True, verbose_name='拒绝原因')
    created_time = models.DateTimeField(default=timezone.now, verbose_name='创建时间')
    
    class Meta:
        db_table = 'personnel_leave'
        verbose_name = '请假申请'
        verbose_name_plural = verbose_name
        ordering = ['-created_time']
        indexes = [
            models.Index(fields=['leave_number']),
            models.Index(fields=['employee', 'status']),
            models.Index(fields=['start_date', 'end_date']),
        ]
    
    def __str__(self):
        return f"{self.leave_number} - {self.employee.name}"


# ==================== 培训管理 ====================

class Training(models.Model):
    """培训记录"""
    STATUS_CHOICES = [
        ('planned', '计划中'),
        ('ongoing', '进行中'),
        ('completed', '已完成'),
        ('cancelled', '已取消'),
    ]
    
    training_number = models.CharField(max_length=100, unique=True, verbose_name='培训编号')
    title = models.CharField(max_length=200, verbose_name='培训标题')
    description = models.TextField(blank=True, verbose_name='培训描述')
    trainer = models.CharField(max_length=100, blank=True, verbose_name='培训讲师')
    training_date = models.DateField(null=True, blank=True, verbose_name='培训日期')
    training_location = models.CharField(max_length=200, blank=True, verbose_name='培训地点')
    duration = models.DecimalField(max_digits=5, decimal_places=2, default=Decimal('0.00'), verbose_name='培训时长（小时）')
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='planned', verbose_name='状态')
    created_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, related_name='created_trainings', verbose_name='创建人')
    created_time = models.DateTimeField(default=timezone.now, verbose_name='创建时间')
    
    class Meta:
        db_table = 'personnel_training'
        verbose_name = '培训记录'
        verbose_name_plural = verbose_name
        ordering = ['-training_date', '-created_time']
        indexes = [
            models.Index(fields=['training_number']),
            models.Index(fields=['status']),
        ]
    
    def __str__(self):
        return f"{self.training_number} - {self.title}"


class TrainingParticipant(models.Model):
    """培训参与人员"""
    training = models.ForeignKey(Training, on_delete=models.CASCADE, related_name='participants', verbose_name='培训')
    employee = models.ForeignKey(Employee, on_delete=models.CASCADE, related_name='trainings', verbose_name='员工')
    score = models.DecimalField(max_digits=5, decimal_places=2, null=True, blank=True, verbose_name='培训成绩')
    certificate = models.FileField(upload_to='training_certificates/', null=True, blank=True, verbose_name='证书')
    notes = models.TextField(blank=True, verbose_name='备注')
    created_time = models.DateTimeField(default=timezone.now, verbose_name='参与时间')
    
    class Meta:
        db_table = 'personnel_training_participant'
        verbose_name = '培训参与人员'
        verbose_name_plural = verbose_name
        unique_together = [['training', 'employee']]
    
    def __str__(self):
        return f"{self.training.title} - {self.employee.name}"


# ==================== 绩效考核 ====================

class Performance(models.Model):
    """绩效考核"""
    PERIOD_CHOICES = [
        ('monthly', '月度'),
        ('quarterly', '季度'),
        ('semi_annual', '半年度'),
        ('annual', '年度'),
    ]
    
    STATUS_CHOICES = [
        ('draft', '草稿'),
        ('self_assessment', '自评中'),
        ('manager_review', '上级评价中'),
        ('hr_review', 'HR审核中'),
        ('completed', '已完成'),
    ]
    
    performance_number = models.CharField(max_length=100, unique=True, verbose_name='考核编号')
    employee = models.ForeignKey(Employee, on_delete=models.CASCADE, related_name='performances', verbose_name='员工')
    period_type = models.CharField(max_length=20, choices=PERIOD_CHOICES, verbose_name='考核周期')
    period_year = models.IntegerField(verbose_name='考核年度')
    period_quarter = models.IntegerField(null=True, blank=True, verbose_name='考核季度')
    period_month = models.IntegerField(null=True, blank=True, verbose_name='考核月份')
    total_score = models.DecimalField(max_digits=5, decimal_places=2, null=True, blank=True, verbose_name='总分')
    level = models.CharField(max_length=20, blank=True, verbose_name='考核等级')
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='draft', verbose_name='状态')
    self_assessment = models.TextField(blank=True, verbose_name='自评')
    manager_comment = models.TextField(blank=True, verbose_name='上级评价')
    hr_comment = models.TextField(blank=True, verbose_name='HR评价')
    reviewer = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True, related_name='reviewed_performances', verbose_name='评价人')
    reviewed_time = models.DateTimeField(null=True, blank=True, verbose_name='评价时间')
    created_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, related_name='created_performances', verbose_name='创建人')
    created_time = models.DateTimeField(default=timezone.now, verbose_name='创建时间')
    
    class Meta:
        db_table = 'personnel_performance'
        verbose_name = '绩效考核'
        verbose_name_plural = verbose_name
        ordering = ['-period_year', '-created_time']
        indexes = [
            models.Index(fields=['performance_number']),
            models.Index(fields=['employee', 'period_year']),
            models.Index(fields=['status']),
        ]
    
    def __str__(self):
        return f"{self.performance_number} - {self.employee.name}"


# ==================== 薪资管理 ====================

class Salary(models.Model):
    """薪资记录"""
    employee = models.ForeignKey(Employee, on_delete=models.CASCADE, related_name='salaries', verbose_name='员工')
    salary_month = models.DateField(verbose_name='薪资月份')
    base_salary = models.DecimalField(max_digits=10, decimal_places=2, verbose_name='基本工资')
    performance_bonus = models.DecimalField(max_digits=10, decimal_places=2, default=Decimal('0.00'), verbose_name='绩效奖金')
    overtime_pay = models.DecimalField(max_digits=10, decimal_places=2, default=Decimal('0.00'), verbose_name='加班费')
    allowance = models.DecimalField(max_digits=10, decimal_places=2, default=Decimal('0.00'), verbose_name='津贴补贴')
    total_income = models.DecimalField(max_digits=10, decimal_places=2, verbose_name='应发金额')
    social_insurance = models.DecimalField(max_digits=10, decimal_places=2, default=Decimal('0.00'), verbose_name='社保扣款')
    housing_fund = models.DecimalField(max_digits=10, decimal_places=2, default=Decimal('0.00'), verbose_name='公积金扣款')
    tax = models.DecimalField(max_digits=10, decimal_places=2, default=Decimal('0.00'), verbose_name='个人所得税')
    other_deduction = models.DecimalField(max_digits=10, decimal_places=2, default=Decimal('0.00'), verbose_name='其他扣款')
    total_deduction = models.DecimalField(max_digits=10, decimal_places=2, default=Decimal('0.00'), verbose_name='扣款合计')
    net_salary = models.DecimalField(max_digits=10, decimal_places=2, verbose_name='实发金额')
    notes = models.TextField(blank=True, verbose_name='备注')
    created_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, related_name='created_salaries', verbose_name='创建人')
    created_time = models.DateTimeField(default=timezone.now, verbose_name='创建时间')
    
    class Meta:
        db_table = 'personnel_salary'
        verbose_name = '薪资记录'
        verbose_name_plural = verbose_name
        ordering = ['-salary_month']
        unique_together = [['employee', 'salary_month']]
        indexes = [
            models.Index(fields=['employee', 'salary_month']),
            models.Index(fields=['salary_month']),
        ]
    
    def __str__(self):
        return f"{self.employee.name} - {self.salary_month.strftime('%Y-%m')}"


# ==================== 劳动合同 ====================

class LaborContract(models.Model):
    """劳动合同"""
    TYPE_CHOICES = [
        ('fixed_term', '固定期限'),
        ('open_term', '无固定期限'),
        ('project_based', '以完成一定工作任务为期限'),
    ]
    
    STATUS_CHOICES = [
        ('draft', '草稿'),
        ('active', '生效中'),
        ('expired', '已到期'),
        ('terminated', '已终止'),
    ]
    
    contract_number = models.CharField(max_length=100, unique=True, verbose_name='合同编号')
    employee = models.ForeignKey(Employee, on_delete=models.CASCADE, related_name='contracts', verbose_name='员工')
    contract_type = models.CharField(max_length=20, choices=TYPE_CHOICES, verbose_name='合同类型')
    start_date = models.DateField(verbose_name='合同开始日期')
    end_date = models.DateField(null=True, blank=True, verbose_name='合同结束日期')
    probation_period = models.IntegerField(default=0, verbose_name='试用期（月）')
    base_salary = models.DecimalField(max_digits=10, decimal_places=2, verbose_name='基本工资')
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='draft', verbose_name='状态')
    contract_file = models.FileField(upload_to='labor_contracts/', null=True, blank=True, verbose_name='合同文件')
    termination_date = models.DateField(null=True, blank=True, verbose_name='终止日期')
    termination_reason = models.TextField(blank=True, verbose_name='终止原因')
    notes = models.TextField(blank=True, verbose_name='备注')
    created_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, related_name='created_labor_contracts', verbose_name='创建人')
    created_time = models.DateTimeField(default=timezone.now, verbose_name='创建时间')
    
    class Meta:
        db_table = 'personnel_labor_contract'
        verbose_name = '劳动合同'
        verbose_name_plural = verbose_name
        ordering = ['-created_time']
        indexes = [
            models.Index(fields=['contract_number']),
            models.Index(fields=['employee', 'status']),
            models.Index(fields=['start_date', 'end_date']),
        ]
    
    def __str__(self):
        return f"{self.contract_number} - {self.employee.name}"


# ==================== 职位管理 ====================

class Position(models.Model):
    """职位"""
    name = models.CharField(max_length=100, verbose_name='职位名称')
    code = models.CharField(max_length=50, unique=True, verbose_name='职位编码')
    department = models.ForeignKey(Department, on_delete=models.CASCADE, related_name='positions', verbose_name='所属部门')
    level = models.IntegerField(default=1, verbose_name='职位级别')
    description = models.TextField(blank=True, verbose_name='职位描述')
    requirements = models.TextField(blank=True, verbose_name='任职要求')
    min_salary = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True, verbose_name='最低薪资')
    max_salary = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True, verbose_name='最高薪资')
    is_active = models.BooleanField(default=True, verbose_name='是否启用')
    created_time = models.DateTimeField(default=timezone.now, verbose_name='创建时间')
    updated_time = models.DateTimeField(auto_now=True, verbose_name='更新时间')
    
    class Meta:
        db_table = 'personnel_position'
        verbose_name = '职位'
        verbose_name_plural = verbose_name
        ordering = ['department', 'level', 'name']
        indexes = [
            models.Index(fields=['code']),
            models.Index(fields=['department']),
            models.Index(fields=['is_active']),
        ]
    
    def __str__(self):
        return f"{self.name} ({self.department.name})"
    
    @property
    def employee_count(self):
        """获取该职位的员工数量"""
        return Employee.objects.filter(position=self.name, department=self.department, status='active').count()


# ==================== 员工档案管理 ====================

class EmployeeArchive(models.Model):
    """员工档案文件"""
    CATEGORY_CHOICES = [
        ('id_card', '身份证'),
        ('education', '学历证书'),
        ('qualification', '资格证书'),
        ('certificate', '证书'),
        ('license', '执照'),
        ('contract', '劳动合同'),
        ('health_report', '体检报告'),
        ('other', '其他'),
    ]
    
    employee = models.ForeignKey(Employee, on_delete=models.CASCADE, related_name='archives', verbose_name='员工')
    category = models.CharField(max_length=50, choices=CATEGORY_CHOICES, verbose_name='档案分类')
    file_name = models.CharField(max_length=255, verbose_name='文件名称')
    file = models.FileField(upload_to='employee_archives/%Y/%m/', verbose_name='档案文件')
    file_size = models.BigIntegerField(verbose_name='文件大小（字节）')
    description = models.TextField(blank=True, verbose_name='档案描述')
    expiry_date = models.DateField(null=True, blank=True, verbose_name='到期日期')
    is_archived = models.BooleanField(default=False, verbose_name='是否归档')
    created_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, related_name='created_employee_archives', verbose_name='创建人')
    created_time = models.DateTimeField(default=timezone.now, verbose_name='创建时间')
    updated_time = models.DateTimeField(auto_now=True, verbose_name='更新时间')
    
    class Meta:
        db_table = 'personnel_employee_archive'
        verbose_name = '员工档案文件'
        verbose_name_plural = verbose_name
        ordering = ['-created_time']
        indexes = [
            models.Index(fields=['employee', 'category']),
            models.Index(fields=['category']),
            models.Index(fields=['expiry_date']),
        ]
    
    def __str__(self):
        return f"{self.employee.name} - {self.get_category_display()} - {self.file_name}"
    
    def save(self, *args, **kwargs):
        if self.file and not self.file_size:
            self.file_size = self.file.size
        super().save(*args, **kwargs)


# ==================== 员工异动管理 ====================

class EmployeeMovement(models.Model):
    """员工异动记录"""
    MOVEMENT_TYPE_CHOICES = [
        ('entry', '入职'),
        ('transfer', '调岗'),
        ('promotion', '晋升'),
        ('demotion', '降职'),
        ('resignation', '离职'),
        ('suspension', '停职'),
        ('reinstatement', '复职'),
        ('other', '其他'),
    ]
    
    STATUS_CHOICES = [
        ('pending', '待审批'),
        ('approved', '已批准'),
        ('rejected', '已拒绝'),
        ('completed', '已完成'),
    ]
    
    movement_number = models.CharField(max_length=50, unique=True, verbose_name='异动编号')
    employee = models.ForeignKey(Employee, on_delete=models.CASCADE, related_name='movements', verbose_name='员工')
    movement_type = models.CharField(max_length=20, choices=MOVEMENT_TYPE_CHOICES, verbose_name='异动类型')
    movement_date = models.DateField(verbose_name='异动日期')
    
    # 异动前信息
    old_department = models.ForeignKey(Department, on_delete=models.SET_NULL, null=True, blank=True, related_name='old_movements', verbose_name='原部门')
    old_position = models.CharField(max_length=100, blank=True, verbose_name='原职位')
    old_salary = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True, verbose_name='原薪资')
    
    # 异动后信息
    new_department = models.ForeignKey(Department, on_delete=models.SET_NULL, null=True, blank=True, related_name='new_movements', verbose_name='新部门')
    new_position = models.CharField(max_length=100, blank=True, verbose_name='新职位')
    new_salary = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True, verbose_name='新薪资')
    
    reason = models.TextField(verbose_name='异动原因')
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='pending', verbose_name='状态')
    approver = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True, related_name='approved_movements', verbose_name='审批人')
    approval_time = models.DateTimeField(null=True, blank=True, verbose_name='审批时间')
    approval_comment = models.TextField(blank=True, verbose_name='审批意见')
    
    created_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, related_name='created_movements', verbose_name='创建人')
    created_time = models.DateTimeField(default=timezone.now, verbose_name='创建时间')
    updated_time = models.DateTimeField(auto_now=True, verbose_name='更新时间')
    
    class Meta:
        db_table = 'personnel_employee_movement'
        verbose_name = '员工异动记录'
        verbose_name_plural = verbose_name
        ordering = ['-movement_date', '-created_time']
        indexes = [
            models.Index(fields=['employee', 'movement_date']),
            models.Index(fields=['movement_type']),
            models.Index(fields=['status']),
            models.Index(fields=['movement_date']),
        ]
    
    def __str__(self):
        return f"{self.movement_number} - {self.employee.name} - {self.get_movement_type_display()}"
    
    def save(self, *args, **kwargs):
        if not self.movement_number:
            # 生成异动编号
            today = timezone.now().date()
            prefix = f"MOV{today.strftime('%Y%m%d')}"
            last_movement = EmployeeMovement.objects.filter(movement_number__startswith=prefix).order_by('-movement_number').first()
            if last_movement:
                last_num = int(last_movement.movement_number[-4:])
                new_num = last_num + 1
            else:
                new_num = 1
            self.movement_number = f"{prefix}{new_num:04d}"
        super().save(*args, **kwargs)


# ==================== 福利管理 ====================

class WelfareProject(models.Model):
    """福利项目"""
    TYPE_CHOICES = [
        ('holiday', '节日福利'),
        ('birthday', '生日福利'),
        ('health', '健康福利'),
        ('training', '培训福利'),
        ('travel', '旅游福利'),
        ('meal', '餐饮福利'),
        ('housing', '住房福利'),
        ('other', '其他'),
    ]
    
    CYCLE_CHOICES = [
        ('once', '一次性'),
        ('monthly', '每月'),
        ('quarterly', '每季度'),
        ('yearly', '每年'),
    ]
    
    name = models.CharField(max_length=100, verbose_name='福利项目名称')
    welfare_type = models.CharField(max_length=20, choices=TYPE_CHOICES, verbose_name='福利类型')
    standard = models.TextField(verbose_name='福利标准')
    target_employees = models.TextField(blank=True, verbose_name='福利对象描述')
    cycle = models.CharField(max_length=20, choices=CYCLE_CHOICES, default='once', verbose_name='福利周期')
    is_active = models.BooleanField(default=True, verbose_name='是否启用')
    created_time = models.DateTimeField(default=timezone.now, verbose_name='创建时间')
    updated_time = models.DateTimeField(auto_now=True, verbose_name='更新时间')
    
    class Meta:
        db_table = 'personnel_welfare_project'
        verbose_name = '福利项目'
        verbose_name_plural = verbose_name
        ordering = ['-created_time']
    
    def __str__(self):
        return self.name


class WelfareDistribution(models.Model):
    """福利发放记录"""
    PAYMENT_METHOD_CHOICES = [
        ('cash', '现金'),
        ('bank_transfer', '银行转账'),
        ('voucher', '代金券'),
        ('goods', '实物'),
        ('other', '其他'),
    ]
    
    welfare_project = models.ForeignKey(WelfareProject, on_delete=models.CASCADE, related_name='distributions', verbose_name='福利项目')
    employee = models.ForeignKey(Employee, on_delete=models.CASCADE, related_name='welfare_distributions', verbose_name='员工')
    distribution_date = models.DateField(verbose_name='发放日期')
    amount = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True, verbose_name='发放金额')
    payment_method = models.CharField(max_length=20, choices=PAYMENT_METHOD_CHOICES, default='cash', verbose_name='发放方式')
    description = models.TextField(blank=True, verbose_name='发放说明')
    created_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, related_name='created_welfare_distributions', verbose_name='创建人')
    created_time = models.DateTimeField(default=timezone.now, verbose_name='创建时间')
    
    class Meta:
        db_table = 'personnel_welfare_distribution'
        verbose_name = '福利发放记录'
        verbose_name_plural = verbose_name
        ordering = ['-distribution_date', '-created_time']
        indexes = [
            models.Index(fields=['welfare_project', 'distribution_date']),
            models.Index(fields=['employee', 'distribution_date']),
        ]
    
    def __str__(self):
        return f"{self.welfare_project.name} - {self.employee.name} - {self.distribution_date}"


# ==================== 招聘管理 ====================

class RecruitmentRequirement(models.Model):
    """招聘需求"""
    STATUS_CHOICES = [
        ('draft', '草稿'),
        ('pending', '待审批'),
        ('approved', '已批准'),
        ('recruiting', '招聘中'),
        ('completed', '已完成'),
        ('cancelled', '已取消'),
    ]
    
    requirement_number = models.CharField(max_length=50, unique=True, verbose_name='需求编号')
    department = models.ForeignKey(Department, on_delete=models.CASCADE, related_name='recruitment_requirements', verbose_name='需求部门')
    position = models.CharField(max_length=100, verbose_name='需求职位')
    required_count = models.IntegerField(verbose_name='需求人数')
    requirements = models.TextField(verbose_name='岗位要求')
    salary_range_min = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True, verbose_name='薪资范围（最低）')
    salary_range_max = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True, verbose_name='薪资范围（最高）')
    reason = models.TextField(verbose_name='需求原因')
    publish_date = models.DateField(null=True, blank=True, verbose_name='发布日期')
    deadline = models.DateField(null=True, blank=True, verbose_name='截止日期')
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='draft', verbose_name='状态')
    approver = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True, related_name='approved_recruitment_requirements', verbose_name='审批人')
    approval_time = models.DateTimeField(null=True, blank=True, verbose_name='审批时间')
    approval_comment = models.TextField(blank=True, verbose_name='审批意见')
    created_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, related_name='created_recruitment_requirements', verbose_name='创建人')
    created_time = models.DateTimeField(default=timezone.now, verbose_name='创建时间')
    updated_time = models.DateTimeField(auto_now=True, verbose_name='更新时间')
    
    class Meta:
        db_table = 'personnel_recruitment_requirement'
        verbose_name = '招聘需求'
        verbose_name_plural = verbose_name
        ordering = ['-created_time']
        indexes = [
            models.Index(fields=['department', 'status']),
            models.Index(fields=['status']),
            models.Index(fields=['publish_date']),
        ]
    
    def __str__(self):
        return f"{self.requirement_number} - {self.position} - {self.department.name}"
    
    def save(self, *args, **kwargs):
        if not self.requirement_number:
            # 生成需求编号
            today = timezone.now().date()
            prefix = f"REQ{today.strftime('%Y%m%d')}"
            last_req = RecruitmentRequirement.objects.filter(requirement_number__startswith=prefix).order_by('-requirement_number').first()
            if last_req:
                last_num = int(last_req.requirement_number[-4:])
                new_num = last_num + 1
            else:
                new_num = 1
            self.requirement_number = f"{prefix}{new_num:04d}"
        super().save(*args, **kwargs)


class Resume(models.Model):
    """简历"""
    STATUS_CHOICES = [
        ('pending', '待处理'),
        ('screened', '已筛选'),
        ('interview', '待面试'),
        ('rejected', '已淘汰'),
        ('hired', '已录用'),
    ]
    
    resume_number = models.CharField(max_length=50, unique=True, verbose_name='简历编号')
    recruitment_requirement = models.ForeignKey(RecruitmentRequirement, on_delete=models.CASCADE, related_name='resumes', verbose_name='招聘需求')
    name = models.CharField(max_length=100, verbose_name='姓名')
    gender = models.CharField(max_length=10, choices=Employee.GENDER_CHOICES, verbose_name='性别')
    phone = models.CharField(max_length=20, verbose_name='手机号')
    email = models.EmailField(blank=True, verbose_name='邮箱')
    education = models.CharField(max_length=50, blank=True, verbose_name='学历')
    work_experience = models.IntegerField(default=0, verbose_name='工作经验（年）')
    resume_file = models.FileField(upload_to='resumes/%Y/%m/', verbose_name='简历文件')
    source = models.CharField(max_length=100, blank=True, verbose_name='简历来源')
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='pending', verbose_name='状态')
    notes = models.TextField(blank=True, verbose_name='备注')
    created_time = models.DateTimeField(default=timezone.now, verbose_name='创建时间')
    updated_time = models.DateTimeField(auto_now=True, verbose_name='更新时间')
    
    class Meta:
        db_table = 'personnel_resume'
        verbose_name = '简历'
        verbose_name_plural = verbose_name
        ordering = ['-created_time']
        indexes = [
            models.Index(fields=['recruitment_requirement', 'status']),
            models.Index(fields=['status']),
        ]
    
    def __str__(self):
        return f"{self.resume_number} - {self.name}"
    
    def save(self, *args, **kwargs):
        if not self.resume_number:
            # 生成简历编号
            today = timezone.now().date()
            prefix = f"RES{today.strftime('%Y%m%d')}"
            last_resume = Resume.objects.filter(resume_number__startswith=prefix).order_by('-resume_number').first()
            if last_resume:
                last_num = int(last_resume.resume_number[-4:])
                new_num = last_num + 1
            else:
                new_num = 1
            self.resume_number = f"{prefix}{new_num:04d}"
        super().save(*args, **kwargs)


class Interview(models.Model):
    """面试记录"""
    STATUS_CHOICES = [
        ('scheduled', '已安排'),
        ('completed', '已完成'),
        ('cancelled', '已取消'),
    ]
    
    RESULT_CHOICES = [
        ('pass', '通过'),
        ('fail', '未通过'),
        ('pending', '待定'),
    ]
    
    interview_number = models.CharField(max_length=50, unique=True, verbose_name='面试编号')
    resume = models.ForeignKey(Resume, on_delete=models.CASCADE, related_name='interviews', verbose_name='简历')
    interviewer = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, related_name='conducted_interviews', verbose_name='面试官')
    interview_date = models.DateTimeField(verbose_name='面试时间')
    interview_location = models.CharField(max_length=200, blank=True, verbose_name='面试地点')
    interview_method = models.CharField(max_length=50, default='onsite', verbose_name='面试方式')  # onsite, online, phone
    evaluation = models.TextField(blank=True, verbose_name='面试评价')
    result = models.CharField(max_length=20, choices=RESULT_CHOICES, blank=True, verbose_name='面试结果')
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='scheduled', verbose_name='状态')
    created_time = models.DateTimeField(default=timezone.now, verbose_name='创建时间')
    updated_time = models.DateTimeField(auto_now=True, verbose_name='更新时间')
    
    class Meta:
        db_table = 'personnel_interview'
        verbose_name = '面试记录'
        verbose_name_plural = verbose_name
        ordering = ['-interview_date']
        indexes = [
            models.Index(fields=['resume', 'interview_date']),
            models.Index(fields=['interviewer', 'interview_date']),
        ]
    
    def __str__(self):
        return f"{self.interview_number} - {self.resume.name}"
    
    def save(self, *args, **kwargs):
        if not self.interview_number:
            # 生成面试编号
            today = timezone.now().date()
            prefix = f"INT{today.strftime('%Y%m%d')}"
            last_interview = Interview.objects.filter(interview_number__startswith=prefix).order_by('-interview_number').first()
            if last_interview:
                last_num = int(last_interview.interview_number[-4:])
                new_num = last_num + 1
            else:
                new_num = 1
            self.interview_number = f"{prefix}{new_num:04d}"
        super().save(*args, **kwargs)


# ==================== 员工关系管理 ====================

class EmployeeCommunication(models.Model):
    """员工沟通记录"""
    METHOD_CHOICES = [
        ('online', '线上'),
        ('offline', '线下'),
        ('anonymous', '匿名'),
    ]
    
    employee = models.ForeignKey(Employee, on_delete=models.CASCADE, related_name='communications', verbose_name='员工')
    subject = models.CharField(max_length=200, verbose_name='沟通主题')
    communication_date = models.DateTimeField(verbose_name='沟通时间')
    content = models.TextField(verbose_name='沟通内容')
    method = models.CharField(max_length=20, choices=METHOD_CHOICES, default='offline', verbose_name='沟通方式')
    feedback = models.TextField(blank=True, verbose_name='员工反馈')
    result = models.TextField(blank=True, verbose_name='处理结果')
    created_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, related_name='created_communications', verbose_name='创建人')
    created_time = models.DateTimeField(default=timezone.now, verbose_name='创建时间')
    
    class Meta:
        db_table = 'personnel_employee_communication'
        verbose_name = '员工沟通记录'
        verbose_name_plural = verbose_name
        ordering = ['-communication_date']
        indexes = [
            models.Index(fields=['employee', 'communication_date']),
        ]
    
    def __str__(self):
        return f"{self.employee.name} - {self.subject}"


class EmployeeCare(models.Model):
    """员工关怀记录"""
    CARE_TYPE_CHOICES = [
        ('birthday', '生日关怀'),
        ('holiday', '节日关怀'),
        ('difficulty', '困难关怀'),
        ('achievement', '成就关怀'),
        ('other', '其他'),
    ]
    
    employee = models.ForeignKey(Employee, on_delete=models.CASCADE, related_name='cares', verbose_name='员工')
    care_type = models.CharField(max_length=20, choices=CARE_TYPE_CHOICES, verbose_name='关怀类型')
    care_date = models.DateField(verbose_name='关怀日期')
    content = models.TextField(verbose_name='关怀内容')
    created_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, related_name='created_cares', verbose_name='创建人')
    created_time = models.DateTimeField(default=timezone.now, verbose_name='创建时间')
    
    class Meta:
        db_table = 'personnel_employee_care'
        verbose_name = '员工关怀记录'
        verbose_name_plural = verbose_name
        ordering = ['-care_date']
        indexes = [
            models.Index(fields=['employee', 'care_date']),
            models.Index(fields=['care_type']),
        ]
    
    def __str__(self):
        return f"{self.employee.name} - {self.get_care_type_display()} - {self.care_date}"


class EmployeeActivity(models.Model):
    """员工活动"""
    STATUS_CHOICES = [
        ('planning', '策划中'),
        ('registration', '报名中'),
        ('ongoing', '进行中'),
        ('completed', '已完成'),
        ('cancelled', '已取消'),
    ]
    
    activity_number = models.CharField(max_length=50, unique=True, verbose_name='活动编号')
    title = models.CharField(max_length=200, verbose_name='活动主题')
    activity_date = models.DateTimeField(verbose_name='活动时间')
    location = models.CharField(max_length=200, blank=True, verbose_name='活动地点')
    max_participants = models.IntegerField(null=True, blank=True, verbose_name='最大参与人数')
    budget = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True, verbose_name='活动预算')
    description = models.TextField(verbose_name='活动描述')
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='planning', verbose_name='状态')
    created_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, related_name='created_activities', verbose_name='创建人')
    created_time = models.DateTimeField(default=timezone.now, verbose_name='创建时间')
    updated_time = models.DateTimeField(auto_now=True, verbose_name='更新时间')
    
    class Meta:
        db_table = 'personnel_employee_activity'
        verbose_name = '员工活动'
        verbose_name_plural = verbose_name
        ordering = ['-activity_date']
        indexes = [
            models.Index(fields=['status', 'activity_date']),
        ]
    
    def __str__(self):
        return f"{self.activity_number} - {self.title}"
    
    def save(self, *args, **kwargs):
        if not self.activity_number:
            # 生成活动编号
            today = timezone.now().date()
            prefix = f"ACT{today.strftime('%Y%m%d')}"
            last_activity = EmployeeActivity.objects.filter(activity_number__startswith=prefix).order_by('-activity_number').first()
            if last_activity:
                last_num = int(last_activity.activity_number[-4:])
                new_num = last_num + 1
            else:
                new_num = 1
            self.activity_number = f"{prefix}{new_num:04d}"
        super().save(*args, **kwargs)
    
    @property
    def participant_count(self):
        """获取参与人数"""
        return self.activity_participants.count()


class ActivityParticipant(models.Model):
    """活动参与记录"""
    activity = models.ForeignKey(EmployeeActivity, on_delete=models.CASCADE, related_name='activity_participants', verbose_name='活动')
    employee = models.ForeignKey(Employee, on_delete=models.CASCADE, related_name='participated_activities', verbose_name='员工')
    signed_in = models.BooleanField(default=False, verbose_name='是否签到')
    signed_in_time = models.DateTimeField(null=True, blank=True, verbose_name='签到时间')
    feedback = models.TextField(blank=True, verbose_name='活动反馈')
    created_time = models.DateTimeField(default=timezone.now, verbose_name='报名时间')
    
    class Meta:
        db_table = 'personnel_activity_participant'
        verbose_name = '活动参与记录'
        verbose_name_plural = verbose_name
        unique_together = [['activity', 'employee']]
        indexes = [
            models.Index(fields=['activity', 'employee']),
        ]
    
    def __str__(self):
        return f"{self.activity.title} - {self.employee.name}"


class EmployeeComplaint(models.Model):
    """员工投诉"""
    STATUS_CHOICES = [
        ('pending', '待处理'),
        ('processing', '处理中'),
        ('resolved', '已解决'),
        ('closed', '已关闭'),
    ]
    
    complaint_number = models.CharField(max_length=50, unique=True, verbose_name='投诉编号')
    employee = models.ForeignKey(Employee, on_delete=models.CASCADE, related_name='complaints', verbose_name='投诉人')
    complaint_date = models.DateTimeField(verbose_name='投诉时间')
    content = models.TextField(verbose_name='投诉内容')
    complaint_type = models.CharField(max_length=100, blank=True, verbose_name='投诉类型')
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='pending', verbose_name='状态')
    handler = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True, related_name='handled_complaints', verbose_name='处理人')
    handling_result = models.TextField(blank=True, verbose_name='处理结果')
    handled_time = models.DateTimeField(null=True, blank=True, verbose_name='处理时间')
    created_time = models.DateTimeField(default=timezone.now, verbose_name='创建时间')
    updated_time = models.DateTimeField(auto_now=True, verbose_name='更新时间')
    
    class Meta:
        db_table = 'personnel_employee_complaint'
        verbose_name = '员工投诉'
        verbose_name_plural = verbose_name
        ordering = ['-complaint_date']
        indexes = [
            models.Index(fields=['employee', 'complaint_date']),
            models.Index(fields=['status']),
        ]
    
    def __str__(self):
        return f"{self.complaint_number} - {self.employee.name}"
    
    def save(self, *args, **kwargs):
        if not self.complaint_number:
            # 生成投诉编号
            today = timezone.now().date()
            prefix = f"COM{today.strftime('%Y%m%d')}"
            last_complaint = EmployeeComplaint.objects.filter(complaint_number__startswith=prefix).order_by('-complaint_number').first()
            if last_complaint:
                last_num = int(last_complaint.complaint_number[-4:])
                new_num = last_num + 1
            else:
                new_num = 1
            self.complaint_number = f"{prefix}{new_num:04d}"
        super().save(*args, **kwargs)


class EmployeeSuggestion(models.Model):
    """员工建议"""
    STATUS_CHOICES = [
        ('pending', '待处理'),
        ('reviewing', '审核中'),
        ('adopted', '已采纳'),
        ('rejected', '已拒绝'),
    ]
    
    suggestion_number = models.CharField(max_length=50, unique=True, verbose_name='建议编号')
    employee = models.ForeignKey(Employee, on_delete=models.CASCADE, related_name='suggestions', verbose_name='建议人')
    suggestion_date = models.DateTimeField(verbose_name='建议时间')
    content = models.TextField(verbose_name='建议内容')
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='pending', verbose_name='状态')
    reviewer = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True, related_name='reviewed_suggestions', verbose_name='审核人')
    review_result = models.TextField(blank=True, verbose_name='审核结果')
    is_adopted = models.BooleanField(default=False, verbose_name='是否采纳')
    reward = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True, verbose_name='奖励金额')
    reviewed_time = models.DateTimeField(null=True, blank=True, verbose_name='审核时间')
    created_time = models.DateTimeField(default=timezone.now, verbose_name='创建时间')
    updated_time = models.DateTimeField(auto_now=True, verbose_name='更新时间')
    
    class Meta:
        db_table = 'personnel_employee_suggestion'
        verbose_name = '员工建议'
        verbose_name_plural = verbose_name
        ordering = ['-suggestion_date']
        indexes = [
            models.Index(fields=['employee', 'suggestion_date']),
            models.Index(fields=['status']),
        ]
    
    def __str__(self):
        return f"{self.suggestion_number} - {self.employee.name}"
    
    def save(self, *args, **kwargs):
        if not self.suggestion_number:
            # 生成建议编号
            today = timezone.now().date()
            prefix = f"SUG{today.strftime('%Y%m%d')}"
            last_suggestion = EmployeeSuggestion.objects.filter(suggestion_number__startswith=prefix).order_by('-suggestion_number').first()
            if last_suggestion:
                last_num = int(last_suggestion.suggestion_number[-4:])
                new_num = last_num + 1
            else:
                new_num = 1
            self.suggestion_number = f"{prefix}{new_num:04d}"
        super().save(*args, **kwargs)

