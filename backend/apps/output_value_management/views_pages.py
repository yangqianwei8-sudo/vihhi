# 产值管理视图
# 产值管理独立模块，与结算模块分离；入口 /output-value/

from django.contrib.auth.decorators import login_required
from django.shortcuts import render, get_object_or_404, redirect
from django.contrib import messages
from django.core.exceptions import PermissionDenied
from django.db.models import Q, Sum, Count, F, Avg
from django.utils import timezone
from decimal import Decimal
from datetime import timedelta, datetime

from .models import (
    OutputValueStage, OutputValueMilestone, OutputValueEvent, OutputValueRecord
)
from .services import get_project_output_value_summary, get_project_output_value_for_settlement
from backend.apps.production_management.models import Project
from backend.apps.system_management.models import User
from backend.apps.system_management.services import get_user_permission_codes
from backend.core.views import _permission_granted, _build_full_top_nav
from django.urls import reverse, NoReverseMatch
from django.core.paginator import Paginator
from django.db.models import Max
import logging

logger = logging.getLogger(__name__)


# ==================== 产值管理模块左侧菜单结构 =====================
OUTPUT_VALUE_MENU_STRUCTURE = [
    {
        'id': 'output_value_management_home',
        'label': '产值管理首页',
        'icon': '🏠',
        'url_name': 'output_value_pages:output_value_management_home',
        'permission': ['output_value_management.view'],
    },
    {
        'id': 'output_value_template',
        'label': '产值模板',
        'icon': '📋',
        'url_name': 'output_value_pages:output_value_template_manage',
        'permission': ['output_value_management.manage_template'],
    },
    {
        'id': 'output_value_record',
        'label': '产值记录',
        'icon': '📝',
        'url_name': 'output_value_pages:output_value_record_list',
        'permission': ['output_value_management.view_record'],
    },
    {
        'id': 'output_value_statistics',
        'label': '产值统计',
        'icon': '📈',
        'url_name': 'output_value_pages:output_value_statistics',
        'permission': ['output_value_management.view_statistics'],
    },
]


def _build_output_value_sidebar_nav(permission_set, request_path=None, active_id=None):
    """生成产值管理模块左侧菜单"""
    try:
        from backend.core.views import _build_unified_sidebar_nav
        return _build_unified_sidebar_nav(OUTPUT_VALUE_MENU_STRUCTURE, permission_set, active_id=active_id)
    except ImportError:
        # Fallback实现：如果 _build_unified_sidebar_nav 不存在，提供简单实现
        nav = []
        for item in OUTPUT_VALUE_MENU_STRUCTURE:
            if item.get('permission') and not _permission_granted(item['permission'], permission_set):
                continue
            
            # 处理 URL：优先使用 url_name 转换为真实 URL
            url = '#'
            url_name = item.get('url_name')
            if url_name:
                try:
                    url = reverse(url_name)
                except NoReverseMatch:
                    url = item.get('url', '#')
            else:
                url = item.get('url', '#')
            
            nav_item = {
                'label': item.get('label', ''),
                'icon': item.get('icon', ''),
                'url': url,
                'active': item.get('id') == active_id if active_id else False,
            }
            
            # 处理子菜单
            if 'children' in item:
                children = []
                for child in item['children']:
                    # 检查子菜单权限
                    if child.get('permission'):
                        if not _permission_granted(child['permission'], permission_set):
                            continue
                    
                    # 处理子菜单 URL
                    child_url = '#'
                    child_url_name = child.get('url_name')
                    if child_url_name:
                        try:
                            child_url = reverse(child_url_name)
                        except NoReverseMatch:
                            child_url = child.get('url', '#')
                    else:
                        child_url = child.get('url', '#')
                    
                    children.append({
                        'label': child.get('label', ''),
                        'icon': child.get('icon', ''),
                        'url': child_url,
                        'active': child.get('id') == active_id if active_id else False,
                    })
                
                nav_item['children'] = children
            
            nav.append(nav_item)
        
        return nav


