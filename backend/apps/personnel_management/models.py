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

