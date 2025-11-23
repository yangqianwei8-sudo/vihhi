from django import forms
from .models import (
    OfficeSupply, MeetingRoom, Vehicle, ReceptionRecord,
    Announcement, Seal, FixedAsset, ExpenseReimbursement, ExpenseItem
)
from backend.apps.system_management.models import User, Department
from backend.apps.system_management.models import Role


class OfficeSupplyForm(forms.ModelForm):
    """办公用品表单"""
    
    class Meta:
        model = OfficeSupply
        fields = [
            'code', 'name', 'category', 'unit', 'specification', 'brand',
            'supplier', 'purchase_price', 'current_stock', 'min_stock',
            'max_stock', 'storage_location', 'description', 'is_active'
        ]
        widgets = {
            'code': forms.TextInput(attrs={'class': 'form-control', 'placeholder': '用品编码'}),
            'name': forms.TextInput(attrs={'class': 'form-control', 'placeholder': '用品名称'}),
            'category': forms.Select(attrs={'class': 'form-select'}),
            'unit': forms.TextInput(attrs={'class': 'form-control', 'placeholder': '单位'}),
            'specification': forms.TextInput(attrs={'class': 'form-control', 'placeholder': '规格型号'}),
            'brand': forms.TextInput(attrs={'class': 'form-control', 'placeholder': '品牌'}),
            'supplier': forms.TextInput(attrs={'class': 'form-control', 'placeholder': '供应商'}),
            'purchase_price': forms.NumberInput(attrs={
                'class': 'form-control',
                'step': '0.01',
                'placeholder': '采购单价'
            }),
            'current_stock': forms.NumberInput(attrs={
                'class': 'form-control',
                'min': 0,
                'placeholder': '当前库存'
            }),
            'min_stock': forms.NumberInput(attrs={
                'class': 'form-control',
                'min': 0,
                'placeholder': '最低库存'
            }),
            'max_stock': forms.NumberInput(attrs={
                'class': 'form-control',
                'min': 0,
                'placeholder': '最高库存'
            }),
            'storage_location': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': '存放位置'
            }),
            'description': forms.Textarea(attrs={
                'class': 'form-control',
                'rows': 3,
                'placeholder': '描述'
            }),
            'is_active': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
        }


class MeetingRoomForm(forms.ModelForm):
    """会议室表单"""
    
    class Meta:
        model = MeetingRoom
        fields = [
            'code', 'name', 'location', 'capacity', 'facilities',
            'hourly_rate', 'status', 'description', 'is_active'
        ]
        widgets = {
            'code': forms.TextInput(attrs={'class': 'form-control', 'placeholder': '会议室编号'}),
            'name': forms.TextInput(attrs={'class': 'form-control', 'placeholder': '会议室名称'}),
            'location': forms.TextInput(attrs={'class': 'form-control', 'placeholder': '位置'}),
            'capacity': forms.NumberInput(attrs={
                'class': 'form-control',
                'min': 0,
                'placeholder': '容纳人数'
            }),
            'facilities': forms.Textarea(attrs={
                'class': 'form-control',
                'rows': 3,
                'placeholder': '设施说明'
            }),
            'hourly_rate': forms.NumberInput(attrs={
                'class': 'form-control',
                'step': '0.01',
                'placeholder': '时租费用'
            }),
            'status': forms.Select(attrs={'class': 'form-select'}),
            'description': forms.Textarea(attrs={
                'class': 'form-control',
                'rows': 3,
                'placeholder': '描述'
            }),
            'is_active': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
        }


