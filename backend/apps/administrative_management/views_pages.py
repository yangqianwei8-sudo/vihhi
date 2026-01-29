from django.contrib.auth.decorators import login_required
from django.shortcuts import render, get_object_or_404, redirect
from django.contrib import messages
from django.db.models import Count, Sum, Q, F, Max
from django.core.paginator import Paginator
from django.urls import reverse, NoReverseMatch
from django.utils import timezone
from django.forms import inlineformset_factory
from django import forms
from datetime import timedelta, datetime
from decimal import Decimal, InvalidOperation
import logging
import functools

from backend.apps.system_management.services import get_user_permission_codes
from backend.core.views import HOME_NAV_STRUCTURE, _permission_granted, _build_full_top_nav

logger = logging.getLogger(__name__)


def handle_view_errors(view_func):
    """装饰器：捕获视图函数中的所有异常，防止500错误"""
    @functools.wraps(view_func)
    def wrapper(request, *args, **kwargs):
        try:
            return view_func(request, *args, **kwargs)
        except Exception as e:
            logger.exception('视图函数 %s 执行失败: %s', view_func.__name__, str(e))
            messages.error(request, f'操作失败: {str(e)}')
            # 尝试返回一个简单的错误页面
            try:
                # 构建最小上下文
                context = {
                    'page_title': '错误',
                    'page_icon': '⚠️',
                    'description': '页面加载时发生错误',
                    'summary_cards': [],
                    'sections': [],
                    'full_top_nav': [],
                    'sidebar_menu': [],
                    'error_message': str(e),
                }
                # 尝试渲染错误页面，如果失败则返回简单响应
                return render(request, "administrative_management/affair_list.html", context)
            except Exception:
                # 如果连错误页面都渲染不了，返回重定向到首页
                return redirect('admin_pages:administrative_home')
    return wrapper
from backend.apps.administrative_management.models import (
    OfficeSupply, SupplyPurchase, SupplyPurchaseItem, SupplyRequest, SupplyRequestItem,
    SupplyCategory,
    InventoryCheck, InventoryCheckItem, InventoryAdjust, InventoryAdjustItem,
    MeetingRoom, MeetingRoomBooking, Meeting, MeetingRecord, MeetingResolution,
    Vehicle, VehicleBooking, VehicleMaintenance,
    ReceptionRecord, ReceptionExpense,
    Announcement, AnnouncementRead,
    Seal, SealBorrowing, SealUsage,
    FixedAsset, AssetTransfer, AssetMaintenance,
    ExpenseReimbursement, ExpenseItem,
    AdministrativeAffair, AffairStatusHistory, AffairProgressRecord,
    TravelApplication,
    Supplier, PurchaseContract, PurchasePayment,
)
from .forms import (
    OfficeSupplyForm, SupplyCategoryForm, MeetingRoomForm, MeetingRoomBookingForm, MeetingForm, MeetingRecordForm,
    VehicleForm, VehicleBookingForm, ReceptionRecordForm,
    AnnouncementForm, SealForm, SealBorrowingForm, SealUsageForm, FixedAssetForm, ExpenseReimbursementForm, ExpenseItemForm,
    AdministrativeAffairForm, AffairProgressRecordForm, TravelApplicationForm,
    SupplierForm, PurchaseContractForm, PurchasePaymentForm,
    InventoryCheckForm, InventoryCheckItemForm, InventoryAdjustForm, InventoryAdjustItemForm,
)

# 创建报销申请的内联表单集
ExpenseItemFormSet = inlineformset_factory(
    ExpenseReimbursement, ExpenseItem,
    form=ExpenseItemForm,
    extra=3,
    can_delete=True,
    min_num=1,
    validate_min=True,
)


# 使用统一的顶部导航菜单生成函数（已从 backend.core.views 导入）

# 行政管理模块左侧导航菜单结构（分组格式）
ADMINISTRATIVE_MANAGEMENT_SIDEBAR_MENU = [
    {
        'id': 'administrative_home',
        'label': '首页',
        'url_name': 'admin_pages:administrative_home',
        'permission': None,
        'path_keywords': ['administrative_home', 'administrative'],
        'icon': 'bi-house-door',
    },
    {
        'id': 'affairs',
        'label': '行政事务',
        'icon': '📋',
        'permission': None,  # 所有用户都可以访问
        'expanded': False,
        'children': [
            {
                'id': 'affair_list',
                'label': '行政事务列表',
                'url_name': 'admin_pages:affair_list',
                'permission': None,
                'path_keywords': ['affair'],
                'icon': 'bi-list-task',
            },
            {
                'id': 'affair_create',
                'label': '创建事务',
                'url_name': 'admin_pages:affair_create',
                'permission': None,
                'path_keywords': ['affairs/create'],
                'icon': 'bi-plus-circle',
            },
        ],
    },
    {
        'id': 'supplies',
        'label': '办公用品',
        'icon': '📦',
        'permission': 'administrative_management.supplies.view',
        'expanded': False,
        'children': [
            {
                'id': 'supplies_management',
                'label': '用品管理',
                'url_name': 'admin_pages:supplies_management',
                'permission': 'administrative_management.supplies.view',
                'path_keywords': ['supplies', 'supply'],
                'icon': 'bi-box',
            },
            {
                'id': 'supply_create',
                'label': '创建用品',
                'url_name': 'admin_pages:supply_create',
                'permission': 'administrative_management.supply.create',
                'path_keywords': ['supplies/create'],
                'icon': 'bi-plus-circle',
            },
            {
                'id': 'supply_category',
                'label': '用品分类',
                'url_name': 'admin_pages:supply_category_list',
                'permission': 'administrative_management.supplies.view',
                'path_keywords': ['supplies/categories', 'category'],
                'icon': 'bi-tags',
            },
            {
                'id': 'supply_category_create',
                'label': '创建分类',
                'url_name': 'admin_pages:supply_category_create',
                'permission': 'administrative_management.supplies.manage',
                'path_keywords': ['supplies/categories/create'],
                'icon': 'bi-plus-circle',
            },
        ],
    },
    {
        'id': 'supply_purchase_group',
        'label': '用品采购',
        'icon': '🛒',
        'permission': 'administrative_management.supplies.view',
        'expanded': False,
        'children': [
            {
                'id': 'supply_purchase',
                'label': '采购管理',
                'url_name': 'admin_pages:supply_purchase_list',
                'permission': 'administrative_management.supplies.view',
                'path_keywords': ['supplies/purchases', 'purchase'],
                'icon': 'bi-cart',
            },
            {
                'id': 'supply_purchase_create',
                'label': '创建采购',
                'url_name': 'admin_pages:supply_purchase_create',
                'permission': 'administrative_management.supply.purchase',
                'path_keywords': ['supplies/purchases/create'],
                'icon': 'bi-plus-circle',
            },
        ],
    },
    {
        'id': 'supply_request_group',
        'label': '用品领用',
        'icon': '🎒',
        'permission': 'administrative_management.supplies.view',
        'expanded': False,
        'children': [
            {
                'id': 'supply_request',
                'label': '领用管理',
                'url_name': 'admin_pages:supply_request_list',
                'permission': 'administrative_management.supplies.view',
                'path_keywords': ['supplies/requests', 'request'],
                'icon': 'bi-handbag',
            },
            {
                'id': 'supply_request_create',
                'label': '创建领用',
                'url_name': 'admin_pages:supply_request_create',
                'permission': 'administrative_management.supply.request',
                'path_keywords': ['supplies/requests/create'],
                'icon': 'bi-plus-circle',
            },
        ],
    },
    {
        'id': 'inventory',
        'label': '库存管理',
        'icon': '📊',
        'permission': 'administrative_management.supplies.view',
        'expanded': False,
        'children': [
            {
                'id': 'inventory_check',
                'label': '库存盘点',
                'url_name': 'admin_pages:inventory_check_list',
                'permission': 'administrative_management.supplies.view',
                'path_keywords': ['supplies/inventory/checks', 'inventory_check'],
                'icon': 'bi-clipboard-check',
            },
            {
                'id': 'inventory_check_create',
                'label': '创建盘点',
                'url_name': 'admin_pages:inventory_check_create',
                'permission': 'administrative_management.supplies.view',
                'path_keywords': ['supplies/inventory/checks/create'],
                'icon': 'bi-plus-circle',
            },
            {
                'id': 'inventory_adjust',
                'label': '库存调整',
                'url_name': 'admin_pages:inventory_adjust_list',
                'permission': 'administrative_management.supplies.view',
                'path_keywords': ['supplies/inventory/adjusts', 'inventory_adjust'],
                'icon': 'bi-arrow-left-right',
            },
            {
                'id': 'inventory_adjust_create',
                'label': '创建调整',
                'url_name': 'admin_pages:inventory_adjust_create',
                'permission': 'administrative_management.supplies.view',
                'path_keywords': ['supplies/inventory/adjusts/create'],
                'icon': 'bi-plus-circle',
            },
        ],
    },
    {
        'id': 'meeting',
        'label': '会议管理',
        'icon': '🏢',
        'permission': 'administrative_management.meeting_room.view',
        'expanded': False,
        'children': [
            {
                'id': 'meeting_room',
                'label': '会议室管理',
                'url_name': 'admin_pages:meeting_room_management',
                'permission': 'administrative_management.meeting_room.view',
                'path_keywords': ['meeting', 'meeting_room'],
                'icon': 'bi-door-open',
            },
            {
                'id': 'meeting_room_create',
                'label': '创建会议室',
                'url_name': 'admin_pages:meeting_room_create',
                'permission': 'administrative_management.meeting_room.create',
                'path_keywords': ['meeting-rooms/create'],
                'icon': 'bi-plus-circle',
            },
            {
                'id': 'meeting_room_booking',
                'label': '会议室预订',
                'url_name': 'admin_pages:meeting_room_booking_list',
                'permission': 'administrative_management.meeting_room.view',
                'path_keywords': ['meeting-rooms/bookings', 'booking'],
                'icon': 'bi-calendar-check',
            },
            {
                'id': 'meeting_room_booking_create',
                'label': '创建预订',
                'url_name': 'admin_pages:meeting_room_booking_create',
                'permission': 'administrative_management.meeting_room.booking',
                'path_keywords': ['meeting-rooms/bookings/create'],
                'icon': 'bi-plus-circle',
            },
            {
                'id': 'meeting_list',
                'label': '会议安排',
                'url_name': 'admin_pages:meeting_list',
                'permission': 'administrative_management.meeting_room.view',
                'path_keywords': ['meetings', 'meeting'],
                'icon': 'bi-people',
            },
            {
                'id': 'meeting_create',
                'label': '创建会议',
                'url_name': 'admin_pages:meeting_create',
                'permission': 'administrative_management.meeting.create',
                'path_keywords': ['meetings/create'],
                'icon': 'bi-plus-circle',
            },
        ],
    },
    {
        'id': 'vehicle',
        'label': '车辆管理',
        'icon': '🚗',
        'permission': 'administrative_management.vehicle.view',
        'expanded': False,
        'children': [
            {
                'id': 'vehicle_management',
                'label': '车辆管理',
                'url_name': 'admin_pages:vehicle_management',
                'permission': 'administrative_management.vehicle.view',
                'path_keywords': ['vehicle'],
                'icon': 'bi-car-front',
            },
            {
                'id': 'vehicle_create',
                'label': '创建车辆',
                'url_name': 'admin_pages:vehicle_create',
                'permission': 'administrative_management.vehicle.create',
                'path_keywords': ['vehicles/create'],
                'icon': 'bi-plus-circle',
            },
            {
                'id': 'vehicle_booking',
                'label': '用车申请',
                'url_name': 'admin_pages:vehicle_booking_list',
                'permission': 'administrative_management.vehicle.view',
                'path_keywords': ['vehicles/bookings', 'booking'],
                'icon': 'bi-calendar-event',
            },
            {
                'id': 'vehicle_booking_create',
                'label': '创建申请',
                'url_name': 'admin_pages:vehicle_booking_create',
                'permission': 'administrative_management.vehicle.booking',
                'path_keywords': ['vehicles/bookings/create'],
                'icon': 'bi-plus-circle',
            },
        ],
    },
    {
        'id': 'asset',
        'label': '固定资产管理',
        'icon': '🏛️',
        'permission': 'administrative_management.asset.view',
        'expanded': False,
        'children': [
            {
                'id': 'asset_management',
                'label': '固定资产',
                'url_name': 'admin_pages:asset_management',
                'permission': 'administrative_management.asset.view',
                'path_keywords': ['asset'],
                'icon': 'bi-building',
            },
            {
                'id': 'asset_create',
                'label': '创建资产',
                'url_name': 'admin_pages:asset_create',
                'permission': 'administrative_management.asset.create',
                'path_keywords': ['assets/create'],
                'icon': 'bi-plus-circle',
            },
            {
                'id': 'asset_transfer',
                'label': '资产转移',
                'url_name': 'admin_pages:asset_transfer_list',
                'permission': 'administrative_management.asset.view',
                'path_keywords': ['assets/transfers', 'transfer'],
                'icon': 'bi-arrow-left-right',
            },
        ],
    },
    {
        'id': 'seal_usage',
        'label': '用印管理',
        'icon': '📝',
        'permission': 'administrative_management.seal.view',
        'expanded': False,
        'children': [
            {
                'id': 'seal_usage_create',
                'label': '申请用印',
                'url_name': 'admin_pages:seal_usage_create',
                'permission': 'administrative_management.seal.view',  # 有查看权限即可申请用印
                'path_keywords': ['seal.*usage', 'usage'],
                'icon': 'bi-file-earmark-text',
            },
            {
                'id': 'seal_usage_list',
                'label': '用印列表',
                'url_name': 'admin_pages:seal_usage_list',
                'permission': 'administrative_management.seal.view',
                'path_keywords': ['seals/usages', 'usage'],
                'icon': 'bi-list-check',
            },
        ],
    },
    {
        'id': 'seal',
        'label': '印章管理',
        'icon': '🔐',
        'permission': 'administrative_management.seal.view',
        'expanded': False,
        'children': [
            {
                'id': 'seal_management',
                'label': '印章列表',
                'url_name': 'admin_pages:seal_management',
                'permission': 'administrative_management.seal.view',
                'path_keywords': ['seal'],
                'icon': 'bi-shield-lock',
            },
            {
                'id': 'seal_create',
                'label': '新增印章',
                'url_name': 'admin_pages:seal_create',
                'permission': 'administrative_management.seal.create',
                'path_keywords': ['seal.*create', 'seals/create'],
                'icon': 'bi-plus-circle',
            },
            {
                'id': 'seal_borrowing_create',
                'label': '申请借用',
                'url_name': 'admin_pages:seal_borrowing_create',
                'permission': 'administrative_management.seal.borrow',  # 优先使用 borrow 权限，如果没有则 fallback 到 view
                'path_keywords': ['seal.*borrow', 'borrow'],
                'icon': 'bi-box-arrow-in-right',
            },
            {
                'id': 'seal_borrowing_return_list',
                'label': '归还印章',
                'url_name': 'admin_pages:seal_borrowing_return_list',
                'permission': 'administrative_management.seal.view',  # 有查看权限即可归还
                'path_keywords': ['seal.*return', 'return'],
                'icon': 'bi-box-arrow-in-left',
            },
        ],
    },
    {
        'id': 'reception',
        'label': '接待管理',
        'icon': '🎫',
        'permission': 'administrative_management.reception.view',
        'expanded': False,
        'children': [
            {
                'id': 'reception_management',
                'label': '接待管理',
                'url_name': 'admin_pages:reception_management',
                'permission': 'administrative_management.reception.view',
                'path_keywords': ['reception'],
                'icon': 'bi-person-heart',
            },
            {
                'id': 'reception_create',
                'label': '创建接待',
                'url_name': 'admin_pages:reception_create',
                'permission': 'administrative_management.reception.create',
                'path_keywords': ['receptions/create'],
                'icon': 'bi-plus-circle',
            },
        ],
    },
    {
        'id': 'travel',
        'label': '差旅管理',
        'icon': '✈️',
        'permission': 'administrative_management.travel.view',
        'expanded': False,
        'children': [
            {
                'id': 'travel_list',
                'label': '差旅申请',
                'url_name': 'admin_pages:travel_list',
                'permission': 'administrative_management.travel.view',
                'path_keywords': ['travel', 'expense'],
                'icon': 'bi-airplane',
            },
            {
                'id': 'travel_create',
                'label': '创建差旅',
                'url_name': 'admin_pages:travel_create',
                'permission': 'administrative_management.travel.create',
                'path_keywords': ['travels/create'],
                'icon': 'bi-plus-circle',
            },
            {
                'id': 'expense_management',
                'label': '报销管理',
                'url_name': 'admin_pages:expense_management',
                'permission': 'administrative_management.travel.view',
                'path_keywords': ['expenses', 'expense'],
                'icon': 'bi-receipt',
            },
            {
                'id': 'expense_create',
                'label': '创建报销',
                'url_name': 'admin_pages:expense_create',
                'permission': 'administrative_management.expense.create',
                'path_keywords': ['expenses/create'],
                'icon': 'bi-plus-circle',
            },
        ],
    },
    {
        'id': 'supplier',
        'label': '供应商管理',
        'icon': '🚚',
        'permission': 'administrative_management.supplies.view',
        'expanded': False,
        'children': [
            {
                'id': 'supplier_list',
                'label': '供应商管理',
                'url_name': 'admin_pages:supplier_list',
                'permission': 'administrative_management.supplies.view',
                'path_keywords': ['suppliers', 'supplier'],
                'icon': 'bi-truck',
            },
            {
                'id': 'supplier_create',
                'label': '创建供应商',
                'url_name': 'admin_pages:supplier_create',
                'permission': 'administrative_management.supplies.view',
                'path_keywords': ['suppliers/create'],
                'icon': 'bi-plus-circle',
            },
        ],
    },
    {
        'id': 'purchase',
        'label': '采购管理',
        'icon': '🛒',
        'permission': 'administrative_management.supplies.view',
        'expanded': False,
        'children': [
            {
                'id': 'purchase_contract',
                'label': '采购合同',
                'url_name': 'admin_pages:purchase_contract_list',
                'permission': 'administrative_management.supplies.view',
                'path_keywords': ['purchases/contracts', 'contract'],
                'icon': 'bi-file-earmark-text',
            },
            {
                'id': 'purchase_contract_create',
                'label': '创建合同',
                'url_name': 'admin_pages:purchase_contract_create',
                'permission': 'administrative_management.contract.create',
                'path_keywords': ['purchases/contracts/create'],
                'icon': 'bi-plus-circle',
            },
        ],
    },
    {
        'id': 'payment',
        'label': '支付管理',
        'icon': '💳',
        'permission': 'administrative_management.supplies.view',
        'expanded': False,
        'children': [
            {
                'id': 'purchase_payment',
                'label': '采购付款',
                'url_name': 'admin_pages:purchase_payment_list',
                'permission': 'administrative_management.supplies.view',
                'path_keywords': ['purchases/payments', 'payment'],
                'icon': 'bi-credit-card',
            },
            {
                'id': 'purchase_payment_create',
                'label': '创建付款',
                'url_name': 'admin_pages:purchase_payment_create',
                'permission': 'administrative_management.payment.create',
                'path_keywords': ['purchases/payments/create'],
                'icon': 'bi-plus-circle',
            },
        ],
    },
    {
        'id': 'announcement',
        'label': '公告通知',
        'icon': '📢',
        'permission': None,  # 所有用户都可以访问
        'expanded': False,
        'children': [
            {
                'id': 'announcement_management',
                'label': '公告管理',
                'url_name': 'admin_pages:announcement_management',
                'permission': None,
                'path_keywords': ['announcements', 'announcement'],
                'icon': 'bi-megaphone',
            },
            {
                'id': 'announcement_create',
                'label': '创建公告',
                'url_name': 'admin_pages:announcement_create',
                'permission': None,
                'path_keywords': ['announcements/create'],
                'icon': 'bi-plus-circle',
            },
        ],
    },
]


def _build_administrative_sidebar_nav(permission_set, request_path=None, active_id=None):
    """生成行政管理模块的左侧菜单导航（分组格式）
    
    Args:
        permission_set: 用户权限集合
        request_path: 当前请求路径，用于判断激活状态
    
    Returns:
        list: 分组菜单项列表，格式为：
        [
            {
                'label': '分组名称',
                'icon': '图标',
                'expanded': True/False,
                'children': [
                    {
                        'label': '子菜单项名称',
                        'url': 'URL',
                        'active': True/False,
                    },
                    ...
                ],
            },
            ...
        ]
    """
    from django.urls import reverse, NoReverseMatch
    
    # 构建分组菜单
    menu_groups = []
    try:
        for group in ADMINISTRATIVE_MANAGEMENT_SIDEBAR_MENU:
            # 检查分组权限
            if group.get('permission') and not _permission_granted(group['permission'], permission_set):
                continue
            
            # 处理顶级菜单项（没有 children 的菜单项）
            if 'children' not in group or not group.get('children'):
                # 这是一个顶级菜单项，直接添加
                try:
                    # 检查权限
                    if group.get('permission') and not _permission_granted(group['permission'], permission_set):
                        continue
                    
                    # 获取URL
                    try:
                        url = reverse(group['url_name'])
                    except NoReverseMatch:
                        url = '#'
                    
                    # 判断是否激活
                    active = False
                    if active_id:
                        active = group.get('id') == active_id
                    elif request_path:
                        # 特殊处理首页
                        if group.get('id') == 'administrative_home':
                            try:
                                home_url = reverse('admin_pages:administrative_home')
                                try:
                                    home_url2 = reverse('admin_pages:administrative_management_home')
                                except NoReverseMatch:
                                    home_url2 = None
                                active = (
                                    request_path == home_url or
                                    (home_url2 and request_path == home_url2) or
                                    request_path == '/administrative/' or
                                    request_path == '/administrative/home/'
                                )
                            except NoReverseMatch:
                                pass
                        if not active:
                            for keyword in group.get('path_keywords', []):
                                if keyword in request_path:
                                    active = True
                                    break
                    
                    menu_groups.append({
                        'label': group['label'],
                        'url': url,
                        'active': active,
                        'icon': group.get('icon', ''),
                        'is_top_level': True,  # 标记为顶级菜单项
                    })
                except Exception as e:
                    logger.warning('构建顶级菜单项失败: %s, 错误: %s', group.get('label', 'unknown'), str(e))
                    continue
                continue  # 跳过后续的分组处理逻辑
            
            # 构建子菜单项（分组菜单）
            children = []
            for child in group.get('children', []):
                try:
                    # 检查子项权限（支持 fallback）
                    child_permission = child.get('permission')
                    if child_permission:
                        # 特殊处理：印章借用权限 fallback 到查看权限
                        if child_permission == 'administrative_management.seal.borrow':
                            if not _permission_granted(child_permission, permission_set) and \
                               not _permission_granted('administrative_management.seal.view', permission_set):
                                continue
                        else:
                            if not _permission_granted(child_permission, permission_set):
                                continue
                    
                    # 获取URL
                    try:
                        url = reverse(child['url_name'])
                    except NoReverseMatch:
                        url = '#'
                    
                    # 判断是否激活
                    active = False
                    if active_id:
                        active = child.get('id') == active_id
                    elif request_path:
                        # 特殊处理首页
                        if child.get('id') == 'administrative_home':
                            try:
                                home_url = reverse('admin_pages:administrative_home')
                                try:
                                    home_url2 = reverse('admin_pages:administrative_management_home')
                                except NoReverseMatch:
                                    home_url2 = None
                                active = (
                                    request_path == home_url or
                                    (home_url2 and request_path == home_url2) or
                                    request_path == '/administrative/' or
                                    request_path == '/administrative/home/'
                                )
                            except NoReverseMatch:
                                pass
                        if not active:
                            for keyword in child.get('path_keywords', []):
                                if keyword in request_path:
                                    active = True
                                    break
                    
                    children.append({
                        'label': child['label'],
                        'url': url,
                        'active': active,
                        'icon': child.get('icon', ''),
                    })
                except Exception as e:
                    logger.warning('构建子菜单项失败: %s, 错误: %s', child.get('label', 'unknown'), str(e))
                    continue
            
            # 只有当分组有可见的子项时才添加分组
            if children:
                # 判断分组是否应该展开（如果有激活的子项，则展开）
                expanded = group.get('expanded', False)
                if not expanded and request_path:
                    for child in children:
                        if child.get('active'):
                            expanded = True
                            break
                
                menu_groups.append({
                    'label': group['label'],
                    'icon': group.get('icon', ''),
                    'expanded': expanded,
                    'children': children,
                })
    except Exception as e:
        logger.exception('构建行政管理左侧菜单导航失败: %s', str(e))
        return []
    
    return menu_groups


def _context(page_title, page_icon, description, summary_cards=None, sections=None, request=None, use_administrative_nav=False):
    """构建页面上下文
    
    Args:
        use_administrative_nav: 已废弃，统一使用全局系统主菜单
    """
    context = {
        "page_title": page_title,
        "page_icon": page_icon,
        "description": description,
        "summary_cards": summary_cards or [],
        "sections": sections or [],
    }
    
    if request and request.user.is_authenticated:
        try:
            permission_set = get_user_permission_codes(request.user)
            # 统一使用全局系统主菜单（与客户管理、财务管理模块保持一致）
            context['full_top_nav'] = _build_full_top_nav(permission_set, request.user)
            
            # 添加左侧菜单导航（使用统一的变量名 sidebar_menu）
            context['sidebar_nav'] = _build_administrative_sidebar_nav(permission_set, request.path)
        except Exception as e:
            import logging
            logger = logging.getLogger(__name__)
            logger.exception('构建页面上下文失败: %s', str(e))
            # 发生错误时使用空列表，避免页面崩溃
            context['full_top_nav'] = []
            context['sidebar_nav'] = []
    else:
        context['full_top_nav'] = []
        context['sidebar_nav'] = []
    # 为所有可能的侧边栏变量设置默认值，避免模板错误
    # 这些变量可能在其他模块的模板中被引用
    context.setdefault('plan_menu', [])
    context.setdefault('sidebar_nav', [])
    context.setdefault('customer_menu', [])
    context.setdefault('sidebar_nav', [])
    context.setdefault('sidebar_nav', [])
    context.setdefault('sidebar_nav', [])
    context.setdefault('sidebar_nav', [])
    context.setdefault('sidebar_nav', [])
    context.setdefault('sidebar_nav', [])
    
    return context


def _format_user_display(user, default='—'):
    """格式化用户显示名称"""
    if not user:
        return default
    if hasattr(user, 'get_full_name') and user.get_full_name():
        return user.get_full_name()
    return user.username if hasattr(user, 'username') else str(user)


@login_required
def administrative_home(request):
    """行政管理首页 - 数据展示中心"""
    permission_codes = get_user_permission_codes(request.user)
    now = timezone.now()
    today = now.date()
    this_month_start = today.replace(day=1)
    seven_days_ago = today - timedelta(days=7)
    
    context = {}
    
    try:
        from django.db.models import Count, Q
        from .models import AdministrativeAffair, OfficeSupply, MeetingRoom, Vehicle
        
        # ========== 核心指标卡片 ==========
        core_cards = []
        
        # 行政事务统计
        all_affairs = AdministrativeAffair.objects.all()
        total_affairs = all_affairs.count()
        pending_affairs = all_affairs.filter(status='pending').count()
        in_progress_affairs = all_affairs.filter(status='in_progress').count()
        completed_affairs = all_affairs.filter(status='completed').count()
        
        # 办公用品统计
        all_supplies = OfficeSupply.objects.filter(is_active=True)
        total_supplies = all_supplies.count()
        low_stock_supplies = all_supplies.filter(current_stock__lte=F('min_stock')).count()
        
        # 会议室统计
        all_rooms = MeetingRoom.objects.filter(is_active=True)
        total_rooms = all_rooms.count()
        available_rooms = all_rooms.filter(status='available').count()
        
        # 车辆统计
        all_vehicles = Vehicle.objects.filter(is_active=True)
        total_vehicles = all_vehicles.count()
        available_vehicles = all_vehicles.filter(status='available').count()
        
        # 卡片1：行政事务
        core_cards.append({
            'label': '行政事务',
            'icon': '📋',
            'value': str(total_affairs),
            'subvalue': f'待处理 {pending_affairs} | 进行中 {in_progress_affairs} | 已完成 {completed_affairs}',
            'url': reverse('admin_pages:affair_list'),
            'variant': 'dark' if pending_affairs > 0 else 'secondary'
        })
        
        # 卡片2：办公用品
        core_cards.append({
            'label': '办公用品',
            'icon': '📦',
            'value': str(total_supplies),
            'subvalue': f'低库存 {low_stock_supplies} 种',
            'url': reverse('admin_pages:supplies_management'),
            'variant': 'dark' if low_stock_supplies > 0 else 'secondary'
        })
        
        # 卡片3：会议室
        core_cards.append({
            'label': '会议室',
            'icon': '🏢',
            'value': str(total_rooms),
            'subvalue': f'可用 {available_rooms} 间',
            'url': reverse('admin_pages:meeting_room_management'),
            'variant': 'secondary'
        })
        
        # 卡片4：车辆
        core_cards.append({
            'label': '车辆',
            'icon': '🚗',
            'value': str(total_vehicles),
            'subvalue': f'可用 {available_vehicles} 辆',
            'url': reverse('admin_pages:vehicle_management'),
            'variant': 'secondary'
        })
        
        context['core_cards'] = core_cards
        
        # ========== 风险预警 ==========
        risk_warnings = []
        
        # 待处理事务（超过7天）
        stale_affairs = all_affairs.filter(
            status='pending',
            created_time__lt=timezone.make_aware(datetime.combine(seven_days_ago, datetime.min.time()))
        ).select_related('responsible_user')[:5]
        
        for affair in stale_affairs:
            days_since_create = (today - affair.created_time.date()).days
            responsible_name = _format_user_display(affair.responsible_user) if affair.responsible_user else '未知'
            risk_warnings.append({
                'type': 'affair',
                'title': affair.title,
                'responsible': responsible_name,
                'days': days_since_create,
                'url': reverse('admin_pages:affair_detail', args=[affair.id])
            })
        
        # 低库存办公用品
        low_stock_list = all_supplies.filter(current_stock__lte=F('min_stock'))[:5]
        for supply in low_stock_list:
            risk_warnings.append({
                'type': 'supply',
                'title': f'{supply.name} - 库存不足',
                'responsible': '库存管理员',
                'days': 0,
                'url': reverse('admin_pages:supply_detail', args=[supply.id])
            })
        
        context['risk_warnings'] = risk_warnings[:5]
        context['stale_affairs_count'] = stale_affairs.count()
        context['low_stock_count'] = low_stock_supplies
        
        # ========== 待办事项 ==========
        todo_items = []
        
        # 待处理事务
        pending_affair_list = all_affairs.filter(status='pending').select_related('responsible_user')[:5]
        for affair in pending_affair_list:
            responsible_name = _format_user_display(affair.responsible_user) if affair.responsible_user else '未知'
            todo_items.append({
                'type': 'affair',
                'title': affair.title,
                'affair_number': affair.affair_number,
                'responsible': responsible_name,
                'url': reverse('admin_pages:affair_detail', args=[affair.id])
            })
        
        context['todo_items'] = todo_items[:10]
        context['pending_approval_count'] = pending_affairs
        context['todo_summary_url'] = reverse('admin_pages:affair_list') + '?status=pending'
        
        # ========== 我的工作 ==========
        my_work = {}
        
        # 我负责的事务
        my_affairs = all_affairs.filter(responsible_user=request.user).order_by('-created_time')[:3]
        my_work['my_affairs'] = [{
            'title': affair.title,
            'status': affair.get_status_display(),
            'url': reverse('admin_pages:affair_detail', args=[affair.id])
        } for affair in my_affairs]
        my_work['my_affairs_count'] = all_affairs.filter(responsible_user=request.user).count()
        
        my_work['summary_url'] = reverse('admin_pages:affair_list')
        
        context['my_work'] = my_work
        
        # ========== 最近活动 ==========
        recent_activities = {}
        
        # 最近创建的事务
        recent_affairs = all_affairs.select_related('responsible_user').order_by('-created_time')[:5]
        recent_activities['recent_affairs'] = [{
            'title': affair.title,
            'creator': _format_user_display(affair.responsible_user),
            'time': affair.created_time,
            'url': reverse('admin_pages:affair_detail', args=[affair.id])
        } for affair in recent_affairs]
        
        context['recent_activities'] = recent_activities
        
    except Exception as e:
        logger.exception('获取行政管理统计数据失败: %s', str(e))
        context.setdefault('core_cards', [])
        context.setdefault('risk_warnings', [])
        context.setdefault('todo_items', [])
        context.setdefault('my_work', {})
        context.setdefault('recent_activities', {})
    
    # 顶部操作栏
    top_actions = []
    if _permission_granted('administrative_management.affair.create', permission_codes):
        try:
            top_actions.append({
                'label': '创建事务',
                'url': reverse('admin_pages:affair_create'),
                'icon': '➕'
            })
        except Exception:
            pass
    
    context['top_actions'] = top_actions
    
    # 构建上下文
    page_context = _context(
        "行政管理",
        "🏢",
        "数据展示中心 - 集中展示行政关键指标、状态与风险",
        request=request,
    )
    
    # 设置侧边栏导航
    administrative_sidebar_nav = _build_administrative_sidebar_nav(permission_codes, request.path, active_id='administrative_home')
    page_context['sidebar_nav'] = administrative_sidebar_nav
    page_context['sidebar_title'] = '行政管理'
    page_context['sidebar_subtitle'] = 'Administrative Management'
    
    # 合并所有数据
    page_context.update(context)
    
    return render(request, "administrative_management/administrative_management_home.html", page_context)


