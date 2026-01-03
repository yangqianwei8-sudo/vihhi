"""
诉讼管理模块表单
"""
from django import forms
from django.core.exceptions import ValidationError
from backend.apps.litigation_management.models import (
    LitigationCase, LitigationProcess, LitigationDocument,
    LitigationExpense, LitigationPerson, LitigationTimeline,
    PreservationSeal
)
from backend.apps.production_management.models import Project
from backend.apps.customer_management.models import Client
from backend.apps.production_management.models import BusinessContract


class LitigationCaseForm(forms.ModelForm):
    """诉讼案件表单"""
    
    class Meta:
        model = LitigationCase
        fields = [
            'case_name', 'case_type', 'case_nature', 'description',
            'project', 'client', 'contract', 'litigation_amount',
            'dispute_amount', 'status', 'priority', 'case_manager',
            'registration_date'
        ]
        widgets = {
            'case_name': forms.TextInput(attrs={'class': 'form-control', 'placeholder': '请输入案件名称'}),
            'case_type': forms.Select(attrs={'class': 'form-select'}),
            'case_nature': forms.Select(attrs={'class': 'form-select'}),
            'description': forms.Textarea(attrs={'class': 'form-control', 'rows': 3, 'placeholder': '请输入案件描述'}),
            'project': forms.Select(attrs={'class': 'form-select'}),
            'client': forms.Select(attrs={'class': 'form-select'}),
            'contract': forms.Select(attrs={'class': 'form-select'}),
            'litigation_amount': forms.NumberInput(attrs={'class': 'form-control', 'step': '0.01', 'placeholder': '请输入诉讼标的额'}),
            'dispute_amount': forms.NumberInput(attrs={'class': 'form-control', 'step': '0.01', 'placeholder': '请输入争议金额'}),
            'status': forms.Select(attrs={'class': 'form-select'}),
            'priority': forms.Select(attrs={'class': 'form-select'}),
            'case_manager': forms.Select(attrs={'class': 'form-select'}),
            'registration_date': forms.DateInput(attrs={'class': 'form-control', 'type': 'date'}),
        }
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['project'].queryset = Project.objects.filter(
            status__in=['in_progress', 'suspended', 'waiting_start']
        ).order_by('-created_time')
        self.fields['client'].queryset = Client.objects.filter(is_active=True).order_by('name')
        self.fields['contract'].queryset = BusinessContract.objects.filter(
            status__in=['signed', 'executing']
        ).order_by('-contract_date')
        
        # 设置可选字段
        self.fields['project'].required = False
        self.fields['client'].required = False
        self.fields['contract'].required = False
        self.fields['litigation_amount'].required = False
        self.fields['dispute_amount'].required = False
        self.fields['case_manager'].required = False


class LitigationProcessForm(forms.ModelForm):
    """诉讼流程表单"""
    
    class Meta:
        model = LitigationProcess
        fields = [
            'case', 'process_type', 'process_date', 'status',
            'filing_number', 'court_name', 'court_address', 'court_contact',
            'judge_name', 'trial_location', 'trial_participants',
            'trial_result', 'trial_notes',
            'judgment_number', 'judgment_content', 'judgment_amount',
            'execution_amount', 'interest_amount', 'execution_deadline',
            'execution_status', 'execution_result', 'notes'
        ]
        widgets = {
            'case': forms.Select(attrs={'class': 'form-select'}),
            'process_type': forms.Select(attrs={'class': 'form-select'}),
            'process_date': forms.DateInput(attrs={'class': 'form-control', 'type': 'date'}),
            'status': forms.Select(attrs={'class': 'form-select'}),
            'filing_number': forms.TextInput(attrs={'class': 'form-control'}),
            'court_name': forms.TextInput(attrs={'class': 'form-control'}),
            'court_address': forms.TextInput(attrs={'class': 'form-control'}),
            'court_contact': forms.TextInput(attrs={'class': 'form-control'}),
            'judge_name': forms.TextInput(attrs={'class': 'form-control'}),
            'trial_location': forms.TextInput(attrs={'class': 'form-control'}),
            'trial_participants': forms.TextInput(attrs={'class': 'form-control'}),
            'trial_result': forms.TextInput(attrs={'class': 'form-control'}),
            'trial_notes': forms.Textarea(attrs={'class': 'form-control', 'rows': 4}),
            'judgment_number': forms.TextInput(attrs={'class': 'form-control'}),
            'judgment_content': forms.Textarea(attrs={'class': 'form-control', 'rows': 4}),
            'judgment_amount': forms.NumberInput(attrs={'class': 'form-control', 'step': '0.01'}),
            'execution_amount': forms.NumberInput(attrs={'class': 'form-control', 'step': '0.01'}),
            'interest_amount': forms.NumberInput(attrs={'class': 'form-control', 'step': '0.01'}),
            'execution_deadline': forms.DateInput(attrs={'class': 'form-control', 'type': 'date'}),
            'execution_status': forms.TextInput(attrs={'class': 'form-control'}),
            'execution_result': forms.Textarea(attrs={'class': 'form-control', 'rows': 4}),
            'notes': forms.Textarea(attrs={'class': 'form-control', 'rows': 3}),
        }


