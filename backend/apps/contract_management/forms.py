# 合同管理表单（独立实现，不依赖 customer_management.forms）
# 仅依赖：contract_management.models、customer_management.models（数据）、opportunity_management、production_management、system_management

from django import forms
from django.core.exceptions import ValidationError

from backend.apps.contract_management.models import BusinessContract
from backend.apps.customer_management.models import (
    Client,
    ContractNegotiation,
    AuthorizationLetter,
    AuthorizationLetterTemplate,
)
from backend.apps.opportunity_management.models import BusinessOpportunity
from backend.apps.production_management.models import Project


class ContractForm(forms.ModelForm):
    """合同表单"""

    class Meta:
        model = BusinessContract
        fields = [
            'client', 'opportunity', 'parent_contract',
            'project_number', 'contract_number', 'contract_name', 'contract_type', 'status',
            'structure_type', 'design_unit_category',
            'contract_amount', 'tax_rate',
            'contract_date', 'effective_date', 'start_date', 'end_date',
            'description', 'notes', 'is_active',
        ]
        widgets = {
            'client': forms.Select(attrs={'class': 'form-select'}),
            'opportunity': forms.Select(attrs={'class': 'form-select', 'required': True}),
            'parent_contract': forms.Select(attrs={'class': 'form-select'}),
            'project_number': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': '项目编号（自动生成：YYYYMMDD-0000）',
            }),
            'contract_number': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': '合同编号（可手动修改）',
            }),
            'contract_name': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': '合同名称'
            }),
            'contract_type': forms.Select(attrs={'class': 'form-select'}),
            'status': forms.HiddenInput(),
            'structure_type': forms.Select(attrs={
                'class': 'form-select',
                'placeholder': '请选择结构形式'
            }),
            'design_unit_category': forms.Select(attrs={
                'class': 'form-select',
                'placeholder': '请选择设计单位分类'
            }),
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
            'contract_date': forms.DateInput(attrs={'class': 'form-control', 'type': 'date'}),
            'effective_date': forms.DateInput(attrs={'class': 'form-control', 'type': 'date'}),
            'start_date': forms.DateInput(attrs={'class': 'form-control', 'type': 'date'}),
            'end_date': forms.DateInput(attrs={'class': 'form-control', 'type': 'date'}),
            'party_a_name': forms.TextInput(attrs={'class': 'form-control', 'placeholder': '甲方单位名称'}),
            'party_a_contact': forms.TextInput(attrs={'class': 'form-control', 'placeholder': '甲方联系人'}),
            'party_b_name': forms.TextInput(attrs={
                'class': 'form-control',
                'value': '四川维海科技有限公司',
                'placeholder': '乙方单位名称'
            }),
            'party_b_contact': forms.TextInput(attrs={'class': 'form-control', 'placeholder': '乙方联系人'}),
            'description': forms.Textarea(attrs={'class': 'form-control', 'rows': 4, 'placeholder': '合同描述'}),
            'notes': forms.Textarea(attrs={'class': 'form-control', 'rows': 3, 'placeholder': '备注信息'}),
            'is_active': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
        }

    def __init__(self, *args, **kwargs):
        user = kwargs.pop('user', None)
        permission_set = kwargs.pop('permission_set', None)
        super().__init__(*args, **kwargs)

        if 'status' in self.fields:
            if not self.instance or not self.instance.pk:
                self.fields['status'].initial = 'draft'

        from backend.apps.customer_management.views_pages import _filter_clients_by_permission
        from backend.apps.system_management.services import get_user_permission_codes
        if user and permission_set is None:
            permission_set = get_user_permission_codes(user)

        opportunity_clients = BusinessOpportunity.objects.filter(
            client__is_active=True
        ).values_list('client_id', flat=True).distinct()
        clients = Client.objects.filter(
            id__in=opportunity_clients,
            is_active=True
        ).select_related('created_by', 'responsible_user', 'responsible_user__department')
        if user and permission_set:
            clients = _filter_clients_by_permission(clients, user, permission_set)
        self.fields['client'].queryset = clients.order_by('name')

        if 'opportunity' in self.fields:
            opportunities = BusinessOpportunity.objects.select_related(
                'client', 'business_manager', 'created_by'
            ).order_by('-created_time')
            self.fields['opportunity'].queryset = opportunities
            self.fields['opportunity'].empty_label = '-- 请选择关联商机 --'
            self.fields['opportunity'].required = True

        self.fields['parent_contract'].queryset = BusinessContract.objects.filter(
            is_active=True,
            contract_type__in=['framework', 'project']
        ).exclude(id=self.instance.id if self.instance.id else None).order_by('-created_time')

        if 'client' in self.fields:
            self.fields['client'].required = True
        self.fields['client'].empty_label = '-- 选择客户 --'
        self.fields['parent_contract'].empty_label = '-- 选择主合同 --'

        self.fields['responsible_department'] = forms.CharField(
            required=False,
            label='责任部门',
            widget=forms.TextInput(attrs={
                'class': 'form-control',
                'readonly': True,
                'placeholder': '系统自动填充'
            })
        )
        self.fields['responsible_person'] = forms.CharField(
            required=False,
            label='责任人员',
            widget=forms.TextInput(attrs={
                'class': 'form-control',
                'readonly': True,
                'placeholder': '系统自动填充'
            })
        )
        self.fields['project_name'] = forms.CharField(
            required=False,
            label='项目名称',
            widget=forms.TextInput(attrs={'class': 'form-control', 'placeholder': '项目名称'})
        )
        if self.instance and self.instance.pk and self.instance.project:
            self.fields['project_name'].initial = self.instance.project.name
        elif self.data and 'project' in self.data and self.data['project']:
            try:
                project = Project.objects.get(id=self.data['project'])
                self.fields['project_name'].initial = project.name
            except (Project.DoesNotExist, ValueError):
                pass

        if 'project_number' in self.fields:
            self.fields['project_number'].required = False
            if not self.instance or not self.instance.pk or not self.instance.project_number:
                from datetime import datetime
                from django.db.models import Max

                current_date = datetime.now().strftime('%Y%m%d')
                date_prefix = f'{current_date}-'
                max_letter = AuthorizationLetter.objects.filter(
                    project_number__startswith=date_prefix
                ).aggregate(max_num=Max('project_number'))['max_num']
                max_contract = BusinessContract.objects.filter(
                    project_number__startswith=date_prefix
                ).exclude(id=self.instance.id if self.instance.id else None).aggregate(
                    max_num=Max('project_number'))['max_num']
                max_project_number = None
                if max_letter and max_contract:
                    max_project_number = max(max_letter, max_contract)
                elif max_letter:
                    max_project_number = max_letter
                elif max_contract:
                    max_project_number = max_contract

                if max_project_number:
                    try:
                        seq_str = max_project_number.split('-')[-1]
                        seq = int(seq_str) + 1
                    except (ValueError, IndexError):
                        seq = 1
                else:
                    seq = 1
                project_number_initial = f'{date_prefix}{seq:04d}'
                self.fields['project_number'].initial = project_number_initial
                if 'contract_number' in self.fields:
                    if not self.instance or not self.instance.pk or not self.instance.contract_number:
                        self.fields['contract_number'].initial = f'HT-{project_number_initial}'
                    elif not self.instance.contract_number:
                        if self.instance.project_number:
                            self.fields['contract_number'].initial = f'HT-{self.instance.project_number}'
                        else:
                            self.fields['contract_number'].initial = f'HT-{project_number_initial}'
            else:
                if self.instance and self.instance.pk and 'contract_number' in self.fields:
                    if not self.instance.contract_number and self.instance.project_number:
                        self.fields['contract_number'].initial = f'HT-{self.instance.project_number}'

    def clean_project_number(self):
        project_number = self.cleaned_data.get('project_number')
        if project_number:
            existing_contract = BusinessContract.objects.filter(
                project_number=project_number
            ).exclude(id=self.instance.id if self.instance.id else None).first()
            if existing_contract:
                raise forms.ValidationError(
                    f'项目编号 "{project_number}" 已被使用（合同：{existing_contract.contract_number or existing_contract.id}）')
            existing_letter = AuthorizationLetter.objects.filter(project_number=project_number).first()
            if existing_letter:
                raise forms.ValidationError(
                    f'项目编号 "{project_number}" 已被使用（业务委托书：{existing_letter.letter_number or existing_letter.id}）')
        return project_number

    def clean_contract_number(self):
        contract_number = self.cleaned_data.get('contract_number')
        if contract_number:
            existing_contract = BusinessContract.objects.filter(
                contract_number=contract_number
            ).exclude(id=self.instance.id if self.instance.id else None).first()
            if existing_contract:
                raise forms.ValidationError(
                    f'合同编号 "{contract_number}" 已被使用（合同：{existing_contract.contract_name or existing_contract.id}）')
        return contract_number