@login_required
def affair_list(request):
    """行政事务列表"""
    import logging
    logger = logging.getLogger(__name__)
    
    try:
        # 获取筛选参数
        search = request.GET.get('search', '')
        affair_type = request.GET.get('affair_type', '')
        status = request.GET.get('status', '')
        priority = request.GET.get('priority', '')
        responsible_user_id = request.GET.get('responsible_user_id', '')
        
        # 获取事务列表（用于统计，在筛选之前）
        base_affairs = AdministrativeAffair.objects.select_related(
            'responsible_user', 'created_by'
        ).prefetch_related('participants').all()
        
        # 如果是普通用户，只显示自己负责或参与的
        permission_codes = get_user_permission_codes(request.user)
        if not _permission_granted('administrative_management.affair.view_all', permission_codes):
            base_affairs = base_affairs.filter(
                Q(responsible_user=request.user) |
                Q(participants=request.user) |
                Q(created_by=request.user)
            ).distinct()
        
        # 统计数据（在过滤之前获取，显示全部数据统计）
        total_count = base_affairs.count()
        pending_count = base_affairs.filter(status='pending').count()
        in_progress_count = base_affairs.filter(status='in_progress').count()
        completed_count = base_affairs.filter(status='completed').count()
        cancelled_count = base_affairs.filter(status='cancelled').count()
        
        # 应用筛选条件
        affairs = base_affairs.order_by('-created_time')
        
        if search:
            affairs = affairs.filter(
                Q(affair_number__icontains=search) |
                Q(title__icontains=search) |
                Q(content__icontains=search)
            )
        if affair_type:
            affairs = affairs.filter(affair_type=affair_type)
        if status:
            affairs = affairs.filter(status=status)
        if priority:
            affairs = affairs.filter(priority=priority)
        if responsible_user_id:
            affairs = affairs.filter(responsible_user_id=responsible_user_id)
        
        # 分页（每页20条）
        paginator = Paginator(affairs, 20)
        page_number = request.GET.get('page', 1)
        try:
            page_obj = paginator.get_page(page_number)
        except:
            page_obj = paginator.get_page(1)
        
        # 生成左侧菜单
        sidebar_menu = _build_administrative_sidebar_nav(permission_codes, request.path)
        
        context = _context(
            "行政事务管理",
            "📋",
            "管理日常行政事务，包括事务创建、分配、处理、跟踪等全流程管理。",
            request=request,
            use_administrative_nav=True
        )
        context.update({
            'page_obj': page_obj,
            'page': page_obj,  # 兼容模板中的变量名
            'affairs': page_obj.object_list if page_obj else [],
            'search': search,
            'affair_type': affair_type,
            'status': status,
            'status_filter': status,  # 兼容模板中的变量名
            'priority': priority,
            'priority_filter': priority,  # 兼容模板中的变量名
            'responsible_user_id': responsible_user_id,
            'affair_type_choices': AdministrativeAffair.AFFAIR_TYPE_CHOICES,
            'status_choices': AdministrativeAffair.STATUS_CHOICES,
            'priority_choices': AdministrativeAffair.PRIORITY_CHOICES,
            'total_count': total_count,
            'pending_count': pending_count,
            'in_progress_count': in_progress_count,
            'completed_count': completed_count,
            'cancelled_count': cancelled_count,
            'sidebar_menu': sidebar_menu,
            'module_sidebar_nav': sidebar_menu,  # 兼容模板中的变量名
            'sidebar_title': '行政管理',  # 侧边栏标题
            'sidebar_subtitle': 'Administrative Management',  # 侧边栏副标题
        })
        return render(request, "administrative_management/affair_list.html", context)
    except Exception as e:
        logger.exception('行政事务列表页面加载失败: %s', str(e))
        messages.error(request, f'页面加载失败: {str(e)}')
        # 返回一个简单的错误页面，而不是500错误
        return render(request, "administrative_management/affair_list.html", {
            'page_obj': None,
            'search': '',
            'affair_type': '',
            'status': '',
            'priority': '',
            'responsible_user_id': '',
            'affair_type_choices': AdministrativeAffair.AFFAIR_TYPE_CHOICES if hasattr(AdministrativeAffair, 'AFFAIR_TYPE_CHOICES') else [],
            'status_choices': AdministrativeAffair.STATUS_CHOICES if hasattr(AdministrativeAffair, 'STATUS_CHOICES') else [],
            'priority_choices': AdministrativeAffair.PRIORITY_CHOICES if hasattr(AdministrativeAffair, 'PRIORITY_CHOICES') else [],
            'summary_cards': [],
            'page_title': '行政事务管理',
            'page_icon': '📋',
            'description': '管理日常行政事务',
            'full_top_nav': [],
            'sidebar_nav': [],
        })


@login_required
def administrative_home_old(request):
    """行政管理主页（旧版本，已注释掉）"""
    # 此函数已被注释，现在使用affair_list作为首页
    permission_codes = get_user_permission_codes(request.user)
    today = timezone.now().date()
    this_month_start = today.replace(day=1)
    
    # 收集统计数据
    stats_cards = []
    
    try:
        # 办公用品统计
        if _permission_granted('administrative_management.supplies.view', permission_codes):
            try:
                total_supplies = OfficeSupply.objects.count()
                active_supplies = OfficeSupply.objects.filter(is_active=True).count()
                low_stock_count = OfficeSupply.objects.filter(
                    current_stock__lte=F('min_stock'),
                    min_stock__gt=0
                ).count()
                total_value = sum(float(s.purchase_price) * s.current_stock for s in OfficeSupply.objects.filter(is_active=True))
                
                try:
                    url = reverse('admin_pages:supplies_management')
                except NoReverseMatch:
                    url = '#'
                stats_cards.append({
                    'label': '办公用品',
                    'icon': '📦',
                    'value': f'{total_supplies}',
                    'subvalue': f'在用 {active_supplies} · 低库存 {low_stock_count}',
                    'extra': f'库存总值 ¥{total_value:,.2f}',
                    'url': url,
                })
            except Exception:
                pass
        
        # 会议室统计
        if _permission_granted('administrative_management.meeting_room.view', permission_codes):
            try:
                total_rooms = MeetingRoom.objects.count()
                available_rooms = MeetingRoom.objects.filter(is_active=True, status='available').count()
                today_bookings = MeetingRoomBooking.objects.filter(
                    booking_date=today,
                    status__in=['confirmed', 'in_progress']
                ).count()
                
                try:
                    url = reverse('admin_pages:meeting_room_management')
                except NoReverseMatch:
                    url = '#'
                stats_cards.append({
                    'label': '会议室',
                    'icon': '🏛️',
                    'value': f'{total_rooms}',
                    'subvalue': f'可用 {available_rooms} · 今日预订 {today_bookings}',
                    'url': url,
                })
            except Exception:
                pass
        
        # 用车管理统计
        if _permission_granted('administrative_management.vehicle.view', permission_codes):
            try:
                total_vehicles = Vehicle.objects.filter(is_active=True).count()
                available_vehicles = Vehicle.objects.filter(is_active=True, status='available').count()
                today_bookings = VehicleBooking.objects.filter(
                    booking_date=today,
                    status__in=['confirmed', 'in_progress']
                ).count()
                
                try:
                    url = reverse('admin_pages:vehicle_management')
                except NoReverseMatch:
                    url = '#'
                stats_cards.append({
                    'label': '用车管理',
                    'icon': '🚗',
                    'value': f'{total_vehicles}',
                    'subvalue': f'可用 {available_vehicles} · 今日预订 {today_bookings}',
                    'url': url,
                })
            except Exception:
                pass
        
        # 接待管理统计
        if _permission_granted('administrative_management.reception.view', permission_codes):
            try:
                from .models import ReceptionExpense
                this_month_receptions = ReceptionRecord.objects.filter(
                    reception_date__gte=this_month_start
                ).count()
                total_expense = ReceptionExpense.objects.filter(
                    reception__reception_date__gte=this_month_start
                ).aggregate(total=Sum('amount'))['total'] or Decimal('0')
                
                try:
                    url = reverse('admin_pages:reception_management')
                except NoReverseMatch:
                    url = '#'
                stats_cards.append({
                    'label': '接待管理',
                    'icon': '🤝',
                    'value': f'{this_month_receptions}',
                    'subvalue': f'本月接待',
                    'extra': f'费用 ¥{total_expense:,.2f}',
                    'url': url,
                })
            except Exception:
                pass
        
        # 公告通知统计
        if _permission_granted('administrative_management.announcement.view', permission_codes):
            try:
                active_announcements = Announcement.objects.filter(
                    is_active=True,
                    publish_date__lte=today
                ).count()
                unread_count = Announcement.objects.filter(
                    is_active=True,
                    publish_date__lte=today
                ).exclude(
                    read_records__user=request.user
                ).count() if request.user.is_authenticated else 0
                
                try:
                    url = reverse('admin_pages:announcement_management')
                except NoReverseMatch:
                    url = '#'
                stats_cards.append({
                    'label': '公告通知',
                    'icon': '📢',
                    'value': f'{active_announcements}',
                    'subvalue': f'生效中 · 未读 {unread_count}',
                    'url': url,
                })
            except Exception:
                pass
        
        # 印章管理统计
        if _permission_granted('administrative_management.seal.view', permission_codes):
            try:
                total_seals = Seal.objects.filter(is_active=True).count()
                borrowed_seals = Seal.objects.filter(status='borrowed').count()
                available_seals = Seal.objects.filter(status='available').count()
                
                try:
                    url = reverse('admin_pages:seal_management')
                except NoReverseMatch:
                    url = '#'
                stats_cards.append({
                    'label': '印章管理',
                    'icon': '🔐',
                    'value': f'{total_seals}',
                    'subvalue': f'可用 {available_seals} · 已借出 {borrowed_seals}',
                    'url': url,
                })
            except Exception:
                pass
        
        # 固定资产统计
        if _permission_granted('administrative_management.asset.view', permission_codes):
            try:
                total_assets = FixedAsset.objects.filter(is_active=True).count()
                total_value = FixedAsset.objects.filter(is_active=True).aggregate(
                    total=Sum('net_value')
                )['total'] or Decimal('0')
                maintenance_count = FixedAsset.objects.filter(
                    is_active=True,
                    status='maintenance'
                ).count()
                
                try:
                    url = reverse('admin_pages:asset_management')
                except NoReverseMatch:
                    url = '#'
                stats_cards.append({
                    'label': '固定资产',
                    'icon': '💼',
                    'value': f'{total_assets}',
                    'subvalue': f'维护中 {maintenance_count}',
                    'extra': f'净值 ¥{total_value:,.2f}',
                    'url': url,
                })
            except Exception:
                pass
        
        # 报销管理统计
        if _permission_granted('administrative_management.expense.view', permission_codes):
            try:
                pending_expenses = ExpenseReimbursement.objects.filter(
                    status='pending_approval'
                ).count()
                this_month_expenses = ExpenseReimbursement.objects.filter(
                    application_date__gte=this_month_start
                ).count()
                this_month_amount = ExpenseReimbursement.objects.filter(
                    application_date__gte=this_month_start,
                    status__in=['approved', 'paid']
                ).aggregate(total=Sum('total_amount'))['total'] or Decimal('0')
                
                try:
                    url = reverse('admin_pages:expense_management')
                except NoReverseMatch:
                    url = '#'
                stats_cards.append({
                    'label': '报销管理',
                    'icon': '💰',
                    'value': f'{pending_expenses}',
                    'subvalue': f'待审批 · 本月 {this_month_expenses} 笔',
                    'extra': f'已批准 ¥{this_month_amount:,.2f}',
                    'url': url,
                })
            except Exception:
                pass
        
    except Exception as e:
        import logging
        logger = logging.getLogger(__name__)
        logger.exception('获取统计数据失败: %s', str(e))
    
    context = _context(
        "行政管理",
        "🏢",
        "企业行政事务管理平台",
        summary_cards=[],
        request=request,
        use_administrative_nav=True
    )
    return render(request, "administrative_management/administrative_management_home.html", context)


@login_required
def supply_create(request):
    """新增办公用品"""
    permission_codes = get_user_permission_codes(request.user)
    if not _permission_granted('administrative_management.supply.create', permission_codes):
        messages.error(request, '您没有权限创建办公用品')
        return redirect('admin_pages:supplies_management')
    
    if request.method == 'POST':
        form = OfficeSupplyForm(request.POST)
        if form.is_valid():
            supply = form.save(commit=False)
            # 自动生成用品编码
            if not supply.code:
                current_year = timezone.now().year
                max_supply = OfficeSupply.objects.filter(
                    code__startswith=f'SUPPLY-{current_year}-'
                ).aggregate(max_num=Max('code'))['max_num']
                if max_supply:
                    try:
                        seq = int(max_supply.split('-')[-1]) + 1
                    except (ValueError, IndexError):
                        seq = 1
                else:
                    seq = 1
                supply.code = f'SUPPLY-{current_year}-{seq:04d}'
            supply.created_by = request.user
            supply.save()
            messages.success(request, f'办公用品 {supply.name} 创建成功！')
            return redirect('admin_pages:supply_detail', supply_id=supply.id)
    else:
        form = OfficeSupplyForm()
    
    context = _context(
        "新增办公用品",
        "➕",
        "创建新的办公用品",
        request=request,
        use_administrative_nav=True
    )
    context.update({
        'form': form,
        'is_create': True,
    })
    return render(request, "administrative_management/supply_form.html", context)


@login_required
def supply_update(request, supply_id):
    """编辑办公用品"""
    permission_codes = get_user_permission_codes(request.user)
    if not _permission_granted('administrative_management.supply.manage', permission_codes):
        messages.error(request, '您没有权限编辑办公用品')
        return redirect('admin_pages:supply_detail', supply_id=supply_id)
    
    supply = get_object_or_404(OfficeSupply, id=supply_id)
    
    if request.method == 'POST':
        form = OfficeSupplyForm(request.POST, instance=supply)
        if form.is_valid():
            form.save()
            messages.success(request, f'办公用品 {supply.name} 更新成功！')
            return redirect('admin_pages:supply_detail', supply_id=supply.id)
    else:
        form = OfficeSupplyForm(instance=supply)
    
    context = _context(
        f"编辑办公用品 - {supply.name}",
        "✏️",
        f"编辑办公用品 {supply.name}",
        request=request,
        use_administrative_nav=True
    )
    context.update({
        'form': form,
        'supply': supply,
        'is_create': False,
    })
    return render(request, "administrative_management/supply_form.html", context)


@login_required
def supply_category_list(request):
    """用品分类列表"""
    permission_codes = get_user_permission_codes(request.user)
    if not _permission_granted('administrative_management.supplies.view', permission_codes):
        messages.error(request, '您没有权限查看用品分类')
        return redirect('admin_pages:administrative_home')
    
    # 获取筛选参数
    search = request.GET.get('search', '').strip()
    is_active_filter = request.GET.get('is_active', '')
    
    try:
        # 基础查询
        categories = SupplyCategory.objects.select_related('parent').order_by('sort_order', 'name')
        
        # 应用筛选
        if search:
            categories = categories.filter(
                Q(name__icontains=search) |
                Q(code__icontains=search) |
                Q(description__icontains=search)
            )
        
        if is_active_filter == 'true':
            categories = categories.filter(is_active=True)
        elif is_active_filter == 'false':
            categories = categories.filter(is_active=False)
        
        # 分页处理
        per_page = 50
        page_number = request.GET.get('page', 1)
        try:
            paginator = Paginator(categories, per_page)
            page_obj = paginator.get_page(page_number)
        except Exception:
            page_obj = None
        
    except Exception as e:
        import logging
        logger = logging.getLogger(__name__)
        logger.exception('获取用品分类列表失败: %s', str(e))
        page_obj = None
    
    # 统计信息
    try:
        total_categories = SupplyCategory.objects.count()
        active_categories = SupplyCategory.objects.filter(is_active=True).count()
        root_categories = SupplyCategory.objects.filter(parent__isnull=True).count()
        
        summary_cards = []
    except Exception as e:
        import logging
        logger = logging.getLogger(__name__)
        logger.exception('获取统计信息失败: %s', str(e))
        summary_cards = []
    
    context = _context(
        "用品分类管理",
        "📁",
        "管理办公用品的分类结构。",
        summary_cards=summary_cards,
        request=request,
        use_administrative_nav=True
    )
    context.update({
        'page_obj': page_obj,
        'page': page_obj,  # 兼容模板中的变量名
        'search': search,
        'is_active': is_active_filter,
    })
    return render(request, "administrative_management/supply_category_list.html", context)


@login_required
def supply_category_create(request):
    """创建用品分类"""
    permission_codes = get_user_permission_codes(request.user)
    if not _permission_granted('administrative_management.supplies.manage', permission_codes):
        messages.error(request, '您没有权限创建用品分类')
        return redirect('admin_pages:supply_category_list')
    
    if request.method == 'POST':
        form = SupplyCategoryForm(request.POST)
        if form.is_valid():
            category = form.save()
            messages.success(request, f'用品分类 {category.name} 创建成功！')
            return redirect('admin_pages:supply_category_list')
    else:
        form = SupplyCategoryForm()
    
    context = _context(
        "创建用品分类",
        "➕",
        "创建新的用品分类",
        request=request,
        use_administrative_nav=True
    )
    context.update({
        'form': form,
        'is_create': True,
    })
    return render(request, "administrative_management/supply_category_form.html", context)


@login_required
def supply_category_update(request, category_id):
    """编辑用品分类"""
    permission_codes = get_user_permission_codes(request.user)
    if not _permission_granted('administrative_management.supplies.manage', permission_codes):
        messages.error(request, '您没有权限编辑用品分类')
        return redirect('admin_pages:supply_category_list')
    
    category = get_object_or_404(SupplyCategory, id=category_id)
    
    if request.method == 'POST':
        form = SupplyCategoryForm(request.POST, instance=category)
        if form.is_valid():
            form.save()
            messages.success(request, f'用品分类 {category.name} 更新成功！')
            return redirect('admin_pages:supply_category_list')
    else:
        form = SupplyCategoryForm(instance=category)
    
    context = _context(
        f"编辑用品分类 - {category.name}",
        "✏️",
        f"编辑用品分类 {category.name}",
        request=request,
        use_administrative_nav=True
    )
    context.update({
        'form': form,
        'category': category,
        'is_create': False,
    })
    return render(request, "administrative_management/supply_category_form.html", context)


@login_required
def supply_category_delete(request, category_id):
    """删除用品分类"""
    permission_codes = get_user_permission_codes(request.user)
    if not _permission_granted('administrative_management.supplies.manage', permission_codes):
        messages.error(request, '您没有权限删除用品分类')
        return redirect('admin_pages:supply_category_list')
    
    category = get_object_or_404(SupplyCategory, id=category_id)
    
    # 检查是否有子分类
    if category.children.exists():
        messages.error(request, f'分类 {category.name} 下有子分类，无法删除')
        return redirect('admin_pages:supply_category_list')
    
    # 检查是否有用品使用此分类
    if category.supplies.exists():
        messages.error(request, f'分类 {category.name} 下有用品，无法删除')
        return redirect('admin_pages:supply_category_list')
    
    if request.method == 'POST':
        category_name = category.name
        category.delete()
        messages.success(request, f'用品分类 {category_name} 已删除')
        return redirect('admin_pages:supply_category_list')
    
    context = _context(
        f"删除用品分类 - {category.name}",
        "❌",
        f"确认删除用品分类 {category.name}",
        request=request,
        use_administrative_nav=True
    )
    context.update({
        'category': category,
    })
    return render(request, "administrative_management/supply_category_delete.html", context)


@login_required
def supplies_management(request):
    """办公用品管理"""
    # 获取筛选参数
    search = request.GET.get('search', '')
    category = request.GET.get('category', '')
    is_active = request.GET.get('is_active', '')
    low_stock = request.GET.get('low_stock', '')
    
    # 获取用品列表
    try:
        supplies = OfficeSupply.objects.select_related('created_by').order_by('-created_time')
        
        # 应用筛选条件
        if search:
            supplies = supplies.filter(
                Q(code__icontains=search) |
                Q(name__icontains=search) |
                Q(brand__icontains=search) |
                Q(supplier__icontains=search)
            )
        if category:
            supplies = supplies.filter(category=category)
        if is_active == 'true':
            supplies = supplies.filter(is_active=True)
        elif is_active == 'false':
            supplies = supplies.filter(is_active=False)
        if low_stock == 'true':
            supplies = supplies.filter(current_stock__lte=F('min_stock'))
        
        # 分页
        page_size = request.GET.get('page_size', '10')
        try:
            per_page = int(page_size)
            if per_page not in [10, 20, 50]:
                per_page = 10
        except (ValueError, TypeError):
            per_page = 10
        paginator = Paginator(supplies, per_page)
        page_number = request.GET.get('page', 1)
        page_obj = paginator.get_page(page_number)
    except Exception as e:
        import logging
        logger = logging.getLogger(__name__)
        logger.exception('获取办公用品列表失败: %s', str(e))
        page_obj = None
    
    # 统计信息
    try:
        total_supplies = OfficeSupply.objects.count()
        active_supplies = OfficeSupply.objects.filter(is_active=True).count()
        low_stock_count = OfficeSupply.objects.filter(
            current_stock__lte=F('min_stock'),
            min_stock__gt=0
        ).count()
        total_value = sum(float(s.purchase_price) * s.current_stock for s in OfficeSupply.objects.filter(is_active=True))
        
        summary_cards = []
    except Exception as e:
        import logging
        logger = logging.getLogger(__name__)
        logger.exception('获取统计信息失败: %s', str(e))
        summary_cards = []
    
    context = _context(
        "办公用品管理",
        "📦",
        "管理办公用品的采购、领用和库存。",
        summary_cards=summary_cards,
        request=request,
        use_administrative_nav=True
    )
    context.update({
        'page_obj': page_obj,
        'search': search,
        'category': category,
        'is_active': is_active,
        'low_stock': low_stock,
        'category_choices': OfficeSupply.CATEGORY_CHOICES,
    })
    return render(request, "administrative_management/supplies_list.html", context)


@login_required
def supply_detail(request, supply_id):
    """办公用品详情"""
    supply = get_object_or_404(OfficeSupply, id=supply_id)
    
    # 获取采购记录
    try:
        purchases = SupplyPurchase.objects.filter(
            items__supply=supply
        ).distinct().order_by('-purchase_date')[:10]
    except Exception:
        purchases = []
    
    # 获取领用记录
    try:
        requests = SupplyRequest.objects.filter(
            items__supply=supply
        ).distinct().order_by('-request_date')[:10]
    except Exception:
        requests = []
    
    context = _context(
        f"办公用品详情 - {supply.name}",
        "📦",
        f"查看 {supply.code} 的详细信息和使用记录",
        request=request,
        use_administrative_nav=True
    )
    context.update({
        'supply': supply,
        'purchases': purchases,
        'requests': requests,
    })
    return render(request, "administrative_management/supply_detail.html", context)


# ==================== 采购管理视图 ====================

@login_required
def supply_purchase_list(request):
    """采购列表"""
    # 获取筛选参数
    search = request.GET.get('search', '')
    status = request.GET.get('status', '')
    
    # 获取采购列表
    try:
        purchases = SupplyPurchase.objects.select_related(
            'created_by', 'approver', 'received_by'
        ).prefetch_related('items').order_by('-purchase_date', '-created_time')
        
        # 应用筛选条件
        if search:
            purchases = purchases.filter(
                Q(purchase_number__icontains=search) |
                Q(supplier__icontains=search)
            )
        if status:
            purchases = purchases.filter(status=status)
        
        # 分页
        page_size = request.GET.get('page_size', '10')
        try:
            per_page = int(page_size)
            if per_page not in [10, 20, 50]:
                per_page = 10
        except (ValueError, TypeError):
            per_page = 10
        paginator = Paginator(purchases, per_page)
        page_number = request.GET.get('page', 1)
        page_obj = paginator.get_page(page_number)
    except Exception as e:
        import logging
        logger = logging.getLogger(__name__)
        logger.exception('获取采购列表失败: %s', str(e))
        page_obj = None
    
    # 统计信息
    try:
        total_purchases = SupplyPurchase.objects.count()
        pending_count = SupplyPurchase.objects.filter(status='pending_approval').count()
        approved_count = SupplyPurchase.objects.filter(status='approved').count()
        received_count = SupplyPurchase.objects.filter(status='received').count()
        
        summary_cards = []
    except Exception as e:
        import logging
        logger = logging.getLogger(__name__)
        logger.exception('获取统计信息失败: %s', str(e))
        summary_cards = []
    
    context = _context(
        "采购管理",
        "🛒",
        "管理办公用品的采购流程，包括采购申请、审批、入库等。",
        summary_cards=summary_cards,
        request=request,
        use_administrative_nav=True
    )
    context.update({
        'page_obj': page_obj,
        'search': search,
        'status': status,
        'status_choices': SupplyPurchase.STATUS_CHOICES,
    })
    return render(request, "administrative_management/supply_purchase_list.html", context)


@login_required
def supply_purchase_create(request):
    """创建采购单"""
    permission_codes = get_user_permission_codes(request.user)
    if not _permission_granted('administrative_management.supply.purchase', permission_codes):
        messages.error(request, '您没有权限创建采购单')
        return redirect('admin_pages:supply_purchase_list')
    
    # 使用内联表单集
    from django.forms import inlineformset_factory
    PurchaseItemFormSet = inlineformset_factory(
        SupplyPurchase, SupplyPurchaseItem,
        fields=('supply', 'quantity', 'unit_price', 'notes'),
        extra=3,
        can_delete=True,
        min_num=1,
        validate_min=True,
    )
    
    if request.method == 'POST':
        class PurchaseForm(forms.ModelForm):
            class Meta:
                model = SupplyPurchase
                fields = ['purchase_date', 'supplier', 'notes']
        
        form = PurchaseForm(request.POST)
        formset = PurchaseItemFormSet(request.POST)
        
        if form.is_valid() and formset.is_valid():
            purchase = form.save(commit=False)
            purchase.created_by = request.user
            purchase.save()
            
            # 保存明细并计算总金额
            items = formset.save(commit=False)
            total_amount = Decimal('0.00')
            
            for item in items:
                item.purchase = purchase
                item.save()
                total_amount += item.total_amount or Decimal('0.00')
            
            # 删除标记为删除的明细
            for obj in formset.deleted_objects:
                obj.delete()
            
            # 更新总金额
            purchase.total_amount = total_amount
            purchase.save()
            
            messages.success(request, f'采购单 {purchase.purchase_number} 创建成功！')
            return redirect('admin_pages:supply_purchase_detail', purchase_id=purchase.id)
    else:
        # 创建临时表单类
        class PurchaseForm(forms.ModelForm):
            class Meta:
                model = SupplyPurchase
                fields = ['purchase_date', 'supplier', 'notes']
                widgets = {
                    'purchase_date': forms.DateInput(attrs={'class': 'form-control', 'type': 'date'}),
                    'supplier': forms.TextInput(attrs={'class': 'form-control', 'placeholder': '供应商名称'}),
                    'notes': forms.Textarea(attrs={'class': 'form-control', 'rows': 3, 'placeholder': '备注'}),
                }
        
        form = PurchaseForm(initial={'purchase_date': timezone.now().date()})
        formset = PurchaseItemFormSet()
    
    context = _context(
        "创建采购单",
        "➕",
        "创建新的采购单",
        request=request,
        use_administrative_nav=True
    )
    context.update({
        'form': form,
        'formset': formset,
        'is_create': True,
    })
    return render(request, "administrative_management/supply_purchase_form.html", context)


@login_required
def supply_purchase_detail(request, purchase_id):
    """采购单详情"""
    purchase = get_object_or_404(
        SupplyPurchase.objects.prefetch_related('items__supply'),
        id=purchase_id
    )
    
    items = purchase.items.all().select_related('supply')
    
    context = _context(
        f"采购单详情 - {purchase.purchase_number}",
        "🛒",
        f"查看采购单 {purchase.purchase_number} 的详细信息",
        request=request,
        use_administrative_nav=True
    )
    context.update({
        'purchase': purchase,
        'items': items,
    })
    return render(request, "administrative_management/supply_purchase_detail.html", context)


