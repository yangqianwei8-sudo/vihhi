from django import forms
from backend.apps.settlement_management.models import ProjectSettlement, ContractSettlement
from backend.apps.production_management.models import Project
from backend.apps.production_management.models import BusinessContract
from backend.apps.settlement_center.models import (
    ServiceFeeSettlementScheme,
    ServiceFeeSegmentedRate,
    ServiceFeeJumpPointRate,
    ServiceFeeUnitCapDetail
)


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
        else:
            # 新建时，设置日期字段默认值为当天
            from datetime import date
            today = date.today()
            if 'settlement_period_start' in self.fields:
                self.fields['settlement_period_start'].initial = today
            if 'settlement_period_end' in self.fields:
                self.fields['settlement_period_end'].initial = today
            if 'settlement_date' in self.fields:
                self.fields['settlement_date'].initial = today
    
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
        else:
            # 新建时，设置日期字段默认值为当天
            from datetime import date
            today = date.today()
            if 'settlement_date' in self.fields:
                self.fields['settlement_date'].initial = today
    
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


class ServiceFeeSettlementSchemeForm(forms.ModelForm):
    """服务费结算方案表单"""
    
    class Meta:
        model = ServiceFeeSettlementScheme
        fields = [
            'name', 'code', 'description',
            'contract', 'project',
            'settlement_method',
            'fixed_total_price', 'fixed_unit_price', 'area_type',
            'cumulative_rate',
            'combined_fixed_method', 'combined_fixed_total', 'combined_fixed_unit',
            'combined_fixed_area_type', 'combined_actual_method', 'combined_cumulative_rate',
            'combined_deduct_fixed',
            'has_cap_fee', 'cap_type', 'total_cap_amount',
            'has_minimum_fee', 'minimum_fee_amount',
            'is_active', 'is_default', 'sort_order'
        ]
        widgets = {
            'name': forms.TextInput(attrs={'class': 'form-control', 'placeholder': '方案名称'}),
            'code': forms.TextInput(attrs={'class': 'form-control', 'placeholder': '方案代码（可选）'}),
            'description': forms.Textarea(attrs={'class': 'form-control', 'rows': 3, 'placeholder': '方案描述'}),
            'contract': forms.Select(attrs={'class': 'form-select'}),
            'project': forms.Select(attrs={'class': 'form-select'}),
            'settlement_method': forms.Select(attrs={'class': 'form-select'}),
            'fixed_total_price': forms.NumberInput(attrs={'class': 'form-control', 'step': '0.01'}),
            'fixed_unit_price': forms.NumberInput(attrs={'class': 'form-control', 'step': '0.01'}),
            'area_type': forms.Select(attrs={'class': 'form-select'}),
            'cumulative_rate': forms.NumberInput(attrs={'class': 'form-control', 'step': '0.01'}),
            'combined_fixed_method': forms.Select(attrs={'class': 'form-select'}),
            'combined_fixed_total': forms.NumberInput(attrs={'class': 'form-control', 'step': '0.01'}),
            'combined_fixed_unit': forms.NumberInput(attrs={'class': 'form-control', 'step': '0.01'}),
            'combined_fixed_area_type': forms.Select(attrs={'class': 'form-select'}),
            'combined_actual_method': forms.Select(attrs={'class': 'form-select'}),
            'combined_cumulative_rate': forms.NumberInput(attrs={'class': 'form-control', 'step': '0.01'}),
            'combined_deduct_fixed': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
            'has_cap_fee': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
            'cap_type': forms.Select(attrs={'class': 'form-select'}),
            'total_cap_amount': forms.NumberInput(attrs={'class': 'form-control', 'step': '0.01'}),
            'has_minimum_fee': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
            'minimum_fee_amount': forms.NumberInput(attrs={'class': 'form-control', 'step': '0.01'}),
            'is_active': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
            'is_default': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
            'sort_order': forms.NumberInput(attrs={'class': 'form-control', 'min': 0}),
        }
    
    def __init__(self, *args, **kwargs):
        user = kwargs.pop('user', None)
        super().__init__(*args, **kwargs)
        
        # 动态加载合同和项目
        self.fields['contract'].queryset = BusinessContract.objects.filter(
            status__in=['effective', 'executing', 'completed']
        ).order_by('-created_time')
        self.fields['contract'].required = False
        
        self.fields['project'].queryset = Project.objects.all().order_by('-created_time')
        self.fields['project'].required = False
    
    def clean(self):
        cleaned_data = super().clean()
        settlement_method = cleaned_data.get('settlement_method')
        
        # 根据结算方式验证必填字段
        if settlement_method == 'fixed_total':
            if not cleaned_data.get('fixed_total_price'):
                raise forms.ValidationError({
                    'fixed_total_price': '固定总价方式必须填写固定总价'
                })
        
        elif settlement_method == 'fixed_unit':
            if not cleaned_data.get('fixed_unit_price'):
                raise forms.ValidationError({
                    'fixed_unit_price': '固定单价方式必须填写固定单价'
                })
            if not cleaned_data.get('area_type'):
                raise forms.ValidationError({
                    'area_type': '固定单价方式必须选择面积类型'
                })
        
        elif settlement_method == 'cumulative_commission':
            if not cleaned_data.get('cumulative_rate'):
                raise forms.ValidationError({
                    'cumulative_rate': '累计提成方式必须填写取费系数'
                })
        
        elif settlement_method == 'combined':
            if not cleaned_data.get('combined_fixed_method'):
                raise forms.ValidationError({
                    'combined_fixed_method': '组合方式必须选择固定部分方式'
                })
            if not cleaned_data.get('combined_actual_method'):
                raise forms.ValidationError({
                    'combined_actual_method': '组合方式必须选择按实结算部分方式'
                })
        
        # 验证封顶费
        if cleaned_data.get('has_cap_fee'):
            if not cleaned_data.get('cap_type') or cleaned_data.get('cap_type') == 'no_cap':
                raise forms.ValidationError({
                    'cap_type': '设置封顶费时必须选择封顶费类型'
                })
            if cleaned_data.get('cap_type') == 'total_cap' and not cleaned_data.get('total_cap_amount'):
                raise forms.ValidationError({
                    'total_cap_amount': '总价封顶时必须填写封顶金额'
                })
        
        # 验证保底费
        if cleaned_data.get('has_minimum_fee') and not cleaned_data.get('minimum_fee_amount'):
            raise forms.ValidationError({
                'minimum_fee_amount': '设置保底费时必须填写保底费金额'
            })
        
        return cleaned_data

