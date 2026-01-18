"""
档案管理模块页面视图
"""
from django.contrib.auth.decorators import login_required
from django.shortcuts import render, get_object_or_404, redirect
from django.contrib import messages
from django.core.paginator import Paginator
from django.db.models import Q, Count, F
from django.utils import timezone
from datetime import timedelta

from backend.apps.system_management.services import get_user_permission_codes
from backend.core.views import HOME_NAV_STRUCTURE, _permission_granted, _build_full_top_nav
from django.urls import reverse, NoReverseMatch
from backend.apps.archive_management.models import (
    ArchiveCategory,
    ArchiveProjectArchive,
    ProjectArchiveDocument,
    ArchivePushRecord,
    AdministrativeArchive,
    ArchiveBorrow,
    ArchiveDestroy,
    ArchiveStorageRoom,
    ArchiveLocation,
    ArchiveShelf,
    ArchiveInventory,
)
from .services import ArchiveOperationLogService


# 使用统一的顶部导航菜单生成函数
from backend.core.views import _build_full_top_nav


def _build_archive_sidebar_nav(permission_set, request_path=None, active_id=None):
    """生成档案管理左侧菜单（兼容侧边栏模板格式）"""
    nav_items = []
    
    # 档案管理首页
    try:
        home_url = reverse('archive_management:archive_management_home')
        is_home_active = (
            request_path == home_url or 
            request_path == reverse('archive_management:archive_home') or
            active_id == 'archive_home'
        )
        nav_items.append({
            'label': '项目归档',
            'icon': '📁',
            'url': home_url,
            'active': is_home_active,
            'is_home': True,
        })
    except NoReverseMatch:
        pass
    
    # 项目归档列表（保留作为子菜单项）
    try:
        project_archive_url = reverse('archive_management:project_archive_list')
        is_project_archive_active = (
            request_path == project_archive_url or
            active_id == 'project_archive_list'
        )
    except NoReverseMatch:
        project_archive_url = None
        is_project_archive_active = False
    
    # 项目档案分组
    project_archive_items = []
    
    if _permission_granted('archive_management.view', permission_set):
        try:
            document_upload_url = reverse('archive_management:project_document_upload')
            project_archive_items.append({
                'label': '文档上传',
                'icon': '➕',
                'url': document_upload_url,
                'active': request_path == document_upload_url,
            })
        except NoReverseMatch:
            pass
        
        try:
            document_list_url = reverse('archive_management:project_document_list')
            project_archive_items.append({
                'label': '项目文档',
                'icon': '📄',
                'url': document_list_url,
                'active': request_path == document_list_url,
            })
        except NoReverseMatch:
            pass
        
        # 图纸归档（待实现）
        try:
            drawing_archive_url = reverse('archive_management:project_drawing_archive_list')
            project_archive_items.append({
                'label': '图纸归档',
                'icon': '📐',
                'url': drawing_archive_url,
                'active': request_path == drawing_archive_url,
            })
        except NoReverseMatch:
            # 如果路由不存在，添加占位菜单项（待实现）
            project_archive_items.append({
                'label': '图纸归档',
                'icon': '📐',
                'url': '#',
                'active': False,
            })
        
        # 交付归档（手动归档，待实现）
        try:
            delivery_archive_url = reverse('archive_management:project_delivery_archive_list')
            project_archive_items.append({
                'label': '交付归档',
                'icon': '📦',
                'url': delivery_archive_url,
                'active': request_path == delivery_archive_url,
            })
        except NoReverseMatch:
            # 如果路由不存在，添加占位菜单项（待实现）
            project_archive_items.append({
                'label': '交付归档',
                'icon': '📦',
                'url': '#',
                'active': False,
            })
        
        try:
            search_url = reverse('archive_management:archive_search') + '?type=project'
            project_archive_items.append({
                'label': '项目档案查询',
                'icon': '🔍',
                'url': search_url,
                'active': request_path and 'archive/search' in request_path and 'type=project' in request_path,
            })
        except NoReverseMatch:
            pass
    
    if project_archive_items:
        has_active = any(item.get('active') for item in project_archive_items)
        nav_items.append({
            'label': '项目档案',
            'icon': '📄',
            'children': project_archive_items,  # 使用 children 而不是 items
            'expanded': has_active,  # 如果有激活项，默认展开
            'active': has_active,
        })
    
    # 行政档案分组
    administrative_archive_items = []
    
    if _permission_granted('archive_management.view', permission_set):
        try:
            admin_archive_url = reverse('archive_management:administrative_archive_list')
            administrative_archive_items.append({
                'label': '行政档案',
                'icon': '📋',
                'url': admin_archive_url,
                'active': request_path == admin_archive_url,
            })
        except NoReverseMatch:
            pass
        
        # 注意：档案分类已移到独立分组，这里不再重复添加
        
        try:
            borrow_url = reverse('archive_management:archive_borrow_list')
            administrative_archive_items.append({
                'label': '档案借阅',
                'icon': '📖',
                'url': borrow_url,
                'active': request_path == borrow_url,
            })
        except NoReverseMatch:
            pass
        
        try:
            destroy_url = reverse('archive_management:archive_destroy_list')
            administrative_archive_items.append({
                'label': '档案销毁',
                'icon': '🗑️',
                'url': destroy_url,
                'active': request_path == destroy_url,
            })
        except NoReverseMatch:
            pass
        
        # 档案归还（待实现）
        try:
            return_url = reverse('archive_management:archive_borrow_return_list')
            administrative_archive_items.append({
                'label': '档案归还',
                'icon': '📥',
                'url': return_url,
                'active': request_path == return_url,
            })
        except NoReverseMatch:
            # 如果路由不存在，添加占位菜单项（待实现）
            administrative_archive_items.append({
                'label': '档案归还',
                'icon': '📥',
                'url': '#',
                'active': False,
            })
    
    if administrative_archive_items:
        has_active = any(item.get('active') for item in administrative_archive_items)
        nav_items.append({
            'label': '行政档案',
            'icon': '📋',
            'children': administrative_archive_items,  # 使用 children 而不是 items
            'expanded': has_active,  # 如果有激活项，默认展开
            'active': has_active,
        })
    
    # 档案库管理分组
    storage_items = []
    
    if _permission_granted('archive_management.view', permission_set):
        try:
            storage_list_url = reverse('archive_management:archive_storage_list')
            storage_items.append({
                'label': '库房管理',
                'icon': '🏢',
                'url': reverse('archive_management:archive_storage_room_list'),
                'active': request_path and 'archive/storage/room' in request_path,
            })
        except NoReverseMatch:
            pass
        
        try:
            storage_items.append({
                'label': '位置管理',
                'icon': '📍',
                'url': reverse('archive_management:archive_location_list'),
                'active': request_path and 'archive/storage/location' in request_path,
            })
        except NoReverseMatch:
            pass
        
        try:
            storage_items.append({
                'label': '档案上架',
                'icon': '📚',
                'url': reverse('archive_management:archive_shelf_list'),
                'active': request_path and 'archive/storage/shelf' in request_path,
            })
        except NoReverseMatch:
            pass
        
        try:
            storage_items.append({
                'label': '档案盘点',
                'icon': '📊',
                'url': reverse('archive_management:archive_inventory_list'),
                'active': request_path and 'archive/storage/inventory' in request_path,
            })
        except NoReverseMatch:
            pass
    
    if storage_items:
        has_active = any(item.get('active') for item in storage_items)
        nav_items.append({
            'label': '档案库管理',
            'icon': '📚',
            'children': storage_items,  # 使用 children 而不是 items
            'expanded': has_active,  # 如果有激活项，默认展开
            'active': has_active,
        })
    
    # 档案分类（独立分组）
    category_items = []
    if _permission_granted('archive_management.view', permission_set):
        try:
            category_url = reverse('archive_management:archive_category_list')
            category_items.append({
                'label': '分类管理',
                'icon': '🗂️',
                'url': category_url,
                'active': request_path == category_url,
            })
        except NoReverseMatch:
            pass
        
        # 分类规则（待实现）
        try:
            category_rule_url = reverse('archive_management:archive_category_rule')
            category_items.append({
                'label': '分类规则',
                'icon': '⚙️',
                'url': category_rule_url,
                'active': request_path == category_rule_url,
            })
        except NoReverseMatch:
            # 如果路由不存在，添加占位菜单项（待实现）
            category_items.append({
                'label': '分类规则',
                'icon': '⚙️',
                'url': '#',
                'active': False,
            })
    
    if category_items:
        has_active = any(item.get('active') for item in category_items)
        nav_items.append({
            'label': '档案分类',
            'icon': '🗂️',
            'children': category_items,  # 使用 children 而不是 items
            'expanded': has_active,  # 如果有激活项，默认展开
            'active': has_active,
        })
    
    # 档案安全分组（待实现）
    security_items = []
    if _permission_granted('archive_management.view', permission_set):
        # 权限管理（待实现）
        try:
            permission_url = reverse('archive_management:archive_security_permission')
            security_items.append({
                'label': '权限管理',
                'icon': '🔐',
                'url': permission_url,
                'active': request_path == permission_url,
            })
        except NoReverseMatch:
            security_items.append({
                'label': '权限管理',
                'icon': '🔐',
                'url': '#',
                'active': False,
            })
        
        # 访问控制（待实现）
        try:
            access_url = reverse('archive_management:archive_security_access')
            security_items.append({
                'label': '访问控制',
                'icon': '🛡️',
                'url': access_url,
                'active': request_path == access_url,
            })
        except NoReverseMatch:
            security_items.append({
                'label': '访问控制',
                'icon': '🛡️',
                'url': '#',
                'active': False,
            })
        
        # 操作日志（待实现）
        try:
            log_url = reverse('archive_management:archive_security_log')
            security_items.append({
                'label': '操作日志',
                'icon': '📝',
                'url': log_url,
                'active': request_path == log_url,
            })
        except NoReverseMatch:
            security_items.append({
                'label': '操作日志',
                'icon': '📝',
                'url': '#',
                'active': False,
            })
        
        # 安全审计（待实现）
        try:
            audit_url = reverse('archive_management:archive_security_audit')
            security_items.append({
                'label': '安全审计',
                'icon': '🔍',
                'url': audit_url,
                'active': request_path == audit_url,
            })
        except NoReverseMatch:
            security_items.append({
                'label': '安全审计',
                'icon': '🔍',
                'url': '#',
                'active': False,
            })
    
    if security_items:
        has_active = any(item.get('active') for item in security_items)
        nav_items.append({
            'label': '档案安全',
            'icon': '🔐',
            'children': security_items,  # 使用 children 而不是 items
            'expanded': has_active,  # 如果有激活项，默认展开
            'active': has_active,
        })
    
    # 档案检索分组（增强功能）
    search_items = []
    if _permission_granted('archive_management.view', permission_set):
        # 全文检索（待实现）
        try:
            fulltext_url = reverse('archive_management:archive_search_fulltext')
            search_items.append({
                'label': '全文检索',
                'icon': '🔍',
                'url': fulltext_url,
                'active': request_path == fulltext_url,
            })
        except NoReverseMatch:
            search_items.append({
                'label': '全文检索',
                'icon': '🔍',
                'url': '#',
                'active': False,
            })
        
        # 高级检索（待实现）
        try:
            advanced_url = reverse('archive_management:archive_search_advanced')
            search_items.append({
                'label': '高级检索',
                'icon': '🔎',
                'url': advanced_url,
                'active': request_path == advanced_url,
            })
        except NoReverseMatch:
            search_items.append({
                'label': '高级检索',
                'icon': '🔎',
                'url': '#',
                'active': False,
            })
        
        # 检索历史（待实现）
        try:
            history_url = reverse('archive_management:archive_search_history')
            search_items.append({
                'label': '检索历史',
                'icon': '📜',
                'url': history_url,
                'active': request_path == history_url,
            })
        except NoReverseMatch:
            search_items.append({
                'label': '检索历史',
                'icon': '📜',
                'url': '#',
                'active': False,
            })
        
        # 档案查询（基础查询，已实现）
        try:
            search_url = reverse('archive_management:archive_search')
            search_items.append({
                'label': '档案查询',
                'icon': '🔍',
                'url': search_url,
                'active': request_path == search_url,
            })
        except NoReverseMatch:
            pass
    
    if search_items:
        nav_items.append({
            'label': '档案检索',
            'icon': '🔍',
            'children': search_items,  # 使用 children 而不是 items
            'expanded': any(item.get('active') for item in search_items),  # 如果有激活项，默认展开
            'active': any(item.get('active') for item in search_items),
        })
    
    # 档案数字化分组（待实现）
    digitization_items = []
    if _permission_granted('archive_management.view', permission_set):
        # 数字化申请（待实现）
        try:
            apply_url = reverse('archive_management:archive_digitization_apply_list')
            digitization_items.append({
                'label': '数字化申请',
                'icon': '📋',
                'url': apply_url,
                'active': request_path == apply_url,
            })
        except NoReverseMatch:
            digitization_items.append({
                'label': '数字化申请',
                'icon': '📋',
                'url': '#',
                'active': False,
            })
        
        # 数字化处理（待实现）
        try:
            process_url = reverse('archive_management:archive_digitization_process_list')
            digitization_items.append({
                'label': '数字化处理',
                'icon': '⚙️',
                'url': process_url,
                'active': request_path == process_url,
            })
        except NoReverseMatch:
            digitization_items.append({
                'label': '数字化处理',
                'icon': '⚙️',
                'url': '#',
                'active': False,
            })
        
        # 数字化成果（待实现）
        try:
            result_url = reverse('archive_management:archive_digitization_result_list')
            digitization_items.append({
                'label': '数字化成果',
                'icon': '📦',
                'url': result_url,
                'active': request_path == result_url,
            })
        except NoReverseMatch:
            digitization_items.append({
                'label': '数字化成果',
                'icon': '📦',
                'url': '#',
                'active': False,
            })
    
    if digitization_items:
        nav_items.append({
            'label': '档案数字化',
            'icon': '💾',
            'children': digitization_items,  # 使用 children 而不是 items
            'expanded': any(item.get('active') for item in digitization_items),  # 如果有激活项，默认展开
            'active': any(item.get('active') for item in digitization_items),
        })
    
    # 档案统计（完善功能）
    statistics_items = []
    if _permission_granted('archive_management.view', permission_set):
        # 档案统计（基础统计，已实现）
        try:
            statistics_url = reverse('archive_management:archive_statistics')
            statistics_items.append({
                'label': '档案统计',
                'icon': '📊',
                'url': statistics_url,
                'active': request_path == statistics_url,
            })
        except NoReverseMatch:
            pass
        
        # 利用统计（待实现）
        try:
            usage_url = reverse('archive_management:archive_statistics_usage')
            statistics_items.append({
                'label': '利用统计',
                'icon': '📈',
                'url': usage_url,
                'active': request_path == usage_url,
            })
        except NoReverseMatch:
            statistics_items.append({
                'label': '利用统计',
                'icon': '📈',
                'url': '#',
                'active': False,
            })
        
        # 保管统计（待实现）
        try:
            storage_stat_url = reverse('archive_management:archive_statistics_storage')
            statistics_items.append({
                'label': '保管统计',
                'icon': '📦',
                'url': storage_stat_url,
                'active': request_path == storage_stat_url,
            })
        except NoReverseMatch:
            statistics_items.append({
                'label': '保管统计',
                'icon': '📦',
                'url': '#',
                'active': False,
            })
    
    if statistics_items:
        nav_items.append({
            'label': '档案统计',
            'icon': '📊',
            'children': statistics_items,  # 使用 children 而不是 items
            'expanded': any(item.get('active') for item in statistics_items),  # 如果有激活项，默认展开
            'active': any(item.get('active') for item in statistics_items),
        })
    
    return nav_items


def _context(page_title, page_icon, description, summary_cards=None, sections=None, request=None):
    context = {
        "page_title": page_title,
        "page_icon": page_icon,
        "description": description,
        "summary_cards": summary_cards or [],
        "sections": sections or [],
    }
    if request and request.user.is_authenticated:
        permission_set = get_user_permission_codes(request.user)
        context['full_top_nav'] = _build_full_top_nav(permission_set, request.user)
        context['sidebar_nav'] = _build_archive_sidebar_nav(permission_set, request.path)
    else:
        context['full_top_nav'] = []
        context['sidebar_nav'] = []
    
    # 为所有可能的侧边栏变量设置默认值，避免模板错误
    # 这些变量可能在其他模块的模板中被引用
    context.setdefault('plan_menu', [])
    context.setdefault('module_sidebar_nav', [])
    context.setdefault('sidebar_nav', [])
    context.setdefault('customer_menu', [])
    context.setdefault('sidebar_nav', [])
    context.setdefault('sidebar_nav', [])
    context.setdefault('sidebar_nav', [])
    context.setdefault('sidebar_nav', [])
    context.setdefault('sidebar_nav', [])
    context.setdefault('sidebar_nav', [])
    
    return context