@login_required
def supply_purchase_update(request, purchase_id):
    """编辑采购单"""
    permission_codes = get_user_permission_codes(request.user)
    purchase = get_object_or_404(SupplyPurchase, id=purchase_id)
    
    # 检查权限：只能编辑自己创建的
    if not _permission_granted('administrative_management.supply.purchase_manage', permission_codes):
        if purchase.created_by != request.user:
            messages.error(request, '您没有权限编辑此采购单')
            return redirect('admin_pages:supply_purchase_detail', purchase_id=purchase_id)
    
    # 只有草稿或待审批状态的采购单可以编辑
    if purchase.status not in ['draft', 'pending_approval']:
        messages.error(request, '只有草稿或待审批状态的采购单可以编辑')
        return redirect('admin_pages:supply_purchase_detail', purchase_id=purchase_id)
    
    from django.forms import inlineformset_factory
    PurchaseItemFormSet = inlineformset_factory(
        SupplyPurchase, SupplyPurchaseItem,
        fields=('supply', 'quantity', 'unit_price', 'notes'),
        extra=1,
        can_delete=True,
    )
    
    if request.method == 'POST':
        class PurchaseForm(forms.ModelForm):
            class Meta:
                model = SupplyPurchase
                fields = ['purchase_date', 'supplier', 'notes']
        
        form = PurchaseForm(request.POST, instance=purchase)
        formset = PurchaseItemFormSet(request.POST, instance=purchase)
        
        if form.is_valid() and formset.is_valid():
            purchase = form.save()
            
            # 保存明细并计算总金额
            items = formset.save(commit=False)
            total_amount = Decimal('0.00')
            
            for item in items:
                item.purchase = purchase
                item.save()
                total_amount += item.total_amount or Decimal('0.00')
            
            # 删除标记为删除的明细
            for obj in formset.deleted_objects:
                obj.delete()
            
            # 更新总金额
            purchase.total_amount = total_amount
            purchase.save()
            
            messages.success(request, f'采购单 {purchase.purchase_number} 更新成功！')
            return redirect('admin_pages:supply_purchase_detail', purchase_id=purchase.id)
    else:
        class PurchaseForm(forms.ModelForm):
            class Meta:
                model = SupplyPurchase
                fields = ['purchase_date', 'supplier', 'notes']
                widgets = {
                    'purchase_date': forms.DateInput(attrs={'class': 'form-control', 'type': 'date'}),
                    'supplier': forms.TextInput(attrs={'class': 'form-control'}),
                    'notes': forms.Textarea(attrs={'class': 'form-control', 'rows': 3}),
                }
        
        form = PurchaseForm(instance=purchase)
        formset = PurchaseItemFormSet(instance=purchase)
    
    context = _context(
        f"编辑采购单 - {purchase.purchase_number}",
        "✏️",
        f"编辑采购单 {purchase.purchase_number}",
        request=request,
        use_administrative_nav=True
    )
    context.update({
        'form': form,
        'formset': formset,
        'purchase': purchase,
        'is_create': False,
    })
    return render(request, "administrative_management/supply_purchase_form.html", context)


@login_required
def supply_purchase_approve(request, purchase_id):
    """审批采购单"""
    permission_codes = get_user_permission_codes(request.user)
    if not _permission_granted('administrative_management.supply.purchase_approve', permission_codes):
        messages.error(request, '您没有权限审批采购单')
        return redirect('admin_pages:supply_purchase_detail', purchase_id=purchase_id)
    
    purchase = get_object_or_404(SupplyPurchase, id=purchase_id)
    
    if purchase.status != 'pending_approval':
        messages.error(request, '只有待审批状态的采购单可以审批')
        return redirect('admin_pages:supply_purchase_detail', purchase_id=purchase_id)
    
    purchase.status = 'approved'
    purchase.approver = request.user
    purchase.approved_time = timezone.now()
    purchase.save()
    
    messages.success(request, f'采购单 {purchase.purchase_number} 已批准')
    return redirect('admin_pages:supply_purchase_detail', purchase_id=purchase_id)


@login_required
def supply_purchase_receive(request, purchase_id):
    """收货确认"""
    permission_codes = get_user_permission_codes(request.user)
    if not _permission_granted('administrative_management.supply.purchase_receive', permission_codes):
        messages.error(request, '您没有权限确认收货')
        return redirect('admin_pages:supply_purchase_detail', purchase_id=purchase_id)
    
    purchase = get_object_or_404(SupplyPurchase.objects.prefetch_related('items'), id=purchase_id)
    
    if purchase.status != 'approved':
        messages.error(request, '只有已批准状态的采购单可以确认收货')
        return redirect('admin_pages:supply_purchase_detail', purchase_id=purchase_id)
    
    if request.method == 'POST':
        # 更新收货数量并入库
        items = purchase.items.all()
        for item in items:
            received_qty = request.POST.get(f'received_quantity_{item.id}', '0')
            try:
                received_qty = int(received_qty)
                if received_qty > 0:
                    item.received_quantity = received_qty
                    item.save()
                    # 更新库存
                    supply = item.supply
                    supply.current_stock += received_qty
                    supply.save()
            except ValueError:
                pass
        
        purchase.status = 'received'
        purchase.received_by = request.user
        purchase.received_time = timezone.now()
        purchase.save()
        
        messages.success(request, f'采购单 {purchase.purchase_number} 收货确认成功，库存已更新')
        return redirect('admin_pages:supply_purchase_detail', purchase_id=purchase_id)
    
    # GET请求，显示收货表单
    context = _context(
        f"收货确认 - {purchase.purchase_number}",
        "📦",
        f"确认采购单 {purchase.purchase_number} 的收货",
        request=request,
        use_administrative_nav=True
    )
    context.update({
        'purchase': purchase,
    })
    return render(request, "administrative_management/supply_purchase_receive.html", context)


# ==================== 领用管理视图 ====================

@login_required
def supply_request_list(request):
    """领用申请列表"""
    # 获取筛选参数
    search = request.GET.get('search', '')
    status = request.GET.get('status', '')
    
    # 获取领用申请列表
    try:
        requests = SupplyRequest.objects.select_related(
            'applicant', 'approver', 'issued_by'
        ).prefetch_related('items').order_by('-request_date', '-created_time')
        
        # 如果是普通用户，只显示自己申请的
        permission_codes = get_user_permission_codes(request.user)
        if not _permission_granted('administrative_management.supply.request_view_all', permission_codes):
            requests = requests.filter(applicant=request.user)
        
        # 应用筛选条件
        if search:
            requests = requests.filter(
                Q(request_number__icontains=search) |
                Q(purpose__icontains=search)
            )
        if status:
            requests = requests.filter(status=status)
        
        # 分页
        page_size = request.GET.get('page_size', '10')
        try:
            per_page = int(page_size)
            if per_page not in [10, 20, 50]:
                per_page = 10
        except (ValueError, TypeError):
            per_page = 10
        paginator = Paginator(requests, per_page)
        page_number = request.GET.get('page', 1)
        page_obj = paginator.get_page(page_number)
    except Exception as e:
        import logging
        logger = logging.getLogger(__name__)
        logger.exception('获取领用申请列表失败: %s', str(e))
        page_obj = None
    
    # 统计信息
    try:
        total_requests = SupplyRequest.objects.count()
        pending_count = SupplyRequest.objects.filter(status='pending_approval').count()
        approved_count = SupplyRequest.objects.filter(status='approved').count()
        issued_count = SupplyRequest.objects.filter(status='issued').count()
        
        summary_cards = []
    except Exception as e:
        import logging
        logger = logging.getLogger(__name__)
        logger.exception('获取统计信息失败: %s', str(e))
        summary_cards = []
    
    context = _context(
        "领用管理",
        "📋",
        "管理办公用品的领用流程，包括领用申请、审批、出库等。",
        summary_cards=summary_cards,
        request=request,
        use_administrative_nav=True
    )
    context.update({
        'page_obj': page_obj,
        'search': search,
        'status': status,
        'status_choices': SupplyRequest.STATUS_CHOICES,
    })
    return render(request, "administrative_management/supply_request_list.html", context)


@login_required
def supply_request_create(request):
    """创建领用申请"""
    permission_codes = get_user_permission_codes(request.user)
    if not _permission_granted('administrative_management.supply.request', permission_codes):
        messages.error(request, '您没有权限创建领用申请')
        return redirect('admin_pages:supply_request_list')
    
    # 使用内联表单集
    from django.forms import inlineformset_factory
    RequestItemFormSet = inlineformset_factory(
        SupplyRequest, SupplyRequestItem,
        fields=('supply', 'requested_quantity', 'notes'),
        extra=3,
        can_delete=True,
        min_num=1,
        validate_min=True,
    )
    
    if request.method == 'POST':
        class RequestForm(forms.ModelForm):
            class Meta:
                model = SupplyRequest
                fields = ['request_date', 'purpose', 'notes']
                widgets = {
                    'request_date': forms.DateInput(attrs={'class': 'form-control', 'type': 'date'}),
                    'purpose': forms.Textarea(attrs={'class': 'form-control', 'rows': 3, 'placeholder': '用途说明'}),
                    'notes': forms.Textarea(attrs={'class': 'form-control', 'rows': 2, 'placeholder': '备注'}),
                }
        
        form = RequestForm(request.POST)
        formset = RequestItemFormSet(request.POST)
        
        if form.is_valid() and formset.is_valid():
            request_obj = form.save(commit=False)
            request_obj.applicant = request.user
            request_obj.save()
            
            # 保存明细
            items = formset.save(commit=False)
            for item in items:
                item.request = request_obj
                item.save()
            
            # 删除标记为删除的明细
            for obj in formset.deleted_objects:
                obj.delete()
            
            messages.success(request, f'领用申请 {request_obj.request_number} 创建成功！')
            return redirect('admin_pages:supply_request_detail', request_id=request_obj.id)
    else:
        class RequestForm(forms.ModelForm):
            class Meta:
                model = SupplyRequest
                fields = ['request_date', 'purpose', 'notes']
                widgets = {
                    'request_date': forms.DateInput(attrs={'class': 'form-control', 'type': 'date'}),
                    'purpose': forms.Textarea(attrs={'class': 'form-control', 'rows': 3, 'placeholder': '用途说明'}),
                    'notes': forms.Textarea(attrs={'class': 'form-control', 'rows': 2, 'placeholder': '备注'}),
                }
        
        form = RequestForm(initial={'request_date': timezone.now().date()})
        formset = RequestItemFormSet()
    
    context = _context(
        "创建领用申请",
        "➕",
        "创建新的领用申请",
        request=request,
        use_administrative_nav=True
    )
    context.update({
        'form': form,
        'formset': formset,
        'is_create': True,
    })
    return render(request, "administrative_management/supply_request_form.html", context)


@login_required
def supply_request_detail(request, request_id):
    """领用申请详情"""
    request_obj = get_object_or_404(
        SupplyRequest.objects.prefetch_related('items__supply'),
        id=request_id
    )
    
    items = request_obj.items.all().select_related('supply')
    
    context = _context(
        f"领用申请详情 - {request_obj.request_number}",
        "📋",
        f"查看领用申请 {request_obj.request_number} 的详细信息",
        request=request,
        use_administrative_nav=True
    )
    context.update({
        'request_obj': request_obj,
        'items': items,
    })
    return render(request, "administrative_management/supply_request_detail.html", context)


@login_required
def supply_request_update(request, request_id):
    """编辑领用申请"""
    permission_codes = get_user_permission_codes(request.user)
    request_obj = get_object_or_404(SupplyRequest, id=request_id)
    
    # 检查权限：只能编辑自己创建的
    if not _permission_granted('administrative_management.supply.request_manage', permission_codes):
        if request_obj.applicant != request.user:
            messages.error(request, '您没有权限编辑此领用申请')
            return redirect('admin_pages:supply_request_detail', request_id=request_id)
    
    # 只有草稿或待审批状态的申请可以编辑
    if request_obj.status not in ['draft', 'pending_approval']:
        messages.error(request, '只有草稿或待审批状态的申请可以编辑')
        return redirect('admin_pages:supply_request_detail', request_id=request_id)
    
    from django.forms import inlineformset_factory
    RequestItemFormSet = inlineformset_factory(
        SupplyRequest, SupplyRequestItem,
        fields=('supply', 'requested_quantity', 'notes'),
        extra=1,
        can_delete=True,
    )
    
    if request.method == 'POST':
        class RequestForm(forms.ModelForm):
            class Meta:
                model = SupplyRequest
                fields = ['request_date', 'purpose', 'notes']
        
        form = RequestForm(request.POST, instance=request_obj)
        formset = RequestItemFormSet(request.POST, instance=request_obj)
        
        if form.is_valid() and formset.is_valid():
            request_obj = form.save()
            
            # 保存明细
            items = formset.save(commit=False)
            for item in items:
                item.request = request_obj
                item.save()
            
            # 删除标记为删除的明细
            for obj in formset.deleted_objects:
                obj.delete()
            
            messages.success(request, f'领用申请 {request_obj.request_number} 更新成功！')
            return redirect('admin_pages:supply_request_detail', request_id=request_obj.id)
    else:
        class RequestForm(forms.ModelForm):
            class Meta:
                model = SupplyRequest
                fields = ['request_date', 'purpose', 'notes']
                widgets = {
                    'request_date': forms.DateInput(attrs={'class': 'form-control', 'type': 'date'}),
                    'purpose': forms.Textarea(attrs={'class': 'form-control', 'rows': 3}),
                    'notes': forms.Textarea(attrs={'class': 'form-control', 'rows': 2}),
                }
        
        form = RequestForm(instance=request_obj)
        formset = RequestItemFormSet(instance=request_obj)
    
    context = _context(
        f"编辑领用申请 - {request_obj.request_number}",
        "✏️",
        f"编辑领用申请 {request_obj.request_number}",
        request=request,
        use_administrative_nav=True
    )
    context.update({
        'form': form,
        'formset': formset,
        'request_obj': request_obj,
        'is_create': False,
    })
    return render(request, "administrative_management/supply_request_form.html", context)


@login_required
def supply_request_approve(request, request_id):
    """审批领用申请"""
    permission_codes = get_user_permission_codes(request.user)
    if not _permission_granted('administrative_management.supply.request_approve', permission_codes):
        messages.error(request, '您没有权限审批领用申请')
        return redirect('admin_pages:supply_request_detail', request_id=request_id)
    
    request_obj = get_object_or_404(SupplyRequest.objects.prefetch_related('items'), id=request_id)
    
    if request_obj.status != 'pending_approval':
        messages.error(request, '只有待审批状态的申请可以审批')
        return redirect('admin_pages:supply_request_detail', request_id=request_id)
    
    # 检查库存是否充足
    items = request_obj.items.all()
    insufficient_items = []
    for item in items:
        if item.supply.current_stock < item.requested_quantity:
            insufficient_items.append(f"{item.supply.name}（库存：{item.supply.current_stock}，申请：{item.requested_quantity}）")
    
    if insufficient_items:
        messages.error(request, f'库存不足：{", ".join(insufficient_items)}')
        return redirect('admin_pages:supply_request_detail', request_id=request_id)
    
    request_obj.status = 'approved'
    request_obj.approver = request.user
    request_obj.approved_time = timezone.now()
    request_obj.save()
    
    messages.success(request, f'领用申请 {request_obj.request_number} 已批准')
    return redirect('admin_pages:supply_request_detail', request_id=request_id)


@login_required
def supply_request_issue(request, request_id):
    """发放确认"""
    permission_codes = get_user_permission_codes(request.user)
    if not _permission_granted('administrative_management.supply.request_issue', permission_codes):
        messages.error(request, '您没有权限确认发放')
        return redirect('admin_pages:supply_request_detail', request_id=request_id)
    
    request_obj = get_object_or_404(SupplyRequest.objects.prefetch_related('items'), id=request_id)
    
    if request_obj.status != 'approved':
        messages.error(request, '只有已批准状态的申请可以确认发放')
        return redirect('admin_pages:supply_request_detail', request_id=request_id)
    
    if request.method == 'POST':
        # 更新发放数量并出库
        items = request_obj.items.all()
        for item in items:
            issued_qty = request.POST.get(f'issued_quantity_{item.id}', '0')
            try:
                issued_qty = int(issued_qty)
                if issued_qty > 0:
                    item.issued_quantity = issued_qty
                    item.save()
                    # 更新库存
                    supply = item.supply
                    supply.current_stock -= issued_qty
                    if supply.current_stock < 0:
                        supply.current_stock = 0
                    supply.save()
            except ValueError:
                pass
        
        request_obj.status = 'issued'
        request_obj.issued_by = request.user
        request_obj.issued_time = timezone.now()
        request_obj.save()
        
        messages.success(request, f'领用申请 {request_obj.request_number} 发放确认成功，库存已更新')
        return redirect('admin_pages:supply_request_detail', request_id=request_id)
    
    # GET请求，显示发放表单
    context = _context(
        f"发放确认 - {request_obj.request_number}",
        "📤",
        f"确认领用申请 {request_obj.request_number} 的发放",
        request=request,
        use_administrative_nav=True
    )
    context.update({
        'request_obj': request_obj,
    })
    return render(request, "administrative_management/supply_request_issue.html", context)

def meeting_room_create(request):
    """新增会议室"""
    permission_codes = get_user_permission_codes(request.user)
    if not _permission_granted('administrative_management.meeting_room.create', permission_codes):
        messages.error(request, '您没有权限创建会议室')
        return redirect('admin_pages:meeting_room_management')
    
    if request.method == 'POST':
        form = MeetingRoomForm(request.POST)
        if form.is_valid():
            room = form.save(commit=False)
            # 自动生成会议室编号
            if not room.code:
                max_room = MeetingRoom.objects.filter(
                    code__startswith='ROOM-'
                ).aggregate(max_code=Max('code'))['max_code']
                if max_room:
                    try:
                        seq = int(max_room.split('-')[-1]) + 1
                    except (ValueError, IndexError):
                        seq = 1
                else:
                    seq = 1
                room.code = f'ROOM-{seq:04d}'
            room.save()
            messages.success(request, f'会议室 {room.name} 创建成功！')
            return redirect('admin_pages:meeting_room_detail', room_id=room.id)
    else:
        form = MeetingRoomForm()
    
    context = _context(
        "新增会议室",
        "➕",
        "创建新的会议室",
        request=request,
        use_administrative_nav=True
    )
    context.update({
        'form': form,
        'is_create': True,
    })
    return render(request, "administrative_management/meeting_room_form.html", context)


@login_required
def meeting_room_update(request, room_id):
    """编辑会议室"""
    permission_codes = get_user_permission_codes(request.user)
    if not _permission_granted('administrative_management.meeting_room.manage', permission_codes):
        messages.error(request, '您没有权限编辑会议室')
        return redirect('admin_pages:meeting_room_detail', room_id=room_id)
    
    room = get_object_or_404(MeetingRoom, id=room_id)
    
    if request.method == 'POST':
        form = MeetingRoomForm(request.POST, instance=room)
        if form.is_valid():
            form.save()
            messages.success(request, f'会议室 {room.name} 更新成功！')
            return redirect('admin_pages:meeting_room_detail', room_id=room.id)
    else:
        form = MeetingRoomForm(instance=room)
    
    context = _context(
        f"编辑会议室 - {room.name}",
        "✏️",
        f"编辑会议室 {room.name}",
        request=request,
        use_administrative_nav=True
    )
    context.update({
        'form': form,
        'room': room,
        'is_create': False,
    })
    return render(request, "administrative_management/meeting_room_form.html", context)


@login_required
def vehicle_create(request):
    """新增车辆"""
    permission_codes = get_user_permission_codes(request.user)
    if not _permission_granted('administrative_management.vehicle.create', permission_codes):
        messages.error(request, '您没有权限创建车辆')
        return redirect('admin_pages:vehicle_management')
    
    if request.method == 'POST':
        form = VehicleForm(request.POST)
        if form.is_valid():
            vehicle = form.save()
            messages.success(request, f'车辆 {vehicle.plate_number} 创建成功！')
            return redirect('admin_pages:vehicle_detail', vehicle_id=vehicle.id)
    else:
        form = VehicleForm()
    
    context = _context(
        "新增车辆",
        "➕",
        "创建新的车辆",
        request=request,
        use_administrative_nav=True
    )
    context.update({
        'form': form,
        'is_create': True,
    })
    return render(request, "administrative_management/vehicle_form.html", context)


@login_required
def vehicle_update(request, vehicle_id):
    """编辑车辆"""
    permission_codes = get_user_permission_codes(request.user)
    if not _permission_granted('administrative_management.vehicle.manage', permission_codes):
        messages.error(request, '您没有权限编辑车辆')
        return redirect('admin_pages:vehicle_detail', vehicle_id=vehicle_id)
    
    vehicle = get_object_or_404(Vehicle, id=vehicle_id)
    
    if request.method == 'POST':
        form = VehicleForm(request.POST, instance=vehicle)
        if form.is_valid():
            form.save()
            messages.success(request, f'车辆 {vehicle.plate_number} 更新成功！')
            return redirect('admin_pages:vehicle_detail', vehicle_id=vehicle.id)
    else:
        form = VehicleForm(instance=vehicle)
    
    context = _context(
        f"编辑车辆 - {vehicle.plate_number}",
        "✏️",
        f"编辑车辆 {vehicle.plate_number}",
        request=request,
        use_administrative_nav=True
    )
    context.update({
        'form': form,
        'vehicle': vehicle,
        'is_create': False,
    })
    return render(request, "administrative_management/vehicle_form.html", context)


@login_required
def reception_create(request):
    """新增接待记录"""
    permission_codes = get_user_permission_codes(request.user)
    if not _permission_granted('administrative_management.reception.create', permission_codes):
        messages.error(request, '您没有权限创建接待记录')
        return redirect('admin_pages:reception_management')
    
    if request.method == 'POST':
        form = ReceptionRecordForm(request.POST)
        if form.is_valid():
            reception = form.save(commit=False)
            reception.created_by = request.user
            reception.save()
            form.save_m2m()  # 保存 ManyToMany 字段
            messages.success(request, f'接待记录 {reception.record_number} 创建成功！')
            return redirect('admin_pages:reception_detail', reception_id=reception.id)
    else:
        form = ReceptionRecordForm(initial={
            'reception_date': timezone.now().date(),
            'reception_time': timezone.now().time(),
            'host': request.user
        })
    
    context = _context(
        "新增接待记录",
        "➕",
        "创建新的接待记录",
        request=request,
        use_administrative_nav=True
    )
    context.update({
        'form': form,
        'is_create': True,
    })
    return render(request, "administrative_management/reception_form.html", context)


@login_required
def reception_update(request, reception_id):
    """编辑接待记录"""
    permission_codes = get_user_permission_codes(request.user)
    if not _permission_granted('administrative_management.reception.manage', permission_codes):
        messages.error(request, '您没有权限编辑接待记录')
        return redirect('admin_pages:reception_detail', reception_id=reception_id)
    
    reception = get_object_or_404(ReceptionRecord, id=reception_id)
    
    if request.method == 'POST':
        form = ReceptionRecordForm(request.POST, instance=reception)
        if form.is_valid():
            form.save()
            form.save_m2m()  # 保存 ManyToMany 字段
            messages.success(request, f'接待记录 {reception.record_number} 更新成功！')
            return redirect('admin_pages:reception_detail', reception_id=reception.id)
    else:
        form = ReceptionRecordForm(instance=reception)
    
    context = _context(
        f"编辑接待记录 - {reception.record_number}",
        "✏️",
        f"编辑接待记录 {reception.record_number}",
        request=request,
        use_administrative_nav=True
    )
    context.update({
        'form': form,
        'reception': reception,
        'is_create': False,
    })
    return render(request, "administrative_management/reception_form.html", context)


@login_required
def announcement_create(request):
    """新增公告通知"""
    permission_codes = get_user_permission_codes(request.user)
    if not _permission_granted('administrative_management.announcement.create', permission_codes):
        messages.error(request, '您没有权限创建公告通知')
        return redirect('admin_pages:announcement_management')
    
    if request.method == 'POST':
        form = AnnouncementForm(request.POST, request.FILES)
        if form.is_valid():
            announcement = form.save(commit=False)
            announcement.publisher = request.user
            announcement.save()
            form.save_m2m()  # 保存 ManyToMany 字段
            messages.success(request, f'公告通知 {announcement.title} 创建成功！')
            return redirect('admin_pages:announcement_detail', announcement_id=announcement.id)
    else:
        form = AnnouncementForm(initial={
            'publish_date': timezone.now().date(),
            'publisher': request.user
        })
    
    context = _context(
        "新增公告通知",
        "➕",
        "创建新的公告通知",
        request=request,
        use_administrative_nav=True
    )
    context.update({
        'form': form,
        'is_create': True,
    })
    return render(request, "administrative_management/announcement_form.html", context)


@login_required
def announcement_update(request, announcement_id):
    """编辑公告通知"""
    permission_codes = get_user_permission_codes(request.user)
    if not _permission_granted('administrative_management.announcement.manage', permission_codes):
        messages.error(request, '您没有权限编辑公告通知')
        return redirect('admin_pages:announcement_detail', announcement_id=announcement_id)
    
    announcement = get_object_or_404(Announcement, id=announcement_id)
    
    if request.method == 'POST':
        form = AnnouncementForm(request.POST, request.FILES, instance=announcement)
        if form.is_valid():
            form.save()
            form.save_m2m()  # 保存 ManyToMany 字段
            messages.success(request, f'公告通知 {announcement.title} 更新成功！')
            return redirect('admin_pages:announcement_detail', announcement_id=announcement.id)
    else:
        form = AnnouncementForm(instance=announcement)
    
    context = _context(
        f"编辑公告通知 - {announcement.title}",
        "✏️",
        f"编辑公告通知 {announcement.title}",
        request=request,
        use_administrative_nav=True
    )
    context.update({
        'form': form,
        'announcement': announcement,
        'is_create': False,
    })
    return render(request, "administrative_management/announcement_form.html", context)


@login_required
def seal_create(request):
    """新增印章"""
    permission_codes = get_user_permission_codes(request.user)
    if not _permission_granted('administrative_management.seal.create', permission_codes):
        messages.error(request, '您没有权限创建印章')
        return redirect('admin_pages:seal_management')
    
    if request.method == 'POST':
        form = SealForm(request.POST)
        if form.is_valid():
            seal = form.save(commit=False)
            # 自动生成印章编号
            if not seal.seal_number:
                max_seal = Seal.objects.filter(
                    seal_number__startswith='SEAL-'
                ).aggregate(max_num=Max('seal_number'))['max_num']
                if max_seal:
                    try:
                        seq = int(max_seal.split('-')[-1]) + 1
                    except (ValueError, IndexError):
                        seq = 1
                else:
                    seq = 1
                seal.seal_number = f'SEAL-{seq:04d}'
            seal.save()
            messages.success(request, f'印章 {seal.seal_name} 创建成功！')
            return redirect('admin_pages:seal_detail', seal_id=seal.id)
    else:
        form = SealForm()
    
    context = _context(
        "新增印章",
        "➕",
        "创建新的印章",
        request=request,
        use_administrative_nav=True
    )
    context.update({
        'form': form,
        'is_create': True,
    })
    return render(request, "administrative_management/seal_form.html", context)


@login_required
def seal_update(request, seal_id):
    """编辑印章"""
    permission_codes = get_user_permission_codes(request.user)
    if not _permission_granted('administrative_management.seal.manage', permission_codes):
        messages.error(request, '您没有权限编辑印章')
        return redirect('admin_pages:seal_detail', seal_id=seal_id)
    
    seal = get_object_or_404(Seal, id=seal_id)
    
    if request.method == 'POST':
        form = SealForm(request.POST, instance=seal)
        if form.is_valid():
            form.save()
            messages.success(request, f'印章 {seal.seal_name} 更新成功！')
            return redirect('admin_pages:seal_detail', seal_id=seal.id)
    else:
        form = SealForm(instance=seal)
    
    context = _context(
        f"编辑印章 - {seal.seal_name}",
        "✏️",
        f"编辑印章 {seal.seal_name}",
        request=request,
        use_administrative_nav=True
    )
    context.update({
        'form': form,
        'seal': seal,
        'is_create': False,
    })
    return render(request, "administrative_management/seal_form.html", context)


@login_required
def seal_borrowing_create(request):
    """申请借用印章"""
    permission_codes = get_user_permission_codes(request.user)
    # 检查是否有申请借用权限，如果没有则检查查看权限（向后兼容）
    if not _permission_granted('administrative_management.seal.borrow', permission_codes) and \
       not _permission_granted('administrative_management.seal.view', permission_codes):
        messages.error(request, '您没有权限申请借用印章')
        return redirect('admin_pages:seal_management')
    
    if request.method == 'POST':
        form = SealBorrowingForm(request.POST, user=request.user)
        if form.is_valid():
            borrowing = form.save(commit=False)
            # 设置默认借用人为当前用户（如果未指定）
            if not borrowing.borrower:
                borrowing.borrower = request.user
            borrowing.save()
            
            # 启动审批流程
            try:
                from backend.apps.workflow_engine.models import WorkflowTemplate
                from backend.apps.workflow_engine.services import ApprovalEngine
                
                # 获取印章借用审批流程
                workflow = WorkflowTemplate.objects.filter(
                    code='seal_borrowing_approval',
                    status='active'
                ).first()
                
                if workflow:
                    # 启动审批流程
                    approval_instance = ApprovalEngine.start_approval(
                        workflow=workflow,
                        content_object=borrowing,
                        applicant=request.user,
                        comment=f'申请借用印章：{borrowing.seal.seal_name}，借用事由：{borrowing.borrowing_reason[:50]}'
                    )
                    messages.success(request, f'印章借用申请 {borrowing.borrowing_number} 提交成功！审批流程已启动，审批单号：{approval_instance.instance_number}')
                else:
                    # 如果没有配置审批流程，使用原有的审批逻辑
                    messages.success(request, f'印章借用申请 {borrowing.borrowing_number} 提交成功！')
            except Exception as e:
                logger.exception('启动审批流程失败: %s', str(e))
                # 审批流程启动失败不影响申请提交
                messages.warning(request, f'印章借用申请 {borrowing.borrowing_number} 提交成功，但审批流程启动失败：{str(e)}')
            
            return redirect('admin_pages:seal_management')
    else:
        form = SealBorrowingForm(initial={'borrower': request.user}, user=request.user)
    
    context = _context(
        "申请借用印章",
        "📝",
        "提交印章借用申请",
        request=request,
        use_administrative_nav=True
    )
    context.update({
        'form': form,
        'is_create': True,
    })
    return render(request, "administrative_management/seal_borrowing_form.html", context)


