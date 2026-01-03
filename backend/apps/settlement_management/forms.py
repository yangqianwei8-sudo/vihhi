from django import forms
from backend.apps.settlement_management.models import ProjectSettlement, ContractSettlement
from backend.apps.production_management.models import Project
from backend.apps.production_management.models import BusinessContract


class ProjectSettlementForm(forms.ModelForm):
    """项目结算表单"""
    
    class Meta:
        model = ProjectSettlement
        fields = [
            'project', 'contract', 'settlement_type', 
            'settlement_period_start', 'settlement_period_end', 'settlement_date',
            'contract_amount', 'tax_rate',
            'total_output_value', 'confirmed_output_value',
            'settlement_file', 'description', 'notes'
        ]
        widgets = {
            'project': forms.Select(attrs={'class': 'form-select'}),
            'contract': forms.Select(attrs={'class': 'form-select'}),
            'settlement_type': forms.Select(attrs={'class': 'form-select'}),
            'settlement_period_start': forms.DateInput(attrs={
                'class': 'form-control',
                'type': 'date'
            }),
            'settlement_period_end': forms.DateInput(attrs={
                'class': 'form-control',
                'type': 'date'
            }),
            'settlement_date': forms.DateInput(attrs={
                'class': 'form-control',
                'type': 'date'
            }),
            'contract_amount': forms.NumberInput(attrs={
                'class': 'form-control',
                'step': '0.01',
                'placeholder': '合同金额'
            }),
            'tax_rate': forms.NumberInput(attrs={
                'class': 'form-control',
                'step': '0.01',
                'placeholder': '税率(%)，默认6%'
            }),
            'total_output_value': forms.NumberInput(attrs={
                'class': 'form-control',
                'step': '0.01',
                'readonly': True,
                'placeholder': '自动统计'
            }),
            'confirmed_output_value': forms.NumberInput(attrs={
                'class': 'form-control',
                'step': '0.01',
                'placeholder': '确认产值'
            }),
            'settlement_file': forms.FileInput(attrs={
                'class': 'form-control',
                'accept': '.pdf,.doc,.docx,.xls,.xlsx'
            }),
            'description': forms.Textarea(attrs={
                'class': 'form-control',
                'rows': 3,
                'placeholder': '结算说明'
            }),
            'notes': forms.Textarea(attrs={
                'class': 'form-control',
                'rows': 3,
                'placeholder': '备注信息'
            }),
        }
        labels = {
            'project': '关联项目',
            'contract': '关联合同',
            'settlement_type': '结算类型',
            'settlement_period_start': '结算周期开始日期',
            'settlement_period_end': '结算周期结束日期',
            'settlement_date': '结算日期',
            'contract_amount': '合同金额',
            'tax_rate': '税率(%)',
            'total_output_value': '累计产值',
            'confirmed_output_value': '确认产值',
            'settlement_file': '结算文件',
            'description': '结算说明',
            'notes': '备注',
        }
    
    def __init__(self, *args, **kwargs):
        user = kwargs.pop('user', None)
        super().__init__(*args, **kwargs)
        
        # 动态加载项目（仅显示状态为"已完工"的项目）
        self.fields['project'].queryset = Project.objects.filter(
            status='completed'
        ).order_by('-created_time')
        
        self.fields['contract'].queryset = BusinessContract.objects.filter(
            status__in=['effective', 'executing', 'completed']
        ).order_by('-created_time')
        
        self.fields['contract'].required = False
        
        # 如果是编辑，显示关联的项目合同
        if self.instance and self.instance.pk:
            if self.instance.project:
                self.fields['contract'].queryset = BusinessContract.objects.filter(
                    project=self.instance.project
                ).order_by('-created_time') | self.fields['contract'].queryset
    
    def clean(self):
        cleaned_data = super().clean()
        settlement_period_start = cleaned_data.get('settlement_period_start')
        settlement_period_end = cleaned_data.get('settlement_period_end')
        
        # 验证结算周期
        if settlement_period_start and settlement_period_end:
            if settlement_period_end < settlement_period_start:
                raise forms.ValidationError({
                    'settlement_period_end': '结算周期结束日期不能早于开始日期'
                })
        
        return cleaned_data