@login_required
def archive_management_home(request):
    """档案管理首页 - 数据展示中心"""
    from django.db.models import Avg, Count
    from datetime import datetime
    from backend.apps.archive_management.models import (
        ArchiveProjectArchive,
        AdministrativeArchive,
        ArchiveBorrow,
        ProjectArchiveDocument,
    )
    
    permission_set = get_user_permission_codes(request.user)
    if not _permission_granted('archive_management.view', permission_set):
        from django.http import HttpResponseForbidden
        return HttpResponseForbidden("无权限访问档案管理")
    
    now = timezone.now()
    today = now.date()
    this_month_start = today.replace(day=1)
    seven_days_ago = today - timedelta(days=7)
    
    context = {}
    
    try:
        # ========== 核心指标卡片 ==========
        core_cards = []
        
        # 项目归档统计
        all_project_archives = ArchiveProjectArchive.objects.all()
        total_project_archives = all_project_archives.count()
        pending_project_archives = all_project_archives.filter(status='pending').count()
        approving_project_archives = all_project_archives.filter(status='approving').count()
        archived_project_archives = all_project_archives.filter(status='archived').count()
        rejected_project_archives = all_project_archives.filter(status='rejected').count()
        this_month_project_archives = all_project_archives.filter(created_time__gte=this_month_start).count()
        
        # 行政档案统计
        all_administrative_archives = AdministrativeArchive.objects.all()
        total_administrative_archives = all_administrative_archives.count()
        archived_administrative_archives = all_administrative_archives.filter(status='archived').count()
        borrowed_administrative_archives = all_administrative_archives.filter(status='borrowed').count()
        
        # 档案借阅统计
        all_borrows = ArchiveBorrow.objects.all()
        total_borrows = all_borrows.count()
        pending_borrows = all_borrows.filter(status='pending').count()
        out_borrows = all_borrows.filter(status='out').count()
        overdue_borrows = all_borrows.filter(status='overdue').count()
        
        # 项目文档统计
        all_project_documents = ProjectArchiveDocument.objects.all()
        total_project_documents = all_project_documents.count()
        
        # 卡片1：项目归档总数
        core_cards.append({
            'label': '项目归档',
            'icon': '📁',
            'value': str(total_project_archives),
            'subvalue': f'待归档 {pending_project_archives} | 审批中 {approving_project_archives} | 已归档 {archived_project_archives}',
            'url': reverse('archive_management:project_archive_list'),
            'variant': 'secondary'
        })
        
        # 卡片2：待归档项目
        core_cards.append({
            'label': '待归档项目',
            'icon': '📋',
            'value': str(pending_project_archives),
            'subvalue': f'等待归档审批',
            'url': reverse('archive_management:project_archive_list') + '?status=pending',
            'variant': 'dark' if pending_project_archives > 0 else 'secondary'
        })
        
        # 卡片3：已归档项目
        core_cards.append({
            'label': '已归档项目',
            'icon': '✅',
            'value': str(archived_project_archives),
            'subvalue': f'本月归档 {this_month_project_archives} 个',
            'url': reverse('archive_management:project_archive_list') + '?status=archived',
            'variant': 'secondary'
        })
        
        # 卡片4：行政档案
        core_cards.append({
            'label': '行政档案',
            'icon': '📄',
            'value': str(total_administrative_archives),
            'subvalue': f'已归档 {archived_administrative_archives} | 已借出 {borrowed_administrative_archives}',
            'url': reverse('archive_management:administrative_archive_list'),
            'variant': 'secondary'
        })
        
        # 卡片5：档案借阅
        core_cards.append({
            'label': '档案借阅',
            'icon': '📖',
            'value': str(total_borrows),
            'subvalue': f'待审批 {pending_borrows} | 已借出 {out_borrows} | 已逾期 {overdue_borrows}',
            'url': reverse('archive_management:archive_borrow_list'),
            'variant': 'dark' if overdue_borrows > 0 else 'secondary'
        })
        
        # 卡片6：项目文档
        core_cards.append({
            'label': '项目文档',
            'icon': '📚',
            'value': str(total_project_documents),
            'subvalue': f'项目文档总数',
            'url': reverse('archive_management:project_document_list'),
            'variant': 'secondary'
        })
        
        context['core_cards'] = core_cards
        
        # ========== 风险预警 ==========
        risk_warnings = []
        
        # 逾期借阅
        overdue_borrow_list = all_borrows.filter(status='overdue').select_related('borrower')[:5]
        for borrow in overdue_borrow_list:
            borrower_name = _format_user_display(borrow.borrower) if borrow.borrower else '未知'
            risk_warnings.append({
                'type': 'overdue',
                'title': f'借阅单号：{borrow.borrow_number}',
                'responsible': borrower_name,
                'days': 0,  # 可以计算逾期天数
                'url': reverse('archive_management:archive_borrow_detail', args=[borrow.id])
            })
        
        # 待归档项目（超过7天）
        stale_project_archives = all_project_archives.filter(
            status__in=['pending', 'approving'],
            created_time__lt=timezone.make_aware(datetime.combine(seven_days_ago, datetime.min.time()))
        ).select_related('applicant')[:5]
        
        for archive in stale_project_archives:
            days_since_create = (today - archive.created_time.date()).days
            applicant_name = _format_user_display(archive.applicant) if archive.applicant else '未知'
            risk_warnings.append({
                'type': 'stale',
                'title': archive.archive_number,
                'responsible': applicant_name,
                'days': days_since_create,
                'url': reverse('archive_management:project_archive_detail', args=[archive.id])
            })
        
        context['risk_warnings'] = risk_warnings[:5]
        context['stale_archives_count'] = all_project_archives.filter(
            status__in=['pending', 'approving'],
            created_time__lt=timezone.make_aware(datetime.combine(seven_days_ago, datetime.min.time()))
        ).count()
        context['overdue_borrows_count'] = overdue_borrows
        
        # ========== 待办事项 ==========
        todo_items = []
        
        # 待归档项目
        pending_archive_list = all_project_archives.filter(status='pending').select_related('applicant')[:5]
        for archive in pending_archive_list:
            applicant_name = _format_user_display(archive.applicant) if archive.applicant else '未知'
            todo_items.append({
                'type': 'archive',
                'title': archive.archive_number,
                'archive_number': archive.archive_number,
                'responsible': applicant_name,
                'url': reverse('archive_management:project_archive_detail', args=[archive.id])
            })
        
        # 待审批借阅
        pending_borrow_list = all_borrows.filter(status='pending').select_related('borrower')[:5]
        for borrow in pending_borrow_list:
            borrower_name = _format_user_display(borrow.borrower) if borrow.borrower else '未知'
            todo_items.append({
                'type': 'borrow',
                'title': f'借阅单号：{borrow.borrow_number}',
                'archive_number': borrow.borrow_number,
                'responsible': borrower_name,
                'url': reverse('archive_management:archive_borrow_detail', args=[borrow.id])
            })
        
        context['todo_items'] = todo_items[:10]
        context['pending_approval_count'] = pending_project_archives + pending_borrows
        context['todo_summary_url'] = reverse('archive_management:project_archive_list') + '?status=pending'
        
        # ========== 我的工作 ==========
        my_work = {}
        
        # 我申请的项目归档
        my_applied_archives = all_project_archives.filter(applicant=request.user).order_by('-created_time')[:3]
        my_work['my_archives'] = [{
            'title': archive.archive_number,
            'status': archive.get_status_display(),
            'url': reverse('archive_management:project_archive_detail', args=[archive.id])
        } for archive in my_applied_archives]
        my_work['my_archives_count'] = all_project_archives.filter(applicant=request.user).count()
        
        # 我借阅的档案
        my_borrows = all_borrows.filter(borrower=request.user).order_by('-created_time')[:3]
        my_work['my_borrows'] = [{
            'title': f'借阅单号：{borrow.borrow_number}',
            'status': borrow.get_status_display(),
            'url': reverse('archive_management:archive_borrow_detail', args=[borrow.id])
        } for borrow in my_borrows]
        my_work['my_borrows_count'] = all_borrows.filter(borrower=request.user).count()
        
        my_work['summary_url'] = reverse('archive_management:project_archive_list')
        
        context['my_work'] = my_work
        
        # ========== 最近活动 ==========
        recent_activities = {}
        
        # 最近创建的项目归档
        recent_project_archives = all_project_archives.select_related('applicant').order_by('-created_time')[:5]
        recent_activities['recent_archives'] = [{
            'title': archive.archive_number,
            'creator': _format_user_display(archive.applicant),
            'time': archive.created_time,
            'url': reverse('archive_management:project_archive_detail', args=[archive.id])
        } for archive in recent_project_archives]
        
        # 最近创建的借阅
        recent_borrows = all_borrows.select_related('borrower').order_by('-created_time')[:5]
        recent_activities['recent_borrows'] = [{
            'title': f'借阅单号：{borrow.borrow_number}',
            'creator': _format_user_display(borrow.borrower),
            'time': borrow.created_time,
            'url': reverse('archive_management:archive_borrow_detail', args=[borrow.id])
        } for borrow in recent_borrows]
        
        context['recent_activities'] = recent_activities
        
    except Exception as e:
        import logging
        logger = logging.getLogger(__name__)
        logger.exception('获取档案管理统计数据失败: %s', str(e))
        context.setdefault('core_cards', [])
        context.setdefault('risk_warnings', [])
        context.setdefault('todo_items', [])
        context.setdefault('my_work', {})
        context.setdefault('recent_activities', {})
    
    # 顶部操作栏
    top_actions = []
    if _permission_granted('archive_management.create', permission_set):
        try:
            top_actions.append({
                'label': '创建项目归档',
                'url': reverse('archive_management:project_archive_create'),
                'icon': '➕'
            })
        except Exception:
            pass
    
    context['top_actions'] = top_actions
    
    # 构建上下文
    page_context = _context(
        "档案管理",
        "📁",
        "数据展示中心 - 集中展示档案关键指标、状态与风险",
        request=request,
    )
    
    # 设置侧边栏导航
    archive_sidebar_nav = _build_archive_sidebar_nav(permission_set, request.path, active_id='archive_home')
    page_context['sidebar_nav'] = archive_sidebar_nav
    page_context['sidebar_title'] = '档案管理'
    page_context['sidebar_subtitle'] = 'Archive Management'
    
    # 合并所有数据
    page_context.update(context)
    
    return render(request, "archive_management/home.html", page_context)


def _format_user_display(user, default='—'):
    """格式化用户显示名称"""
    if not user:
        return default
    if hasattr(user, 'get_full_name') and user.get_full_name():
        return user.get_full_name()
    return user.username if hasattr(user, 'username') else str(user)


@login_required
def archive_list(request):
    """档案管理首页 - 新版本：使用左侧菜单布局"""
    permission_set = get_user_permission_codes(request.user)
    
    # 权限检查
    if not _permission_granted('archive_management.view', permission_set):
        from django.http import HttpResponseForbidden
        return HttpResponseForbidden("无权限访问档案管理")
    
    # 新版本：直接跳转到项目归档列表页（首页=项目归档列表）
    return redirect('archive_management:project_archive_list')
    
    # ==================== 老版本代码（已注释）====================
    # 老版本使用卡片式布局的首页，已改为使用左侧菜单布局
    # # 统计数据
    # try:
    #     project_archive_count = ArchiveProjectArchive.objects.filter(status='archived').count()
    #     project_document_count = ProjectArchiveDocument.objects.filter(status='archived').count()
    #     administrative_archive_count = AdministrativeArchive.objects.filter(status='archived').count()
    #     borrow_count = ArchiveBorrow.objects.filter(status='out').count()
    # except:
    #     project_archive_count = 0
    #     project_document_count = 0
    #     administrative_archive_count = 0
    #     borrow_count = 0
    # 
    # context = _context(
    #     "档案管理",
    #     "📁",
    #     "统一管理所有档案，包括项目档案和行政档案。实现档案的全生命周期管理。",
    #     request=request,
    #     summary_cards=[
    #         {"label": "项目归档", "value": str(project_archive_count), "hint": "已归档的项目数量"},
    #         {"label": "项目文档", "value": str(project_document_count), "hint": "项目档案文档数量"},
    #         {"label": "行政档案", "value": str(administrative_archive_count), "hint": "行政档案数量"},
    #         {"label": "借出档案", "value": str(borrow_count), "hint": "当前借出的档案数量"},
    #     ],
    #     sections=[
    #         {
    #             "title": "项目档案",
    #             "description": "管理项目档案和文档归档。",
    #             "items": [
    #                 {"label": "项目归档", "description": "项目归档管理。", "url": "/archive/project/", "icon": "📄"},
    #                 {"label": "文档上传", "description": "上传项目文档。", "url": "/archive/project/document/upload/", "icon": "📤"},
    #                 {"label": "项目档案查询", "description": "查询项目档案。", "url": "/archive/search/?type=project", "icon": "🔍"},
    #             ],
    #         },
    #         {
    #             "title": "行政档案",
    #             "description": "管理行政档案的归档、借阅、销毁。",
    #             "items": [
    #                 {"label": "行政档案", "description": "行政档案管理。", "url": "/archive/administrative/", "icon": "📋"},
    #                 {"label": "档案借阅", "description": "档案借阅管理。", "url": "/archive/borrow/", "icon": "📖"},
    #                 {"label": "档案销毁", "description": "档案销毁管理。", "url": "/archive/destroy/", "icon": "🗑️"},
    #             ],
    #         },
    #         {
    #             "title": "档案库管理",
    #             "description": "管理档案库房、位置、上架、盘点。",
    #             "items": [
    #                 {"label": "库房管理", "description": "档案库房管理。", "url": "/archive/storage/room/", "icon": "🏢"},
    #                 {"label": "位置管理", "description": "档案位置管理。", "url": "/archive/storage/location/", "icon": "📍"},
    #                 {"label": "档案盘点", "description": "档案盘点管理。", "url": "/archive/storage/inventory/", "icon": "📊"},
    #             ],
    #         },
    #     ],
    # )
    # return render(request, "archive_management/archive_list.html", context)
    # ==================== 老版本代码结束 ====================


@login_required
def project_archive_list(request):
    """项目归档列表"""
    permission_set = get_user_permission_codes(request.user)
    if not _permission_granted('archive_management.view', permission_set):
        from django.http import HttpResponseForbidden
        return HttpResponseForbidden("无权限访问")
    
    queryset = ArchiveProjectArchive.objects.all().select_related('project', 'applicant')
    
    # 筛选
    status = request.GET.get('status', '')
    if status:
        queryset = queryset.filter(status=status)
    
    search = request.GET.get('search', '')
    if search:
        queryset = queryset.filter(
            Q(archive_number__icontains=search) |
            Q(project__name__icontains=search) |
            Q(project__project_number__icontains=search)
        )
    
    # 排序
    queryset = queryset.order_by('-created_time')
    
    # 分页（每页20条）
    paginator = Paginator(queryset, 20)
    page_number = request.GET.get('page', 1)
    try:
        page = paginator.get_page(page_number)
    except:
        page = paginator.get_page(1)
    
    # 统计数据（用于统计卡片）
    base_queryset = ArchiveProjectArchive.objects.all()
    if not _permission_granted('archive_management.view_all', permission_set):
        # 根据权限过滤（如果需要）
        pass
    
    total_count = base_queryset.count()
    pending_count = base_queryset.filter(status='pending').count()
    approving_count = base_queryset.filter(status='approving').count()
    archived_count = base_queryset.filter(status='archived').count()
    rejected_count = base_queryset.filter(status='rejected').count()
    
    # 生成左侧菜单
    archive_sidebar_nav = _build_archive_sidebar_nav(permission_set, request.path)
    
    # 使用 _context 函数获取基础上下文（包含所有侧边栏变量的默认值）
    context = _context(
        "项目归档",
        "📁",
        "管理项目归档记录，支持筛选和搜索",
        request=request,
    )
    
    # 更新上下文变量
    context.update({
        'page': page,
        'status': status,
        'status_filter': status,  # 兼容模板中的变量名
        'search': search,
        'total_count': total_count,
        'pending_count': pending_count,
        'approving_count': approving_count,
        'archived_count': archived_count,
        'rejected_count': rejected_count,
        'archive_sidebar_nav': archive_sidebar_nav,
        'module_sidebar_nav': archive_sidebar_nav,  # 兼容模板中的变量名
        'sidebar_title': '档案管理',  # 侧边栏标题
        'sidebar_subtitle': 'Archive Management',  # 侧边栏副标题
    })
    return render(request, "archive_management/project_archive_list.html", context)


@login_required
def project_archive_detail(request, pk):
    """项目归档详情"""
    permission_set = get_user_permission_codes(request.user)
    if not _permission_granted('archive_management.view', permission_set):
        from django.http import HttpResponseForbidden
        return HttpResponseForbidden("无权限访问")
    
    archive = get_object_or_404(ArchiveProjectArchive.objects.select_related('project', 'applicant', 'executor'), pk=pk)
    documents = ProjectArchiveDocument.objects.filter(project_archive=archive).select_related('category', 'uploaded_by')
    
    context = {
        'archive': archive,
        'documents': documents,
        'full_top_nav': _build_full_top_nav(permission_set, request.user),
        'archive_sidebar_nav': _build_archive_sidebar_nav(permission_set, request.path),
    }
    return render(request, "archive_management/project_archive_detail.html", context)


@login_required
def project_document_list(request):
    """项目档案文档列表"""
    permission_set = get_user_permission_codes(request.user)
    if not _permission_granted('archive_management.view', permission_set):
        from django.http import HttpResponseForbidden
        return HttpResponseForbidden("无权限访问")
    
    queryset = ProjectArchiveDocument.objects.all().select_related('project', 'category', 'uploaded_by')
    
    # 筛选
    document_type = request.GET.get('document_type', '')
    if document_type:
        queryset = queryset.filter(document_type=document_type)
    
    status = request.GET.get('status', '')
    if status:
        queryset = queryset.filter(status=status)
    
    project_id = request.GET.get('project', '')
    if project_id:
        queryset = queryset.filter(project_id=project_id)
    
    search = request.GET.get('search', '')
    if search:
        queryset = queryset.filter(
            Q(document_number__icontains=search) |
            Q(document_name__icontains=search) |
            Q(project__name__icontains=search)
        )
    
    # 分页
    page_size = request.GET.get('page_size', '10')
    try:
        per_page = int(page_size)
        if per_page not in [10, 20, 50]:
            per_page = 10
    except (ValueError, TypeError):
        per_page = 10
    paginator = Paginator(queryset, per_page)
    page_num = request.GET.get('page', 1)
    page = paginator.get_page(page_num)
    
    # 统计数据（用于统计卡片）
    base_queryset = ProjectArchiveDocument.objects.all()
    total_count = base_queryset.count()
    draft_count = base_queryset.filter(status='draft').count()
    pending_archive_count = base_queryset.filter(status='pending_archive').count()
    archived_count = base_queryset.filter(status='archived').count()
    borrowed_count = base_queryset.filter(status='borrowed').count()
    
    context = {
        'page': page,
        'document_type': document_type,
        'status': status,
        'project_id': project_id,
        'search': search,
        'total_count': total_count,
        'draft_count': draft_count,
        'pending_archive_count': pending_archive_count,
        'archived_count': archived_count,
        'borrowed_count': borrowed_count,
        'full_top_nav': _build_full_top_nav(permission_set, request.user),
        'archive_sidebar_nav': _build_archive_sidebar_nav(permission_set, request.path),
    }
    return render(request, "archive_management/project_document_list.html", context)