@login_required
def seal_borrowing_return(request, borrowing_id):
    """归还印章"""
    borrowing = get_object_or_404(SealBorrowing, id=borrowing_id)
    seal = borrowing.seal
    permission_codes = get_user_permission_codes(request.user)
    
    # 判断是借用人提交归还，还是保管员确认归还
    is_borrower = borrowing.borrower == request.user
    is_keeper = seal.keeper == request.user
    has_manage_permission = (
        _permission_granted('administrative_management.seal.manage', permission_codes) or
        _permission_granted('administrative_management.seal.view', permission_codes)
    )
    
    if request.method == 'POST':
        action = request.POST.get('action', 'submit_return')  # submit_return 或 confirm_return
        
        # 借用人提交归还申请
        if action == 'submit_return' and is_borrower:
            # 检查状态：只有借用中或已批准的状态可以提交归还
            if borrowing.status not in ['borrowed', 'approved']:
                messages.error(request, f'只有借用中或已批准状态的印章可以归还，当前状态：{borrowing.get_status_display()}')
                return redirect('admin_pages:seal_detail', seal_id=seal.id)
            
            actual_return_date = request.POST.get('actual_return_date')
            return_notes = request.POST.get('return_notes', '').strip()
            
            if not actual_return_date:
                messages.error(request, '请填写实际归还日期')
                return redirect('admin_pages:seal_borrowing_return', borrowing_id=borrowing_id)
            
            try:
                from datetime import datetime
                return_date = datetime.strptime(actual_return_date, '%Y-%m-%d').date()
                
                # 更新借用记录为待确认归还状态
                borrowing.actual_return_date = return_date
                borrowing.status = 'pending_return_confirmation'
                if return_notes:
                    borrowing.notes = (borrowing.notes + '\n归还备注：' + return_notes).strip()
                borrowing.save()
                
                messages.success(request, f'归还申请已提交，等待保管员 {seal.keeper.get_full_name|default:seal.keeper.username} 确认归还')
                return redirect('admin_pages:seal_detail', seal_id=seal.id)
                
            except ValueError:
                messages.error(request, '归还日期格式不正确')
                return redirect('admin_pages:seal_borrowing_return', borrowing_id=borrowing_id)
            except Exception as e:
                logger.exception('提交归还申请失败: %s', str(e))
                messages.error(request, f'提交归还申请失败：{str(e)}')
                return redirect('admin_pages:seal_detail', seal_id=seal.id)
        
        # 保管员确认归还
        elif action == 'confirm_return' and (is_keeper or has_manage_permission):
            # 检查状态：只有待确认归还状态可以确认
            if borrowing.status != 'pending_return_confirmation':
                messages.error(request, f'只有待确认归还状态的印章可以确认，当前状态：{borrowing.get_status_display()}')
                return redirect('admin_pages:seal_detail', seal_id=seal.id)
            
            try:
                # 更新借用记录为已归还
                borrowing.return_received_by = request.user
                borrowing.status = 'returned'
                borrowing.save()
                
                # 更新印章状态为可用
                seal.status = 'available'
                seal.save(update_fields=['status'])
                
                messages.success(request, f'印章 {seal.seal_name} 已成功确认归还！')
                return redirect('admin_pages:seal_detail', seal_id=seal.id)
                
            except Exception as e:
                logger.exception('确认归还失败: %s', str(e))
                messages.error(request, f'确认归还失败：{str(e)}')
                return redirect('admin_pages:seal_detail', seal_id=seal.id)
        else:
            messages.error(request, '您没有权限执行此操作')
            return redirect('admin_pages:seal_detail', seal_id=seal.id)
    
    # GET 请求，显示归还表单或确认页面
    is_pending_confirmation = borrowing.status == 'pending_return_confirmation'
    
    context = _context(
        "归还印章" if not is_pending_confirmation else "确认归还",
        "🔙",
        f"{'归还' if not is_pending_confirmation else '确认归还'}印章：{seal.seal_name}",
        request=request,
        use_administrative_nav=True
    )
    context.update({
        'borrowing': borrowing,
        'seal': seal,
        'default_return_date': timezone.now().date(),
        'is_borrower': is_borrower,
        'is_keeper': is_keeper,
        'has_manage_permission': has_manage_permission,
        'is_pending_confirmation': is_pending_confirmation,
    })
    return render(request, "administrative_management/seal_borrowing_return.html", context)


@login_required
def seal_borrowing_return_list(request):
    """归还印章列表（显示当前用户借用中的印章）"""
    permission_codes = get_user_permission_codes(request.user)
    if not _permission_granted('administrative_management.seal.view', permission_codes):
        messages.error(request, '您没有权限查看印章归还列表')
        return redirect('admin_pages:administrative_home')
    
    # 获取筛选参数
    search = request.GET.get('search', '').strip()
    
    # 获取当前用户借用中的印章记录
    # 如果有管理权限，可以查看所有借用中的记录；否则只查看自己的
    if _permission_granted('administrative_management.seal.manage', permission_codes):
        borrowings = SealBorrowing.objects.filter(
            status__in=['borrowed', 'approved']
        ).select_related('seal', 'borrower', 'approver')
    else:
        borrowings = SealBorrowing.objects.filter(
            borrower=request.user,
            status__in=['borrowed', 'approved']
        ).select_related('seal', 'borrower', 'approver')
    
    # 搜索功能
    if search:
        borrowings = borrowings.filter(
            Q(borrowing_number__icontains=search) |
            Q(seal__seal_name__icontains=search) |
            Q(seal__seal_number__icontains=search) |
            Q(borrower__username__icontains=search) |
            Q(borrower__first_name__icontains=search) |
            Q(borrower__last_name__icontains=search)
        )
    
    # 排序和分页
    borrowings = borrowings.order_by('-borrowing_date')
    paginator = Paginator(borrowings, 20)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)
    
    context = _context(
        "归还印章",
        "🔙",
        "查看并归还借用中的印章",
        request=request,
        use_administrative_nav=True
    )
    context.update({
        'page_obj': page_obj,
        'borrowings': page_obj,
        'search': search,
    })
    return render(request, "administrative_management/seal_borrowing_return_list.html", context)


@login_required
def seal_usage_create(request):
    """申请用印"""
    permission_codes = get_user_permission_codes(request.user)
    # 检查是否有用印权限，如果没有则检查查看权限（向后兼容）
    if not _permission_granted('administrative_management.seal.view', permission_codes):
        messages.error(request, '您没有权限申请用印')
        return redirect('admin_pages:seal_management')
    
    if request.method == 'POST':
        form = SealUsageForm(request.POST, request.FILES, user=request.user)
        if form.is_valid():
            usage = form.save(commit=True)  # commit=True会自动保存文件
            # 设置默认用印人为当前用户（如果未指定）
            if not usage.used_by:
                usage.used_by = request.user
                usage.save()
            # 如果提供了用印时间，从用印时间中提取日期设置到用印日期
            if usage.usage_time and not usage.usage_date:
                usage.usage_date = usage.usage_time.date()
                usage.save()
            
            # 启动审批流程
            try:
                from backend.apps.workflow_engine.models import WorkflowTemplate
                from backend.apps.workflow_engine.services import ApprovalEngine
                
                # 获取用印申请审批流程
                workflow = WorkflowTemplate.objects.filter(
                    code='seal_usage_approval',
                    status='active'
                ).first()
                
                if workflow:
                    # 启动审批流程
                    approval_instance = ApprovalEngine.start_approval(
                        workflow=workflow,
                        content_object=usage,
                        applicant=request.user,
                        comment=f'申请用印：{usage.seal.seal_name}，用印事由：{usage.usage_reason[:50]}'
                    )
                    
                    # 抄送行政主管
                    try:
                        from backend.apps.system_management.models import Role
                        from backend.apps.project_center.models import ProjectTeamNotification
                        from django.urls import reverse
                        
                        # 查找行政主管角色（admin_office）
                        admin_office_role = Role.objects.filter(code='admin_office', is_active=True).first()
                        if admin_office_role:
                            # 获取所有行政主管用户
                            admin_office_users = admin_office_role.users.filter(is_active=True)
                            
                            # 为每个行政主管发送通知
                            action_url = reverse('admin_pages:seal_usage_detail', args=[usage.id])
                            for admin_user in admin_office_users:
                                ProjectTeamNotification.objects.create(
                                    project=None,
                                    recipient=admin_user,
                                    operator=request.user,
                                    title=f'用印申请通知 - {usage.usage_number}',
                                    message=f'{request.user.get_full_name() or request.user.username} 提交了用印申请：{usage.seal.seal_name}，用印事由：{usage.usage_reason[:100]}',
                                    category='approval',
                                    action_url=action_url,
                                    is_read=False,
                                    context={
                                        'approval_instance_id': approval_instance.id,
                                        'approval_instance_number': approval_instance.instance_number,
                                        'seal_usage_id': usage.id,
                                        'seal_usage_number': usage.usage_number,
                                    }
                                )
                            logger.info(f'已抄送行政主管: {usage.usage_number}, 抄送人数: {admin_office_users.count()}')
                    except Exception as e:
                        logger.warning(f'抄送行政主管失败: {str(e)}')
                        # 抄送失败不影响主流程
                    
                    messages.success(request, f'用印申请 {usage.usage_number} 提交成功！审批流程已启动，审批单号：{approval_instance.instance_number}')
                else:
                    # 如果没有配置审批流程，使用原有的逻辑
                    messages.success(request, f'用印申请 {usage.usage_number} 提交成功！')
            except Exception as e:
                logger.exception('启动审批流程失败: %s', str(e))
                # 审批流程启动失败不影响申请提交
                messages.warning(request, f'用印申请 {usage.usage_number} 提交成功，但审批流程启动失败：{str(e)}')
            
            return redirect('admin_pages:seal_usage_list')
    else:
        now = timezone.now()
        form = SealUsageForm(user=request.user, initial={
            'used_by': request.user,
            'usage_time': now,
        })
    
    context = _context(
        "申请用印",
        "📝",
        "提交用印申请",
        request=request,
        use_administrative_nav=True
    )
    context.update({
        'form': form,
        'is_create': True,
    })
    return render(request, "administrative_management/seal_usage_form.html", context)


@login_required
def seal_usage_list(request):
    """用印记录列表"""
    permission_codes = get_user_permission_codes(request.user)
    if not _permission_granted('administrative_management.seal.view', permission_codes):
        messages.error(request, '您没有权限查看用印记录')
        return redirect('admin_pages:administrative_home')
    
    # 获取筛选参数
    search = request.GET.get('search', '').strip()
    usage_type = request.GET.get('usage_type', '')
    seal_id = request.GET.get('seal', '')
    
    # 获取用印记录
    # 如果有管理权限，可以查看所有记录；否则只查看自己的
    if _permission_granted('administrative_management.seal.manage', permission_codes):
        usages = SealUsage.objects.all().select_related('seal', 'used_by', 'witness', 'borrowing')
    else:
        usages = SealUsage.objects.filter(
            used_by=request.user
        ).select_related('seal', 'used_by', 'witness', 'borrowing')
    
    # 搜索功能
    if search:
        usages = usages.filter(
            Q(usage_number__icontains=search) |
            Q(seal__seal_name__icontains=search) |
            Q(seal__seal_number__icontains=search) |
            Q(document_name__icontains=search) |
            Q(usage_reason__icontains=search) |
            Q(used_by__username__icontains=search) |
            Q(used_by__first_name__icontains=search) |
            Q(used_by__last_name__icontains=search)
        )
    
    # 筛选
    if usage_type:
        usages = usages.filter(usage_type=usage_type)
    if seal_id:
        usages = usages.filter(seal_id=seal_id)
    
    # 排序和分页
    usages = usages.order_by('-usage_date', '-usage_time')
    paginator = Paginator(usages, 20)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)
    
    # 获取审批实例信息（用于显示审批状态）
    if page_obj:
        try:
            from backend.apps.workflow_engine.models import ApprovalInstance
            from django.contrib.contenttypes.models import ContentType
            
            content_type = ContentType.objects.get_for_model(SealUsage)
            usage_ids = [usage.id for usage in page_obj]
            
            approval_instances = ApprovalInstance.objects.filter(
                content_type=content_type,
                object_id__in=usage_ids,
                workflow__code='seal_usage_approval'
            ).select_related('workflow', 'current_node').order_by('-created_time')
            
            # 为每个用印申请获取最新的审批实例，并添加到usage对象上
            approval_instances_map = {}
            for instance in approval_instances:
                if instance.object_id not in approval_instances_map:
                    approval_instances_map[instance.object_id] = instance
            
            # 为每个usage对象添加approval_instance属性
            for usage in page_obj:
                usage.approval_instance = approval_instances_map.get(usage.id)
        except Exception as e:
            logger.exception('获取审批实例信息失败: %s', str(e))
            # 如果获取失败，为每个usage对象设置None
            for usage in page_obj:
                usage.approval_instance = None
    
    # 获取筛选选项
    seal_choices = Seal.objects.filter(is_active=True).order_by('seal_name')
    
    context = _context(
        "用印记录",
        "📋",
        "查看用印申请记录",
        request=request,
        use_administrative_nav=True
    )
    context.update({
        'page_obj': page_obj,
        'usages': page_obj,
        'search': search,
        'usage_type': usage_type,
        'seal_id': seal_id,
        'usage_type_choices': SealUsage.USAGE_TYPE_CHOICES,
        'seal_choices': seal_choices,
    })
    return render(request, "administrative_management/seal_usage_list.html", context)


@login_required
def seal_usage_detail(request, usage_id):
    """用印记录详情"""
    usage = get_object_or_404(SealUsage, id=usage_id)
    permission_codes = get_user_permission_codes(request.user)
    
    # 检查权限：用印人可以查看，或者有印章管理权限的人可以查看
    can_view = (
        usage.used_by == request.user or
        _permission_granted('administrative_management.seal.view', permission_codes) or
        _permission_granted('administrative_management.seal.manage', permission_codes)
    )
    
    if not can_view:
        messages.error(request, '您没有权限查看此用印记录')
        return redirect('admin_pages:seal_usage_list')
    
    # 获取审批流程相关信息
    approval_instance = None
    records = []
    can_approve = False
    
    try:
        from backend.apps.workflow_engine.models import ApprovalInstance, ApprovalRecord
        from django.contrib.contenttypes.models import ContentType
        
        content_type = ContentType.objects.get_for_model(usage)
        approval_instance = ApprovalInstance.objects.filter(
            content_type=content_type,
            object_id=usage.id,
            workflow__code='seal_usage_approval'
        ).select_related('workflow', 'applicant', 'current_node').order_by('-created_time').first()
        
        if approval_instance:
            # 获取审批记录
            records = ApprovalRecord.objects.filter(
                instance=approval_instance
            ).select_related('approver', 'node').order_by('created_time')
            
            # 处理过时记录（节点已由他人处理完成）
            # 获取每个节点的最终状态
            from collections import defaultdict
            node_final_status = defaultdict(str)
            for record in records:
                if record.result in ['approved', 'rejected']:
                    node_final_status[record.node_id] = record.result
            
            # 为每个记录添加 is_obsolete 属性
            for record in records:
                if record.result == 'pending' and node_final_status.get(record.node_id) in ['approved', 'rejected']:
                    record.is_obsolete = True
                else:
                    record.is_obsolete = False
            
            # 检查当前用户是否可以审批
            from backend.apps.workflow_engine.services import ApprovalEngine
            can_approve = ApprovalEngine.can_user_approve(approval_instance, request.user)
    except Exception as e:
        logger.exception('获取审批流程信息失败: %s', str(e))
    
    # 获取所有用户列表（用于转交）
    from django.contrib.auth import get_user_model
    User = get_user_model()
    all_users = User.objects.filter(is_active=True).order_by('username')[:100]
    
    context = _context(
        f"用印记录详情 - {usage.usage_number}",
        "📋",
        f"查看用印记录 {usage.usage_number} 的详细信息",
        request=request,
        use_administrative_nav=True
    )
    context.update({
        'object': usage,  # 用于 detail_base.html（基础模板会自动检测 usage_number）
        'usage': usage,
        'seal': usage.seal,
        'instance': approval_instance,  # 审批实例
        'records': records,  # 审批记录
        'can_approve': can_approve,  # 是否可以审批
        'all_users': all_users,  # 用于转交的用户列表
    })
    return render(request, "administrative_management/seal_usage_detail.html", context)


@login_required
def asset_create(request):
    """新增固定资产"""
    permission_codes = get_user_permission_codes(request.user)
    if not _permission_granted('administrative_management.asset.create', permission_codes):
        messages.error(request, '您没有权限创建固定资产')
        return redirect('admin_pages:asset_management')
    
    if request.method == 'POST':
        form = FixedAssetForm(request.POST)
        if form.is_valid():
            asset = form.save(commit=False)
            # 自动生成资产编号
            if not asset.asset_number:
                current_year = timezone.now().year
                max_asset = FixedAsset.objects.filter(
                    asset_number__startswith=f'ADM-ASSET-{current_year}-'
                ).aggregate(max_num=Max('asset_number'))['max_num']
                if max_asset:
                    try:
                        seq = int(max_asset.split('-')[-1]) + 1
                    except (ValueError, IndexError):
                        seq = 1
                else:
                    seq = 1
                asset.asset_number = f'ADM-ASSET-{current_year}-{seq:04d}'
            asset.save()
            messages.success(request, f'固定资产 {asset.asset_name} 创建成功！')
            return redirect('admin_pages:asset_detail', asset_id=asset.id)
    else:
        form = FixedAssetForm()
    
    context = _context(
        "新增固定资产",
        "➕",
        "创建新的固定资产",
        request=request,
        use_administrative_nav=True
    )
    context.update({
        'form': form,
        'is_create': True,
    })
    return render(request, "administrative_management/asset_form.html", context)


@login_required
def asset_update(request, asset_id):
    """编辑固定资产"""
    permission_codes = get_user_permission_codes(request.user)
    if not _permission_granted('administrative_management.asset.manage', permission_codes):
        messages.error(request, '您没有权限编辑固定资产')
        return redirect('admin_pages:asset_detail', asset_id=asset_id)
    
    asset = get_object_or_404(FixedAsset, id=asset_id)
    
    if request.method == 'POST':
        form = FixedAssetForm(request.POST, instance=asset)
        if form.is_valid():
            form.save()
            messages.success(request, f'固定资产 {asset.asset_name} 更新成功！')
            return redirect('admin_pages:asset_detail', asset_id=asset.id)
    else:
        form = FixedAssetForm(instance=asset)
    
    context = _context(
        f"编辑固定资产 - {asset.asset_name}",
        "✏️",
        f"编辑固定资产 {asset.asset_name}",
        request=request,
        use_administrative_nav=True
    )
    context.update({
        'form': form,
        'asset': asset,
        'is_create': False,
    })
    return render(request, "administrative_management/asset_form.html", context)


@login_required
def expense_create(request):
    """新增报销申请"""
    permission_codes = get_user_permission_codes(request.user)
    if not _permission_granted('administrative_management.expense.create', permission_codes):
        messages.error(request, '您没有权限创建报销申请')
        return redirect('admin_pages:expense_management')
    
    if request.method == 'POST':
        form = ExpenseReimbursementForm(request.POST)
        formset = ExpenseItemFormSet(request.POST, request.FILES)
        
        if form.is_valid() and formset.is_valid():
            expense = form.save(commit=False)
            expense.applicant = request.user
            # 自动生成报销单号（已在模型save方法中处理）
            expense.save()
            
            # 保存费用明细并计算合计
            items = formset.save(commit=False)
            total_amount = Decimal('0.00')
            
            for item in items:
                item.reimbursement = expense
                item.save()
                total_amount += item.amount or Decimal('0.00')
            
            # 删除标记为删除的明细
            for obj in formset.deleted_objects:
                obj.delete()
            
            # 更新合计
            expense.total_amount = total_amount
            expense.save()
            
            messages.success(request, f'报销申请 {expense.reimbursement_number} 创建成功！')
            return redirect('admin_pages:expense_detail', expense_id=expense.id)
        else:
            messages.error(request, '请检查表单中的错误。')
    else:
        form = ExpenseReimbursementForm(initial={
            'application_date': timezone.now().date(),
            'applicant': request.user
        })
        formset = ExpenseItemFormSet()
    
    context = _context(
        "新增报销申请",
        "➕",
        "创建新的报销申请",
        request=request,
        use_administrative_nav=True
    )
    context.update({
        'form': form,
        'formset': formset,
        'is_create': True,
    })
    return render(request, "administrative_management/expense_form.html", context)


@login_required
def expense_update(request, expense_id):
    """编辑报销申请"""
    permission_codes = get_user_permission_codes(request.user)
    if not _permission_granted('administrative_management.expense.manage', permission_codes):
        messages.error(request, '您没有权限编辑报销申请')
        return redirect('admin_pages:expense_detail', expense_id=expense_id)
    
    expense = get_object_or_404(ExpenseReimbursement.objects.prefetch_related('items'), id=expense_id)
    
    # 已支付或已批准的报销不能编辑
    if expense.status in ['paid', 'approved']:
        messages.error(request, '已支付或已批准的报销申请不能编辑')
        return redirect('admin_pages:expense_detail', expense_id=expense.id)
    
    if request.method == 'POST':
        form = ExpenseReimbursementForm(request.POST, instance=expense)
        formset = ExpenseItemFormSet(request.POST, request.FILES, instance=expense)
        
        if form.is_valid() and formset.is_valid():
            expense = form.save()
            
            # 保存费用明细并计算合计
            items = formset.save(commit=False)
            total_amount = Decimal('0.00')
            
            for item in items:
                item.reimbursement = expense
                item.save()
                total_amount += item.amount or Decimal('0.00')
            
            # 删除标记为删除的明细
            for obj in formset.deleted_objects:
                obj.delete()
            
            # 更新合计
            expense.total_amount = total_amount
            expense.save()
            
            messages.success(request, f'报销申请 {expense.reimbursement_number} 更新成功！')
            return redirect('admin_pages:expense_detail', expense_id=expense.id)
        else:
            messages.error(request, '请检查表单中的错误。')
    else:
        form = ExpenseReimbursementForm(instance=expense)
        formset = ExpenseItemFormSet(instance=expense)
    
    context = _context(
        f"编辑报销申请 - {expense.reimbursement_number}",
        "✏️",
        f"编辑报销申请 {expense.reimbursement_number}",
        request=request,
        use_administrative_nav=True
    )
    context.update({
        'form': form,
        'formset': formset,
        'expense': expense,
        'is_create': False,
    })
    return render(request, "administrative_management/expense_form.html", context)


def meeting_room_management(request):
    """会议室管理"""
    # 获取筛选参数
    search = request.GET.get('search', '')
    status = request.GET.get('status', '')
    is_active = request.GET.get('is_active', '')
    
    # 获取会议室列表
    try:
        rooms = MeetingRoom.objects.order_by('code')
        
        # 应用筛选条件
        if search:
            rooms = rooms.filter(
                Q(code__icontains=search) |
                Q(name__icontains=search) |
                Q(location__icontains=search)
            )
        if status:
            rooms = rooms.filter(status=status)
        if is_active == 'true':
            rooms = rooms.filter(is_active=True)
        elif is_active == 'false':
            rooms = rooms.filter(is_active=False)
        
        # 分页
        page_size = request.GET.get('page_size', '10')
        try:
            per_page = int(page_size)
            if per_page not in [10, 20, 50]:
                per_page = 10
        except (ValueError, TypeError):
            per_page = 10
        paginator = Paginator(rooms, per_page)
        page_number = request.GET.get('page', 1)
        page_obj = paginator.get_page(page_number)
    except Exception as e:
        import logging
        logger = logging.getLogger(__name__)
        logger.exception('获取会议室列表失败: %s', str(e))
        page_obj = None
    
    # 统计信息
    try:
        total_rooms = MeetingRoom.objects.count()
        available_rooms = MeetingRoom.objects.filter(status='available', is_active=True).count()
        active_rooms = MeetingRoom.objects.filter(is_active=True).count()
        # 获取今日预订数量
        from django.utils import timezone
        today = timezone.now().date()
        today_bookings = MeetingRoomBooking.objects.filter(
            booking_date=today,
            status__in=['pending', 'confirmed']
        ).count()
        
        summary_cards = []
    except Exception as e:
        import logging
        logger = logging.getLogger(__name__)
        logger.exception('获取统计信息失败: %s', str(e))
        summary_cards = []
    
    context = _context(
        "会议室管理",
        "🏢",
        "管理会议室预订和使用情况。",
        summary_cards=summary_cards,
        request=request,
        use_administrative_nav=True
    )
    context.update({
        'page_obj': page_obj,
        'search': search,
        'status': status,
        'is_active': is_active,
        'status_choices': MeetingRoom.STATUS_CHOICES,
    })
    return render(request, "administrative_management/meeting_room_list.html", context)


@login_required
def meeting_room_detail(request, room_id):
    """会议室详情"""
    room = get_object_or_404(MeetingRoom, id=room_id)
    
    # 获取今日预订
    from django.utils import timezone
    today = timezone.now().date()
    try:
        today_bookings = MeetingRoomBooking.objects.filter(
            room=room,
            booking_date=today,
            status__in=['pending', 'confirmed']
        ).order_by('start_time')
    except Exception:
        today_bookings = []
    
    # 获取最近预订记录
    try:
        recent_bookings = MeetingRoomBooking.objects.filter(
            room=room
        ).order_by('-booking_date', '-start_time')[:10]
    except Exception:
        recent_bookings = []
    
    context = _context(
        f"会议室详情 - {room.name}",
        "🏢",
        f"查看 {room.code} 的详细信息和预订记录",
        request=request,
        use_administrative_nav=True
    )
    context.update({
        'room': room,
        'today_bookings': today_bookings,
        'recent_bookings': recent_bookings,
        'today': today,
    })
    return render(request, "administrative_management/meeting_room_detail.html", context)


# ==================== 会议室预订管理视图 ====================

@login_required
def meeting_room_booking_list(request):
    """会议室预订列表"""
    # 获取筛选参数
    search = request.GET.get('search', '')
    status = request.GET.get('status', '')
    room_id = request.GET.get('room_id', '')
    booking_date = request.GET.get('booking_date', '')
    
    # 获取预订列表
    try:
        bookings = MeetingRoomBooking.objects.select_related(
            'room', 'booker', 'cancelled_by'
        ).prefetch_related('attendees').order_by('-booking_date', '-start_time')
        
        # 应用筛选条件
        if search:
            bookings = bookings.filter(
                Q(booking_number__icontains=search) |
                Q(meeting_topic__icontains=search)
            )
        if status:
            bookings = bookings.filter(status=status)
        if room_id:
            bookings = bookings.filter(room_id=room_id)
        if booking_date:
            bookings = bookings.filter(booking_date=booking_date)
        
        # 权限检查：普通用户只能看到自己的预订
        permission_codes = get_user_permission_codes(request.user)
        if not _permission_granted('administrative_management.meeting_room.manage', permission_codes):
            bookings = bookings.filter(booker=request.user)
        
        # 分页
        page_size = request.GET.get('page_size', '10')
        try:
            per_page = int(page_size)
            if per_page not in [10, 20, 50]:
                per_page = 10
        except (ValueError, TypeError):
            per_page = 10
        paginator = Paginator(bookings, per_page)
        page_number = request.GET.get('page', 1)
        page_obj = paginator.get_page(page_number)
    except Exception as e:
        import logging
        logger = logging.getLogger(__name__)
        logger.exception('获取会议室预订列表失败: %s', str(e))
        page_obj = None
    
    # 统计信息
    try:
        permission_codes = get_user_permission_codes(request.user)
        if _permission_granted('administrative_management.meeting_room.manage', permission_codes):
            total_bookings = MeetingRoomBooking.objects.count()
            pending_count = MeetingRoomBooking.objects.filter(status='pending').count()
            confirmed_count = MeetingRoomBooking.objects.filter(status='confirmed').count()
            today = timezone.now().date()
            today_bookings = MeetingRoomBooking.objects.filter(booking_date=today, status__in=['pending', 'confirmed']).count()
        else:
            total_bookings = MeetingRoomBooking.objects.filter(booker=request.user).count()
            pending_count = MeetingRoomBooking.objects.filter(booker=request.user, status='pending').count()
            confirmed_count = MeetingRoomBooking.objects.filter(booker=request.user, status='confirmed').count()
            today = timezone.now().date()
            today_bookings = MeetingRoomBooking.objects.filter(booker=request.user, booking_date=today, status__in=['pending', 'confirmed']).count()
        
        summary_cards = []
    except Exception as e:
        import logging
        logger = logging.getLogger(__name__)
        logger.exception('获取统计信息失败: %s', str(e))
        summary_cards = []
    
    context = _context(
        "会议室预订管理",
        "📅",
        "管理会议室预订和确认。",
        summary_cards=summary_cards,
        request=request,
        use_administrative_nav=True
    )
    context.update({
        'page_obj': page_obj,
        'search': search,
        'status': status,
        'room_id': room_id,
        'booking_date': booking_date,
        'status_choices': MeetingRoomBooking.STATUS_CHOICES,
    })
    return render(request, "administrative_management/meeting_room_booking_list.html", context)


@login_required
def meeting_room_booking_create(request):
    """创建会议室预订"""
    permission_codes = get_user_permission_codes(request.user)
    if not _permission_granted('administrative_management.meeting_room.booking', permission_codes):
        messages.error(request, '您没有权限创建会议室预订')
        return redirect('admin_pages:meeting_room_booking_list')
    
    if request.method == 'POST':
        form = MeetingRoomBookingForm(request.POST)
        if form.is_valid():
            booking = form.save(commit=False)
            booking.booker = request.user
            booking.save()
            form.save_m2m()  # 保存 ManyToMany 字段
            
            messages.success(request, f'会议室预订 {booking.booking_number} 创建成功！')
            return redirect('admin_pages:meeting_room_booking_detail', booking_id=booking.id)
    else:
        form = MeetingRoomBookingForm(initial={
            'booking_date': timezone.now().date()
        })
    
    context = _context(
        "创建会议室预订",
        "➕",
        "创建新的会议室预订",
        request=request,
        use_administrative_nav=True
    )
    context.update({
        'form': form,
        'is_create': True,
    })
    return render(request, "administrative_management/meeting_room_booking_form.html", context)


@login_required
def meeting_room_booking_detail(request, booking_id):
    """会议室预订详情"""
    booking = get_object_or_404(MeetingRoomBooking, id=booking_id)
    
    # 权限检查：普通用户只能查看自己的预订
    permission_codes = get_user_permission_codes(request.user)
    if not _permission_granted('administrative_management.meeting_room.manage', permission_codes):
        if booking.booker != request.user:
            messages.error(request, '您没有权限查看此会议室预订')
            return redirect('admin_pages:meeting_room_booking_list')
    
    context = _context(
        f"会议室预订详情 - {booking.booking_number}",
        "📅",
        f"查看会议室预订的详细信息",
        request=request,
        use_administrative_nav=True
    )
    context.update({
        'booking': booking,
        'can_confirm': _permission_granted('administrative_management.meeting_room.manage', permission_codes) and booking.status == 'pending',
        'can_cancel': booking.booker == request.user and booking.status in ['pending', 'confirmed'],
        'can_edit': booking.booker == request.user and booking.status == 'pending',
    })
    return render(request, "administrative_management/meeting_room_booking_detail.html", context)


@login_required
def meeting_room_booking_update(request, booking_id):
    """编辑会议室预订"""
    booking = get_object_or_404(MeetingRoomBooking, id=booking_id)
    
    # 权限检查：只能编辑自己的待确认预订
    if booking.booker != request.user:
        messages.error(request, '您没有权限编辑此会议室预订')
        return redirect('admin_pages:meeting_room_booking_detail', booking_id=booking_id)
    
    if booking.status != 'pending':
        messages.error(request, '只能编辑待确认状态的会议室预订')
        return redirect('admin_pages:meeting_room_booking_detail', booking_id=booking_id)
    
    if request.method == 'POST':
        form = MeetingRoomBookingForm(request.POST, instance=booking)
        if form.is_valid():
            form.save()
            form.save_m2m()  # 保存 ManyToMany 字段
            
            messages.success(request, f'会议室预订 {booking.booking_number} 更新成功！')
            return redirect('admin_pages:meeting_room_booking_detail', booking_id=booking.id)
    else:
        form = MeetingRoomBookingForm(instance=booking)
    
    context = _context(
        f"编辑会议室预订 - {booking.booking_number}",
        "✏️",
        f"编辑会议室预订 {booking.booking_number}",
        request=request,
        use_administrative_nav=True
    )
    context.update({
        'form': form,
        'booking': booking,
        'is_create': False,
    })
    return render(request, "administrative_management/meeting_room_booking_form.html", context)


