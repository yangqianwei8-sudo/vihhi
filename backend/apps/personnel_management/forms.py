from django import forms
from datetime import date
from backend.apps.personnel_management.models import (
    Employee, Attendance, Leave, Training, Performance, Salary, LaborContract,
    EmployeeMovement, EmployeeArchive, WelfareProject, WelfareDistribution,
    RecruitmentRequirement, Resume, Interview,
    EmployeeCommunication, EmployeeCare, EmployeeActivity,
    EmployeeComplaint, EmployeeSuggestion
)
from backend.apps.system_management.models import Department, User


def set_date_fields_default_today(form_instance):
    """
    为表单中所有日期字段设置默认值为当天
    仅在新建时（没有instance.pk）设置默认值
    """
    if form_instance.instance and form_instance.instance.pk:
        return  # 编辑时，不设置默认值
    
    today = date.today()
    for field_name, field in form_instance.fields.items():
        # 检查是否是日期输入字段
        if isinstance(field.widget, forms.DateInput):
            # 如果字段还没有初始值，设置为今天
            if field_name not in form_instance.initial:
                form_instance.fields[field_name].initial = today


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
        
        # 新建时，设置日期字段默认值为当天
        set_date_fields_default_today(self)


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
        
        # 新建时，设置日期字段默认值为当天
        set_date_fields_default_today(self)
        
        # 新建时，设置日期字段默认值为当天
        set_date_fields_default_today(self)


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
        
        # 新建时，设置日期字段默认值为当天
        set_date_fields_default_today(self)
        
        # 新建时，设置日期字段默认值为当天
        set_date_fields_default_today(self)
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
        
        # 新建时，设置日期字段默认值为当天
        set_date_fields_default_today(self)
        
        # 新建时，设置日期字段默认值为当天
        set_date_fields_default_today(self)


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
        
        # 新建时，设置日期字段默认值为当天
        set_date_fields_default_today(self)
        
        # 新建时，设置日期字段默认值为当天
        set_date_fields_default_today(self)
        self.fields['end_date'].required = False
        
        # 新建时，设置日期字段默认值为当天
        set_date_fields_default_today(self)


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
        
        # 新建时，设置日期字段默认值为当天
        set_date_fields_default_today(self)
        
        # 新建时，设置日期字段默认值为当天
        set_date_fields_default_today(self)


class EmployeeMovementForm(forms.ModelForm):
    """员工异动表单"""
    
    class Meta:
        model = EmployeeMovement
        fields = [
            'employee', 'movement_type', 'movement_date',
            'old_department', 'old_position', 'old_salary',
            'new_department', 'new_position', 'new_salary',
            'reason'
        ]
        widgets = {
            'employee': forms.Select(attrs={'class': 'form-select'}),
            'movement_type': forms.Select(attrs={'class': 'form-select'}),
            'movement_date': forms.DateInput(attrs={
                'class': 'form-control',
                'type': 'date'
            }),
            'old_department': forms.Select(attrs={'class': 'form-select'}),
            'old_position': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': '原职位'
            }),
            'old_salary': forms.NumberInput(attrs={
                'class': 'form-control',
                'step': '0.01',
                'placeholder': '原薪资'
            }),
            'new_department': forms.Select(attrs={'class': 'form-select'}),
            'new_position': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': '新职位'
            }),
            'new_salary': forms.NumberInput(attrs={
                'class': 'form-control',
                'step': '0.01',
                'placeholder': '新薪资'
            }),
            'reason': forms.Textarea(attrs={
                'class': 'form-control',
                'rows': 4,
                'placeholder': '异动原因'
            }),
        }
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['employee'].queryset = Employee.objects.filter(status__in=['active', 'suspended']).order_by('name')
        self.fields['old_department'].queryset = Department.objects.filter(is_active=True).order_by('name')
        self.fields['new_department'].queryset = Department.objects.filter(is_active=True).order_by('name')
        self.fields['old_department'].required = False
        self.fields['old_position'].required = False
        self.fields['old_salary'].required = False
        self.fields['new_department'].required = False
        
        # 新建时，设置日期字段默认值为当天
        set_date_fields_default_today(self)
        self.fields['new_position'].required = False
        self.fields['new_salary'].required = False