@login_required
def administrative_archive_list(request):
    """行政档案列表"""
    permission_set = get_user_permission_codes(request.user)
    if not _permission_granted('archive_management.view', permission_set):
        from django.http import HttpResponseForbidden
        return HttpResponseForbidden("无权限访问")
    
    queryset = AdministrativeArchive.objects.all().select_related('category', 'archivist', 'storage_room', 'location')
    
    # 筛选
    status = request.GET.get('status', '')
    if status:
        queryset = queryset.filter(status=status)
    
    category_id = request.GET.get('category', '')
    if category_id:
        queryset = queryset.filter(category_id=category_id)
    
    search = request.GET.get('search', '')
    if search:
        queryset = queryset.filter(
            Q(archive_number__icontains=search) |
            Q(archive_name__icontains=search)
        )
    
    # 分页
    page_size = request.GET.get('page_size', '10')
    try:
        per_page = int(page_size)
        if per_page not in [10, 20, 50]:
            per_page = 10
    except (ValueError, TypeError):
        per_page = 10
    paginator = Paginator(queryset, per_page)
    page_num = request.GET.get('page', 1)
    page = paginator.get_page(page_num)
    
    # 统计数据（用于统计卡片）
    base_queryset = AdministrativeArchive.objects.all()
    total_count = base_queryset.count()
    pending_count = base_queryset.filter(status='pending').count()
    approving_count = base_queryset.filter(status='approving').count()
    archived_count = base_queryset.filter(status='archived').count()
    borrowed_count = base_queryset.filter(status='borrowed').count()
    
    context = {
        'page': page,
        'status': status,
        'category_id': category_id,
        'search': search,
        'total_count': total_count,
        'pending_count': pending_count,
        'approving_count': approving_count,
        'archived_count': archived_count,
        'borrowed_count': borrowed_count,
        'full_top_nav': _build_full_top_nav(permission_set, request.user),
        'archive_sidebar_nav': _build_archive_sidebar_nav(permission_set, request.path),
    }
    return render(request, "archive_management/administrative_archive_list.html", context)


@login_required
def archive_category_list(request):
    """档案分类列表"""
    permission_set = get_user_permission_codes(request.user)
    if not _permission_granted('archive_management.view', permission_set):
        from django.http import HttpResponseForbidden
        return HttpResponseForbidden("无权限访问")
    
    category_type = request.GET.get('category_type', '')
    queryset = ArchiveCategory.objects.all()
    if category_type:
        queryset = queryset.filter(category_type=category_type)
    
    context = {
        'categories': queryset.select_related('parent'),
        'category_type': category_type,
        'full_top_nav': _build_full_top_nav(permission_set, request.user),
        'archive_sidebar_nav': _build_archive_sidebar_nav(permission_set, request.path),
    }
    return render(request, "archive_management/archive_category_list.html", context)


@login_required
def archive_category_rule(request):
    """档案分类规则管理"""
    permission_set = get_user_permission_codes(request.user)
    if not _permission_granted('archive_management.view', permission_set):
        from django.http import HttpResponseForbidden
        return HttpResponseForbidden("无权限访问")
    
    # 尝试导入ArchiveCategoryRule模型
    try:
        from backend.apps.archive_management.models import ArchiveCategoryRule
        model_available = True
    except ImportError:
        model_available = False
    
    if not model_available:
        from django.http import HttpResponse
        return HttpResponse("档案分类规则功能暂未实现，ArchiveCategoryRule 模型尚未定义", status=503)
    
    queryset = ArchiveCategoryRule.objects.all().select_related('category', 'created_by')
    
    # 筛选
    rule_type = request.GET.get('rule_type', '')
    if rule_type:
        queryset = queryset.filter(rule_type=rule_type)
    
    status = request.GET.get('status', '')
    if status:
        queryset = queryset.filter(status=status)
    
    category_id = request.GET.get('category', '')
    if category_id:
        queryset = queryset.filter(category_id=category_id)
    
    search = request.GET.get('search', '')
    if search:
        queryset = queryset.filter(
            Q(name__icontains=search) |
            Q(description__icontains=search) |
            Q(category__name__icontains=search)
        )
    
    # 分页
    page_size = request.GET.get('page_size', '10')
    try:
        per_page = int(page_size)
        if per_page not in [10, 20, 50]:
            per_page = 10
    except (ValueError, TypeError):
        per_page = 10
    paginator = Paginator(queryset, per_page)
    page_num = request.GET.get('page', 1)
    page = paginator.get_page(page_num)
    
    # 统计数据
    base_queryset = ArchiveCategoryRule.objects.all()
    total_count = base_queryset.count()
    active_count = base_queryset.filter(status='active', is_active=True).count()
    inactive_count = base_queryset.filter(status='inactive').count()
    auto_count = base_queryset.filter(rule_type='auto').count()
    
    # 获取所有分类（用于筛选）
    categories = ArchiveCategory.objects.filter(is_active=True).order_by('category_type', 'order', 'id')
    
    context = {
        'page': page,
        'rule_type': rule_type,
        'status': status,
        'category_id': category_id,
        'search': search,
        'total_count': total_count,
        'active_count': active_count,
        'inactive_count': inactive_count,
        'auto_count': auto_count,
        'categories': categories,
        'full_top_nav': _build_full_top_nav(permission_set, request.user),
        'archive_sidebar_nav': _build_archive_sidebar_nav(permission_set, request.path),
    }
    return render(request, "archive_management/archive_category_rule.html", context)


@login_required
def archive_borrow_list(request):
    """档案借阅列表"""
    permission_set = get_user_permission_codes(request.user)
    if not _permission_granted('archive_management.view', permission_set):
        from django.http import HttpResponseForbidden
        return HttpResponseForbidden("无权限访问")
    
    queryset = ArchiveBorrow.objects.all().select_related('borrower', 'project_document', 'administrative_archive')
    
    # 筛选
    status = request.GET.get('status', '')
    if status:
        queryset = queryset.filter(status=status)
    
    search = request.GET.get('search', '')
    if search:
        queryset = queryset.filter(
            Q(borrow_number__icontains=search) |
            Q(borrower__username__icontains=search)
        )
    
    # 分页
    page_size = request.GET.get('page_size', '10')
    try:
        per_page = int(page_size)
        if per_page not in [10, 20, 50]:
            per_page = 10
    except (ValueError, TypeError):
        per_page = 10
    paginator = Paginator(queryset, per_page)
    page_num = request.GET.get('page', 1)
    page = paginator.get_page(page_num)
    
    # 统计数据（用于统计卡片）
    base_queryset = ArchiveBorrow.objects.all()
    total_count = base_queryset.count()
    pending_count = base_queryset.filter(status='pending').count()
    approving_count = base_queryset.filter(status='approving').count()
    approved_count = base_queryset.filter(status='approved').count()
    out_count = base_queryset.filter(status='out').count()
    returned_count = base_queryset.filter(status='returned').count()
    overdue_count = base_queryset.filter(status='overdue').count()
    
    context = {
        'page': page,
        'status': status,
        'search': search,
        'total_count': total_count,
        'pending_count': pending_count,
        'approving_count': approving_count,
        'approved_count': approved_count,
        'out_count': out_count,
        'returned_count': returned_count,
        'overdue_count': overdue_count,
        'full_top_nav': _build_full_top_nav(permission_set, request.user),
        'archive_sidebar_nav': _build_archive_sidebar_nav(permission_set, request.path),
    }
    return render(request, "archive_management/archive_borrow_list.html", context)


@login_required
def archive_search(request):
    """档案查询"""
    permission_set = get_user_permission_codes(request.user)
    if not _permission_granted('archive_management.view', permission_set):
        from django.http import HttpResponseForbidden
        return HttpResponseForbidden("无权限访问")
    
    archive_type = request.GET.get('type', '')
    search = request.GET.get('search', '')
    
    project_documents = []
    administrative_archives = []
    
    if archive_type == 'project' or not archive_type:
        project_documents = ProjectArchiveDocument.objects.all()
        if search:
            project_documents = project_documents.filter(
                Q(document_number__icontains=search) |
                Q(document_name__icontains=search) |
                Q(project__name__icontains=search)
            )
        project_documents = project_documents[:20]
    
    if archive_type == 'administrative' or not archive_type:
        administrative_archives = AdministrativeArchive.objects.all()
        if search:
            administrative_archives = administrative_archives.filter(
                Q(archive_number__icontains=search) |
                Q(archive_name__icontains=search)
            )
        administrative_archives = administrative_archives[:20]
    
    context = {
        'archive_type': archive_type,
        'search': search,
        'project_documents': project_documents,
        'administrative_archives': administrative_archives,
        'full_top_nav': _build_full_top_nav(permission_set, request.user),
        'archive_sidebar_nav': _build_archive_sidebar_nav(permission_set, request.path),
    }
    return render(request, "archive_management/archive_search.html", context)


# 占位视图函数（待实现）
@login_required
def project_archive_create(request):
    """创建项目归档"""
    permission_set = get_user_permission_codes(request.user)
    if not _permission_granted('archive_management.add', permission_set):
        from django.http import HttpResponseForbidden
        return HttpResponseForbidden("无权限访问")
    
    from .forms import ProjectArchiveForm
    from backend.apps.production_management.models import Project
    
    # 获取可归档的项目列表（已结算的项目）
    available_projects = Project.objects.filter(
        status__in=['settled', 'completed', 'archived']
    ).order_by('-updated_time')[:100]  # 限制显示最近100个项目
    
    if request.method == 'POST':
        form = ProjectArchiveForm(request.POST)
        if form.is_valid():
            archive = form.save(commit=False)
            archive.applicant = request.user
            archive.status = 'pending'  # 初始状态为待归档
            archive.save()
            messages.success(request, f'项目归档申请已提交，归档编号：{archive.archive_number}')
            return redirect('archive_management:project_archive_detail', pk=archive.pk)
        else:
            messages.error(request, '表单验证失败，请检查输入信息')
    else:
        # 预填充项目ID（如果URL中有project_id参数）
        project_id = request.GET.get('project_id')
        initial_data = {}
        if project_id:
            try:
                project = Project.objects.get(pk=project_id)
                initial_data['project'] = project
            except Project.DoesNotExist:
                pass
        form = ProjectArchiveForm(initial=initial_data)
    
    context = {
        'form': form,
        'available_projects': available_projects,
        'full_top_nav': _build_full_top_nav(permission_set, request.user),
        'archive_sidebar_nav': _build_archive_sidebar_nav(permission_set, request.path),
    }
    return render(request, "archive_management/project_archive_create.html", context)


@login_required
def project_archive_edit(request, pk):
    """编辑项目归档"""
    permission_set = get_user_permission_codes(request.user)
    if not _permission_granted('archive_management.change', permission_set):
        from django.http import HttpResponseForbidden
        return HttpResponseForbidden("无权限访问")
    
    archive = get_object_or_404(ArchiveProjectArchive, pk=pk)
    
    # 只有待归档和驳回状态可以编辑
    if archive.status not in ['pending', 'rejected']:
        messages.warning(request, f'当前归档状态为"{archive.get_status_display()}"，无法编辑')
        return redirect('archive_management:project_archive_detail', pk=archive.pk)
    
    from .forms import ProjectArchiveForm
    
    if request.method == 'POST':
        form = ProjectArchiveForm(request.POST, instance=archive)
        if form.is_valid():
            form.save()
            messages.success(request, '归档信息已更新')
            return redirect('archive_management:project_archive_detail', pk=archive.pk)
        else:
            messages.error(request, '表单验证失败，请检查输入信息')
    else:
        form = ProjectArchiveForm(instance=archive)
    
    context = {
        'form': form,
        'archive': archive,
        'full_top_nav': _build_full_top_nav(permission_set, request.user),
        'archive_sidebar_nav': _build_archive_sidebar_nav(permission_set, request.path),
    }
    return render(request, "archive_management/project_archive_edit.html", context)


@login_required
def project_document_upload(request):
    """上传项目文档"""
    permission_set = get_user_permission_codes(request.user)
    if not _permission_granted('archive_management.add', permission_set):
        from django.http import HttpResponseForbidden
        return HttpResponseForbidden("无权限访问")
    
    from .forms import ProjectArchiveDocumentForm
    from backend.apps.production_management.models import Project
    
    # 获取项目列表
    projects = Project.objects.filter(status__in=['in_progress', 'settled', 'completed']).order_by('-updated_time')[:100]
    
    # 获取分类列表
    categories = ArchiveCategory.objects.filter(
        category_type='project',
        is_active=True
    ).order_by('order', 'id')
    
    if request.method == 'POST':
        form = ProjectArchiveDocumentForm(request.POST, request.FILES)
        if form.is_valid():
            document = form.save(commit=False)
            document.uploaded_by = request.user
            document.status = 'pending'  # 初始状态为待归档
            
            # 提取文件信息
            if document.file:
                import os
                from django.core.files.uploadedfile import UploadedFile
                file = document.file
                document.file_name = file.name
                document.file_size = file.size
                
                # 提取文件扩展名
                file_ext = os.path.splitext(file.name)[1].lower().lstrip('.')
                document.file_extension = file_ext
                
                # 尝试获取MIME类型
                if hasattr(file, 'content_type'):
                    document.mime_type = file.content_type
                else:
                    # 简单的MIME类型映射
                    mime_map = {
                        'pdf': 'application/pdf',
                        'doc': 'application/msword',
                        'docx': 'application/vnd.openxmlformats-officedocument.wordprocessingml.document',
                        'xls': 'application/vnd.ms-excel',
                        'xlsx': 'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet',
                        'jpg': 'image/jpeg',
                        'jpeg': 'image/jpeg',
                        'png': 'image/png',
                        'dwg': 'image/vnd.dwg',
                    }
                    document.mime_type = mime_map.get(file_ext, 'application/octet-stream')
            
            document.save()
            
            # 记录操作日志
            ArchiveOperationLogService.log_from_request(
                request,
                operation_type='upload',
                operation_content=f'上传项目文档：{document.document_name}（编号：{document.document_number}）',
                operation_result='success',
                project_document=document,
                extra_data={'file_size': document.file_size, 'file_extension': document.file_extension}
            )
            
            messages.success(request, f'文档上传成功，文档编号：{document.document_number}')
            return redirect('archive_management:project_document_detail', pk=document.pk)
        else:
            messages.error(request, '表单验证失败，请检查输入信息')
    else:
        # 预填充项目ID（如果URL中有project_id参数）
        project_id = request.GET.get('project_id')
        initial_data = {}
        if project_id:
            try:
                project = Project.objects.get(pk=project_id)
                initial_data['project'] = project
            except Project.DoesNotExist:
                pass
        form = ProjectArchiveDocumentForm(initial=initial_data)
    
    context = {
        'form': form,
        'projects': projects,
        'categories': categories,
        'full_top_nav': _build_full_top_nav(permission_set, request.user),
        'archive_sidebar_nav': _build_archive_sidebar_nav(permission_set, request.path),
    }
    return render(request, "archive_management/project_document_upload.html", context)


@login_required
def project_document_detail(request, pk):
    permission_set = get_user_permission_codes(request.user)
    context = {
        'full_top_nav': _build_full_top_nav(permission_set, request.user),
        'archive_sidebar_nav': _build_archive_sidebar_nav(permission_set, request.path),
    }
    return render(request, "archive_management/project_document_detail.html", context)