@login_required
def meeting_room_booking_confirm(request, booking_id):
    """确认会议室预订"""
    permission_codes = get_user_permission_codes(request.user)
    if not _permission_granted('administrative_management.meeting_room.manage', permission_codes):
        messages.error(request, '您没有权限确认会议室预订')
        return redirect('admin_pages:meeting_room_booking_detail', booking_id=booking_id)
    
    booking = get_object_or_404(MeetingRoomBooking, id=booking_id)
    
    if booking.status != 'pending':
        messages.error(request, '只能确认待确认状态的会议室预订')
        return redirect('admin_pages:meeting_room_booking_detail', booking_id=booking_id)
    
    booking.status = 'confirmed'
    booking.save()
    
    messages.success(request, f'会议室预订 {booking.booking_number} 已确认')
    return redirect('admin_pages:meeting_room_booking_detail', booking_id=booking_id)


@login_required
def meeting_room_booking_cancel(request, booking_id):
    """取消会议室预订"""
    booking = get_object_or_404(MeetingRoomBooking, id=booking_id)
    
    # 权限检查：预订人或管理员可以取消
    permission_codes = get_user_permission_codes(request.user)
    if booking.booker != request.user and not _permission_granted('administrative_management.meeting_room.manage', permission_codes):
        messages.error(request, '您没有权限取消此会议室预订')
        return redirect('admin_pages:meeting_room_booking_detail', booking_id=booking_id)
    
    if booking.status in ['cancelled', 'completed']:
        messages.error(request, '该预订已取消或已完成')
        return redirect('admin_pages:meeting_room_booking_detail', booking_id=booking_id)
    
    if request.method == 'POST':
        cancelled_reason = request.POST.get('cancelled_reason', '')
        booking.status = 'cancelled'
        booking.cancelled_by = request.user
        booking.cancelled_time = timezone.now()
        booking.cancelled_reason = cancelled_reason
        booking.save()
        
        messages.success(request, f'会议室预订 {booking.booking_number} 已取消')
        return redirect('admin_pages:meeting_room_booking_detail', booking_id=booking_id)
    
    context = _context(
        f"取消会议室预订 - {booking.booking_number}",
        "❌",
        f"取消会议室预订 {booking.booking_number}",
        request=request,
        use_administrative_nav=True
    )
    context.update({
        'booking': booking,
    })
    return render(request, "administrative_management/meeting_room_booking_cancel.html", context)


@login_required
def vehicle_management(request):
    """用车管理"""
    # 获取筛选参数
    search = request.GET.get('search', '')
    status = request.GET.get('status', '')
    vehicle_type = request.GET.get('vehicle_type', '')
    is_active = request.GET.get('is_active', '')
    
    # 获取车辆列表
    try:
        vehicles = Vehicle.objects.select_related('driver').order_by('plate_number')
        
        # 应用筛选条件
        if search:
            vehicles = vehicles.filter(
                Q(plate_number__icontains=search) |
                Q(brand__icontains=search)
            )
        if status:
            vehicles = vehicles.filter(status=status)
        if vehicle_type:
            vehicles = vehicles.filter(vehicle_type=vehicle_type)
        if is_active == 'true':
            vehicles = vehicles.filter(is_active=True)
        elif is_active == 'false':
            vehicles = vehicles.filter(is_active=False)
        
        # 分页
        page_size = request.GET.get('page_size', '10')
        try:
            per_page = int(page_size)
            if per_page not in [10, 20, 50]:
                per_page = 10
        except (ValueError, TypeError):
            per_page = 10
        paginator = Paginator(vehicles, per_page)
        page_number = request.GET.get('page', 1)
        page_obj = paginator.get_page(page_number)
    except Exception as e:
        import logging
        logger = logging.getLogger(__name__)
        logger.exception('获取车辆列表失败: %s', str(e))
        page_obj = None
    
    # 统计信息
    try:
        total_vehicles = Vehicle.objects.count()
        available_vehicles = Vehicle.objects.filter(status='available', is_active=True).count()
        active_vehicles = Vehicle.objects.filter(is_active=True).count()
        # 获取今日用车申请数量
        from django.utils import timezone
        today = timezone.now().date()
        today_bookings = VehicleBooking.objects.filter(
            booking_date=today,
            status__in=['approved', 'in_use']
        ).count()
        
        summary_cards = []
    except Exception as e:
        import logging
        logger = logging.getLogger(__name__)
        logger.exception('获取统计信息失败: %s', str(e))
        summary_cards = []
    
    context = _context(
        "用车管理",
        "🚗",
        "管理车辆使用和费用。",
        summary_cards=summary_cards,
        request=request,
        use_administrative_nav=True
    )
    context.update({
        'page_obj': page_obj,
        'search': search,
        'status': status,
        'vehicle_type': vehicle_type,
        'is_active': is_active,
        'status_choices': Vehicle.STATUS_CHOICES,
        'vehicle_type_choices': Vehicle.VEHICLE_TYPE_CHOICES,
    })
    return render(request, "administrative_management/vehicle_list.html", context)


@login_required
def vehicle_detail(request, vehicle_id):
    """车辆详情"""
    vehicle = get_object_or_404(Vehicle, id=vehicle_id)
    
    # 获取今日用车申请
    from django.utils import timezone
    today = timezone.now().date()
    try:
        today_bookings = VehicleBooking.objects.filter(
            vehicle=vehicle,
            booking_date=today,
            status__in=['approved', 'in_use']
        ).order_by('start_time')
    except Exception:
        today_bookings = []
    
    # 获取最近用车记录
    try:
        recent_bookings = VehicleBooking.objects.filter(
            vehicle=vehicle
        ).select_related('applicant', 'driver', 'approver').order_by('-booking_date', '-start_time')[:10]
    except Exception:
        recent_bookings = []
    
    context = _context(
        f"车辆详情 - {vehicle.plate_number}",
        "🚗",
        f"查看 {vehicle.brand} 的详细信息和用车记录",
        request=request,
        use_administrative_nav=True
    )
    context.update({
        'vehicle': vehicle,
        'today_bookings': today_bookings,
        'recent_bookings': recent_bookings,
        'today': today,
    })
    return render(request, "administrative_management/vehicle_detail.html", context)


# ==================== 用车申请管理视图 ====================

@login_required
def vehicle_booking_list(request):
    """用车申请列表"""
    # 获取筛选参数
    search = request.GET.get('search', '')
    status = request.GET.get('status', '')
    vehicle_id = request.GET.get('vehicle_id', '')
    applicant_id = request.GET.get('applicant_id', '')
    
    # 获取用车申请列表
    try:
        bookings = VehicleBooking.objects.select_related(
            'vehicle', 'applicant', 'driver', 'approver'
        ).order_by('-booking_date', '-start_time')
        
        # 应用筛选条件
        if search:
            bookings = bookings.filter(
                Q(booking_number__icontains=search) |
                Q(destination__icontains=search) |
                Q(purpose__icontains=search)
            )
        if status:
            bookings = bookings.filter(status=status)
        if vehicle_id:
            bookings = bookings.filter(vehicle_id=vehicle_id)
        if applicant_id:
            bookings = bookings.filter(applicant_id=applicant_id)
        
        # 权限检查：普通用户只能看到自己的申请
        permission_codes = get_user_permission_codes(request.user)
        if not _permission_granted('administrative_management.vehicle.manage', permission_codes):
            bookings = bookings.filter(applicant=request.user)
        
        # 分页
        page_size = request.GET.get('page_size', '10')
        try:
            per_page = int(page_size)
            if per_page not in [10, 20, 50]:
                per_page = 10
        except (ValueError, TypeError):
            per_page = 10
        paginator = Paginator(bookings, per_page)
        page_number = request.GET.get('page', 1)
        page_obj = paginator.get_page(page_number)
    except Exception as e:
        import logging
        logger = logging.getLogger(__name__)
        logger.exception('获取用车申请列表失败: %s', str(e))
        page_obj = None
    
    # 统计信息
    try:
        permission_codes = get_user_permission_codes(request.user)
        if _permission_granted('administrative_management.vehicle.manage', permission_codes):
            total_bookings = VehicleBooking.objects.count()
            pending_count = VehicleBooking.objects.filter(status='pending_approval').count()
            approved_count = VehicleBooking.objects.filter(status='approved').count()
            in_use_count = VehicleBooking.objects.filter(status='in_use').count()
        else:
            total_bookings = VehicleBooking.objects.filter(applicant=request.user).count()
            pending_count = VehicleBooking.objects.filter(applicant=request.user, status='pending_approval').count()
            approved_count = VehicleBooking.objects.filter(applicant=request.user, status='approved').count()
            in_use_count = VehicleBooking.objects.filter(applicant=request.user, status='in_use').count()
        
        summary_cards = []
    except Exception as e:
        import logging
        logger = logging.getLogger(__name__)
        logger.exception('获取统计信息失败: %s', str(e))
        summary_cards = []
    
    context = _context(
        "用车申请管理",
        "🚗",
        "管理用车申请、审批和调度。",
        summary_cards=summary_cards,
        request=request,
        use_administrative_nav=True
    )
    context.update({
        'page_obj': page_obj,
        'search': search,
        'status': status,
        'vehicle_id': vehicle_id,
        'applicant_id': applicant_id,
        'status_choices': VehicleBooking.STATUS_CHOICES,
    })
    return render(request, "administrative_management/vehicle_booking_list.html", context)


@login_required
def vehicle_booking_create(request):
    """创建用车申请"""
    permission_codes = get_user_permission_codes(request.user)
    if not _permission_granted('administrative_management.vehicle.booking', permission_codes):
        messages.error(request, '您没有权限创建用车申请')
        return redirect('admin_pages:vehicle_booking_list')
    
    if request.method == 'POST':
        form = VehicleBookingForm(request.POST)
        if form.is_valid():
            booking = form.save(commit=False)
            booking.applicant = request.user
            booking.booking_date = timezone.now().date()
            booking.save()
            
            messages.success(request, f'用车申请 {booking.booking_number} 创建成功！')
            return redirect('admin_pages:vehicle_booking_detail', booking_id=booking.id)
    else:
        form = VehicleBookingForm()
    
    context = _context(
        "创建用车申请",
        "➕",
        "创建新的用车申请",
        request=request,
        use_administrative_nav=True
    )
    context.update({
        'form': form,
        'is_create': True,
    })
    return render(request, "administrative_management/vehicle_booking_form.html", context)


@login_required
def vehicle_booking_detail(request, booking_id):
    """用车申请详情"""
    booking = get_object_or_404(VehicleBooking, id=booking_id)
    
    # 权限检查：普通用户只能查看自己的申请
    permission_codes = get_user_permission_codes(request.user)
    if not _permission_granted('administrative_management.vehicle.manage', permission_codes):
        if booking.applicant != request.user:
            messages.error(request, '您没有权限查看此用车申请')
            return redirect('admin_pages:vehicle_booking_list')
    
    context = _context(
        f"用车申请详情 - {booking.booking_number}",
        "🚗",
        f"查看用车申请的详细信息",
        request=request,
        use_administrative_nav=True
    )
    context.update({
        'booking': booking,
        'can_approve': _permission_granted('administrative_management.vehicle.approve', permission_codes),
        'can_dispatch': _permission_granted('administrative_management.vehicle.dispatch', permission_codes) and booking.status == 'approved',
        'can_return': booking.status == 'in_use' and (booking.applicant == request.user or _permission_granted('administrative_management.vehicle.manage', permission_codes)),
        'can_edit': booking.applicant == request.user and booking.status == 'draft',
    })
    return render(request, "administrative_management/vehicle_booking_detail.html", context)


@login_required
def vehicle_booking_update(request, booking_id):
    """编辑用车申请"""
    booking = get_object_or_404(VehicleBooking, id=booking_id)
    
    # 权限检查：只能编辑自己的草稿申请
    if booking.applicant != request.user:
        messages.error(request, '您没有权限编辑此用车申请')
        return redirect('admin_pages:vehicle_booking_detail', booking_id=booking_id)
    
    if booking.status != 'draft':
        messages.error(request, '只能编辑草稿状态的用车申请')
        return redirect('admin_pages:vehicle_booking_detail', booking_id=booking_id)
    
    if request.method == 'POST':
        form = VehicleBookingForm(request.POST, instance=booking)
        if form.is_valid():
            form.save()
            messages.success(request, f'用车申请 {booking.booking_number} 更新成功！')
            return redirect('admin_pages:vehicle_booking_detail', booking_id=booking.id)
    else:
        form = VehicleBookingForm(instance=booking)
    
    context = _context(
        f"编辑用车申请 - {booking.booking_number}",
        "✏️",
        f"编辑用车申请 {booking.booking_number}",
        request=request,
        use_administrative_nav=True
    )
    context.update({
        'form': form,
        'booking': booking,
        'is_create': False,
    })
    return render(request, "administrative_management/vehicle_booking_form.html", context)


@login_required
def vehicle_booking_approve(request, booking_id):
    """审批用车申请"""
    permission_codes = get_user_permission_codes(request.user)
    if not _permission_granted('administrative_management.vehicle.approve', permission_codes):
        messages.error(request, '您没有权限审批用车申请')
        return redirect('admin_pages:vehicle_booking_detail', booking_id=booking_id)
    
    booking = get_object_or_404(VehicleBooking, id=booking_id)
    
    if booking.status != 'pending_approval':
        messages.error(request, '只能审批待审批状态的用车申请')
        return redirect('admin_pages:vehicle_booking_detail', booking_id=booking_id)
    
    if request.method == 'POST':
        approval_notes = request.POST.get('approval_notes', '')
        booking.status = 'approved'
        booking.approver = request.user
        booking.approved_time = timezone.now()
        booking.save()
        
        messages.success(request, f'用车申请 {booking.booking_number} 已批准')
        return redirect('admin_pages:vehicle_booking_detail', booking_id=booking_id)
    
    context = _context(
        f"审批用车申请 - {booking.booking_number}",
        "✅",
        f"审批用车申请 {booking.booking_number}",
        request=request,
        use_administrative_nav=True
    )
    context.update({
        'booking': booking,
    })
    return render(request, "administrative_management/vehicle_booking_approve.html", context)


@login_required
def vehicle_booking_reject(request, booking_id):
    """拒绝用车申请"""
    permission_codes = get_user_permission_codes(request.user)
    if not _permission_granted('administrative_management.vehicle.approve', permission_codes):
        messages.error(request, '您没有权限拒绝用车申请')
        return redirect('admin_pages:vehicle_booking_detail', booking_id=booking_id)
    
    booking = get_object_or_404(VehicleBooking, id=booking_id)
    
    if booking.status != 'pending_approval':
        messages.error(request, '只能拒绝待审批状态的用车申请')
        return redirect('admin_pages:vehicle_booking_detail', booking_id=booking_id)
    
    if request.method == 'POST':
        approval_notes = request.POST.get('approval_notes', '')
        if not approval_notes:
            messages.error(request, '请填写拒绝原因')
            return redirect('admin_pages:vehicle_booking_reject', booking_id=booking_id)
        
        booking.status = 'rejected'
        booking.approver = request.user
        booking.approved_time = timezone.now()
        booking.save()
        
        messages.success(request, f'用车申请 {booking.booking_number} 已拒绝')
        return redirect('admin_pages:vehicle_booking_detail', booking_id=booking_id)
    
    context = _context(
        f"拒绝用车申请 - {booking.booking_number}",
        "❌",
        f"拒绝用车申请 {booking.booking_number}",
        request=request,
        use_administrative_nav=True
    )
    context.update({
        'booking': booking,
    })
    return render(request, "administrative_management/vehicle_booking_reject.html", context)


@login_required
def vehicle_booking_dispatch(request, booking_id):
    """车辆调度"""
    permission_codes = get_user_permission_codes(request.user)
    if not _permission_granted('administrative_management.vehicle.dispatch', permission_codes):
        messages.error(request, '您没有权限进行车辆调度')
        return redirect('admin_pages:vehicle_booking_detail', booking_id=booking_id)
    
    booking = get_object_or_404(VehicleBooking, id=booking_id)
    
    if booking.status != 'approved':
        messages.error(request, '只能调度已批准状态的用车申请')
        return redirect('admin_pages:vehicle_booking_detail', booking_id=booking_id)
    
    if request.method == 'POST':
        vehicle_id = request.POST.get('vehicle')
        driver_id = request.POST.get('driver')
        mileage_before = request.POST.get('mileage_before')
        
        if vehicle_id:
            booking.vehicle_id = vehicle_id
        if driver_id:
            booking.driver_id = driver_id
        if mileage_before:
            try:
                booking.mileage_before = int(mileage_before)
            except ValueError:
                pass
        
        booking.status = 'in_use'
        booking.actual_start_time = timezone.now()
        booking.vehicle.status = 'in_use'
        booking.vehicle.save()
        booking.save()
        
        messages.success(request, f'用车申请 {booking.booking_number} 已调度，车辆已分配')
        return redirect('admin_pages:vehicle_booking_detail', booking_id=booking_id)
    
    # 获取可用车辆
    available_vehicles = Vehicle.objects.filter(
        is_active=True,
        status__in=['available', 'in_use']
    ).order_by('plate_number')
    
    # 获取可用驾驶员
    available_drivers = User.objects.filter(is_active=True).order_by('username')
    
    context = _context(
        f"车辆调度 - {booking.booking_number}",
        "🚗",
        f"为用车申请 {booking.booking_number} 分配车辆和驾驶员",
        request=request,
        use_administrative_nav=True
    )
    context.update({
        'booking': booking,
        'available_vehicles': available_vehicles,
        'available_drivers': available_drivers,
    })
    return render(request, "administrative_management/vehicle_booking_dispatch.html", context)


@login_required
def vehicle_booking_return(request, booking_id):
    """车辆归还"""
    booking = get_object_or_404(VehicleBooking, id=booking_id)
    
    # 权限检查：申请人或管理员可以归还
    permission_codes = get_user_permission_codes(request.user)
    if booking.applicant != request.user and not _permission_granted('administrative_management.vehicle.manage', permission_codes):
        messages.error(request, '您没有权限归还车辆')
        return redirect('admin_pages:vehicle_booking_detail', booking_id=booking_id)
    
    if booking.status != 'in_use':
        messages.error(request, '只能归还使用中状态的用车申请')
        return redirect('admin_pages:vehicle_booking_detail', booking_id=booking_id)
    
    if request.method == 'POST':
        mileage_after = request.POST.get('mileage_after')
        fuel_cost = request.POST.get('fuel_cost', '0')
        parking_fee = request.POST.get('parking_fee', '0')
        toll_fee = request.POST.get('toll_fee', '0')
        other_cost = request.POST.get('other_cost', '0')
        
        if mileage_after:
            try:
                booking.mileage_after = int(mileage_after)
            except ValueError:
                pass
        
        try:
            booking.fuel_cost = Decimal(fuel_cost)
            booking.parking_fee = Decimal(parking_fee)
            booking.toll_fee = Decimal(toll_fee)
            booking.other_cost = Decimal(other_cost)
        except (ValueError, InvalidOperation):
            pass
        
        booking.status = 'completed'
        booking.actual_end_time = timezone.now()
        booking.vehicle.status = 'available'
        booking.vehicle.current_mileage = booking.mileage_after or booking.vehicle.current_mileage
        booking.vehicle.save()
        booking.save()
        
        messages.success(request, f'用车申请 {booking.booking_number} 已归还，车辆已释放')
        return redirect('admin_pages:vehicle_booking_detail', booking_id=booking_id)
    
    context = _context(
        f"车辆归还 - {booking.booking_number}",
        "🔄",
        f"归还车辆并录入费用信息",
        request=request,
        use_administrative_nav=True
    )
    context.update({
        'booking': booking,
    })
    return render(request, "administrative_management/vehicle_booking_return.html", context)


@login_required
def reception_management(request):
    """接待管理"""
    # 获取筛选参数
    search = request.GET.get('search', '')
    reception_type = request.GET.get('reception_type', '')
    reception_level = request.GET.get('reception_level', '')
    host_id = request.GET.get('host_id', '')
    
    # 获取接待记录列表
    try:
        receptions = ReceptionRecord.objects.select_related('host', 'created_by').order_by('-reception_date', '-reception_time')
        
        # 应用筛选条件
        if search:
            receptions = receptions.filter(
                Q(visitor_name__icontains=search) |
                Q(visitor_company__icontains=search) |
                Q(meeting_topic__icontains=search) |
                Q(record_number__icontains=search)
            )
        if reception_type:
            receptions = receptions.filter(reception_type=reception_type)
        if reception_level:
            receptions = receptions.filter(reception_level=reception_level)
        if host_id:
            receptions = receptions.filter(host_id=host_id)
        
        # 分页
        page_size = request.GET.get('page_size', '10')
        try:
            per_page = int(page_size)
            if per_page not in [10, 20, 50]:
                per_page = 10
        except (ValueError, TypeError):
            per_page = 10
        paginator = Paginator(receptions, per_page)
        page_number = request.GET.get('page', 1)
        page_obj = paginator.get_page(page_number)
    except Exception as e:
        import logging
        logger = logging.getLogger(__name__)
        logger.exception('获取接待记录列表失败: %s', str(e))
        page_obj = None
    
    # 统计信息
    try:
        total_receptions = ReceptionRecord.objects.count()
        # 获取本月接待数量
        from django.utils import timezone
        from datetime import datetime
        today = timezone.now().date()
        this_month_start = today.replace(day=1)
        this_month_count = ReceptionRecord.objects.filter(
            reception_date__gte=this_month_start
        ).count()
        # 获取VIP接待数量
        vip_count = ReceptionRecord.objects.filter(reception_level='vip').count()
        # 获取本月接待费用总额
        this_month_expenses = ReceptionExpense.objects.filter(
            expense_date__gte=this_month_start
        ).aggregate(total=Sum('amount'))['total'] or Decimal('0')
        
        summary_cards = []
    except Exception as e:
        import logging
        logger = logging.getLogger(__name__)
        logger.exception('获取统计信息失败: %s', str(e))
        summary_cards = []
    
    context = _context(
        "接待管理",
        "🤝",
        "管理访客接待记录和费用。",
        summary_cards=summary_cards,
        request=request,
        use_administrative_nav=True
    )
    context.update({
        'page_obj': page_obj,
        'search': search,
        'reception_type': reception_type,
        'reception_level': reception_level,
        'host_id': host_id,
        'reception_type_choices': ReceptionRecord.RECEPTION_TYPE_CHOICES,
        'reception_level_choices': ReceptionRecord.RECEPTION_LEVEL_CHOICES,
    })
    return render(request, "administrative_management/reception_list.html", context)


@login_required
def reception_detail(request, reception_id):
    """接待记录详情"""
    reception = get_object_or_404(ReceptionRecord, id=reception_id)
    
    # 获取接待费用
    try:
        expenses = ReceptionExpense.objects.filter(reception=reception).order_by('-expense_date')
        total_expense = expenses.aggregate(total=Sum('amount'))['total'] or Decimal('0')
    except Exception:
        expenses = []
        total_expense = Decimal('0')
    
    # 获取参与人员
    try:
        participants = reception.participants.all()
    except Exception:
        participants = []
    
    context = _context(
        f"接待记录详情 - {reception.record_number}",
        "🤝",
        f"查看 {reception.visitor_name} 的接待详细信息",
        request=request,
        use_administrative_nav=True
    )
    context.update({
        'reception': reception,
        'expenses': expenses,
        'total_expense': total_expense,
        'participants': participants,
    })
    return render(request, "administrative_management/reception_detail.html", context)


@login_required
def announcement_management(request):
    """公告通知管理"""
    # 获取筛选参数
    search = request.GET.get('search', '')
    category = request.GET.get('category', '')
    priority = request.GET.get('priority', '')
    is_active = request.GET.get('is_active', '')
    is_top = request.GET.get('is_top', '')
    
    # 获取公告列表
    try:
        # 管理页面：显示本人收到的所有通知（包括 Announcement 和 ProjectTeamNotification）
        user = request.user
        
        # 1. 获取 Announcement 类型的公告（根据发布范围过滤），不检查过期日期
        all_announcements = Announcement.objects.select_related('publisher').prefetch_related('target_departments', 'target_roles', 'target_users').all()
        
        # 获取用户的部门和角色信息
        user_departments = []
        user_roles = []
        if hasattr(user, 'department') and user.department:
            user_departments.append(user.department)
        if hasattr(user, 'roles'):
            user_roles = list(user.roles.all())
        
        # 根据发布范围过滤，只显示用户可见的公告（使用 Python 过滤，与通知中心逻辑一致）
        filtered_announcements = []
        for ann in all_announcements:
            if ann.target_scope == 'all':
                filtered_announcements.append(ann)
            elif ann.target_scope == 'department' and user_departments:
                if any(dept in ann.target_departments.all() for dept in user_departments):
                    filtered_announcements.append(ann)
            elif ann.target_scope == 'specific_roles' and user_roles:
                if any(role in ann.target_roles.all() for role in user_roles):
                    filtered_announcements.append(ann)
            elif ann.target_scope == 'specific_users':
                if user in ann.target_users.all():
                    filtered_announcements.append(ann)
        
        # 2. 获取 ProjectTeamNotification 类型的通知（直接发送给用户的）
        from backend.apps.production_management.models import ProjectTeamNotification
        team_notifications = ProjectTeamNotification.objects.filter(recipient=user).select_related('project', 'operator').all()
        
        # 创建一个统一的通知列表（包含所有类型的通知）
        all_notifications = []
        
        # 添加 Announcement 类型的通知
        for ann in filtered_announcements:
            all_notifications.append({
                'type': 'announcement',
                'id': ann.id,
                'title': ann.title,
                'content': ann.content,
                'category': ann.category,
                'priority': ann.priority,
                'publish_date': ann.publish_date,
                'publish_time': ann.publish_time,
                'publisher': ann.publisher,
                'is_top': ann.is_top,
                'is_active': ann.is_active,
                'view_count': ann.view_count,
                'target_scope': ann.target_scope,
                'obj': ann,  # 保存原始对象，用于后续操作
            })
        
        # 添加 ProjectTeamNotification 类型的通知
        for notif in team_notifications:
            all_notifications.append({
                'type': 'team_notification',
                'id': notif.id,
                'title': notif.title,
                'content': notif.message,
                'category': notif.category,
                'priority': 'normal',
                'publish_date': notif.created_time.date(),
                'publish_time': notif.created_time,
                'publisher': notif.operator,
                'is_top': False,
                'is_active': not notif.is_read,  # 未读视为活跃
                'view_count': 0,
                'target_scope': 'specific_users',
                'is_read': notif.is_read,
                'obj': notif,  # 保存原始对象，用于后续操作
            })
        
        # 应用筛选条件
        if search:
            all_notifications = [n for n in all_notifications if search.lower() in n['title'].lower() or search.lower() in n['content'].lower()]
        
        if category:
            all_notifications = [n for n in all_notifications if n.get('category') == category]
        
        if priority:
            all_notifications = [n for n in all_notifications if n.get('priority') == priority]
        
        # 处理状态筛选：默认显示所有状态的公告（包括失效的）
        if is_active == 'true':
            all_notifications = [n for n in all_notifications if n.get('is_active', True)]
        elif is_active == 'false':
            all_notifications = [n for n in all_notifications if not n.get('is_active', True)]
        
        if is_top == 'true':
            all_notifications = [n for n in all_notifications if n.get('is_top', False)]
        
        # 排序：按置顶、发布时间排序
        def get_sort_key(notif):
            is_top = notif.get('is_top', False)
            publish_time = notif.get('publish_time')
            if publish_time:
                if hasattr(publish_time, 'timestamp'):
                    time_key = publish_time.timestamp()
                else:
                    time_key = 0
            else:
                time_key = 0
            return (-is_top, -time_key)
        
        all_notifications.sort(key=get_sort_key)
        
        # 创建一个简单的包装类，让模板可以像访问对象属性一样访问数据
        class NotificationWrapper:
            def __init__(self, data):
                self._data = data
                self.type = data.get('type')
                self.obj = data.get('obj')
            
            def get_category_display(self):
                """获取分类的中文显示名称"""
                category = self._data.get('category', '')
                if not category:
                    return '-'
                
                # 如果是普通公告，使用 Announcement 的分类映射
                if self.type == 'announcement':
                    category_map = {
                        'system': '系统公告',
                        'notice': '通知',
                        'policy': '政策制度',
                        'culture': '企业文化',
                        'other': '其他',
                    }
                    return category_map.get(category, category)
                
                # 如果是团队通知，使用 ProjectTeamNotification 的分类映射
                elif self.type == 'team_notification':
                    category_map = {
                        'team_change': '团队变更',
                        'quality_alert': '质量提醒',
                        'approval': '审批通知',
                    }
                    return category_map.get(category, category)
                
                # 默认返回原值
                return category
            
            def get_target_scope_display(self):
                """获取发布范围的中文显示名称"""
                scope = self._data.get('target_scope', '')
                scope_map = {
                    'all': '全部',
                    'department': '指定部门',
                    'specific_roles': '指定角色',
                    'specific_users': '指定用户',
                }
                return scope_map.get(scope, scope or '-')
            
            def __getattr__(self, name):
                if name in self._data:
                    return self._data[name]
                # 对于 Announcement 对象，尝试从原始对象获取
                if self.obj and hasattr(self.obj, name):
                    return getattr(self.obj, name)
                # 提供默认值
                if name == 'is_popup':
                    return False
                return None
        
        # 将字典转换为包装对象
        wrapped_notifications = [NotificationWrapper(n) for n in all_notifications]
        
        # 分页
        page_size = request.GET.get('page_size', '10')
        try:
            per_page = int(page_size)
            if per_page not in [10, 20, 50]:
                per_page = 10
        except (ValueError, TypeError):
            per_page = 10
        
        from django.core.paginator import Paginator, EmptyPage, PageNotAnInteger
        paginator = Paginator(wrapped_notifications, per_page)
        page_number = request.GET.get('page', 1)
        try:
            page_obj = paginator.get_page(page_number)
        except (EmptyPage, PageNotAnInteger):
            page_obj = paginator.get_page(1)
    except Exception as e:
        import logging
        logger = logging.getLogger(__name__)
        logger.exception('获取公告列表失败: %s', str(e))
        page_obj = None
    
    # 统计信息
    try:
        total_announcements = Announcement.objects.count()
        active_announcements = Announcement.objects.filter(is_active=True).count()
        top_announcements = Announcement.objects.filter(is_top=True, is_active=True).count()
        # 获取本月发布的公告数量
        from django.utils import timezone
        today = timezone.now().date()
        this_month_start = today.replace(day=1)
        this_month_count = Announcement.objects.filter(
            publish_date__gte=this_month_start
        ).count()
        
        summary_cards = []
    except Exception as e:
        import logging
        logger = logging.getLogger(__name__)
        logger.exception('获取统计信息失败: %s', str(e))
        summary_cards = []
    
    context = _context(
        "公告通知管理",
        "📢",
        "管理公告通知的发布和阅读。",
        summary_cards=summary_cards,
        request=request,
        use_administrative_nav=True
    )
    context.update({
        'page_obj': page_obj,
        'search': search,
        'category': category,
        'priority': priority,
        'is_active': is_active,
        'is_top': is_top,
        'category_choices': Announcement.CATEGORY_CHOICES,
        'priority_choices': Announcement.PRIORITY_CHOICES,
    })
    return render(request, "administrative_management/announcement_list.html", context)


