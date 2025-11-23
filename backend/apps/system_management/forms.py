from django import forms
from django.contrib.auth import get_user_model

from .models import RegistrationRequest, Department, Role


CONSULTING_UNIT_POSITIONS = [
    ('综合办', [
        ('consulting_general_manager', '总经理'),
        ('consulting_admin_supervisor', '行政主管'),
        ('consulting_finance_supervisor', '财务主管'),
    ]),
    ('商务部', [
        ('consulting_commerce_manager', '商务部经理'),
        ('consulting_business_manager', '商务经理'),
        ('consulting_business_assistant', '商务助理'),
    ]),
    ('技术部', [
        ('consulting_technical_manager', '技术部经理'),
        ('consulting_project_manager', '项目经理'),
        ('consulting_professional_lead', '专业负责人'),
        ('consulting_professional_engineer', '专业工程师'),
        ('consulting_technical_assistant', '技术助理'),
    ]),
    ('造价部', [
        ('consulting_cost_manager', '造价部经理'),
        ('consulting_civil_auditor', '土建审核人'),
        ('consulting_install_auditor', '安装审核人'),
        ('consulting_civil_cost_engineer', '土建造价师'),
        ('consulting_install_cost_engineer', '安装造价师'),
    ]),
    ('合作技术', [
        ('consulting_partner_professional_lead', '专业负责人'),
        ('consulting_partner_professional_engineer', '专业工程师'),
    ]),
    ('合作造价', [
        ('consulting_partner_civil_auditor', '土建审核人'),
        ('consulting_partner_install_auditor', '安装审核人'),
        ('consulting_partner_civil_cost_engineer', '土建造价师'),
        ('consulting_partner_install_cost_engineer', '安装造价师'),
    ]),
]

COMMISSION_UNIT_POSITIONS = [
    ('委托单位', [
        ('commission_professional_engineer', '专业工程师'),
        ('commission_professional_lead', '专业负责人'),
        ('commission_project_lead', '项目负责人'),
    ]),
]

DESIGN_UNIT_POSITIONS = [
    ('设计单位', [
        ('design_professional_engineer', '专业工程师'),
        ('design_professional_lead', '专业负责人'),
        ('design_project_lead', '项目负责人'),
    ]),
]

CONTROL_UNIT_POSITIONS = [
    ('过控单位', [
        ('control_civil_auditor', '土建审核人'),
        ('control_install_auditor', '安装审核人'),
        ('control_project_lead', '项目负责人'),
    ]),
]

SERVICE_CATEGORY_CHOICES = [
    ('internal', '咨询单位'),
    ('client_owner', '委托单位'),
    ('design_partner', '设计单位'),
    ('control_partner', '过控单位'),
]

SERVICE_CATEGORY_CLIENT_TYPE = {
    'internal': 'service_provider',
    'client_owner': 'client_owner',
    'design_partner': 'design_partner',
    'control_partner': 'control_partner',
}

POSITION_CHOICES = {
    'internal': CONSULTING_UNIT_POSITIONS,
    'service_provider': CONSULTING_UNIT_POSITIONS,
    'client_owner': COMMISSION_UNIT_POSITIONS,
    'design_partner': DESIGN_UNIT_POSITIONS,
    'control_partner': CONTROL_UNIT_POSITIONS,
}

CONSULTING_GROUP_LOOKUP = {
    group_label: [value for value, _ in group_options]
    for group_label, group_options in CONSULTING_UNIT_POSITIONS
}

def flatten_position_choices(choices):
    flat = []
    for entry in choices:
        if isinstance(entry, (tuple, list)) and len(entry) == 2 and isinstance(entry[1], (list, tuple)):
            _, group_options = entry
            for value, label in group_options:
                flat.append((value, label))
        else:
            value, label = entry
            flat.append((value, label))
    return flat


POSITION_LOOKUP = {
    key: dict(flatten_position_choices(value))
    for key, value in POSITION_CHOICES.items()
}

