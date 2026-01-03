"""
档案管理模块表单
"""
from django import forms
from backend.apps.archive_management.models import (
    ArchiveCategory,
    ArchiveProjectArchive,
    ProjectArchiveDocument,
    AdministrativeArchive,
    ArchiveBorrow,
    ArchiveDestroy,
    ArchiveStorageRoom,
    ArchiveLocation,
    ArchiveInventory,
)

# 尝试导入扩展模型
try:
    from backend.apps.archive_management.models import ArchiveCategoryRule
    ARCHIVE_CATEGORY_RULE_AVAILABLE = True
except ImportError:
    ARCHIVE_CATEGORY_RULE_AVAILABLE = False


class ArchiveCategoryForm(forms.ModelForm):
    """档案分类表单"""
    name = forms.CharField(
        label='分类名称',
        required=True,
        widget=forms.TextInput(attrs={'class': 'form-control', 'placeholder': '请输入分类名称'})
    )
    code = forms.CharField(
        label='分类代码',
        required=True,
        widget=forms.TextInput(attrs={'class': 'form-control', 'placeholder': '请输入分类代码（唯一）'})
    )
    
    class Meta:
        model = ArchiveCategory
        fields = ['name', 'code', 'category_type', 'parent', 'description', 'order', 
                  'icon', 'storage_period', 'security_level', 'is_active']
        widgets = {
            'category_type': forms.Select(attrs={'class': 'form-select'}),
            'parent': forms.Select(attrs={'class': 'form-select'}),
            'description': forms.Textarea(attrs={'rows': 3, 'class': 'form-control', 'placeholder': '可选的分类描述信息'}),
            'order': forms.NumberInput(attrs={'class': 'form-control', 'min': 0}),
            'icon': forms.TextInput(attrs={'class': 'form-control', 'placeholder': '图标代码或emoji'}),
            'storage_period': forms.NumberInput(attrs={'class': 'form-control', 'min': 1, 'max': 100}),
            'security_level': forms.Select(attrs={'class': 'form-select'}),
            'is_active': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
        }
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # 限制上级分类选择（排除自己和子分类）
        if self.instance and self.instance.pk:
            self.fields['parent'].queryset = ArchiveCategory.objects.filter(
                is_active=True
            ).exclude(pk=self.instance.pk).exclude(parent=self.instance).order_by('category_type', 'order', 'id')
        else:
            self.fields['parent'].queryset = ArchiveCategory.objects.filter(
                is_active=True
            ).order_by('category_type', 'order', 'id')
    
    def clean_code(self):
        code = self.cleaned_data.get('code')
        if code:
            # 检查代码唯一性（排除当前实例）
            queryset = ArchiveCategory.objects.filter(code=code)
            if self.instance and self.instance.pk:
                queryset = queryset.exclude(pk=self.instance.pk)
            if queryset.exists():
                raise forms.ValidationError('分类代码已存在，请使用其他代码')
        return code


class ProjectArchiveForm(forms.ModelForm):
    """项目归档表单"""
    archive_reason = forms.CharField(
        label='归档原因',
        required=True,
        widget=forms.Textarea(attrs={'rows': 3, 'placeholder': '请详细说明归档原因，必填'})
    )
    archive_description = forms.CharField(
        label='归档说明',
        required=False,
        widget=forms.Textarea(attrs={'rows': 3, 'placeholder': '可选的归档说明信息'})
    )
    
    class Meta:
        model = ArchiveProjectArchive
        fields = ['project', 'archive_reason', 'archive_description']
        widgets = {
            'project': forms.Select(attrs={'class': 'form-select'}),
        }
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # 限制项目选择为已结算的项目
        from backend.apps.production_management.models import Project
        self.fields['project'].queryset = Project.objects.filter(
            status__in=['settled', 'completed', 'archived']
        ).order_by('-updated_time')
        self.fields['project'].label = '选择项目'
        # 将提示文字移到 widget 的 title 属性中
        self.fields['project'].widget.attrs['title'] = '仅显示已结算或已完成的项目'


