from django import forms
from .models import (
    OfficeSupply, SupplyPurchase, SupplyCategory, MeetingRoom, MeetingRoomBooking, Meeting, MeetingRecord, MeetingResolution,
    Vehicle, VehicleBooking, ReceptionRecord,
    Announcement, Seal, FixedAsset, ExpenseReimbursement, ExpenseItem,
    AdministrativeAffair, AffairProgressRecord, TravelApplication,
    Supplier, PurchaseContract, PurchasePayment,
    InventoryCheck, InventoryCheckItem, InventoryAdjust, InventoryAdjustItem
)
from backend.apps.system_management.models import User, Department
from backend.apps.system_management.models import Role


class SupplyCategoryForm(forms.ModelForm):
    """办公用品分类表单"""
    
    class Meta:
        model = SupplyCategory
        fields = ['name', 'parent', 'description', 'sort_order', 'is_active']
        widgets = {
            'name': forms.TextInput(attrs={'class': 'form-control', 'placeholder': '分类名称'}),
            'parent': forms.Select(attrs={'class': 'form-select'}),
            'description': forms.Textarea(attrs={
                'class': 'form-control',
                'rows': 3,
                'placeholder': '分类描述'
            }),
            'sort_order': forms.NumberInput(attrs={
                'class': 'form-control',
                'placeholder': '排序顺序'
            }),
            'is_active': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
        }
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # 排除自己和自己的子分类作为父分类
        if self.instance and self.instance.pk:
            exclude_ids = [self.instance.pk]
            # 获取所有子分类ID
            def get_children_ids(category):
                ids = []
                for child in category.children.all():
                    ids.append(child.id)
                    ids.extend(get_children_ids(child))
                return ids
            exclude_ids.extend(get_children_ids(self.instance))
            self.fields['parent'].queryset = SupplyCategory.objects.exclude(id__in=exclude_ids).order_by('sort_order', 'name')
        else:
            self.fields['parent'].queryset = SupplyCategory.objects.order_by('sort_order', 'name')
        self.fields['parent'].required = False


class OfficeSupplyForm(forms.ModelForm):
    """办公用品表单"""
    
    class Meta:
        model = OfficeSupply
        fields = [
            'code', 'name', 'category', 'supply_category', 'unit', 'specification', 'brand',
            'supplier', 'purchase_price', 'current_stock', 'min_stock',
            'max_stock', 'storage_location', 'description', 'is_active'
        ]
        widgets = {
            'code': forms.TextInput(attrs={'class': 'form-control', 'placeholder': '用品编码'}),
            'name': forms.TextInput(attrs={'class': 'form-control', 'placeholder': '用品名称'}),
            'category': forms.Select(attrs={'class': 'form-select'}),
            'supply_category': forms.Select(attrs={'class': 'form-select'}),
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


class MeetingRoomBookingForm(forms.ModelForm):
    """会议室预订表单"""
    
    class Meta:
        model = MeetingRoomBooking
        fields = [
            'room', 'booking_date', 'start_time', 'end_time',
            'meeting_topic', 'attendees_count', 'attendees',
            'equipment_needed', 'special_requirements'
        ]
        widgets = {
            'room': forms.Select(attrs={'class': 'form-select'}),
            'booking_date': forms.DateInput(attrs={
                'class': 'form-control',
                'type': 'date'
            }),
            'start_time': forms.TimeInput(attrs={
                'class': 'form-control',
                'type': 'time'
            }),
            'end_time': forms.TimeInput(attrs={
                'class': 'form-control',
                'type': 'time'
            }),
            'meeting_topic': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': '会议主题'
            }),
            'attendees_count': forms.NumberInput(attrs={
                'class': 'form-control',
                'min': 0,
                'placeholder': '参会人数'
            }),
            'attendees': forms.SelectMultiple(attrs={
                'class': 'form-select',
                'size': 5
            }),
            'special_requirements': forms.Textarea(attrs={
                'class': 'form-control',
                'rows': 3,
                'placeholder': '特殊需求'
            }),
        }
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['room'].queryset = MeetingRoom.objects.filter(
            is_active=True,
            status='available'
        ).order_by('code')
        self.fields['attendees'].queryset = User.objects.filter(is_active=True).order_by('username')
        self.fields['attendees'].required = False
        self.fields['meeting_topic'].required = False
        self.fields['special_requirements'].required = False
    
    def clean(self):
        cleaned_data = super().clean()
        booking_date = cleaned_data.get('booking_date')
        start_time = cleaned_data.get('start_time')
        end_time = cleaned_data.get('end_time')
        room = cleaned_data.get('room')
        
        if start_time and end_time and end_time <= start_time:
            self.add_error('end_time', '结束时间必须晚于开始时间。')
        
        # 检查时间冲突
        if room and booking_date and start_time and end_time:
            conflicts = MeetingRoomBooking.objects.filter(
                room=room,
                booking_date=booking_date,
                status__in=['pending', 'confirmed']
            ).exclude(id=self.instance.id if self.instance.id else None)
            
            for conflict in conflicts:
                if (start_time < conflict.end_time and end_time > conflict.start_time):
                    self.add_error('start_time', f'该时间段与已有预订冲突：{conflict.meeting_topic or conflict.booking_number}')
                    break
        
        return cleaned_data


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


