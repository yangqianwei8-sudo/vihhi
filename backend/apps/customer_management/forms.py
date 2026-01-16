from django import forms
from django.core.exceptions import ValidationError
from django.db import models as django_models
from .models import (
    Client, 
    ClientContact,
    ContactCareer,
    ContactColleague,
    ContactEducation,
    School,
    CustomerRelationship,
    CustomerRelationshipUpgrade,
    BusinessExpenseApplication,
    CustomerRelationshipCollaboration,
    CustomerRelationshipCollaborationAttachment,
    ContractNegotiation,
    VisitPlan,
    VisitCheckin,
    VisitReview,
    BusinessOpportunity,
    AuthorizationLetter,
    AuthorizationLetterTemplate
)
# 尝试导入 ContactInfoChange（如果模型存在）
try:
    from .models import ContactInfoChange
except ImportError:
    ContactInfoChange = None
from backend.apps.production_management.models import BusinessContract, Project


class ContractForm(forms.ModelForm):
    """合同表单"""
    
    class Meta:
        model = BusinessContract
        fields = [
            # 关联信息
            'client', 'opportunity', 'parent_contract',
            # 基本信息
            'project_number', 'contract_number', 'contract_name', 'contract_type', 'status',
            # 项目信息
            'structure_type', 'design_unit_category',
            # 金额信息
            'contract_amount', 'tax_rate',
            # 时间信息
            'contract_date', 'effective_date', 'start_date', 'end_date',
            # 其他信息
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
            'status': forms.HiddenInput(),  # 合同状态由系统自动判断，不显示在表单中
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
        # 从kwargs中提取user和permission_set（如果提供）
        user = kwargs.pop('user', None)
        permission_set = kwargs.pop('permission_set', None)
        
        super().__init__(*args, **kwargs)
        
        # 设置合同状态默认值（由系统自动判断，默认为合同草稿）
        if 'status' in self.fields:
            if not self.instance or not self.instance.pk:
                # 新建合同时，默认状态为合同草稿
                self.fields['status'].initial = 'draft'
            # status字段已设置为HiddenInput，用户不可见
        
        # 设置客户查询集（从商机创建列表中获取，应用权限过滤）
        from .views_pages import _filter_clients_by_permission, get_user_permission_codes
        if user and permission_set is None:
            permission_set = get_user_permission_codes(user)
        
        # 从商机创建列表中获取关联的客户（只显示有商机的客户）
        opportunity_clients = BusinessOpportunity.objects.filter(
            client__is_active=True
        ).values_list('client_id', flat=True).distinct()
        
        clients = Client.objects.filter(
            id__in=opportunity_clients,
            is_active=True
        ).select_related('created_by', 'responsible_user', 'responsible_user__department')
        
        # 应用权限过滤（与客户列表页面保持一致）
        if user and permission_set:
            clients = _filter_clients_by_permission(clients, user, permission_set)
        
        self.fields['client'].queryset = clients.order_by('name')
        
        # 设置关联商机查询集（从商机管理列表中获取）
        if 'opportunity' in self.fields:
            # 获取商机管理列表中的所有商机（不依赖客户选择）
            opportunities = BusinessOpportunity.objects.select_related(
                'client', 'business_manager', 'created_by'
            ).order_by('-created_time')
            
            # 不再根据客户过滤，显示所有商机
            # 关联客户将通过JavaScript根据选择的商机自动填充
            
            self.fields['opportunity'].queryset = opportunities
            self.fields['opportunity'].empty_label = '-- 请选择关联商机 --'
            self.fields['opportunity'].required = True
        
        self.fields['parent_contract'].queryset = BusinessContract.objects.filter(
            is_active=True,
            contract_type__in=['framework', 'project']
        ).exclude(id=self.instance.id if self.instance.id else None).order_by('-created_time')
        
        from backend.apps.system_management.models import User
        # 设置关联客户为必填
        if 'client' in self.fields:
            self.fields['client'].required = True
        
        # 设置空选项
        self.fields['client'].empty_label = '-- 选择客户 --'
        self.fields['parent_contract'].empty_label = '-- 选择主合同 --'
        
        # 添加责任部门和责任人员字段（只读，非模型字段）
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
        
        # 项目编号字段处理：解析为HT、年度、顺序号
        # 添加项目名称字段（非模型字段，用于显示和输入）
        self.fields['project_name'] = forms.CharField(
            required=False,
            label='项目名称',
            widget=forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': '项目名称'
            })
        )
        # 如果实例存在且有关联的project，从project中获取项目名称
        if self.instance and self.instance.pk and self.instance.project:
            self.fields['project_name'].initial = self.instance.project.name
        # 如果是新建且从POST数据中有project，也需要设置
        elif self.data and 'project' in self.data and self.data['project']:
            try:
                # Project已在文件顶部导入，无需再次导入
                project = Project.objects.get(id=self.data['project'])
                self.fields['project_name'].initial = project.name
            except (Project.DoesNotExist, ValueError):
                pass
        
        if 'project_number' in self.fields:
            self.fields['project_number'].required = False
            # 自动生成项目编号：YYYYMMDD-0000格式
            if not self.instance or not self.instance.pk or not self.instance.project_number:
                # 新建模式：自动生成项目编号
                from datetime import datetime
                from django.db.models import Max
                from backend.apps.customer_management.models import AuthorizationLetter
                
                current_date = datetime.now().strftime('%Y%m%d')
                date_prefix = f'{current_date}-'
                
                # 查找当天最大项目编号（从业务委托书和合同中查找）
                max_letter = AuthorizationLetter.objects.filter(
                    project_number__startswith=date_prefix
                ).aggregate(max_num=Max('project_number'))['max_num']
                
                max_contract = BusinessContract.objects.filter(
                    project_number__startswith=date_prefix
                ).exclude(id=self.instance.id if self.instance.id else None).aggregate(max_num=Max('project_number'))['max_num']
                
                # 取两者中的最大值
                max_project_number = None
                if max_letter and max_contract:
                    max_project_number = max(max_letter, max_contract)
                elif max_letter:
                    max_project_number = max_letter
                elif max_contract:
                    max_project_number = max_contract
                
                if max_project_number:
                    try:
                        # 提取序列号，格式：YYYYMMDD-0000
                        seq_str = max_project_number.split('-')[-1]
                        seq = int(seq_str) + 1
                    except (ValueError, IndexError):
                        seq = 1
                else:
                    seq = 1
                
                # 设置初始值
                project_number_initial = f'{date_prefix}{seq:04d}'
                self.fields['project_number'].initial = project_number_initial
                
                # 自动生成合同编号：HT-项目编号
                if 'contract_number' in self.fields:
                    if not self.instance or not self.instance.pk or not self.instance.contract_number:
                        # 新建模式：根据项目编号自动生成合同编号
                        self.fields['contract_number'].initial = f'HT-{project_number_initial}'
                    else:
                        # 编辑模式：如果合同编号为空，根据项目编号生成
                        if not self.instance.contract_number:
                            if self.instance.project_number:
                                self.fields['contract_number'].initial = f'HT-{self.instance.project_number}'
                            else:
                                self.fields['contract_number'].initial = f'HT-{project_number_initial}'
        else:
            # 编辑模式：如果项目编号存在但合同编号为空，自动生成
            if self.instance and self.instance.pk:
                if 'contract_number' in self.fields:
                    if not self.instance.contract_number and self.instance.project_number:
                        self.fields['contract_number'].initial = f'HT-{self.instance.project_number}'
    
    def clean_project_number(self):
        """验证项目编号的唯一性"""
        project_number = self.cleaned_data.get('project_number')
        if project_number:
            # 检查是否与其他合同或业务委托书的项目编号重复
            from backend.apps.customer_management.models import AuthorizationLetter
            
            # 检查合同中的重复
            existing_contract = BusinessContract.objects.filter(
                project_number=project_number
            ).exclude(id=self.instance.id if self.instance.id else None).first()
            
            if existing_contract:
                raise forms.ValidationError(f'项目编号 "{project_number}" 已被使用（合同：{existing_contract.contract_number or existing_contract.id}）')
            
            # 检查业务委托书中的重复
            existing_letter = AuthorizationLetter.objects.filter(
                project_number=project_number
            ).first()
            
            if existing_letter:
                raise forms.ValidationError(f'项目编号 "{project_number}" 已被使用（业务委托书：{existing_letter.letter_number or existing_letter.id}）')
        
        return project_number
    
    def clean_contract_number(self):
        """验证合同编号的唯一性"""
        contract_number = self.cleaned_data.get('contract_number')
        if contract_number:
            # 检查是否与其他合同的合同编号重复
            existing_contract = BusinessContract.objects.filter(
                contract_number=contract_number
            ).exclude(id=self.instance.id if self.instance.id else None).first()
            
            if existing_contract:
                raise forms.ValidationError(f'合同编号 "{contract_number}" 已被使用（合同：{existing_contract.contract_name or existing_contract.id}）')
        
        return contract_number