class ProjectArchiveDocumentForm(forms.ModelForm):
    """项目档案文档表单"""
    document_name = forms.CharField(
        label='文档名称',
        required=True,
        widget=forms.TextInput(attrs={'class': 'form-control', 'placeholder': '请输入文档名称'})
    )
    file = forms.FileField(
        label='文档文件',
        required=True,
        widget=forms.FileInput(attrs={'class': 'form-control', 'accept': '.pdf,.doc,.docx,.xls,.xlsx,.ppt,.pptx,.txt,.jpg,.jpeg,.png,.dwg,.zip,.rar'})
    )
    
    class Meta:
        model = ProjectArchiveDocument
        fields = ['document_name', 'document_type', 'category', 'project', 'file',
                  'description', 'tags', 'security_level', 'version']
        widgets = {
            'document_type': forms.Select(attrs={'class': 'form-select'}),
            'category': forms.Select(attrs={'class': 'form-select'}),
            'project': forms.Select(attrs={'class': 'form-select'}),
            'description': forms.Textarea(attrs={'rows': 3, 'class': 'form-control', 'placeholder': '可选的文档描述信息'}),
            'tags': forms.TextInput(attrs={'class': 'form-control', 'placeholder': '多个标签用逗号分隔'}),
            'security_level': forms.Select(attrs={'class': 'form-select'}),
            'version': forms.TextInput(attrs={'class': 'form-control', 'placeholder': '如：v1.0'}),
        }
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # 限制项目选择
        from backend.apps.production_management.models import Project
        self.fields['project'].queryset = Project.objects.filter(
            status__in=['in_progress', 'settled', 'completed']
        ).order_by('-updated_time')
        # 限制分类选择
        self.fields['category'].queryset = ArchiveCategory.objects.filter(
            category_type='project',
            is_active=True
        ).order_by('order', 'id')


class AdministrativeArchiveForm(forms.ModelForm):
    """行政档案表单"""
    archive_name = forms.CharField(
        label='档案名称',
        required=True,
        widget=forms.TextInput(attrs={'class': 'form-control', 'placeholder': '请输入档案名称'})
    )
    archive_file = forms.FileField(
        label='档案文件',
        required=False,
        widget=forms.FileInput(attrs={
            'class': 'form-control',
            'accept': '.pdf,.doc,.docx,.xls,.xlsx,.ppt,.pptx,.txt,.jpg,.jpeg,.png,.zip,.rar',
            'title': '支持PDF、Word、Excel、图片等格式'
        })
    )
    
    class Meta:
        model = AdministrativeArchive
        fields = ['archive_name', 'category', 'archive_date', 'archive_department',
                  'description', 'security_level', 'storage_period', 'storage_room', 'location']
        widgets = {
            'category': forms.Select(attrs={'class': 'form-select'}),
            'archive_date': forms.DateInput(attrs={'type': 'date', 'class': 'form-control'}),
            'archive_department': forms.Select(attrs={'class': 'form-select'}),
            'description': forms.Textarea(attrs={'rows': 3, 'class': 'form-control', 'placeholder': '可选的档案描述信息'}),
            'security_level': forms.Select(attrs={'class': 'form-select'}),
            'storage_period': forms.NumberInput(attrs={'class': 'form-control', 'min': 1, 'max': 100}),
            'storage_room': forms.Select(attrs={'class': 'form-select'}),
            'location': forms.Select(attrs={'class': 'form-select'}),
        }
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # 限制分类选择
        self.fields['category'].queryset = ArchiveCategory.objects.filter(
            category_type='administrative',
            is_active=True
        ).order_by('order', 'id')
        # 限制库房选择
        from backend.apps.archive_management.models import ArchiveStorageRoom
        self.fields['storage_room'].queryset = ArchiveStorageRoom.objects.filter(
            status='active'
        ).order_by('room_name')
        # 限制位置选择（需要根据库房动态加载）
        from backend.apps.archive_management.models import ArchiveLocation
        self.fields['location'].queryset = ArchiveLocation.objects.none()
        if self.instance and self.instance.pk and self.instance.storage_room:
            self.fields['location'].queryset = ArchiveLocation.objects.filter(
                storage_room=self.instance.storage_room
            ).order_by('location_name')


