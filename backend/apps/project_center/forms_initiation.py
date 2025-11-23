"""项目立项表单"""
from django import forms
from django.core.exceptions import ValidationError
from .models import Project, ProjectInitiationApproval, ServiceType, ServiceProfession
from backend.apps.customer_success.models import Client
from backend.apps.system_management.models import Department, User


class ProjectInitiationStep1Form(forms.ModelForm):
    """项目立项 - 第一步：上传凭证"""
    class Meta:
        model = Project
        fields = ['subsidiary', 'initiation_document_type', 'initiation_document']
        widgets = {
            'subsidiary': forms.Select(attrs={
                'class': 'form-select',
                'required': True,
            }),
            'initiation_document_type': forms.Select(attrs={
                'class': 'form-select',
                'required': True,
            }),
            'initiation_document': forms.FileInput(attrs={
                'class': 'form-control',
                'accept': '.pdf,.doc,.docx,.jpg,.jpeg,.png',
                'required': True,
            }),
        }
        labels = {
            'subsidiary': '子公司',
            'initiation_document_type': '立项凭证类型',
            'initiation_document': '立项凭证文件',
        }
    
    def clean_initiation_document(self):
        document = self.cleaned_data.get('initiation_document')
        if document and document.size > 10 * 1024 * 1024:  # 10MB
            raise ValidationError('文件大小不能超过10MB')
        return document