class LitigationDocumentForm(forms.ModelForm):
    """诉讼文档表单"""
    
    class Meta:
        model = LitigationDocument
        fields = ['case', 'process', 'document_name', 'document_type', 'document_file', 'description']
        widgets = {
            'case': forms.Select(attrs={'class': 'form-select'}),
            'process': forms.Select(attrs={'class': 'form-select'}),
            'document_name': forms.TextInput(attrs={'class': 'form-control'}),
            'document_type': forms.Select(attrs={'class': 'form-select'}),
            'document_file': forms.FileInput(attrs={'class': 'form-control'}),
            'description': forms.Textarea(attrs={'class': 'form-control', 'rows': 3}),
        }
    
    def __init__(self, *args, **kwargs):
        case = kwargs.pop('case', None)
        super().__init__(*args, **kwargs)
        if case:
            self.fields['case'].initial = case
            self.fields['case'].widget = forms.HiddenInput()
            self.fields['process'].queryset = case.processes.all().order_by('-process_date')
        self.fields['process'].required = False
        self.fields['description'].required = False


class LitigationExpenseForm(forms.ModelForm):
    """诉讼费用表单"""
    
    class Meta:
        model = LitigationExpense
        fields = [
            'case', 'project', 'expense_name', 'expense_type',
            'amount', 'expense_date', 'payment_method', 'payment_status',
            'invoice_file', 'description'
        ]
        widgets = {
            'case': forms.Select(attrs={'class': 'form-select'}),
            'project': forms.Select(attrs={'class': 'form-select'}),
            'expense_name': forms.TextInput(attrs={'class': 'form-control'}),
            'expense_type': forms.Select(attrs={'class': 'form-select'}),
            'amount': forms.NumberInput(attrs={'class': 'form-control', 'step': '0.01'}),
            'expense_date': forms.DateInput(attrs={'class': 'form-control', 'type': 'date'}),
            'payment_method': forms.Select(attrs={'class': 'form-select'}),
            'payment_status': forms.Select(attrs={'class': 'form-select'}),
            'invoice_file': forms.FileInput(attrs={'class': 'form-control'}),
            'description': forms.Textarea(attrs={'class': 'form-control', 'rows': 3}),
        }
    
    def __init__(self, *args, **kwargs):
        case = kwargs.pop('case', None)
        super().__init__(*args, **kwargs)
        if case:
            self.fields['case'].initial = case
            self.fields['case'].widget = forms.HiddenInput()
        self.fields['project'].queryset = Project.objects.all().order_by('-created_time')
        self.fields['project'].required = False
        self.fields['payment_method'].required = False
        self.fields['invoice_file'].required = False
        self.fields['description'].required = False


class LitigationPersonForm(forms.ModelForm):
    """诉讼人员表单"""
    
    class Meta:
        model = LitigationPerson
        fields = [
            'case', 'person_type', 'name', 'law_firm', 'license_number',
            'specialty', 'role', 'rating', 'evaluation',
            'court_name', 'position',
            'party_type', 'address',
            'contact_phone', 'contact_email'
        ]
        widgets = {
            'case': forms.Select(attrs={'class': 'form-select'}),
            'person_type': forms.Select(attrs={'class': 'form-select'}),
            'name': forms.TextInput(attrs={'class': 'form-control'}),
            'law_firm': forms.TextInput(attrs={'class': 'form-control'}),
            'license_number': forms.TextInput(attrs={'class': 'form-control'}),
            'specialty': forms.TextInput(attrs={'class': 'form-control'}),
            'role': forms.TextInput(attrs={'class': 'form-control'}),
            'rating': forms.Select(attrs={'class': 'form-select'}),
            'evaluation': forms.Textarea(attrs={'class': 'form-control', 'rows': 3}),
            'court_name': forms.TextInput(attrs={'class': 'form-control'}),
            'position': forms.TextInput(attrs={'class': 'form-control'}),
            'party_type': forms.Select(attrs={'class': 'form-select'}),
            'address': forms.TextInput(attrs={'class': 'form-control'}),
            'contact_phone': forms.TextInput(attrs={'class': 'form-control'}),
            'contact_email': forms.EmailInput(attrs={'class': 'form-control'}),
        }
    
    def __init__(self, *args, **kwargs):
        case = kwargs.pop('case', None)
        super().__init__(*args, **kwargs)
        if case:
            self.fields['case'].initial = case
            self.fields['case'].widget = forms.HiddenInput()
        
        # 设置可选字段
        self.fields['law_firm'].required = False
        self.fields['license_number'].required = False
        self.fields['specialty'].required = False
        self.fields['role'].required = False
        self.fields['rating'].required = False
        self.fields['evaluation'].required = False
        self.fields['court_name'].required = False
        self.fields['position'].required = False
        self.fields['party_type'].required = False
        self.fields['address'].required = False
        self.fields['contact_phone'].required = False
        self.fields['contact_email'].required = False