class VehicleForm(forms.ModelForm):
    """车辆表单"""
    
    class Meta:
        model = Vehicle
        fields = [
            'plate_number', 'brand', 'vehicle_type', 'color',
            'purchase_date', 'purchase_price', 'current_mileage',
            'fuel_type', 'driver', 'status', 'insurance_expiry',
            'annual_inspection_date', 'description', 'is_active'
        ]
        widgets = {
            'plate_number': forms.TextInput(attrs={'class': 'form-control', 'placeholder': '车牌号'}),
            'brand': forms.TextInput(attrs={'class': 'form-control', 'placeholder': '品牌型号'}),
            'vehicle_type': forms.Select(attrs={'class': 'form-select'}),
            'color': forms.TextInput(attrs={'class': 'form-control', 'placeholder': '颜色'}),
            'purchase_date': forms.DateInput(attrs={
                'class': 'form-control',
                'type': 'date'
            }),
            'purchase_price': forms.NumberInput(attrs={
                'class': 'form-control',
                'step': '0.01',
                'placeholder': '购买价格'
            }),
            'current_mileage': forms.NumberInput(attrs={
                'class': 'form-control',
                'min': 0,
                'placeholder': '当前里程数'
            }),
            'fuel_type': forms.Select(attrs={'class': 'form-select'}),
            'driver': forms.Select(attrs={'class': 'form-select'}),
            'status': forms.Select(attrs={'class': 'form-select'}),
            'insurance_expiry': forms.DateInput(attrs={
                'class': 'form-control',
                'type': 'date'
            }),
            'annual_inspection_date': forms.DateInput(attrs={
                'class': 'form-control',
                'type': 'date'
            }),
            'description': forms.Textarea(attrs={
                'class': 'form-control',
                'rows': 3,
                'placeholder': '描述'
            }),
            'is_active': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
        }
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['driver'].queryset = User.objects.filter(is_active=True).order_by('username')
        self.fields['driver'].required = False


class ReceptionRecordForm(forms.ModelForm):
    """接待记录表单"""
    
    class Meta:
        model = ReceptionRecord
        fields = [
            'visitor_name', 'visitor_company', 'visitor_position', 'visitor_phone',
            'visitor_count', 'reception_date', 'reception_time', 'expected_duration',
            'reception_type', 'reception_level', 'host', 'meeting_topic',
            'meeting_location', 'catering_arrangement', 'accommodation_arrangement',
            'gifts_exchanged', 'outcome', 'notes'
        ]
        widgets = {
            'visitor_name': forms.TextInput(attrs={'class': 'form-control', 'placeholder': '访客姓名'}),
            'visitor_company': forms.TextInput(attrs={'class': 'form-control', 'placeholder': '访客单位'}),
            'visitor_position': forms.TextInput(attrs={'class': 'form-control', 'placeholder': '访客职位'}),
            'visitor_phone': forms.TextInput(attrs={'class': 'form-control', 'placeholder': '访客电话'}),
            'visitor_count': forms.NumberInput(attrs={
                'class': 'form-control',
                'min': 1,
                'placeholder': '访客人数'
            }),
            'reception_date': forms.DateInput(attrs={
                'class': 'form-control',
                'type': 'date'
            }),
            'reception_time': forms.TimeInput(attrs={
                'class': 'form-control',
                'type': 'time'
            }),
            'expected_duration': forms.NumberInput(attrs={
                'class': 'form-control',
                'min': 0,
                'placeholder': '预计时长（分钟）'
            }),
            'reception_type': forms.Select(attrs={'class': 'form-select'}),
            'reception_level': forms.Select(attrs={'class': 'form-select'}),
            'host': forms.Select(attrs={'class': 'form-select'}),
            'meeting_topic': forms.TextInput(attrs={'class': 'form-control', 'placeholder': '会议主题'}),
            'meeting_location': forms.TextInput(attrs={'class': 'form-control', 'placeholder': '会议地点'}),
            'catering_arrangement': forms.Select(attrs={'class': 'form-select'}),
            'accommodation_arrangement': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
            'gifts_exchanged': forms.Textarea(attrs={
                'class': 'form-control',
                'rows': 2,
                'placeholder': '礼品交换情况'
            }),
            'outcome': forms.Textarea(attrs={
                'class': 'form-control',
                'rows': 3,
                'placeholder': '接待结果/成果'
            }),
            'notes': forms.Textarea(attrs={
                'class': 'form-control',
                'rows': 2,
                'placeholder': '备注'
            }),
        }
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['host'].queryset = User.objects.filter(is_active=True).order_by('username')