def _context(page_title, page_icon, description, summary_cards=None, sections=None, request=None, active_menu_id=None):
    """构建页面上下文"""
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
        
        # 设置产值管理侧边栏
        context['sidebar_nav'] = _build_output_value_sidebar_nav(permission_set, request.path, active_id=active_menu_id)
        context['module_sidebar_nav'] = context['sidebar_nav']
        context['sidebar_title'] = '产值管理'
        context['sidebar_subtitle'] = 'Output Value Management'
    else:
        context['full_top_nav'] = []
        context['sidebar_nav'] = []
        context['module_sidebar_nav'] = []
        context['sidebar_title'] = '产值管理'
        context['sidebar_subtitle'] = 'Output Value Management'
    
    return context


@login_required
def output_value_management_home(request):
    """产值管理首页 - 数据展示中心"""
    permission_set = get_user_permission_codes(request.user)
    has_permission = _permission_granted('output_value_management.view', permission_set)
    if not has_permission:
        from django.http import HttpResponseForbidden
        return HttpResponseForbidden("无权限访问产值管理")

    now = timezone.now()
    today = now.date()
    this_month_start = today.replace(day=1)
    seven_days_ago = today - timedelta(days=7)

    all_records = OutputValueRecord.objects.all()

    context = {}

    try:
        # ========== 核心指标卡片 ==========
        core_cards = []

        # 产值统计
        total_records = all_records.count()
        pending_records = all_records.filter(status='pending').count()
        calculated_records = all_records.filter(status='calculated').count()
        confirmed_records = all_records.filter(status='confirmed').count()
        this_month_records = all_records.filter(created_time__gte=this_month_start).count()
        this_month_confirmed_records = all_records.filter(
            status='confirmed',
            confirmed_time__gte=this_month_start
        ).count()

        # 计算总产值
        total_output_value = all_records.aggregate(total=Sum('calculated_value'))['total'] or Decimal('0')
        confirmed_output_value = all_records.filter(status='confirmed').aggregate(
            total=Sum('calculated_value')
        )['total'] or Decimal('0')

        # 卡片1：产值记录总数
        core_cards.append({
            'label': '产值记录总数',
            'icon': '📊',
            'value': str(total_records),
            'subvalue': f'待计算 {pending_records} | 已计算 {calculated_records} | 已确认 {confirmed_records}',
            'url': reverse('output_value_pages:output_value_record_list'),
            'variant': 'secondary'
        })

        # 卡片2：累计产值
        core_cards.append({
            'label': '累计产值',
            'icon': '💰',
            'value': f'{total_output_value:,.2f}',
            'subvalue': f'已确认产值 {confirmed_output_value:,.2f}',
            'url': reverse('output_value_pages:output_value_statistics'),
            'variant': 'secondary'
        })

        # 卡片3：已确认产值
        core_cards.append({
            'label': '已确认产值',
            'icon': '✅',
            'value': f'{confirmed_output_value:,.2f}',
            'subvalue': f'本月确认 {this_month_confirmed_records} 条',
            'url': reverse('output_value_pages:output_value_record_list') + '?status=confirmed',
            'variant': 'secondary'
        })

        # 卡片4：待确认产值
        core_cards.append({
            'label': '待确认产值',
            'icon': '⏳',
            'value': str(calculated_records),
            'subvalue': f'等待确认',
            'url': reverse('output_value_pages:output_value_record_list') + '?status=calculated',
            'variant': 'dark' if calculated_records > 0 else 'secondary'
        })

        # 卡片5：本月新增
        core_cards.append({
            'label': '本月新增',
            'icon': '📈',
            'value': str(this_month_records),
            'subvalue': f'新记录 {this_month_records} 条',
            'url': reverse('output_value_pages:output_value_record_list'),
            'variant': 'secondary'
        })

        context['core_cards'] = core_cards

        # ========== 待办事项 ==========
        todo_items = []

        # 待确认产值记录
        pending_confirm_list = all_records.filter(status='calculated').select_related('responsible_user', 'project')[:5]
        for record in pending_confirm_list:
            responsible_name = record.responsible_user.get_full_name() or record.responsible_user.username if record.responsible_user else '未分配'
            todo_items.append({
                'type': 'confirm',
                'title': f"{record.project.project_number} - {record.event.name}",
                'value': f'{record.calculated_value:,.2f}',
                'responsible': responsible_name,
                'url': reverse('output_value_pages:output_value_record_confirm', args=[record.id])
            })

        context['todo_items'] = todo_items[:10]
        context['pending_confirm_count'] = calculated_records
        context['todo_summary_url'] = reverse('output_value_pages:output_value_record_list') + '?status=calculated'

        # ========== 我的工作 ==========
        my_work = {}

        # 我负责的产值记录
        my_records = all_records.filter(responsible_user=request.user).order_by('-calculated_time')[:3]
        my_work['my_records'] = [{
            'title': f"{record.project.project_number} - {record.event.name}",
            'value': f'{record.calculated_value:,.2f}',
            'status': record.get_status_display(),
            'url': reverse('output_value_pages:project_output_value_detail', args=[record.project.id])
        } for record in my_records]
        my_work['my_records_count'] = all_records.filter(responsible_user=request.user).count()
        my_work['my_total_value'] = all_records.filter(responsible_user=request.user).aggregate(
            total=Sum('calculated_value')
        )['total'] or Decimal('0')

        my_work['summary_url'] = reverse('output_value_pages:output_value_record_list') + f'?responsible_user={request.user.id}'

        context['my_work'] = my_work

        # ========== 最近活动 ==========
        recent_activities = {}

        # 最近创建的产值记录
        recent_records = all_records.select_related('responsible_user', 'project').order_by('-created_time')[:5]
        recent_activities['recent_records'] = [{
            'title': f"{record.project.project_number} - {record.event.name}",
            'creator': record.responsible_user.get_full_name() or record.responsible_user.username if record.responsible_user else '系统',
            'value': f'{record.calculated_value:,.2f}',
            'time': record.created_time,
            'url': reverse('output_value_pages:project_output_value_detail', args=[record.project.id])
        } for record in recent_records]

        # 最近确认的产值记录
        recent_confirmed = all_records.filter(status='confirmed').select_related('confirmed_by', 'project').order_by('-confirmed_time')[:5]
        recent_activities['recent_confirmed'] = [{
            'title': f"{record.project.project_number} - {record.event.name}",
            'confirmer': record.confirmed_by.get_full_name() or record.confirmed_by.username if record.confirmed_by else '系统',
            'value': f'{record.calculated_value:,.2f}',
            'time': record.confirmed_time,
            'url': reverse('output_value_pages:project_output_value_detail', args=[record.project.id])
        } for record in recent_confirmed]

        context['recent_activities'] = recent_activities

    except Exception as e:
        logger.exception('获取产值管理统计数据失败: %s', str(e))
        context.setdefault('core_cards', [])
        context.setdefault('todo_items', [])
        context.setdefault('my_work', {})
        context.setdefault('recent_activities', {})

    # 顶部操作栏
    top_actions = []
    # 兼容新旧权限
    if _permission_granted('output_value_management.manage_template', permission_set) or \
       _permission_granted('output_value_management.manage_template', permission_set):
        try:
            top_actions.append({
                'label': '产值模板管理',
                'url': reverse('output_value_pages:output_value_template_manage'),
                'icon': '📋'
            })
        except Exception:
            pass

    context['top_actions'] = top_actions

    # 构建上下文
    page_context = _context(
        "产值管理",
        "📊",
        "数据展示中心 - 集中展示产值关键指标、状态与统计",
        request=request,
    )

    # 设置侧边栏导航
    output_value_sidebar_nav = _build_output_value_sidebar_nav(permission_set, request.path, active_id='output_value_management_home')
    page_context['sidebar_nav'] = output_value_sidebar_nav
    page_context['module_sidebar_nav'] = output_value_sidebar_nav

    # 合并所有数据
    page_context.update(context)

    return render(request, "output_value_management/output_value_management_home.html", page_context)