class EmployeeArchiveForm(forms.ModelForm):
    """员工档案文件表单"""
    
    class Meta:
        model = EmployeeArchive
        fields = [
            'employee', 'category', 'file', 'file_name', 'description', 'expiry_date'
        ]
        widgets = {
            'employee': forms.Select(attrs={'class': 'form-select'}),
            'category': forms.Select(attrs={'class': 'form-select'}),
            'file': forms.FileInput(attrs={
                'class': 'form-control',
                'accept': '.pdf,.doc,.docx,.jpg,.jpeg,.png'
            }),
            'file_name': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': '文件名称（可选，默认使用上传文件名）'
            }),
            'description': forms.Textarea(attrs={
                'class': 'form-control',
                'rows': 3,
                'placeholder': '档案描述'
            }),
            'expiry_date': forms.DateInput(attrs={
                'class': 'form-control',
                'type': 'date'
            }),
        }
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['employee'].queryset = Employee.objects.filter(status__in=['active', 'suspended']).order_by('name')
        self.fields['file_name'].required = False
        self.fields['description'].required = False
        self.fields['expiry_date'].required = False
        
        # 新建时，设置日期字段默认值为当天
        set_date_fields_default_today(self)
    
    def clean_file(self):
        file = self.cleaned_data.get('file')
        if file:
            # 限制文件大小（50MB）
            if file.size > 50 * 1024 * 1024:
                raise forms.ValidationError('文件大小不能超过50MB')
        return file
    
    def save(self, commit=True):
        archive = super().save(commit=False)
        if archive.file:
            # 如果没有指定文件名称，使用上传的文件名
            if not archive.file_name:
                archive.file_name = archive.file.name.split('/')[-1]
            # 自动设置文件大小
            archive.file_size = archive.file.size
        if commit:
            archive.save()
        return archive


class WelfareDistributionForm(forms.ModelForm):
    """福利发放表单"""
    
    class Meta:
        model = WelfareDistribution
        fields = [
            'welfare_project', 'employee', 'distribution_date',
            'amount', 'payment_method', 'description'
        ]
        widgets = {
            'welfare_project': forms.Select(attrs={'class': 'form-select'}),
            'employee': forms.Select(attrs={'class': 'form-select'}),
            'distribution_date': forms.DateInput(attrs={
                'class': 'form-control',
                'type': 'date'
            }),
            'amount': forms.NumberInput(attrs={
                'class': 'form-control',
                'step': '0.01',
                'placeholder': '发放金额'
            }),
            'payment_method': forms.Select(attrs={'class': 'form-select'}),
            'description': forms.Textarea(attrs={
                'class': 'form-control',
                'rows': 3,
                'placeholder': '发放说明'
            }),
        }
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['welfare_project'].queryset = WelfareProject.objects.filter(is_active=True).order_by('name')
        self.fields['employee'].queryset = Employee.objects.filter(status='active').order_by('name')
        self.fields['amount'].required = False
        self.fields['description'].required = False
        
        # 新建时，设置日期字段默认值为当天
        set_date_fields_default_today(self)


class RecruitmentRequirementForm(forms.ModelForm):
    """招聘需求表单"""
    
    class Meta:
        model = RecruitmentRequirement
        fields = [
            'department', 'position', 'required_count', 'requirements',
            'salary_range_min', 'salary_range_max', 'reason',
            'publish_date', 'deadline', 'status'
        ]
        widgets = {
            'department': forms.Select(attrs={'class': 'form-select'}),
            'position': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': '需求职位'
            }),
            'required_count': forms.NumberInput(attrs={
                'class': 'form-control',
                'min': 1,
                'placeholder': '需求人数'
            }),
            'requirements': forms.Textarea(attrs={
                'class': 'form-control',
                'rows': 5,
                'placeholder': '岗位要求'
            }),
            'salary_range_min': forms.NumberInput(attrs={
                'class': 'form-control',
                'step': '0.01',
                'placeholder': '最低薪资'
            }),
            'salary_range_max': forms.NumberInput(attrs={
                'class': 'form-control',
                'step': '0.01',
                'placeholder': '最高薪资'
            }),
            'reason': forms.Textarea(attrs={
                'class': 'form-control',
                'rows': 4,
                'placeholder': '需求原因'
            }),
            'publish_date': forms.DateInput(attrs={
                'class': 'form-control',
                'type': 'date'
            }),
            'deadline': forms.DateInput(attrs={
                'class': 'form-control',
                'type': 'date'
            }),
            'status': forms.Select(attrs={'class': 'form-select'}),
        }
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['department'].queryset = Department.objects.filter(is_active=True).order_by('name')
        self.fields['salary_range_min'].required = False
        self.fields['salary_range_max'].required = False
        self.fields['publish_date'].required = False
        
        # 新建时，设置日期字段默认值为当天
        set_date_fields_default_today(self)
        self.fields['deadline'].required = False