# ==================== 客户管理模块表单（按《客户管理详细设计方案 v1.12》实现）====================

class CustomerForm(forms.ModelForm):
    """客户表单"""
    
    class Meta:
        model = Client
        fields = [
            'name', 'unified_credit_code',
            'legal_representative', 'established_date', 'registered_capital',
            'company_phone', 'company_email', 'company_address',
            'grade', 'client_type',
            'region', 'source',
            'responsible_user',
        ]
        widgets = {
            'name': forms.TextInput(attrs={'class': 'form-control', 'required': True}),
            'unified_credit_code': forms.TextInput(attrs={'class': 'form-control'}),
            'legal_representative': forms.TextInput(attrs={'class': 'form-control'}),
            'established_date': forms.DateInput(attrs={'class': 'form-control', 'type': 'date'}),
            'registered_capital': forms.NumberInput(attrs={'class': 'form-control', 'step': '0.01'}),
            'company_phone': forms.TextInput(attrs={'class': 'form-control'}),
            'company_email': forms.EmailInput(attrs={'class': 'form-control'}),
            'company_address': forms.TextInput(attrs={'class': 'form-control'}),
            'grade': forms.Select(attrs={'class': 'form-select'}),
            'client_type': forms.Select(attrs={'class': 'form-select', 'required': True}),
            'region': forms.TextInput(attrs={'class': 'form-control'}),
            'source': forms.Select(attrs={'class': 'form-select'}),
            'responsible_user': forms.Select(attrs={'class': 'form-select'}),
        }
    
    def __init__(self, *args, **kwargs):
        user = kwargs.pop('user', None)
        super().__init__(*args, **kwargs)
        # 设置空选项
        self.fields['grade'].empty_label = '-- 自动计算 --'
        # client_type 设为必填，不允许为空
        self.fields['client_type'].required = True
        self.fields['client_type'].empty_label = None  # 不允许空选项
        self.fields['source'].empty_label = '-- 选择来源 --'
        # 设置字段标签
        self.fields['region'].label = '办公地址'
        
        # 设置负责人字段
        from backend.apps.system_management.models import User
        self.fields['responsible_user'].queryset = User.objects.filter(is_active=True).order_by('username')
        self.fields['responsible_user'].empty_label = '-- 选择负责人 --'
        
        # 设置客户类型和客户分级的查询集（从后台管理模型获取）
        from .models import ClientType, ClientGrade
        # 注意：查询集限制为is_active=True，但在clean方法中会处理不在查询集中的ID
        self.fields['client_type'].queryset = ClientType.objects.filter(is_active=True).order_by('display_order', 'name')
        self.fields['grade'].queryset = ClientGrade.objects.filter(is_active=True).order_by('display_order', 'name')
        
        # 如果是创建模式（没有instance或instance没有pk），设置默认值为当前用户
        if user and (not self.instance or not self.instance.pk):
            self.fields['responsible_user'].initial = user
    
    def clean_client_type(self):
        """单独验证 client_type 字段"""
        from .models import ClientType
        
        client_type = self.cleaned_data.get('client_type')
        
        # 如果 client_type 是 None（可能是因为查询集中没有该ID），尝试从原始数据中获取ID
        if not client_type:
            client_type_id = self.data.get('client_type')
            if client_type_id:
                try:
                    client_type_id = int(client_type_id)
                    # 尝试获取该ID的ClientType（先不限制is_active，因为用户可能选择了已禁用的）
                    client_type = ClientType.objects.filter(id=client_type_id).first()
                    if client_type and not client_type.is_active:
                        # 如果选择的类型已被禁用，尝试获取一个激活的默认值
                        default_type = ClientType.objects.filter(is_active=True).order_by('display_order', 'id').first()
                        if default_type:
                            client_type = default_type
                except (ValueError, TypeError):
                    pass
        
        # 如果仍然没有，尝试获取默认值
        if not client_type:
            client_type = ClientType.objects.filter(is_active=True).order_by('display_order', 'id').first()
            if not client_type:
                raise forms.ValidationError('请选择客户类型。如果没有可用的客户类型，请联系管理员配置。')
        
        return client_type
    
    def clean(self):
        """表单验证：检查客户是否重复，并确保必填字段有值"""
        cleaned_data = super().clean()
        name = cleaned_data.get('name')
        unified_credit_code = cleaned_data.get('unified_credit_code', '').strip()
        client_type = cleaned_data.get('client_type')
        
        # 确保 client_type 有值（clean_client_type 应该已经处理了）
        if not client_type:
            from .models import ClientType
            default_client_type = ClientType.objects.filter(is_active=True).order_by('display_order', 'id').first()
            if default_client_type:
                cleaned_data['client_type'] = default_client_type
            else:
                raise forms.ValidationError({
                    'client_type': '请选择客户类型。如果没有可用的客户类型，请联系管理员配置。'
                })
        
        if not name:
            return cleaned_data
        
        # 查询是否存在相同客户名称和统一信用代码的客户
        from .models import Client
        query = Client.objects.filter(name=name)
        
        # 如果填写了统一信用代码，则同时检查名称和统一信用代码
        if unified_credit_code:
            query = query.filter(unified_credit_code=unified_credit_code)
        
        # 如果是编辑模式，排除当前客户
        if self.instance and self.instance.pk:
            query = query.exclude(pk=self.instance.pk)
        
        duplicate_client = query.first()
        
        if duplicate_client:
            # 如果填写了统一信用代码，检查是否完全相同（客户名称和统一信用代码都相同）
            if unified_credit_code and duplicate_client.unified_credit_code == unified_credit_code:
                raise forms.ValidationError(
                    f'与"{duplicate_client.name}"的客户重复，不允许创建'
                )
            # 如果只检查名称（统一信用代码为空），也提示重复
            elif not unified_credit_code:
                # 如果已存在的客户也没有统一信用代码，则认为是重复
                if not duplicate_client.unified_credit_code:
                    raise forms.ValidationError(
                        f'与"{duplicate_client.name}"的客户重复，不允许创建'
                    )
        
        return cleaned_data


