"""审批流程引擎表单"""
from django import forms
from .models import WorkflowTemplate
from .constants import APPLICABLE_MODEL_CHOICES


class WorkflowTemplateForm(forms.ModelForm):
    """审批流程模板表单（创建/编辑），含适用范围（适用模型）"""

    applicable_models = forms.MultipleChoiceField(
        choices=APPLICABLE_MODEL_CHOICES,
        required=False,
        label='适用模型',
        help_text='选择此流程适用的业务类型，可多选。不选表示不限制，由业务提交时指定流程。',
        widget=forms.SelectMultiple(attrs={
            'class': 'form-select',
            'size': 12,
        }),
    )

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
        if self.instance and self.instance.pk and getattr(self.instance, 'applicable_models', None):
            self.fields['applicable_models'].initial = list(self.instance.applicable_models)

    def save(self, commit=True):
        workflow = super().save(commit=False)
        workflow.applicable_models = self.cleaned_data.get('applicable_models', [])
        if commit:
            workflow.save()
        return workflow