class WelfareProjectForm(forms.ModelForm):
    """福利项目表单"""
    
    class Meta:
        model = WelfareProject
        fields = [
            'name', 'welfare_type', 'standard', 'target_employees',
            'cycle', 'is_active'
        ]
        widgets = {
            'name': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': '福利项目名称'
            }),
            'welfare_type': forms.Select(attrs={'class': 'form-select'}),
            'standard': forms.Textarea(attrs={
                'class': 'form-control',
                'rows': 4,
                'placeholder': '福利标准'
            }),
            'target_employees': forms.Textarea(attrs={
                'class': 'form-control',
                'rows': 3,
                'placeholder': '福利对象描述（可选）'
            }),
            'cycle': forms.Select(attrs={'class': 'form-select'}),
            'is_active': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
        }
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['target_employees'].required = False
        
        # 新建时，设置日期字段默认值为当天
        set_date_fields_default_today(self)


class ResumeForm(forms.ModelForm):
    """简历表单"""
    
    class Meta:
        model = Resume
        fields = [
            'recruitment_requirement', 'name', 'gender', 'phone', 'email',
            'education', 'work_experience', 'resume_file', 'source', 'status', 'notes'
        ]
        widgets = {
            'recruitment_requirement': forms.Select(attrs={'class': 'form-select'}),
            'name': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': '姓名'
            }),
            'gender': forms.Select(attrs={'class': 'form-select'}),
            'phone': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': '手机号'
            }),
            'email': forms.EmailInput(attrs={
                'class': 'form-control',
                'placeholder': '邮箱（可选）'
            }),
            'education': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': '学历（可选）'
            }),
            'work_experience': forms.NumberInput(attrs={
                'class': 'form-control',
                'min': 0,
                'placeholder': '工作经验（年）'
            }),
            'resume_file': forms.FileInput(attrs={
                'class': 'form-control',
                'accept': '.pdf,.doc,.docx'
            }),
            'source': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': '简历来源（可选）'
            }),
            'status': forms.Select(attrs={'class': 'form-select'}),
            'notes': forms.Textarea(attrs={
                'class': 'form-control',
                'rows': 3,
                'placeholder': '备注（可选）'
            }),
        }
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['recruitment_requirement'].queryset = RecruitmentRequirement.objects.filter(
            status__in=['approved', 'recruiting']
        ).order_by('-created_time')
        self.fields['email'].required = False
        self.fields['education'].required = False
        
        # 新建时，设置日期字段默认值为当天
        set_date_fields_default_today(self)
        self.fields['source'].required = False
        self.fields['notes'].required = False