class VehicleBookingForm(forms.ModelForm):
    """用车申请表单"""
    
    class Meta:
        model = VehicleBooking
        fields = [
            'vehicle', 'driver', 'start_time', 'end_time',
            'destination', 'purpose', 'passenger_count', 'notes'
        ]
        widgets = {
            'vehicle': forms.Select(attrs={'class': 'form-select'}),
            'driver': forms.Select(attrs={'class': 'form-select'}),
            'start_time': forms.DateTimeInput(attrs={
                'class': 'form-control',
                'type': 'datetime-local'
            }),
            'end_time': forms.DateTimeInput(attrs={
                'class': 'form-control',
                'type': 'datetime-local'
            }),
            'destination': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': '目的地'
            }),
            'purpose': forms.Textarea(attrs={
                'class': 'form-control',
                'rows': 3,
                'placeholder': '用车事由'
            }),
            'passenger_count': forms.NumberInput(attrs={
                'class': 'form-control',
                'min': 1,
                'placeholder': '乘车人数'
            }),
            'notes': forms.Textarea(attrs={
                'class': 'form-control',
                'rows': 2,
                'placeholder': '备注'
            }),
        }
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['vehicle'].queryset = Vehicle.objects.filter(
            is_active=True,
            status__in=['available', 'in_use']
        ).order_by('plate_number')
        self.fields['driver'].queryset = User.objects.filter(is_active=True).order_by('username')
        self.fields['driver'].required = False
        self.fields['notes'].required = False
    
    def clean(self):
        cleaned_data = super().clean()
        start_time = cleaned_data.get('start_time')
        end_time = cleaned_data.get('end_time')
        
        if start_time and end_time and end_time <= start_time:
            self.add_error('end_time', '结束时间必须晚于开始时间。')
        
        return cleaned_data


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


class AdministrativeAffairForm(forms.ModelForm):
    """行政事务表单"""
    
    class Meta:
        model = AdministrativeAffair
        fields = [
            'title', 'affair_type', 'content', 'priority', 'responsible_user',
            'participants', 'planned_start_time', 'planned_end_time', 'attachment'
        ]
        widgets = {
            'title': forms.TextInput(attrs={'class': 'form-control', 'placeholder': '事务标题'}),
            'affair_type': forms.Select(attrs={'class': 'form-select'}),
            'content': forms.Textarea(attrs={
                'class': 'form-control',
                'rows': 6,
                'placeholder': '事务内容'
            }),
            'priority': forms.Select(attrs={'class': 'form-select'}),
            'responsible_user': forms.Select(attrs={'class': 'form-select'}),
            'participants': forms.SelectMultiple(attrs={
                'class': 'form-select',
                'size': 5
            }),
            'planned_start_time': forms.DateTimeInput(attrs={
                'class': 'form-control',
                'type': 'datetime-local'
            }),
            'planned_end_time': forms.DateTimeInput(attrs={
                'class': 'form-control',
                'type': 'datetime-local'
            }),
            'attachment': forms.FileInput(attrs={
                'class': 'form-control',
                'accept': '.pdf,.doc,.docx,.xls,.xlsx,.jpg,.png'
            }),
        }
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['responsible_user'].queryset = User.objects.filter(is_active=True).order_by('username')
        self.fields['participants'].queryset = User.objects.filter(is_active=True).order_by('username')
        self.fields['participants'].required = False
        self.fields['attachment'].required = False