@login_required
def administrative_archive_create(request):
    """创建行政档案"""
    permission_set = get_user_permission_codes(request.user)
    if not _permission_granted('archive_management.add', permission_set):
        from django.http import HttpResponseForbidden
        return HttpResponseForbidden("无权限访问")
    
    from .forms import AdministrativeArchiveForm
    from backend.apps.system_management.models import Department
    
    # 获取分类列表
    categories = ArchiveCategory.objects.filter(
        category_type='administrative',
        is_active=True
    ).order_by('order', 'id')
    
    # 获取部门列表
    departments = Department.objects.filter(is_active=True).order_by('name')
    
    # 获取库房列表
    storage_rooms = ArchiveStorageRoom.objects.filter(status='active').order_by('room_name')
    
    if request.method == 'POST':
        form = AdministrativeArchiveForm(request.POST, request.FILES)
        if form.is_valid():
            archive = form.save(commit=False)
            archive.archivist = request.user
            archive.status = 'pending'  # 初始状态为待归档
            
            # 处理文件上传（支持多文件）
            uploaded_files = []
            if 'archive_file' in request.FILES:
                import os
                from django.core.files.storage import default_storage
                from django.core.files.base import ContentFile
                files = request.FILES.getlist('archive_file')
                
                # 先保存档案记录，以便生成档案编号用于文件路径
                if not archive.archive_number:
                    archive.save()
                
                for file in files:
                    try:
                        # 生成文件保存路径
                        date_path = timezone.now().strftime('%Y/%m/%d')
                        file_dir = f'archive_files/{date_path}/{archive.archive_number}'
                        file_path = os.path.join(file_dir, file.name)
                        
                        # 保存文件
                        file_extension = os.path.splitext(file.name)[1].lower().lstrip('.')
                        saved_path = default_storage.save(file_path, ContentFile(file.read()))
                        
                        # 记录文件信息
                        file_info = {
                            'name': file.name,
                            'path': saved_path,
                            'size': file.size,
                            'extension': file_extension,
                            'mime_type': getattr(file, 'content_type', ''),
                            'upload_time': timezone.now().isoformat(),
                        }
                        uploaded_files.append(file_info)
                    except Exception as e:
                        # 文件保存失败，记录错误但继续处理其他文件
                        messages.warning(request, f'文件 {file.name} 保存失败：{str(e)}')
                        continue
                
                archive.files = uploaded_files
            
            # 保存档案记录（包含文件信息）
            archive.save()
            
            # 记录操作日志
            ArchiveOperationLogService.log_from_request(
                request,
                operation_type='archive',
                operation_content=f'创建行政档案：{archive.archive_name}（编号：{archive.archive_number}）',
                operation_result='success',
                administrative_archive=archive,
                extra_data={'file_count': len(uploaded_files)}
            )
            
            messages.success(request, f'行政档案创建成功，档案编号：{archive.archive_number}')
            return redirect('archive_management:administrative_archive_detail', pk=archive.pk)
        else:
            messages.error(request, '表单验证失败，请检查输入信息')
    else:
        form = AdministrativeArchiveForm()
    
    context = {
        'form': form,
        'categories': categories,
        'departments': departments,
        'storage_rooms': storage_rooms,
        'full_top_nav': _build_full_top_nav(permission_set, request.user),
        'archive_sidebar_nav': _build_archive_sidebar_nav(permission_set, request.path),
    }
    return render(request, "archive_management/administrative_archive_create.html", context)


@login_required
def administrative_archive_detail(request, pk):
    """行政档案详情"""
    permission_set = get_user_permission_codes(request.user)
    if not _permission_granted('archive_management.view', permission_set):
        from django.http import HttpResponseForbidden
        return HttpResponseForbidden("无权限访问")
    
    archive = get_object_or_404(AdministrativeArchive.objects.select_related(
        'category', 'archive_department', 'archivist', 'storage_room', 'location'
    ), pk=pk)
    
    # 获取关联的借阅记录
    borrows = ArchiveBorrow.objects.filter(
        administrative_archive=archive
    ).select_related('borrower').order_by('-created_time')[:10]
    
    # 获取关联的销毁记录
    destroys = ArchiveDestroy.objects.filter(
        administrative_archive=archive
    ).select_related('destroyer').order_by('-created_time')[:10]
    
    context = {
        'archive': archive,
        'borrows': borrows,
        'destroys': destroys,
        'full_top_nav': _build_full_top_nav(permission_set, request.user),
        'archive_sidebar_nav': _build_archive_sidebar_nav(permission_set, request.path),
    }
    return render(request, "archive_management/administrative_archive_detail.html", context)


@login_required
def archive_category_create(request):
    """创建档案分类"""
    permission_set = get_user_permission_codes(request.user)
    if not _permission_granted('archive_management.add', permission_set):
        from django.http import HttpResponseForbidden
        return HttpResponseForbidden("无权限访问")
    
    from .forms import ArchiveCategoryForm
    
    # 获取上级分类列表
    parent_categories = ArchiveCategory.objects.filter(is_active=True).order_by('category_type', 'order', 'id')
    
    if request.method == 'POST':
        form = ArchiveCategoryForm(request.POST)
        if form.is_valid():
            category = form.save(commit=False)
            category.created_by = request.user
            category.save()
            messages.success(request, f'档案分类创建成功：{category.name}')
            return redirect('archive_management:archive_category_list')
        else:
            messages.error(request, '表单验证失败，请检查输入信息')
    else:
        # 预填充分类类型（如果URL中有参数）
        category_type = request.GET.get('category_type')
        initial_data = {}
        if category_type:
            initial_data['category_type'] = category_type
        form = ArchiveCategoryForm(initial=initial_data)
    
    context = {
        'form': form,
        'parent_categories': parent_categories,
        'full_top_nav': _build_full_top_nav(permission_set, request.user),
        'archive_sidebar_nav': _build_archive_sidebar_nav(permission_set, request.path),
    }
    return render(request, "archive_management/archive_category_create.html", context)


@login_required
def archive_category_edit(request, pk):
    """编辑档案分类"""
    permission_set = get_user_permission_codes(request.user)
    if not _permission_granted('archive_management.change', permission_set):
        from django.http import HttpResponseForbidden
        return HttpResponseForbidden("无权限访问")
    
    category = get_object_or_404(ArchiveCategory, pk=pk)
    from .forms import ArchiveCategoryForm
    
    # 获取上级分类列表（排除自己和子分类）
    parent_categories = ArchiveCategory.objects.filter(
        is_active=True
    ).exclude(pk=pk).exclude(parent=category).order_by('category_type', 'order', 'id')
    
    if request.method == 'POST':
        form = ArchiveCategoryForm(request.POST, instance=category)
        if form.is_valid():
            form.save()
            messages.success(request, f'档案分类已更新：{category.name}')
            return redirect('archive_management:archive_category_list')
        else:
            messages.error(request, '表单验证失败，请检查输入信息')
    else:
        form = ArchiveCategoryForm(instance=category)
    
    context = {
        'form': form,
        'category': category,
        'parent_categories': parent_categories,
        'full_top_nav': _build_full_top_nav(permission_set, request.user),
        'archive_sidebar_nav': _build_archive_sidebar_nav(permission_set, request.path),
    }
    return render(request, "archive_management/archive_category_edit.html", context)


@login_required
def archive_borrow_create(request):
    """创建档案借阅"""
    permission_set = get_user_permission_codes(request.user)
    if not _permission_granted('archive_management.add', permission_set):
        from django.http import HttpResponseForbidden
        return HttpResponseForbidden("无权限访问")
    
    from .forms import ArchiveBorrowForm
    from backend.apps.system_management.models import Department
    
    # 获取可借阅的项目文档
    project_documents = ProjectArchiveDocument.objects.filter(
        status__in=['archived', 'pending_archive']
    ).select_related('project', 'category').order_by('-uploaded_time')[:100]
    
    # 获取可借阅的行政档案
    administrative_archives = AdministrativeArchive.objects.filter(
        status='archived'
    ).select_related('category', 'archive_department').order_by('-created_time')[:100]
    
    # 获取部门列表
    departments = Department.objects.filter(is_active=True).order_by('name')
    
    if request.method == 'POST':
        form = ArchiveBorrowForm(request.POST)
        if form.is_valid():
            borrow = form.save(commit=False)
            borrow.borrower = request.user
            borrow.status = 'pending'  # 初始状态为待审批
            
            # 设置借阅部门（如果用户有部门）
            if not borrow.borrower_department and hasattr(request.user, 'department'):
                borrow.borrower_department = request.user.department
            
            borrow.save()
            
            # 记录操作日志
            archive_name = ''
            if borrow.project_document:
                archive_name = borrow.project_document.document_name
            elif borrow.administrative_archive:
                archive_name = borrow.administrative_archive.archive_name
            
            ArchiveOperationLogService.log_from_request(
                request,
                operation_type='borrow',
                operation_content=f'申请借阅档案：{archive_name}（借阅单号：{borrow.borrow_number}）',
                operation_result='success',
                borrow_record=borrow,
                project_document=borrow.project_document,
                administrative_archive=borrow.administrative_archive,
                extra_data={'borrow_type': borrow.borrow_type, 'expected_return_date': str(borrow.return_date) if borrow.return_date else None}
            )
            
            messages.success(request, f'借阅申请已提交，借阅单号：{borrow.borrow_number}')
            return redirect('archive_management:archive_borrow_detail', pk=borrow.pk)
        else:
            messages.error(request, '表单验证失败，请检查输入信息')
    else:
        # 预填充档案ID（如果URL中有参数）
        project_doc_id = request.GET.get('project_document_id')
        admin_archive_id = request.GET.get('administrative_archive_id')
        initial_data = {}
        if project_doc_id:
            try:
                doc = ProjectArchiveDocument.objects.get(pk=project_doc_id)
                initial_data['project_document'] = doc
            except ProjectArchiveDocument.DoesNotExist:
                pass
        if admin_archive_id:
            try:
                archive = AdministrativeArchive.objects.get(pk=admin_archive_id)
                initial_data['administrative_archive'] = archive
            except AdministrativeArchive.DoesNotExist:
                pass
        form = ArchiveBorrowForm(initial=initial_data)
    
    context = {
        'form': form,
        'project_documents': project_documents,
        'administrative_archives': administrative_archives,
        'departments': departments,
        'full_top_nav': _build_full_top_nav(permission_set, request.user),
        'archive_sidebar_nav': _build_archive_sidebar_nav(permission_set, request.path),
    }
    return render(request, "archive_management/archive_borrow_create.html", context)


@login_required
def archive_borrow_detail(request, pk):
    """档案借阅详情"""
    permission_set = get_user_permission_codes(request.user)
    if not _permission_granted('archive_management.view', permission_set):
        from django.http import HttpResponseForbidden
        return HttpResponseForbidden("无权限访问")
    
    borrow = get_object_or_404(ArchiveBorrow.objects.select_related(
        'project_document', 'administrative_archive', 'borrower', 
        'borrower_department', 'approver', 'out_by', 'returned_by'
    ), pk=pk)
    
    # 计算是否逾期
    is_overdue = borrow.is_overdue
    overdue_days = 0
    if is_overdue and borrow.return_date:
        from datetime import date
        overdue_days = (date.today() - borrow.return_date).days
    
    context = {
        'borrow': borrow,
        'is_overdue': is_overdue,
        'overdue_days': overdue_days,
        'full_top_nav': _build_full_top_nav(permission_set, request.user),
        'archive_sidebar_nav': _build_archive_sidebar_nav(permission_set, request.path),
    }
    return render(request, "archive_management/archive_borrow_detail.html", context)


@login_required
def archive_destroy_list(request):
    """档案销毁列表"""
    permission_set = get_user_permission_codes(request.user)
    if not _permission_granted('archive_management.view', permission_set):
        from django.http import HttpResponseForbidden
        return HttpResponseForbidden("无权限访问")
    
    # 获取筛选参数
    status = request.GET.get('status', '')
    destroy_type = request.GET.get('destroy_type', '')
    search = request.GET.get('search', '').strip()
    
    # 查询销毁记录
    queryset = ArchiveDestroy.objects.all().select_related(
        'project_document', 'administrative_archive', 'destroyer'
    ).order_by('-created_time')
    
    # 筛选
    if status:
        queryset = queryset.filter(status=status)
    if destroy_type:
        queryset = queryset.filter(destroy_type=destroy_type)
    if search:
        queryset = queryset.filter(
            Q(destroy_reason__icontains=search) |
            Q(project_document__document_name__icontains=search) |
            Q(administrative_archive__archive_name__icontains=search)
        )
    
    # 分页
    page_size = request.GET.get('page_size', '10')
    try:
        per_page = int(page_size)
        if per_page not in [10, 20, 50]:
            per_page = 10
    except (ValueError, TypeError):
        per_page = 10
    paginator = Paginator(queryset, per_page)
    page_num = request.GET.get('page', 1)
    page = paginator.get_page(page_num)
    
    # 统计数据
    total_count = ArchiveDestroy.objects.count()
    pending_count = ArchiveDestroy.objects.filter(status='pending').count()
    approved_count = ArchiveDestroy.objects.filter(status='approved').count()
    completed_count = ArchiveDestroy.objects.filter(status='completed').count()
    
    context = {
        'page': page,
        'status': status,
        'destroy_type': destroy_type,
        'search': search,
        'total_count': total_count,
        'pending_count': pending_count,
        'approved_count': approved_count,
        'completed_count': completed_count,
        'full_top_nav': _build_full_top_nav(permission_set, request.user),
        'archive_sidebar_nav': _build_archive_sidebar_nav(permission_set, request.path),
    }
    return render(request, "archive_management/archive_destroy_list.html", context)


@login_required
def archive_destroy_create(request):
    """创建档案销毁申请"""
    permission_set = get_user_permission_codes(request.user)
    if not _permission_granted('archive_management.add', permission_set):
        from django.http import HttpResponseForbidden
        return HttpResponseForbidden("无权限访问")
    
    from .forms import ArchiveDestroyForm
    
    # 获取可销毁的项目文档（已归档且超过保管期限）
    project_documents = ProjectArchiveDocument.objects.filter(
        status='archived'
    ).select_related('project', 'category').order_by('-uploaded_time')[:100]
    
    # 获取可销毁的行政档案（已归档且超过保管期限）
    administrative_archives = AdministrativeArchive.objects.filter(
        status='archived'
    ).select_related('category', 'archive_department').order_by('-created_time')[:100]
    
    if request.method == 'POST':
        form = ArchiveDestroyForm(request.POST)
        if form.is_valid():
            destroy = form.save(commit=False)
            destroy.destroyer = request.user
            destroy.status = 'pending'  # 初始状态为待审批
            
            # 检查保管期限
            archive = destroy.project_document or destroy.administrative_archive
            if archive:
                # 获取保管期限
                storage_period_years = None
                archive_date = None
                
                if hasattr(archive, 'category') and archive.category:
                    # 优先使用分类的保管期限
                    storage_period_years = archive.category.storage_period
                elif hasattr(archive, 'storage_period') and archive.storage_period:
                    # 使用档案自身的保管期限
                    storage_period_years = archive.storage_period
                
                # 获取归档日期
                if hasattr(archive, 'archive_date'):
                    archive_date = archive.archive_date
                elif hasattr(archive, 'uploaded_time'):
                    archive_date = archive.uploaded_time.date()
                elif hasattr(archive, 'created_time'):
                    archive_date = archive.created_time.date()
                
                # 检查是否超过保管期限
                if storage_period_years and archive_date:
                    from datetime import timedelta
                    expiry_date = archive_date + timedelta(days=storage_period_years * 365)
                    current_date = timezone.now().date()
                    
                    if current_date < expiry_date:
                        remaining_days = (expiry_date - current_date).days
                        messages.warning(
                            request, 
                            f'该档案尚未到期，距离到期还有{remaining_days}天。如需提前销毁，请说明原因。'
                        )
                    else:
                        overdue_days = (current_date - expiry_date).days
                        messages.info(
                            request,
                            f'该档案已超过保管期限{overdue_days}天，符合销毁条件。'
                        )
            
            destroy.save()
            messages.success(request, f'销毁申请已提交，销毁单号：{destroy.destroy_number}')
            return redirect('archive_management:archive_destroy_detail', pk=destroy.pk)
        else:
            messages.error(request, '表单验证失败，请检查输入信息')
    else:
        # 预填充档案ID（如果URL中有参数）
        project_doc_id = request.GET.get('project_document_id')
        admin_archive_id = request.GET.get('administrative_archive_id')
        initial_data = {}
        if project_doc_id:
            try:
                doc = ProjectArchiveDocument.objects.get(pk=project_doc_id)
                initial_data['project_document'] = doc
            except ProjectArchiveDocument.DoesNotExist:
                pass
        if admin_archive_id:
            try:
                archive = AdministrativeArchive.objects.get(pk=admin_archive_id)
                initial_data['administrative_archive'] = archive
            except AdministrativeArchive.DoesNotExist:
                pass
        form = ArchiveDestroyForm(initial=initial_data)
    
    context = {
        'form': form,
        'project_documents': project_documents,
        'administrative_archives': administrative_archives,
        'full_top_nav': _build_full_top_nav(permission_set, request.user),
        'archive_sidebar_nav': _build_archive_sidebar_nav(permission_set, request.path),
    }
    return render(request, "archive_management/archive_destroy_create.html", context)


@login_required
def archive_destroy_detail(request, pk):
    """档案销毁详情"""
    permission_set = get_user_permission_codes(request.user)
    if not _permission_granted('archive_management.view', permission_set):
        from django.http import HttpResponseForbidden
        return HttpResponseForbidden("无权限访问")
    
    destroy = get_object_or_404(ArchiveDestroy.objects.select_related(
        'project_document', 'administrative_archive', 'destroyer', 'approver'
    ), pk=pk)
    
    context = {
        'destroy': destroy,
        'full_top_nav': _build_full_top_nav(permission_set, request.user),
        'archive_sidebar_nav': _build_archive_sidebar_nav(permission_set, request.path),
    }
    return render(request, "archive_management/archive_destroy_detail.html", context)


@login_required
def archive_storage_list(request):
    permission_set = get_user_permission_codes(request.user)
    context = {
        'full_top_nav': _build_full_top_nav(permission_set, request.user),
        'archive_sidebar_nav': _build_archive_sidebar_nav(permission_set, request.path),
    }
    return render(request, "archive_management/archive_storage_list.html", context)


@login_required
def archive_storage_room_list(request):
    permission_set = get_user_permission_codes(request.user)
    context = {
        'full_top_nav': _build_full_top_nav(permission_set, request.user),
        'archive_sidebar_nav': _build_archive_sidebar_nav(permission_set, request.path),
    }
    return render(request, "archive_management/archive_storage_room_list.html", context)


@login_required
def archive_storage_room_create(request):
    permission_set = get_user_permission_codes(request.user)
    context = {
        'full_top_nav': _build_full_top_nav(permission_set, request.user),
        'archive_sidebar_nav': _build_archive_sidebar_nav(permission_set, request.path),
    }
    return render(request, "archive_management/archive_storage_room_create.html", context)