class AnnouncementForm(forms.ModelForm):
    """公告通知表单"""
    
    class Meta:
        model = Announcement
        fields = [
            'title', 'content', 'category', 'priority', 'target_scope',
            'target_departments', 'target_roles', 'target_users',
            'publish_date', 'expiry_date', 'is_top', 'is_popup',
            'attachment', 'is_active'
        ]
        widgets = {
            'title': forms.TextInput(attrs={'class': 'form-control', 'placeholder': '标题'}),
            'content': forms.Textarea(attrs={
                'class': 'form-control',
                'rows': 8,
                'placeholder': '内容'
            }),
            'category': forms.Select(attrs={'class': 'form-select'}),
            'priority': forms.Select(attrs={'class': 'form-select'}),
            'target_scope': forms.Select(attrs={'class': 'form-select'}),
            'target_departments': forms.SelectMultiple(attrs={
                'class': 'form-select',
                'size': 5
            }),
            'target_roles': forms.SelectMultiple(attrs={
                'class': 'form-select',
                'size': 5
            }),
            'target_users': forms.SelectMultiple(attrs={
                'class': 'form-select',
                'size': 5
            }),
            'publish_date': forms.DateInput(attrs={
                'class': 'form-control',
                'type': 'date'
            }),
            'expiry_date': forms.DateInput(attrs={
                'class': 'form-control',
                'type': 'date'
            }),
            'is_top': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
            'is_popup': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
            'attachment': forms.FileInput(attrs={
                'class': 'form-control',
                'accept': '.pdf,.doc,.docx,.xls,.xlsx,.jpg,.png'
            }),
            'is_active': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
        }
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['target_departments'].queryset = Department.objects.filter(is_active=True).order_by('name')
        self.fields['target_roles'].queryset = Role.objects.filter(is_active=True).order_by('name')
        self.fields['target_users'].queryset = User.objects.filter(is_active=True).order_by('username')
        self.fields['target_departments'].required = False
        self.fields['target_roles'].required = False
        self.fields['target_users'].required = False


class SealForm(forms.ModelForm):
    """印章表单"""
    
    class Meta:
        model = Seal
        fields = [
            'seal_number', 'seal_name', 'seal_type', 'keeper',
            'storage_location', 'status', 'description', 'is_active'
        ]
        widgets = {
            'seal_number': forms.TextInput(attrs={'class': 'form-control', 'placeholder': '印章编号'}),
            'seal_name': forms.TextInput(attrs={'class': 'form-control', 'placeholder': '印章名称'}),
            'seal_type': forms.Select(attrs={'class': 'form-select'}),
            'keeper': forms.Select(attrs={'class': 'form-select'}),
            'storage_location': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': '存放位置'
            }),
            'status': forms.Select(attrs={'class': 'form-select'}),
            'description': forms.Textarea(attrs={
                'class': 'form-control',
                'rows': 3,
                'placeholder': '描述'
            }),
            'is_active': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
        }
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['keeper'].queryset = User.objects.filter(is_active=True).order_by('username')