class ContractSettlementForm(forms.ModelForm):
    """合同结算表单"""
    
    class Meta:
        model = ContractSettlement
        fields = [
            'contract', 'settlement_batch', 'settlement_date',
            'contract_amount', 'previous_settlement_amount', 'this_settlement_amount',
            'total_settlement_amount', 'tax_rate', 'tax_amount', 'settlement_amount_tax',
            'settlement_file', 'invoice_number', 'description', 'notes'
        ]
        widgets = {
            'contract': forms.Select(attrs={'class': 'form-select'}),
            'settlement_batch': forms.NumberInput(attrs={
                'class': 'form-control',
                'min': 1,
                'placeholder': '结算批次'
            }),
            'settlement_date': forms.DateInput(attrs={
                'class': 'form-control',
                'type': 'date'
            }),
            'contract_amount': forms.NumberInput(attrs={
                'class': 'form-control',
                'step': '0.01',
                'readonly': True,
                'placeholder': '自动获取'
            }),
            'previous_settlement_amount': forms.NumberInput(attrs={
                'class': 'form-control',
                'step': '0.01',
                'readonly': True,
                'placeholder': '自动计算'
            }),
            'this_settlement_amount': forms.NumberInput(attrs={
                'class': 'form-control',
                'step': '0.01',
                'placeholder': '本次结算金额'
            }),
            'total_settlement_amount': forms.NumberInput(attrs={
                'class': 'form-control',
                'step': '0.01',
                'readonly': True,
                'placeholder': '自动计算'
            }),
            'tax_rate': forms.NumberInput(attrs={
                'class': 'form-control',
                'step': '0.01',
                'placeholder': '税率(%)，默认6%'
            }),
            'tax_amount': forms.NumberInput(attrs={
                'class': 'form-control',
                'step': '0.01',
                'readonly': True,
                'placeholder': '自动计算'
            }),
            'settlement_amount_tax': forms.NumberInput(attrs={
                'class': 'form-control',
                'step': '0.01',
                'readonly': True,
                'placeholder': '自动计算'
            }),
            'settlement_file': forms.FileInput(attrs={
                'class': 'form-control',
                'accept': '.pdf,.doc,.docx,.xls,.xlsx'
            }),
            'invoice_number': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': '发票号码'
            }),
            'description': forms.Textarea(attrs={
                'class': 'form-control',
                'rows': 3,
                'placeholder': '结算说明'
            }),
            'notes': forms.Textarea(attrs={
                'class': 'form-control',
                'rows': 3,
                'placeholder': '备注信息'
            }),
        }
        labels = {
            'contract': '关联合同',
            'settlement_batch': '结算批次',
            'settlement_date': '结算日期',
            'contract_amount': '合同金额',
            'previous_settlement_amount': '已结算金额',
            'this_settlement_amount': '本次结算金额',
            'total_settlement_amount': '累计结算金额',
            'tax_rate': '税率(%)',
            'tax_amount': '税额',
            'settlement_amount_tax': '结算金额（含税）',
            'settlement_file': '结算文件',
            'invoice_number': '发票号码',
            'description': '结算说明',
            'notes': '备注',
        }
    
    def __init__(self, *args, **kwargs):
        user = kwargs.pop('user', None)
        super().__init__(*args, **kwargs)
        
        # 动态加载合同
        self.fields['contract'].queryset = BusinessContract.objects.filter(
            status__in=['effective', 'executing', 'completed']
        ).order_by('-created_time')
        
        # 如果是编辑，锁定合同和批次
        if self.instance and self.instance.pk:
            self.fields['contract'].disabled = True
            self.fields['settlement_batch'].disabled = True
            self.fields['contract_amount'].widget.attrs['readonly'] = True
            self.fields['previous_settlement_amount'].widget.attrs['readonly'] = True
    
    def clean(self):
        cleaned_data = super().clean()
        contract = cleaned_data.get('contract')
        settlement_batch = cleaned_data.get('settlement_batch', 1)
        this_settlement_amount = cleaned_data.get('this_settlement_amount')
        tax_rate = cleaned_data.get('tax_rate', 6.00)
        
        # 自动计算税额和含税金额
        if this_settlement_amount:
            tax_amount = this_settlement_amount * (tax_rate / 100)
            settlement_amount_tax = this_settlement_amount + tax_amount
            cleaned_data['tax_amount'] = tax_amount
            cleaned_data['settlement_amount_tax'] = settlement_amount_tax
        
        # 如果是新记录，检查批次是否已存在
        if not self.instance.pk and contract:
            if ContractSettlement.objects.filter(
                contract=contract, settlement_batch=settlement_batch
            ).exists():
                raise forms.ValidationError({
                    'settlement_batch': f'该合同的第{settlement_batch}批结算已存在'
                })
        
        return cleaned_data