class ContactForm(forms.ModelForm):
    """联系人表单"""
    
    # 操作类型：save_draft（保存草稿）或 submit（提交）
    action = forms.CharField(
        required=False,
        widget=forms.HiddenInput(),
        initial='submit'
    )
    
    # 自定义多选字段
    preferred_contact_methods = forms.MultipleChoiceField(
        choices=ClientContact.PREFERRED_CONTACT_METHODS_CHOICES,
        required=False,
        widget=forms.CheckboxSelectMultiple(attrs={'class': 'form-check-input'}),
        label='偏好沟通方式'
    )
    
    tags = forms.CharField(
        required=False,
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': '输入标签，用逗号分隔，例如：技术专家,决策者,影响者',
        }),
        label='个人标签'
    )
    
    class Meta:
        model = ClientContact
        fields = [
            'client', 'name', 'gender', 'birthplace',
            'phone', 'email', 'wechat',
            'office_address',
            'role', 'relationship_level', 'decision_influence',
            'first_contact_time', 'last_contact_time', 'contact_frequency',
            'tracking_cycle_days',
            'preferred_contact_methods', 'best_contact_time',
            'interests', 'focus_areas', 'tags',
            'is_primary', 'notes',
            'resume_file', 'resume_source',
        ]
        widgets = {
            'client': forms.Select(attrs={'class': 'form-select', 'required': True}),
            'name': forms.TextInput(attrs={'class': 'form-control', 'required': True, 'placeholder': '请输入联系人姓名'}),
            'gender': forms.Select(attrs={'class': 'form-select'}),
            'birthplace': forms.HiddenInput(),  # 改为隐藏字段，由省市区选择器自动填充
            'phone': forms.TextInput(attrs={'class': 'form-control', 'placeholder': '请输入手机号'}),
            'email': forms.EmailInput(attrs={'class': 'form-control', 'placeholder': '例如：zhangsan@example.com'}),
            'wechat': forms.TextInput(attrs={'class': 'form-control', 'placeholder': '可输入多个微信号，用逗号分隔'}),
            'office_address': forms.TextInput(attrs={'class': 'form-control', 'placeholder': '办公地址'}),
            'role': forms.Select(attrs={'class': 'form-select'}),
            'relationship_level': forms.Select(attrs={'class': 'form-select'}),
            'decision_influence': forms.Select(attrs={'class': 'form-select'}),
            'first_contact_time': forms.DateTimeInput(attrs={'class': 'form-control', 'type': 'datetime-local'}),
            'last_contact_time': forms.DateTimeInput(attrs={'class': 'form-control', 'type': 'datetime-local'}),
            'contact_frequency': forms.Select(attrs={'class': 'form-select'}),
            'tracking_cycle_days': forms.Select(attrs={'class': 'form-select'}),
            'best_contact_time': forms.TextInput(attrs={'class': 'form-control', 'placeholder': '例如：工作日9-11点'}),
            'interests': forms.Textarea(attrs={'class': 'form-control', 'rows': 3, 'placeholder': '请输入个人兴趣爱好'}),
            'focus_areas': forms.Textarea(attrs={'class': 'form-control', 'rows': 3, 'placeholder': '例如：技术、管理、市场等'}),
            'is_primary': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
            'notes': forms.Textarea(attrs={'class': 'form-control', 'rows': 4, 'placeholder': '备注信息'}),
            'resume_file': forms.FileInput(attrs={'class': 'form-control', 'accept': '.pdf,.doc,.docx,.jpg,.jpeg,.png'}),
            'resume_source': forms.Select(attrs={'class': 'form-select'}),
        }
    
    def __init__(self, *args, **kwargs):
        # 获取action参数，判断是保存草稿还是提交
        self.is_draft = kwargs.pop('is_draft', False)
        action = kwargs.get('data', {}).get('action', '') if 'data' in kwargs else ''
        if action == 'save_draft' or self.is_draft:
            self.is_draft = True
        
        super().__init__(*args, **kwargs)
        # 设置查询集
        self.fields['client'].queryset = Client.objects.filter(is_active=True).order_by('name')
        self.fields['client'].empty_label = '-- 选择客户 --'
        
        # 如果不是保存草稿，设置必填字段
        if not self.is_draft:
            # 设置基本信息字段为必填
            self.fields['gender'].required = True
            self.fields['birthplace'].required = True
            
            # 设置角色与关系字段为必填
            self.fields['role'].required = True
            self.fields['role'].empty_label = '-- 请选择 --'
            self.fields['relationship_level'].required = True
            self.fields['relationship_level'].empty_label = '-- 请选择 --'
            self.fields['decision_influence'].required = True
            self.fields['decision_influence'].empty_label = '-- 请选择 --'
        else:
            # 保存草稿时，所有字段都不是必填
            self.fields['gender'].required = False
            self.fields['birthplace'].required = False
            self.fields['role'].required = False
            self.fields['relationship_level'].required = False
            self.fields['decision_influence'].required = False
        
        # 设置其他空选项
        self.fields['contact_frequency'].empty_label = '-- 请选择 --'
        if 'tracking_cycle_days' in self.fields:
            self.fields['tracking_cycle_days'].empty_label = '-- 自动计算 --'
            self.fields['tracking_cycle_days'].help_text = '留空则根据角色和关系等级自动计算跟踪周期'
        self.fields['resume_source'].empty_label = '-- 请选择 --'
        
        # 如果是编辑模式，加载现有的多选字段值
        if self.instance and self.instance.pk:
            if self.instance.preferred_contact_methods:
                self.initial['preferred_contact_methods'] = self.instance.preferred_contact_methods
            if self.instance.tags:
                self.initial['tags'] = ', '.join(self.instance.tags)
    
    def clean_tags(self):
        """将逗号分隔的标签字符串转换为列表"""
        tags_str = self.cleaned_data.get('tags', '')
        if tags_str:
            # 分割并清理标签
            tags = [tag.strip() for tag in tags_str.split(',') if tag.strip()]
            return tags
        return []
    
    def clean_preferred_contact_methods(self):
        """确保偏好沟通方式返回列表"""
        methods = self.cleaned_data.get('preferred_contact_methods', [])
        return list(methods) if methods else []
    
    def clean(self):
        """验证联系方式至少填写两项（仅在提交时验证，保存草稿时不验证）"""
        cleaned_data = super().clean()
        
        # 如果是保存草稿，跳过验证
        action = cleaned_data.get('action', 'submit')
        if action == 'save_draft' or self.is_draft:
            return cleaned_data
        
        # 联系方式字段：phone, email, wechat, office_address
        phone = cleaned_data.get('phone', '').strip()
        email = cleaned_data.get('email', '').strip()
        wechat = cleaned_data.get('wechat', '').strip()
        office_address = cleaned_data.get('office_address', '').strip()
        
        # 统计已填写的联系方式数量
        filled_count = 0
        if phone:
            filled_count += 1
        if email:
            filled_count += 1
        if wechat:
            filled_count += 1
        if office_address:
            filled_count += 1
        
        # 至少需要填写两项
        if filled_count < 2:
            raise forms.ValidationError(
                '联系方式至少需要填写两项（手机、邮箱、微信号、办公地址中至少填写两项）'
            )
        
        return cleaned_data


class ContactCareerForm(forms.ModelForm):
    """联系人职业信息表单"""
    
    class Meta:
        model = ContactCareer
        fields = [
            'company', 'unified_credit_code', 'department', 'position',
            'join_date', 'leave_date'
        ]
        widgets = {
            'company': forms.TextInput(attrs={'class': 'form-control', 'placeholder': '就职公司'}),
            'unified_credit_code': forms.TextInput(attrs={'class': 'form-control', 'placeholder': '社会统一信用代码'}),
            'department': forms.TextInput(attrs={'class': 'form-control', 'placeholder': '部门'}),
            'position': forms.TextInput(attrs={'class': 'form-control', 'placeholder': '职位'}),
            'join_date': forms.DateInput(attrs={'class': 'form-control', 'type': 'date'}),
            'leave_date': forms.DateInput(attrs={'class': 'form-control', 'type': 'date'}),
        }
    
    def __init__(self, *args, **kwargs):
        # 获取is_draft参数
        self.is_draft = kwargs.pop('is_draft', False)
        super().__init__(*args, **kwargs)
        
        # 如果不是保存草稿，设置职业信息字段为必填
        if not self.is_draft:
            self.fields['company'].required = True
            self.fields['department'].required = True
            self.fields['position'].required = True
            self.fields['join_date'].required = True
        else:
            self.fields['company'].required = False
            self.fields['department'].required = False
            self.fields['position'].required = False
            self.fields['join_date'].required = False
    
    def clean(self):
        cleaned_data = super().clean()
        
        # 如果是保存草稿，跳过验证
        if self.is_draft:
            return cleaned_data
        
        join_date = cleaned_data.get('join_date')
        leave_date = cleaned_data.get('leave_date')
        
        if join_date and leave_date and leave_date < join_date:
            raise ValidationError('离职时间不能早于入职时间')
        
        return cleaned_data


# 创建内联表单集
from django.forms import inlineformset_factory

ContactCareerFormSet = inlineformset_factory(
    ClientContact,
    ContactCareer,
    form=ContactCareerForm,
    extra=1,  # 默认显示1个空表单
    can_delete=True,  # 允许删除
    min_num=1,  # 最少1个
    validate_min=True,  # 强制最少数量
)