class InterviewForm(forms.ModelForm):
    """面试表单"""
    
    class Meta:
        model = Interview
        fields = [
            'resume', 'interviewer', 'interview_date', 'interview_location',
            'interview_method', 'evaluation', 'result', 'status'
        ]
        widgets = {
            'resume': forms.Select(attrs={'class': 'form-select'}),
            'interviewer': forms.Select(attrs={'class': 'form-select'}),
            'interview_date': forms.DateTimeInput(attrs={
                'class': 'form-control',
                'type': 'datetime-local'
            }),
            'interview_location': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': '面试地点（可选）'
            }),
            'interview_method': forms.Select(attrs={'class': 'form-select'}),
            'evaluation': forms.Textarea(attrs={
                'class': 'form-control',
                'rows': 5,
                'placeholder': '面试评价（可选）'
            }),
            'result': forms.Select(attrs={'class': 'form-select'}),
            'status': forms.Select(attrs={'class': 'form-select'}),
        }
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['resume'].queryset = Resume.objects.filter(
            status__in=['screened', 'interview']
        ).order_by('-created_time')
        self.fields['interviewer'].queryset = User.objects.filter(is_active=True).order_by('username')
        
        # 新建时，设置日期字段默认值为当天
        set_date_fields_default_today(self)
        self.fields['interview_location'].required = False
        self.fields['evaluation'].required = False
        self.fields['result'].required = False


class EmployeeCommunicationForm(forms.ModelForm):
    """员工沟通记录表单"""
    
    class Meta:
        model = EmployeeCommunication
        fields = [
            'employee', 'subject', 'communication_date', 'content',
            'method', 'feedback', 'result'
        ]
        widgets = {
            'employee': forms.Select(attrs={'class': 'form-select'}),
            'subject': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': '沟通主题'
            }),
            'communication_date': forms.DateTimeInput(attrs={
                'class': 'form-control',
                'type': 'datetime-local'
            }),
            'content': forms.Textarea(attrs={
                'class': 'form-control',
                'rows': 5,
                'placeholder': '沟通内容'
            }),
            'method': forms.Select(attrs={'class': 'form-select'}),
            'feedback': forms.Textarea(attrs={
                'class': 'form-control',
                'rows': 3,
                'placeholder': '员工反馈（可选）'
            }),
            'result': forms.Textarea(attrs={
                'class': 'form-control',
                'rows': 3,
                'placeholder': '处理结果（可选）'
            }),
        }
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['employee'].queryset = Employee.objects.filter(status='active').order_by('name')
        
        # 新建时，设置日期字段默认值为当天
        set_date_fields_default_today(self)
        
        # 新建时，设置日期字段默认值为当天
        set_date_fields_default_today(self)
        self.fields['feedback'].required = False
        self.fields['result'].required = False


class EmployeeCareForm(forms.ModelForm):
    """员工关怀记录表单"""
    
    class Meta:
        model = EmployeeCare
        fields = [
            'employee', 'care_type', 'care_date', 'content'
        ]
        widgets = {
            'employee': forms.Select(attrs={'class': 'form-select'}),
            'care_type': forms.Select(attrs={'class': 'form-select'}),
            'care_date': forms.DateInput(attrs={
                'class': 'form-control',
                'type': 'date'
            }),
            'content': forms.Textarea(attrs={
                'class': 'form-control',
                'rows': 5,
                'placeholder': '关怀内容'
            }),
        }
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['employee'].queryset = Employee.objects.filter(status='active').order_by('name')
        
        # 新建时，设置日期字段默认值为当天
        set_date_fields_default_today(self)
        
        # 新建时，设置日期字段默认值为当天
        set_date_fields_default_today(self)


class EmployeeActivityForm(forms.ModelForm):
    """员工活动表单"""
    
    class Meta:
        model = EmployeeActivity
        fields = [
            'title', 'activity_date', 'location', 'max_participants',
            'budget', 'description', 'status'
        ]
        widgets = {
            'title': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': '活动主题'
            }),
            'activity_date': forms.DateTimeInput(attrs={
                'class': 'form-control',
                'type': 'datetime-local'
            }),
            'location': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': '活动地点（可选）'
            }),
            'max_participants': forms.NumberInput(attrs={
                'class': 'form-control',
                'min': 1,
                'placeholder': '最大参与人数（可选）'
            }),
            'budget': forms.NumberInput(attrs={
                'class': 'form-control',
                'step': '0.01',
                'placeholder': '活动预算（可选）'
            }),
            'description': forms.Textarea(attrs={
                'class': 'form-control',
                'rows': 5,
                'placeholder': '活动描述'
            }),
            'status': forms.Select(attrs={'class': 'form-select'}),
        }
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['location'].required = False
        self.fields['max_participants'].required = False
        self.fields['budget'].required = False
        
        # 新建时，设置日期字段默认值为当天
        set_date_fields_default_today(self)