@login_required
def announcement_detail(request, announcement_id):
    """公告通知详情"""
    # 先尝试查询 Announcement 类型的公告
    try:
        announcement = Announcement.objects.get(id=announcement_id)
        notification_type = 'announcement'
        
        # 增加查看次数（仅首次查看）
        if request.user.is_authenticated:
            try:
                AnnouncementRead.objects.get_or_create(
                    announcement=announcement,
                    user=request.user
                )
                # 更新查看次数
                announcement.view_count = announcement.read_records.count()
                announcement.save(update_fields=['view_count'])
            except Exception:
                pass
        
        # 获取阅读记录（最近20条）
        try:
            read_records = announcement.read_records.select_related('user').order_by('-read_time')[:20]
        except Exception:
            read_records = []
        
        page_title = f"公告详情 - {announcement.title}"
        description = "查看公告通知的详细内容和阅读记录"
        
    except Announcement.DoesNotExist:
        # 如果找不到 Announcement，尝试查询 ProjectTeamNotification
        from backend.apps.production_management.models import ProjectTeamNotification
        
        try:
            team_notification = ProjectTeamNotification.objects.get(
                id=announcement_id,
                recipient=request.user  # 确保用户只能查看自己的通知
            )
            notification_type = 'team_notification'
            
            # 标记为已读（如果还未读）
            if not team_notification.is_read:
                team_notification.is_read = True
                from django.utils import timezone
                team_notification.read_time = timezone.now()
                team_notification.save(update_fields=['is_read', 'read_time'])
            
            # 创建一个类似 Announcement 的对象，用于模板兼容
            class TeamNotificationWrapper:
                def __init__(self, notif):
                    self.id = notif.id
                    self.title = notif.title
                    self.content = notif.message
                    self.category = notif.category
                    self.priority = 'normal'
                    self.target_scope = 'specific_users'
                    self.publish_date = notif.created_time.date()
                    self.publish_time = notif.created_time
                    self.publisher = notif.operator
                    self.is_top = False
                    self.is_popup = False
                    self.is_active = True
                    self.view_count = 0
                    self.expiry_date = None
                    self.attachment = None
                    self.created_time = notif.created_time
                    self.is_read = notif.is_read
                    self.action_url = notif.action_url
                    self._notif = notif  # 保留原始对象引用，以防需要访问其他属性
                
                def get_category_display(self):
                    category_map = {
                        'team_change': '团队变更',
                        'quality_alert': '质量提醒',
                        'approval': '审批通知',
                    }
                    return category_map.get(self.category, self.category)
                
                def get_target_scope_display(self):
                    return '指定用户'
            
            announcement = TeamNotificationWrapper(team_notification)
            read_records = []  # 团队通知没有阅读记录列表
            
            page_title = f"团队通知详情 - {announcement.title}"
            description = "查看团队通知的详细内容"
            
        except ProjectTeamNotification.DoesNotExist:
            from django.http import Http404
            raise Http404("No Announcement or TeamNotification matches the given query.")
    
    context = _context(
        page_title,
        "📢",
        description,
        request=request,
        use_administrative_nav=True
    )
    context.update({
        'announcement': announcement,
        'read_records': read_records,
        'notification_type': notification_type,
    })
    return render(request, "administrative_management/announcement_detail.html", context)


@login_required
def seal_management(request):
    """印章管理"""
    # 获取筛选参数
    search = request.GET.get('search', '')
    seal_type = request.GET.get('seal_type', '')
    status = request.GET.get('status', '')
    is_active = request.GET.get('is_active', '')
    
    # 获取印章列表
    try:
        seals = Seal.objects.select_related('keeper').order_by('seal_number')
        
        # 应用筛选条件
        if search:
            seals = seals.filter(
                Q(seal_number__icontains=search) |
                Q(seal_name__icontains=search) |
                Q(keeper__username__icontains=search)
            )
        if seal_type:
            seals = seals.filter(seal_type=seal_type)
        if status:
            seals = seals.filter(status=status)
        if is_active == 'true':
            seals = seals.filter(is_active=True)
        elif is_active == 'false':
            seals = seals.filter(is_active=False)
        
        # 分页
        page_size = request.GET.get('page_size', '10')
        try:
            per_page = int(page_size)
            if per_page not in [10, 20, 50]:
                per_page = 10
        except (ValueError, TypeError):
            per_page = 10
        paginator = Paginator(seals, per_page)
        page_number = request.GET.get('page', 1)
        page_obj = paginator.get_page(page_number)
    except Exception as e:
        import logging
        logger = logging.getLogger(__name__)
        logger.exception('获取印章列表失败: %s', str(e))
        page_obj = None
    
    # 统计信息
    try:
        total_seals = Seal.objects.count()
        available_seals = Seal.objects.filter(status='available', is_active=True).count()
        borrowed_seals = Seal.objects.filter(status='borrowed').count()
        active_seals = Seal.objects.filter(is_active=True).count()
        
        summary_cards = []
    except Exception as e:
        import logging
        logger = logging.getLogger(__name__)
        logger.exception('获取统计信息失败: %s', str(e))
        summary_cards = []
    
    context = _context(
        "印章管理",
        "🔐",
        "管理印章的借用和归还。",
        summary_cards=summary_cards,
        request=request,
        use_administrative_nav=True
    )
    context.update({
        'page_obj': page_obj,
        'search': search,
        'seal_type': seal_type,
        'status': status,
        'is_active': is_active,
        'seal_type_choices': Seal.SEAL_TYPE_CHOICES,
        'status_choices': Seal.STATUS_CHOICES,
    })
    return render(request, "administrative_management/seal_list.html", context)


@login_required
def seal_detail(request, seal_id):
    """印章详情"""
    seal = get_object_or_404(Seal, id=seal_id)
    
    # 获取借用记录（最近10条）
    try:
        borrowings = SealBorrowing.objects.filter(seal=seal).select_related(
            'borrower', 'approver', 'return_received_by'
        ).order_by('-borrowing_date')[:10]
    except Exception as e:
        logger.exception('获取印章借用记录失败: %s', str(e))
        borrowings = []
    
    # 获取当前借用中的记录（状态为 borrowed、approved 或 pending_return_confirmation）
    current_borrowing = None
    try:
        current_borrowing = SealBorrowing.objects.filter(
            seal=seal,
            status__in=['borrowed', 'approved', 'pending_return_confirmation']
        ).select_related('borrower', 'approver').order_by('-borrowing_date').first()
    except Exception as e:
        logger.exception('获取当前借用记录失败: %s', str(e))
    
    context = _context(
        f"印章详情 - {seal.seal_name}",
        "🔐",
        f"查看印章 {seal.seal_number} 的详细信息和借用记录",
        request=request,
        use_administrative_nav=True
    )
    context.update({
        'seal': seal,
        'borrowings': borrowings,
        'current_borrowing': current_borrowing,
        'user': request.user,  # 传递当前用户，用于判断权限
    })
    return render(request, "administrative_management/seal_detail.html", context)


@login_required
def asset_management(request):
    """固定资产管理"""
    # 获取筛选参数
    search = request.GET.get('search', '')
    category = request.GET.get('category', '')
    status = request.GET.get('status', '')
    department_id = request.GET.get('department_id', '')
    is_active = request.GET.get('is_active', '')
    
    # 获取资产列表
    try:
        assets = FixedAsset.objects.select_related('current_user', 'department').order_by('-created_time')
        
        # 应用筛选条件
        if search:
            assets = assets.filter(
                Q(asset_number__icontains=search) |
                Q(asset_name__icontains=search) |
                Q(brand__icontains=search) |
                Q(model__icontains=search)
            )
        if category:
            assets = assets.filter(category=category)
        if status:
            assets = assets.filter(status=status)
        if department_id:
            assets = assets.filter(department_id=department_id)
        if is_active == 'true':
            assets = assets.filter(is_active=True)
        elif is_active == 'false':
            assets = assets.filter(is_active=False)
        
        # 分页
        page_size = request.GET.get('page_size', '10')
        try:
            per_page = int(page_size)
            if per_page not in [10, 20, 50]:
                per_page = 10
        except (ValueError, TypeError):
            per_page = 10
        paginator = Paginator(assets, per_page)
        page_number = request.GET.get('page', 1)
        page_obj = paginator.get_page(page_number)
    except Exception as e:
        import logging
        logger = logging.getLogger(__name__)
        logger.exception('获取资产列表失败: %s', str(e))
        page_obj = None
    
    # 统计信息
    try:
        total_assets = FixedAsset.objects.count()
        in_use_assets = FixedAsset.objects.filter(status='in_use', is_active=True).count()
        active_assets = FixedAsset.objects.filter(is_active=True).count()
        # 计算资产总价值
        total_value = sum(float(a.purchase_price) for a in FixedAsset.objects.filter(is_active=True))
        
        summary_cards = []
    except Exception as e:
        import logging
        logger = logging.getLogger(__name__)
        logger.exception('获取统计信息失败: %s', str(e))
        summary_cards = []
    
    context = _context(
        "固定资产管理",
        "💼",
        "管理固定资产的信息、转移和维护。",
        summary_cards=summary_cards,
        request=request,
        use_administrative_nav=True
    )
    context.update({
        'page_obj': page_obj,
        'search': search,
        'category': category,
        'status': status,
        'department_id': department_id,
        'is_active': is_active,
        'category_choices': FixedAsset.CATEGORY_CHOICES,
        'status_choices': FixedAsset.STATUS_CHOICES,
    })
    return render(request, "administrative_management/asset_list.html", context)


@login_required
def asset_detail(request, asset_id):
    """固定资产详情"""
    asset = get_object_or_404(FixedAsset, id=asset_id)
    
    # 获取转移记录
    try:
        transfers = AssetTransfer.objects.filter(asset=asset).select_related(
            'from_user', 'to_user', 'approver', 'completed_by'
        ).order_by('-transfer_date')[:10]
    except Exception:
        transfers = []
    
    # 获取维护记录
    try:
        maintenances = AssetMaintenance.objects.filter(asset=asset).select_related(
            'performed_by'
        ).order_by('-maintenance_date')[:10]
    except Exception:
        maintenances = []
    
    # 检查是否可以创建转移和维护
    permission_codes = get_user_permission_codes(request.user)
    can_transfer = _permission_granted('administrative_management.asset.transfer', permission_codes)
    can_maintenance = _permission_granted('administrative_management.asset.maintenance', permission_codes)
    
    context = _context(
        f"资产详情 - {asset.asset_name}",
        "💼",
        f"查看 {asset.asset_number} 的详细信息和维护记录",
        request=request,
        use_administrative_nav=True
    )
    context.update({
        'asset': asset,
        'transfers': transfers,
        'maintenances': maintenances,
        'can_transfer': can_transfer,
        'can_maintenance': can_maintenance,
    })
    return render(request, "administrative_management/asset_detail.html", context)


# ==================== 资产转移视图 ====================

@login_required
def asset_transfer_list(request):
    """资产转移列表"""
    # 获取筛选参数
    search = request.GET.get('search', '')
    status = request.GET.get('status', '')
    
    # 获取转移列表
    try:
        transfers = AssetTransfer.objects.select_related(
            'asset', 'from_user', 'to_user', 'approver', 'completed_by'
        ).order_by('-transfer_date', '-created_time')
        
        # 应用筛选条件
        if search:
            transfers = transfers.filter(
                Q(transfer_number__icontains=search) |
                Q(asset__asset_name__icontains=search) |
                Q(transfer_reason__icontains=search)
            )
        if status:
            transfers = transfers.filter(status=status)
        
        # 分页
        page_size = request.GET.get('page_size', '10')
        try:
            per_page = int(page_size)
            if per_page not in [10, 20, 50]:
                per_page = 10
        except (ValueError, TypeError):
            per_page = 10
        paginator = Paginator(transfers, per_page)
        page_number = request.GET.get('page', 1)
        page_obj = paginator.get_page(page_number)
    except Exception as e:
        import logging
        logger = logging.getLogger(__name__)
        logger.exception('获取资产转移列表失败: %s', str(e))
        page_obj = None
    
    # 统计信息
    try:
        total_transfers = AssetTransfer.objects.count()
        pending_count = AssetTransfer.objects.filter(status='pending_approval').count()
        approved_count = AssetTransfer.objects.filter(status='approved').count()
        completed_count = AssetTransfer.objects.filter(status='completed').count()
        
        summary_cards = []
    except Exception as e:
        import logging
        logger = logging.getLogger(__name__)
        logger.exception('获取统计信息失败: %s', str(e))
        summary_cards = []
    
    context = _context(
        "资产转移管理",
        "🔄",
        "管理固定资产的转移流程，包括转移申请、审批、执行等。",
        summary_cards=summary_cards,
        request=request,
        use_administrative_nav=True
    )
    context.update({
        'page_obj': page_obj,
        'search': search,
        'status': status,
        'status_choices': AssetTransfer.STATUS_CHOICES,
    })
    return render(request, "administrative_management/asset_transfer_list.html", context)


@login_required
def asset_transfer_create(request, asset_id):
    """创建资产转移申请"""
    permission_codes = get_user_permission_codes(request.user)
    if not _permission_granted('administrative_management.asset.transfer', permission_codes):
        messages.error(request, '您没有权限创建资产转移申请')
        return redirect('admin_pages:asset_detail', asset_id=asset_id)
    
    asset = get_object_or_404(FixedAsset, id=asset_id)
    
    if request.method == 'POST':
        class TransferForm(forms.ModelForm):
            class Meta:
                model = AssetTransfer
                fields = ['to_user', 'from_location', 'to_location', 'transfer_date', 'transfer_reason', 'notes']
                widgets = {
                    'to_user': forms.Select(attrs={'class': 'form-select'}),
                    'from_location': forms.TextInput(attrs={'class': 'form-control', 'placeholder': '原位置'}),
                    'to_location': forms.TextInput(attrs={'class': 'form-control', 'placeholder': '新位置'}),
                    'transfer_date': forms.DateInput(attrs={'class': 'form-control', 'type': 'date'}),
                    'transfer_reason': forms.Textarea(attrs={'class': 'form-control', 'rows': 4, 'placeholder': '转移原因'}),
                    'notes': forms.Textarea(attrs={'class': 'form-control', 'rows': 3, 'placeholder': '备注'}),
                }
        
        form = TransferForm(request.POST)
        if form.is_valid():
            transfer = form.save(commit=False)
            transfer.asset = asset
            transfer.from_user = asset.current_user or request.user
            transfer.save()
            
            messages.success(request, f'资产转移申请 {transfer.transfer_number} 创建成功！')
            return redirect('admin_pages:asset_transfer_detail', transfer_id=transfer.id)
    else:
        class TransferForm(forms.ModelForm):
            class Meta:
                model = AssetTransfer
                fields = ['to_user', 'from_location', 'to_location', 'transfer_date', 'transfer_reason', 'notes']
                widgets = {
                    'to_user': forms.Select(attrs={'class': 'form-select'}),
                    'from_location': forms.TextInput(attrs={'class': 'form-control', 'placeholder': '原位置'}),
                    'to_location': forms.TextInput(attrs={'class': 'form-control', 'placeholder': '新位置'}),
                    'transfer_date': forms.DateInput(attrs={'class': 'form-control', 'type': 'date'}),
                    'transfer_reason': forms.Textarea(attrs={'class': 'form-control', 'rows': 4, 'placeholder': '转移原因'}),
                    'notes': forms.Textarea(attrs={'class': 'form-control', 'rows': 3, 'placeholder': '备注'}),
                }
        
        form = TransferForm(initial={
            'transfer_date': timezone.now().date(),
            'from_user': asset.current_user,
            'from_location': asset.current_location,
        })
        form.fields['to_user'].queryset = User.objects.filter(is_active=True).order_by('username')
    
    context = _context(
        f"创建资产转移 - {asset.asset_name}",
        "➕",
        f"为资产 {asset.asset_number} 创建转移申请",
        request=request,
        use_administrative_nav=True
    )
    context.update({
        'form': form,
        'asset': asset,
    })
    return render(request, "administrative_management/asset_transfer_form.html", context)


@login_required
def asset_transfer_detail(request, transfer_id):
    """资产转移详情"""
    transfer = get_object_or_404(
        AssetTransfer.objects.select_related('asset', 'from_user', 'to_user', 'approver', 'completed_by'),
        id=transfer_id
    )
    
    context = _context(
        f"资产转移详情 - {transfer.transfer_number}",
        "🔄",
        f"查看资产转移 {transfer.transfer_number} 的详细信息",
        request=request,
        use_administrative_nav=True
    )
    context.update({
        'transfer': transfer,
    })
    return render(request, "administrative_management/asset_transfer_detail.html", context)


@login_required
def asset_transfer_approve(request, transfer_id):
    """审批资产转移"""
    permission_codes = get_user_permission_codes(request.user)
    if not _permission_granted('administrative_management.asset.transfer_approve', permission_codes):
        messages.error(request, '您没有权限审批资产转移')
        return redirect('admin_pages:asset_transfer_detail', transfer_id=transfer_id)
    
    transfer = get_object_or_404(AssetTransfer, id=transfer_id)
    
    if transfer.status != 'pending_approval':
        messages.error(request, '只有待审批状态的转移申请可以审批')
        return redirect('admin_pages:asset_transfer_detail', transfer_id=transfer_id)
    
    transfer.status = 'approved'
    transfer.approver = request.user
    transfer.approved_time = timezone.now()
    transfer.save()
    
    messages.success(request, f'资产转移申请 {transfer.transfer_number} 已批准')
    return redirect('admin_pages:asset_transfer_detail', transfer_id=transfer_id)


@login_required
def asset_transfer_complete(request, transfer_id):
    """完成资产转移"""
    permission_codes = get_user_permission_codes(request.user)
    if not _permission_granted('administrative_management.asset.transfer_complete', permission_codes):
        messages.error(request, '您没有权限完成资产转移')
        return redirect('admin_pages:asset_transfer_detail', transfer_id=transfer_id)
    
    transfer = get_object_or_404(AssetTransfer, id=transfer_id)
    
    if transfer.status != 'approved':
        messages.error(request, '只有已批准状态的转移申请可以完成')
        return redirect('admin_pages:asset_transfer_detail', transfer_id=transfer_id)
    
    # 更新资产信息
    asset = transfer.asset
    asset.current_user = transfer.to_user
    asset.current_location = transfer.to_location
    asset.save()
    
    transfer.status = 'completed'
    transfer.completed_by = request.user
    transfer.completed_time = timezone.now()
    transfer.save()
    
    messages.success(request, f'资产转移 {transfer.transfer_number} 已完成，资产信息已更新')
    return redirect('admin_pages:asset_transfer_detail', transfer_id=transfer_id)


# ==================== 资产维护视图 ====================

@login_required
def asset_maintenance_create(request, asset_id):
    """创建资产维护记录"""
    permission_codes = get_user_permission_codes(request.user)
    if not _permission_granted('administrative_management.asset.maintenance', permission_codes):
        messages.error(request, '您没有权限创建资产维护记录')
        return redirect('admin_pages:asset_detail', asset_id=asset_id)
    
    asset = get_object_or_404(FixedAsset, id=asset_id)
    
    if request.method == 'POST':
        class MaintenanceForm(forms.ModelForm):
            class Meta:
                model = AssetMaintenance
                fields = ['maintenance_date', 'maintenance_type', 'service_provider', 'cost', 'description', 'next_maintenance_date', 'performed_by']
                widgets = {
                    'maintenance_date': forms.DateInput(attrs={'class': 'form-control', 'type': 'date'}),
                    'maintenance_type': forms.Select(attrs={'class': 'form-select'}),
                    'service_provider': forms.TextInput(attrs={'class': 'form-control', 'placeholder': '服务商'}),
                    'cost': forms.NumberInput(attrs={'class': 'form-control', 'step': '0.01', 'placeholder': '维护费用'}),
                    'description': forms.Textarea(attrs={'class': 'form-control', 'rows': 4, 'placeholder': '维护描述'}),
                    'next_maintenance_date': forms.DateInput(attrs={'class': 'form-control', 'type': 'date'}),
                    'performed_by': forms.Select(attrs={'class': 'form-select'}),
                }
        
        form = MaintenanceForm(request.POST)
        if form.is_valid():
            maintenance = form.save(commit=False)
            maintenance.asset = asset
            # 如果资产状态是维护中，可以更新
            if maintenance.maintenance_type == 'repair':
                asset.status = 'maintenance'
                asset.save()
            maintenance.save()
            
            messages.success(request, '资产维护记录创建成功！')
            return redirect('admin_pages:asset_detail', asset_id=asset.id)
    else:
        class MaintenanceForm(forms.ModelForm):
            class Meta:
                model = AssetMaintenance
                fields = ['maintenance_date', 'maintenance_type', 'service_provider', 'cost', 'description', 'next_maintenance_date', 'performed_by']
                widgets = {
                    'maintenance_date': forms.DateInput(attrs={'class': 'form-control', 'type': 'date'}),
                    'maintenance_type': forms.Select(attrs={'class': 'form-select'}),
                    'service_provider': forms.TextInput(attrs={'class': 'form-control', 'placeholder': '服务商'}),
                    'cost': forms.NumberInput(attrs={'class': 'form-control', 'step': '0.01', 'placeholder': '维护费用'}),
                    'description': forms.Textarea(attrs={'class': 'form-control', 'rows': 4, 'placeholder': '维护描述'}),
                    'next_maintenance_date': forms.DateInput(attrs={'class': 'form-control', 'type': 'date'}),
                    'performed_by': forms.Select(attrs={'class': 'form-select'}),
                }
        
        form = MaintenanceForm(initial={
            'maintenance_date': timezone.now().date(),
            'performed_by': request.user,
        })
        form.fields['performed_by'].queryset = User.objects.filter(is_active=True).order_by('username')
    
    context = _context(
        f"创建资产维护 - {asset.asset_name}",
        "🔧",
        f"为资产 {asset.asset_number} 创建维护记录",
        request=request,
        use_administrative_nav=True
    )
    context.update({
        'form': form,
        'asset': asset,
    })
    return render(request, "administrative_management/asset_maintenance_form.html", context)


@login_required
def asset_maintenance_detail(request, maintenance_id):
    """资产维护详情"""
    maintenance = get_object_or_404(
        AssetMaintenance.objects.select_related('asset', 'performed_by'),
        id=maintenance_id
    )
    
    context = _context(
        f"资产维护详情 - {maintenance.asset.asset_name}",
        "🔧",
        f"查看资产维护记录的详细信息",
        request=request,
        use_administrative_nav=True
    )
    context.update({
        'maintenance': maintenance,
    })
    return render(request, "administrative_management/asset_maintenance_detail.html", context)


@login_required
def asset_maintenance_update(request, maintenance_id):
    """编辑资产维护记录"""
    permission_codes = get_user_permission_codes(request.user)
    maintenance = get_object_or_404(AssetMaintenance, id=maintenance_id)
    
    # 检查权限：只有执行人可以编辑
    if not _permission_granted('administrative_management.asset.maintenance_manage', permission_codes):
        if maintenance.performed_by != request.user:
            messages.error(request, '您没有权限编辑此维护记录')
            return redirect('admin_pages:asset_maintenance_detail', maintenance_id=maintenance_id)
    
    if request.method == 'POST':
        class MaintenanceForm(forms.ModelForm):
            class Meta:
                model = AssetMaintenance
                fields = ['maintenance_date', 'maintenance_type', 'service_provider', 'cost', 'description', 'next_maintenance_date', 'performed_by']
        
        form = MaintenanceForm(request.POST, instance=maintenance)
        if form.is_valid():
            form.save()
            messages.success(request, '资产维护记录更新成功！')
            return redirect('admin_pages:asset_maintenance_detail', maintenance_id=maintenance.id)
    else:
        class MaintenanceForm(forms.ModelForm):
            class Meta:
                model = AssetMaintenance
                fields = ['maintenance_date', 'maintenance_type', 'service_provider', 'cost', 'description', 'next_maintenance_date', 'performed_by']
                widgets = {
                    'maintenance_date': forms.DateInput(attrs={'class': 'form-control', 'type': 'date'}),
                    'maintenance_type': forms.Select(attrs={'class': 'form-select'}),
                    'service_provider': forms.TextInput(attrs={'class': 'form-control'}),
                    'cost': forms.NumberInput(attrs={'class': 'form-control', 'step': '0.01'}),
                    'description': forms.Textarea(attrs={'class': 'form-control', 'rows': 4}),
                    'next_maintenance_date': forms.DateInput(attrs={'class': 'form-control', 'type': 'date'}),
                    'performed_by': forms.Select(attrs={'class': 'form-select'}),
                }
        
        form = MaintenanceForm(instance=maintenance)
        form.fields['performed_by'].queryset = User.objects.filter(is_active=True).order_by('username')
    
    context = _context(
        f"编辑资产维护 - {maintenance.asset.asset_name}",
        "✏️",
        f"编辑资产维护记录",
        request=request,
        use_administrative_nav=True
    )
    context.update({
        'form': form,
        'maintenance': maintenance,
    })
    return render(request, "administrative_management/asset_maintenance_form.html", context)


@login_required
def expense_management(request):
    """报销管理"""
    # 获取筛选参数
    search = request.GET.get('search', '')
    expense_type = request.GET.get('expense_type', '')
    status = request.GET.get('status', '')
    applicant_id = request.GET.get('applicant_id', '')
    
    # 获取报销申请列表
    try:
        expenses = ExpenseReimbursement.objects.select_related('applicant', 'approver', 'finance_reviewer').order_by('-application_date', '-created_time')
        
        # 如果是普通用户，只显示自己申请的
        if not request.user.is_superuser and not request.user.roles.filter(code__in=['system_admin', 'general_manager', 'admin_office']).exists():
            expenses = expenses.filter(applicant=request.user)
        
        # 应用筛选条件
        if search:
            expenses = expenses.filter(
                Q(reimbursement_number__icontains=search) |
                Q(notes__icontains=search)
            )
        if expense_type:
            expenses = expenses.filter(expense_type=expense_type)
        if status:
            expenses = expenses.filter(status=status)
        if applicant_id:
            expenses = expenses.filter(applicant_id=applicant_id)
        
        # 分页
        page_size = request.GET.get('page_size', '10')
        try:
            per_page = int(page_size)
            if per_page not in [10, 20, 50]:
                per_page = 10
        except (ValueError, TypeError):
            per_page = 10
        paginator = Paginator(expenses, per_page)
        page_number = request.GET.get('page', 1)
        page_obj = paginator.get_page(page_number)
    except Exception as e:
        import logging
        logger = logging.getLogger(__name__)
        logger.exception('获取报销列表失败: %s', str(e))
        page_obj = None
    
    # 统计信息
    try:
        total_expenses = ExpenseReimbursement.objects.count()
        # 如果是普通用户，只统计自己的
        if not request.user.is_superuser and not request.user.roles.filter(code__in=['system_admin', 'general_manager', 'admin_office']).exists():
            pending_count = ExpenseReimbursement.objects.filter(
                applicant=request.user,
                status='pending_approval'
            ).count()
            approved_count = ExpenseReimbursement.objects.filter(
                applicant=request.user,
                status='approved'
            ).count()
            total_amount = ExpenseReimbursement.objects.filter(
                applicant=request.user
            ).aggregate(total=Sum('total_amount'))['total'] or Decimal('0')
        else:
            pending_count = ExpenseReimbursement.objects.filter(status='pending_approval').count()
            approved_count = ExpenseReimbursement.objects.filter(status='approved').count()
            total_amount = ExpenseReimbursement.objects.aggregate(total=Sum('total_amount'))['total'] or Decimal('0')
        
        # 获取本月报销数量
        from django.utils import timezone
        today = timezone.now().date()
        this_month_start = today.replace(day=1)
        this_month_count = ExpenseReimbursement.objects.filter(
            application_date__gte=this_month_start
        ).count()
        if not request.user.is_superuser and not request.user.roles.filter(code__in=['system_admin', 'general_manager', 'admin_office']).exists():
            this_month_count = this_month_count.filter(applicant=request.user).count()
        
        summary_cards = []
    except Exception as e:
        import logging
        logger = logging.getLogger(__name__)
        logger.exception('获取统计信息失败: %s', str(e))
        summary_cards = []
    
    context = _context(
        "报销管理",
        "💰",
        "管理报销申请和审批流程。",
        summary_cards=summary_cards,
        request=request,
        use_administrative_nav=True
    )
    context.update({
        'page_obj': page_obj,
        'search': search,
        'expense_type': expense_type,
        'status': status,
        'applicant_id': applicant_id,
        'expense_type_choices': ExpenseReimbursement.EXPENSE_TYPE_CHOICES,
        'status_choices': ExpenseReimbursement.STATUS_CHOICES,
    })
    return render(request, "administrative_management/expense_list.html", context)


@login_required
def expense_detail(request, expense_id):
    """报销申请详情"""
    from django.contrib import messages
    from backend.apps.system_management.services import get_user_permission_codes
    
    expense = get_object_or_404(ExpenseReimbursement, id=expense_id)
    
    # 检查权限：普通用户只能查看自己的申请
    permission_codes = get_user_permission_codes(request.user)
    if not _permission_granted('administrative_management.expense.manage', permission_codes):
        if expense.applicant != request.user:
            messages.error(request, '您没有权限查看此报销申请。')
            return redirect('admin_pages:expense_management')
    
    # 获取费用明细
    try:
        items = expense.items.all().order_by('expense_date')
    except Exception:
        items = []
    
    context = _context(
        f"报销申请详情 - {expense.reimbursement_number}",
        "💰",
        f"查看报销申请的详细信息和费用明细",
        request=request,
        use_administrative_nav=True
    )
    context.update({
        'expense': expense,
        'items': items,
    })
    return render(request, "administrative_management/expense_detail.html", context)


# ==================== 行政事务管理视图 ====================

@login_required
def affair_create(request):
    """创建行政事务"""
    permission_codes = get_user_permission_codes(request.user)
    if not _permission_granted('administrative_management.affair.create', permission_codes):
        messages.error(request, '您没有权限创建行政事务')
        return redirect('admin_pages:affair_list')
    
    if request.method == 'POST':
        form = AdministrativeAffairForm(request.POST, request.FILES, user=request.user)
        if form.is_valid():
            affair = form.save(commit=False)
            affair.created_by = request.user
            affair.save()
            form.save_m2m()  # 保存 ManyToMany 字段
            
            # 记录状态历史
            AffairStatusHistory.objects.create(
                affair=affair,
                old_status='',
                new_status=affair.status,
                operator=request.user,
                notes='创建事务'
            )
            
            messages.success(request, f'行政事务 {affair.affair_number} 创建成功！')
            return redirect('admin_pages:affair_detail', affair_id=affair.id)
    else:
        form = AdministrativeAffairForm(user=request.user)
    
    context = _context(
        "创建行政事务",
        "➕",
        "创建新的行政事务",
        request=request,
        use_administrative_nav=True
    )
    context.update({
        'form': form,
        'is_create': True,
        'list_url_name': 'admin_pages:affair_list',
    })
    return render(request, "administrative_management/affair_form.html", context)