# Mapping from position code to role code
POSITION_ROLE_MAP = {
    'consulting_general_manager': 'general_manager',
    'consulting_admin_supervisor': 'admin_office',
    'consulting_finance_supervisor': 'finance_supervisor',
    'consulting_commerce_manager': 'business_team',
    'consulting_business_manager': 'business_team',
    'consulting_business_assistant': 'business_assistant',
    'consulting_technical_manager': 'technical_manager',
    'consulting_project_manager': 'project_manager',
    'consulting_professional_lead': 'professional_lead',
    'consulting_professional_engineer': 'professional_engineer',
    'consulting_technical_assistant': 'technical_assistant',
    'consulting_cost_manager': 'cost_team',
    'consulting_civil_auditor': 'cost_auditor',
    'consulting_install_auditor': 'cost_auditor',
    'consulting_civil_cost_engineer': 'cost_engineer',
    'consulting_install_cost_engineer': 'cost_engineer',
    'consulting_partner_professional_lead': 'professional_lead',
    'consulting_partner_professional_engineer': 'professional_engineer',
    'consulting_partner_civil_auditor': 'cost_auditor',
    'consulting_partner_install_auditor': 'cost_auditor',
    'consulting_partner_civil_cost_engineer': 'cost_engineer',
    'consulting_partner_install_cost_engineer': 'cost_engineer',
    'commission_professional_engineer': 'client_engineer',
    'commission_professional_lead': 'client_professional_lead',
    'commission_project_lead': 'client_project_lead',
    'design_professional_engineer': 'design_engineer',
    'design_professional_lead': 'design_professional_lead',
    'design_project_lead': 'design_project_lead',
    'control_civil_auditor': 'control_civil_auditor',
    'control_install_auditor': 'control_install_auditor',
    'control_project_lead': 'control_project_lead',
}


class RegistrationRequestForm(forms.ModelForm):
    password = forms.CharField(
        label='登录密码',
        widget=forms.PasswordInput(attrs={'class': 'form-control', 'placeholder': '请输入密码'}),
        min_length=6,
        max_length=128,
    )
    confirm_password = forms.CharField(
        label='确认密码',
        widget=forms.PasswordInput(attrs={'class': 'form-control', 'placeholder': '请再次输入密码'}),
        min_length=6,
        max_length=128,
    )

    class Meta:
        model = RegistrationRequest
        fields = [
            'phone',
            'client_type',
        ]
        widgets = {
            'phone': forms.TextInput(attrs={'class': 'form-control', 'placeholder': '请输入常用手机号'}),
            'client_type': forms.Select(attrs={'class': 'form-select'}),
        }

    def clean_phone(self):
        phone = self.cleaned_data['phone']
        User = get_user_model()
        if User.objects.filter(username=phone).exists() or User.objects.filter(phone=phone).exists():
            raise forms.ValidationError('该手机号已注册，请直接登录或联系管理员。')
        if RegistrationRequest.objects.filter(phone=phone, status=RegistrationRequest.STATUS_PENDING).exists():
            raise forms.ValidationError('该手机号的注册申请正在审核中，请勿重复提交。')
        return phone

    def clean(self):
        cleaned_data = super().clean()
        password = cleaned_data.get('password')
        confirm = cleaned_data.get('confirm_password')
        if password and confirm and password != confirm:
            self.add_error('confirm_password', '两次输入的密码不一致')
        return cleaned_data

    def save(self, commit=True):
        instance = super().save(commit=False)
        phone = self.cleaned_data['phone']
        instance.username = phone
        instance.phone = phone
        if commit:
            instance.save()
        return instance


class RegistrationAuditForm(forms.Form):
    status = forms.ChoiceField(
        choices=[
            (RegistrationRequest.STATUS_APPROVED, '批准'),
            (RegistrationRequest.STATUS_REJECTED, '拒绝'),
        ],
        widget=forms.RadioSelect,
        label='审核结果',
    )
    feedback = forms.CharField(
        label='审核意见',
        widget=forms.Textarea(attrs={'class': 'form-control', 'rows': 3}),
        required=False,
    )


