from django import forms
from backend.apps.financial_management.models import (
    AccountSubject, Voucher, VoucherEntry, Budget, Invoice, FundFlow,
    ReceivableAccount, PayableAccount
)
from backend.apps.system_management.models import User
from backend.apps.production_management.models import Project


class AccountSubjectForm(forms.ModelForm):
    """会计科目表单"""
    
    class Meta:
        model = AccountSubject
        fields = [
            'code', 'name', 'parent', 'subject_type', 'direction', 
            'level', 'is_active', 'description'
        ]
        widgets = {
            'code': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': '科目编码，如：1001'
            }),
            'name': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': '科目名称'
            }),
            'parent': forms.Select(attrs={'class': 'form-select'}),
            'subject_type': forms.Select(attrs={'class': 'form-select'}),
            'direction': forms.Select(attrs={'class': 'form-select'}),
            'level': forms.NumberInput(attrs={
                'class': 'form-control',
                'min': 1,
                'max': 5,
                'placeholder': '科目级别（1-5）'
            }),
            'is_active': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
            'description': forms.Textarea(attrs={
                'class': 'form-control',
                'rows': 3,
                'placeholder': '备注说明'
            }),
        }
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # 动态加载上级科目
        self.fields['parent'].queryset = AccountSubject.objects.filter(is_active=True).order_by('code')
        # 编辑时排除自己
        if self.instance and self.instance.pk:
            self.fields['parent'].queryset = self.fields['parent'].queryset.exclude(pk=self.instance.pk)


class VoucherForm(forms.ModelForm):
    """记账凭证表单"""
    
    class Meta:
        model = Voucher
        fields = [
            'voucher_date', 'attachment_count', 'status', 
            'preparer', 'reviewer', 'notes'
        ]
        widgets = {
            'voucher_date': forms.DateInput(attrs={
                'class': 'form-control',
                'type': 'date'
            }),
            'attachment_count': forms.NumberInput(attrs={
                'class': 'form-control',
                'min': 0,
                'placeholder': '附件数量'
            }),
            'status': forms.Select(attrs={'class': 'form-select'}),
            'preparer': forms.Select(attrs={'class': 'form-select'}),
            'reviewer': forms.Select(attrs={'class': 'form-select'}),
            'notes': forms.Textarea(attrs={
                'class': 'form-control',
                'rows': 3,
                'placeholder': '备注'
            }),
        }
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['preparer'].queryset = User.objects.filter(is_active=True).order_by('username')
        self.fields['reviewer'].queryset = User.objects.filter(is_active=True).order_by('username')
        self.fields['reviewer'].required = False


class VoucherEntryForm(forms.ModelForm):
    """凭证分录表单（用于内联）"""
    
    class Meta:
        model = VoucherEntry
        fields = ['line_number', 'account_subject', 'summary', 'debit_amount', 'credit_amount']
        widgets = {
            'line_number': forms.NumberInput(attrs={
                'class': 'form-control',
                'readonly': True
            }),
            'account_subject': forms.Select(attrs={'class': 'form-select'}),
            'summary': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': '摘要'
            }),
            'debit_amount': forms.NumberInput(attrs={
                'class': 'form-control',
                'step': '0.01',
                'placeholder': '0.00'
            }),
            'credit_amount': forms.NumberInput(attrs={
                'class': 'form-control',
                'step': '0.01',
                'placeholder': '0.00'
            }),
        }
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['account_subject'].queryset = AccountSubject.objects.filter(is_active=True).order_by('code')