# ==================== 产值管理视图函数 ====================

@login_required
def output_value_template_manage(request):
    """产值模板管理页面"""
    # 检查权限
    from backend.apps.system_management.services import user_has_permission
    # 兼容新旧权限
    has_permission = (user_has_permission(request.user, 'output_value_management.manage_template') or
                      user_has_permission(request.user, 'output_value_management.manage_template') or
                      user_has_permission(request.user, 'system_management.manage_settings'))
    if not has_permission:
        raise PermissionDenied("您没有权限访问产值模板管理。")
    
    # 获取所有阶段及其里程碑和事件
    try:
        stages = OutputValueStage.objects.filter(is_active=True).prefetch_related(
            'milestones__events'
        ).order_by('order')
    except Exception as e:
        logger.exception('获取产值阶段失败: %s', str(e))
        messages.error(request, f'获取产值阶段失败：{str(e)}')
        return render(request, "output_value_management/output_value_template.html", _context(
            "产值模板管理",
            "📊",
            "获取产值阶段失败，请检查数据库表是否正确创建。",
            summary_cards=[],
            sections=[],
            request=request,
        ))
    
    # 统计信息
    total_stages = stages.count()
    total_milestones = OutputValueMilestone.objects.filter(is_active=True).count()
    total_events = OutputValueEvent.objects.filter(is_active=True).count()
    
    summary_cards = []
    
    # 构建阶段数据
    stage_data = []
    for stage in stages:
        milestone_list = []
        for milestone in stage.milestones.filter(is_active=True).order_by('order'):
            event_list = []
            for event in milestone.events.filter(is_active=True).order_by('order'):
                event_list.append({
                    "id": event.id,
                    "name": event.name,
                    "code": event.code,
                    "percentage": float(event.event_percentage),
                    "role": event.responsible_role_code,
                    "trigger_condition": event.trigger_condition,
                })
            milestone_list.append({
                "id": milestone.id,
                "name": milestone.name,
                "code": milestone.code,
                "percentage": float(milestone.milestone_percentage),
                "events": event_list,
            })
        stage_data.append({
            "id": stage.id,
            "name": stage.name,
            "code": stage.code,
            "stage_type": stage.get_stage_type_display(),
            "percentage": float(stage.stage_percentage),
            "base_amount_type": stage.get_base_amount_type_display(),
            "milestones": milestone_list,
        })
    
    sections = [
        {
            "title": "产值模板配置",
            "description": "查看和管理产值计算模板的配置。",
            "items": [
                {
                    "label": "阶段列表",
                    "description": "查看所有产值阶段的配置",
                    "url": "#stages",
                    "icon": "📊",
                    "data": stage_data,
                },
            ],
        }
    ]
    
    permission_set = get_user_permission_codes(request.user)
    context = _context(
        "产值模板管理",
        "📊",
        "配置和管理产值计算模板，包括阶段、里程碑和事件的设置。",
        summary_cards=summary_cards,
        sections=sections,
        request=request,
    )
    context['stages'] = stage_data
    
    # 设置侧边栏导航
    output_value_sidebar_nav = _build_output_value_sidebar_nav(permission_set, request.path, active_id='output_value_template')
    context['sidebar_nav'] = output_value_sidebar_nav
    context['module_sidebar_nav'] = output_value_sidebar_nav
    
    return render(request, "output_value_management/output_value_template.html", context)


