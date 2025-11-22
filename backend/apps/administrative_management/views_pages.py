from django.contrib.auth.decorators import login_required
from django.shortcuts import render, get_object_or_404, redirect
from django.contrib import messages
from django.db.models import Count, Sum, Q, F, Max
from django.core.paginator import Paginator
from django.urls import reverse, NoReverseMatch
from django.utils import timezone
from django.forms import inlineformset_factory
from datetime import timedelta
from decimal import Decimal

from backend.apps.system_management.services import get_user_permission_codes
from backend.core.views import HOME_NAV_STRUCTURE, _permission_granted
from .models import (
    OfficeSupply, SupplyPurchase, SupplyRequest,
    MeetingRoom, MeetingRoomBooking,
    Vehicle, VehicleBooking,
    ReceptionRecord,
    Announcement, AnnouncementRead,
    Seal, SealBorrowing,
    FixedAsset, AssetTransfer, AssetMaintenance,
    ExpenseReimbursement, ExpenseItem,
)
from .forms import (
    OfficeSupplyForm, MeetingRoomForm, VehicleForm, ReceptionRecordForm,
    AnnouncementForm, SealForm, FixedAssetForm, ExpenseReimbursementForm, ExpenseItemForm
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


def _build_full_top_nav(permission_set, user):
    """生成完整的顶部导航菜单"""
    full_nav = []
    
    for section in HOME_NAV_STRUCTURE:
        if not _permission_granted(section.get("permission"), permission_set):
            continue
        
        section_items = []
        for child in section.get("children", []):
            permission = child.get("permission")
            if permission and not _permission_granted(permission, permission_set):
                continue
            
            from django.urls import reverse, NoReverseMatch
            url_name = child.get("url_name")
            url = child.get("url")
            if url_name:
                try:
                    url = reverse(url_name)
                except NoReverseMatch:
                    url = url or '#'
            elif not url:
                url = '#'
            
            section_items.append({
                'label': child.get("label", ""),
                'url': url,
            })
        
        if section_items:
            full_nav.append({
                'section_label': section.get("label", ""),
                'section_icon': section.get("icon", ""),
                'items': section_items,
            })
    
    return full_nav


def _build_administrative_top_nav(permission_set):
    """生成行政管理专用的顶部导航菜单 - 8个子功能横向排列"""
    from django.urls import reverse, NoReverseMatch
    
    # 定义行政管理功能模块（从左到右的顺序）
    administrative_modules = [
        {
            'label': '办公用品',
            'url_name': 'admin_pages:supplies_management',
            'permission': 'administrative_management.supplies.view',
            'icon': '📦',
        },
        {
            'label': '会议室',
            'url_name': 'admin_pages:meeting_room_management',
            'permission': 'administrative_management.meeting_room.view',
            'icon': '🏛️',
        },
        {
            'label': '用车管理',
            'url_name': 'admin_pages:vehicle_management',
            'permission': 'administrative_management.vehicle.view',
            'icon': '🚗',
        },
        {
            'label': '接待管理',
            'url_name': 'admin_pages:reception_management',
            'permission': 'administrative_management.reception.view',
            'icon': '🤝',
        },
        {
            'label': '公告通知',
            'url_name': 'admin_pages:announcement_management',
            'permission': 'administrative_management.announcement.view',
            'icon': '📢',
        },
        {
            'label': '印章管理',
            'url_name': 'admin_pages:seal_management',
            'permission': 'administrative_management.seal.view',
            'icon': '🔐',
        },
        {
            'label': '固定资产',
            'url_name': 'admin_pages:asset_management',
            'permission': 'administrative_management.asset.view',
            'icon': '💼',
        },
        {
            'label': '报销管理',
            'url_name': 'admin_pages:expense_management',
            'permission': 'administrative_management.expense.view',
            'icon': '💰',
        },
    ]
    
    # 过滤有权限的模块，直接返回导航项（不是下拉菜单）
    nav_items = []
    for module in administrative_modules:
        if _permission_granted(module['permission'], permission_set):
            try:
                url = reverse(module['url_name'])
            except NoReverseMatch:
                url = '#'
            nav_items.append({
                'label': module['label'],
                'url': url,
                'icon': module.get('icon', ''),
            })
    
    return nav_items


def _context(page_title, page_icon, description, summary_cards=None, sections=None, request=None, use_administrative_nav=False):
    """构建页面上下文
    
    Args:
        use_administrative_nav: 如果为True，使用行政管理专用的顶部导航菜单
    """
    context = {
        "page_title": page_title,
        "page_icon": page_icon,
        "description": description,
        "summary_cards": summary_cards or [],
        "sections": sections or [],
    }
    
    if request and request.user.is_authenticated:
        permission_set = get_user_permission_codes(request.user)
        if use_administrative_nav:
            context['full_top_nav'] = _build_administrative_top_nav(permission_set)
        else:
            context['full_top_nav'] = _build_full_top_nav(permission_set, request.user)
    else:
        context['full_top_nav'] = []
    
    return context


@login_required
def administrative_home(request):
    """行政管理主页"""
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
                this_month_receptions = ReceptionRecord.objects.filter(
                    reception_date__gte=this_month_start
                ).count()
                total_expense = ReceptionRecord.objects.filter(
                    reception_date__gte=this_month_start
                ).aggregate(total=Sum('total_expense'))['total'] or Decimal('0')
                
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
        summary_cards=stats_cards,
        request=request,
        use_administrative_nav=True
    )
    return render(request, "administrative_management/home.html", context)


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
        paginator = Paginator(supplies, 20)
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
        
        summary_cards = [
            {"label": "用品总数", "value": total_supplies, "hint": "系统中维护的办公用品数量"},
            {"label": "在用用品", "value": active_supplies, "hint": "状态为启用的用品数量"},
            {"label": "低库存预警", "value": low_stock_count, "hint": "库存低于最低库存的用品数量"},
            {"label": "库存总值", "value": f"¥{total_value:,.2f}", "hint": "所有在用用品的库存总价值"},
        ]
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