@login_required
def archive_location_list(request):
    permission_set = get_user_permission_codes(request.user)
    context = {
        'full_top_nav': _build_full_top_nav(permission_set, request.user),
        'archive_sidebar_nav': _build_archive_sidebar_nav(permission_set, request.path),
    }
    return render(request, "archive_management/archive_location_list.html", context)


@login_required
def archive_location_create(request):
    permission_set = get_user_permission_codes(request.user)
    context = {
        'full_top_nav': _build_full_top_nav(permission_set, request.user),
        'archive_sidebar_nav': _build_archive_sidebar_nav(permission_set, request.path),
    }
    return render(request, "archive_management/archive_location_create.html", context)


@login_required
def archive_shelf_list(request):
    permission_set = get_user_permission_codes(request.user)
    context = {
        'full_top_nav': _build_full_top_nav(permission_set, request.user),
        'archive_sidebar_nav': _build_archive_sidebar_nav(permission_set, request.path),
    }
    return render(request, "archive_management/archive_shelf_list.html", context)


@login_required
def archive_inventory_list(request):
    permission_set = get_user_permission_codes(request.user)
    context = {
        'full_top_nav': _build_full_top_nav(permission_set, request.user),
        'archive_sidebar_nav': _build_archive_sidebar_nav(permission_set, request.path),
    }
    return render(request, "archive_management/archive_inventory_list.html", context)


@login_required
def archive_inventory_create(request):
    permission_set = get_user_permission_codes(request.user)
    context = {
        'full_top_nav': _build_full_top_nav(permission_set, request.user),
        'archive_sidebar_nav': _build_archive_sidebar_nav(permission_set, request.path),
    }
    return render(request, "archive_management/archive_inventory_create.html", context)


@login_required
def archive_statistics(request):
    permission_set = get_user_permission_codes(request.user)
    context = {
        'full_top_nav': _build_full_top_nav(permission_set, request.user),
        'archive_sidebar_nav': _build_archive_sidebar_nav(permission_set, request.path),
    }
    return render(request, "archive_management/archive_statistics.html", context)


# ==================== 待实现功能视图函数 ====================

# 图纸归档
@login_required
def project_drawing_archive_list(request):
    """图纸归档列表"""
    permission_set = get_user_permission_codes(request.user)
    if not _permission_granted('archive_management.view', permission_set):
        from django.http import HttpResponseForbidden
        return HttpResponseForbidden("无权限访问")
    
    try:
        from backend.apps.customer_management.models import ProjectDrawingArchive
        model_available = True
    except ImportError:
        model_available = False
    
    if not model_available:
        from django.http import HttpResponse
        return HttpResponse("图纸归档功能暂未实现，ProjectDrawingArchive 模型尚未定义", status=503)
    
    queryset = ProjectDrawingArchive.objects.all().select_related('project', 'applicant', 'executor', 'category')
    
    # 筛选
    status = request.GET.get('status', '')
    if status:
        queryset = queryset.filter(status=status)
    
    project_id = request.GET.get('project', '')
    if project_id:
        queryset = queryset.filter(project_id=project_id)
    
    archive_type = request.GET.get('archive_type', '')
    if archive_type:
        queryset = queryset.filter(archive_type=archive_type)
    
    search = request.GET.get('search', '')
    if search:
        queryset = queryset.filter(
            Q(archive_number__icontains=search) |
            Q(project__project_name__icontains=search) |
            Q(project__project_number__icontains=search)
        )
    
    # 分页
    page_size = request.GET.get('page_size', '10')
    try:
        per_page = int(page_size)
        if per_page not in [10, 20, 50]:
            per_page = 10
    except (ValueError, TypeError):
        per_page = 10
    paginator = Paginator(queryset, per_page)
    page_num = request.GET.get('page', 1)
    page = paginator.get_page(page_num)
    
    # 统计数据
    base_queryset = ProjectDrawingArchive.objects.all()
    total_count = base_queryset.count()
    pending_count = base_queryset.filter(status='pending').count()
    approving_count = base_queryset.filter(status='approving').count()
    archiving_count = base_queryset.filter(status='archiving').count()
    archived_count = base_queryset.filter(status='archived').count()
    
    # 获取项目列表（用于筛选）
    projects = Project.objects.all().order_by('-created_time')[:100]
    
    context = {
        'page': page,
        'status': status,
        'project_id': project_id,
        'archive_type': archive_type,
        'search': search,
        'total_count': total_count,
        'pending_count': pending_count,
        'approving_count': approving_count,
        'archiving_count': archiving_count,
        'archived_count': archived_count,
        'projects': projects,
        'full_top_nav': _build_full_top_nav(permission_set, request.user),
        'archive_sidebar_nav': _build_archive_sidebar_nav(permission_set, request.path),
    }
    return render(request, "archive_management/project_drawing_archive_list.html", context)


@login_required
def project_drawing_archive_create(request):
    """创建图纸归档"""
    permission_set = get_user_permission_codes(request.user)
    if not _permission_granted('archive_management.add', permission_set):
        from django.http import HttpResponseForbidden
        return HttpResponseForbidden("无权限访问")
    
    try:
        from backend.apps.customer_management.models import ProjectDrawingArchive
        model_available = True
    except ImportError:
        model_available = False
    
    if not model_available:
        from django.http import HttpResponse
        return HttpResponse("图纸归档功能暂未实现，ProjectDrawingArchive 模型尚未定义", status=503)
    
    # 尝试导入图纸相关模型
    try:
        from backend.apps.production_management.models import ProjectDrawingFile, ProjectDrawingSubmission
        drawing_models_available = True
    except ImportError:
        drawing_models_available = False
    
    if request.method == 'POST':
        project_id = request.POST.get('project')
        archive_type = request.POST.get('archive_type', 'all')
        archive_reason = request.POST.get('archive_reason', '')
        archive_description = request.POST.get('archive_description', '')
        category_id = request.POST.get('category', '')
        
        # 获取选中的图纸提交和文件
        submission_ids = request.POST.getlist('submission_ids')
        file_ids = request.POST.getlist('file_ids')
        
        try:
            project = Project.objects.get(pk=project_id)
        except Project.DoesNotExist:
            messages.error(request, '项目不存在')
            return redirect('archive_management:project_drawing_archive_list')
        
        # 创建归档记录
        archive = ProjectDrawingArchive.objects.create(
            project=project,
            archive_type=archive_type,
            archive_reason=archive_reason,
            archive_description=archive_description,
            applicant=request.user,
            status='pending',
            drawing_submission_ids=[int(id) for id in submission_ids if id],
            drawing_file_ids=[int(id) for id in file_ids if id],
        )
        
        if category_id:
            try:
                category = ArchiveCategory.objects.get(pk=category_id)
                archive.category = category
                archive.save()
            except ArchiveCategory.DoesNotExist:
                pass
        
        messages.success(request, f'图纸归档申请已提交，归档编号：{archive.archive_number}')
        return redirect('archive_management:project_drawing_archive_detail', pk=archive.pk)
    
    # GET请求，显示创建表单
    project_id = request.GET.get('project_id', '')
    project = None
    submissions = []
    drawing_files = []
    
    if project_id:
        try:
            project = Project.objects.get(pk=project_id)
            if drawing_models_available:
                submissions = ProjectDrawingSubmission.objects.filter(
                    project=project,
                    status='approved'
                ).order_by('-submitted_time')
                drawing_files = ProjectDrawingFile.objects.filter(
                    submission__project=project
                ).select_related('submission').order_by('-uploaded_time')
        except Project.DoesNotExist:
            pass
    
    # 获取项目列表
    projects = Project.objects.all().order_by('-created_time')[:100]
    
    # 获取分类列表
    categories = ArchiveCategory.objects.filter(
        category_type='project',
        is_active=True
    ).order_by('order', 'id')
    
    context = {
        'project': project,
        'project_id': project_id,
        'submissions': submissions,
        'drawing_files': drawing_files,
        'projects': projects,
        'categories': categories,
        'drawing_models_available': drawing_models_available,
        'full_top_nav': _build_full_top_nav(permission_set, request.user),
        'archive_sidebar_nav': _build_archive_sidebar_nav(permission_set, request.path),
    }
    return render(request, "archive_management/project_drawing_archive_create.html", context)


@login_required
def project_drawing_archive_detail(request, pk):
    """图纸归档详情"""
    permission_set = get_user_permission_codes(request.user)
    if not _permission_granted('archive_management.view', permission_set):
        from django.http import HttpResponseForbidden
        return HttpResponseForbidden("无权限访问")
    
    try:
        from backend.apps.customer_management.models import ProjectDrawingArchive
        model_available = True
    except ImportError:
        model_available = False
    
    if not model_available:
        from django.http import HttpResponse
        return HttpResponse("图纸归档功能暂未实现，ProjectDrawingArchive 模型尚未定义", status=503)
    
    archive = get_object_or_404(
        ProjectDrawingArchive.objects.select_related('project', 'applicant', 'executor', 'category'),
        pk=pk
    )
    
    # 获取归档的图纸文件
    drawing_files = archive.get_drawing_files()
    drawing_submissions = archive.get_drawing_submissions()
    
    context = {
        'archive': archive,
        'drawing_files': drawing_files,
        'drawing_submissions': drawing_submissions,
        'full_top_nav': _build_full_top_nav(permission_set, request.user),
        'archive_sidebar_nav': _build_archive_sidebar_nav(permission_set, request.path),
    }
    return render(request, "archive_management/project_drawing_archive_detail.html", context)


# 交付归档（手动归档）
@login_required
def project_delivery_archive_list(request):
    """交付归档列表"""
    permission_set = get_user_permission_codes(request.user)
    if not _permission_granted('archive_management.view', permission_set):
        from django.http import HttpResponseForbidden
        return HttpResponseForbidden("无权限访问")
    
    # 尝试导入ProjectDeliveryArchive模型
    try:
        from backend.apps.customer_management.models import ProjectDeliveryArchive
        model_available = True
    except ImportError:
        model_available = False
    
    if not model_available:
        from django.http import HttpResponse
        return HttpResponse("交付归档功能暂未实现，ProjectDeliveryArchive 模型尚未定义", status=503)
    
    queryset = ProjectDeliveryArchive.objects.all().select_related('delivery_record', 'project', 'applicant', 'executor', 'category')
    
    # 筛选
    status = request.GET.get('status', '')
    if status:
        queryset = queryset.filter(status=status)
    
    project_id = request.GET.get('project', '')
    if project_id:
        queryset = queryset.filter(project_id=project_id)
    
    search = request.GET.get('search', '')
    if search:
        queryset = queryset.filter(
            Q(archive_number__icontains=search) |
            Q(delivery_record__delivery_number__icontains=search) |
            Q(delivery_record__title__icontains=search) |
            Q(project__project_name__icontains=search) |
            Q(project__project_number__icontains=search)
        )
    
    # 分页
    page_size = request.GET.get('page_size', '10')
    try:
        per_page = int(page_size)
        if per_page not in [10, 20, 50]:
            per_page = 10
    except (ValueError, TypeError):
        per_page = 10
    paginator = Paginator(queryset, per_page)
    page_num = request.GET.get('page', 1)
    page = paginator.get_page(page_num)
    
    # 统计数据
    base_queryset = ProjectDeliveryArchive.objects.all()
    total_count = base_queryset.count()
    pending_count = base_queryset.filter(status='pending').count()
    approving_count = base_queryset.filter(status='approving').count()
    archiving_count = base_queryset.filter(status='archiving').count()
    archived_count = base_queryset.filter(status='archived').count()
    
    # 获取项目列表（用于筛选）
    projects = Project.objects.all().order_by('-created_time')[:100]
    
    context = {
        'page': page,
        'status': status,
        'project_id': project_id,
        'search': search,
        'total_count': total_count,
        'pending_count': pending_count,
        'approving_count': approving_count,
        'archiving_count': archiving_count,
        'archived_count': archived_count,
        'projects': projects,
        'full_top_nav': _build_full_top_nav(permission_set, request.user),
        'archive_sidebar_nav': _build_archive_sidebar_nav(permission_set, request.path),
    }
    return render(request, "archive_management/project_delivery_archive_list.html", context)


@login_required
def project_delivery_archive_create(request):
    """创建交付归档"""
    permission_set = get_user_permission_codes(request.user)
    if not _permission_granted('archive_management.add', permission_set):
        from django.http import HttpResponseForbidden
        return HttpResponseForbidden("无权限访问")
    
    # 尝试导入模型
    try:
        from backend.apps.customer_management.models import ProjectDeliveryArchive
        from backend.apps.delivery_customer.models import DeliveryRecord, DeliveryFile
        model_available = True
    except ImportError:
        model_available = False
    
    if not model_available:
        from django.http import HttpResponse
        return HttpResponse("交付归档功能暂未实现，ProjectDeliveryArchive 模型尚未定义", status=503)
    
    if request.method == 'POST':
        delivery_record_id = request.POST.get('delivery_record')
        archive_reason = request.POST.get('archive_reason', '')
        archive_description = request.POST.get('archive_description', '')
        category_id = request.POST.get('category')
        
        if not delivery_record_id:
            from django.contrib import messages
            messages.error(request, "请选择交付记录")
            return redirect('archive_management:project_delivery_archive_create')
        
        delivery_record = get_object_or_404(DeliveryRecord, pk=delivery_record_id)
        
        # 检查是否已经归档
        existing_archive = ProjectDeliveryArchive.objects.filter(
            delivery_record=delivery_record,
            status__in=['pending', 'approving', 'archiving', 'archived']
        ).first()
        
        if existing_archive:
            from django.contrib import messages
            messages.warning(request, f"该交付记录已存在归档记录：{existing_archive.archive_number}")
            return redirect('archive_management:project_delivery_archive_detail', pk=existing_archive.pk)
        
        # 创建归档记录
        archive = ProjectDeliveryArchive.objects.create(
            delivery_record=delivery_record,
            project=delivery_record.project,
            archive_reason=archive_reason,
            archive_description=archive_description,
            applicant=request.user,
            category_id=category_id if category_id else None,
        )
        
        from django.contrib import messages
        messages.success(request, f"交付归档申请创建成功！归档编号：{archive.archive_number}")
        return redirect('archive_management:project_delivery_archive_detail', pk=archive.pk)
    
    # GET请求，显示创建表单
    # 获取可归档的交付记录（排除已归档的）
    delivery_records = DeliveryRecord.objects.exclude(
        status='archived'
    ).select_related('project', 'client').order_by('-created_at')[:100]
    
    categories = ArchiveCategory.objects.filter(category_type='project', is_active=True)
    
    context = {
        'delivery_records': delivery_records,
        'categories': categories,
        'full_top_nav': _build_full_top_nav(permission_set, request.user),
        'archive_sidebar_nav': _build_archive_sidebar_nav(permission_set, request.path),
    }
    return render(request, "archive_management/project_delivery_archive_create.html", context)


@login_required
def project_delivery_archive_detail(request, pk):
    """交付归档详情"""
    permission_set = get_user_permission_codes(request.user)
    if not _permission_granted('archive_management.view', permission_set):
        from django.http import HttpResponseForbidden
        return HttpResponseForbidden("无权限访问")
    
    # 尝试导入模型
    try:
        from backend.apps.customer_management.models import ProjectDeliveryArchive
        from backend.apps.delivery_customer.models import DeliveryFile
        model_available = True
    except ImportError:
        model_available = False
    
    if not model_available:
        from django.http import HttpResponse
        return HttpResponse("交付归档功能暂未实现，ProjectDeliveryArchive 模型尚未定义", status=503)
    
    archive = get_object_or_404(
        ProjectDeliveryArchive.objects.select_related('delivery_record', 'project', 'applicant', 'executor', 'category'),
        pk=pk
    )
    
    # 获取交付文件
    delivery_files = []
    if archive.delivery_record:
        try:
            delivery_files = DeliveryFile.objects.filter(delivery_record=archive.delivery_record)
        except:
            pass
    
    context = {
        'archive': archive,
        'delivery_files': delivery_files,
        'full_top_nav': _build_full_top_nav(permission_set, request.user),
        'archive_sidebar_nav': _build_archive_sidebar_nav(permission_set, request.path),
    }
    return render(request, "archive_management/project_delivery_archive_detail.html", context)


# 档案归还
@login_required
def archive_borrow_return_list(request):
    """档案归还列表 - 显示待归还的借阅记录"""
    permission_set = get_user_permission_codes(request.user)
    if not _permission_granted('archive_management.view', permission_set):
        from django.http import HttpResponseForbidden
        return HttpResponseForbidden("无权限访问")
    
    # 查询待归还的借阅记录（状态为 'out' 或 'approved'）
    queryset = ArchiveBorrow.objects.filter(
        status__in=['out', 'approved']
    ).select_related('borrower', 'project_document', 'administrative_archive', 'borrower_department')
    
    # 筛选
    status = request.GET.get('status', '')
    if status:
        queryset = queryset.filter(status=status)
    
    # 是否逾期
    is_overdue = request.GET.get('is_overdue', '')
    if is_overdue == 'true':
        from django.utils import timezone
        queryset = queryset.filter(return_date__lt=timezone.now().date())
    
    search = request.GET.get('search', '')
    if search:
        queryset = queryset.filter(
            Q(borrow_number__icontains=search) |
            Q(borrower__username__icontains=search) |
            Q(borrower__first_name__icontains=search) |
            Q(borrower__last_name__icontains=search)
        )
    
    # 分页
    page_size = request.GET.get('page_size', '10')
    try:
        per_page = int(page_size)
        if per_page not in [10, 20, 50]:
            per_page = 10
    except (ValueError, TypeError):
        per_page = 10
    paginator = Paginator(queryset, per_page)
    page_num = request.GET.get('page', 1)
    page = paginator.get_page(page_num)
    
    # 统计数据
    base_queryset = ArchiveBorrow.objects.filter(status__in=['out', 'approved'])
    total_count = base_queryset.count()
    out_count = base_queryset.filter(status='out').count()
    approved_count = base_queryset.filter(status='approved').count()
    
    # 逾期统计
    from django.utils import timezone
    overdue_count = base_queryset.filter(return_date__lt=timezone.now().date()).count()
    
    context = {
        'page': page,
        'status': status,
        'is_overdue': is_overdue,
        'search': search,
        'total_count': total_count,
        'out_count': out_count,
        'approved_count': approved_count,
        'overdue_count': overdue_count,
        'full_top_nav': _build_full_top_nav(permission_set, request.user),
        'archive_sidebar_nav': _build_archive_sidebar_nav(permission_set, request.path),
    }
    return render(request, "archive_management/archive_borrow_return_list.html", context)