@login_required
def output_value_record_list(request):
    """产值计算记录列表"""
    # 检查权限
    from backend.apps.system_management.services import user_has_permission
    # 兼容新旧权限
    has_view_permission = (user_has_permission(request.user, 'output_value_management.view_record') or
                           user_has_permission(request.user, 'output_value_management.view') or
                           user_has_permission(request.user, 'output_value_management.view_statistics') or
                           user_has_permission(request.user, 'output_value_management.manage_template'))
    if not has_view_permission:
        raise PermissionDenied("您没有权限查看产值记录。")
    
    # 获取当前用户的产值记录
    try:
        records = OutputValueRecord.objects.select_related(
            'project', 'stage', 'milestone', 'event', 'responsible_user'
        ).order_by('-calculated_time')
    except Exception as e:
        logger.exception('获取产值记录失败: %s', str(e))
        messages.error(request, f'获取产值记录失败：{str(e)}')
        return render(request, "output_value_management/output_value_record_list.html", _context(
            "产值记录查询",
            "📈",
            "获取产值记录失败，请检查数据库表是否正确创建。",
            summary_cards=[],
            request=request,
        ))
    
    # 如果是普通用户，只显示自己的记录
    # 兼容新旧权限
    has_manage_permission = (user_has_permission(request.user, 'output_value_management.manage_template') or
                             user_has_permission(request.user, 'output_value_management.manage_template'))
    if not has_manage_permission:
        records = records.filter(responsible_user=request.user)
    
    # 筛选条件
    project_id = request.GET.get('project_id')
    if project_id:
        records = records.filter(project_id=project_id)
    
    status = request.GET.get('status')
    if status:
        records = records.filter(status=status)
    
    # 分页
    paginator = Paginator(records, 20)
    page_number = request.GET.get('page', 1)
    page_obj = paginator.get_page(page_number)
    
    # 统计信息
    total_value = records.filter(status__in=['calculated', 'confirmed']).aggregate(
        total=Sum('calculated_value')
    )['total'] or Decimal('0')
    
    confirmed_value = records.filter(status='confirmed').aggregate(
        total=Sum('calculated_value')
    )['total'] or Decimal('0')
    
    summary_cards = []
    
    permission_set = get_user_permission_codes(request.user)
    context = _context(
        "产值记录查询",
        "📈",
        "查看和管理产值计算记录，了解产值分配情况。",
        summary_cards=summary_cards,
        request=request,
    )
    context['records'] = page_obj
    context['projects'] = Project.objects.filter(status__in=['in_progress', 'completed']).order_by('-created_time')
    
    # 设置侧边栏导航
    output_value_sidebar_nav = _build_output_value_sidebar_nav(permission_set, request.path, active_id='output_value_record')
    context['sidebar_nav'] = output_value_sidebar_nav
    context['module_sidebar_nav'] = output_value_sidebar_nav
    
    return render(request, "output_value_management/output_value_record_list.html", context)