class ProjectInitiationStep2Form(forms.ModelForm):
    """项目立项 - 第二步：填写基本信息"""
    
    # 项目规模（分批次）- 使用隐藏字段存储 JSON 数据
    project_batches_json = forms.CharField(
        required=False,
        widget=forms.HiddenInput(),
        label='项目规模（分批次）'
    )
    
    # 服务范围
    service_scope = forms.CharField(
        max_length=500,
        required=False,
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': '例如：一批次、二批次（多个用逗号分隔）',
        }),
        label='服务范围'
    )
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['service_type'].queryset = ServiceType.objects.all().order_by('order', 'id')
        # 如果有实例且存在批次数据，将其转换为 JSON 字符串
        if self.instance and self.instance.pk and self.instance.project_batches:
            import json
            self.fields['project_batches_json'].initial = json.dumps(self.instance.project_batches, ensure_ascii=False)
        
        # 设置必填字段（除描述、说明外）
        self.fields['name'].required = True
        self.fields['service_type'].required = True
        self.fields['service_professions'].required = True
        self.fields['business_type'].required = True
        self.fields['design_stage'].required = True
        self.fields['project_address'].required = True
        # 描述和别名保持可选
        self.fields['alias'].required = False
        self.fields['description'].required = False
        
        # 配置service_professions字段
        # 在POST请求时，根据提交的service_type设置queryset
        # 在GET请求时，如果有实例且已选择服务类型，则加载对应的专业
        if self.data and 'service_type' in self.data:
            # POST请求：根据提交的service_type设置queryset
            try:
                service_type_id = self.data.get('service_type')
                if service_type_id:
                    self.fields['service_professions'].queryset = ServiceProfession.objects.filter(
                        service_type_id=service_type_id
                    ).order_by('order', 'id')
                else:
                    self.fields['service_professions'].queryset = ServiceProfession.objects.all()
            except (ValueError, TypeError):
                self.fields['service_professions'].queryset = ServiceProfession.objects.all()
        elif self.instance and self.instance.pk and self.instance.service_type:
            # GET请求：如果有实例且已选择服务类型，则加载对应的专业
            self.fields['service_professions'].queryset = ServiceProfession.objects.filter(
                service_type=self.instance.service_type
            ).order_by('order', 'id')
        else:
            # 初始状态：设置为所有专业，避免验证错误
            self.fields['service_professions'].queryset = ServiceProfession.objects.all()
        
        # 使用CheckboxSelectMultiple widget，但通过JavaScript动态加载
        # 不设置widget，让Django使用默认的CheckboxSelectMultiple，但我们在模板中自定义渲染
    
    class Meta:
        model = Project
        fields = [
            'name', 'alias', 'description',
            'service_type', 'service_professions', 'business_type', 'design_stage',
            'project_address', 'service_scope',
            # 保留原有字段用于向后兼容，但将在模板中隐藏
            'building_area', 'aboveground_floors', 'underground_floors',
            'structure_type', 'building_height',
        ]
        widgets = {
            'name': forms.TextInput(attrs={
                'class': 'form-control',
                'required': True,
                'placeholder': '请输入项目名称',
            }),
            'alias': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': '项目别名（可选）',
            }),
            'description': forms.Textarea(attrs={
                'class': 'form-control',
                'rows': 3,
                'placeholder': '项目描述（可选）',
            }),
            'service_type': forms.Select(attrs={
                'class': 'form-select',
                'required': True,
            }),
            'business_type': forms.Select(attrs={
                'class': 'form-select',
                'required': True,
            }),
            'design_stage': forms.Select(attrs={
                'class': 'form-select',
                'required': True,
            }),
            'project_address': forms.TextInput(attrs={
                'class': 'form-control',
                'required': True,
                'placeholder': '项目地址（与图纸保持一致）',
            }),
            'building_area': forms.NumberInput(attrs={
                'class': 'form-control',
                'step': '0.01',
                'placeholder': '建筑面积（㎡）',
            }),
            'aboveground_floors': forms.NumberInput(attrs={
                'class': 'form-control',
                'placeholder': '地上层数',
            }),
            'underground_floors': forms.NumberInput(attrs={
                'class': 'form-control',
                'placeholder': '地下层数',
            }),
            'structure_type': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': '结构形式',
            }),
            'building_height': forms.NumberInput(attrs={
                'class': 'form-control',
                'step': '0.01',
                'placeholder': '建筑高度（米）',
            }),
        }
        labels = {
            'name': '项目名称',
            'alias': '项目别名',
            'description': '项目描述',
            'service_type': '服务类型',
            'business_type': '项目业态',
            'design_stage': '图纸阶段',
            'project_address': '项目地址（与图纸保持一致）',
            'service_scope': '服务范围',
            'building_area': '建筑面积（㎡）',
            'aboveground_floors': '地上层数',
            'underground_floors': '地下层数',
            'structure_type': '结构形式',
            'building_height': '建筑高度（米）',
        }
    
    def clean_service_professions(self):
        """验证服务专业"""
        service_professions = self.cleaned_data.get('service_professions')
        service_type = self.cleaned_data.get('service_type')
        
        if not service_professions:
            raise ValidationError('请至少选择一个服务专业')
        
        # 验证所选专业是否属于当前服务类型
        if service_type:
            valid_profession_ids = ServiceProfession.objects.filter(
                service_type=service_type
            ).values_list('id', flat=True)
            
            selected_ids = set(p.id for p in service_professions)
            valid_profession_ids_set = set(valid_profession_ids)
            invalid_ids = selected_ids - valid_profession_ids_set
            
            if invalid_ids:
                invalid_names = ServiceProfession.objects.filter(id__in=invalid_ids).values_list('name', flat=True)
                raise ValidationError(f'所选服务专业不属于当前服务类型：{", ".join(invalid_names)}')
        
        return service_professions
    
    def clean_project_batches_json(self):
        """验证并解析项目批次 JSON 数据"""
        import json
        batches_json = self.cleaned_data.get('project_batches_json', '[]')
        if not batches_json:
            return []
        try:
            batches = json.loads(batches_json) if isinstance(batches_json, str) else batches_json
            # 验证数据格式
            for batch in batches:
                if not isinstance(batch, dict):
                    raise ValidationError('批次数据格式错误')
                required_fields = ['batch_name', 'total_area', 'aboveground_area', 'underground_area', 'aboveground_floors', 'underground_floors']
                for field in required_fields:
                    if field not in batch:
                        raise ValidationError(f'批次数据缺少必填字段：{field}')
            return batches
        except json.JSONDecodeError:
            raise ValidationError('项目批次数据格式错误，必须是有效的 JSON')
    
    def save(self, commit=True):
        instance = super().save(commit=False)
        # 处理项目批次数据
        batches_json = self.cleaned_data.get('project_batches_json', '[]')
        if batches_json:
            try:
                import json
                batches = json.loads(batches_json) if isinstance(batches_json, str) else batches_json
                instance.project_batches = batches
                
                # 计算总建筑面积（如果存在批次数据）
                if batches:
                    total_area = sum(float(batch.get('total_area', 0) or 0) for batch in batches)
                    total_aboveground_area = sum(float(batch.get('aboveground_area', 0) or 0) for batch in batches)
                    total_underground_area = sum(float(batch.get('underground_area', 0) or 0) for batch in batches)
                    instance.building_area = total_area
                    instance.aboveground_area = total_aboveground_area
                    instance.underground_area = total_underground_area
            except (json.JSONDecodeError, ValueError, TypeError):
                pass  # 如果解析失败，保持原值
        
        if commit:
            instance.save()
            self.save_m2m()
        return instance