@login_required
@login_required
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
        paginator = Paginator(rooms, 20)
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
        
        summary_cards = [
            {"label": "会议室总数", "value": total_rooms, "hint": "系统中维护的会议室数量"},
            {"label": "可用会议室", "value": available_rooms, "hint": "当前可用的会议室数量"},
            {"label": "启用会议室", "value": active_rooms, "hint": "状态为启用的会议室数量"},
            {"label": "今日预订", "value": today_bookings, "hint": "今日已预订的会议数量"},
        ]
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
        paginator = Paginator(vehicles, 20)
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
        
        summary_cards = [
            {"label": "车辆总数", "value": total_vehicles, "hint": "系统中维护的车辆数量"},
            {"label": "可用车辆", "value": available_vehicles, "hint": "当前可用的车辆数量"},
            {"label": "在用车辆", "value": active_vehicles, "hint": "状态为启用的车辆数量"},
            {"label": "今日用车", "value": today_bookings, "hint": "今日已批准或使用中的申请数量"},
        ]
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
        paginator = Paginator(receptions, 20)
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
        from .models import ReceptionExpense
        this_month_expenses = ReceptionExpense.objects.filter(
            expense_date__gte=this_month_start
        ).aggregate(total=Sum('amount'))['total'] or Decimal('0')
        
        summary_cards = [
            {"label": "接待总数", "value": total_receptions, "hint": "系统中维护的接待记录数量"},
            {"label": "本月接待", "value": this_month_count, "hint": "本月的接待记录数量"},
            {"label": "VIP接待", "value": vip_count, "hint": "VIP级别的接待记录数量"},
            {"label": "本月费用", "value": f"¥{float(this_month_expenses):,.2f}", "hint": "本月接待产生的费用总额"},
        ]
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
        announcements = Announcement.objects.select_related('publisher').order_by('-is_top', '-publish_date', '-publish_time')
        
        # 应用筛选条件
        if search:
            announcements = announcements.filter(
                Q(title__icontains=search) |
                Q(content__icontains=search)
            )
        if category:
            announcements = announcements.filter(category=category)
        if priority:
            announcements = announcements.filter(priority=priority)
        if is_active == 'true':
            announcements = announcements.filter(is_active=True)
        elif is_active == 'false':
            announcements = announcements.filter(is_active=False)
        if is_top == 'true':
            announcements = announcements.filter(is_top=True)
        
        # 分页
        paginator = Paginator(announcements, 20)
        page_number = request.GET.get('page', 1)
        page_obj = paginator.get_page(page_number)
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
        
        summary_cards = [
            {"label": "公告总数", "value": total_announcements, "hint": "系统中维护的公告数量"},
            {"label": "生效公告", "value": active_announcements, "hint": "状态为启用的公告数量"},
            {"label": "置顶公告", "value": top_announcements, "hint": "置顶的生效公告数量"},
            {"label": "本月发布", "value": this_month_count, "hint": "本月发布的公告数量"},
        ]
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
    announcement = get_object_or_404(Announcement, id=announcement_id)
    
    # 增加查看次数（仅首次查看）
    if request.user.is_authenticated:
        try:
            from .models import AnnouncementRead
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
    
    context = _context(
        f"公告详情 - {announcement.title}",
        "📢",
        f"查看公告通知的详细内容和阅读记录",
        request=request,
        use_administrative_nav=True
    )
    context.update({
        'announcement': announcement,
        'read_records': read_records,
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
        paginator = Paginator(seals, 20)
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
        
        summary_cards = [
            {"label": "印章总数", "value": total_seals, "hint": "系统中维护的印章数量"},
            {"label": "可用印章", "value": available_seals, "hint": "当前可用的印章数量"},
            {"label": "借用中", "value": borrowed_seals, "hint": "当前借用中的印章数量"},
            {"label": "启用印章", "value": active_seals, "hint": "状态为启用的印章数量"},
        ]
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
    
    # 获取借用记录
    try:
        borrowings = SealBorrowing.objects.filter(seal=seal).select_related(
            'borrower', 'approver', 'returned_by'
        ).order_by('-borrow_date')[:10]
    except Exception:
        borrowings = []
    
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
        paginator = Paginator(assets, 20)
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
        
        summary_cards = [
            {"label": "资产总数", "value": total_assets, "hint": "系统中维护的固定资产数量"},
            {"label": "使用中", "value": in_use_assets, "hint": "当前使用中的资产数量"},
            {"label": "启用资产", "value": active_assets, "hint": "状态为启用的资产数量"},
            {"label": "资产总值", "value": f"¥{total_value:,.2f}", "hint": "所有启用资产的总价值"},
        ]
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
    })
    return render(request, "administrative_management/asset_detail.html", context)


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
        paginator = Paginator(expenses, 20)
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
        
        summary_cards = [
            {"label": "报销总数", "value": total_expenses, "hint": "系统中维护的报销申请数量"},
            {"label": "待审批", "value": pending_count, "hint": "待审批的报销申请数量"},
            {"label": "已批准", "value": approved_count, "hint": "已批准的报销申请数量"},
            {"label": "总金额", "value": f"¥{float(total_amount):,.2f}", "hint": "报销申请的总金额"},
        ]
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