class BudgetForm(forms.ModelForm):
    """预算管理表单"""
    
    class Meta:
        model = Budget
        fields = [
            'name', 'account_subject', 'department',
            'budget_year', 'budget_amount',
            'start_date', 'end_date', 'status', 'description'
        ]
        widgets = {
            'name': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': '预算名称'
            }),
            'account_subject': forms.Select(attrs={'class': 'form-select'}),
            'department': forms.Select(attrs={'class': 'form-select'}),
            'budget_year': forms.NumberInput(attrs={
                'class': 'form-control',
                'placeholder': '预算年度'
            }),
            'budget_amount': forms.NumberInput(attrs={
                'class': 'form-control',
                'step': '0.01',
                'placeholder': '预算金额'
            }),
            'start_date': forms.DateInput(attrs={
                'class': 'form-control',
                'type': 'date'
            }),
            'end_date': forms.DateInput(attrs={
                'class': 'form-control',
                'type': 'date'
            }),
            'status': forms.Select(attrs={'class': 'form-select'}),
            'description': forms.Textarea(attrs={
                'class': 'form-control',
                'rows': 3,
                'placeholder': '备注说明'
            }),
        }
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        from backend.apps.system_management.models import Department
        try:
            self.fields['account_subject'].queryset = AccountSubject.objects.filter(is_active=True).order_by('code')
            self.fields['department'].queryset = Department.objects.filter(is_active=True).order_by('name')
        except Exception:
            # 如果数据库连接有问题，使用默认查询集
            self.fields['account_subject'].queryset = AccountSubject.objects.none()
            self.fields['department'].queryset = Department.objects.none()
        self.fields['account_subject'].required = False
        self.fields['department'].required = False
        # 默认当前年度
        from django.utils import timezone
        self.fields['budget_year'].initial = timezone.now().year


class InvoiceForm(forms.ModelForm):
    """发票管理表单"""
    
    class Meta:
        model = Invoice
        fields = [
            'invoice_number', 'invoice_code', 'invoice_type', 'amount',
            'tax_amount', 'total_amount', 'invoice_date',
            'customer_name', 'supplier_name', 'status', 'attachment', 'notes'
        ]
        widgets = {
            'invoice_number': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': '发票号码'
            }),
            'invoice_code': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': '发票代码'
            }),
            'invoice_type': forms.Select(attrs={'class': 'form-select'}),
            'amount': forms.NumberInput(attrs={
                'class': 'form-control',
                'step': '0.01',
                'placeholder': '发票金额（不含税）'
            }),
            'tax_amount': forms.NumberInput(attrs={
                'class': 'form-control',
                'step': '0.01',
                'placeholder': '税额'
            }),
            'total_amount': forms.NumberInput(attrs={
                'class': 'form-control',
                'step': '0.01',
                'placeholder': '价税合计'
            }),
            'invoice_date': forms.DateInput(attrs={
                'class': 'form-control',
                'type': 'date'
            }),
            'customer_name': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': '客户名称'
            }),
            'supplier_name': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': '供应商名称'
            }),
            'status': forms.Select(attrs={'class': 'form-select'}),
            'attachment': forms.FileInput(attrs={
                'class': 'form-control',
                'accept': '.pdf,.jpg,.jpeg,.png'
            }),
            'notes': forms.Textarea(attrs={
                'class': 'form-control',
                'rows': 3,
                'placeholder': '备注'
            }),
        }


class FundFlowForm(forms.ModelForm):
    """资金流表单"""
    
    class Meta:
        model = FundFlow
        fields = [
            'flow_type', 'project', 'amount', 'flow_date',
            'account_name', 'counterparty', 'summary', 'voucher'
        ]
        widgets = {
            'flow_type': forms.Select(attrs={'class': 'form-select'}),
            'project': forms.Select(attrs={'class': 'form-select'}),
            'amount': forms.NumberInput(attrs={
                'class': 'form-control',
                'step': '0.01',
                'placeholder': '金额'
            }),
            'flow_date': forms.DateInput(attrs={
                'class': 'form-control',
                'type': 'date'
            }),
            'account_name': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': '账户名称'
            }),
            'counterparty': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': '对方单位'
            }),
            'summary': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': '摘要'
            }),
            'voucher': forms.Select(attrs={'class': 'form-select'}),
        }
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        try:
            self.fields['project'].queryset = Project.objects.all().order_by('-created_time')
            self.fields['voucher'].queryset = Voucher.objects.filter(status='posted').order_by('-voucher_date')
        except Exception:
            # 如果数据库连接有问题，使用默认查询集
            self.fields['project'].queryset = Project.objects.none()
            self.fields['voucher'].queryset = Voucher.objects.none()
        self.fields['project'].required = False
        self.fields['voucher'].required = False
        self.fields['counterparty'].required = False