class FixedAssetForm(forms.ModelForm):
    """固定资产表单"""
    
    class Meta:
        model = FixedAsset
        fields = [
            'asset_name', 'category', 'brand', 'model', 'specification',
            'purchase_date', 'purchase_price', 'supplier', 'warranty_period',
            'warranty_expiry', 'current_user', 'current_location', 'department',
            'depreciation_method', 'depreciation_rate', 'net_value', 'status',
            'description', 'is_active'
        ]
        widgets = {
            'asset_name': forms.TextInput(attrs={'class': 'form-control', 'placeholder': '资产名称'}),
            'category': forms.Select(attrs={'class': 'form-select'}),
            'brand': forms.TextInput(attrs={'class': 'form-control', 'placeholder': '品牌'}),
            'model': forms.TextInput(attrs={'class': 'form-control', 'placeholder': '型号'}),
            'specification': forms.TextInput(attrs={'class': 'form-control', 'placeholder': '规格'}),
            'purchase_date': forms.DateInput(attrs={
                'class': 'form-control',
                'type': 'date'
            }),
            'purchase_price': forms.NumberInput(attrs={
                'class': 'form-control',
                'step': '0.01',
                'placeholder': '购买价格'
            }),
            'supplier': forms.TextInput(attrs={'class': 'form-control', 'placeholder': '供应商'}),
            'warranty_period': forms.NumberInput(attrs={
                'class': 'form-control',
                'min': 0,
                'placeholder': '保修期（月）'
            }),
            'warranty_expiry': forms.DateInput(attrs={
                'class': 'form-control',
                'type': 'date'
            }),
            'current_user': forms.Select(attrs={'class': 'form-select'}),
            'current_location': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': '当前位置'
            }),
            'department': forms.Select(attrs={'class': 'form-select'}),
            'depreciation_method': forms.Select(attrs={'class': 'form-select'}),
            'depreciation_rate': forms.NumberInput(attrs={
                'class': 'form-control',
                'step': '0.01',
                'placeholder': '折旧率'
            }),
            'net_value': forms.NumberInput(attrs={
                'class': 'form-control',
                'step': '0.01',
                'placeholder': '净值'
            }),
            'status': forms.Select(attrs={'class': 'form-select'}),
            'description': forms.Textarea(attrs={
                'class': 'form-control',
                'rows': 3,
                'placeholder': '描述'
            }),
            'is_active': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
        }
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['current_user'].queryset = User.objects.filter(is_active=True).order_by('username')
        self.fields['department'].queryset = Department.objects.filter(is_active=True).order_by('name')
        self.fields['current_user'].required = False


class ExpenseItemForm(forms.ModelForm):
    """费用明细表单（用于内联）"""
    
    class Meta:
        model = ExpenseItem
        fields = ['expense_date', 'expense_type', 'description', 'amount', 'invoice_number', 'attachment', 'notes']
        widgets = {
            'expense_date': forms.DateInput(attrs={
                'class': 'form-control',
                'type': 'date'
            }),
            'expense_type': forms.Select(attrs={'class': 'form-select'}),
            'description': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': '费用说明'
            }),
            'amount': forms.NumberInput(attrs={
                'class': 'form-control',
                'step': '0.01',
                'placeholder': '金额'
            }),
            'invoice_number': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': '发票号码'
            }),
            'attachment': forms.FileInput(attrs={
                'class': 'form-control',
                'accept': '.pdf,.jpg,.jpeg,.png'
            }),
            'notes': forms.Textarea(attrs={
                'class': 'form-control',
                'rows': 2,
                'placeholder': '备注'
            }),
        }


class ExpenseReimbursementForm(forms.ModelForm):
    """报销申请表单"""
    
    class Meta:
        model = ExpenseReimbursement
        fields = [
            'expense_type', 'application_date', 'status',
            'payment_method', 'notes'
        ]
        widgets = {
            'expense_type': forms.Select(attrs={'class': 'form-select'}),
            'application_date': forms.DateInput(attrs={
                'class': 'form-control',
                'type': 'date'
            }),
            'status': forms.Select(attrs={'class': 'form-select'}),
            'payment_method': forms.Select(attrs={'class': 'form-select'}),
            'notes': forms.Textarea(attrs={
                'class': 'form-control',
                'rows': 3,
                'placeholder': '备注'
            }),
        }
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['payment_method'].required = False