@login_required
def archive_borrow_return(request, pk):
    """档案归还操作"""
    permission_set = get_user_permission_codes(request.user)
    if not _permission_granted('archive_management.view', permission_set):
        from django.http import HttpResponseForbidden
        return HttpResponseForbidden("无权限访问")
    
    borrow = get_object_or_404(
        ArchiveBorrow.objects.select_related('borrower', 'project_document', 'administrative_archive'),
        pk=pk
    )
    
    # 检查是否可以归还（状态必须是 'out' 或 'approved'）
    if borrow.status not in ['out', 'approved']:
        from django.contrib import messages
        messages.error(request, f"该借阅记录状态为'{borrow.get_status_display()}'，无法归还。")
        from django.shortcuts import redirect
        return redirect('archive_management:archive_borrow_return_list')
    
    if request.method == 'POST':
        # 处理归还
        return_status = request.POST.get('return_status', '完好')
        return_notes = request.POST.get('return_notes', '')
        
        from django.utils import timezone
        borrow.returned_time = timezone.now()
        borrow.returned_by = request.user
        borrow.return_status = return_status
        borrow.return_notes = return_notes
        borrow.status = 'returned'
        borrow.save()
        
        # 更新档案状态（如果档案存在）
        if borrow.project_document:
            borrow.project_document.status = 'archived'  # 归还后恢复为已归档状态
            borrow.project_document.save()
        elif borrow.administrative_archive:
            borrow.administrative_archive.status = 'archived'  # 归还后恢复为已归档状态
            borrow.administrative_archive.save()
        
        # 记录操作日志
        archive_name = ''
        if borrow.project_document:
            archive_name = borrow.project_document.document_name
        elif borrow.administrative_archive:
            archive_name = borrow.administrative_archive.archive_name
        
        ArchiveOperationLogService.log_from_request(
            request,
            operation_type='return',
            operation_content=f'归还档案：{archive_name}（借阅单号：{borrow.borrow_number}）',
            operation_result='success',
            borrow_record=borrow,
            project_document=borrow.project_document,
            administrative_archive=borrow.administrative_archive,
            extra_data={'return_status': return_status, 'return_notes': return_notes}
        )
        
        from django.contrib import messages
        messages.success(request, f"档案归还成功！借阅单号：{borrow.borrow_number}")
        from django.shortcuts import redirect
        return redirect('archive_management:archive_borrow_return_list')
    
    # GET请求，显示归还表单
    context = {
        'borrow': borrow,
        'full_top_nav': _build_full_top_nav(permission_set, request.user),
        'archive_sidebar_nav': _build_archive_sidebar_nav(permission_set, request.path),
    }
    return render(request, "archive_management/archive_borrow_return.html", context)


# 档案分类规则
@login_required
def archive_category_rule(request):
    """档案分类规则管理"""
    permission_set = get_user_permission_codes(request.user)
    if not _permission_granted('archive_management.view', permission_set):
        from django.http import HttpResponseForbidden
        return HttpResponseForbidden("无权限访问")
    
    try:
        from backend.apps.archive_management.models import ArchiveCategoryRule
        model_available = True
    except ImportError:
        model_available = False
    
    if not model_available:
        from django.http import HttpResponse
        return HttpResponse("ArchiveCategoryRule模型未定义", status=503)
    
    # 查询规则列表
    queryset = ArchiveCategoryRule.objects.all().select_related('category', 'created_by').order_by('-priority', '-created_time')
    
    # 筛选
    rule_type = request.GET.get('rule_type', '')
    if rule_type:
        queryset = queryset.filter(rule_type=rule_type)
    
    status_filter = request.GET.get('status', '')
    if status_filter:
        queryset = queryset.filter(status=status_filter)
    
    is_active = request.GET.get('is_active', '')
    if is_active == 'true':
        queryset = queryset.filter(is_active=True)
    elif is_active == 'false':
        queryset = queryset.filter(is_active=False)
    
    category_id = request.GET.get('category', '')
    if category_id:
        queryset = queryset.filter(category_id=category_id)
    
    search = request.GET.get('search', '')
    if search:
        queryset = queryset.filter(
            Q(name__icontains=search) |
            Q(description__icontains=search) |
            Q(category__name__icontains=search)
        )
    
    # 分页
    page_size = request.GET.get('page_size', '10')
    try:
        per_page = int(page_size)
        if per_page not in [10, 20, 50]:
            per_page = 10
    except (ValueError, TypeError):
        per_page = 10
    paginator = Paginator(queryset, per_page)
    page_num = request.GET.get('page', 1)
    page = paginator.get_page(page_num)
    
    # 统计数据
    total_count = ArchiveCategoryRule.objects.count()
    active_count = ArchiveCategoryRule.objects.filter(is_active=True, status='active').count()
    auto_count = ArchiveCategoryRule.objects.filter(rule_type='auto').count()
    manual_count = ArchiveCategoryRule.objects.filter(rule_type='manual').count()
    
    # 获取分类列表（用于筛选）
    categories = ArchiveCategory.objects.filter(is_active=True).order_by('category_type', 'order', 'id')
    
    context = {
        'page': page,
        'rule_type': rule_type,
        'status': status_filter,
        'is_active': is_active,
        'category_id': category_id,
        'search': search,
        'total_count': total_count,
        'active_count': active_count,
        'auto_count': auto_count,
        'manual_count': manual_count,
        'categories': categories,
        'full_top_nav': _build_full_top_nav(permission_set, request.user),
        'archive_sidebar_nav': _build_archive_sidebar_nav(permission_set, request.path),
    }
    return render(request, "archive_management/archive_category_rule.html", context)


@login_required
def archive_category_rule_create(request):
    """创建档案分类规则"""
    permission_set = get_user_permission_codes(request.user)
    if not _permission_granted('archive_management.add', permission_set):
        from django.http import HttpResponseForbidden
        return HttpResponseForbidden("无权限访问")
    
    try:
        from backend.apps.archive_management.models import ArchiveCategoryRule
        from .forms import ArchiveCategoryRuleForm
        model_available = True
    except ImportError:
        model_available = False
    
    if not model_available:
        from django.http import HttpResponse
        return HttpResponse("ArchiveCategoryRule模型未定义", status=503)
    
    if request.method == 'POST':
        form = ArchiveCategoryRuleForm(request.POST)
        if form.is_valid():
            rule = form.save(commit=False)
            rule.created_by = request.user
            rule.save()
            messages.success(request, f'分类规则创建成功：{rule.name}')
            return redirect('archive_management:archive_category_rule')
        else:
            messages.error(request, '表单验证失败，请检查输入信息')
    else:
        form = ArchiveCategoryRuleForm()
    
    # 获取分类列表
    categories = ArchiveCategory.objects.filter(is_active=True).order_by('category_type', 'order', 'id')
    
    context = {
        'form': form,
        'categories': categories,
        'full_top_nav': _build_full_top_nav(permission_set, request.user),
        'archive_sidebar_nav': _build_archive_sidebar_nav(permission_set, request.path),
    }
    return render(request, "archive_management/archive_category_rule_create.html", context)


@login_required
def archive_category_rule_edit(request, pk):
    """编辑档案分类规则"""
    permission_set = get_user_permission_codes(request.user)
    if not _permission_granted('archive_management.change', permission_set):
        from django.http import HttpResponseForbidden
        return HttpResponseForbidden("无权限访问")
    
    try:
        from backend.apps.archive_management.models import ArchiveCategoryRule
        from .forms import ArchiveCategoryRuleForm
        model_available = True
    except ImportError:
        model_available = False
    
    if not model_available:
        from django.http import HttpResponse
        return HttpResponse("ArchiveCategoryRule模型未定义", status=503)
    
    rule = get_object_or_404(ArchiveCategoryRule, pk=pk)
    
    if request.method == 'POST':
        form = ArchiveCategoryRuleForm(request.POST, instance=rule)
        if form.is_valid():
            form.save()
            messages.success(request, f'分类规则更新成功：{rule.name}')
            return redirect('archive_management:archive_category_rule')
        else:
            messages.error(request, '表单验证失败，请检查输入信息')
    else:
        form = ArchiveCategoryRuleForm(instance=rule)
    
    # 获取分类列表
    categories = ArchiveCategory.objects.filter(is_active=True).order_by('category_type', 'order', 'id')
    
    context = {
        'form': form,
        'rule': rule,
        'categories': categories,
        'full_top_nav': _build_full_top_nav(permission_set, request.user),
        'archive_sidebar_nav': _build_archive_sidebar_nav(permission_set, request.path),
    }
    return render(request, "archive_management/archive_category_rule_edit.html", context)


@login_required
def archive_category_rule_test(request, pk):
    """测试档案分类规则"""
    permission_set = get_user_permission_codes(request.user)
    if not _permission_granted('archive_management.view', permission_set):
        from django.http import HttpResponseForbidden
        return HttpResponseForbidden("无权限访问")
    
    try:
        from backend.apps.archive_management.models import ArchiveCategoryRule
        model_available = True
    except ImportError:
        model_available = False
    
    if not model_available:
        from django.http import HttpResponse
        return HttpResponse("ArchiveCategoryRule模型未定义", status=503)
    
    rule = get_object_or_404(ArchiveCategoryRule, pk=pk)
    
    if request.method == 'POST':
        import json
        test_data_str = request.POST.get('test_data', '{}')
        try:
            test_data = json.loads(test_data_str) if isinstance(test_data_str, str) else test_data_str
            match_result = rule.test_rule(test_data)
            context = {
                'rule': rule,
                'test_data': test_data_str,
                'match_result': match_result,
                'full_top_nav': _build_full_top_nav(permission_set, request.user),
                'archive_sidebar_nav': _build_archive_sidebar_nav(permission_set, request.path),
            }
            return render(request, "archive_management/archive_category_rule_test.html", context)
        except json.JSONDecodeError:
            messages.error(request, '测试数据必须是有效的JSON格式')
    
    # GET请求，显示测试表单
    # 提供示例数据
    example_data = {
        "project_name": "测试项目",
        "status": "completed",
        "project_number": "PRJ-2025-001"
    }
    import json
    example_json = json.dumps(example_data, ensure_ascii=False, indent=2)
    
    context = {
        'rule': rule,
        'example_data': example_json,
        'full_top_nav': _build_full_top_nav(permission_set, request.user),
        'archive_sidebar_nav': _build_archive_sidebar_nav(permission_set, request.path),
    }
    return render(request, "archive_management/archive_category_rule_test.html", context)


# 档案安全
@login_required
def archive_security_permission(request):
    """档案权限管理"""
    permission_set = get_user_permission_codes(request.user)
    if not _permission_granted('archive_management.view', permission_set):
        from django.http import HttpResponseForbidden
        return HttpResponseForbidden("无权限访问")
    
    from backend.apps.system_management.models import User, Department
    from django.db.models import Count, Q
    
    # 获取用户列表（有档案操作记录的用户）
    users_with_operations = User.objects.filter(
        archive_operations__isnull=False
    ).distinct().annotate(
        operation_count=Count('archive_operations')
    ).order_by('-operation_count')[:100]
    
    # 获取部门列表
    departments = Department.objects.filter(is_active=True).order_by('name')
    
    # 权限统计
    total_users = User.objects.filter(is_active=True).count()
    users_with_permission = User.objects.filter(
        user_permissions__permission_code__startswith='archive_management'
    ).distinct().count()
    
    # 按部门统计权限
    department_permission_stats = []
    for dept in departments:
        dept_users = User.objects.filter(department=dept, is_active=True)
        dept_with_permission = dept_users.filter(
            user_permissions__permission_code__startswith='archive_management'
        ).distinct().count()
        department_permission_stats.append({
            'department': dept,
            'total_users': dept_users.count(),
            'users_with_permission': dept_with_permission,
        })
    
    context = {
        'users_with_operations': users_with_operations,
        'departments': departments,
        'total_users': total_users,
        'users_with_permission': users_with_permission,
        'department_permission_stats': department_permission_stats,
        'full_top_nav': _build_full_top_nav(permission_set, request.user),
        'archive_sidebar_nav': _build_archive_sidebar_nav(permission_set, request.path),
    }
    return render(request, "archive_management/archive_security_permission.html", context)


@login_required
def archive_security_access(request):
    """档案访问控制"""
    permission_set = get_user_permission_codes(request.user)
    if not _permission_granted('archive_management.view', permission_set):
        from django.http import HttpResponseForbidden
        return HttpResponseForbidden("无权限访问")
    
    try:
        from backend.apps.customer_management.models import ArchiveOperationLog
        model_available = True
    except ImportError:
        model_available = False
    
    from django.utils import timezone
    from datetime import timedelta
    from django.db.models import Count, Q
    
    # 时间范围筛选
    days = request.GET.get('days', '7')  # 默认7天
    try:
        days = int(days)
    except:
        days = 7
    
    start_date = timezone.now() - timedelta(days=days)
    
    if model_available:
        # 访问统计
        access_stats = ArchiveOperationLog.objects.filter(
            operation_time__gte=start_date,
            operation_type__in=['view', 'download']
        ).values('operator').annotate(
            view_count=Count('id', filter=Q(operation_type='view')),
            download_count=Count('id', filter=Q(operation_type='download'))
        ).order_by('-view_count')[:50]
        
        # IP访问统计
        ip_stats = ArchiveOperationLog.objects.filter(
            operation_time__gte=start_date
        ).exclude(ip_address__isnull=True).values('ip_address').annotate(
            count=Count('id')
        ).order_by('-count')[:20]
        
        # 异常访问（失败的操作）
        failed_operations = ArchiveOperationLog.objects.filter(
            operation_time__gte=start_date,
            operation_result='failed'
        ).select_related('operator').order_by('-operation_time')[:50]
        
        # 访问时间分布（按小时）
        hour_distribution = []
        for hour in range(24):
            count = ArchiveOperationLog.objects.filter(
                operation_time__gte=start_date,
                operation_time__hour=hour
            ).count()
            hour_distribution.append({
                'hour': hour,
                'count': count
            })
    else:
        access_stats = []
        ip_stats = []
        failed_operations = []
        hour_distribution = []
    
    context = {
        'days': days,
        'access_stats': access_stats,
        'ip_stats': ip_stats,
        'failed_operations': failed_operations,
        'hour_distribution': hour_distribution,
        'full_top_nav': _build_full_top_nav(permission_set, request.user),
        'archive_sidebar_nav': _build_archive_sidebar_nav(permission_set, request.path),
    }
    return render(request, "archive_management/archive_security_access.html", context)


@login_required
def archive_security_log(request):
    """档案操作日志"""
    permission_set = get_user_permission_codes(request.user)
    if not _permission_granted('archive_management.view', permission_set):
        from django.http import HttpResponseForbidden
        return HttpResponseForbidden("无权限访问")
    
    # 尝试导入ArchiveOperationLog模型
    try:
        from backend.apps.customer_management.models import ArchiveOperationLog
        model_available = True
    except ImportError:
        model_available = False
    
    if not model_available:
        from django.http import HttpResponse
        return HttpResponse("档案操作日志功能暂未实现，ArchiveOperationLog 模型尚未定义", status=503)
    
    queryset = ArchiveOperationLog.objects.all().select_related(
        'operator', 'project_document', 'administrative_archive', 'project_archive', 'borrow_record'
    )
    
    # 筛选
    operation_type = request.GET.get('operation_type', '')
    if operation_type:
        queryset = queryset.filter(operation_type=operation_type)
    
    operation_result = request.GET.get('operation_result', '')
    if operation_result:
        queryset = queryset.filter(operation_result=operation_result)
    
    operator_id = request.GET.get('operator', '')
    if operator_id:
        queryset = queryset.filter(operator_id=operator_id)
    
    # 时间范围筛选
    start_date = request.GET.get('start_date', '')
    end_date = request.GET.get('end_date', '')
    if start_date:
        from django.utils.dateparse import parse_date
        try:
            start_date_obj = parse_date(start_date)
            if start_date_obj:
                from django.utils import timezone
                queryset = queryset.filter(operation_time__gte=timezone.make_aware(
                    timezone.datetime.combine(start_date_obj, timezone.datetime.min.time())
                ))
        except:
            pass
    
    if end_date:
        from django.utils.dateparse import parse_date
        try:
            end_date_obj = parse_date(end_date)
            if end_date_obj:
                from django.utils import timezone
                queryset = queryset.filter(operation_time__lte=timezone.make_aware(
                    timezone.datetime.combine(end_date_obj, timezone.datetime.max.time())
                ))
        except:
            pass
    
    search = request.GET.get('search', '')
    if search:
        queryset = queryset.filter(
            Q(operation_content__icontains=search) |
            Q(project_document__document_name__icontains=search) |
            Q(administrative_archive__archive_name__icontains=search) |
            Q(operator__username__icontains=search) |
            Q(operator__first_name__icontains=search) |
            Q(operator__last_name__icontains=search)
        )
    
    # 分页
    paginator = Paginator(queryset, 50)  # 日志记录较多，每页50条
    page_num = request.GET.get('page', 1)
    page = paginator.get_page(page_num)
    
    # 统计数据
    base_queryset = ArchiveOperationLog.objects.all()
    total_count = base_queryset.count()
    success_count = base_queryset.filter(operation_result='success').count()
    failed_count = base_queryset.filter(operation_result='failed').count()
    
    # 操作类型统计
    operation_type_stats = {}
    for op_type, op_name in ArchiveOperationLog.OPERATION_TYPE_CHOICES:
        operation_type_stats[op_type] = {
            'name': op_name,
            'count': base_queryset.filter(operation_type=op_type).count()
        }
    
    # 最近7天的操作统计
    from django.utils import timezone
    from datetime import timedelta
    seven_days_ago = timezone.now() - timedelta(days=7)
    recent_count = base_queryset.filter(operation_time__gte=seven_days_ago).count()
    
    # 获取操作人列表（用于筛选）
    operators = User.objects.filter(
        archive_operations__isnull=False
    ).distinct().order_by('username')[:50]
    
    context = {
        'page': page,
        'operation_type': operation_type,
        'operation_result': operation_result,
        'operator_id': operator_id,
        'start_date': start_date,
        'end_date': end_date,
        'search': search,
        'total_count': total_count,
        'success_count': success_count,
        'failed_count': failed_count,
        'recent_count': recent_count,
        'operation_type_stats': operation_type_stats,
        'operators': operators,
        'full_top_nav': _build_full_top_nav(permission_set, request.user),
        'archive_sidebar_nav': _build_archive_sidebar_nav(permission_set, request.path),
    }
    return render(request, "archive_management/archive_security_log.html", context)