class ArchiveBorrowForm(forms.ModelForm):
    """档案借阅表单"""
    borrow_reason = forms.CharField(
        label='借阅事由',
        required=True,
        widget=forms.Textarea(attrs={'rows': 3, 'class': 'form-control', 'placeholder': '请详细说明借阅事由，必填'})
    )
    return_date = forms.DateField(
        label='归还日期',
        required=True,
        widget=forms.DateInput(attrs={'type': 'date', 'class': 'form-control'})
    )
    
    class Meta:
        model = ArchiveBorrow
        fields = ['project_document', 'administrative_archive', 'borrow_reason',
                  'borrow_date', 'return_date', 'borrower_department', 'borrow_purpose', 'borrow_method']
        widgets = {
            'project_document': forms.Select(attrs={'class': 'form-select'}),
            'administrative_archive': forms.Select(attrs={'class': 'form-select'}),
            'borrow_date': forms.DateInput(attrs={'type': 'date', 'class': 'form-control'}),
            'borrower_department': forms.Select(attrs={'class': 'form-select'}),
            'borrow_purpose': forms.TextInput(attrs={'class': 'form-control', 'placeholder': '借阅用途'}),
            'borrow_method': forms.Select(attrs={'class': 'form-select'}),
        }
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # 限制项目文档选择
        self.fields['project_document'].queryset = ProjectArchiveDocument.objects.filter(
            status__in=['archived', 'pending_archive']
        ).order_by('-uploaded_time')
        # 限制行政档案选择
        self.fields['administrative_archive'].queryset = AdministrativeArchive.objects.filter(
            status='archived'
        ).order_by('-created_time')
        # 限制部门选择
        from backend.apps.system_management.models import Department
        self.fields['borrower_department'].queryset = Department.objects.filter(
            is_active=True
        ).order_by('name')
    
    def clean(self):
        cleaned_data = super().clean()
        project_document = cleaned_data.get('project_document')
        administrative_archive = cleaned_data.get('administrative_archive')
        
        # 必须选择项目文档或行政档案之一
        if not project_document and not administrative_archive:
            raise forms.ValidationError('请选择要借阅的项目文档或行政档案')
        
        # 不能同时选择两者
        if project_document and administrative_archive:
            raise forms.ValidationError('不能同时选择项目文档和行政档案，请只选择其中一个')
        
        # 检查归还日期
        borrow_date = cleaned_data.get('borrow_date')
        return_date = cleaned_data.get('return_date')
        if borrow_date and return_date and return_date <= borrow_date:
            raise forms.ValidationError('归还日期必须晚于借阅日期')
        
        return cleaned_data


class ArchiveDestroyForm(forms.ModelForm):
    """档案销毁表单"""
    destroy_reason = forms.CharField(
        label='销毁原因',
        required=True,
        widget=forms.Textarea(attrs={'rows': 3, 'class': 'form-control', 'placeholder': '请详细说明销毁原因，必填'})
    )
    destroy_basis = forms.CharField(
        label='销毁依据',
        required=False,
        widget=forms.Textarea(attrs={'rows': 2, 'class': 'form-control', 'placeholder': '销毁依据（如：保管期限已到、重复档案等）'})
    )
    
    class Meta:
        model = ArchiveDestroy
        fields = ['project_document', 'administrative_archive', 'destroy_reason',
                  'destroy_date', 'destroy_method', 'destroy_basis']
        widgets = {
            'project_document': forms.Select(attrs={'class': 'form-select'}),
            'administrative_archive': forms.Select(attrs={'class': 'form-select'}),
            'destroy_date': forms.DateInput(attrs={'type': 'date', 'class': 'form-control'}),
            'destroy_method': forms.Select(attrs={'class': 'form-select'}),
        }
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # 限制项目文档选择
        self.fields['project_document'].queryset = ProjectArchiveDocument.objects.filter(
            status='archived'
        ).order_by('-uploaded_time')
        # 限制行政档案选择
        self.fields['administrative_archive'].queryset = AdministrativeArchive.objects.filter(
            status='archived'
        ).order_by('-created_time')
    
    def clean(self):
        cleaned_data = super().clean()
        project_document = cleaned_data.get('project_document')
        administrative_archive = cleaned_data.get('administrative_archive')
        
        # 必须选择项目文档或行政档案之一
        if not project_document and not administrative_archive:
            raise forms.ValidationError('请选择要销毁的项目文档或行政档案')
        
        # 不能同时选择两者
        if project_document and administrative_archive:
            raise forms.ValidationError('不能同时选择项目文档和行政档案，请只选择其中一个')
        
        return cleaned_data