@login_required
def affair_update(request, affair_id):
    """编辑行政事务"""
    permission_codes = get_user_permission_codes(request.user)
    affair = get_object_or_404(AdministrativeAffair, id=affair_id)
    
    # 检查权限：只能编辑自己创建的或负责的事务
    if not _permission_granted('administrative_management.affair.manage', permission_codes):
        if affair.created_by != request.user and affair.responsible_user != request.user:
            messages.error(request, '您没有权限编辑此事务')
            return redirect('admin_pages:affair_detail', affair_id=affair_id)
    
    # 已完成或已取消的事务不能编辑
    if affair.status in ['completed', 'cancelled']:
        messages.error(request, '已完成或已取消的事务不能编辑')
        return redirect('admin_pages:affair_detail', affair_id=affair_id)
    
    if request.method == 'POST':
        old_status = affair.status
        form = AdministrativeAffairForm(request.POST, request.FILES, instance=affair, user=request.user)
        if form.is_valid():
            affair = form.save()
            form.save_m2m()
            
            # 如果状态改变，记录状态历史
            if affair.status != old_status:
                AffairStatusHistory.objects.create(
                    affair=affair,
                    old_status=old_status,
                    new_status=affair.status,
                    operator=request.user,
                    notes='编辑事务'
                )
            
            messages.success(request, f'行政事务 {affair.affair_number} 更新成功！')
            return redirect('admin_pages:affair_detail', affair_id=affair.id)
    else:
        form = AdministrativeAffairForm(instance=affair, user=request.user)
    
    context = _context(
        f"编辑行政事务 - {affair.title}",
        "✏️",
        f"编辑行政事务 {affair.affair_number}",
        request=request,
        use_administrative_nav=True
    )
    context.update({
        'form': form,
        'affair': affair,
        'is_create': False,
        'list_url_name': 'admin_pages:affair_list',
    })
    return render(request, "administrative_management/affair_form.html", context)


@login_required
def affair_detail(request, affair_id):
    """行政事务详情"""
    affair = get_object_or_404(
        AdministrativeAffair.objects.prefetch_related('participants', 'status_history', 'progress_records'),
        id=affair_id
    )
    
    # 获取状态历史记录
    status_history = affair.status_history.all().order_by('-operation_time')
    
    # 获取进度记录
    progress_records = affair.progress_records.all().order_by('-record_time')
    
    context = _context(
        f"行政事务详情 - {affair.title}",
        "📋",
        f"查看 {affair.affair_number} 的详细信息和跟踪记录",
        request=request,
        use_administrative_nav=True
    )
    context.update({
        'affair': affair,
        'status_history': status_history,
        'progress_records': progress_records,
    })
    return render(request, "administrative_management/affair_detail.html", context)


@login_required
def affair_start(request, affair_id):
    """开始处理事务"""
    affair = get_object_or_404(AdministrativeAffair, id=affair_id)
    
    # 检查权限：只有负责人可以开始处理
    if affair.responsible_user != request.user:
        messages.error(request, '只有负责人可以开始处理此事务')
        return redirect('admin_pages:affair_detail', affair_id=affair_id)
    
    if affair.status != 'pending':
        messages.error(request, '只有待处理状态的事务可以开始处理')
        return redirect('admin_pages:affair_detail', affair_id=affair_id)
    
    old_status = affair.status
    affair.status = 'in_progress'
    affair.actual_start_time = timezone.now()
    affair.save()
    
    # 记录状态历史
    AffairStatusHistory.objects.create(
        affair=affair,
        old_status=old_status,
        new_status=affair.status,
        operator=request.user,
        notes='开始处理事务'
    )
    
    messages.success(request, f'事务 {affair.affair_number} 已开始处理')
    return redirect('admin_pages:affair_detail', affair_id=affair_id)


@login_required
def affair_complete(request, affair_id):
    """完成事务"""
    affair = get_object_or_404(AdministrativeAffair, id=affair_id)
    
    # 检查权限：只有负责人可以完成
    if affair.responsible_user != request.user:
        messages.error(request, '只有负责人可以完成此事务')
        return redirect('admin_pages:affair_detail', affair_id=affair_id)
    
    if affair.status != 'in_progress':
        messages.error(request, '只有处理中状态的事务可以完成')
        return redirect('admin_pages:affair_detail', affair_id=affair_id)
    
    if request.method == 'POST':
        completion_notes = request.POST.get('completion_notes', '')
        old_status = affair.status
        affair.status = 'completed'
        affair.progress = 100
        affair.actual_end_time = timezone.now()
        affair.completion_notes = completion_notes
        affair.save()
        
        # 记录状态历史
        AffairStatusHistory.objects.create(
            affair=affair,
            old_status=old_status,
            new_status=affair.status,
            operator=request.user,
            notes=f'完成事务：{completion_notes}'
        )
        
        messages.success(request, f'事务 {affair.affair_number} 已完成')
        return redirect('admin_pages:affair_detail', affair_id=affair_id)
    
    # GET请求，显示完成表单
    context = _context(
        f"完成事务 - {affair.title}",
        "✅",
        f"完成行政事务 {affair.affair_number}",
        request=request,
        use_administrative_nav=True
    )
    context.update({
        'affair': affair,
    })
    return render(request, "administrative_management/affair_complete.html", context)


@login_required
def affair_cancel(request, affair_id):
    """取消事务"""
    affair = get_object_or_404(AdministrativeAffair, id=affair_id)
    
    # 检查权限：创建人或负责人可以取消
    permission_codes = get_user_permission_codes(request.user)
    if not _permission_granted('administrative_management.affair.manage', permission_codes):
        if affair.created_by != request.user and affair.responsible_user != request.user:
            messages.error(request, '您没有权限取消此事务')
            return redirect('admin_pages:affair_detail', affair_id=affair_id)
    
    if affair.status in ['completed', 'cancelled']:
        messages.error(request, '已完成或已取消的事务不能再次取消')
        return redirect('admin_pages:affair_detail', affair_id=affair_id)
    
    if request.method == 'POST':
        cancel_reason = request.POST.get('cancel_reason', '')
        old_status = affair.status
        affair.status = 'cancelled'
        affair.save()
        
        # 记录状态历史
        AffairStatusHistory.objects.create(
            affair=affair,
            old_status=old_status,
            new_status=affair.status,
            operator=request.user,
            notes=f'取消事务：{cancel_reason}'
        )
        
        messages.success(request, f'事务 {affair.affair_number} 已取消')
        return redirect('admin_pages:affair_detail', affair_id=affair_id)
    
    # GET请求，显示取消表单
    context = _context(
        f"取消事务 - {affair.title}",
        "❌",
        f"取消行政事务 {affair.affair_number}",
        request=request,
        use_administrative_nav=True
    )
    context.update({
        'affair': affair,
    })
    return render(request, "administrative_management/affair_cancel.html", context)


@login_required
def affair_add_progress(request, affair_id):
    """添加进度记录"""
    affair = get_object_or_404(AdministrativeAffair, id=affair_id)
    
    # 检查权限：只有负责人可以添加进度
    if affair.responsible_user != request.user:
        messages.error(request, '只有负责人可以添加进度记录')
        return redirect('admin_pages:affair_detail', affair_id=affair_id)
    
    if affair.status not in ['in_progress']:
        messages.error(request, '只有处理中状态的事务可以添加进度')
        return redirect('admin_pages:affair_detail', affair_id=affair_id)
    
    if request.method == 'POST':
        form = AffairProgressRecordForm(request.POST, request.FILES)
        if form.is_valid():
            progress_record = form.save(commit=False)
            progress_record.affair = affair
            progress_record.recorder = request.user
            progress_record.save()
            
            # 更新事务进度
            affair.progress = progress_record.progress
            affair.processing_notes = progress_record.notes
            affair.save()
            
            messages.success(request, '进度记录添加成功')
            return redirect('admin_pages:affair_detail', affair_id=affair_id)
    else:
        form = AffairProgressRecordForm(initial={'progress': affair.progress})
    
    context = _context(
        f"添加进度 - {affair.title}",
        "📊",
        f"为事务 {affair.affair_number} 添加进度记录",
        request=request,
        use_administrative_nav=True
    )
    context.update({
        'form': form,
        'affair': affair,
    })
    return render(request, "administrative_management/affair_progress_form.html", context)


# ==================== 会议管理视图 ====================

@login_required
def meeting_list(request):
    """会议列表"""
    # 获取筛选参数
    search = request.GET.get('search', '')
    meeting_type = request.GET.get('meeting_type', '')
    status = request.GET.get('status', '')
    room_id = request.GET.get('room_id', '')
    date_from = request.GET.get('date_from', '')
    date_to = request.GET.get('date_to', '')
    
    # 获取会议列表
    try:
        meetings = Meeting.objects.select_related(
            'room', 'organizer', 'created_by'
        ).prefetch_related('attendees').order_by('-meeting_date', '-start_time')
        
        # 应用筛选条件
        if search:
            meetings = meetings.filter(
                Q(meeting_number__icontains=search) |
                Q(title__icontains=search) |
                Q(agenda__icontains=search)
            )
        if meeting_type:
            meetings = meetings.filter(meeting_type=meeting_type)
        if status:
            meetings = meetings.filter(status=status)
        if room_id:
            meetings = meetings.filter(room_id=room_id)
        if date_from:
            meetings = meetings.filter(meeting_date__gte=date_from)
        if date_to:
            meetings = meetings.filter(meeting_date__lte=date_to)
        
        # 分页
        page_size = request.GET.get('page_size', '10')
        try:
            per_page = int(page_size)
            if per_page not in [10, 20, 50]:
                per_page = 10
        except (ValueError, TypeError):
            per_page = 10
        paginator = Paginator(meetings, per_page)
        page_number = request.GET.get('page', 1)
        page_obj = paginator.get_page(page_number)
    except Exception as e:
        import logging
        logger = logging.getLogger(__name__)
        logger.exception('获取会议列表失败: %s', str(e))
        page_obj = None
    
    # 统计信息
    try:
        total_meetings = Meeting.objects.count()
        scheduled_count = Meeting.objects.filter(status='scheduled').count()
        in_progress_count = Meeting.objects.filter(status='in_progress').count()
        completed_count = Meeting.objects.filter(status='completed').count()
        
        summary_cards = []
    except Exception as e:
        import logging
        logger = logging.getLogger(__name__)
        logger.exception('获取统计信息失败: %s', str(e))
        summary_cards = []
    
    # 获取会议室列表用于筛选
    rooms = MeetingRoom.objects.filter(is_active=True).order_by('code')
    
    context = _context(
        "会议管理",
        "🏢",
        "管理会议的全流程，包括会议安排、会议室管理、会议记录等。",
        summary_cards=summary_cards,
        request=request,
        use_administrative_nav=True
    )
    context.update({
        'page_obj': page_obj,
        'search': search,
        'meeting_type': meeting_type,
        'status': status,
        'room_id': room_id,
        'date_from': date_from,
        'date_to': date_to,
        'meeting_type_choices': Meeting.MEETING_TYPE_CHOICES,
        'status_choices': Meeting.STATUS_CHOICES,
        'rooms': rooms,
    })
    return render(request, "administrative_management/meeting_list.html", context)


@login_required
def meeting_create(request):
    """创建会议"""
    permission_codes = get_user_permission_codes(request.user)
    if not _permission_granted('administrative_management.meeting.create', permission_codes):
        messages.error(request, '您没有权限创建会议')
        return redirect('admin_pages:meeting_list')
    
    if request.method == 'POST':
        form = MeetingForm(request.POST, request.FILES)
        if form.is_valid():
            meeting = form.save(commit=False)
            meeting.created_by = request.user
            if not meeting.organizer:
                meeting.organizer = request.user
            meeting.save()
            form.save_m2m()  # 保存 ManyToMany 字段
            
            # 检查时间冲突
            if meeting.is_conflict:
                messages.warning(request, f'会议 {meeting.meeting_number} 创建成功，但检测到时间冲突！')
            else:
                messages.success(request, f'会议 {meeting.meeting_number} 创建成功！')
            return redirect('admin_pages:meeting_detail', meeting_id=meeting.id)
    else:
        form = MeetingForm(initial={'organizer': request.user})
    
    context = _context(
        "创建会议",
        "➕",
        "创建新的会议",
        request=request,
        use_administrative_nav=True
    )
    context.update({
        'form': form,
        'is_create': True,
    })
    return render(request, "administrative_management/meeting_form.html", context)


@login_required
def meeting_update(request, meeting_id):
    """编辑会议"""
    permission_codes = get_user_permission_codes(request.user)
    meeting = get_object_or_404(Meeting, id=meeting_id)
    
    # 检查权限：只能编辑自己创建的或组织的会议
    if not _permission_granted('administrative_management.meeting.manage', permission_codes):
        if meeting.created_by != request.user and meeting.organizer != request.user:
            messages.error(request, '您没有权限编辑此会议')
            return redirect('admin_pages:meeting_detail', meeting_id=meeting_id)
    
    # 只有待开始状态的会议可以编辑
    if meeting.status != 'scheduled':
        messages.error(request, '只有待开始状态的会议可以编辑')
        return redirect('admin_pages:meeting_detail', meeting_id=meeting_id)
    
    if request.method == 'POST':
        form = MeetingForm(request.POST, request.FILES, instance=meeting)
        if form.is_valid():
            meeting = form.save()
            form.save_m2m()
            
            # 检查时间冲突
            if meeting.is_conflict:
                messages.warning(request, f'会议 {meeting.meeting_number} 更新成功，但检测到时间冲突！')
            else:
                messages.success(request, f'会议 {meeting.meeting_number} 更新成功！')
            return redirect('admin_pages:meeting_detail', meeting_id=meeting.id)
    else:
        form = MeetingForm(instance=meeting)
    
    context = _context(
        f"编辑会议 - {meeting.title}",
        "✏️",
        f"编辑会议 {meeting.meeting_number}",
        request=request,
        use_administrative_nav=True
    )
    context.update({
        'form': form,
        'meeting': meeting,
        'is_create': False,
    })
    return render(request, "administrative_management/meeting_form.html", context)


@login_required
def meeting_detail(request, meeting_id):
    """会议详情"""
    meeting = get_object_or_404(
        Meeting.objects.prefetch_related('attendees'),
        id=meeting_id
    )
    
    # 获取会议记录
    try:
        record = meeting.record
        resolutions = record.resolutions.all().order_by('-created_time')
    except MeetingRecord.DoesNotExist:
        record = None
        resolutions = []
    
    context = _context(
        f"会议详情 - {meeting.title}",
        "🏢",
        f"查看 {meeting.meeting_number} 的详细信息",
        request=request,
        use_administrative_nav=True
    )
    context.update({
        'meeting': meeting,
        'record': record,
        'resolutions': resolutions,
    })
    return render(request, "administrative_management/meeting_detail.html", context)


@login_required
def meeting_cancel(request, meeting_id):
    """取消会议"""
    meeting = get_object_or_404(Meeting, id=meeting_id)
    
    # 检查权限：创建人或组织人可以取消
    permission_codes = get_user_permission_codes(request.user)
    if not _permission_granted('administrative_management.meeting.manage', permission_codes):
        if meeting.created_by != request.user and meeting.organizer != request.user:
            messages.error(request, '您没有权限取消此会议')
            return redirect('admin_pages:meeting_detail', meeting_id=meeting_id)
    
    if meeting.status in ['completed', 'cancelled']:
        messages.error(request, '已完成或已取消的会议不能再次取消')
        return redirect('admin_pages:meeting_detail', meeting_id=meeting_id)
    
    if request.method == 'POST':
        cancel_reason = request.POST.get('cancel_reason', '')
        meeting.status = 'cancelled'
        meeting.cancelled_by = request.user
        meeting.cancelled_time = timezone.now()
        meeting.cancelled_reason = cancel_reason
        meeting.save()
        
        messages.success(request, f'会议 {meeting.meeting_number} 已取消')
        return redirect('admin_pages:meeting_detail', meeting_id=meeting_id)
    
    # GET请求，显示取消表单
    context = _context(
        f"取消会议 - {meeting.title}",
        "❌",
        f"取消会议 {meeting.meeting_number}",
        request=request,
        use_administrative_nav=True
    )
    context.update({
        'meeting': meeting,
    })
    return render(request, "administrative_management/meeting_cancel.html", context)


@login_required
def meeting_record_create(request, meeting_id):
    """创建会议记录"""
    meeting = get_object_or_404(Meeting, id=meeting_id)
    
    # 检查是否已有记录
    if hasattr(meeting, 'record'):
        messages.info(request, '该会议已有记录，请编辑现有记录')
        return redirect('admin_pages:meeting_record_update', meeting_id=meeting_id)
    
    # 只有已结束的会议才能创建记录
    if meeting.status != 'completed':
        messages.error(request, '只有已结束的会议才能创建记录')
        return redirect('admin_pages:meeting_detail', meeting_id=meeting_id)
    
    if request.method == 'POST':
        form = MeetingRecordForm(request.POST, request.FILES)
        if form.is_valid():
            record = form.save(commit=False)
            record.meeting = meeting
            record.recorder = request.user
            record.save()
            
            messages.success(request, '会议记录创建成功')
            return redirect('admin_pages:meeting_detail', meeting_id=meeting_id)
    else:
        form = MeetingRecordForm()
    
    context = _context(
        f"创建会议记录 - {meeting.title}",
        "📝",
        f"为会议 {meeting.meeting_number} 创建记录",
        request=request,
        use_administrative_nav=True
    )
    context.update({
        'form': form,
        'meeting': meeting,
    })
    return render(request, "administrative_management/meeting_record_form.html", context)


@login_required
def meeting_record_update(request, meeting_id):
    """编辑会议记录"""
    meeting = get_object_or_404(Meeting, id=meeting_id)
    
    try:
        record = meeting.record
    except MeetingRecord.DoesNotExist:
        messages.info(request, '该会议还没有记录，请先创建记录')
        return redirect('admin_pages:meeting_record_create', meeting_id=meeting_id)
    
    # 检查权限：只有记录人可以编辑
    if record.recorder != request.user:
        permission_codes = get_user_permission_codes(request.user)
        if not _permission_granted('administrative_management.meeting.manage', permission_codes):
            messages.error(request, '您没有权限编辑此会议记录')
            return redirect('admin_pages:meeting_detail', meeting_id=meeting_id)
    
    if request.method == 'POST':
        form = MeetingRecordForm(request.POST, request.FILES, instance=record)
        if form.is_valid():
            form.save()
            messages.success(request, '会议记录更新成功')
            return redirect('admin_pages:meeting_detail', meeting_id=meeting_id)
    else:
        form = MeetingRecordForm(instance=record)
    
    context = _context(
        f"编辑会议记录 - {meeting.title}",
        "✏️",
        f"编辑会议 {meeting.meeting_number} 的记录",
        request=request,
        use_administrative_nav=True
    )
    context.update({
        'form': form,
        'meeting': meeting,
        'record': record,
    })
    return render(request, "administrative_management/meeting_record_form.html", context)


# ==================== 差旅管理视图 ====================

@login_required
def travel_list(request):
    """差旅申请列表"""
    # 获取筛选参数
    search = request.GET.get('search', '')
    status = request.GET.get('status', '')
    applicant_id = request.GET.get('applicant_id', '')
    
    # 获取差旅申请列表
    try:
        travels = TravelApplication.objects.select_related(
            'applicant', 'department', 'approver'
        ).prefetch_related('travelers').order_by('-application_date', '-created_time')
        
        # 应用筛选条件
        if search:
            travels = travels.filter(
                Q(application_number__icontains=search) |
                Q(destination__icontains=search) |
                Q(travel_reason__icontains=search)
            )
        if status:
            travels = travels.filter(status=status)
        if applicant_id:
            travels = travels.filter(applicant_id=applicant_id)
        
        # 权限检查：普通用户只能看到自己的申请
        permission_codes = get_user_permission_codes(request.user)
        if not _permission_granted('administrative_management.travel.manage', permission_codes):
            travels = travels.filter(applicant=request.user)
        
        # 分页
        page_size = request.GET.get('page_size', '10')
        try:
            per_page = int(page_size)
            if per_page not in [10, 20, 50]:
                per_page = 10
        except (ValueError, TypeError):
            per_page = 10
        paginator = Paginator(travels, per_page)
        page_number = request.GET.get('page', 1)
        page_obj = paginator.get_page(page_number)
    except Exception as e:
        import logging
        logger = logging.getLogger(__name__)
        logger.exception('获取差旅申请列表失败: %s', str(e))
        page_obj = None
    
    # 统计信息
    try:
        permission_codes = get_user_permission_codes(request.user)
        if _permission_granted('administrative_management.travel.manage', permission_codes):
            total_travels = TravelApplication.objects.count()
            pending_count = TravelApplication.objects.filter(status='pending_approval').count()
            approved_count = TravelApplication.objects.filter(status='approved').count()
            in_progress_count = TravelApplication.objects.filter(status='in_progress').count()
        else:
            total_travels = TravelApplication.objects.filter(applicant=request.user).count()
            pending_count = TravelApplication.objects.filter(applicant=request.user, status='pending_approval').count()
            approved_count = TravelApplication.objects.filter(applicant=request.user, status='approved').count()
            in_progress_count = TravelApplication.objects.filter(applicant=request.user, status='in_progress').count()
        
        summary_cards = []
    except Exception as e:
        import logging
        logger = logging.getLogger(__name__)
        logger.exception('获取统计信息失败: %s', str(e))
        summary_cards = []
    
    context = _context(
        "差旅管理",
        "✈️",
        "管理差旅申请和审批。",
        summary_cards=summary_cards,
        request=request,
        use_administrative_nav=True
    )
    context.update({
        'page_obj': page_obj,
        'search': search,
        'status': status,
        'applicant_id': applicant_id,
        'status_choices': TravelApplication.STATUS_CHOICES,
    })
    return render(request, "administrative_management/travel_list.html", context)


@login_required
def travel_create(request):
    """创建差旅申请"""
    permission_codes = get_user_permission_codes(request.user)
    if not _permission_granted('administrative_management.travel.create', permission_codes):
        messages.error(request, '您没有权限创建差旅申请')
        return redirect('admin_pages:travel_list')
    
    if request.method == 'POST':
        form = TravelApplicationForm(request.POST)
        if form.is_valid():
            travel = form.save(commit=False)
            travel.applicant = request.user
            travel.application_date = timezone.now().date()
            # 计算差旅天数
            if travel.start_date and travel.end_date:
                travel.travel_days = (travel.end_date - travel.start_date).days + 1
            travel.save()
            form.save_m2m()  # 保存 ManyToMany 字段
            
            messages.success(request, f'差旅申请 {travel.application_number} 创建成功！')
            return redirect('admin_pages:travel_detail', travel_id=travel.id)
    else:
        form = TravelApplicationForm(initial={
            'department': request.user.department if hasattr(request.user, 'department') else None
        })
    
    context = _context(
        "创建差旅申请",
        "➕",
        "创建新的差旅申请",
        request=request,
        use_administrative_nav=True
    )
    context.update({
        'form': form,
        'is_create': True,
    })
    return render(request, "administrative_management/travel_form.html", context)


@login_required
def travel_detail(request, travel_id):
    """差旅申请详情"""
    travel = get_object_or_404(TravelApplication, id=travel_id)
    
    # 权限检查：普通用户只能查看自己的申请
    permission_codes = get_user_permission_codes(request.user)
    if not _permission_granted('administrative_management.travel.manage', permission_codes):
        if travel.applicant != request.user:
            messages.error(request, '您没有权限查看此差旅申请')
            return redirect('admin_pages:travel_list')
    
    context = _context(
        f"差旅申请详情 - {travel.application_number}",
        "✈️",
        f"查看差旅申请的详细信息",
        request=request,
        use_administrative_nav=True
    )
    context.update({
        'travel': travel,
        'can_approve': _permission_granted('administrative_management.travel.approve', permission_codes),
        'can_edit': travel.applicant == request.user and travel.status == 'draft',
    })
    return render(request, "administrative_management/travel_detail.html", context)


@login_required
def travel_update(request, travel_id):
    """编辑差旅申请"""
    travel = get_object_or_404(TravelApplication, id=travel_id)
    
    # 权限检查：只能编辑自己的草稿申请
    if travel.applicant != request.user:
        messages.error(request, '您没有权限编辑此差旅申请')
        return redirect('admin_pages:travel_detail', travel_id=travel_id)
    
    if travel.status != 'draft':
        messages.error(request, '只能编辑草稿状态的差旅申请')
        return redirect('admin_pages:travel_detail', travel_id=travel_id)
    
    if request.method == 'POST':
        form = TravelApplicationForm(request.POST, instance=travel)
        if form.is_valid():
            travel = form.save(commit=False)
            # 计算差旅天数
            if travel.start_date and travel.end_date:
                travel.travel_days = (travel.end_date - travel.start_date).days + 1
            travel.save()
            form.save_m2m()  # 保存 ManyToMany 字段
            
            messages.success(request, f'差旅申请 {travel.application_number} 更新成功！')
            return redirect('admin_pages:travel_detail', travel_id=travel.id)
    else:
        form = TravelApplicationForm(instance=travel)
    
    context = _context(
        f"编辑差旅申请 - {travel.application_number}",
        "✏️",
        f"编辑差旅申请 {travel.application_number}",
        request=request,
        use_administrative_nav=True
    )
    context.update({
        'form': form,
        'travel': travel,
        'is_create': False,
    })
    return render(request, "administrative_management/travel_form.html", context)


@login_required
def travel_approve(request, travel_id):
    """审批差旅申请"""
    permission_codes = get_user_permission_codes(request.user)
    if not _permission_granted('administrative_management.travel.approve', permission_codes):
        messages.error(request, '您没有权限审批差旅申请')
        return redirect('admin_pages:travel_detail', travel_id=travel_id)
    
    travel = get_object_or_404(TravelApplication, id=travel_id)
    
    if travel.status != 'pending_approval':
        messages.error(request, '只能审批待审批状态的差旅申请')
        return redirect('admin_pages:travel_detail', travel_id=travel_id)
    
    if request.method == 'POST':
        approval_notes = request.POST.get('approval_notes', '')
        travel.status = 'approved'
        travel.approver = request.user
        travel.approved_time = timezone.now()
        travel.approval_notes = approval_notes
        travel.save()
        
        messages.success(request, f'差旅申请 {travel.application_number} 已批准')
        return redirect('admin_pages:travel_detail', travel_id=travel_id)
    
    context = _context(
        f"审批差旅申请 - {travel.application_number}",
        "✅",
        f"审批差旅申请 {travel.application_number}",
        request=request,
        use_administrative_nav=True
    )
    context.update({
        'travel': travel,
    })
    return render(request, "administrative_management/travel_approve.html", context)


@login_required
def travel_reject(request, travel_id):
    """拒绝差旅申请"""
    permission_codes = get_user_permission_codes(request.user)
    if not _permission_granted('administrative_management.travel.approve', permission_codes):
        messages.error(request, '您没有权限拒绝差旅申请')
        return redirect('admin_pages:travel_detail', travel_id=travel_id)
    
    travel = get_object_or_404(TravelApplication, id=travel_id)
    
    if travel.status != 'pending_approval':
        messages.error(request, '只能拒绝待审批状态的差旅申请')
        return redirect('admin_pages:travel_detail', travel_id=travel_id)
    
    if request.method == 'POST':
        approval_notes = request.POST.get('approval_notes', '')
        if not approval_notes:
            messages.error(request, '请填写拒绝原因')
            return redirect('admin_pages:travel_reject', travel_id=travel_id)
        
        travel.status = 'rejected'
        travel.approver = request.user
        travel.approved_time = timezone.now()
        travel.approval_notes = approval_notes
        travel.save()
        
        messages.success(request, f'差旅申请 {travel.application_number} 已拒绝')
        return redirect('admin_pages:travel_detail', travel_id=travel_id)
    
    context = _context(
        f"拒绝差旅申请 - {travel.application_number}",
        "❌",
        f"拒绝差旅申请 {travel.application_number}",
        request=request,
        use_administrative_nav=True
    )
    context.update({
        'travel': travel,
    })
    return render(request, "administrative_management/travel_reject.html", context)


# ==================== 供应商管理视图 ====================

@login_required
def supplier_list(request):
    """供应商列表"""
    # 获取筛选参数
    search = request.GET.get('search', '')
    rating = request.GET.get('rating', '')
    is_active = request.GET.get('is_active', '')
    
    # 获取供应商列表
    try:
        suppliers = Supplier.objects.select_related('created_by').order_by('name')
        
        # 应用筛选条件
        if search:
            suppliers = suppliers.filter(
                Q(name__icontains=search) |
                Q(contact_person__icontains=search) |
                Q(contact_phone__icontains=search)
            )
        if rating:
            suppliers = suppliers.filter(rating=rating)
        if is_active == 'true':
            suppliers = suppliers.filter(is_active=True)
        elif is_active == 'false':
            suppliers = suppliers.filter(is_active=False)
        
        # 分页
        page_size = request.GET.get('page_size', '10')
        try:
            per_page = int(page_size)
            if per_page not in [10, 20, 50]:
                per_page = 10
        except (ValueError, TypeError):
            per_page = 10
        paginator = Paginator(suppliers, per_page)
        page_number = request.GET.get('page', 1)
        page_obj = paginator.get_page(page_number)
    except Exception as e:
        import logging
        logger = logging.getLogger(__name__)
        logger.exception('获取供应商列表失败: %s', str(e))
        page_obj = None
    
    # 统计信息
    try:
        total_suppliers = Supplier.objects.count()
        active_suppliers = Supplier.objects.filter(is_active=True).count()
        a_rating_count = Supplier.objects.filter(rating='A', is_active=True).count()
        total_purchase_amount = sum(float(s.total_purchase_amount) for s in Supplier.objects.filter(is_active=True))
        
        summary_cards = []
    except Exception as e:
        import logging
        logger = logging.getLogger(__name__)
        logger.exception('获取统计信息失败: %s', str(e))
        summary_cards = []
    
    context = _context(
        "供应商管理",
        "🏢",
        "管理供应商信息和评级。",
        summary_cards=summary_cards,
        request=request,
        use_administrative_nav=True
    )
    context.update({
        'page_obj': page_obj,
        'search': search,
        'rating': rating,
        'is_active': is_active,
        'rating_choices': Supplier.RATING_CHOICES,
    })
    return render(request, "administrative_management/supplier_list.html", context)


@login_required
def supplier_create(request):
    """创建供应商"""
    permission_codes = get_user_permission_codes(request.user)
    if not _permission_granted('administrative_management.supplies.view', permission_codes):
        messages.error(request, '您没有权限创建供应商')
        return redirect('admin_pages:supplier_list')
    
    if request.method == 'POST':
        form = SupplierForm(request.POST)
        if form.is_valid():
            supplier = form.save(commit=False)
            supplier.created_by = request.user
            supplier.save()
            messages.success(request, f'供应商 {supplier.name} 创建成功！')
            return redirect('admin_pages:supplier_detail', supplier_id=supplier.id)
    else:
        form = SupplierForm()
    
    context = _context(
        "创建供应商",
        "➕",
        "创建新的供应商",
        request=request,
        use_administrative_nav=True
    )
    context.update({
        'form': form,
        'is_create': True,
    })
    return render(request, "administrative_management/supplier_form.html", context)


@login_required
def supplier_detail(request, supplier_id):
    """供应商详情"""
    supplier = get_object_or_404(Supplier, id=supplier_id)
    
    # 获取采购记录
    try:
        purchases = SupplyPurchase.objects.filter(
            supplier_obj=supplier
        ).select_related('created_by', 'approver').order_by('-purchase_date')[:10]
    except Exception:
        purchases = []
    
    # 获取合同记录
    try:
        contracts = PurchaseContract.objects.filter(
            supplier=supplier
        ).order_by('-signed_date')[:10]
    except Exception:
        contracts = []
    
    context = _context(
        f"供应商详情 - {supplier.name}",
        "🏢",
        f"查看供应商 {supplier.name} 的详细信息和采购记录",
        request=request,
        use_administrative_nav=True
    )
    context.update({
        'supplier': supplier,
        'purchases': purchases,
        'contracts': contracts,
    })
    return render(request, "administrative_management/supplier_detail.html", context)