@login_required
def project_output_value_detail(request, project_id):
    """项目产值详情页（在产值管理模块中查看项目的产值统计）"""
    project = get_object_or_404(Project, id=project_id)
    permission_codes = get_user_permission_codes(request.user)
    
    # 检查权限
    from backend.apps.system_management.services import user_has_permission
    # 兼容新旧权限
    has_view_permission = (user_has_permission(request.user, 'output_value_management.view_record') or
                           user_has_permission(request.user, 'output_value_management.view') or
                           user_has_permission(request.user, 'output_value_management.view_statistics') or
                           user_has_permission(request.user, 'output_value_management.manage_template'))
    if not has_view_permission:
        # 检查是否是项目成员
        if not (project.project_manager == request.user or 
                project.business_manager == request.user or
                project.team_members.filter(user=request.user, is_active=True).exists()):
            messages.error(request, '您没有权限查看此项目的产值信息')
            return redirect('output_value_pages:output_value_record_list')
    
    # 获取项目产值统计
    try:
        output_value_summary = get_project_output_value_summary(project)
    except Exception as e:
        logger.exception('获取项目产值统计失败: %s', str(e))
        messages.error(request, f'获取项目产值统计失败：{str(e)}')
        return redirect('output_value_pages:output_value_record_list')
    
    # 检查权限
    # 兼容新旧权限
    has_manage_permission = (user_has_permission(request.user, 'output_value_management.manage_template') or
                             user_has_permission(request.user, 'output_value_management.manage_template'))
    
    # 产值记录分页
    paginator = Paginator(output_value_summary['records'], 20)
    page_number = request.GET.get('page', 1)
    page_obj = paginator.get_page(page_number)
    
    permission_set = get_user_permission_codes(request.user)
    context = _context(
        f"项目产值详情 - {project.project_number}",
        "📊",
        f"项目：{project.name}",
        request=request,
    )
    context.update({
        'project': project,
        'output_value_summary': output_value_summary,
        'records': page_obj,
        'has_manage_permission': has_manage_permission,
    })
    
    # 设置侧边栏导航
    output_value_sidebar_nav = _build_output_value_sidebar_nav(permission_set, request.path)
    context['sidebar_nav'] = output_value_sidebar_nav
    context['module_sidebar_nav'] = output_value_sidebar_nav
    
    return render(request, "output_value_management/project_output_value_detail.html", context)