class AffairProgressRecordForm(forms.ModelForm):
    """事务进度记录表单"""
    
    class Meta:
        model = AffairProgressRecord
        fields = ['progress', 'notes', 'attachment']
        widgets = {
            'progress': forms.NumberInput(attrs={
                'class': 'form-control',
                'min': 0,
                'max': 100,
                'placeholder': '进度（%）'
            }),
            'notes': forms.Textarea(attrs={
                'class': 'form-control',
                'rows': 4,
                'placeholder': '进度说明'
            }),
            'attachment': forms.FileInput(attrs={
                'class': 'form-control',
                'accept': '.pdf,.doc,.docx,.xls,.xlsx,.jpg,.png'
            }),
        }
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['attachment'].required = False


class MeetingForm(forms.ModelForm):
    """会议表单"""
    
    class Meta:
        model = Meeting
        fields = [
            'title', 'meeting_type', 'room', 'meeting_date',
            'start_time', 'end_time', 'duration', 'organizer',
            'attendees', 'agenda', 'attachment'
        ]
        widgets = {
            'title': forms.TextInput(attrs={'class': 'form-control', 'placeholder': '会议主题'}),
            'meeting_type': forms.Select(attrs={'class': 'form-select'}),
            'room': forms.Select(attrs={'class': 'form-select'}),
            'meeting_date': forms.DateInput(attrs={
                'class': 'form-control',
                'type': 'date'
            }),
            'start_time': forms.TimeInput(attrs={
                'class': 'form-control',
                'type': 'time'
            }),
            'end_time': forms.TimeInput(attrs={
                'class': 'form-control',
                'type': 'time'
            }),
            'duration': forms.NumberInput(attrs={
                'class': 'form-control',
                'min': 0,
                'placeholder': '会议时长（分钟）'
            }),
            'organizer': forms.Select(attrs={'class': 'form-select'}),
            'attendees': forms.SelectMultiple(attrs={
                'class': 'form-select',
                'size': 5
            }),
            'agenda': forms.Textarea(attrs={
                'class': 'form-control',
                'rows': 6,
                'placeholder': '会议议程'
            }),
            'attachment': forms.FileInput(attrs={
                'class': 'form-control',
                'accept': '.pdf,.doc,.docx,.xls,.xlsx,.jpg,.png'
            }),
        }
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['organizer'].queryset = User.objects.filter(is_active=True).order_by('username')
        self.fields['attendees'].queryset = User.objects.filter(is_active=True).order_by('username')
        self.fields['room'].queryset = MeetingRoom.objects.filter(is_active=True, status='available').order_by('code')
        self.fields['attendees'].required = False
        self.fields['attachment'].required = False
        self.fields['room'].required = False


class MeetingRecordForm(forms.ModelForm):
    """会议记录表单"""
    
    class Meta:
        model = MeetingRecord
        fields = ['minutes', 'resolutions', 'attachment']
        widgets = {
            'minutes': forms.Textarea(attrs={
                'class': 'form-control',
                'rows': 10,
                'placeholder': '会议纪要'
            }),
            'resolutions': forms.Textarea(attrs={
                'class': 'form-control',
                'rows': 6,
                'placeholder': '会议决议'
            }),
            'attachment': forms.FileInput(attrs={
                'class': 'form-control',
                'accept': '.pdf,.doc,.docx,.xls,.xlsx,.jpg,.png'
            }),
        }
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['attachment'].required = False


class TravelApplicationForm(forms.ModelForm):
    """差旅申请表单"""
    
    class Meta:
        model = TravelApplication
        fields = [
            'travel_reason', 'destination', 'start_date', 'end_date',
            'travel_method', 'travelers', 'travel_budget', 'department', 'notes'
        ]
        widgets = {
            'travel_reason': forms.Textarea(attrs={
                'class': 'form-control',
                'rows': 3,
                'placeholder': '差旅事由'
            }),
            'destination': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': '差旅目的地'
            }),
            'start_date': forms.DateInput(attrs={
                'class': 'form-control',
                'type': 'date'
            }),
            'end_date': forms.DateInput(attrs={
                'class': 'form-control',
                'type': 'date'
            }),
            'travel_method': forms.Select(attrs={'class': 'form-select'}),
            'travelers': forms.SelectMultiple(attrs={
                'class': 'form-select',
                'size': 5
            }),
            'travel_budget': forms.NumberInput(attrs={
                'class': 'form-control',
                'step': '0.01',
                'placeholder': '差旅预算'
            }),
            'department': forms.Select(attrs={'class': 'form-select'}),
            'notes': forms.Textarea(attrs={
                'class': 'form-control',
                'rows': 2,
                'placeholder': '备注'
            }),
        }
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['travelers'].queryset = User.objects.filter(is_active=True).order_by('username')
        self.fields['department'].queryset = Department.objects.filter(is_active=True).order_by('name')
        self.fields['travelers'].required = False
        self.fields['travel_budget'].required = False
        self.fields['department'].required = False
        self.fields['notes'].required = False
    
    def clean(self):
        cleaned_data = super().clean()
        start_date = cleaned_data.get('start_date')
        end_date = cleaned_data.get('end_date')
        
        if start_date and end_date and end_date < start_date:
            self.add_error('end_date', '结束日期不能早于开始日期。')
        
        return cleaned_data