class ContactColleagueForm(forms.ModelForm):
    """联系人同事关系人员表单"""
    
    class Meta:
        model = ContactColleague
        fields = ['department', 'name', 'position', 'phone']
        widgets = {
            'department': forms.TextInput(attrs={'class': 'form-control', 'placeholder': '部门'}),
            'name': forms.TextInput(attrs={'class': 'form-control', 'placeholder': '姓名'}),
            'position': forms.TextInput(attrs={'class': 'form-control', 'placeholder': '职位'}),
            'phone': forms.TextInput(attrs={'class': 'form-control', 'placeholder': '电话'}),
        }
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['name'].required = True


ContactColleagueFormSet = inlineformset_factory(
    ContactCareer,
    ContactColleague,
    form=ContactColleagueForm,
    extra=1,  # 默认显示1个空表单
    can_delete=True,  # 允许删除
    min_num=0,  # 最少0个
    validate_min=False,  # 不强制最少数量
)


class SchoolSelectWidget(forms.Select):
    """学校选择器，按地区分组显示"""
    
    def __init__(self, attrs=None, choices=()):
        super().__init__(attrs, choices)
        if attrs is None:
            attrs = {}
        attrs.setdefault('class', 'form-select school-select')
        self.attrs = attrs
    
    def optgroups(self, name, value, attrs=None):
        """重写optgroups方法，按地区分组"""
        groups = []
        has_selected = False
        
        # 获取所有学校并按地区分组
        schools = School.objects.filter(is_active=True).order_by('display_order', 'region', 'name')
        
        # 按地区分组
        schools_by_region = {}
        for school in schools:
            region_display = school.get_region_display()
            if region_display not in schools_by_region:
                schools_by_region[region_display] = []
            schools_by_region[region_display].append(school)
        
        # 添加空选项
        option_value = ''
        option_label = '-- 选择毕业学校 --'
        option_attrs = {'value': option_value}
        if str(option_value) == str(value):
            option_attrs['selected'] = True
            has_selected = True
        option = self.create_option(name, option_value, option_label, False, 0, attrs=option_attrs)
        groups.append((None, [option], 0))
        
        # 按地区分组添加选项
        for region_display in sorted(schools_by_region.keys()):
            region_schools = schools_by_region[region_display]
            group_options = []
            
            for school in region_schools:
                option_value = str(school.id)
                option_label = school.name
                # 添加标签显示
                tags = []
                if school.is_985:
                    tags.append('985')
                if school.is_211:
                    tags.append('211')
                if school.is_double_first_class:
                    tags.append('双一流')
                if tags:
                    option_label += f" ({', '.join(tags)})"
                
                option_attrs = {'value': option_value}
                if str(option_value) == str(value):
                    option_attrs['selected'] = True
                    has_selected = True
                
                option = self.create_option(name, option_value, option_label, False, len(group_options), attrs=option_attrs)
                group_options.append(option)
            
            if group_options:
                groups.append((region_display, group_options, len(groups)))
        
        return groups


class ContactEducationForm(forms.ModelForm):
    """联系人教育信息表单"""
    
    class Meta:
        model = ContactEducation
        fields = [
            'degree', 'school', 'school_name',
            'enrollment_date', 'graduation_date'
        ]
        widgets = {
            'degree': forms.Select(attrs={'class': 'form-select', 'placeholder': '选择学历'}),
            'school': SchoolSelectWidget(attrs={'class': 'form-select school-select', 'placeholder': '选择毕业学校'}),
            'school_name': forms.TextInput(attrs={
                'class': 'form-control', 
                'placeholder': '如果毕业学校不在列表中，可手动输入学校名称',
                'style': 'display: none;'  # 默认隐藏，通过JavaScript控制显示
            }),
            'enrollment_date': forms.DateInput(attrs={'class': 'form-control', 'type': 'date'}),
            'graduation_date': forms.DateInput(attrs={'class': 'form-control', 'type': 'date'}),
        }
    
    def __init__(self, *args, **kwargs):
        # 获取is_draft参数
        self.is_draft = kwargs.pop('is_draft', False)
        super().__init__(*args, **kwargs)
        
        # 如果不是保存草稿，设置教育信息字段为必填
        if not self.is_draft:
            self.fields['degree'].required = True
            self.fields['enrollment_date'].required = True
            self.fields['graduation_date'].required = True
        else:
            self.fields['degree'].required = False
            self.fields['enrollment_date'].required = False
            self.fields['graduation_date'].required = False
        
        # 学校字段不需要设置queryset，因为SchoolSelectWidget会自己处理
        self.fields['school'].required = False  # 允许为空，如果选择了学校则使用学校名称
    
    def clean(self):
        cleaned_data = super().clean()
        
        # 如果是保存草稿，跳过验证
        if self.is_draft:
            return cleaned_data
        
        enrollment_date = cleaned_data.get('enrollment_date')
        graduation_date = cleaned_data.get('graduation_date')
        school = cleaned_data.get('school')
        school_name = cleaned_data.get('school_name', '').strip()
        
        # 验证：学校或学校名称至少填写一个
        if not school and not school_name:
            raise ValidationError('请选择毕业学校或输入毕业学校名称')
        
        # 如果选择了学校，优先使用学校名称
        if school:
            cleaned_data['school_name'] = ''  # 清空手动输入的名称
        
        if enrollment_date and graduation_date and graduation_date < enrollment_date:
            raise ValidationError('毕业时间不能早于入学时间')
        
        return cleaned_data


# 创建教育信息内联表单集
ContactEducationFormSet = inlineformset_factory(
    ClientContact,
    ContactEducation,
    form=ContactEducationForm,
    extra=1,  # 默认显示1个空表单
    can_delete=True,  # 允许删除
    min_num=1,  # 最少1个
    validate_min=True,  # 强制最少数量
)


class VisitForm(forms.ModelForm):
    """拜访记录表单"""
    
    # 添加拜访日期字段（使用DateField）
    visit_date = forms.DateField(
        label='拜访日期',
        required=True,
        widget=forms.DateInput(attrs={'class': 'form-control', 'type': 'date', 'required': True})
    )
    
    class Meta:
        model = CustomerRelationship
        fields = [
            'client', 'visit_type', 'followup_method',
            'related_contacts', 'latitude', 'longitude', 'location_address',
        ]
        widgets = {
            'client': forms.Select(attrs={'class': 'form-select', 'required': True}),
            'visit_type': forms.Select(attrs={'class': 'form-select', 'required': True}),
            'followup_method': forms.Select(attrs={'class': 'form-select', 'required': True}),
            'related_contacts': forms.SelectMultiple(attrs={'class': 'form-select', 'size': 5}),
            'latitude': forms.NumberInput(attrs={'class': 'form-control', 'step': 'any', 'placeholder': '自动获取或手动输入'}),
            'longitude': forms.NumberInput(attrs={'class': 'form-control', 'step': 'any', 'placeholder': '自动获取或手动输入'}),
            'location_address': forms.TextInput(attrs={'class': 'form-control', 'readonly': True, 'placeholder': '自动获取地址'}),
        }
        labels = {
            'related_contacts': '拜访对象',
        }
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # 设置查询集
        self.fields['client'].queryset = Client.objects.filter(is_active=True).order_by('name')
        self.fields['related_contacts'].queryset = ClientContact.objects.all().select_related('client').order_by('client__name', 'name')
        self.fields['client'].empty_label = '-- 选择客户 --'
        self.fields['visit_type'].empty_label = '-- 选择拜访类型 --'
        
        # 如果有实例，设置visit_date的初始值（从followup_time提取日期）
        if self.instance and self.instance.pk and self.instance.followup_time:
            self.fields['visit_date'].initial = self.instance.followup_time.date()
    
    def save(self, commit=True):
        instance = super().save(commit=False)
        # 将visit_date转换为followup_time（设置为当天的开始时间）
        from django.utils import timezone
        from datetime import datetime, time
        visit_date = self.cleaned_data.get('visit_date')
        if visit_date:
            # 将日期转换为datetime（设置为当天的开始时间）
            instance.followup_time = timezone.make_aware(datetime.combine(visit_date, time.min))
        if commit:
            instance.save()
            # 保存多对多关系
            self.save_m2m()
        return instance