class ProjectInitiationStep3Form(forms.ModelForm):
    """项目立项 - 第三步：配置参与方信息"""
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # 设置必填字段
        # 委托单位字段
        self.fields['client_company_name'].required = True
        self.fields['client_credit_code'].required = True
        self.fields['client_registered_capital'].required = True
        self.fields['client_registered_address'].required = True
        self.fields['client_company_type'].required = True
        self.fields['client_ownership_type'].required = True
        self.fields['client_established_date'].required = True
        self.fields['client_contact_person'].required = True
        self.fields['client_phone'].required = True
        # 启信宝字段为可选
        self.fields['client_litigation_count'].required = False
        self.fields['client_enforcement_count'].required = False
        self.fields['client_final_case_count'].required = False
        self.fields['client_restriction_count'].required = False
        
        # 设计单位字段
        self.fields['design_company'].required = True
        self.fields['design_credit_code'].required = True
        self.fields['design_contact_person'].required = True
        self.fields['design_phone'].required = True
    
    class Meta:
        model = Project
        fields = [
            # 委托单位字段
            'client_company_name', 'client_credit_code', 'client_registered_capital',
            'client_registered_address', 'client_company_type', 'client_ownership_type',
            'client_established_date', 'client_contact_person', 'client_phone',
            'client_litigation_count', 'client_enforcement_count', 'client_final_case_count',
            'client_restriction_count',
            # 设计单位字段
            'design_company', 'design_credit_code', 'design_contact_person', 'design_phone',
        ]
        widgets = {
            # 委托单位
            'client_company_name': forms.TextInput(attrs={
                'class': 'form-control',
                'required': True,
                'placeholder': '委托单位名称',
            }),
            'client_credit_code': forms.TextInput(attrs={
                'class': 'form-control',
                'required': True,
                'placeholder': '统一社会信用代码',
                'maxlength': 50,
            }),
            'client_registered_capital': forms.NumberInput(attrs={
                'class': 'form-control',
                'required': True,
                'step': '0.01',
                'placeholder': '注册资本（万元）',
            }),
            'client_registered_address': forms.TextInput(attrs={
                'class': 'form-control',
                'required': True,
                'placeholder': '注册地址',
            }),
            'client_company_type': forms.Select(attrs={
                'class': 'form-select',
                'required': True,
            }),
            'client_ownership_type': forms.Select(attrs={
                'class': 'form-select',
                'required': True,
            }),
            'client_established_date': forms.DateInput(attrs={
                'class': 'form-control',
                'type': 'date',
                'required': True,
            }),
            'client_contact_person': forms.TextInput(attrs={
                'class': 'form-control',
                'required': True,
                'placeholder': '项目负责人',
            }),
            'client_phone': forms.TextInput(attrs={
                'class': 'form-control',
                'required': True,
                'placeholder': '项目负责人联系电话',
            }),
            'client_litigation_count': forms.NumberInput(attrs={
                'class': 'form-control',
                'placeholder': '启信宝公开数量',
                'min': 0,
            }),
            'client_enforcement_count': forms.NumberInput(attrs={
                'class': 'form-control',
                'placeholder': '启信宝公开数量',
                'min': 0,
            }),
            'client_final_case_count': forms.NumberInput(attrs={
                'class': 'form-control',
                'placeholder': '启信宝公开数量',
                'min': 0,
            }),
            'client_restriction_count': forms.NumberInput(attrs={
                'class': 'form-control',
                'placeholder': '启信宝公开数量',
                'min': 0,
            }),
            # 设计单位
            'design_company': forms.TextInput(attrs={
                'class': 'form-control',
                'required': True,
                'placeholder': '设计单位名称',
            }),
            'design_credit_code': forms.TextInput(attrs={
                'class': 'form-control',
                'required': True,
                'placeholder': '统一社会信用代码',
                'maxlength': 50,
            }),
            'design_contact_person': forms.TextInput(attrs={
                'class': 'form-control',
                'required': True,
                'placeholder': '项目负责人',
            }),
            'design_phone': forms.TextInput(attrs={
                'class': 'form-control',
                'required': True,
                'placeholder': '项目负责人联系电话',
            }),
        }
        labels = {
            # 委托单位
            'client_company_name': '单位名称',
            'client_credit_code': '统一社会信用代码',
            'client_registered_capital': '注册资本（万元）',
            'client_registered_address': '注册地址',
            'client_company_type': '企业类型',
            'client_ownership_type': '企业所有',
            'client_established_date': '成立日期',
            'client_contact_person': '项目负责人',
            'client_phone': '项目负责人联系电话',
            'client_litigation_count': '司法案件数量（启信宝公开数量）',
            'client_enforcement_count': '被执行人数量（启信宝公开数量）',
            'client_final_case_count': '终本案件数量（启信宝公开数量）',
            'client_restriction_count': '限制高消费数量（启信宝公开数量）',
            # 设计单位
            'design_company': '单位名称',
            'design_credit_code': '统一社会信用代码',
            'design_contact_person': '项目负责人',
            'design_phone': '项目负责人联系电话',
        }