class ArchiveStorageRoomForm(forms.ModelForm):
    """档案库房表单"""
    class Meta:
        model = ArchiveStorageRoom
        fields = ['room_number', 'room_name', 'location', 'area', 'capacity',
                  'manager', 'description', 'status']
        widgets = {
            'description': forms.Textarea(attrs={'rows': 3}),
        }


class ArchiveLocationForm(forms.ModelForm):
    """档案位置表单"""
    class Meta:
        model = ArchiveLocation
        fields = ['location_number', 'location_name', 'storage_room', 'location_type',
                  'capacity', 'description']
        widgets = {
            'description': forms.Textarea(attrs={'rows': 2}),
        }


class ArchiveInventoryForm(forms.ModelForm):
    """档案盘点表单"""
    class Meta:
        model = ArchiveInventory
        fields = ['inventory_name', 'inventory_type', 'inventory_date', 'storage_room',
                  'category', 'date_range_start', 'date_range_end', 'notes']
        widgets = {
            'inventory_date': forms.DateInput(attrs={'type': 'date'}),
            'date_range_start': forms.DateInput(attrs={'type': 'date'}),
            'date_range_end': forms.DateInput(attrs={'type': 'date'}),
            'notes': forms.Textarea(attrs={'rows': 3}),
        }


if ARCHIVE_CATEGORY_RULE_AVAILABLE:
    class ArchiveCategoryRuleForm(forms.ModelForm):
        """档案分类规则表单"""
        name = forms.CharField(
            label='规则名称',
            required=True,
            widget=forms.TextInput(attrs={'class': 'form-control', 'placeholder': '请输入规则名称'})
        )
        
        rule_conditions = forms.JSONField(
            label='规则条件',
            required=False,
            widget=forms.Textarea(attrs={
                'class': 'form-control',
                'rows': 5,
                'placeholder': 'JSON格式的规则条件配置'
            })
        )
        
        class Meta:
            model = ArchiveCategoryRule
            fields = ['name', 'rule_type', 'category', 'priority', 'rule_expression', 
                     'rule_conditions', 'description', 'status', 'is_active']
            widgets = {
                'rule_type': forms.Select(attrs={'class': 'form-select'}),
                'category': forms.Select(attrs={'class': 'form-select'}),
                'priority': forms.NumberInput(attrs={'class': 'form-control', 'min': 0, 'max': 100}),
                'rule_expression': forms.Textarea(attrs={'rows': 5, 'class': 'form-control', 'placeholder': 'JSON格式的规则表达式（可选）'}),
                'rule_conditions': forms.Textarea(attrs={'rows': 8, 'class': 'form-control', 'placeholder': 'JSON格式的规则条件配置'}),
                'description': forms.Textarea(attrs={'rows': 3, 'class': 'form-control', 'placeholder': '规则描述'}),
                'status': forms.Select(attrs={'class': 'form-select'}),
                'is_active': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
            }
        
        def __init__(self, *args, **kwargs):
            super().__init__(*args, **kwargs)
            # 限制分类选择（只显示激活的分类）
            self.fields['category'].queryset = ArchiveCategory.objects.filter(is_active=True).order_by('category_type', 'order', 'id')
            
            # 如果rule_conditions是dict，转换为JSON字符串显示
            if self.instance and self.instance.pk and self.instance.rule_conditions:
                import json
                try:
                    self.initial['rule_conditions'] = json.dumps(self.instance.rule_conditions, ensure_ascii=False, indent=2)
                except:
                    pass
        
        def clean_rule_conditions(self):
            rule_conditions = self.cleaned_data.get('rule_conditions')
            if isinstance(rule_conditions, str):
                import json
                try:
                    rule_conditions = json.loads(rule_conditions)
                except json.JSONDecodeError:
                    raise forms.ValidationError('规则条件必须是有效的JSON格式')
            return rule_conditions or {}