class RelationshipUpgradeForm(forms.ModelForm):
    """关系升级申请表单"""
    
    class Meta:
        model = CustomerRelationshipUpgrade
        fields = [
            'client', 'from_level', 'to_level', 'upgrade_reason', 'related_contacts',
        ]
        widgets = {
            'client': forms.Select(attrs={'class': 'form-select', 'required': True}),
            'from_level': forms.Select(attrs={'class': 'form-select', 'required': True}),
            'to_level': forms.Select(attrs={'class': 'form-select', 'required': True}),
            'upgrade_reason': forms.Textarea(attrs={'class': 'form-control', 'rows': 6, 'required': True}),
            'related_contacts': forms.SelectMultiple(attrs={'class': 'form-select', 'size': 5}),
        }
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # 设置查询集
        self.fields['client'].queryset = Client.objects.filter(is_active=True).order_by('name')
        self.fields['related_contacts'].queryset = ClientContact.objects.all().select_related('client').order_by('client__name', 'name')
        self.fields['client'].empty_label = '-- 选择客户 --'


class CollaborationTaskForm(forms.ModelForm):
    """协作任务表单"""
    
    class Meta:
        model = CustomerRelationshipCollaboration
        fields = [
            'client', 'task_type', 'description',
            'related_contacts', 'related_relationships',
        ]
        widgets = {
            'client': forms.Select(attrs={'class': 'form-select', 'required': True}),
            'task_type': forms.Select(attrs={'class': 'form-select', 'required': True}),
            'description': forms.Textarea(attrs={'class': 'form-control', 'rows': 6, 'required': True, 'placeholder': '请输入任务描述'}),
            'related_contacts': forms.SelectMultiple(attrs={'class': 'form-select', 'size': 5}),
            'related_relationships': forms.SelectMultiple(attrs={'class': 'form-select', 'size': 5}),
        }
        labels = {
            'client': '关联客户',
            'task_type': '任务类型',
            'description': '任务描述',
            'related_contacts': '关联客户人员',
            'related_relationships': '关联跟进记录',
        }
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        
        # 设置查询集
        self.fields['client'].queryset = Client.objects.filter(is_active=True).order_by('name')
        self.fields['related_contacts'].queryset = ClientContact.objects.all().select_related('client').order_by('client__name', 'name')
        self.fields['related_relationships'].queryset = CustomerRelationship.objects.all().select_related('client').order_by('-followup_time')
        
        # 设置空选项
        self.fields['client'].empty_label = '-- 选择客户 --'


class CollaborationAttachmentForm(forms.ModelForm):
    """协作任务附件上传表单"""
    
    class Meta:
        model = CustomerRelationshipCollaborationAttachment
        fields = ['file', 'file_name']
        widgets = {
            'file': forms.FileInput(attrs={
                'class': 'form-control',
                'accept': '.pdf,.doc,.docx,.xls,.xlsx,.ppt,.pptx,.jpg,.jpeg,.png,.zip,.rar,.7z',
                'required': True,
            }),
            'file_name': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': '文件名称（如未填写，将使用上传文件名）',
            }),
        }
        labels = {
            'file': '选择文件',
            'file_name': '文件名称',
        }
    
    def clean_file(self):
        """验证文件"""
        file = self.cleaned_data.get('file')
        if file:
            # 检查文件大小（限制为50MB）
            if file.size > 50 * 1024 * 1024:
                raise ValidationError('文件大小不能超过50MB')
            
            # 检查文件扩展名
            allowed_extensions = ['.pdf', '.doc', '.docx', '.xls', '.xlsx', '.ppt', '.pptx', 
                                '.jpg', '.jpeg', '.png', '.zip', '.rar', '.7z', '.dwg', '.dgn']
            file_ext = file.name.lower().split('.')[-1] if '.' in file.name else ''
            if file_ext and f'.{file_ext}' not in allowed_extensions:
                raise ValidationError(f'不支持的文件类型。允许的类型：{", ".join(allowed_extensions)}')
        
        return file
    
    def clean_file_name(self):
        """如果文件名称未填写，使用上传文件名"""
        file_name = self.cleaned_data.get('file_name')
        if not file_name and self.cleaned_data.get('file'):
            file_name = self.cleaned_data['file'].name
        return file_name



class VisitPlanForm(forms.ModelForm):
    """拜访计划表单（第一步：创建计划）"""
    
    # 参与人员多选字段（不在模型中，需要手动处理）
    participants = forms.ModelMultipleChoiceField(
        queryset=None,
        required=False,
        widget=forms.SelectMultiple(attrs={
            'class': 'form-select', 
            'size': '5',
            'title': '可多选，按住 Ctrl 键或 Command 键选择多个'
        }),
        label='参与人员'
    )
    
    class Meta:
        model = VisitPlan
        fields = [
            'client', 'plan_date', 'location', 'related_opportunity'
        ]
        widgets = {
            'client': forms.Select(attrs={'class': 'form-select', 'required': True, 'id': 'id_client'}),
            'plan_date': forms.DateInput(attrs={'class': 'form-control', 'type': 'date', 'required': True}),
            'location': forms.TextInput(attrs={'class': 'form-control', 'readonly': True, 'id': 'id_location', 'placeholder': '将根据客户办公地址自动填充'}),
            'related_opportunity': forms.Select(attrs={'class': 'form-select'}),
        }
    
    def __init__(self, *args, **kwargs):
        user = kwargs.pop('user', None)
        permission_set = kwargs.pop('permission_set', None)
        super().__init__(*args, **kwargs)
        
        # 根据用户过滤客户：只显示该用户作为负责人的、已审批通过的客户
        if user:
            from django.contrib.contenttypes.models import ContentType
            from backend.apps.workflow_engine.models import ApprovalInstance
            
            # 1. 只显示该用户作为负责人的客户
            base_queryset = Client.objects.filter(
                is_active=True,
                responsible_user=user
            )
            
            # 2. 只显示已审批通过的客户（通过 ApprovalInstance 判断）
            client_content_type = ContentType.objects.get_for_model(Client)
            approved_instance_ids = ApprovalInstance.objects.filter(
                content_type=client_content_type,
                status='approved'
            ).values_list('object_id', flat=True)
            
            # 只显示有审批通过记录的客户
            if approved_instance_ids:
                approved_clients = base_queryset.filter(id__in=approved_instance_ids)
                self.fields['client'].queryset = approved_clients.distinct().order_by('name')
            else:
                # 如果没有审批通过的客户，显示空列表
                self.fields['client'].queryset = Client.objects.none()
        else:
            # 没有用户信息，显示所有已审批通过的激活客户
            from django.contrib.contenttypes.models import ContentType
            from backend.apps.workflow_engine.models import ApprovalInstance
            
            client_content_type = ContentType.objects.get_for_model(Client)
            approved_instance_ids = ApprovalInstance.objects.filter(
                content_type=client_content_type,
                status='approved'
            ).values_list('object_id', flat=True)
            
            if approved_instance_ids:
                approved_clients = Client.objects.filter(
                    is_active=True,
                    id__in=approved_instance_ids
                )
                self.fields['client'].queryset = approved_clients.distinct().order_by('name')
            else:
                self.fields['client'].queryset = Client.objects.none()
        
        self.fields['client'].empty_label = '-- 选择客户 --'
        
        # 如果是编辑，将datetime字段转换为date显示
        if self.instance and self.instance.pk and self.instance.plan_date:
            self.fields['plan_date'].initial = self.instance.plan_date.date()
        else:
            # 新建时，设置日期字段默认值为当天
            from datetime import date
            today = date.today()
            self.fields['plan_date'].initial = today
        
        # 关联商机会根据选择的客户动态过滤（在模板中通过 JavaScript 实现）
        # 这里先设置一个空的查询集，实际选项会在前端根据客户选择动态更新
        self.fields['related_opportunity'].queryset = BusinessOpportunity.objects.none()
        self.fields['related_opportunity'].empty_label = '-- 请先选择客户 --'
        
        # 设置参与人员查询集（所有激活的用户）
        from backend.apps.system_management.models import User
        self.fields['participants'].queryset = User.objects.filter(is_active=True).order_by('username')
        
        # 如果是编辑模式，设置已选择的参与人员
        if self.instance and self.instance.pk and self.instance.participants:
            # 将逗号分隔的字符串转换为用户ID列表
            participant_names = [name.strip() for name in self.instance.participants.split(',') if name.strip()]
            # 根据用户名查找用户
            participant_users = User.objects.filter(
                username__in=participant_names
            ) | User.objects.filter(
                first_name__in=participant_names
            ) | User.objects.filter(
                last_name__in=participant_names
            )
            self.fields['participants'].initial = participant_users
    
    def clean(self):
        cleaned_data = super().clean()
        plan_date = cleaned_data.get('plan_date')
        
        # 将日期转换为datetime（设置为当天的开始时间 00:00:00）
        if plan_date:
            from django.utils import timezone
            from datetime import datetime
            if isinstance(plan_date, datetime):
                # 如果已经是datetime，只保留日期部分，时间设为00:00:00
                cleaned_data['plan_date'] = datetime.combine(plan_date.date(), datetime.min.time())
                cleaned_data['plan_date'] = timezone.make_aware(cleaned_data['plan_date'])
            elif hasattr(plan_date, 'date'):
                # 如果是date对象，转换为datetime
                cleaned_data['plan_date'] = datetime.combine(plan_date, datetime.min.time())
                cleaned_data['plan_date'] = timezone.make_aware(cleaned_data['plan_date'])
        
        return cleaned_data
    
    def save(self, commit=True):
        instance = super().save(commit=False)
        
        # 自动生成计划标题（如果未提供）
        if not instance.plan_title:
            client_name = instance.client.name if instance.client else '客户'
            plan_date_str = instance.plan_date.strftime('%Y-%m-%d') if instance.plan_date else ''
            instance.plan_title = f"{client_name} - {plan_date_str} 拜访计划"
        
        # 自动生成拜访目的（如果未提供）
        if not instance.plan_purpose:
            instance.plan_purpose = '客户拜访'
        
        # 处理参与人员：将选中的用户转换为逗号分隔的字符串
        selected_users = self.cleaned_data.get('participants', [])
        if selected_users:
            # 使用用户的显示名称（全名或用户名）
            participant_names = []
            for user in selected_users:
                name = user.get_full_name() or user.username
                participant_names.append(name)
            instance.participants = ', '.join(participant_names)
        else:
            instance.participants = ''
        
        if commit:
            instance.save()
        return instance