@login_required
def archive_security_audit(request):
    """档案安全审计"""
    permission_set = get_user_permission_codes(request.user)
    if not _permission_granted('archive_management.view', permission_set):
        from django.http import HttpResponseForbidden
        return HttpResponseForbidden("无权限访问")
    
    try:
        from backend.apps.customer_management.models import ArchiveOperationLog
        model_available = True
    except ImportError:
        model_available = False
    
    if not model_available:
        from django.http import HttpResponse
        return HttpResponse("档案操作日志功能暂未实现，ArchiveOperationLog 模型尚未定义", status=503)
    
    from django.utils import timezone
    from datetime import timedelta
    from django.db.models import Count, Q
    
    # 时间范围筛选
    days = request.GET.get('days', '30')  # 默认30天
    try:
        days = int(days)
    except:
        days = 30
    
    start_date = timezone.now() - timedelta(days=days)
    
    # 审计统计
    base_queryset = ArchiveOperationLog.objects.filter(operation_time__gte=start_date)
    
    # 操作类型统计
    operation_type_stats = base_queryset.values('operation_type').annotate(
        count=Count('id'),
        success_count=Count('id', filter=Q(operation_result='success')),
        failed_count=Count('id', filter=Q(operation_result='failed'))
    ).order_by('-count')
    
    # 高风险操作（删除、销毁）
    high_risk_operations = base_queryset.filter(
        operation_type__in=['delete', 'destroy']
    ).select_related('operator', 'project_document', 'administrative_archive').order_by('-operation_time')
    
    # 失败操作统计
    failed_operations = base_queryset.filter(
        operation_result='failed'
    ).select_related('operator').order_by('-operation_time')[:100]
    
    # 异常IP访问（同一IP多次失败）
    suspicious_ips = base_queryset.filter(
        operation_result='failed'
    ).exclude(ip_address__isnull=True).values('ip_address').annotate(
        failed_count=Count('id'),
        total_count=Count('id')
    ).filter(failed_count__gte=3).order_by('-failed_count')[:20]
    
    # 用户操作统计（操作次数最多的用户）
    top_operators = base_queryset.values('operator__username', 'operator__first_name', 'operator__last_name').annotate(
        count=Count('id')
    ).order_by('-count')[:20]
    
    # 审计报告数据
    audit_report = {
        'total_operations': base_queryset.count(),
        'success_operations': base_queryset.filter(operation_result='success').count(),
        'failed_operations': base_queryset.filter(operation_result='failed').count(),
        'high_risk_count': high_risk_operations.count(),
        'unique_users': base_queryset.values('operator').distinct().count(),
        'unique_ips': base_queryset.exclude(ip_address__isnull=True).values('ip_address').distinct().count(),
    }
    
    context = {
        'days': days,
        'start_date': start_date,
        'operation_type_stats': list(operation_type_stats),
        'high_risk_operations': high_risk_operations[:50],
        'failed_operations': failed_operations,
        'suspicious_ips': list(suspicious_ips),
        'top_operators': list(top_operators),
        'audit_report': audit_report,
        'full_top_nav': _build_full_top_nav(permission_set, request.user),
        'archive_sidebar_nav': _build_archive_sidebar_nav(permission_set, request.path),
    }
    return render(request, "archive_management/archive_security_audit.html", context)


# 档案检索（增强功能）
@login_required
def archive_search_fulltext(request):
    """档案全文检索"""
    permission_set = get_user_permission_codes(request.user)
    if not _permission_granted('archive_management.view', permission_set):
        from django.http import HttpResponseForbidden
        return HttpResponseForbidden("无权限访问")
    
    import time
    start_time = time.time()
    
    # 尝试导入检索历史模型
    try:
        from backend.apps.customer_management.models import ArchiveSearchHistory
        history_available = True
    except ImportError:
        history_available = False
    
    # 获取检索参数
    keyword = request.GET.get('keyword', '').strip()
    search_range = request.GET.get('search_range', 'all')  # all, project, administrative
    archive_type = request.GET.get('archive_type', '')  # document, archive
    page_num = request.GET.get('page', 1)
    
    results = []
    result_count = 0
    
    if keyword:
        # 检索项目文档
        if search_range in ['all', 'project']:
            project_docs = ProjectArchiveDocument.objects.filter(
                Q(document_name__icontains=keyword) |
                Q(document_number__icontains=keyword) |
                Q(description__icontains=keyword)
            ).select_related('project', 'category', 'uploaded_by')
            
            if archive_type == 'document' or not archive_type:
                for doc in project_docs:
                    results.append({
                        'type': 'project_document',
                        'id': doc.id,
                        'title': doc.document_name,
                        'number': doc.document_number,
                        'description': doc.description,
                        'project': doc.project,
                        'category': doc.category,
                        'status': doc.status,
                        'created_time': doc.created_time,
                        'url': reverse('archive_management:project_document_detail', args=[doc.id]),
                    })
        
        # 检索行政档案
        if search_range in ['all', 'administrative']:
            admin_archives = AdministrativeArchive.objects.filter(
                Q(archive_name__icontains=keyword) |
                Q(archive_number__icontains=keyword) |
                Q(description__icontains=keyword)
            ).select_related('category', 'archivist')
            
            if archive_type == 'archive' or not archive_type:
                for archive in admin_archives:
                    results.append({
                        'type': 'administrative_archive',
                        'id': archive.id,
                        'title': archive.archive_name,
                        'number': archive.archive_number,
                        'description': archive.description,
                        'category': archive.category,
                        'status': archive.status,
                        'created_time': archive.created_time,
                        'url': reverse('archive_management:administrative_archive_detail', args=[archive.id]),
                    })
        
        # 检索项目归档
        if search_range in ['all', 'project']:
            project_archives = ArchiveProjectArchive.objects.filter(
                Q(archive_number__icontains=keyword) |
                Q(archive_reason__icontains=keyword) |
                Q(archive_description__icontains=keyword)
            ).select_related('project', 'applicant')
            
            for archive in project_archives:
                results.append({
                    'type': 'project_archive',
                    'id': archive.id,
                    'title': f"项目归档 - {archive.archive_number}",
                    'number': archive.archive_number,
                    'description': archive.archive_description or archive.archive_reason,
                    'project': archive.project,
                    'status': archive.status,
                    'created_time': archive.applied_time,
                    'url': reverse('archive_management:project_archive_detail', args=[archive.id]),
                })
        
        result_count = len(results)
        
        # 保存检索历史
        if history_available and keyword:
            search_duration = time.time() - start_time
            ArchiveSearchHistory.objects.create(
                searcher=request.user,
                search_type='fulltext',
                search_keyword=keyword,
                search_range=search_range,
                result_count=result_count,
                search_duration=search_duration,
            )
    
    # 分页
    paginator = Paginator(results, 20)
    page = paginator.get_page(page_num)
    
    # 检索耗时
    search_duration = time.time() - start_time
    
    context = {
        'keyword': keyword,
        'search_range': search_range,
        'archive_type': archive_type,
        'page': page,
        'result_count': result_count,
        'search_duration': round(search_duration, 3),
        'full_top_nav': _build_full_top_nav(permission_set, request.user),
        'archive_sidebar_nav': _build_archive_sidebar_nav(permission_set, request.path),
    }
    return render(request, "archive_management/archive_search_fulltext.html", context)


@login_required
def archive_search_advanced(request):
    """档案高级检索"""
    permission_set = get_user_permission_codes(request.user)
    if not _permission_granted('archive_management.view', permission_set):
        from django.http import HttpResponseForbidden
        return HttpResponseForbidden("无权限访问")
    
    import time
    start_time = time.time()
    
    # 尝试导入检索历史模型
    try:
        from backend.apps.customer_management.models import ArchiveSearchHistory
        history_available = True
    except ImportError:
        history_available = False
    
    # 获取检索条件
    archive_name = request.GET.get('archive_name', '').strip()
    archive_number = request.GET.get('archive_number', '').strip()
    category_id = request.GET.get('category', '')
    archive_type = request.GET.get('archive_type', 'all')  # all, project, administrative
    status = request.GET.get('status', '')
    start_date = request.GET.get('start_date', '')
    end_date = request.GET.get('end_date', '')
    project_id = request.GET.get('project', '')
    page_num = request.GET.get('page', 1)
    
    results = []
    result_count = 0
    
    # 构建检索条件
    has_conditions = any([archive_name, archive_number, category_id, status, start_date, end_date, project_id])
    
    if has_conditions or request.method == 'GET':
        # 检索项目文档
        if archive_type in ['all', 'project']:
            project_docs = ProjectArchiveDocument.objects.all()
            
            if archive_name:
                project_docs = project_docs.filter(document_name__icontains=archive_name)
            if archive_number:
                project_docs = project_docs.filter(document_number__icontains=archive_number)
            if category_id:
                project_docs = project_docs.filter(category_id=category_id)
            if status:
                project_docs = project_docs.filter(status=status)
            if start_date:
                from django.utils.dateparse import parse_date
                try:
                    start_date_obj = parse_date(start_date)
                    if start_date_obj:
                        from django.utils import timezone
                        project_docs = project_docs.filter(created_time__gte=timezone.make_aware(
                            timezone.datetime.combine(start_date_obj, timezone.datetime.min.time())
                        ))
                except:
                    pass
            if end_date:
                from django.utils.dateparse import parse_date
                try:
                    end_date_obj = parse_date(end_date)
                    if end_date_obj:
                        from django.utils import timezone
                        project_docs = project_docs.filter(created_time__lte=timezone.make_aware(
                            timezone.datetime.combine(end_date_obj, timezone.datetime.max.time())
                        ))
                except:
                    pass
            if project_id:
                project_docs = project_docs.filter(project_id=project_id)
            
            project_docs = project_docs.select_related('project', 'category', 'uploaded_by')
            
            for doc in project_docs:
                results.append({
                    'type': 'project_document',
                    'id': doc.id,
                    'title': doc.document_name,
                    'number': doc.document_number,
                    'description': doc.description,
                    'project': doc.project,
                    'category': doc.category,
                    'status': doc.status,
                    'created_time': doc.created_time,
                    'url': reverse('archive_management:project_document_detail', args=[doc.id]),
                })
        
        # 检索行政档案
        if archive_type in ['all', 'administrative']:
            admin_archives = AdministrativeArchive.objects.all()
            
            if archive_name:
                admin_archives = admin_archives.filter(archive_name__icontains=archive_name)
            if archive_number:
                admin_archives = admin_archives.filter(archive_number__icontains=archive_number)
            if category_id:
                admin_archives = admin_archives.filter(category_id=category_id)
            if status:
                admin_archives = admin_archives.filter(status=status)
            if start_date:
                from django.utils.dateparse import parse_date
                try:
                    start_date_obj = parse_date(start_date)
                    if start_date_obj:
                        from django.utils import timezone
                        admin_archives = admin_archives.filter(created_time__gte=timezone.make_aware(
                            timezone.datetime.combine(start_date_obj, timezone.datetime.min.time())
                        ))
                except:
                    pass
            if end_date:
                from django.utils.dateparse import parse_date
                try:
                    end_date_obj = parse_date(end_date)
                    if end_date_obj:
                        from django.utils import timezone
                        admin_archives = admin_archives.filter(created_time__lte=timezone.make_aware(
                            timezone.datetime.combine(end_date_obj, timezone.datetime.max.time())
                        ))
                except:
                    pass
            
            admin_archives = admin_archives.select_related('category', 'archivist')
            
            for archive in admin_archives:
                results.append({
                    'type': 'administrative_archive',
                    'id': archive.id,
                    'title': archive.archive_name,
                    'number': archive.archive_number,
                    'description': archive.description,
                    'category': archive.category,
                    'status': archive.status,
                    'created_time': archive.created_time,
                    'url': reverse('archive_management:administrative_archive_detail', args=[archive.id]),
                })
        
        result_count = len(results)
        
        # 保存检索历史
        if history_available and has_conditions:
            search_duration = time.time() - start_time
            search_conditions = {
                'archive_name': archive_name,
                'archive_number': archive_number,
                'category_id': category_id,
                'archive_type': archive_type,
                'status': status,
                'start_date': start_date,
                'end_date': end_date,
                'project_id': project_id,
            }
            ArchiveSearchHistory.objects.create(
                searcher=request.user,
                search_type='advanced',
                search_conditions=search_conditions,
                search_range=archive_type,
                result_count=result_count,
                search_duration=search_duration,
            )
    
    # 分页
    paginator = Paginator(results, 20)
    page = paginator.get_page(page_num)
    
    # 检索耗时
    search_duration = time.time() - start_time
    
    # 获取分类列表（用于筛选）
    categories = ArchiveCategory.objects.filter(is_active=True).order_by('category_type', 'order', 'id')
    
    # 获取项目列表（用于筛选）
    projects = Project.objects.all().order_by('-created_time')[:100]
    
    context = {
        'archive_name': archive_name,
        'archive_number': archive_number,
        'category_id': category_id,
        'archive_type': archive_type,
        'status': status,
        'start_date': start_date,
        'end_date': end_date,
        'project_id': project_id,
        'page': page,
        'result_count': result_count,
        'search_duration': round(search_duration, 3),
        'categories': categories,
        'projects': projects,
        'full_top_nav': _build_full_top_nav(permission_set, request.user),
        'archive_sidebar_nav': _build_archive_sidebar_nav(permission_set, request.path),
    }
    return render(request, "archive_management/archive_search_advanced.html", context)


@login_required
def archive_search_history(request):
    """档案检索历史"""
    permission_set = get_user_permission_codes(request.user)
    if not _permission_granted('archive_management.view', permission_set):
        from django.http import HttpResponseForbidden
        return HttpResponseForbidden("无权限访问")
    
    # 尝试导入检索历史模型
    try:
        from backend.apps.customer_management.models import ArchiveSearchHistory
        model_available = True
    except ImportError:
        model_available = False
    
    if not model_available:
        from django.http import HttpResponse
        return HttpResponse("档案检索历史功能暂未实现，ArchiveSearchHistory 模型尚未定义", status=503)
    
    # 只显示当前用户的检索历史
    queryset = ArchiveSearchHistory.objects.filter(searcher=request.user).select_related('searcher')
    
    # 筛选
    search_type = request.GET.get('search_type', '')
    if search_type:
        queryset = queryset.filter(search_type=search_type)
    
    # 分页
    page_size = request.GET.get('page_size', '10')
    try:
        per_page = int(page_size)
        if per_page not in [10, 20, 50]:
            per_page = 10
    except (ValueError, TypeError):
        per_page = 10
    paginator = Paginator(queryset, per_page)
    page_num = request.GET.get('page', 1)
    page = paginator.get_page(page_num)
    
    # 统计数据
    base_queryset = ArchiveSearchHistory.objects.filter(searcher=request.user)
    total_count = base_queryset.count()
    fulltext_count = base_queryset.filter(search_type='fulltext').count()
    advanced_count = base_queryset.filter(search_type='advanced').count()
    
    context = {
        'page': page,
        'search_type': search_type,
        'total_count': total_count,
        'fulltext_count': fulltext_count,
        'advanced_count': advanced_count,
        'full_top_nav': _build_full_top_nav(permission_set, request.user),
        'archive_sidebar_nav': _build_archive_sidebar_nav(permission_set, request.path),
    }
    return render(request, "archive_management/archive_search_history.html", context)


