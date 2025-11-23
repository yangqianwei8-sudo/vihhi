from django import forms
from .models import (
    Employee, Attendance, Leave, Training, Performance, Salary, LaborContract
)
from backend.apps.system_management.models import Department, User


class EmployeeForm(forms.ModelForm):
    """员工档案表单"""
    
    class Meta:
        model = Employee
        fields = [
            'name', 'gender', 'id_number', 'birthday', 'phone', 'email',
            'department', 'position', 'job_title', 'entry_date', 'status',
            'resignation_date', 'address', 'emergency_contact', 'emergency_phone',
            'avatar', 'resume', 'notes', 'user'
        ]
        widgets = {
            'name': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': '请输入姓名'
            }),
            'gender': forms.Select(attrs={'class': 'form-select'}),
            'id_number': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': '18位身份证号',
                'maxlength': '18'
            }),
            'birthday': forms.DateInput(attrs={
                'class': 'form-control',
                'type': 'date'
            }),
            'phone': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': '手机号'
            }),
            'email': forms.EmailInput(attrs={
                'class': 'form-control',
                'placeholder': '邮箱地址'
            }),
            'department': forms.Select(attrs={'class': 'form-select'}),
            'position': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': '职位'
            }),
            'job_title': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': '职称'
            }),
            'entry_date': forms.DateInput(attrs={
                'class': 'form-control',
                'type': 'date'
            }),
            'status': forms.Select(attrs={'class': 'form-select'}),
            'resignation_date': forms.DateInput(attrs={
                'class': 'form-control',
                'type': 'date'
            }),
            'address': forms.Textarea(attrs={
                'class': 'form-control',
                'rows': 2,
                'placeholder': '住址'
            }),
            'emergency_contact': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': '紧急联系人姓名'
            }),
            'emergency_phone': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': '紧急联系电话'
            }),
            'avatar': forms.FileInput(attrs={
                'class': 'form-control',
                'accept': 'image/*'
            }),
            'resume': forms.FileInput(attrs={
                'class': 'form-control',
                'accept': '.pdf,.doc,.docx'
            }),
            'notes': forms.Textarea(attrs={
                'class': 'form-control',
                'rows': 3,
                'placeholder': '备注信息'
            }),
            'user': forms.Select(attrs={'class': 'form-select'}),
        }
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # 动态加载部门和用户
        self.fields['department'].queryset = Department.objects.filter(is_active=True).order_by('name')
        self.fields['user'].queryset = User.objects.filter(is_active=True).order_by('username')
        self.fields['user'].required = False
        self.fields['resignation_date'].required = False
        self.fields['birthday'].required = False


class LeaveForm(forms.ModelForm):
    """请假申请表单"""
    
    class Meta:
        model = Leave
        fields = [
            'employee', 'leave_type', 'start_date', 'end_date', 'days', 'reason'
        ]
        widgets = {
            'employee': forms.Select(attrs={'class': 'form-select'}),
            'leave_type': forms.Select(attrs={'class': 'form-select'}),
            'start_date': forms.DateInput(attrs={
                'class': 'form-control',
                'type': 'date'
            }),
            'end_date': forms.DateInput(attrs={
                'class': 'form-control',
                'type': 'date'
            }),
            'days': forms.NumberInput(attrs={
                'class': 'form-control',
                'step': '0.5',
                'placeholder': '请假天数'
            }),
            'reason': forms.Textarea(attrs={
                'class': 'form-control',
                'rows': 4,
                'placeholder': '请假事由'
            }),
        }
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['employee'].queryset = Employee.objects.filter(status='active').order_by('name')


class TrainingForm(forms.ModelForm):
    """培训记录表单"""
    
    class Meta:
        model = Training
        fields = [
            'title', 'description', 'trainer', 'training_date', 'training_location',
            'duration', 'status'
        ]
        widgets = {
            'title': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': '培训标题'
            }),
            'description': forms.Textarea(attrs={
                'class': 'form-control',
                'rows': 4,
                'placeholder': '培训描述'
            }),
            'trainer': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': '培训讲师'
            }),
            'training_date': forms.DateInput(attrs={
                'class': 'form-control',
                'type': 'date'
            }),
            'training_location': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': '培训地点'
            }),
            'duration': forms.NumberInput(attrs={
                'class': 'form-control',
                'step': '0.5',
                'placeholder': '培训时长（小时）'
            }),
            'status': forms.Select(attrs={'class': 'form-select'}),
        }


class PerformanceForm(forms.ModelForm):
    """绩效考核表单"""
    
    class Meta:
        model = Performance
        fields = [
            'employee', 'period_type', 'period_year', 'period_quarter', 'period_month',
            'self_assessment', 'manager_comment', 'hr_comment', 'status', 'reviewer'
        ]
        widgets = {
            'employee': forms.Select(attrs={'class': 'form-select'}),
            'period_type': forms.Select(attrs={'class': 'form-select'}),
            'period_year': forms.NumberInput(attrs={
                'class': 'form-control',
                'placeholder': '年度，如：2025'
            }),
            'period_quarter': forms.NumberInput(attrs={
                'class': 'form-control',
                'min': 1,
                'max': 4,
                'placeholder': '季度（1-4）'
            }),
            'period_month': forms.NumberInput(attrs={
                'class': 'form-control',
                'min': 1,
                'max': 12,
                'placeholder': '月份（1-12）'
            }),
            'self_assessment': forms.Textarea(attrs={
                'class': 'form-control',
                'rows': 5,
                'placeholder': '员工自评'
            }),
            'manager_comment': forms.Textarea(attrs={
                'class': 'form-control',
                'rows': 5,
                'placeholder': '上级评价'
            }),
            'hr_comment': forms.Textarea(attrs={
                'class': 'form-control',
                'rows': 5,
                'placeholder': 'HR评价'
            }),
            'status': forms.Select(attrs={'class': 'form-select'}),
            'reviewer': forms.Select(attrs={'class': 'form-select'}),
        }
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['employee'].queryset = Employee.objects.filter(status='active').order_by('name')
        self.fields['reviewer'].queryset = User.objects.filter(is_active=True).order_by('username')
        self.fields['reviewer'].required = False
        self.fields['period_quarter'].required = False
        self.fields['period_month'].required = False


