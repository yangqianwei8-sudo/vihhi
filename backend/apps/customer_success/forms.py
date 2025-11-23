from django import forms
from .models import BusinessContract, Client
from backend.apps.project_center.models import Project


class ContractForm(forms.ModelForm):
    """合同表单"""
    
    class Meta:
        model = BusinessContract
        fields = [
            # 关联信息
            'project', 'client', 'parent_contract',
            # 基本信息（contract_number 可留空自动生成）
            'contract_number', 'contract_name', 'contract_type', 'status',
            # 金额信息
            'contract_amount', 'tax_rate',
            # 时间信息
            'contract_date', 'effective_date', 'start_date', 'end_date',
            # 双方信息
            'party_a_name', 'party_a_contact', 'party_b_name', 'party_b_contact',
            'signed_by', 'approved_by',
            # 其他信息
            'description', 'notes', 'is_active',
        ]
        widgets = {
            'project': forms.Select(attrs={'class': 'form-select'}),
            'client': forms.Select(attrs={'class': 'form-select'}),
            'parent_contract': forms.Select(attrs={'class': 'form-select'}),
            'contract_number': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': '留空将自动生成，例如：VIH-CON-2025-0001'
            }),
            'contract_name': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': '合同名称'
            }),
            'contract_type': forms.Select(attrs={'class': 'form-select'}),
            'status': forms.Select(attrs={'class': 'form-select'}),
            'contract_amount': forms.NumberInput(attrs={
                'class': 'form-control',
                'step': '0.01',
                'placeholder': '0.00'
            }),
            'tax_rate': forms.NumberInput(attrs={
                'class': 'form-control',
                'step': '0.01',
                'value': '6.00',
                'placeholder': '6.00'
            }),
            'contract_date': forms.DateInput(attrs={
                'class': 'form-control',
                'type': 'date'
            }),
            'effective_date': forms.DateInput(attrs={
                'class': 'form-control',
                'type': 'date'
            }),
            'start_date': forms.DateInput(attrs={
                'class': 'form-control',
                'type': 'date'
            }),
            'end_date': forms.DateInput(attrs={
                'class': 'form-control',
                'type': 'date'
            }),
            'party_a_name': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': '甲方单位名称'
            }),
            'party_a_contact': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': '甲方联系人'
            }),
            'party_b_name': forms.TextInput(attrs={
                'class': 'form-control',
                'value': '四川维海科技有限公司',
                'placeholder': '乙方单位名称'
            }),
            'party_b_contact': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': '乙方联系人'
            }),
            'signed_by': forms.Select(attrs={'class': 'form-select'}),
            'approved_by': forms.Select(attrs={'class': 'form-select'}),
            'description': forms.Textarea(attrs={
                'class': 'form-control',
                'rows': 4,
                'placeholder': '合同描述'
            }),
            'notes': forms.Textarea(attrs={
                'class': 'form-control',
                'rows': 3,
                'placeholder': '备注信息'
            }),
            'is_active': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
        }
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # 设置查询集
        self.fields['client'].queryset = Client.objects.filter(is_active=True).order_by('name')
        self.fields['project'].queryset = Project.objects.filter(status__in=['planning', 'in_progress', 'completed']).order_by('-created_time')
        self.fields['parent_contract'].queryset = BusinessContract.objects.filter(
            is_active=True,
            contract_type__in=['framework', 'project']
        ).exclude(id=self.instance.id if self.instance.id else None).order_by('-created_time')
        
        from backend.apps.system_management.models import User
        self.fields['signed_by'].queryset = User.objects.filter(is_active=True).order_by('username')
        self.fields['approved_by'].queryset = User.objects.filter(is_active=True).order_by('username')
        
        # 设置空选项
        self.fields['project'].empty_label = '-- 选择项目 --'
        self.fields['client'].empty_label = '-- 选择客户 --'
        self.fields['parent_contract'].empty_label = '-- 选择主合同 --'
        self.fields['signed_by'].empty_label = '-- 选择签订人 --'
        self.fields['approved_by'].empty_label = '-- 选择审批人 --'
    
    def clean_contract_number(self):
        contract_number = self.cleaned_data.get('contract_number')
        if contract_number:
            # 去除前后空格
            contract_number = contract_number.strip()
            if not contract_number:
                return None  # 空字符串转换为 None，让模型自动生成
            # 检查是否已存在（编辑时排除自己）
            qs = BusinessContract.objects.filter(contract_number=contract_number)
            if self.instance and self.instance.id:
                qs = qs.exclude(id=self.instance.id)
            if qs.exists():
                raise forms.ValidationError('合同编号已存在，请使用其他编号。')
        return contract_number or None  # 空值转换为 None，让模型自动生成