class SupplierForm(forms.ModelForm):
    """供应商表单"""
    
    class Meta:
        model = Supplier
        fields = [
            'name', 'contact_person', 'contact_phone', 'contact_email',
            'address', 'tax_id', 'bank_name', 'bank_account',
            'rating', 'credit_limit', 'payment_terms', 'description', 'is_active'
        ]
        widgets = {
            'name': forms.TextInput(attrs={'class': 'form-control', 'placeholder': '供应商名称'}),
            'contact_person': forms.TextInput(attrs={'class': 'form-control', 'placeholder': '联系人'}),
            'contact_phone': forms.TextInput(attrs={'class': 'form-control', 'placeholder': '联系电话'}),
            'contact_email': forms.EmailInput(attrs={'class': 'form-control', 'placeholder': '联系邮箱'}),
            'address': forms.Textarea(attrs={'class': 'form-control', 'rows': 2, 'placeholder': '地址'}),
            'tax_id': forms.TextInput(attrs={'class': 'form-control', 'placeholder': '税号'}),
            'bank_name': forms.TextInput(attrs={'class': 'form-control', 'placeholder': '开户银行'}),
            'bank_account': forms.TextInput(attrs={'class': 'form-control', 'placeholder': '银行账号'}),
            'rating': forms.Select(attrs={'class': 'form-select'}),
            'credit_limit': forms.NumberInput(attrs={
                'class': 'form-control',
                'step': '0.01',
                'placeholder': '信用额度'
            }),
            'payment_terms': forms.TextInput(attrs={'class': 'form-control', 'placeholder': '付款条件'}),
            'description': forms.Textarea(attrs={
                'class': 'form-control',
                'rows': 3,
                'placeholder': '描述'
            }),
            'is_active': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
        }


class PurchaseContractForm(forms.ModelForm):
    """采购合同表单"""
    
    class Meta:
        model = PurchaseContract
        fields = [
            'contract_name', 'supplier', 'purchase', 'contract_amount',
            'signed_date', 'start_date', 'end_date', 'payment_terms',
            'contract_file', 'notes'
        ]
        widgets = {
            'contract_name': forms.TextInput(attrs={'class': 'form-control', 'placeholder': '合同名称'}),
            'supplier': forms.Select(attrs={'class': 'form-select'}),
            'purchase': forms.Select(attrs={'class': 'form-select'}),
            'contract_amount': forms.NumberInput(attrs={
                'class': 'form-control',
                'step': '0.01',
                'placeholder': '合同金额'
            }),
            'signed_date': forms.DateInput(attrs={'class': 'form-control', 'type': 'date'}),
            'start_date': forms.DateInput(attrs={'class': 'form-control', 'type': 'date'}),
            'end_date': forms.DateInput(attrs={'class': 'form-control', 'type': 'date'}),
            'payment_terms': forms.TextInput(attrs={'class': 'form-control', 'placeholder': '付款条件'}),
            'contract_file': forms.FileInput(attrs={
                'class': 'form-control',
                'accept': '.pdf,.doc,.docx'
            }),
            'notes': forms.Textarea(attrs={
                'class': 'form-control',
                'rows': 3,
                'placeholder': '备注'
            }),
        }
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['supplier'].queryset = Supplier.objects.filter(is_active=True).order_by('name')
        self.fields['purchase'].queryset = SupplyPurchase.objects.filter(
            status__in=['approved', 'purchased']
        ).order_by('-purchase_date')
        self.fields['purchase'].required = False
        self.fields['contract_file'].required = False
    
    def clean(self):
        cleaned_data = super().clean()
        start_date = cleaned_data.get('start_date')
        end_date = cleaned_data.get('end_date')
        
        if start_date and end_date and end_date < start_date:
            self.add_error('end_date', '结束日期不能早于开始日期。')
        
        return cleaned_data