class SalaryForm(forms.ModelForm):
    """薪资记录表单"""
    
    class Meta:
        model = Salary
        fields = [
            'employee', 'salary_month', 'base_salary', 'performance_bonus',
            'overtime_pay', 'allowance', 'social_insurance', 'housing_fund',
            'tax', 'other_deduction', 'notes'
        ]
        widgets = {
            'employee': forms.Select(attrs={'class': 'form-select'}),
            'salary_month': forms.DateInput(attrs={
                'class': 'form-control',
                'type': 'month'
            }),
            'base_salary': forms.NumberInput(attrs={
                'class': 'form-control',
                'step': '0.01',
                'placeholder': '基本工资'
            }),
            'performance_bonus': forms.NumberInput(attrs={
                'class': 'form-control',
                'step': '0.01',
                'placeholder': '绩效奖金'
            }),
            'overtime_pay': forms.NumberInput(attrs={
                'class': 'form-control',
                'step': '0.01',
                'placeholder': '加班费'
            }),
            'allowance': forms.NumberInput(attrs={
                'class': 'form-control',
                'step': '0.01',
                'placeholder': '津贴补贴'
            }),
            'social_insurance': forms.NumberInput(attrs={
                'class': 'form-control',
                'step': '0.01',
                'placeholder': '社保扣除'
            }),
            'housing_fund': forms.NumberInput(attrs={
                'class': 'form-control',
                'step': '0.01',
                'placeholder': '公积金扣除'
            }),
            'tax': forms.NumberInput(attrs={
                'class': 'form-control',
                'step': '0.01',
                'placeholder': '个人所得税'
            }),
            'other_deduction': forms.NumberInput(attrs={
                'class': 'form-control',
                'step': '0.01',
                'placeholder': '其他扣款'
            }),
            'notes': forms.Textarea(attrs={
                'class': 'form-control',
                'rows': 3,
                'placeholder': '备注'
            }),
        }
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['employee'].queryset = Employee.objects.filter(status='active').order_by('name')


class LaborContractForm(forms.ModelForm):
    """劳动合同表单"""
    
    class Meta:
        model = LaborContract
        fields = [
            'employee', 'contract_type', 'start_date', 'end_date',
            'probation_period', 'base_salary', 'contract_file', 'notes'
        ]
        widgets = {
            'employee': forms.Select(attrs={'class': 'form-select'}),
            'contract_type': forms.Select(attrs={'class': 'form-select'}),
            'start_date': forms.DateInput(attrs={
                'class': 'form-control',
                'type': 'date'
            }),
            'end_date': forms.DateInput(attrs={
                'class': 'form-control',
                'type': 'date'
            }),
            'probation_period': forms.NumberInput(attrs={
                'class': 'form-control',
                'min': 0,
                'placeholder': '试用期（月）'
            }),
            'base_salary': forms.NumberInput(attrs={
                'class': 'form-control',
                'step': '0.01',
                'placeholder': '基本工资'
            }),
            'contract_file': forms.FileInput(attrs={
                'class': 'form-control',
                'accept': '.pdf,.doc,.docx'
            }),
            'notes': forms.Textarea(attrs={
                'class': 'form-control',
                'rows': 3,
                'placeholder': '备注'
            }),
        }
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['employee'].queryset = Employee.objects.filter(status='active').order_by('name')
        self.fields['end_date'].required = False


class AttendanceForm(forms.ModelForm):
    """考勤记录表单"""
    
    class Meta:
        model = Attendance
        fields = [
            'employee', 'attendance_date', 'check_in_time', 'check_out_time',
            'is_late', 'is_early_leave', 'is_absent', 'overtime_hours', 'notes'
        ]
        widgets = {
            'employee': forms.Select(attrs={'class': 'form-select'}),
            'attendance_date': forms.DateInput(attrs={
                'class': 'form-control',
                'type': 'date'
            }),
            'check_in_time': forms.TimeInput(attrs={
                'class': 'form-control',
                'type': 'time'
            }),
            'check_out_time': forms.TimeInput(attrs={
                'class': 'form-control',
                'type': 'time'
            }),
            'is_late': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
            'is_early_leave': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
            'is_absent': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
            'overtime_hours': forms.NumberInput(attrs={
                'class': 'form-control',
                'step': '0.5',
                'placeholder': '加班时长（小时）'
            }),
            'notes': forms.Textarea(attrs={
                'class': 'form-control',
                'rows': 3,
                'placeholder': '备注'
            }),
        }
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['employee'].queryset = Employee.objects.filter(status='active').order_by('name')