class ContractNegotiationForm(forms.ModelForm):
    """合同洽谈记录表单"""

    class Meta:
        model = ContractNegotiation
        fields = [
            'contract', 'client', 'project',
            'negotiation_type', 'status', 'title', 'content',
            'participants', 'client_participants',
            'negotiation_date', 'negotiation_start_time', 'negotiation_end_time', 'next_negotiation_date',
            'result_summary', 'agreed_items', 'pending_items',
            'attachments', 'notes',
        ]
        widgets = {
            'contract': forms.Select(attrs={'class': 'form-select'}),
            'client': forms.Select(attrs={'class': 'form-select'}),
            'project': forms.Select(attrs={'class': 'form-select'}),
            'negotiation_type': forms.Select(attrs={'class': 'form-select'}),
            'status': forms.Select(attrs={'class': 'form-select'}),
            'title': forms.TextInput(attrs={'class': 'form-control', 'placeholder': '请输入洽谈主题'}),
            'content': forms.Textarea(attrs={'class': 'form-control', 'rows': 6, 'placeholder': '详细记录洽谈过程中的讨论内容、双方意见等'}),
            'participants': forms.SelectMultiple(attrs={'class': 'form-select', 'size': 5}),
            'client_participants': forms.TextInput(attrs={'class': 'form-control', 'placeholder': '多个用逗号分隔'}),
            'negotiation_date': forms.DateInput(attrs={'class': 'form-control', 'type': 'date'}),
            'negotiation_start_time': forms.TimeInput(attrs={'class': 'form-control', 'type': 'time'}),
            'negotiation_end_time': forms.TimeInput(attrs={'class': 'form-control', 'type': 'time'}),
            'next_negotiation_date': forms.DateInput(attrs={'class': 'form-control', 'type': 'date'}),
            'result_summary': forms.Textarea(attrs={'class': 'form-control', 'rows': 4, 'placeholder': '本次洽谈达成的共识、待解决问题等'}),
            'agreed_items': forms.Textarea(attrs={'class': 'form-control', 'rows': 4, 'placeholder': '双方已达成一致的事项'}),
            'pending_items': forms.Textarea(attrs={'class': 'form-control', 'rows': 4, 'placeholder': '需要进一步讨论或解决的问题'}),
            'attachments': forms.Textarea(attrs={'class': 'form-control', 'rows': 3, 'placeholder': '洽谈过程中涉及的文档、资料等'}),
            'notes': forms.Textarea(attrs={'class': 'form-control', 'rows': 3, 'placeholder': '其他备注信息'}),
        }
        labels = {
            'contract': '关联合同', 'client': '客户', 'project': '关联项目',
            'negotiation_type': '洽谈类型', 'status': '洽谈状态', 'title': '洽谈主题', 'content': '洽谈内容',
            'participants': '参与人员（我方）', 'client_participants': '客户参与人员',
            'negotiation_date': '洽谈日期', 'negotiation_start_time': '开始时间',
            'negotiation_end_time': '结束时间', 'next_negotiation_date': '下次洽谈日期',
            'result_summary': '洽谈结果摘要', 'agreed_items': '已达成事项', 'pending_items': '待解决事项',
            'attachments': '附件说明', 'notes': '备注',
        }
        help_texts = {
            'contract': '可选，如果洽谈时合同尚未创建可留空',
            'client': '如果未关联合同，则必须填写客户',
        }

    def __init__(self, *args, **kwargs):
        user = kwargs.pop('user', None)
        super().__init__(*args, **kwargs)
        if user:
            from backend.apps.system_management.services import get_user_permission_codes
            from backend.core.views import _permission_granted
            from backend.apps.permission_management.utils import normalize_permission_code
            permission_set = get_user_permission_codes(user)
            code = normalize_permission_code('contract_management.client.view')
            if not _permission_granted(code, permission_set):
                self.fields['contract'].queryset = BusinessContract.objects.none()
            else:
                self.fields['contract'].queryset = BusinessContract.objects.filter(
                    is_active=True
                ).order_by('-created_time')[:100]
        self.fields['client'].queryset = Client.objects.filter(is_active=True).order_by('name')[:100]
        if user:
            from backend.apps.system_management.services import get_user_permission_codes
            from backend.core.views import _permission_granted
            permission_set = get_user_permission_codes(user)
            if _permission_granted('production_management.view_all', permission_set):
                self.fields['project'].queryset = Project.objects.all().order_by('-created_time')[:100]
            else:
                self.fields['project'].queryset = Project.objects.none()
        if user:
            from backend.apps.system_management.models import User
            self.fields['participants'].queryset = User.objects.filter(is_active=True).order_by('username')

    def clean(self):
        cleaned_data = super().clean()
        contract = cleaned_data.get('contract')
        client = cleaned_data.get('client')
        if not contract and not client:
            raise forms.ValidationError('请至少选择关联合同或客户')
        if contract and contract.client:
            cleaned_data['client'] = contract.client
        return cleaned_data