class PurchasePaymentForm(forms.ModelForm):
    """采购付款表单"""
    
    class Meta:
        model = PurchasePayment
        fields = [
            'contract', 'amount', 'payment_date', 'payment_method',
            'voucher_number', 'notes'
        ]
        widgets = {
            'contract': forms.Select(attrs={'class': 'form-select'}),
            'amount': forms.NumberInput(attrs={
                'class': 'form-control',
                'step': '0.01',
                'placeholder': '付款金额'
            }),
            'payment_date': forms.DateInput(attrs={'class': 'form-control', 'type': 'date'}),
            'payment_method': forms.Select(attrs={'class': 'form-select'}),
            'voucher_number': forms.TextInput(attrs={'class': 'form-control', 'placeholder': '凭证号'}),
            'notes': forms.Textarea(attrs={
                'class': 'form-control',
                'rows': 3,
                'placeholder': '备注'
            }),
        }
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['contract'].queryset = PurchaseContract.objects.filter(
            status__in=['approved', 'signed', 'executing']
        ).order_by('-signed_date')
        self.fields['voucher_number'].required = False
    
    def clean(self):
        cleaned_data = super().clean()
        contract = cleaned_data.get('contract')
        amount = cleaned_data.get('amount')
        
        if contract and amount:
            unpaid_amount = contract.unpaid_amount
            if amount > unpaid_amount:
                self.add_error('amount', f'付款金额不能超过未付款金额（¥{unpaid_amount}）。')
        
        return cleaned_data


class InventoryCheckForm(forms.ModelForm):
    """库存盘点表单"""
    
    class Meta:
        model = InventoryCheck
        fields = ['check_date', 'check_scope', 'check_location', 'notes']
        widgets = {
            'check_date': forms.DateInput(attrs={
                'class': 'form-control',
                'type': 'date'
            }),
            'check_scope': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': '盘点范围'
            }),
            'check_location': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': '盘点地点'
            }),
            'notes': forms.Textarea(attrs={
                'class': 'form-control',
                'rows': 3,
                'placeholder': '备注'
            }),
        }
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['check_scope'].required = False
        self.fields['check_location'].required = False
        self.fields['notes'].required = False


class InventoryCheckItemForm(forms.ModelForm):
    """库存盘点明细表单"""
    
    class Meta:
        model = InventoryCheckItem
        fields = ['supply', 'book_quantity', 'actual_quantity', 'notes']
        widgets = {
            'supply': forms.Select(attrs={'class': 'form-select'}),
            'book_quantity': forms.NumberInput(attrs={
                'class': 'form-control',
                'readonly': True
            }),
            'actual_quantity': forms.NumberInput(attrs={
                'class': 'form-control',
                'min': 0,
                'placeholder': '实际数量'
            }),
            'notes': forms.Textarea(attrs={
                'class': 'form-control',
                'rows': 2,
                'placeholder': '备注'
            }),
        }
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['supply'].queryset = OfficeSupply.objects.filter(is_active=True).order_by('code')
        self.fields['notes'].required = False


class InventoryAdjustForm(forms.ModelForm):
    """库存调整表单"""
    
    class Meta:
        model = InventoryAdjust
        fields = ['adjust_date', 'reason', 'notes']
        widgets = {
            'adjust_date': forms.DateInput(attrs={
                'class': 'form-control',
                'type': 'date'
            }),
            'reason': forms.Textarea(attrs={
                'class': 'form-control',
                'rows': 3,
                'placeholder': '调整原因'
            }),
            'notes': forms.Textarea(attrs={
                'class': 'form-control',
                'rows': 2,
                'placeholder': '备注'
            }),
        }
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['notes'].required = False


class InventoryAdjustItemForm(forms.ModelForm):
    """库存调整明细表单"""
    
    class Meta:
        model = InventoryAdjustItem
        fields = ['supply', 'adjust_quantity', 'notes']
        widgets = {
            'supply': forms.Select(attrs={'class': 'form-select'}),
            'adjust_quantity': forms.NumberInput(attrs={
                'class': 'form-control',
                'placeholder': '调整数量（正数为增加，负数为减少）'
            }),
            'notes': forms.Textarea(attrs={
                'class': 'form-control',
                'rows': 2,
                'placeholder': '备注'
            }),
        }
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['supply'].queryset = OfficeSupply.objects.filter(is_active=True).order_by('code')
        self.fields['notes'].required = False