class VisitChecklistForm(forms.ModelForm):
    """沟通清单准备表单（第二步：沟通清单准备）"""
    
    class Meta:
        model = VisitPlan
        fields = ['communication_checklist']
        widgets = {
            'communication_checklist': forms.Textarea(attrs={
                'class': 'form-control', 
                'rows': 10, 
                'required': True,
                'placeholder': '请输入沟通清单内容，包括：\n1. 需要沟通的关键问题\n2. 需要准备的资料和文件\n3. 需要展示的产品或方案\n4. 其他注意事项'
            }),
        }
        labels = {
            'communication_checklist': '沟通清单',
        }


class VisitCheckinForm(forms.ModelForm):
    """拜访定位打卡表单（第三步：拜访定位打卡）"""
    
    class Meta:
        model = VisitCheckin
        fields = ['checkin_time', 'checkin_location', 'latitude', 'longitude', 'notes']
        widgets = {
            'checkin_time': forms.DateTimeInput(attrs={'class': 'form-control', 'type': 'datetime-local', 'required': True}),
            'checkin_location': forms.TextInput(attrs={'class': 'form-control', 'required': True, 'readonly': True, 'placeholder': '自动获取或手动输入'}),
            'latitude': forms.NumberInput(attrs={'class': 'form-control', 'step': 'any', 'placeholder': '自动获取或手动输入'}),
            'longitude': forms.NumberInput(attrs={'class': 'form-control', 'step': 'any', 'placeholder': '自动获取或手动输入'}),
            'notes': forms.Textarea(attrs={'class': 'form-control', 'rows': 4, 'placeholder': '请输入备注信息（可选）'}),
        }
        labels = {
            'checkin_time': '打卡时间',
            'checkin_location': '打卡地点',
            'latitude': '纬度',
            'longitude': '经度',
            'notes': '备注',
        }


class VisitReviewForm(forms.ModelForm):
    """拜访结果复盘表单（第四步：拜访结果复盘）"""
    
    class Meta:
        model = VisitReview
        fields = [
            'visit_result', 'customer_feedback', 'key_points', 
            'next_actions', 'satisfaction_score', 'effectiveness'
        ]
        widgets = {
            'visit_result': forms.Textarea(attrs={
                'class': 'form-control', 
                'rows': 6, 
                'required': True,
                'placeholder': '请详细记录本次拜访的结果和关键信息'
            }),
            'customer_feedback': forms.Textarea(attrs={
                'class': 'form-control', 
                'rows': 5,
                'placeholder': '请记录客户的主要反馈和意见'
            }),
            'key_points': forms.Textarea(attrs={
                'class': 'form-control', 
                'rows': 5,
                'placeholder': '请总结本次拜访的关键要点和收获'
            }),
            'next_actions': forms.Textarea(attrs={
                'class': 'form-control', 
                'rows': 5,
                'placeholder': '请列出后续需要跟进的事项和行动计划'
            }),
            'satisfaction_score': forms.NumberInput(attrs={
                'class': 'form-control', 
                'min': 1, 
                'max': 10,
                'placeholder': '1-10分'
            }),
            'effectiveness': forms.Select(attrs={'class': 'form-select'}),
        }
        labels = {
            'visit_result': '拜访结果',
            'customer_feedback': '客户反馈',
            'key_points': '关键要点',
            'next_actions': '下一步行动',
            'satisfaction_score': '满意度评分',
            'effectiveness': '拜访效果',
        }