class LitigationTimelineForm(forms.ModelForm):
    """时间节点表单"""
    
    class Meta:
        model = LitigationTimeline
        fields = [
            'case', 'timeline_name', 'timeline_type', 'timeline_date',
            'status', 'reminder_enabled', 'reminder_days_before', 'description'
        ]
        widgets = {
            'case': forms.Select(attrs={'class': 'form-select'}),
            'timeline_name': forms.TextInput(attrs={'class': 'form-control'}),
            'timeline_type': forms.Select(attrs={'class': 'form-select'}),
            'timeline_date': forms.DateInput(attrs={'class': 'form-control', 'type': 'date'}),
            'status': forms.Select(attrs={'class': 'form-select'}),
            'reminder_enabled': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
            'reminder_days_before': forms.TextInput(attrs={'class': 'form-control'}),
            'description': forms.Textarea(attrs={'class': 'form-control', 'rows': 3}),
        }
    
    def __init__(self, *args, **kwargs):
        case = kwargs.pop('case', None)
        super().__init__(*args, **kwargs)
        if case:
            self.fields['case'].initial = case
            self.fields['case'].widget = forms.HiddenInput()
        self.fields['reminder_days_before'].required = False
        self.fields['description'].required = False
    
    def clean_reminder_days_before(self):
        """验证提醒天数格式"""
        days_before = self.cleaned_data.get('reminder_days_before')
        if days_before:
            if isinstance(days_before, str):
                try:
                    # 尝试解析逗号分隔的数字列表
                    days_list = [int(d.strip()) for d in days_before.split(',')]
                    return days_list
                except ValueError:
                    raise ValidationError('提醒天数格式错误，请使用逗号分隔的数字，如：7,3,1,0')
            return days_before
        return []


class PreservationSealForm(forms.ModelForm):
    """保全续封表单"""
    
    class Meta:
        model = PreservationSeal
        fields = [
            'case', 'seal_type', 'seal_amount', 'seal_number',
            'court_name', 'start_date', 'end_date',
            'renewal_deadline', 'renewal_materials', 'notes'
        ]
        widgets = {
            'case': forms.Select(attrs={'class': 'form-select'}),
            'seal_type': forms.Select(attrs={'class': 'form-select'}),
            'seal_amount': forms.NumberInput(attrs={'class': 'form-control', 'step': '0.01'}),
            'seal_number': forms.TextInput(attrs={'class': 'form-control'}),
            'court_name': forms.TextInput(attrs={'class': 'form-control'}),
            'start_date': forms.DateInput(attrs={'class': 'form-control', 'type': 'date'}),
            'end_date': forms.DateInput(attrs={'class': 'form-control', 'type': 'date'}),
            'renewal_deadline': forms.DateInput(attrs={'class': 'form-control', 'type': 'date'}),
            'renewal_materials': forms.Textarea(attrs={'class': 'form-control', 'rows': 3}),
            'notes': forms.Textarea(attrs={'class': 'form-control', 'rows': 3}),
        }
    
    def __init__(self, *args, **kwargs):
        case = kwargs.pop('case', None)
        super().__init__(*args, **kwargs)
        if case:
            self.fields['case'].initial = case
            self.fields['case'].widget = forms.HiddenInput()
        
        # 设置可选字段
        self.fields['seal_amount'].required = False
        self.fields['seal_number'].required = False
        self.fields['court_name'].required = False
        self.fields['renewal_deadline'].required = False
        self.fields['renewal_materials'].required = False
        self.fields['notes'].required = False
    
    def clean(self):
        """验证日期逻辑"""
        cleaned_data = super().clean()
        start_date = cleaned_data.get('start_date')
        end_date = cleaned_data.get('end_date')
        renewal_deadline = cleaned_data.get('renewal_deadline')
        
        if start_date and end_date and start_date > end_date:
            raise ValidationError({'end_date': '结束日期不能早于开始日期'})
        
        if renewal_deadline and end_date and renewal_deadline < end_date:
            raise ValidationError({'renewal_deadline': '续封申请截止日期不能早于保全结束日期'})
        
        return cleaned_data