@login_required
def output_value_record_confirm(request, record_id):
    """确认产值记录"""
    record = get_object_or_404(OutputValueRecord, id=record_id)
    
    # 检查权限：只有责任人或有管理权限的用户可以确认
    from backend.apps.system_management.services import user_has_permission
    # 兼容新旧权限
    has_manage_permission = (user_has_permission(request.user, 'output_value_management.manage_template') or
                             user_has_permission(request.user, 'output_value_management.manage_template'))
    if record.responsible_user != request.user and not has_manage_permission:
        raise PermissionDenied("您没有权限确认此产值记录。")
    
    if request.method == 'POST':
        record.status = 'confirmed'
        record.confirmed_time = timezone.now()
        record.confirmed_by = request.user
        record.save(update_fields=['status', 'confirmed_time', 'confirmed_by', 'updated_time'])
        messages.success(request, '产值记录已确认。')
        return redirect('output_value_pages:output_value_record_list')
    
    permission_set = get_user_permission_codes(request.user)
    context = _context(
        '确认产值记录',
        '✅',
        f'确认产值记录：{record.project.project_number} - {record.event.name}',
        request=request,
    )
    context['record'] = record
    
    # 设置侧边栏导航
    output_value_sidebar_nav = _build_output_value_sidebar_nav(permission_set, request.path)
    context['sidebar_nav'] = output_value_sidebar_nav
    context['module_sidebar_nav'] = output_value_sidebar_nav
    
    return render(request, "output_value_management/output_value_record_confirm.html", context)