class AuthorizationLetterForm(forms.ModelForm):
    """业务委托书表单"""
    
    class Meta:
        model = AuthorizationLetter
        fields = [
            # 基本信息
            'project_number', 'letter_date', 'business_manager',
            # 保留其他字段
            'project_name', 'status', 'client', 'opportunity', 'provisional_price',
            # 委托单位信息
            'client_name', 'client_contact', 'client_representative', 'client_phone', 'client_email', 'client_address',
            # 服务单位信息
            'trustee_name', 'trustee_representative', 'trustee_phone', 'trustee_email', 'trustee_address',
            # 服务费确定原则
            'result_optimization_rate', 'process_optimization_rate', 
            'detailed_review_unit_price_min', 'detailed_review_unit_price_max',
            'fee_determination_principle',
            # 结算与支付
            'settlement_review_process', 'payment_schedule',
            # 补充约定
            'supplementary_agreement',
            # 委托期限
            'start_date', 'end_date',
            # 关联信息
            'opportunity', 'project', 'notes',
        ]
        widgets = {
            'project_number': forms.TextInput(attrs={
                'class': 'form-control',
                'readonly': True,
                'placeholder': '系统自动生成，例如：HT-2025-0001'
            }),
            'letter_date': forms.DateInput(attrs={
                'class': 'form-control',
                'type': 'date',
                'required': True
            }),
            'business_manager': forms.Select(attrs={
                'class': 'form-select',
                'required': True
            }),
            'client': forms.Select(attrs={
                'class': 'form-select',
                'required': True,
                'id': 'id_client'
            }),
            'opportunity': forms.Select(attrs={'class': 'form-select'}),
            'provisional_price': forms.NumberInput(attrs={
                'class': 'form-control',
                'step': '0.01',
                'placeholder': '0.00'
            }),
            'project_name': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': '项目名称'
            }),
            'status': forms.Select(attrs={'class': 'form-select'}),
            'client_name': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': '单位名称',
                'readonly': True
            }),
            'client_contact': forms.Select(attrs={
                'class': 'form-select',
                'id': 'id_client_contact'
            }),
            'client_representative': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': '单位代表',
                'readonly': True
            }),
            'client_phone': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': '联系电话'
            }),
            'client_email': forms.EmailInput(attrs={
                'class': 'form-control',
                'placeholder': '电子邮箱'
            }),
            'client_address': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': '收件地址'
            }),
            'trustee_name': forms.TextInput(attrs={
                'class': 'form-control',
                'value': '四川维海科技有限公司',
                'placeholder': '服务单位',
                'required': True
            }),
            'trustee_representative': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': '单位代表，例如：田霞'
            }),
            'trustee_phone': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': '联系电话，例如：13666287899/02883574973'
            }),
            'trustee_email': forms.EmailInput(attrs={
                'class': 'form-control',
                'placeholder': '电子邮箱，例如：whkj@vihgroup.com.cn'
            }),
            'trustee_address': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': '收件地址，例如：四川省成都市武侯区武科西一路瑞景产业园1号楼5A01'
            }),
            'result_optimization_rate': forms.NumberInput(attrs={
                'class': 'form-control',
                'step': '0.01',
                'min': '10',
                'max': '15',
                'placeholder': '10-15'
            }),
            'process_optimization_rate': forms.NumberInput(attrs={
                'class': 'form-control',
                'step': '0.01',
                'min': '10',
                'max': '15',
                'placeholder': '10-15'
            }),
            'detailed_review_unit_price_min': forms.NumberInput(attrs={
                'class': 'form-control',
                'step': '0.01',
                'placeholder': '1.5'
            }),
            'detailed_review_unit_price_max': forms.NumberInput(attrs={
                'class': 'form-control',
                'step': '0.01',
                'placeholder': '3.0'
            }),
            'fee_determination_principle': forms.Textarea(attrs={
                'class': 'form-control',
                'rows': 6,
                'placeholder': '服务费确定原则说明（可选）'
            }),
            'settlement_review_process': forms.Textarea(attrs={
                'class': 'form-control',
                'rows': 8,
                'placeholder': '结算审核流程说明（可选）'
            }),
            'payment_schedule': forms.HiddenInput(),  # 使用JSON字段，通过JavaScript处理
            'supplementary_agreement': forms.Textarea(attrs={
                'class': 'form-control',
                'rows': 4,
                'placeholder': '补充约定（可选）'
            }),
            'start_date': forms.DateInput(attrs={
                'class': 'form-control',
                'type': 'date'
            }),
            'end_date': forms.DateInput(attrs={
                'class': 'form-control',
                'type': 'date'
            }),
            'project': forms.Select(attrs={'class': 'form-select'}),
            'notes': forms.Textarea(attrs={
                'class': 'form-control',
                'rows': 3,
                'placeholder': '备注信息（可选）'
            }),
        }
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        
        # 获取当前实例的客户（如果有）
        client = None
        if self.instance and self.instance.pk:
            client = self.instance.client
        
        # 客户列表（用于委托单位信息的关联客户）
        from .models import Client
        if 'client' in self.fields:
            self.fields['client'].queryset = Client.objects.filter(is_active=True).order_by('name')
            self.fields['client'].empty_label = '-- 选择客户 --'
            self.fields['client'].required = True
        
        # 根据客户过滤商机
        opportunity_queryset = BusinessOpportunity.objects.filter(
            status__in=['potential', 'initial_contact', 'requirement_confirmed', 'quotation', 'negotiation']
        )
        if client:
            # 如果已有客户，只显示该客户的商机
            opportunity_queryset = opportunity_queryset.filter(client=client)
        
        if 'opportunity' in self.fields:
            self.fields['opportunity'].queryset = opportunity_queryset.select_related('client').order_by('-created_time')
            self.fields['opportunity'].empty_label = '-- 选择商机（可选） --'
        
        self.fields['project'].queryset = Project.objects.filter(
            status__in=['planning', 'in_progress', 'completed']
        ).order_by('-created_time')
        
        # 设置空选项
        self.fields['project'].empty_label = '-- 选择项目（可选） --'
        
        # 商务经理列表（具有商务经理角色的用户）
        if 'business_manager' in self.fields:
            from django.contrib.auth import get_user_model
            User = get_user_model()
            business_managers = User.objects.filter(
                roles__code='business_manager',
                is_active=True
            ).distinct().order_by('username')
            if not business_managers.exists():
                # 如果没有找到商务经理角色，显示所有活跃用户
                business_managers = User.objects.filter(is_active=True).order_by('username')[:50]
            self.fields['business_manager'].queryset = business_managers
            self.fields['business_manager'].empty_label = '-- 选择商务经理 --'
        
        # 项目编号字段设置为只读（系统自动生成）
        if 'project_number' in self.fields:
            self.fields['project_number'].required = False
        
        # 为字段添加 ID，方便 JavaScript 使用
        if 'client' in self.fields:
            self.fields['client'].widget.attrs['id'] = 'id_client'
        if 'opportunity' in self.fields:
            self.fields['opportunity'].widget.attrs['id'] = 'id_opportunity'
        if 'client_name' in self.fields:
            self.fields['client_name'].widget.attrs['id'] = 'id_client_name'
        
    def clean(self):
        """验证日期范围，并将ModelMultipleChoiceField的值转换为ID列表"""
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
            'template_type': forms.Select(attrs={
                'class': 'form-select',
                'required': True
            }),
            'category': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': '模板分类（可选）'
            }),
            'status': forms.Select(attrs={
                'class': 'form-select'
            }),
            'description': forms.Textarea(attrs={
                'class': 'form-control',
                'rows': 4,
                'placeholder': '模板说明（可选）'
            }),
            'template_content': forms.HiddenInput(),  # 使用JSON字段，通过JavaScript处理
            'variables': forms.HiddenInput(),  # 使用JSON字段，通过JavaScript处理
            'template_file': forms.FileInput(attrs={
                'class': 'form-control',
                'accept': '.doc,.docx,.pdf,.xls,.xlsx,.ppt,.pptx',
            }),
        }
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        
        # 如果是编辑模式，初始化JSON字段
        if self.instance and self.instance.pk:
            if self.instance.template_content:
                # 将JSON转换为字符串，用于前端显示
                import json
                self.initial['template_content'] = json.dumps(self.instance.template_content, ensure_ascii=False, indent=2)
            if self.instance.variables:
                import json
                self.initial['variables'] = json.dumps(self.instance.variables, ensure_ascii=False, indent=2)
    
    def clean_template_content(self):
        """验证模板内容"""
        import json
        template_content = self.cleaned_data.get('template_content')
        if isinstance(template_content, str):
            try:
                return json.loads(template_content)
            except json.JSONDecodeError:
                raise forms.ValidationError('模板内容格式错误，必须是有效的JSON格式')
        return template_content or {}
    
    def clean_variables(self):
        """验证变量列表"""
        import json
        variables = self.cleaned_data.get('variables')
        if isinstance(variables, str):
            try:
                return json.loads(variables)
            except json.JSONDecodeError:
                raise forms.ValidationError('变量列表格式错误，必须是有效的JSON格式')
        return variables or []
    
    def clean_template_file(self):
        """验证模板文件"""
        template_file = self.cleaned_data.get('template_file')
        if template_file:
            # 检查文件大小（限制为50MB）
            max_size = 50 * 1024 * 1024  # 50MB
            if template_file.size > max_size:
                raise forms.ValidationError(f'文件大小不能超过50MB，当前文件大小为 {template_file.size / 1024 / 1024:.2f}MB')
            
            # 检查文件扩展名
            import os
            ext = os.path.splitext(template_file.name)[1].lower()
            allowed_extensions = ['.doc', '.docx', '.pdf', '.xls', '.xlsx', '.ppt', '.pptx']
            if ext not in allowed_extensions:
                raise forms.ValidationError(f'不支持的文件格式，仅支持：{", ".join(allowed_extensions)}')
        
        return template_file