@login_required
def supplier_update(request, supplier_id):
    """编辑供应商"""
    permission_codes = get_user_permission_codes(request.user)
    supplier = get_object_or_404(Supplier, id=supplier_id)
    
    if not _permission_granted('administrative_management.supplier.manage', permission_codes):
        messages.error(request, '您没有权限编辑供应商')
        return redirect('admin_pages:supplier_detail', supplier_id=supplier_id)
    
    if request.method == 'POST':
        form = SupplierForm(request.POST, instance=supplier)
        if form.is_valid():
            form.save()
            messages.success(request, f'供应商 {supplier.name} 更新成功！')
            return redirect('admin_pages:supplier_detail', supplier_id=supplier.id)
    else:
        form = SupplierForm(instance=supplier)
    
    context = _context(
        f"编辑供应商 - {supplier.name}",
        "✏️",
        f"编辑供应商 {supplier.name}",
        request=request,
        use_administrative_nav=True
    )
    context.update({
        'form': form,
        'supplier': supplier,
        'is_create': False,
    })
    return render(request, "administrative_management/supplier_form.html", context)


# ==================== 采购合同管理视图 ====================

@login_required
def purchase_contract_list(request):
    """采购合同列表"""
    # 获取筛选参数
    search = request.GET.get('search', '')
    status = request.GET.get('status', '')
    supplier_id = request.GET.get('supplier_id', '')
    
    # 获取合同列表
    try:
        contracts = PurchaseContract.objects.select_related(
            'supplier', 'purchase', 'created_by'
        ).order_by('-created_time')
        
        # 应用筛选条件
        if search:
            contracts = contracts.filter(
                Q(contract_number__icontains=search) |
                Q(contract_name__icontains=search)
            )
        if status:
            contracts = contracts.filter(status=status)
        if supplier_id:
            contracts = contracts.filter(supplier_id=supplier_id)
        
        # 分页
        page_size = request.GET.get('page_size', '10')
        try:
            per_page = int(page_size)
            if per_page not in [10, 20, 50]:
                per_page = 10
        except (ValueError, TypeError):
            per_page = 10
        paginator = Paginator(contracts, per_page)
        page_number = request.GET.get('page', 1)
        page_obj = paginator.get_page(page_number)
    except Exception as e:
        import logging
        logger = logging.getLogger(__name__)
        logger.exception('获取采购合同列表失败: %s', str(e))
        page_obj = None
    
    # 统计信息
    try:
        total_contracts = PurchaseContract.objects.count()
        pending_count = PurchaseContract.objects.filter(status='pending_approval').count()
        signed_count = PurchaseContract.objects.filter(status='signed').count()
        total_amount = sum(float(c.contract_amount) for c in PurchaseContract.objects.filter(status__in=['signed', 'executing']))
        
        summary_cards = []
    except Exception as e:
        import logging
        logger = logging.getLogger(__name__)
        logger.exception('获取统计信息失败: %s', str(e))
        summary_cards = []
    
    context = _context(
        "采购合同管理",
        "📄",
        "管理采购合同的签订和执行。",
        summary_cards=summary_cards,
        request=request,
        use_administrative_nav=True
    )
    context.update({
        'page_obj': page_obj,
        'search': search,
        'status': status,
        'supplier_id': supplier_id,
        'status_choices': PurchaseContract.STATUS_CHOICES,
    })
    return render(request, "administrative_management/purchase_contract_list.html", context)


@login_required
def purchase_contract_create(request):
    """创建采购合同"""
    permission_codes = get_user_permission_codes(request.user)
    if not _permission_granted('administrative_management.contract.create', permission_codes):
        messages.error(request, '您没有权限创建采购合同')
        return redirect('admin_pages:purchase_contract_list')
    
    if request.method == 'POST':
        form = PurchaseContractForm(request.POST, request.FILES)
        if form.is_valid():
            contract = form.save(commit=False)
            contract.created_by = request.user
            contract.save()
            messages.success(request, f'采购合同 {contract.contract_number} 创建成功！')
            return redirect('admin_pages:purchase_contract_detail', contract_id=contract.id)
    else:
        form = PurchaseContractForm()
    
    context = _context(
        "创建采购合同",
        "➕",
        "创建新的采购合同",
        request=request,
        use_administrative_nav=True
    )
    context.update({
        'form': form,
        'is_create': True,
    })
    return render(request, "administrative_management/purchase_contract_form.html", context)


@login_required
def purchase_contract_detail(request, contract_id):
    """采购合同详情"""
    contract = get_object_or_404(PurchaseContract, id=contract_id)
    
    # 获取付款记录
    try:
        payments = PurchasePayment.objects.filter(
            contract=contract
        ).select_related('paid_by', 'created_by').order_by('-payment_date')
    except Exception:
        payments = []
    
    context = _context(
        f"采购合同详情 - {contract.contract_number}",
        "📄",
        f"查看采购合同 {contract.contract_number} 的详细信息和付款记录",
        request=request,
        use_administrative_nav=True
    )
    context.update({
        'contract': contract,
        'payments': payments,
        'can_pay': contract.status in ['signed', 'executing'] and contract.unpaid_amount > 0,
    })
    return render(request, "administrative_management/purchase_contract_detail.html", context)


@login_required
def purchase_contract_update(request, contract_id):
    """编辑采购合同"""
    permission_codes = get_user_permission_codes(request.user)
    contract = get_object_or_404(PurchaseContract, id=contract_id)
    
    if not _permission_granted('administrative_management.contract.manage', permission_codes):
        messages.error(request, '您没有权限编辑采购合同')
        return redirect('admin_pages:purchase_contract_detail', contract_id=contract_id)
    
    if contract.status in ['completed', 'cancelled']:
        messages.error(request, '已完成或已取消的合同不能编辑')
        return redirect('admin_pages:purchase_contract_detail', contract_id=contract_id)
    
    if request.method == 'POST':
        form = PurchaseContractForm(request.POST, request.FILES, instance=contract)
        if form.is_valid():
            form.save()
            messages.success(request, f'采购合同 {contract.contract_number} 更新成功！')
            return redirect('admin_pages:purchase_contract_detail', contract_id=contract.id)
    else:
        form = PurchaseContractForm(instance=contract)
    
    context = _context(
        f"编辑采购合同 - {contract.contract_number}",
        "✏️",
        f"编辑采购合同 {contract.contract_number}",
        request=request,
        use_administrative_nav=True
    )
    context.update({
        'form': form,
        'contract': contract,
        'is_create': False,
    })
    return render(request, "administrative_management/purchase_contract_form.html", context)


# ==================== 采购付款管理视图 ====================

@login_required
def purchase_payment_list(request):
    """采购付款列表"""
    # 获取筛选参数
    search = request.GET.get('search', '')
    status = request.GET.get('status', '')
    contract_id = request.GET.get('contract_id', '')
    
    # 获取付款列表
    try:
        payments = PurchasePayment.objects.select_related(
            'contract', 'paid_by', 'created_by'
        ).order_by('-payment_date', '-created_time')
        
        # 应用筛选条件
        if search:
            payments = payments.filter(
                Q(payment_number__icontains=search) |
                Q(voucher_number__icontains=search)
            )
        if status:
            payments = payments.filter(status=status)
        if contract_id:
            payments = payments.filter(contract_id=contract_id)
        
        # 分页
        page_size = request.GET.get('page_size', '10')
        try:
            per_page = int(page_size)
            if per_page not in [10, 20, 50]:
                per_page = 10
        except (ValueError, TypeError):
            per_page = 10
        paginator = Paginator(payments, per_page)
        page_number = request.GET.get('page', 1)
        page_obj = paginator.get_page(page_number)
    except Exception as e:
        import logging
        logger = logging.getLogger(__name__)
        logger.exception('获取采购付款列表失败: %s', str(e))
        page_obj = None
    
    # 统计信息
    try:
        total_payments = PurchasePayment.objects.count()
        pending_count = PurchasePayment.objects.filter(status='pending').count()
        paid_count = PurchasePayment.objects.filter(status='paid').count()
        total_paid_amount = sum(float(p.amount) for p in PurchasePayment.objects.filter(status='paid'))
        
        summary_cards = []
    except Exception as e:
        import logging
        logger = logging.getLogger(__name__)
        logger.exception('获取统计信息失败: %s', str(e))
        summary_cards = []
    
    context = _context(
        "采购付款管理",
        "💰",
        "管理采购合同的付款记录。",
        summary_cards=summary_cards,
        request=request,
        use_administrative_nav=True
    )
    context.update({
        'page_obj': page_obj,
        'search': search,
        'status': status,
        'contract_id': contract_id,
        'status_choices': PurchasePayment.STATUS_CHOICES,
    })
    return render(request, "administrative_management/purchase_payment_list.html", context)


@login_required
def purchase_payment_create(request, contract_id=None):
    """创建采购付款"""
    permission_codes = get_user_permission_codes(request.user)
    if not _permission_granted('administrative_management.payment.create', permission_codes):
        messages.error(request, '您没有权限创建采购付款')
        if contract_id:
            return redirect('admin_pages:purchase_contract_detail', contract_id=contract_id)
        return redirect('admin_pages:purchase_payment_list')
    
    contract = None
    if contract_id:
        contract = get_object_or_404(PurchaseContract, id=contract_id)
        if contract.status not in ['signed', 'executing']:
            messages.error(request, '只能为已签约或执行中的合同创建付款')
            return redirect('admin_pages:purchase_contract_detail', contract_id=contract_id)
    
    if request.method == 'POST':
        form = PurchasePaymentForm(request.POST)
        if form.is_valid():
            payment = form.save(commit=False)
            payment.created_by = request.user
            payment.save()
            messages.success(request, f'采购付款 {payment.payment_number} 创建成功！')
            return redirect('admin_pages:purchase_payment_detail', payment_id=payment.id)
    else:
        initial = {}
        if contract:
            initial['contract'] = contract
            initial['payment_date'] = timezone.now().date()
        form = PurchasePaymentForm(initial=initial)
    
    context = _context(
        "创建采购付款",
        "➕",
        "创建新的采购付款",
        request=request,
        use_administrative_nav=True
    )
    context.update({
        'form': form,
        'contract': contract,
        'is_create': True,
    })
    return render(request, "administrative_management/purchase_payment_form.html", context)


@login_required
def purchase_payment_detail(request, payment_id):
    """采购付款详情"""
    payment = get_object_or_404(PurchasePayment, id=payment_id)
    
    context = _context(
        f"采购付款详情 - {payment.payment_number}",
        "💰",
        f"查看采购付款 {payment.payment_number} 的详细信息",
        request=request,
        use_administrative_nav=True
    )
    context.update({
        'payment': payment,
        'can_pay': payment.status == 'pending',
    })
    return render(request, "administrative_management/purchase_payment_detail.html", context)


@login_required
def purchase_payment_confirm(request, payment_id):
    """确认付款"""
    permission_codes = get_user_permission_codes(request.user)
    if not _permission_granted('administrative_management.payment.confirm', permission_codes):
        messages.error(request, '您没有权限确认付款')
        return redirect('admin_pages:purchase_payment_detail', payment_id=payment_id)
    
    payment = get_object_or_404(PurchasePayment, id=payment_id)
    
    if payment.status != 'pending':
        messages.error(request, '只能确认待付款状态的付款单')
        return redirect('admin_pages:purchase_payment_detail', payment_id=payment_id)
    
    if request.method == 'POST':
        payment.status = 'paid'
        payment.paid_by = request.user
        payment.paid_time = timezone.now()
        payment.save()
        
        messages.success(request, f'采购付款 {payment.payment_number} 已确认付款')
        return redirect('admin_pages:purchase_payment_detail', payment_id=payment_id)
    
    context = _context(
        f"确认付款 - {payment.payment_number}",
        "✅",
        f"确认采购付款 {payment.payment_number}",
        request=request,
        use_administrative_nav=True
    )
    context.update({
        'payment': payment,
    })
    return render(request, "administrative_management/purchase_payment_confirm.html", context)


# ==================== 库存盘点管理视图 ====================

@login_required
def inventory_check_list(request):
    """库存盘点列表"""
    permission_codes = get_user_permission_codes(request.user)
    if not _permission_granted('administrative_management.supplies.view', permission_codes):
        messages.error(request, '您没有权限查看库存盘点')
        return redirect('admin_pages:administrative_home')
    
    # 获取筛选参数
    search = request.GET.get('search', '')
    status = request.GET.get('status', '')
    check_date = request.GET.get('check_date', '')
    
    # 获取盘点列表
    try:
        checks = InventoryCheck.objects.select_related('checker', 'approver').prefetch_related('participants').order_by('-check_date', '-created_time')
        
        # 应用筛选条件
        if search:
            checks = checks.filter(
                Q(check_number__icontains=search) |
                Q(check_scope__icontains=search)
            )
        if status:
            checks = checks.filter(status=status)
        if check_date:
            checks = checks.filter(check_date=check_date)
        
        # 权限检查：普通用户只能看到自己创建的盘点
        if not _permission_granted('administrative_management.supplies.manage', permission_codes):
            checks = checks.filter(checker=request.user)
        
        # 分页
        page_size = request.GET.get('page_size', '10')
        try:
            per_page = int(page_size)
            if per_page not in [10, 20, 50]:
                per_page = 10
        except (ValueError, TypeError):
            per_page = 10
        paginator = Paginator(checks, per_page)
        page_number = request.GET.get('page', 1)
        page_obj = paginator.get_page(page_number)
    except Exception as e:
        import logging
        logger = logging.getLogger(__name__)
        logger.exception('获取库存盘点列表失败: %s', str(e))
        page_obj = None
    
    # 统计信息
    try:
        if _permission_granted('administrative_management.supplies.manage', permission_codes):
            total_checks = InventoryCheck.objects.count()
            in_progress_count = InventoryCheck.objects.filter(status='in_progress').count()
            completed_count = InventoryCheck.objects.filter(status='completed').count()
            approved_count = InventoryCheck.objects.filter(status='approved').count()
        else:
            total_checks = InventoryCheck.objects.filter(checker=request.user).count()
            in_progress_count = InventoryCheck.objects.filter(checker=request.user, status='in_progress').count()
            completed_count = InventoryCheck.objects.filter(checker=request.user, status='completed').count()
            approved_count = InventoryCheck.objects.filter(checker=request.user, status='approved').count()
        
        summary_cards = []
    except Exception as e:
        import logging
        logger = logging.getLogger(__name__)
        logger.exception('获取统计信息失败: %s', str(e))
        summary_cards = []
    
    context = _context(
        "库存盘点管理",
        "📊",
        "管理库存盘点计划和执行。",
        summary_cards=summary_cards,
        request=request,
        use_administrative_nav=True
    )
    context.update({
        'page_obj': page_obj,
        'search': search,
        'status': status,
        'check_date': check_date,
    })
    return render(request, "administrative_management/inventory_check_list.html", context)


@login_required
def inventory_check_create(request):
    """创建库存盘点"""
    permission_codes = get_user_permission_codes(request.user)
    if not _permission_granted('administrative_management.supplies.manage', permission_codes):
        messages.error(request, '您没有权限创建库存盘点')
        return redirect('admin_pages:inventory_check_list')
    
    # 创建内联表单集
    InventoryCheckItemFormSet = inlineformset_factory(
        InventoryCheck, InventoryCheckItem,
        form=InventoryCheckItemForm,
        extra=5,
        can_delete=True,
        min_num=1,
    )
    
    if request.method == 'POST':
        form = InventoryCheckForm(request.POST)
        formset = InventoryCheckItemFormSet(request.POST)
        
        if form.is_valid() and formset.is_valid():
            check = form.save(commit=False)
            check.checker = request.user
            check.save()
            form.save_m2m()  # 保存 ManyToMany 字段
            
            # 保存明细项，自动设置账面数量
            for item_form in formset:
                if item_form.cleaned_data and not item_form.cleaned_data.get('DELETE', False):
                    item = item_form.save(commit=False)
                    item.check = check
                    if not item.book_quantity:
                        item.book_quantity = item.supply.current_stock
                    item.save()
            
            messages.success(request, f'库存盘点 {check.check_number} 创建成功！')
            return redirect('admin_pages:inventory_check_detail', check_id=check.id)
    else:
        form = InventoryCheckForm(initial={
            'check_date': timezone.now().date()
        })
        formset = InventoryCheckItemFormSet()
    
    context = _context(
        "创建库存盘点",
        "➕",
        "创建新的库存盘点",
        request=request,
        use_administrative_nav=True
    )
    context.update({
        'form': form,
        'formset': formset,
        'is_create': True,
    })
    return render(request, "administrative_management/inventory_check_form.html", context)


@login_required
def inventory_check_detail(request, check_id):
    """库存盘点详情"""
    check = get_object_or_404(InventoryCheck, id=check_id)
    
    # 权限检查
    permission_codes = get_user_permission_codes(request.user)
    if not _permission_granted('administrative_management.supplies.manage', permission_codes):
        if check.checker != request.user:
            messages.error(request, '您没有权限查看此库存盘点')
            return redirect('admin_pages:inventory_check_list')
    
    # 获取盘点明细
    items = check.items.select_related('supply', 'checked_by').order_by('supply__code')
    
    context = _context(
        f"库存盘点详情 - {check.check_number}",
        "📊",
        f"查看库存盘点的详细信息",
        request=request,
        use_administrative_nav=True
    )
    context.update({
        'check': check,
        'items': items,
        'can_approve': _permission_granted('administrative_management.supplies.manage', permission_codes) and check.status == 'completed',
        'can_edit': check.status == 'draft' and check.checker == request.user,
    })
    return render(request, "administrative_management/inventory_check_detail.html", context)


@login_required
def inventory_check_update(request, check_id):
    """编辑库存盘点"""
    check = get_object_or_404(InventoryCheck, id=check_id)
    
    # 权限检查：只能编辑自己的草稿盘点
    if check.checker != request.user:
        messages.error(request, '您没有权限编辑此库存盘点')
        return redirect('admin_pages:inventory_check_detail', check_id=check_id)
    
    if check.status != 'draft':
        messages.error(request, '只能编辑草稿状态的库存盘点')
        return redirect('admin_pages:inventory_check_detail', check_id=check_id)
    
    # 创建内联表单集
    InventoryCheckItemFormSet = inlineformset_factory(
        InventoryCheck, InventoryCheckItem,
        form=InventoryCheckItemForm,
        extra=3,
        can_delete=True,
    )
    
    if request.method == 'POST':
        form = InventoryCheckForm(request.POST, instance=check)
        formset = InventoryCheckItemFormSet(request.POST, instance=check)
        
        if form.is_valid() and formset.is_valid():
            form.save()
            formset.save()
            
            messages.success(request, f'库存盘点 {check.check_number} 更新成功！')
            return redirect('admin_pages:inventory_check_detail', check_id=check.id)
    else:
        form = InventoryCheckForm(instance=check)
        formset = InventoryCheckItemFormSet(instance=check)
    
    context = _context(
        f"编辑库存盘点 - {check.check_number}",
        "✏️",
        f"编辑库存盘点 {check.check_number}",
        request=request,
        use_administrative_nav=True
    )
    context.update({
        'form': form,
        'formset': formset,
        'check': check,
        'is_create': False,
    })
    return render(request, "administrative_management/inventory_check_form.html", context)


@login_required
def inventory_check_approve(request, check_id):
    """审核库存盘点"""
    permission_codes = get_user_permission_codes(request.user)
    if not _permission_granted('administrative_management.supplies.manage', permission_codes):
        messages.error(request, '您没有权限审核库存盘点')
        return redirect('admin_pages:inventory_check_detail', check_id=check_id)
    
    check = get_object_or_404(InventoryCheck, id=check_id)
    
    if check.status != 'completed':
        messages.error(request, '只能审核已完成状态的库存盘点')
        return redirect('admin_pages:inventory_check_detail', check_id=check_id)
    
    if request.method == 'POST':
        # 审核通过，更新库存
        for item in check.items.all():
            if item.actual_quantity is not None and item.difference != 0:
                # 更新库存
                item.supply.current_stock = item.actual_quantity
                item.supply.save()
        
        check.status = 'approved'
        check.approver = request.user
        check.approved_time = timezone.now()
        check.save()
        
        messages.success(request, f'库存盘点 {check.check_number} 已审核通过，库存已更新')
        return redirect('admin_pages:inventory_check_detail', check_id=check_id)
    
    # 获取盘点明细
    items = check.items.select_related('supply').order_by('supply__code')
    
    context = _context(
        f"审核库存盘点 - {check.check_number}",
        "✅",
        f"审核库存盘点 {check.check_number}",
        request=request,
        use_administrative_nav=True
    )
    context.update({
        'check': check,
        'items': items,
    })
    return render(request, "administrative_management/inventory_check_approve.html", context)


# ==================== 库存调整管理视图 ====================

@login_required
def inventory_adjust_list(request):
    """库存调整列表"""
    permission_codes = get_user_permission_codes(request.user)
    if not _permission_granted('administrative_management.supplies.view', permission_codes):
        messages.error(request, '您没有权限查看库存调整')
        return redirect('admin_pages:administrative_home')
    
    # 获取筛选参数
    search = request.GET.get('search', '')
    status = request.GET.get('status', '')
    adjust_date = request.GET.get('adjust_date', '')
    
    # 获取调整列表
    try:
        adjusts = InventoryAdjust.objects.select_related('created_by', 'approver', 'executed_by').order_by('-adjust_date', '-created_time')
        
        # 应用筛选条件
        if search:
            adjusts = adjusts.filter(
                Q(adjust_number__icontains=search) |
                Q(reason__icontains=search)
            )
        if status:
            adjusts = adjusts.filter(status=status)
        if adjust_date:
            adjusts = adjusts.filter(adjust_date=adjust_date)
        
        # 权限检查：普通用户只能看到自己创建的调整
        if not _permission_granted('administrative_management.supplies.manage', permission_codes):
            adjusts = adjusts.filter(created_by=request.user)
        
        # 分页
        page_size = request.GET.get('page_size', '10')
        try:
            per_page = int(page_size)
            if per_page not in [10, 20, 50]:
                per_page = 10
        except (ValueError, TypeError):
            per_page = 10
        paginator = Paginator(adjusts, per_page)
        page_number = request.GET.get('page', 1)
        page_obj = paginator.get_page(page_number)
    except Exception as e:
        import logging
        logger = logging.getLogger(__name__)
        logger.exception('获取库存调整列表失败: %s', str(e))
        page_obj = None
    
    # 统计信息
    try:
        if _permission_granted('administrative_management.supplies.manage', permission_codes):
            total_adjusts = InventoryAdjust.objects.count()
            pending_count = InventoryAdjust.objects.filter(status='pending_approval').count()
            approved_count = InventoryAdjust.objects.filter(status='approved').count()
            executed_count = InventoryAdjust.objects.filter(status='executed').count()
        else:
            total_adjusts = InventoryAdjust.objects.filter(created_by=request.user).count()
            pending_count = InventoryAdjust.objects.filter(created_by=request.user, status='pending_approval').count()
            approved_count = InventoryAdjust.objects.filter(created_by=request.user, status='approved').count()
            executed_count = InventoryAdjust.objects.filter(created_by=request.user, status='executed').count()
        
        summary_cards = []
    except Exception as e:
        import logging
        logger = logging.getLogger(__name__)
        logger.exception('获取统计信息失败: %s', str(e))
        summary_cards = []
    
    context = _context(
        "库存调整管理",
        "🔄",
        "管理库存调整申请和执行。",
        summary_cards=summary_cards,
        request=request,
        use_administrative_nav=True
    )
    context.update({
        'page_obj': page_obj,
        'search': search,
        'status': status,
        'adjust_date': adjust_date,
    })
    return render(request, "administrative_management/inventory_adjust_list.html", context)


@login_required
def inventory_adjust_create(request):
    """创建库存调整"""
    permission_codes = get_user_permission_codes(request.user)
    if not _permission_granted('administrative_management.supplies.manage', permission_codes):
        messages.error(request, '您没有权限创建库存调整')
        return redirect('admin_pages:inventory_adjust_list')
    
    # 创建内联表单集
    InventoryAdjustItemFormSet = inlineformset_factory(
        InventoryAdjust, InventoryAdjustItem,
        form=InventoryAdjustItemForm,
        extra=3,
        can_delete=True,
        min_num=1,
    )
    
    if request.method == 'POST':
        form = InventoryAdjustForm(request.POST)
        formset = InventoryAdjustItemFormSet(request.POST)
        
        if form.is_valid() and formset.is_valid():
            adjust = form.save(commit=False)
            adjust.created_by = request.user
            adjust.save()
            formset.save()
            
            messages.success(request, f'库存调整 {adjust.adjust_number} 创建成功！')
            return redirect('admin_pages:inventory_adjust_detail', adjust_id=adjust.id)
    else:
        form = InventoryAdjustForm(initial={
            'adjust_date': timezone.now().date()
        })
        formset = InventoryAdjustItemFormSet()
    
    context = _context(
        "创建库存调整",
        "➕",
        "创建新的库存调整",
        request=request,
        use_administrative_nav=True
    )
    context.update({
        'form': form,
        'formset': formset,
        'is_create': True,
    })
    return render(request, "administrative_management/inventory_adjust_form.html", context)


@login_required
def inventory_adjust_detail(request, adjust_id):
    """库存调整详情"""
    adjust = get_object_or_404(InventoryAdjust, id=adjust_id)
    
    # 权限检查
    permission_codes = get_user_permission_codes(request.user)
    if not _permission_granted('administrative_management.supplies.manage', permission_codes):
        if adjust.created_by != request.user:
            messages.error(request, '您没有权限查看此库存调整')
            return redirect('admin_pages:inventory_adjust_list')
    
    # 获取调整明细
    items = adjust.items.select_related('supply').order_by('supply__code')
    
    context = _context(
        f"库存调整详情 - {adjust.adjust_number}",
        "🔄",
        f"查看库存调整的详细信息",
        request=request,
        use_administrative_nav=True
    )
    context.update({
        'adjust': adjust,
        'items': items,
        'can_approve': _permission_granted('administrative_management.supplies.manage', permission_codes) and adjust.status == 'pending_approval',
        'can_execute': _permission_granted('administrative_management.supplies.manage', permission_codes) and adjust.status == 'approved',
        'can_edit': adjust.status == 'draft' and adjust.created_by == request.user,
    })
    return render(request, "administrative_management/inventory_adjust_detail.html", context)


@login_required
def inventory_adjust_update(request, adjust_id):
    """编辑库存调整"""
    adjust = get_object_or_404(InventoryAdjust, id=adjust_id)
    
    # 权限检查：只能编辑自己的草稿调整
    if adjust.created_by != request.user:
        messages.error(request, '您没有权限编辑此库存调整')
        return redirect('admin_pages:inventory_adjust_detail', adjust_id=adjust_id)
    
    if adjust.status != 'draft':
        messages.error(request, '只能编辑草稿状态的库存调整')
        return redirect('admin_pages:inventory_adjust_detail', adjust_id=adjust_id)
    
    # 创建内联表单集
    InventoryAdjustItemFormSet = inlineformset_factory(
        InventoryAdjust, InventoryAdjustItem,
        form=InventoryAdjustItemForm,
        extra=2,
        can_delete=True,
    )
    
    if request.method == 'POST':
        form = InventoryAdjustForm(request.POST, instance=adjust)
        formset = InventoryAdjustItemFormSet(request.POST, instance=adjust)
        
        if form.is_valid() and formset.is_valid():
            form.save()
            formset.save()
            
            messages.success(request, f'库存调整 {adjust.adjust_number} 更新成功！')
            return redirect('admin_pages:inventory_adjust_detail', adjust_id=adjust.id)
    else:
        form = InventoryAdjustForm(instance=adjust)
        formset = InventoryAdjustItemFormSet(instance=adjust)
    
    context = _context(
        f"编辑库存调整 - {adjust.adjust_number}",
        "✏️",
        f"编辑库存调整 {adjust.adjust_number}",
        request=request,
        use_administrative_nav=True
    )
    context.update({
        'form': form,
        'formset': formset,
        'adjust': adjust,
        'is_create': False,
    })
    return render(request, "administrative_management/inventory_adjust_form.html", context)


@login_required
def inventory_adjust_approve(request, adjust_id):
    """审批库存调整"""
    permission_codes = get_user_permission_codes(request.user)
    if not _permission_granted('administrative_management.supplies.manage', permission_codes):
        messages.error(request, '您没有权限审批库存调整')
        return redirect('admin_pages:inventory_adjust_detail', adjust_id=adjust_id)
    
    adjust = get_object_or_404(InventoryAdjust, id=adjust_id)
    
    if adjust.status != 'pending_approval':
        messages.error(request, '只能审批待审批状态的库存调整')
        return redirect('admin_pages:inventory_adjust_detail', adjust_id=adjust_id)
    
    if request.method == 'POST':
        adjust.status = 'approved'
        adjust.approver = request.user
        adjust.approved_time = timezone.now()
        adjust.save()
        
        messages.success(request, f'库存调整 {adjust.adjust_number} 已批准')
        return redirect('admin_pages:inventory_adjust_detail', adjust_id=adjust_id)
    
    # 获取调整明细
    items = adjust.items.select_related('supply').order_by('supply__code')
    
    context = _context(
        f"审批库存调整 - {adjust.adjust_number}",
        "✅",
        f"审批库存调整 {adjust.adjust_number}",
        request=request,
        use_administrative_nav=True
    )
    context.update({
        'adjust': adjust,
        'items': items,
    })
    return render(request, "administrative_management/inventory_adjust_approve.html", context)


@login_required
def inventory_adjust_execute(request, adjust_id):
    """执行库存调整"""
    permission_codes = get_user_permission_codes(request.user)
    if not _permission_granted('administrative_management.supplies.manage', permission_codes):
        messages.error(request, '您没有权限执行库存调整')
        return redirect('admin_pages:inventory_adjust_detail', adjust_id=adjust_id)
    
    adjust = get_object_or_404(InventoryAdjust, id=adjust_id)
    
    if adjust.status != 'approved':
        messages.error(request, '只能执行已批准状态的库存调整')
        return redirect('admin_pages:inventory_adjust_detail', adjust_id=adjust_id)
    
    if request.method == 'POST':
        # 执行调整，更新库存
        for item in adjust.items.all():
            supply = item.supply
            supply.current_stock += item.adjust_quantity
            if supply.current_stock < 0:
                supply.current_stock = 0
            supply.save()
        
        adjust.status = 'executed'
        adjust.executed_by = request.user
        adjust.executed_time = timezone.now()
        adjust.save()
        
        messages.success(request, f'库存调整 {adjust.adjust_number} 已执行，库存已更新')
        return redirect('admin_pages:inventory_adjust_detail', adjust_id=adjust_id)
    
    # 获取调整明细
    items = adjust.items.select_related('supply').order_by('supply__code')
    
    context = _context(
        f"执行库存调整 - {adjust.adjust_number}",
        "⚙️",
        f"执行库存调整 {adjust.adjust_number}",
        request=request,
        use_administrative_nav=True
    )
    context.update({
        'adjust': adjust,
        'items': items,
    })
    return render(request, "administrative_management/inventory_adjust_execute.html", context)