class ProjectInitiationStep4Form(forms.ModelForm):
    """项目立项 - 第四步：合同金额确定"""
    
    class Meta:
        model = Project
        fields = [
            'billing_method',
            'project_region',
            'structure_type',
            'base_fee',
            'unit_price',
            'fee_rate_coefficient',
            'contract_amount',
        ]
        widgets = {
            'billing_method': forms.Select(attrs={
                'class': 'form-select',
                'required': True,
                'id': 'id_billing_method',
            }),
            'project_region': forms.Select(attrs={
                'class': 'form-select',
                'required': True,
                'id': 'id_project_region',
            }),
            'structure_type': forms.Select(attrs={
                'class': 'form-select',
                'required': True,
                'id': 'id_structure_type',
            }),
            'base_fee': forms.NumberInput(attrs={
                'class': 'form-control',
                'step': '0.01',
                'min': '0',
                'placeholder': '基本费（元）',
                'id': 'id_base_fee',
            }),
            'unit_price': forms.NumberInput(attrs={
                'class': 'form-control',
                'step': '0.01',
                'min': '0',
                'placeholder': '包干单价（元/平方米）',
                'id': 'id_unit_price',
            }),
            'fee_rate_coefficient': forms.NumberInput(attrs={
                'class': 'form-control',
                'step': '0.01',
                'min': '0',
                'max': '100',
                'placeholder': '取费系数（%）',
                'id': 'id_fee_rate_coefficient',
            }),
            'contract_amount': forms.NumberInput(attrs={
                'class': 'form-control',
                'step': '0.01',
                'min': '0',
                'placeholder': '合同金额（元）',
                'readonly': True,
                'id': 'id_contract_amount',
            }),
        }
        labels = {
            'billing_method': '服务费取费方式',
            'project_region': '项目区域',
            'structure_type': '结构形式',
            'base_fee': '基本费（元）',
            'unit_price': '包干单价（元/平方米）',
            'fee_rate_coefficient': '取费系数（%）',
            'contract_amount': '合同金额（元）',
        }
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['billing_method'].required = True
        self.fields['project_region'].required = True
        self.fields['structure_type'].required = True
        self.fields['contract_amount'].required = False  # 自动计算，不需要手动输入
        
        # 取费系数不是必填的，根据取费方式动态设置
        self.fields['fee_rate_coefficient'].required = False
        self.fields['base_fee'].required = False
        self.fields['unit_price'].required = False
    
    def clean(self):
        cleaned_data = super().clean()
        billing_method = cleaned_data.get('billing_method')
        
        if billing_method == 'base_fee_rate':
            # 基本费+费率取费：基本费和取费系数至少有一个
            base_fee = cleaned_data.get('base_fee') or 0
            fee_rate = cleaned_data.get('fee_rate_coefficient') or 0
            if base_fee == 0 and (not fee_rate or fee_rate == 0):
                raise ValidationError('基本费+费率取费方式需要填写基本费或取费系数')
        
        elif billing_method == 'unit_price':
            # 综合单价包干：需要包干单价
            unit_price = cleaned_data.get('unit_price')
            if not unit_price or unit_price <= 0:
                raise ValidationError('综合单价包干方式需要填写包干单价')
        
        elif billing_method == 'pure_rate':
            # 纯费率计费：需要取费系数，如果没有填写则使用默认值10%
            fee_rate = cleaned_data.get('fee_rate_coefficient')
            if not fee_rate or fee_rate <= 0:
                # 如果没有填写，设置默认值为10%
                cleaned_data['fee_rate_coefficient'] = 10
        
        return cleaned_data
    
    def save(self, commit=True):
        instance = super().save(commit=False)
        
        # 自动计算合同金额
        calculated_amount = instance.calculate_contract_amount()
        if calculated_amount:
            instance.contract_amount = calculated_amount
        
        if commit:
            instance.save()
            self.save_m2m()
        
        return instance


class ProjectInitiationSubmitForm(forms.ModelForm):
    """项目立项 - 提交审批"""
    submission_comment = forms.CharField(
        required=False,
        widget=forms.Textarea(attrs={
            'class': 'form-control',
            'rows': 3,
            'placeholder': '提交说明（可选）',
        }),
        label='提交说明',
    )
    
    class Meta:
        model = ProjectInitiationApproval
        fields = ['submission_comment']