# 档案数字化
@login_required
def archive_digitization_apply_list(request):
    """档案数字化申请列表"""
    permission_set = get_user_permission_codes(request.user)
    if not _permission_granted('archive_management.view', permission_set):
        from django.http import HttpResponseForbidden
        return HttpResponseForbidden("无权限访问")
    
    try:
        from backend.apps.customer_management.models import ArchiveDigitizationApply
        model_available = True
    except ImportError:
        model_available = False
    
    if not model_available:
        from django.http import HttpResponse
        return HttpResponse("档案数字化功能暂未实现，ArchiveDigitizationApply 模型尚未定义", status=503)
    
    queryset = ArchiveDigitizationApply.objects.all().select_related(
        'applicant', 'approver', 'processor', 'project_document', 'administrative_archive'
    )
    
    # 筛选
    status = request.GET.get('status', '')
    if status:
        queryset = queryset.filter(status=status)
    
    digitization_type = request.GET.get('digitization_type', '')
    if digitization_type:
        queryset = queryset.filter(digitization_type=digitization_type)
    
    priority = request.GET.get('priority', '')
    if priority:
        queryset = queryset.filter(priority=priority)
    
    # 只显示当前用户的申请（除非有查看所有权限）
    if not _permission_granted('archive_management.view_all', permission_set):
        queryset = queryset.filter(applicant=request.user)
    
    search = request.GET.get('search', '')
    if search:
        queryset = queryset.filter(
            Q(apply_number__icontains=search) |
            Q(apply_reason__icontains=search) |
            Q(apply_description__icontains=search)
        )
    
    # 分页
    page_size = request.GET.get('page_size', '10')
    try:
        per_page = int(page_size)
        if per_page not in [10, 20, 50]:
            per_page = 10
    except (ValueError, TypeError):
        per_page = 10
    paginator = Paginator(queryset, per_page)
    page_num = request.GET.get('page', 1)
    page = paginator.get_page(page_num)
    
    # 统计数据
    base_queryset = ArchiveDigitizationApply.objects.all()
    if not _permission_granted('archive_management.view_all', permission_set):
        base_queryset = base_queryset.filter(applicant=request.user)
    
    total_count = base_queryset.count()
    pending_count = base_queryset.filter(status='pending').count()
    approved_count = base_queryset.filter(status='approved').count()
    processing_count = base_queryset.filter(status='processing').count()
    completed_count = base_queryset.filter(status='completed').count()
    
    context = {
        'page': page,
        'status': status,
        'digitization_type': digitization_type,
        'priority': priority,
        'search': search,
        'total_count': total_count,
        'pending_count': pending_count,
        'approved_count': approved_count,
        'processing_count': processing_count,
        'completed_count': completed_count,
        'full_top_nav': _build_full_top_nav(permission_set, request.user),
        'archive_sidebar_nav': _build_archive_sidebar_nav(permission_set, request.path),
    }
    return render(request, "archive_management/archive_digitization_apply_list.html", context)


@login_required
def archive_digitization_apply_create(request):
    """创建档案数字化申请"""
    permission_set = get_user_permission_codes(request.user)
    if not _permission_granted('archive_management.add', permission_set):
        from django.http import HttpResponseForbidden
        return HttpResponseForbidden("无权限访问")
    
    try:
        from backend.apps.customer_management.models import ArchiveDigitizationApply
        model_available = True
    except ImportError:
        model_available = False
    
    if not model_available:
        from django.http import HttpResponse
        return HttpResponse("档案数字化功能暂未实现，ArchiveDigitizationApply 模型尚未定义", status=503)
    
    if request.method == 'POST':
        project_document_id = request.POST.get('project_document')
        administrative_archive_id = request.POST.get('administrative_archive')
        digitization_type = request.POST.get('digitization_type')
        priority = request.POST.get('priority', 'normal')
        apply_reason = request.POST.get('apply_reason', '')
        apply_description = request.POST.get('apply_description', '')
        
        if not (project_document_id or administrative_archive_id):
            messages.error(request, '请选择要数字化的档案')
            return redirect('archive_management:archive_digitization_apply_create')
        
        if not digitization_type:
            messages.error(request, '请选择数字化类型')
            return redirect('archive_management:archive_digitization_apply_create')
        
        # 创建申请
        apply = ArchiveDigitizationApply.objects.create(
            project_document_id=int(project_document_id) if project_document_id else None,
            administrative_archive_id=int(administrative_archive_id) if administrative_archive_id else None,
            digitization_type=digitization_type,
            priority=priority,
            apply_reason=apply_reason,
            apply_description=apply_description,
            applicant=request.user,
            status='pending',
        )
        
        messages.success(request, f'数字化申请已提交，申请编号：{apply.apply_number}')
        return redirect('archive_management:archive_digitization_apply_list')
    
    # GET请求，显示创建表单
    # 获取可申请的项目文档
    project_documents = ProjectArchiveDocument.objects.filter(
        status__in=['archived', 'pending_archive']
    ).select_related('project', 'category').order_by('-uploaded_time')[:100]
    
    # 获取可申请的行政档案
    administrative_archives = AdministrativeArchive.objects.filter(
        status='archived'
    ).select_related('category', 'archive_department').order_by('-created_time')[:100]
    
    context = {
        'project_documents': project_documents,
        'administrative_archives': administrative_archives,
        'full_top_nav': _build_full_top_nav(permission_set, request.user),
        'archive_sidebar_nav': _build_archive_sidebar_nav(permission_set, request.path),
    }
    return render(request, "archive_management/archive_digitization_apply_create.html", context)


@login_required
def archive_digitization_process_list(request):
    """档案数字化处理列表"""
    permission_set = get_user_permission_codes(request.user)
    if not _permission_granted('archive_management.view', permission_set):
        from django.http import HttpResponseForbidden
        return HttpResponseForbidden("无权限访问")
    
    try:
        from backend.apps.customer_management.models import ArchiveDigitizationProcess
        model_available = True
    except ImportError:
        model_available = False
    
    if not model_available:
        from django.http import HttpResponse
        return HttpResponse("档案数字化功能暂未实现，ArchiveDigitizationProcess 模型尚未定义", status=503)
    
    queryset = ArchiveDigitizationProcess.objects.all().select_related(
        'apply', 'processor', 'quality_checker'
    )
    
    # 筛选
    status = request.GET.get('status', '')
    if status:
        queryset = queryset.filter(status=status)
    
    # 只显示当前用户的处理任务（除非有查看所有权限）
    if not _permission_granted('archive_management.view_all', permission_set):
        queryset = queryset.filter(processor=request.user)
    
    search = request.GET.get('search', '')
    if search:
        queryset = queryset.filter(
            Q(process_number__icontains=search) |
            Q(apply__apply_number__icontains=search) |
            Q(process_description__icontains=search)
        )
    
    # 分页
    page_size = request.GET.get('page_size', '10')
    try:
        per_page = int(page_size)
        if per_page not in [10, 20, 50]:
            per_page = 10
    except (ValueError, TypeError):
        per_page = 10
    paginator = Paginator(queryset, per_page)
    page_num = request.GET.get('page', 1)
    page = paginator.get_page(page_num)
    
    # 统计数据
    base_queryset = ArchiveDigitizationProcess.objects.all()
    if not _permission_granted('archive_management.view_all', permission_set):
        base_queryset = base_queryset.filter(processor=request.user)
    
    total_count = base_queryset.count()
    pending_count = base_queryset.filter(status='pending').count()
    processing_count = base_queryset.filter(status='processing').count()
    quality_check_count = base_queryset.filter(status='quality_check').count()
    completed_count = base_queryset.filter(status='completed').count()
    
    context = {
        'page': page,
        'status': status,
        'search': search,
        'total_count': total_count,
        'pending_count': pending_count,
        'processing_count': processing_count,
        'quality_check_count': quality_check_count,
        'completed_count': completed_count,
        'full_top_nav': _build_full_top_nav(permission_set, request.user),
        'archive_sidebar_nav': _build_archive_sidebar_nav(permission_set, request.path),
    }
    return render(request, "archive_management/archive_digitization_process_list.html", context)


@login_required
def archive_digitization_result_list(request):
    """档案数字化成果列表"""
    permission_set = get_user_permission_codes(request.user)
    if not _permission_granted('archive_management.view', permission_set):
        from django.http import HttpResponseForbidden
        return HttpResponseForbidden("无权限访问")
    
    try:
        from backend.apps.customer_management.models import ArchiveDigitizationResult
        model_available = True
    except ImportError:
        model_available = False
    
    if not model_available:
        from django.http import HttpResponse
        return HttpResponse("档案数字化功能暂未实现，ArchiveDigitizationResult 模型尚未定义", status=503)
    
    queryset = ArchiveDigitizationResult.objects.all().select_related(
        'process', 'process__apply', 'created_by', 'project_document', 'administrative_archive'
    )
    
    # 筛选
    result_type = request.GET.get('result_type', '')
    if result_type:
        queryset = queryset.filter(result_type=result_type)
    
    search = request.GET.get('search', '')
    if search:
        queryset = queryset.filter(
            Q(result_number__icontains=search) |
            Q(result_name__icontains=search) |
            Q(result_description__icontains=search) |
            Q(process__apply__apply_number__icontains=search)
        )
    
    # 分页
    page_size = request.GET.get('page_size', '10')
    try:
        per_page = int(page_size)
        if per_page not in [10, 20, 50]:
            per_page = 10
    except (ValueError, TypeError):
        per_page = 10
    paginator = Paginator(queryset, per_page)
    page_num = request.GET.get('page', 1)
    page = paginator.get_page(page_num)
    
    # 统计数据
    base_queryset = ArchiveDigitizationResult.objects.all()
    total_count = base_queryset.count()
    
    # 按类型统计
    type_stats = base_queryset.values('result_type').annotate(
        count=Count('id')
    ).order_by('-count')
    
    context = {
        'page': page,
        'result_type': result_type,
        'search': search,
        'total_count': total_count,
        'type_stats': list(type_stats),
        'full_top_nav': _build_full_top_nav(permission_set, request.user),
        'archive_sidebar_nav': _build_archive_sidebar_nav(permission_set, request.path),
    }
    return render(request, "archive_management/archive_digitization_result_list.html", context)


# 档案统计（完善功能）
@login_required
def archive_statistics_usage(request):
    """档案利用统计"""
    permission_set = get_user_permission_codes(request.user)
    if not _permission_granted('archive_management.view', permission_set):
        from django.http import HttpResponseForbidden
        return HttpResponseForbidden("无权限访问")
    
    from django.utils import timezone
    from datetime import timedelta
    from django.db.models import Count, Q
    
    # 时间范围筛选
    date_range = request.GET.get('date_range', '30')  # 7, 30, 90, 365, all
    days = int(date_range) if date_range != 'all' else None
    
    if days:
        start_date = timezone.now() - timedelta(days=days)
    else:
        start_date = None
    
    # 借阅统计
    borrow_queryset = ArchiveBorrow.objects.all()
    if start_date:
        borrow_queryset = borrow_queryset.filter(created_time__gte=start_date)
    
    borrow_total = borrow_queryset.count()
    borrow_by_status = borrow_queryset.values('status').annotate(count=Count('id')).order_by('-count')
    borrow_by_type = borrow_queryset.values('borrow_type').annotate(count=Count('id')).order_by('-count')
    
    # 最近30天的借阅趋势
    borrow_trend = []
    if days and days <= 90:
        for i in range(days, 0, -1):
            date = timezone.now() - timedelta(days=i)
            count = ArchiveBorrow.objects.filter(
                created_time__date=date.date()
            ).count()
            borrow_trend.append({
                'date': date.strftime('%m-%d'),
                'count': count
            })
    
    # 下载统计（从操作日志获取）
    try:
        from backend.apps.customer_management.models import ArchiveOperationLog
        download_queryset = ArchiveOperationLog.objects.filter(operation_type='download')
        if start_date:
            download_queryset = download_queryset.filter(operation_time__gte=start_date)
        download_total = download_queryset.count()
        download_by_result = download_queryset.values('operation_result').annotate(count=Count('id')).order_by('-count')
    except ImportError:
        download_total = 0
        download_by_result = []
    
    # 检索统计（从检索历史获取）
    try:
        from backend.apps.customer_management.models import ArchiveSearchHistory
        search_queryset = ArchiveSearchHistory.objects.all()
        if start_date:
            search_queryset = search_queryset.filter(search_time__gte=start_date)
        search_total = search_queryset.count()
        search_by_type = search_queryset.values('search_type').annotate(count=Count('id')).order_by('-count')
        
        # 热门检索关键词
        popular_keywords = search_queryset.filter(
            search_keyword__isnull=False
        ).exclude(
            search_keyword=''
        ).values('search_keyword').annotate(
            count=Count('id')
        ).order_by('-count')[:10]
    except ImportError:
        search_total = 0
        search_by_type = []
        popular_keywords = []
    
    # 利用效率统计
    total_archives = ProjectArchiveDocument.objects.filter(status='archived').count() + \
                    AdministrativeArchive.objects.filter(status='archived').count()
    utilization_rate = 0
    if total_archives > 0:
        utilization_count = borrow_total + download_total + search_total
        utilization_rate = round((utilization_count / total_archives) * 100, 2)
    
    context = {
        'date_range': date_range,
        'borrow_total': borrow_total,
        'borrow_by_status': list(borrow_by_status),
        'borrow_by_type': list(borrow_by_type),
        'borrow_trend': borrow_trend,
        'download_total': download_total,
        'download_by_result': list(download_by_result),
        'search_total': search_total,
        'search_by_type': list(search_by_type),
        'popular_keywords': list(popular_keywords),
        'total_archives': total_archives,
        'utilization_rate': utilization_rate,
        'full_top_nav': _build_full_top_nav(permission_set, request.user),
        'archive_sidebar_nav': _build_archive_sidebar_nav(permission_set, request.path),
    }
    return render(request, "archive_management/archive_statistics_usage.html", context)


@login_required
def archive_statistics_storage(request):
    """档案保管统计"""
    permission_set = get_user_permission_codes(request.user)
    if not _permission_granted('archive_management.view', permission_set):
        from django.http import HttpResponseForbidden
        return HttpResponseForbidden("无权限访问")
    
    from django.db.models import Count, Sum, Q
    from django.utils import timezone
    from datetime import timedelta
    
    # 档案数量统计
    project_doc_total = ProjectArchiveDocument.objects.filter(status='archived').count()
    admin_archive_total = AdministrativeArchive.objects.filter(status='archived').count()
    total_archives = project_doc_total + admin_archive_total
    
    # 档案分类统计
    category_stats = ArchiveCategory.objects.annotate(
        project_count=Count('projectarchivedocument', filter=Q(projectarchivedocument__status='archived')),
        admin_count=Count('administrativearchive', filter=Q(administrativearchive__status='archived'))
    ).filter(
        Q(project_count__gt=0) | Q(admin_count__gt=0)
    )
    
    # 档案状态统计
    project_doc_by_status = ProjectArchiveDocument.objects.values('status').annotate(count=Count('id')).order_by('-count')
    admin_archive_by_status = AdministrativeArchive.objects.values('status').annotate(count=Count('id')).order_by('-count')
    
    # 档案密级统计
    admin_archive_by_security = AdministrativeArchive.objects.values('security_level').annotate(count=Count('id')).order_by('-count')
    
    # 库房使用统计
    try:
        from backend.apps.customer_management.models import ArchiveStorageRoom, ArchiveLocation
        storage_rooms = ArchiveStorageRoom.objects.all().annotate(
            archive_count=Count('locations__shelves__archives', distinct=True)
        )
        total_capacity = sum(room.capacity or 0 for room in storage_rooms)
        total_used = sum(room.archive_count for room in storage_rooms)
        storage_usage_rate = round((total_used / total_capacity * 100) if total_capacity > 0 else 0, 2)
    except ImportError:
        storage_rooms = []
        total_capacity = 0
        total_used = 0
        storage_usage_rate = 0
    
    # 保管期限统计
    try:
        from backend.apps.customer_management.models import ArchiveCategory
        categories_with_period = ArchiveCategory.objects.filter(
            storage_period__isnull=False
        ).values('storage_period').annotate(
            count=Count('id')
        ).order_by('storage_period')
        
        # 到期档案统计（需要根据创建时间和保管期限计算）
        expired_count = 0
        expiring_soon_count = 0
        for category in ArchiveCategory.objects.filter(storage_period__isnull=False):
            if category.category_type == 'project':
                archives = ProjectArchiveDocument.objects.filter(category=category, status='archived')
            else:
                archives = AdministrativeArchive.objects.filter(category=category, status='archived')
            
            for archive in archives:
                created_date = archive.created_time.date()
                expiry_date = created_date + timedelta(days=category.storage_period * 365)
                days_until_expiry = (expiry_date - timezone.now().date()).days
                
                if days_until_expiry < 0:
                    expired_count += 1
                elif days_until_expiry <= 90:
                    expiring_soon_count += 1
    except:
        categories_with_period = []
        expired_count = 0
        expiring_soon_count = 0
    
    # 盘点统计
    try:
        from backend.apps.customer_management.models import ArchiveInventory
        inventory_total = ArchiveInventory.objects.count()
        inventory_recent = ArchiveInventory.objects.filter(
            inventory_time__gte=timezone.now() - timedelta(days=30)
        ).count()
    except ImportError:
        inventory_total = 0
        inventory_recent = 0
    
    context = {
        'total_archives': total_archives,
        'project_doc_total': project_doc_total,
        'admin_archive_total': admin_archive_total,
        'category_stats': category_stats,
        'project_doc_by_status': list(project_doc_by_status),
        'admin_archive_by_status': list(admin_archive_by_status),
        'admin_archive_by_security': list(admin_archive_by_security),
        'storage_rooms': storage_rooms,
        'total_capacity': total_capacity,
        'total_used': total_used,
        'storage_usage_rate': storage_usage_rate,
        'categories_with_period': list(categories_with_period),
        'expired_count': expired_count,
        'expiring_soon_count': expiring_soon_count,
        'inventory_total': inventory_total,
        'inventory_recent': inventory_recent,
        'full_top_nav': _build_full_top_nav(permission_set, request.user),
        'archive_sidebar_nav': _build_archive_sidebar_nav(permission_set, request.path),
    }
    return render(request, "archive_management/archive_statistics_storage.html", context)