class ReceivableAccountForm(forms.ModelForm):
    """应收账款表单"""
    
    class Meta:
        model = ReceivableAccount
        fields = [
            'customer', 'project', 'receivable_amount', 'received_amount',
            'receivable_date', 'due_date', 'payment_terms', 'status', 'description'
        ]
        widgets = {
            'customer': forms.Select(attrs={'class': 'form-select'}),
            'project': forms.Select(attrs={'class': 'form-select'}),
            'receivable_amount': forms.NumberInput(attrs={
                'class': 'form-control',
                'step': '0.01',
                'placeholder': '应收金额'
            }),
            'received_amount': forms.NumberInput(attrs={
                'class': 'form-control',
                'step': '0.01',
                'placeholder': '已收金额',
                'value': '0.00'
            }),
            'receivable_date': forms.DateInput(attrs={
                'class': 'form-control',
                'type': 'date'
            }),
            'due_date': forms.DateInput(attrs={
                'class': 'form-control',
                'type': 'date'
            }),
            'payment_terms': forms.NumberInput(attrs={
                'class': 'form-control',
                'min': 0,
                'placeholder': '账期（天）'
            }),
            'status': forms.Select(attrs={'class': 'form-select'}),
            'description': forms.Textarea(attrs={
                'class': 'form-control',
                'rows': 3,
                'placeholder': '备注说明'
            }),
        }
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        try:
            from backend.apps.customer_management.models import Client
            self.fields['customer'].queryset = Client.objects.filter(is_active=True).order_by('name')
        except (ImportError, AttributeError):
            # 如果Client模型不存在或无法导入，使用空查询集
            self.fields['customer'].queryset = AccountSubject.objects.none()  # 临时使用AccountSubject作为占位符
        try:
            self.fields['project'].queryset = Project.objects.all().order_by('-created_time')
        except Exception:
            self.fields['project'].queryset = Project.objects.none()
        self.fields['customer'].required = False
        self.fields['project'].required = False
        self.fields['due_date'].required = False
        self.fields['payment_terms'].required = False
        self.fields['received_amount'].initial = 0.00


class PayableAccountForm(forms.ModelForm):
    """应付账款表单"""
    
    class Meta:
        model = PayableAccount
        fields = [
            'supplier', 'project', 'payable_amount', 'paid_amount',
            'payable_date', 'due_date', 'payment_terms', 'status', 'description'
        ]
        widgets = {
            'supplier': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': '供应商名称'
            }),
            'project': forms.Select(attrs={'class': 'form-select'}),
            'payable_amount': forms.NumberInput(attrs={
                'class': 'form-control',
                'step': '0.01',
                'placeholder': '应付金额'
            }),
            'paid_amount': forms.NumberInput(attrs={
                'class': 'form-control',
                'step': '0.01',
                'placeholder': '已付金额',
                'value': '0.00'
            }),
            'payable_date': forms.DateInput(attrs={
                'class': 'form-control',
                'type': 'date'
            }),
            'due_date': forms.DateInput(attrs={
                'class': 'form-control',
                'type': 'date'
            }),
            'payment_terms': forms.NumberInput(attrs={
                'class': 'form-control',
                'min': 0,
                'placeholder': '账期（天）'
            }),
            'status': forms.Select(attrs={'class': 'form-select'}),
            'description': forms.Textarea(attrs={
                'class': 'form-control',
                'rows': 3,
                'placeholder': '备注说明'
            }),
        }
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        try:
            self.fields['project'].queryset = Project.objects.all().order_by('-created_time')
        except Exception:
            self.fields['project'].queryset = Project.objects.none()
        self.fields['project'].required = False
        self.fields['due_date'].required = False
        self.fields['payment_terms'].required = False
        self.fields['paid_amount'].initial = 0.00

