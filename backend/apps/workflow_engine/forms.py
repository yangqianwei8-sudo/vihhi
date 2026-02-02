"""审批流程引擎表单"""
from django import forms
from .models import WorkflowTemplate


class WorkflowTemplateForm(forms.ModelForm):
    """审批流程模板表单（创建/编辑）"""
    
    class Meta:
        model = WorkflowTemplate
        fields = [
            'name', 'code', 'description', 'category', 'status',
            'allow_withdraw', 'allow_reject', 'allow_transfer',
            'timeout_hours', 'timeout_action',
        ]
        widgets = {
            'name': forms.TextInput(attrs={'class': 'form-control', 'required': True}),
            'code': forms.TextInput(attrs={'class': 'form-control', 'required': True}),
            'description': forms.Textarea(attrs={'class': 'form-control', 'rows': 3}),
            'category': forms.TextInput(attrs={'class': 'form-control', 'placeholder': '例如：合同管理、商机管理'}),
            'status': forms.Select(attrs={'class': 'form-select'}),
            'allow_withdraw': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
            'allow_reject': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
            'allow_transfer': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
            'timeout_hours': forms.NumberInput(attrs={'class': 'form-control', 'min': 0, 'placeholder': '为空则不限制'}),
            'timeout_action': forms.Select(attrs={'class': 'form-select'}),
        }
    
    def __init__(self, *args, **kwargs):
        self.instance = kwargs.get('instance')
        super().__init__(*args, **kwargs)
        if self.instance and self.instance.pk:
            self.fields['code'].widget.attrs['readonly'] = True