class AuthorizationLetterForm(forms.ModelForm):
    """业务委托书表单"""

    class Meta:
        model = AuthorizationLetter
        fields = [
            'project_number', 'letter_date', 'business_manager',
            'project_name', 'status', 'client', 'opportunity', 'provisional_price',
            'client_name', 'client_contact', 'client_representative', 'client_phone', 'client_email', 'client_address',
            'trustee_name', 'trustee_representative', 'trustee_phone', 'trustee_email', 'trustee_address',
            'result_optimization_rate', 'process_optimization_rate',
            'detailed_review_unit_price_min', 'detailed_review_unit_price_max',
            'fee_determination_principle',
            'settlement_review_process', 'payment_schedule',
            'supplementary_agreement',
            'start_date', 'end_date',
            'opportunity', 'project', 'notes',
        ]
        widgets = {
            'project_number': forms.TextInput(attrs={
                'class': 'form-control', 'readonly': True,
                'placeholder': '系统自动生成，例如：HT-2025-0001'
            }),
            'letter_date': forms.DateInput(attrs={'class': 'form-control', 'type': 'date', 'required': True}),
            'business_manager': forms.Select(attrs={'class': 'form-select', 'required': True}),
            'client': forms.Select(attrs={'class': 'form-select', 'required': True, 'id': 'id_client'}),
            'opportunity': forms.Select(attrs={'class': 'form-select'}),
            'provisional_price': forms.NumberInput(attrs={'class': 'form-control', 'step': '0.01', 'placeholder': '0.00'}),
            'project_name': forms.TextInput(attrs={'class': 'form-control', 'placeholder': '项目名称'}),
            'status': forms.Select(attrs={'class': 'form-select'}),
            'client_name': forms.TextInput(attrs={'class': 'form-control', 'placeholder': '单位名称', 'readonly': True}),
            'client_contact': forms.Select(attrs={'class': 'form-select', 'id': 'id_client_contact'}),
            'client_representative': forms.TextInput(attrs={'class': 'form-control', 'placeholder': '单位代表', 'readonly': True}),
            'client_phone': forms.TextInput(attrs={'class': 'form-control', 'placeholder': '联系电话'}),
            'client_email': forms.EmailInput(attrs={'class': 'form-control', 'placeholder': '电子邮箱'}),
            'client_address': forms.TextInput(attrs={'class': 'form-control', 'placeholder': '收件地址'}),
            'trustee_name': forms.TextInput(attrs={
                'class': 'form-control', 'value': '四川维海科技有限公司',
                'placeholder': '服务单位', 'required': True
            }),
            'trustee_representative': forms.TextInput(attrs={'class': 'form-control', 'placeholder': '单位代表，例如：田霞'}),
            'trustee_phone': forms.TextInput(attrs={'class': 'form-control', 'placeholder': '联系电话，例如：13666287899/02883574973'}),
            'trustee_email': forms.EmailInput(attrs={'class': 'form-control', 'placeholder': '电子邮箱，例如：whkj@vihgroup.com.cn'}),
            'trustee_address': forms.TextInput(attrs={'class': 'form-control', 'placeholder': '收件地址'}),
            'result_optimization_rate': forms.NumberInput(attrs={'class': 'form-control', 'step': '0.01', 'min': '10', 'max': '15', 'placeholder': '10-15'}),
            'process_optimization_rate': forms.NumberInput(attrs={'class': 'form-control', 'step': '0.01', 'min': '10', 'max': '15', 'placeholder': '10-15'}),
            'detailed_review_unit_price_min': forms.NumberInput(attrs={'class': 'form-control', 'step': '0.01', 'placeholder': '1.5'}),
            'detailed_review_unit_price_max': forms.NumberInput(attrs={'class': 'form-control', 'step': '0.01', 'placeholder': '3.0'}),
            'fee_determination_principle': forms.Textarea(attrs={'class': 'form-control', 'rows': 6, 'placeholder': '服务费确定原则说明（可选）'}),
            'settlement_review_process': forms.Textarea(attrs={'class': 'form-control', 'rows': 8, 'placeholder': '结算审核流程说明（可选）'}),
            'payment_schedule': forms.HiddenInput(),
            'supplementary_agreement': forms.Textarea(attrs={'class': 'form-control', 'rows': 4, 'placeholder': '补充约定（可选）'}),
            'start_date': forms.DateInput(attrs={'class': 'form-control', 'type': 'date'}),
            'end_date': forms.DateInput(attrs={'class': 'form-control', 'type': 'date'}),
            'project': forms.Select(attrs={'class': 'form-select'}),
            'notes': forms.Textarea(attrs={'class': 'form-control', 'rows': 3, 'placeholder': '备注信息（可选）'}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        client = self.instance.client if (self.instance and self.instance.pk) else None
        if 'client' in self.fields:
            self.fields['client'].queryset = Client.objects.filter(is_active=True).order_by('name')
            self.fields['client'].empty_label = '-- 选择客户 --'
            self.fields['client'].required = True
        opportunity_queryset = BusinessOpportunity.objects.filter(
            status__in=['potential', 'initial_contact', 'requirement_confirmed', 'quotation', 'negotiation']
        )
        if client:
            opportunity_queryset = opportunity_queryset.filter(client=client)
        if 'opportunity' in self.fields:
            self.fields['opportunity'].queryset = opportunity_queryset.select_related('client').order_by('-created_time')
            self.fields['opportunity'].empty_label = '-- 选择商机（可选） --'
        self.fields['project'].queryset = Project.objects.filter(
            status__in=['planning', 'in_progress', 'completed']
        ).order_by('-created_time')
        self.fields['project'].empty_label = '-- 选择项目（可选） --'
        if 'business_manager' in self.fields:
            from backend.apps.system_management.models import User
            business_managers = User.objects.filter(
                roles__code='business_manager',
                is_active=True
            ).distinct().order_by('username')
            if not business_managers.exists():
                business_managers = User.objects.filter(is_active=True).order_by('username')[:50]
            self.fields['business_manager'].queryset = business_managers
            self.fields['business_manager'].empty_label = '-- 选择商务经理 --'
        if 'project_number' in self.fields:
            self.fields['project_number'].required = False
        if 'client' in self.fields:
            self.fields['client'].widget.attrs['id'] = 'id_client'
        if 'opportunity' in self.fields:
            self.fields['opportunity'].widget.attrs['id'] = 'id_opportunity'
        if 'project' in self.fields:
            self.fields['project'].widget.attrs['id'] = 'id_project'
        if 'client_name' in self.fields:
            self.fields['client_name'].widget.attrs['id'] = 'id_client_name'

    def clean(self):
        cleaned_data = super().clean()
        start_date = cleaned_data.get('start_date')
        end_date = cleaned_data.get('end_date')
        if start_date and end_date and end_date < start_date:
            raise forms.ValidationError('结束日期不能早于开始日期')
        return cleaned_data


class AuthorizationLetterTemplateForm(forms.ModelForm):
    """业务委托书模板表单"""

    class Meta:
        model = AuthorizationLetterTemplate
        fields = [
            'template_name', 'template_type', 'category', 'status', 'description',
            'template_content', 'variables', 'template_file'
        ]
        widgets = {
            'template_name': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': '请输入模板名称',
                'required': True
            }),
            'template_type': forms.Select(attrs={'class': 'form-select', 'required': True}),
            'category': forms.TextInput(attrs={'class': 'form-control', 'placeholder': '模板分类（可选）'}),
            'status': forms.Select(attrs={'class': 'form-select'}),
            'description': forms.Textarea(attrs={
                'class': 'form-control',
                'rows': 4,
                'placeholder': '模板说明（可选）'
            }),
            'template_content': forms.HiddenInput(),
            'variables': forms.HiddenInput(),
            'template_file': forms.FileInput(attrs={
                'class': 'form-control',
                'accept': '.doc,.docx,.pdf,.xls,.xlsx,.ppt,.pptx',
            }),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        if self.instance and self.instance.pk:
            import json
            if self.instance.template_content:
                self.initial['template_content'] = json.dumps(
                    self.instance.template_content, ensure_ascii=False, indent=2)
            if self.instance.variables:
                self.initial['variables'] = json.dumps(
                    self.instance.variables, ensure_ascii=False, indent=2)

    def clean_template_content(self):
        import json
        template_content = self.cleaned_data.get('template_content')
        if isinstance(template_content, str):
            try:
                return json.loads(template_content)
            except json.JSONDecodeError:
                raise forms.ValidationError('模板内容格式错误，必须是有效的JSON格式')
        return template_content or {}

    def clean_variables(self):
        import json
        variables = self.cleaned_data.get('variables')
        if isinstance(variables, str):
            try:
                return json.loads(variables)
            except json.JSONDecodeError:
                raise forms.ValidationError('变量列表格式错误，必须是有效的JSON格式')
        return variables or []

    def clean_template_file(self):
        template_file = self.cleaned_data.get('template_file')
        if template_file:
            max_size = 50 * 1024 * 1024
            if template_file.size > max_size:
                raise forms.ValidationError(
                    f'文件大小不能超过50MB，当前文件大小为 {template_file.size / 1024 / 1024:.2f}MB')
            import os
            ext = os.path.splitext(template_file.name)[1].lower()
            allowed_extensions = ['.doc', '.docx', '.pdf', '.xls', '.xlsx', '.ppt', '.pptx']
            if ext not in allowed_extensions:
                raise forms.ValidationError(f'不支持的文件格式，仅支持：{", ".join(allowed_extensions)}')
        return template_file


__all__ = [
    'ContractForm',
    'ContractNegotiationForm',
    'AuthorizationLetterForm',
    'AuthorizationLetterTemplateForm',
]