class EmployeeComplaintForm(forms.ModelForm):
    """员工投诉表单"""
    
    class Meta:
        model = EmployeeComplaint
        fields = [
            'employee', 'complaint_date', 'content', 'complaint_type', 'status'
        ]
        widgets = {
            'employee': forms.Select(attrs={'class': 'form-select'}),
            'complaint_date': forms.DateInput(attrs={
                'class': 'form-control',
                'type': 'date'
            }),
            'content': forms.Textarea(attrs={
                'class': 'form-control',
                'rows': 6,
                'placeholder': '投诉内容'
            }),
            'complaint_type': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': '投诉类型（可选）'
            }),
            'status': forms.Select(attrs={'class': 'form-select'}),
        }
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['employee'].queryset = Employee.objects.filter(status='active').order_by('name')
        self.fields['complaint_type'].required = False
        
        # 如果是编辑，将datetime字段转换为date显示
        if self.instance and self.instance.pk and self.instance.complaint_date:
            self.fields['complaint_date'].initial = self.instance.complaint_date.date()
        else:
            # 新建时，设置日期字段默认值为当天
            set_date_fields_default_today(self)
    
    def clean(self):
        cleaned_data = super().clean()
        complaint_date = cleaned_data.get('complaint_date')
        
        # 将日期转换为datetime（设置为当天的开始时间 00:00:00）
        if complaint_date:
            from django.utils import timezone
            from datetime import datetime
            if isinstance(complaint_date, datetime):
                # 如果已经是datetime，只保留日期部分，时间设为00:00:00
                cleaned_data['complaint_date'] = datetime.combine(complaint_date.date(), datetime.min.time())
                cleaned_data['complaint_date'] = timezone.make_aware(cleaned_data['complaint_date'])
            elif hasattr(complaint_date, 'date'):
                # 如果是date对象，转换为datetime
                cleaned_data['complaint_date'] = datetime.combine(complaint_date, datetime.min.time())
                cleaned_data['complaint_date'] = timezone.make_aware(cleaned_data['complaint_date'])
        
        return cleaned_data


class EmployeeSuggestionForm(forms.ModelForm):
    """员工建议表单"""
    
    class Meta:
        model = EmployeeSuggestion
        fields = [
            'employee', 'suggestion_date', 'content', 'status'
        ]
        widgets = {
            'employee': forms.Select(attrs={'class': 'form-select'}),
            'suggestion_date': forms.DateInput(attrs={
                'class': 'form-control',
                'type': 'date'
            }),
            'content': forms.Textarea(attrs={
                'class': 'form-control',
                'rows': 6,
                'placeholder': '建议内容'
            }),
            'status': forms.Select(attrs={'class': 'form-select'}),
        }
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['employee'].queryset = Employee.objects.filter(status='active').order_by('name')
        
        # 如果是编辑，将datetime字段转换为date显示
        if self.instance and self.instance.pk and self.instance.suggestion_date:
            self.fields['suggestion_date'].initial = self.instance.suggestion_date.date()
        else:
            # 新建时，设置日期字段默认值为当天
            set_date_fields_default_today(self)
    
    def clean(self):
        cleaned_data = super().clean()
        suggestion_date = cleaned_data.get('suggestion_date')
        
        # 将日期转换为datetime（设置为当天的开始时间 00:00:00）
        if suggestion_date:
            from django.utils import timezone
            from datetime import datetime
            if isinstance(suggestion_date, datetime):
                # 如果已经是datetime，只保留日期部分，时间设为00:00:00
                cleaned_data['suggestion_date'] = datetime.combine(suggestion_date.date(), datetime.min.time())
                cleaned_data['suggestion_date'] = timezone.make_aware(cleaned_data['suggestion_date'])
            elif hasattr(suggestion_date, 'date'):
                # 如果是date对象，转换为datetime
                cleaned_data['suggestion_date'] = datetime.combine(suggestion_date, datetime.min.time())
                cleaned_data['suggestion_date'] = timezone.make_aware(cleaned_data['suggestion_date'])
        
        return cleaned_data