class BusinessExpenseApplicationForm(forms.ModelForm):
    """业务费申请表单"""
    
    class Meta:
        model = BusinessExpenseApplication
        fields = [
            'client', 'expense_type', 'amount', 'expense_date',
            'description', 'related_contacts', 'attachment'
        ]
        widgets = {
            'client': forms.Select(attrs={'class': 'form-select', 'required': True}),
            'expense_type': forms.Select(attrs={'class': 'form-select', 'required': True}),
            'amount': forms.NumberInput(attrs={'class': 'form-control', 'required': True, 'step': '0.01', 'min': '0.01'}),
            'expense_date': forms.DateInput(attrs={'class': 'form-control', 'type': 'date', 'required': True}),
            'description': forms.Textarea(attrs={'class': 'form-control', 'rows': 4, 'required': True, 'placeholder': '请详细说明费用用途和必要性'}),
            'related_contacts': forms.SelectMultiple(attrs={'class': 'form-select', 'size': 5}),
            'attachment': forms.FileInput(attrs={'class': 'form-control', 'accept': '.pdf,.jpg,.jpeg,.png,.doc,.docx'}),
        }
    
    def __init__(self, *args, **kwargs):
        self.is_draft = kwargs.pop('is_draft', False)
        super().__init__(*args, **kwargs)
        
        # 设置客户选择
        from backend.apps.customer_management.models import Client
        self.fields['client'].queryset = Client.objects.all().order_by('name')
        self.fields['client'].empty_label = '-- 请选择客户 --'
        
        # 设置关联联系人选择
        from backend.apps.customer_management.models import ClientContact
        self.fields['related_contacts'].queryset = ClientContact.objects.all().select_related('client').order_by('client__name', 'name')
        self.fields['related_contacts'].required = False
        self.fields['related_contacts'].help_text = '可选，选择与此费用相关的客户人员'
        
        # 设置费用日期默认值为今天
        if not self.instance.pk:
            from django.utils import timezone
            self.fields['expense_date'].initial = timezone.now().date()
        
        # 如果是草稿，不强制必填
        if self.is_draft:
            self.fields['client'].required = False
            self.fields['expense_type'].required = False
            self.fields['amount'].required = False
            self.fields['expense_date'].required = False
            self.fields['description'].required = False
    
    def clean_amount(self):
        amount = self.cleaned_data.get('amount')
        if amount and amount <= 0:
            raise forms.ValidationError('费用金额必须大于0')
        return amount
    
    def clean(self):
        cleaned_data = super().clean()
        if self.is_draft:
            return cleaned_data
        
        # 验证必填字段
        if not cleaned_data.get('client'):
            raise forms.ValidationError({'client': '请选择客户'})
        if not cleaned_data.get('expense_type'):
            raise forms.ValidationError({'expense_type': '请选择费用类型'})
        if not cleaned_data.get('amount'):
            raise forms.ValidationError({'amount': '请输入费用金额'})
        if not cleaned_data.get('expense_date'):
            raise forms.ValidationError({'expense_date': '请选择费用发生日期'})
        if not cleaned_data.get('description'):
            raise forms.ValidationError({'description': '请输入费用说明'})
        
        return cleaned_data


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
            'contract': '关联合同',
            'client': '客户',
            'project': '关联项目',
            'negotiation_type': '洽谈类型',
            'status': '洽谈状态',
            'title': '洽谈主题',
            'content': '洽谈内容',
            'participants': '参与人员（我方）',
            'client_participants': '客户参与人员',
            'negotiation_date': '洽谈日期',
            'negotiation_start_time': '开始时间',
            'negotiation_end_time': '结束时间',
            'next_negotiation_date': '下次洽谈日期',
            'result_summary': '洽谈结果摘要',
            'agreed_items': '已达成事项',
            'pending_items': '待解决事项',
            'attachments': '附件说明',
            'notes': '备注',
        }
        help_texts = {
            'contract': '可选，如果洽谈时合同尚未创建可留空',
            'client': '如果未关联合同，则必须填写客户',
            'negotiation_type': '选择本次洽谈的主要类型',
            'content': '详细记录洽谈过程中的讨论内容、双方意见等',
            'client_participants': '客户方参与洽谈的人员，多个用逗号分隔',
        }
    
    def __init__(self, *args, **kwargs):
        user = kwargs.pop('user', None)
        super().__init__(*args, **kwargs)
        
        # 限制合同选择：只显示当前用户有权限查看的合同
        if user:
            from backend.core.views import get_user_permission_codes, _permission_granted
            permission_set = get_user_permission_codes(user)
            if not _permission_granted('customer_management.client.view', permission_set):
                self.fields['contract'].queryset = BusinessContract.objects.none()
            else:
                self.fields['contract'].queryset = BusinessContract.objects.filter(is_active=True).order_by('-created_time')[:100]
        
        # 限制客户选择：只显示活跃客户
        self.fields['client'].queryset = Client.objects.filter(is_active=True).order_by('name')[:100]
        
        # 限制项目选择
        if user:
            from backend.core.views import get_user_permission_codes, _permission_granted
            permission_set = get_user_permission_codes(user)
            if _permission_granted('production_management.view_all', permission_set):
                # Project模型没有is_active字段，直接查询所有项目
                self.fields['project'].queryset = Project.objects.all().order_by('-created_time')[:100]
            else:
                self.fields['project'].queryset = Project.objects.none()
        
        # 限制参与人员选择：只显示活跃用户
        if user:
            from backend.apps.system_management.models import User
            self.fields['participants'].queryset = User.objects.filter(is_active=True).order_by('username')
    
    def clean(self):
        cleaned_data = super().clean()
        contract = cleaned_data.get('contract')
        client = cleaned_data.get('client')
        
        # 验证：如果未关联合同，则必须填写客户
        if not contract and not client:
            raise forms.ValidationError('请至少选择关联合同或客户')
        
        # 如果关联了合同，自动填充客户
        if contract and contract.client:
            cleaned_data['client'] = contract.client
        
        return cleaned_data


# 尝试导入 ContactInfoChange（如果模型存在）
try:
    from .models import ContactInfoChange
except ImportError:
    ContactInfoChange = None


class ContactInfoChangeForm(forms.ModelForm):
    """人员信息变更申请表单"""
    
    class Meta:
        # 注意：如果 ContactInfoChange 模型已被删除，此表单将无法使用
        if ContactInfoChange is None:
            # 如果模型不存在，创建一个虚拟的 Meta 类
            model = None
            fields = []
        else:
            model = ContactInfoChange
            fields = [
                'contact',
                'change_type',
                'change_reason',
                'change_content',
                'approval_status',
            ]
            widgets = {
                'contact': forms.Select(attrs={'class': 'form-select'}),
                'change_type': forms.Select(attrs={'class': 'form-select'}),
                'change_reason': forms.Textarea(attrs={
                    'class': 'form-control',
                    'rows': 4,
                    'placeholder': '请说明变更的原因和依据'
                }),
                'change_content': forms.Textarea(attrs={
                    'class': 'form-control',
                    'rows': 6,
                    'placeholder': 'JSON格式：存储变更的字段和对应的旧值、新值'
                }),
                'approval_status': forms.Select(attrs={'class': 'form-select'}),
            }
            labels = {
                'contact': '关联联系人',
                'change_type': '变更类型',
                'change_reason': '变更原因',
                'change_content': '变更内容',
                'approval_status': '审批状态',
            }
    
    def __init__(self, *args, **kwargs):
        user = kwargs.pop('user', None)
        super().__init__(*args, **kwargs)
        
        if ContactInfoChange is None:
            return
        
        # 设置联系人查询集
        from .models import ClientContact
        self.fields['contact'].queryset = ClientContact.objects.all().order_by('name')
        self.fields['contact'].empty_label = '-- 选择联系人 --'
        
        # 如果是创建模式，设置默认创建人
        if user and (not self.instance or not self.instance.pk):
            # created_by 字段通常不在表单中，由视图函数设置
            pass
    
    def clean(self):
        if ContactInfoChange is None:
            raise forms.ValidationError('ContactInfoChange 模型不存在，无法使用此表单')
        
        cleaned_data = super().clean()
        change_type = cleaned_data.get('change_type')
        change_reason = cleaned_data.get('change_reason')
        change_content = cleaned_data.get('change_content')
        
        # 验证必填字段
        if not change_type:
            raise forms.ValidationError({'change_type': '请选择变更类型'})
        if not change_reason:
            raise forms.ValidationError({'change_reason': '请输入变更原因'})
        
        # 验证 change_content 是否为有效的 JSON
        if change_content:
            try:
                import json
                if isinstance(change_content, str):
                    json.loads(change_content)
                elif not isinstance(change_content, dict):
                    raise forms.ValidationError({
                        'change_content': '变更内容必须是有效的 JSON 格式'
                    })
            except json.JSONDecodeError:
                raise forms.ValidationError({
                    'change_content': '变更内容必须是有效的 JSON 格式'
                })
        
        return cleaned_data