class ProfileCompletionForm(forms.Form):
    full_name = forms.CharField(
        label='姓名',
        max_length=100,
        widget=forms.TextInput(attrs={'class': 'form-control', 'placeholder': '请输入姓名'})
    )
    email = forms.EmailField(
        label='邮箱',
        widget=forms.EmailInput(attrs={'class': 'form-control', 'placeholder': '请输入邮箱'})
    )
    service_category = forms.ChoiceField(
        label='服务端类别',
        choices=SERVICE_CATEGORY_CHOICES,
        widget=forms.Select(attrs={'class': 'form-select'})
    )
    position = forms.ChoiceField(label='职责')

    def __init__(self, *args, **kwargs):
        self.user = kwargs.pop('user')
        super().__init__(*args, **kwargs)

        category_from_data = self.data.get('service_category') if self.data else None
        category_from_initial = kwargs.get('initial', {}).get('service_category') if kwargs.get('initial') else None
        user_category = self.user.user_type or 'internal'
        service_category = category_from_data or category_from_initial or user_category

        self.fields['service_category'].initial = service_category

        choices = POSITION_CHOICES.get(service_category, CONSULTING_UNIT_POSITIONS)
        self.fields['position'].widget = forms.Select(attrs={'class': 'form-select'})
        self.fields['position'].choices = choices
        flat_choices = POSITION_LOOKUP.get(service_category, POSITION_LOOKUP.get('internal', {}))

        if service_category == 'internal':
            self.fields['department'] = forms.ModelChoiceField(
                label='部门',
                queryset=Department.objects.filter(is_active=True).order_by('order', 'name'),
                widget=forms.Select(attrs={'class': 'form-select'})
            )
        else:
            self.fields['department'] = forms.ModelChoiceField(
                queryset=Department.objects.none(),
                required=False
            )
            self.fields['department'].widget = forms.HiddenInput()

        # 初始化数据
        self.initial.setdefault('full_name', self.user.get_full_name() or '')
        self.initial.setdefault('email', self.user.email or '')
        self.initial.setdefault('service_category', service_category)
        # 如果已有岗位，反向匹配选项
        existing_position = self.user.position
        if existing_position:
            for code, label in flat_choices.items():
                if existing_position == label:
                    self.initial.setdefault('position', code)
                    break
        if 'position' not in self.initial or not self.initial['position']:
            default_code = next(iter(flat_choices.keys()), '')
            if default_code:
                self.initial['position'] = default_code
        if self.user.department_id and 'department' in self.fields:
            self.initial.setdefault('department', self.user.department_id)

    def clean_email(self):
        email = self.cleaned_data['email']
        User = get_user_model()
        qs = User.objects.filter(email=email)
        if self.user.pk:
            qs = qs.exclude(pk=self.user.pk)
        if qs.exists():
            raise forms.ValidationError('该邮箱已被其他账户使用，请更换。')
        return email

    def save(self):
        position_code = self.cleaned_data['position']
        category = self.cleaned_data['service_category']
        position_label = POSITION_LOOKUP.get(category, POSITION_LOOKUP.get('internal', {})).get(position_code, position_code)

        self.user.first_name = self.cleaned_data['full_name']
        self.user.email = self.cleaned_data['email']
        self.user.position = position_label
        self.user.user_type = category
        self.user.client_type = SERVICE_CATEGORY_CLIENT_TYPE.get(category, 'service_provider')
        if category == 'internal':
            self.user.department = self.cleaned_data['department']
        else:
            self.user.department = None
        self.user.profile_completed = True
        self.user.save()
        role_code = POSITION_ROLE_MAP.get(position_code)
        if role_code:
            role = Role.objects.filter(code=role_code, is_active=True).first()
            if role:
                self.user.roles.set([role])
        return self.user

    def get_service_options(self):
        result = {}
        for key, value in POSITION_CHOICES.items():
            grouped = []
            for entry in value:
                if (
                    isinstance(entry, (tuple, list))
                    and len(entry) == 2
                    and isinstance(entry[1], (list, tuple))
                ):
                    group_label, group_options = entry
                    grouped.append(
                        {
                            'group': group_label,
                            'options': [{'value': code, 'label': label} for code, label in group_options],
                        }
                    )
                else:
                    code, label = entry
                    grouped.append(
                        {
                            'group': None,
                            'options': [{'value': code, 'label': label}],
                        }
                    )
            result[key] = grouped
        return result

    def get_department_group_map(self):
        if 'department' not in self.fields:
            return {}
        department_queryset = getattr(self.fields['department'], 'queryset', None)
        if department_queryset is None:
            return {}
        mapping = {}
        for department in department_queryset:
            group_label = self._match_consulting_group(department.name)
            if group_label:
                mapping[str(department.pk)] = group_label
        return mapping

    @staticmethod
    def _match_consulting_group(name: str) -> str | None:
        if not name:
            return None
        for group_label in CONSULTING_GROUP_LOOKUP.keys():
            if group_label == name or group_label in name or name in group_label:
                return group_label
        return None