@login_required
def output_value_statistics(request):
    """产值统计报表"""
    # 检查权限
    from backend.apps.system_management.services import user_has_permission
    # 兼容新旧权限
    has_view_permission = (user_has_permission(request.user, 'output_value_management.view_record') or
                           user_has_permission(request.user, 'output_value_management.view') or
                           user_has_permission(request.user, 'output_value_management.view_statistics') or
                           user_has_permission(request.user, 'output_value_management.manage_template'))
    if not has_view_permission:
        raise PermissionDenied("您没有权限查看产值统计。")
    
    # 获取筛选参数
    date_from = request.GET.get('date_from')
    date_to = request.GET.get('date_to')
    user_id = request.GET.get('user_id')
    project_id = request.GET.get('project_id')
    stage_id = request.GET.get('stage_id')
    
    # 构建查询
    try:
        records = OutputValueRecord.objects.select_related(
            'project', 'stage', 'milestone', 'event', 'responsible_user'
        ).filter(status__in=['calculated', 'confirmed'])
    except Exception as e:
        logger.exception('获取产值记录失败: %s', str(e))
        messages.error(request, f'获取产值记录失败：{str(e)}')
        return render(request, "output_value_management/output_value_statistics.html", _context(
            "产值统计报表",
            "📊",
            "获取产值记录失败，请检查数据库表是否正确创建。",
            summary_cards=[],
            request=request,
        ))
    
    if date_from:
        records = records.filter(calculated_time__gte=date_from)
    if date_to:
        records = records.filter(calculated_time__lte=date_to)
    if user_id:
        records = records.filter(responsible_user_id=user_id)
    if project_id:
        records = records.filter(project_id=project_id)
    if stage_id:
        records = records.filter(stage_id=stage_id)
    
    # 如果是普通用户，只显示自己的记录
    # 兼容新旧权限
    has_manage_permission = (user_has_permission(request.user, 'output_value_management.manage_template') or
                             user_has_permission(request.user, 'output_value_management.manage_template'))
    if not has_manage_permission:
        records = records.filter(responsible_user=request.user)
    
    # 按用户统计
    user_stats = records.values(
        'responsible_user__username',
        'responsible_user__first_name',
        'responsible_user__last_name'
    ).annotate(
        total_value=Sum('calculated_value'),
        record_count=Count('id')
    ).order_by('-total_value')
    
    # 为每个用户统计添加平均值
    user_stats_list = []
    for stat in user_stats:
        avg_value = float(stat['total_value'] or 0) / stat['record_count'] if stat['record_count'] > 0 else 0
        stat_dict = dict(stat)
        stat_dict['avg_value'] = Decimal(str(avg_value))
        user_stats_list.append(stat_dict)
    user_stats = user_stats_list
    
    # 按阶段统计
    stage_stats = records.values('stage__name', 'stage__code').annotate(
        total_value=Sum('calculated_value'),
        record_count=Count('id')
    ).order_by('-total_value')
    
    # 按项目统计
    project_stats = records.values(
        'project__project_number',
        'project__name'
    ).annotate(
        total_value=Sum('calculated_value'),
        record_count=Count('id')
    ).order_by('-total_value')[:20]
    
    # 时间趋势统计（按月）
    from django.db.models.functions import TruncMonth
    monthly_stats = records.annotate(
        year_month=TruncMonth('calculated_time')
    ).values('year_month').annotate(
        total_value=Sum('calculated_value'),
        record_count=Count('id')
    ).order_by('year_month')
    
    # 总统计
    total_stats = records.aggregate(
        total_value=Sum('calculated_value'),
        confirmed_value=Sum('calculated_value', filter=Q(status='confirmed')),
        record_count=Count('id')
    )
    
    summary_cards = []
    
    permission_set = get_user_permission_codes(request.user)
    context = _context(
        "产值统计报表",
        "📊",
        "查看产值分配统计和分析报表。",
        summary_cards=summary_cards,
        request=request,
    )
    context.update({
        'user_stats': user_stats,
        'stage_stats': stage_stats,
        'project_stats': project_stats,
        'monthly_stats': monthly_stats,
        'total_stats': total_stats,
        'users': User.objects.filter(is_active=True).order_by('username') if has_manage_permission else [request.user],
        'projects': Project.objects.filter(status__in=['in_progress', 'completed']).order_by('-created_time'),
        'stages': OutputValueStage.objects.filter(is_active=True).order_by('order'),
    })
    
    # 设置侧边栏导航
    output_value_sidebar_nav = _build_output_value_sidebar_nav(permission_set, request.path, active_id='output_value_statistics')
    context['sidebar_nav'] = output_value_sidebar_nav
    context['module_sidebar_nav'] = output_value_sidebar_nav
    
    return render(request, "output_value_management/output_value_statistics.html", context)
