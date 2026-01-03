from django.contrib.auth.decorators import login_required
from django.shortcuts import render, get_object_or_404, redirect
from django.contrib import messages
from django.core.exceptions import PermissionDenied
from django.db.models import Q, Sum, Count, F
from django.utils import timezone
from django.urls import reverse
from decimal import Decimal

from backend.apps.settlement_center.models import (
    OutputValueStage, OutputValueMilestone, OutputValueEvent, OutputValueRecord,
    PaymentRecord, PaymentApplication
)
from backend.apps.settlement_management.models import (
    ProjectSettlement, SettlementItem, ServiceFeeRate, ContractSettlement
)
# from backend.apps.production_quality.models import Opinion  # 已删除生产质量模块
from .forms import ProjectSettlementForm, ContractSettlementForm
from .services import get_project_output_value_for_settlement, get_project_output_value_summary
from backend.apps.production_management.models import Project
from backend.apps.system_management.models import User
from backend.apps.system_management.services import get_user_permission_codes
from backend.core.views import _permission_granted, _build_full_top_nav, _build_unified_sidebar_nav
from backend.apps.production_management.models import BusinessContract
from django.core.paginator import Paginator
from django.db.models import Max


# 产值管理菜单结构定义（重新设计）
OUTPUT_VALUE_MENU_STRUCTURE = [
    {
        'id': 'output_value_home',
        'label': '产值概览',
        'icon': '📊',
        'url_name': 'settlement_pages:output_value_home',
        'permission': 'settlement_center.view_output_value',
    },
    {
        'id': 'output_value_records',
        'label': '产值记录',
        'icon': '📋',
        'url_name': 'settlement_pages:output_value_record_list',
        'permission': 'settlement_center.view_output_value',
    },
    {
        'id': 'output_value_stage_config',
        'label': '阶段配置',
        'icon': '🎯',
        'permission': 'settlement_center.manage_output',
        'children': [
            {
                'id': 'output_value_stage_list',
                'label': '阶段列表',
                'icon': '📋',
                'url_name': 'settlement_pages:output_value_stage_list',
                'permission': 'settlement_center.manage_output',
            },
            {
                'id': 'output_value_stage_create',
                'label': '新建阶段',
                'icon': '➕',
                'url_name': 'settlement_pages:output_value_stage_create',
                'permission': 'settlement_center.manage_output',
            },
        ]
    },
    {
        'id': 'output_value_milestone_config',
        'label': '里程碑配置',
        'icon': '🏁',
        'permission': 'settlement_center.manage_output',
        'children': [
            {
                'id': 'output_value_milestone_list',
                'label': '里程碑列表',
                'icon': '📋',
                'url_name': 'settlement_pages:output_value_milestone_list',
                'permission': 'settlement_center.manage_output',
            },
            {
                'id': 'output_value_milestone_create',
                'label': '新建里程碑',
                'icon': '➕',
                'url_name': 'settlement_pages:output_value_milestone_create',
                'permission': 'settlement_center.manage_output',
            },
        ]
    },
    {
        'id': 'output_value_event_config',
        'label': '事件配置',
        'icon': '⚡',
        'permission': 'settlement_center.manage_output',
        'children': [
            {
                'id': 'output_value_event_list',
                'label': '事件列表',
                'icon': '📋',
                'url_name': 'settlement_pages:output_value_event_list',
                'permission': 'settlement_center.manage_output',
            },
            {
                'id': 'output_value_event_create',
                'label': '新建事件',
                'icon': '➕',
                'url_name': 'settlement_pages:output_value_event_create',
                'permission': 'settlement_center.manage_output',
            },
        ]
    },
    {
        'id': 'output_value_calculation_config',
        'label': '产值计算配置',
        'icon': '⚖️',
        'permission': 'settlement_center.view_output_value',
        'children': [
            {
                'id': 'output_value_template_manage',
                'label': '计算方式列表',
                'icon': '📊',
                'url_name': 'settlement_pages:output_value_template_manage',
                'permission': 'settlement_center.view_output_value',
            },
            # 注意：新建计算方式暂时使用阶段权重配置页面，后续可以创建专门的页面
            {
                'id': 'output_value_calculation_create',
                'label': '新建计算方式',
                'icon': '➕',
                'url_name': 'settlement_pages:output_value_template_manage',
                'permission': 'settlement_center.manage_output',
            },
        ]
    },
    {
        'id': 'output_value_statistics',
        'label': '统计分析',
        'icon': '📈',
        'url_name': 'settlement_pages:output_value_statistics',
        'permission': 'settlement_center.view_output_value_statistics',
    },
]


def _build_output_value_sidebar_nav(permission_set, request_path=None, active_id=None):
    """生成产值管理左侧菜单（统一格式）"""
    # 使用统一的菜单构建函数
    return _build_unified_sidebar_nav(OUTPUT_VALUE_MENU_STRUCTURE, permission_set, active_id=active_id)


# 项目结算菜单结构定义
PROJECT_SETTLEMENT_MENU_STRUCTURE = [
    {
        'id': 'project_settlement_home',
        'label': '项目结算首页',
        'icon': '🏠',
        'url_name': 'settlement_pages:project_settlement_home',
        'permission': 'settlement_center.view_project_settlement',
    },
    {
        'id': 'project_settlement_list',
        'label': '结算单列表',
        'icon': '📄',
        'url_name': 'settlement_pages:project_settlement_list',
        'permission': 'settlement_center.view_project_settlement',
    },
    {
        'id': 'project_settlement_create',
        'label': '创建结算单',
        'icon': '➕',
        'url_name': 'settlement_pages:project_settlement_create',
        'permission': 'settlement_center.create_project_settlement',
    },
]


def _build_project_settlement_sidebar_nav(permission_set, request_path=None, active_id=None):
    """生成项目结算左侧菜单（统一格式）"""
    # 使用统一的菜单构建函数
    return _build_unified_sidebar_nav(PROJECT_SETTLEMENT_MENU_STRUCTURE, permission_set, active_id=active_id)


def _context(page_title, page_icon, description, summary_cards=None, sections=None, request=None, active_menu_id=None):
    """统一的页面上下文生成函数"""
    context = {
        "page_title": page_title,
        "page_icon": page_icon,
        "description": description,
        "summary_cards": summary_cards or [],
        "sections": sections or [],
    }
    
    # 添加顶部导航栏和侧边栏
    if request and request.user.is_authenticated:
        try:
            permission_set = get_user_permission_codes(request.user)
            context['full_top_nav'] = _build_full_top_nav(permission_set, request.user)
            
            # 根据路径判断应该使用哪个模块的导航栏
            request_path = request.path
            if '/output-value' in request_path or 'output_value' in request_path:
                # 产值管理模块
                context['module_sidebar_nav'] = _build_output_value_sidebar_nav(permission_set, request_path, active_id=active_menu_id)
            elif '/project-settlement' in request_path or 'project_settlement' in request_path:
                # 项目结算模块
                context['module_sidebar_nav'] = _build_project_settlement_sidebar_nav(permission_set, request_path, active_id=active_menu_id)
            elif '/payment' in request_path or 'payment' in request_path:
                # 回款管理模块
                context['module_sidebar_nav'] = _build_payment_sidebar_nav(permission_set, request_path, active_id=active_menu_id)
            else:
                # 默认使用产值管理导航栏
                context['module_sidebar_nav'] = _build_output_value_sidebar_nav(permission_set, request_path, active_id=active_menu_id)
        except Exception as e:
            import logging
            logger = logging.getLogger(__name__)
            logger.exception('构建导航栏失败: %s', str(e))
            context['full_top_nav'] = []
            context['module_sidebar_nav'] = []
    else:
        context['full_top_nav'] = []
        context['module_sidebar_nav'] = []
    
    return context


@login_required
def output_value_home(request):
    """产值管理首页（重新设计）"""
    permission_codes = get_user_permission_codes(request.user)
    from datetime import timedelta
    today = timezone.now().date()
    this_month_start = today.replace(day=1)
    last_month_start = (this_month_start - timedelta(days=1)).replace(day=1)
    
    # 权限检查
    if not _permission_granted('settlement_center.view_output_value', permission_codes):
        messages.error(request, '您没有权限访问产值管理')
        return redirect('core:home')
    
    has_manage_permission = _permission_granted('settlement_center.manage_output', permission_codes)
    
    # 收集统计数据
    summary_cards = []
    quick_actions = []
    recent_records = []
    pending_tasks = []
    
    try:
        # 产值记录统计
        all_records = OutputValueRecord.objects.select_related('project', 'stage', 'responsible_user')
        
        # 如果是普通用户，只显示自己的记录
        if not has_manage_permission:
            all_records = all_records.filter(responsible_user=request.user)
        
        total_records = all_records.count()
        total_value = all_records.filter(status__in=['calculated', 'confirmed']).aggregate(
            total=Sum('calculated_value')
        )['total'] or Decimal('0')
        
        confirmed_value = all_records.filter(status='confirmed').aggregate(
            total=Sum('calculated_value')
        )['total'] or Decimal('0')
        
        pending_count = all_records.filter(status='calculated').count()
        pending_value = all_records.filter(status='calculated').aggregate(
            total=Sum('calculated_value')
        )['total'] or Decimal('0')
        
        # 本月统计
        this_month_records = all_records.filter(calculated_time__gte=this_month_start)
        this_month_value = this_month_records.filter(status__in=['calculated', 'confirmed']).aggregate(
            total=Sum('calculated_value')
        )['total'] or Decimal('0')
        
        # 上月统计（用于对比）
        last_month_records = all_records.filter(
            calculated_time__gte=last_month_start,
            calculated_time__lt=this_month_start
        )
        last_month_value = last_month_records.filter(status__in=['calculated', 'confirmed']).aggregate(
            total=Sum('calculated_value')
        )['total'] or Decimal('0')
        
        # 计算增长率
        growth_rate = 0
        if last_month_value > 0:
            growth_rate = ((this_month_value - last_month_value) / last_month_value * 100)
        
        # 统计卡片
        summary_cards = [
            {
                'label': '总产值',
                'value': f'¥{total_value:,.0f}',
                'subvalue': f'已确认 ¥{confirmed_value:,.0f}',
                'icon': '💰',
                'color': 'primary',
                'url': reverse('settlement_pages:output_value_record_list'),
            },
            {
                'label': '待确认产值',
                'value': f'¥{pending_value:,.0f}',
                'subvalue': f'{pending_count} 条待确认',
                'icon': '⏳',
                'color': 'warning',
                'url': reverse('settlement_pages:output_value_record_list') + '?status=calculated',
            },
            {
                'label': '本月产值',
                'value': f'¥{this_month_value:,.0f}',
                'subvalue': f'{"↑" if growth_rate > 0 else "↓"} {abs(growth_rate):.1f}% 较上月',
                'icon': '📅',
                'color': 'success' if growth_rate > 0 else 'info',
                'url': reverse('settlement_pages:output_value_record_list'),
            },
            {
                'label': '产值记录',
                'value': str(total_records),
                'subvalue': f'本月新增 {this_month_records.count()} 条',
                'icon': '📋',
                'color': 'info',
                'url': reverse('settlement_pages:output_value_record_list'),
            },
        ]
        
        # 快速操作
        quick_actions = [
            {
                'label': '查看产值记录',
                'icon': '📋',
                'url': reverse('settlement_pages:output_value_record_list'),
                'color': 'primary',
            },
            {
                'label': '产值统计',
                'icon': '📈',
                'url': reverse('settlement_pages:output_value_statistics'),
                'color': 'success',
            },
        ]
        
        if has_manage_permission:
            quick_actions.extend([
                {
                    'label': '模板配置',
                    'icon': '⚙️',
                    'url': reverse('settlement_pages:output_value_template_manage'),
                    'color': 'info',
                },
                {
                    'label': '阶段管理',
                    'icon': '🎯',
                    'url': reverse('settlement_pages:output_value_stage_list'),
                    'color': 'secondary',
                },
            ])
        
        # 待办事项
        if pending_count > 0:
            pending_tasks.append({
                'label': f'待确认产值记录',
                'count': pending_count,
                'value': f'¥{pending_value:,.0f}',
                'url': reverse('settlement_pages:output_value_record_list') + '?status=calculated',
                'priority': 'high' if pending_value > Decimal('100000') else 'medium',
            })
        
        # 最近记录（最近10条）
        recent_records = all_records.select_related(
            'project', 'stage', 'milestone', 'event', 'responsible_user'
        ).order_by('-calculated_time')[:10]
        
    except Exception as e:
        import logging
        logger = logging.getLogger(__name__)
        logger.exception('获取统计数据失败: %s', str(e))
    
    # 按阶段统计
    stage_stats = []
    try:
        stage_stats = all_records.values('stage__name', 'stage__code').annotate(
            total=Sum('calculated_value'),
            count=Count('id')
        ).order_by('-total')[:6]
    except:
        pass
    
    # 构建上下文
    permission_codes = get_user_permission_codes(request.user)
    context = _context(
        page_title="产值概览",
        page_icon="📊",
        description="产值管理总览和快速入口",
        summary_cards=summary_cards,
        request=request,
        active_menu_id='output_value_home',
    )
    context.update({
        'quick_actions': quick_actions,
        'pending_tasks': pending_tasks,
        'recent_records': recent_records,
        'stage_stats': stage_stats,
        'has_manage_permission': has_manage_permission,
    })
    context['module_sidebar_nav'] = _build_output_value_sidebar_nav(
        permission_codes,
        request_path=request.path,
        active_id='output_value_home'
    )
    
    return render(request, "settlement_center/output_value_home.html", context)


@login_required
def project_settlement_home(request):
    """项目结算首页"""
    permission_codes = get_user_permission_codes(request.user)
    today = timezone.now().date()
    this_month_start = today.replace(day=1)
    
    # 权限检查
    if not _permission_granted('settlement_center.view_project_settlement', permission_codes):
        messages.error(request, '您没有权限访问项目结算')
        return redirect('admin:index')
    
    # 收集统计数据
    summary_cards = []
    
    try:
        from backend.apps.settlement_management.models import ProjectSettlement
        total_settlements = ProjectSettlement.objects.count()
        pending_settlements = ProjectSettlement.objects.filter(
            status__in=['draft', 'submitted']
        ).count()
        
        summary_cards.append({
            'label': '项目结算',
            'icon': '📋',
            'value': str(total_settlements),
            'subvalue': f'待处理 {pending_settlements} 单',
            'url': reverse('settlement_pages:project_settlement_list'),
            'variant': 'warning'
        })
    except Exception as e:
        import logging
        logger = logging.getLogger(__name__)
        logger.exception('获取统计数据失败: %s', str(e))
    
    # 快捷操作
    quick_actions = []
    
    if _permission_granted('settlement_center.project_settlement.create', permission_codes):
        try:
            quick_actions.append({
                'label': '新建项目结算',
                'icon': '➕',
                'description': '创建新的项目结算单',
                'url': reverse('settlement_pages:project_settlement_create'),
                'link_label': '创建结算 →'
            })
        except Exception:
            pass
    
    # 功能模块入口
    module_entries = []
    
    try:
        module_entries.append({
            'label': '结算单列表',
            'icon': '📄',
            'description': '查看和管理项目结算单',
            'url': reverse('settlement_pages:project_settlement_list'),
            'link_label': '进入模块 →'
        })
    except Exception:
        pass
    
    # 构建区域
    sections = []
    
    if quick_actions:
        sections.append({
            'title': '快捷操作',
            'description': '常用的快速操作入口',
            'items': quick_actions,
            'layout': 'grid'
        })
    
    if module_entries:
        sections.append({
            'title': '功能模块',
            'description': '项目结算的各个功能模块入口',
            'items': module_entries,
            'layout': 'grid'
        })
    
    # 构建上下文
    context = _context(
        page_title="项目结算",
        page_icon="💳",
        description="管理项目结算单",
        summary_cards=summary_cards,
        sections=sections,
        request=request,
    )
    
    return render(request, "settlement_center/home.html", context)


@login_required
def payment_management_home(request):
    """回款管理首页"""
    permission_codes = get_user_permission_codes(request.user)
    today = timezone.now().date()
    
    # 权限检查
    if not _permission_granted('settlement_center.view_payment', permission_codes):
        messages.error(request, '您没有权限访问回款管理')
        return redirect('admin:index')
    
    # 收集统计数据
    summary_cards = []
    
    try:
        from backend.apps.production_management.models import BusinessPaymentPlan
        total_plans = BusinessPaymentPlan.objects.count()
        overdue_plans = BusinessPaymentPlan.objects.filter(
            planned_date__lt=today,
            status__in=['pending', 'partial']
        ).count()
        
        summary_cards.append({
            'label': '回款计划',
            'icon': '💰',
            'value': str(total_plans),
            'subvalue': f'逾期 {overdue_plans} 项',
            'url': reverse('settlement_pages:payment_plan_list'),
            'variant': 'danger' if overdue_plans > 0 else 'success'
        })
    except Exception as e:
        import logging
        logger = logging.getLogger(__name__)
        logger.exception('获取统计数据失败: %s', str(e))
    
    # 功能模块入口
    module_entries = []
    
    try:
        module_entries.append({
            'label': '回款计划',
            'icon': '📅',
            'description': '管理回款计划',
            'url': reverse('settlement_pages:payment_plan_list'),
            'link_label': '进入模块 →'
        })
        module_entries.append({
            'label': '回款记录',
            'icon': '🧾',
            'description': '管理实际回款记录',
            'url': reverse('settlement_pages:payment_record_list'),
            'link_label': '进入模块 →'
        })
    except Exception:
        pass
    
    # 构建区域
    sections = []
    
    if module_entries:
        sections.append({
            'title': '功能模块',
            'description': '回款管理的各个功能模块入口',
            'items': module_entries,
            'layout': 'grid'
        })
    
    # 构建上下文
    context = _context(
        page_title="回款管理",
        page_icon="💵",
        description="管理回款计划和记录",
        summary_cards=summary_cards,
        sections=sections,
        request=request,
        active_menu_id='payment_management_home',
    )
    
    return render(request, "settlement_center/home.html", context)


@login_required
def output_value_template_manage(request):
    """阶段权重配置页面"""
    # 检查权限
    from backend.apps.system_management.services import user_has_permission
    has_permission = user_has_permission(request.user, 'settlement_center.manage_output') or user_has_permission(request.user, 'system_management.manage_settings')
    if not has_permission:
        raise PermissionDenied("您没有权限访问阶段权重配置。")
    
    # 检查数据库表是否存在
    try:
        from django.db import connection
        with connection.cursor() as cursor:
            cursor.execute("""
                SELECT EXISTS (
                    SELECT FROM information_schema.tables 
                    WHERE table_schema = 'public' 
                    AND table_name = 'settlement_output_value_stage'
                );
            """)
            table_exists = cursor.fetchone()[0]
        
        if not table_exists:
            from django.contrib import messages
            messages.warning(request, '产值管理模块尚未初始化，请先运行数据库迁移：python manage.py migrate')
            return render(request, "settlement_center/output_value_template.html", _context(
                "阶段权重配置",
                "⚖️",
                "产值管理模块尚未初始化，请先运行数据库迁移。",
                summary_cards=[],
                sections=[],
                request=request,
            ))
    except Exception as e:
        import logging
        logger = logging.getLogger(__name__)
        logger.exception('检查产值表失败: %s', str(e))
        from django.contrib import messages
        messages.error(request, f'检查数据库表失败：{str(e)}')
        return render(request, "settlement_center/output_value_template.html", _context(
            "阶段权重配置",
            "⚖️",
            "无法访问数据库，请检查数据库配置。",
            summary_cards=[],
            sections=[],
            request=request,
        ))
    
    # 获取所有阶段及其里程碑和事件
    try:
        stages = OutputValueStage.objects.filter(is_active=True).prefetch_related(
            'milestones__events'
        ).order_by('order')
    except Exception as e:
        import logging
        logger = logging.getLogger(__name__)
        logger.exception('获取产值阶段失败: %s', str(e))
        from django.contrib import messages
        messages.error(request, f'获取产值阶段失败：{str(e)}')
        return render(request, "settlement_center/output_value_template.html", _context(
            "阶段权重配置",
            "⚖️",
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
    
    # 构建产值权重分配汇总数据
    weight_distribution = []
    total_weight = Decimal('0')
    for stage in stages:
        weight_distribution.append({
            'id': stage.id,
            'stage_name': stage.name,
            'weight': float(stage.stage_percentage),
            'is_subtotal': False,
        })
        total_weight += stage.stage_percentage
    
    # 添加小计行
    weight_distribution.append({
        'id': 0,
        'stage_name': '小计',
        'weight': float(total_weight),
        'is_subtotal': True,
    })
    
    # 构建动态表格配置
    weight_table_config = {
        'id': 'weightDistributionTable',
        'columns': [
            {
                'key': 'stage_name',
                'label': '服务类型',
                'sortable': False,
                'width': '50%',
                'align': 'left',
            },
            {
                'key': 'weight',
                'label': '产值权重',
                'sortable': False,
                'width': '50%',
                'align': 'center',
                'render': 'render_weight',
            },
        ],
        'pagination': False,
        'searchable': False,
        'filterable': False,
        'selectable': False,
    }
    
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
    
    sections = []
    
    # 构建左侧栏菜单
    permission_codes = get_user_permission_codes(request.user)
    context = _context(
        "阶段权重配置",
        "⚖️",
        "查看和管理各服务阶段的产值权重分配情况。",
        summary_cards=summary_cards,
        sections=sections,
        request=request,
        active_menu_id='output_value_template_manage',
    )
    context['stages'] = stage_data
    context['weight_distribution'] = weight_distribution
    context['weight_table_config'] = weight_table_config
    context['weight_table_data'] = weight_distribution
    context['module_sidebar_nav'] = _build_output_value_sidebar_nav(
        permission_codes,
        request_path=request.path,
        active_id='output_value_template_manage'
    )
    
    return render(request, "settlement_center/output_value_template.html", context)


@login_required
def output_value_record_list(request):
    """产值计算记录列表"""
    # 检查权限
    from backend.apps.system_management.services import user_has_permission
    has_view_permission = user_has_permission(request.user, 'settlement_center.view_analysis') or user_has_permission(request.user, 'settlement_center.manage_output')
    if not has_view_permission:
        raise PermissionDenied("您没有权限查看产值记录。")
    
    # 检查数据库表是否存在
    try:
        from django.db import connection
        with connection.cursor() as cursor:
            cursor.execute("""
                SELECT EXISTS (
                    SELECT FROM information_schema.tables 
                    WHERE table_schema = 'public' 
                    AND table_name = 'settlement_output_value_record'
                );
            """)
            table_exists = cursor.fetchone()[0]
        
        if not table_exists:
            from django.contrib import messages
            messages.warning(request, '产值管理模块尚未初始化，请先运行数据库迁移：python manage.py migrate')
            return render(request, "settlement_center/output_value_record_list.html", _context(
                "产值记录查询",
                "📈",
                "产值管理模块尚未初始化，请先运行数据库迁移。",
                summary_cards=[],
                request=request,
            ))
    except Exception as e:
        import logging
        logger = logging.getLogger(__name__)
        logger.exception('检查产值表失败: %s', str(e))
        from django.contrib import messages
        messages.error(request, f'检查数据库表失败：{str(e)}')
        return render(request, "settlement_center/output_value_record_list.html", _context(
            "产值记录查询",
            "📈",
            "无法访问数据库，请检查数据库配置。",
            summary_cards=[],
            request=request,
        ))
    
    # 获取当前用户的产值记录
    try:
        records = OutputValueRecord.objects.select_related(
            'project', 'stage', 'milestone', 'event', 'responsible_user'
        ).order_by('-calculated_time')
    except Exception as e:
        import logging
        logger = logging.getLogger(__name__)
        logger.exception('获取产值记录失败: %s', str(e))
        from django.contrib import messages
        messages.error(request, f'获取产值记录失败：{str(e)}')
        return render(request, "settlement_center/output_value_record_list.html", _context(
            "产值记录查询",
            "📈",
            "获取产值记录失败，请检查数据库表是否正确创建。",
            summary_cards=[],
            request=request,
        ))
    
    # 如果是普通用户，只显示自己的记录
    has_manage_permission = user_has_permission(request.user, 'settlement_center.manage_output')
    if not has_manage_permission:
        records = records.filter(responsible_user=request.user)
    
    # 筛选条件
    project_id = request.GET.get('project_id')
    if project_id:
        records = records.filter(project_id=project_id)
    
    status = request.GET.get('status')
    if status:
        records = records.filter(status=status)
    
    # 日期范围筛选
    date_from = request.GET.get('date_from')
    date_to = request.GET.get('date_to')
    if date_from:
        records = records.filter(calculated_time__gte=date_from)
    if date_to:
        records = records.filter(calculated_time__lte=date_to)
    
    # 阶段筛选
    stage_id = request.GET.get('stage_id')
    if stage_id:
        records = records.filter(stage_id=stage_id)
    
    # 责任人筛选（仅管理员）
    user_id = request.GET.get('user_id')
    if user_id and has_manage_permission:
        records = records.filter(responsible_user_id=user_id)
    
    # 分页
    from django.core.paginator import Paginator
    paginator = Paginator(records, 20)
    page_number = request.GET.get('page', 1)
    try:
        page_obj = paginator.get_page(page_number)
    except:
        page_obj = paginator.get_page(1)
    
    # 统计信息（基于筛选后的记录）
    filtered_records = records
    total_value = filtered_records.filter(status__in=['calculated', 'confirmed']).aggregate(
        total=Sum('calculated_value')
    )['total'] or Decimal('0')
    
    confirmed_value = filtered_records.filter(status='confirmed').aggregate(
        total=Sum('calculated_value')
    )['total'] or Decimal('0')
    
    pending_value = filtered_records.filter(status='calculated').aggregate(
        total=Sum('calculated_value')
    )['total'] or Decimal('0')
    
    total_count = filtered_records.count()
    confirmed_count = filtered_records.filter(status='confirmed').count()
    pending_count = filtered_records.filter(status='calculated').count()
    
    summary_cards = [
        {
            'label': '总产值',
            'value': f'¥{total_value:,.2f}',
            'hint': f'共 {total_count} 条记录',
            'icon': '💰',
        },
        {
            'label': '已确认产值',
            'value': f'¥{confirmed_value:,.2f}',
            'hint': f'{confirmed_count} 条已确认',
            'icon': '✅',
        },
        {
            'label': '待确认产值',
            'value': f'¥{pending_value:,.2f}',
            'hint': f'{pending_count} 条待确认',
            'icon': '⏳',
        },
    ]
    
    # 构建左侧栏菜单
    permission_codes = get_user_permission_codes(request.user)
    context = _context(
        "产值记录查询",
        "📈",
        "查看和管理产值计算记录，了解产值分配情况。",
        summary_cards=summary_cards,
        request=request,
        active_menu_id='output_value_record_list',
    )
    context['records'] = page_obj
    context['projects'] = Project.objects.filter(status__in=['in_progress', 'completed']).order_by('-created_time')
    context['stages'] = OutputValueStage.objects.filter(is_active=True).order_by('order')
    context['users'] = User.objects.filter(is_active=True).order_by('username') if has_manage_permission else []
    context['has_manage_permission'] = has_manage_permission
    context['current_filters'] = {
        'project_id': project_id,
        'status': status,
        'date_from': date_from,
        'date_to': date_to,
        'stage_id': stage_id,
        'user_id': user_id,
    }
    context['module_sidebar_nav'] = _build_output_value_sidebar_nav(
        permission_codes,
        request_path=request.path,
        active_id='output_value_record_list'
    )
    
    return render(request, "settlement_center/output_value_record_list.html", context)


@login_required
def project_output_value_detail(request, project_id):
    """项目产值详情页（在产值管理模块中查看项目的产值统计）"""
    project = get_object_or_404(Project, id=project_id)
    permission_codes = get_user_permission_codes(request.user)
    
    # 检查权限
    from backend.apps.system_management.services import user_has_permission
    has_view_permission = user_has_permission(request.user, 'settlement_center.view_analysis') or user_has_permission(request.user, 'settlement_center.manage_output')
    if not has_view_permission:
        # 检查是否是项目成员
        if not (project.project_manager == request.user or 
                project.business_manager == request.user or
                project.team_members.filter(user=request.user, is_active=True).exists()):
            messages.error(request, '您没有权限查看此项目的产值信息')
            return redirect('settlement_pages:output_value_record_list')
    
    # 获取项目产值统计
    try:
        output_value_summary = get_project_output_value_summary(project)
    except Exception as e:
        import logging
        logger = logging.getLogger(__name__)
        logger.exception('获取项目产值统计失败: %s', str(e))
        messages.error(request, f'获取项目产值统计失败：{str(e)}')
        return redirect('settlement_pages:output_value_record_list')
    
    # 检查权限
    has_manage_permission = user_has_permission(request.user, 'settlement_center.manage_output')
    
    # 产值记录分页
    paginator = Paginator(output_value_summary['records'], 20)
    page_number = request.GET.get('page', 1)
    page_obj = paginator.get_page(page_number)
    
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
    
    return render(request, "settlement_center/project_output_value_detail.html", context)


@login_required
def output_value_record_confirm(request, record_id):
    """确认产值记录"""
    record = get_object_or_404(OutputValueRecord, id=record_id)
    
    # 检查权限：只有责任人或有管理权限的用户可以确认
    from backend.apps.system_management.services import user_has_permission
    has_manage_permission = user_has_permission(request.user, 'settlement_center.manage_output')
    if record.responsible_user != request.user and not has_manage_permission:
        raise PermissionDenied("您没有权限确认此产值记录。")
    
    if request.method == 'POST':
        record.status = 'confirmed'
        record.confirmed_time = timezone.now()
        record.confirmed_by = request.user
        record.save(update_fields=['status', 'confirmed_time', 'confirmed_by', 'updated_time'])
        messages.success(request, '产值记录已确认。')
        return redirect('settlement_pages:output_value_record_list')
    
    # 构建左侧栏菜单
    permission_codes = get_user_permission_codes(request.user)
    context = _context(
        '确认产值记录',
        '✅',
        f'确认产值记录：{record.id}',
        request=request,
    )
    context['record'] = record
    context['module_sidebar_nav'] = _build_output_value_sidebar_nav(
        permission_codes,
        request_path=request.path,
        active_id='output_value_record_list'
    )
    return render(request, "settlement_center/output_value_record_confirm.html", context)


@login_required
def output_value_record_batch_confirm(request):
    """批量确认产值记录"""
    from backend.apps.system_management.services import user_has_permission
    has_manage_permission = user_has_permission(request.user, 'settlement_center.manage_output')
    if not has_manage_permission:
        raise PermissionDenied("您没有权限批量确认产值记录。")
    
    if request.method == 'POST':
        record_ids = request.POST.getlist('record_ids')
        if not record_ids:
            messages.error(request, '请选择要确认的产值记录。')
            return redirect('settlement_pages:output_value_record_list')
        
        # 获取记录并检查权限
        records = OutputValueRecord.objects.filter(
            id__in=record_ids,
            status='calculated'
        )
        
        if not records.exists():
            messages.warning(request, '没有可确认的记录。')
            return redirect('settlement_pages:output_value_record_list')
        
        # 批量更新
        updated_count = records.update(
            status='confirmed',
            confirmed_time=timezone.now(),
            confirmed_by=request.user
        )
        
        messages.success(request, f'成功确认 {updated_count} 条产值记录。')
    else:
        messages.error(request, '无效的请求方法。')
    
    return redirect('settlement_pages:output_value_record_list')


@login_required
def output_value_record_export(request):
    """导出产值记录"""
    from django.http import HttpResponse
    import csv
    
    # 检查权限
    from backend.apps.system_management.services import user_has_permission
    has_view_permission = user_has_permission(request.user, 'settlement_center.view_analysis') or user_has_permission(request.user, 'settlement_center.manage_output')
    if not has_view_permission:
        raise PermissionDenied("您没有权限导出产值记录。")
    
    # 获取筛选条件（与列表页面相同）
    records = OutputValueRecord.objects.select_related(
        'project', 'stage', 'milestone', 'event', 'responsible_user'
    ).order_by('-calculated_time')
    
    has_manage_permission = user_has_permission(request.user, 'settlement_center.manage_output')
    if not has_manage_permission:
        records = records.filter(responsible_user=request.user)
    
    # 应用筛选条件
    project_id = request.GET.get('project_id')
    if project_id:
        records = records.filter(project_id=project_id)
    
    status = request.GET.get('status')
    if status:
        records = records.filter(status=status)
    
    date_from = request.GET.get('date_from')
    date_to = request.GET.get('date_to')
    if date_from:
        records = records.filter(calculated_time__gte=date_from)
    if date_to:
        records = records.filter(calculated_time__lte=date_to)
    
    stage_id = request.GET.get('stage_id')
    if stage_id:
        records = records.filter(stage_id=stage_id)
    
    user_id = request.GET.get('user_id')
    if user_id and has_manage_permission:
        records = records.filter(responsible_user_id=user_id)
    
    # 创建CSV响应
    response = HttpResponse(content_type='text/csv; charset=utf-8-sig')
    response['Content-Disposition'] = f'attachment; filename="产值记录_{timezone.now().strftime("%Y%m%d_%H%M%S")}.csv"'
    
    writer = csv.writer(response)
    
    # 写入表头
    headers = ['项目编号', '项目名称', '产值阶段', '里程碑', '事件', '责任人', 
               '计取基数', '阶段比例(%)', '里程碑比例(%)', '事件比例(%)', 
               '计算产值', '状态', '计算时间', '确认时间', '确认人']
    writer.writerow(headers)
    
    # 写入数据
    for record in records:
        writer.writerow([
            record.project.project_number if record.project else '',
            record.project.name if record.project else '',
            record.stage.name if record.stage else '',
            record.milestone.name if record.milestone else '',
            record.event.name if record.event else '',
            record.responsible_user.get_full_name() or record.responsible_user.username if record.responsible_user else '',
            f'{record.base_amount:,.2f}',
            f'{record.stage_percentage:.2f}',
            f'{record.milestone_percentage:.2f}',
            f'{record.event_percentage:.2f}',
            f'{record.calculated_value:,.2f}',
            record.get_status_display(),
            record.calculated_time.strftime('%Y-%m-%d %H:%M:%S') if record.calculated_time else '',
            record.confirmed_time.strftime('%Y-%m-%d %H:%M:%S') if record.confirmed_time else '',
            record.confirmed_by.get_full_name() or record.confirmed_by.username if record.confirmed_by else '',
        ])
    
    return response


@login_required
def output_value_statistics(request):
    """产值统计报表"""
    # 检查权限
    from backend.apps.system_management.services import user_has_permission
    has_view_permission = user_has_permission(request.user, 'settlement_center.view_analysis') or user_has_permission(request.user, 'settlement_center.manage_output')
    if not has_view_permission:
        raise PermissionDenied("您没有权限查看产值统计。")
    
    # 检查数据库表是否存在
    try:
        from django.db import connection
        with connection.cursor() as cursor:
            cursor.execute("""
                SELECT EXISTS (
                    SELECT FROM information_schema.tables 
                    WHERE table_schema = 'public' 
                    AND table_name = 'settlement_output_value_record'
                );
            """)
            table_exists = cursor.fetchone()[0]
        
        if not table_exists:
            from django.contrib import messages
            messages.warning(request, '产值管理模块尚未初始化，请先运行数据库迁移：python manage.py migrate')
            return render(request, "settlement_center/output_value_statistics.html", _context(
                "产值统计报表",
                "📊",
                "产值管理模块尚未初始化，请先运行数据库迁移。",
                summary_cards=[],
                request=request,
            ))
    except Exception as e:
        import logging
        logger = logging.getLogger(__name__)
        logger.exception('检查产值表失败: %s', str(e))
        from django.contrib import messages
        messages.error(request, f'检查数据库表失败：{str(e)}')
        return render(request, "settlement_center/output_value_statistics.html", _context(
            "产值统计报表",
            "📊",
            "无法访问数据库，请检查数据库配置。",
            summary_cards=[],
            request=request,
        ))
    
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
        import logging
        logger = logging.getLogger(__name__)
        logger.exception('获取产值记录失败: %s', str(e))
        from django.contrib import messages
        messages.error(request, f'获取产值记录失败：{str(e)}')
        return render(request, "settlement_center/output_value_statistics.html", _context(
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
    has_manage_permission = user_has_permission(request.user, 'settlement_center.manage_output')
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
    
    # 构建左侧栏菜单
    permission_codes = get_user_permission_codes(request.user)
    context = _context(
        "产值统计报表",
        "📊",
        "查看产值分配统计和分析报表。",
        summary_cards=summary_cards,
        request=request,
    )
    context['module_sidebar_nav'] = _build_output_value_sidebar_nav(
        permission_codes,
        request_path=request.path,
        active_id='output_value_statistics'
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
    
    return render(request, "settlement_center/output_value_statistics.html", context)


# ==================== 结算管理辅助函数 ====================

def _generate_settlement_items_from_opinions(settlement, user):
    """从项目的Opinion生成结算明细项（已禁用：生产质量模块已删除）"""
    # 生产质量模块已删除，此功能已禁用
    # 保留函数定义以避免调用错误，但返回0表示未生成任何明细项
    import logging
    logger = logging.getLogger(__name__)
    logger.warning('尝试从Opinion生成结算明细项，但生产质量模块已删除')
    return 0


# ==================== 结算管理视图函数 ====================

@login_required
def project_settlement_list(request):
    """项目结算列表页"""
    permission_codes = get_user_permission_codes(request.user)
    if not _permission_granted('settlement_center.settlement.view', permission_codes):
        messages.error(request, '您没有权限查看项目结算')
        return redirect('settlement_pages:output_value_record_list')
    
    settlements = ProjectSettlement.objects.select_related(
        'project', 'contract', 'created_by'
    ).order_by('-settlement_date', '-created_time')
    
    # 权限过滤：如果不是管理员，只能查看自己创建的
    if not _permission_granted('settlement_center.settlement.manage', permission_codes):
        settlements = settlements.filter(created_by=request.user)
    
    # 筛选
    status_filter = request.GET.get('status')
    if status_filter:
        settlements = settlements.filter(status=status_filter)
    
    project_id = request.GET.get('project_id')
    if project_id:
        settlements = settlements.filter(project_id=project_id)
    
    # 分页
    page_size = request.GET.get('page_size', '10')
    try:
        per_page = int(page_size)
        if per_page not in [10, 20, 50]:
            per_page = 10
    except (ValueError, TypeError):
        per_page = 10
    paginator = Paginator(settlements, per_page)
    page_number = request.GET.get('page', 1)
    page_obj = paginator.get_page(page_number)
    
    # 统计信息
    total_count = settlements.count()
    total_amount = settlements.filter(status__in=['confirmed', 'reconciliation']).aggregate(
        total=Sum('total_settlement_amount')
    )['total'] or Decimal('0')
    pending_count = settlements.filter(status__in=['submitted', 'client_review', 'client_feedback', 'reconciliation']).count()
    
    summary_cards = []
    
    context = _context(
        "项目结算管理",
        "💰",
        "管理项目结算单，包括结算申请、审核和确认",
        summary_cards=summary_cards,
        request=request,
    )
    context.update({
        'settlements': page_obj,
        'projects': Project.objects.filter(status__in=['in_progress', 'completed']).order_by('-created_time'),
        'status_choices': ProjectSettlement.STATUS_CHOICES,
        'status_filter': status_filter,
        'project_id': project_id,
        'can_create': _permission_granted('settlement_center.settlement.create', permission_codes),
    })
    
    return render(request, "settlement_center/project_settlement_list.html", context)


@login_required
def project_settlement_detail(request, settlement_id):
    """项目结算详情页"""
    settlement = get_object_or_404(ProjectSettlement, id=settlement_id)
    permission_codes = get_user_permission_codes(request.user)
    
    # 权限检查：只有有查看权限或创建人可以查看
    if not _permission_granted('settlement_center.settlement.view', permission_codes):
        if settlement.created_by != request.user:
            messages.error(request, '您没有权限查看此结算单')
            return redirect('settlement_pages:project_settlement_list')
    
    # 获取项目产值统计（从产值管理模块获取）
    output_value_summary = get_project_output_value_for_settlement(settlement.project)
    total_calculated_value = output_value_summary['total_output_value']
    
    # 如果结算单的累计产值未设置，自动更新
    if settlement.total_output_value == 0 and total_calculated_value > 0:
        settlement.total_output_value = total_calculated_value
        settlement.save(update_fields=['total_output_value'])
    
    # 检查可执行的操作
    can_edit = (
        settlement.status == 'draft' and
        (_permission_granted('settlement_center.settlement.manage', permission_codes) or
         settlement.created_by == request.user)
    )
    can_submit = (
        settlement.status == 'draft' and
        (_permission_granted('settlement_center.settlement.manage', permission_codes) or
         settlement.created_by == request.user)
    )
    can_finance_review = (
        settlement.status == 'submitted' and
        _permission_granted('settlement_center.settlement.finance_review', permission_codes)
    )
    can_manager_approve = (
        settlement.status == 'finance_review' and
        _permission_granted('settlement_center.settlement.manager_approve', permission_codes)
    )
    can_gm_approve = (
        settlement.status == 'manager_approve' and
        _permission_granted('settlement_center.settlement.gm_approve', permission_codes)
    )
    can_confirm = (
        settlement.status == 'approved' and
        _permission_granted('settlement_center.settlement.confirm', permission_codes)
    )
    
    context = _context(
        f"项目结算 - {settlement.settlement_number}",
        "💰",
        f"项目：{settlement.project.name}",
        request=request,
    )
    # 获取结算明细项
    settlement_items = settlement.items.select_related('reviewed_by', 'created_by').order_by('order')
    
    # 检查是否有权限审核明细项（造价工程师或有管理权限）
    can_review_items = (
        settlement.status == 'draft' and
        (_permission_granted('settlement_center.settlement.manage', permission_codes) or
         request.user.roles.filter(code='cost_engineer').exists())
    )
    
    # 检查是否可以重新生成明细项
    can_generate_items = (
        settlement.status == 'draft' and
        (_permission_granted('settlement_center.settlement.manage', permission_codes) or
         settlement.created_by == request.user)
    )
    
    context.update({
        'settlement': settlement,
        'settlement_items': settlement_items,
        'output_value_summary': output_value_summary,
        'total_calculated_value': total_calculated_value,
        'can_edit': can_edit,
        'can_submit': can_submit,
        'can_review_items': can_review_items,
        'can_generate_items': can_generate_items,
        'can_finance_review': can_finance_review,
        'can_manager_approve': can_manager_approve,
        'can_gm_approve': can_gm_approve,
        'can_confirm': can_confirm,
    })
    
    return render(request, "settlement_center/project_settlement_detail.html", context)


@login_required
def project_settlement_create(request):
    """创建项目结算单"""
    permission_codes = get_user_permission_codes(request.user)
    if not _permission_granted('settlement_center.settlement.create', permission_codes):
        messages.error(request, '您没有权限创建项目结算单')
        return redirect('settlement_pages:project_settlement_list')
    
    if request.method == 'POST':
        form = ProjectSettlementForm(request.POST, request.FILES, user=request.user)
        if form.is_valid():
            settlement = form.save(commit=False)
            settlement.created_by = request.user
            
            # 设置默认结算日期（如果未填写）
            if not settlement.settlement_date:
                from datetime import date
                settlement.settlement_date = date.today()
            
            # 如果选择了项目，自动获取合同金额和产值
            if settlement.project:
                # 从合同获取金额
                if settlement.contract:
                    settlement.contract_amount = settlement.contract.contract_amount or Decimal('0')
                elif settlement.project.contracts.exists():
                    latest_contract = settlement.project.contracts.order_by('-created_time').first()
                    if latest_contract:
                        settlement.contract = latest_contract
                        settlement.contract_amount = latest_contract.contract_amount or Decimal('0')
                
                # 从产值管理模块获取产值统计
                output_value_summary = get_project_output_value_for_settlement(settlement.project)
                if output_value_summary['total_output_value'] > 0:
                    settlement.total_output_value = output_value_summary['total_output_value']
            
            settlement.save()
            
            # 如果选择了项目，自动从Opinion生成结算明细项
            if settlement.project:
                items_count = _generate_settlement_items_from_opinions(settlement, request.user)
                if items_count > 0:
                    messages.success(request, f'项目结算单 {settlement.settlement_number} 创建成功！已自动生成 {items_count} 条结算明细项。')
                else:
                    messages.info(request, f'项目结算单 {settlement.settlement_number} 创建成功！未找到可用的Opinion（需有节省金额），请手动添加明细项。')
            else:
                messages.success(request, f'项目结算单 {settlement.settlement_number} 创建成功！')
            
            return redirect('settlement_pages:project_settlement_detail', settlement_id=settlement.id)
        else:
            messages.error(request, "请检查表单中的错误。")
    else:
        form = ProjectSettlementForm(user=request.user)
    
    context = _context(
        "新增项目结算单",
        "➕",
        "创建新的项目结算单",
        request=request,
    )
    context.update({
        'form': form,
        'is_create': True,
    })
    
    return render(request, "settlement_center/project_settlement_form.html", context)


@login_required
def project_settlement_update(request, settlement_id):
    """编辑项目结算单"""
    settlement = get_object_or_404(ProjectSettlement, id=settlement_id)
    permission_codes = get_user_permission_codes(request.user)
    
    # 权限检查：只有草稿状态才能编辑，且必须是创建人或管理员
    if settlement.status != 'draft':
        messages.error(request, '只有草稿状态的结算单才能编辑')
        return redirect('settlement_pages:project_settlement_detail', settlement_id=settlement.id)
    
    if not _permission_granted('settlement_center.settlement.manage', permission_codes):
        if settlement.created_by != request.user:
            messages.error(request, '您没有权限编辑此结算单')
            return redirect('settlement_pages:project_settlement_detail', settlement_id=settlement.id)
    
    if request.method == 'POST':
        form = ProjectSettlementForm(request.POST, request.FILES, instance=settlement, user=request.user)
        if form.is_valid():
            settlement = form.save()
            messages.success(request, f'项目结算单 {settlement.settlement_number} 更新成功！')
            return redirect('settlement_pages:project_settlement_detail', settlement_id=settlement.id)
        else:
            messages.error(request, "请检查表单中的错误。")
    else:
        form = ProjectSettlementForm(instance=settlement, user=request.user)
    
    context = _context(
        f"编辑项目结算单 - {settlement.settlement_number}",
        "✏️",
        f"项目：{settlement.project.name}",
        request=request,
    )
    context.update({
        'form': form,
        'settlement': settlement,
        'is_create': False,
    })
    
    return render(request, "settlement_center/project_settlement_form.html", context)


@login_required
def project_settlement_submit(request, settlement_id):
    """提交结算单审核"""
    settlement = get_object_or_404(ProjectSettlement, id=settlement_id)
    permission_codes = get_user_permission_codes(request.user)
    
    if settlement.status != 'draft':
        messages.error(request, '只有草稿状态的结算单才能提交')
        return redirect('settlement_pages:project_settlement_detail', settlement_id=settlement.id)
    
    if not _permission_granted('settlement_center.settlement.manage', permission_codes):
        if settlement.created_by != request.user:
            messages.error(request, '您没有权限提交此结算单')
            return redirect('settlement_pages:project_settlement_detail', settlement_id=settlement.id)
    
    if request.method == 'POST':
        settlement.status = 'submitted'
        settlement.submitted_by = request.user
        settlement.submitted_time = timezone.now()
        settlement.save(update_fields=['status', 'submitted_by', 'submitted_time', 'updated_time'])
        messages.success(request, '结算单已提交审核')
        return redirect('settlement_pages:project_settlement_detail', settlement_id=settlement.id)
    
    context = _context(
        "提交结算单",
        "📤",
        f"确认提交结算单 {settlement.settlement_number} 进行审核？",
        request=request,
    )
    context.update({
        'settlement': settlement,
    })
    return render(request, "settlement_center/project_settlement_confirm.html", context)


# ==================== 回款管理模块 ====================

# 回款管理菜单结构定义
PAYMENT_MENU_STRUCTURE = [
    {
        'id': 'payment_management_home',
        'label': '回款管理首页',
        'icon': '🏠',
        'url_name': 'settlement_pages:payment_management_home',
        'permission': 'settlement_center.view_payment',
    },
    {
        'id': 'payment_plan',
        'label': '回款计划',
        'icon': '💳',
        'permission': 'settlement_center.payment.view',
        'children': [
            {
                'id': 'payment_plan_list',
                'label': '回款计划列表',
                'icon': '📋',
                'url_name': 'settlement_pages:payment_plan_list',
                'permission': 'settlement_center.payment.view',
            },
            {
                'id': 'payment_plan_create',
                'label': '新建回款计划',
                'icon': '➕',
                'url_name': 'settlement_pages:payment_plan_create',
                'permission': 'settlement_center.payment.view',
            },
        ]
    },
    {
        'id': 'payment_application',
        'label': '回款申请',
        'icon': '📄',
        'permission': 'settlement_center.payment.view',
        'children': [
            {
                'id': 'payment_application_list',
                'label': '回款申请列表',
                'icon': '📋',
                'url_name': 'settlement_pages:payment_application_list',
                'permission': 'settlement_center.payment.view',
            },
            {
                'id': 'payment_application_create',
                'label': '新建回款申请',
                'icon': '➕',
                'url_name': 'settlement_pages:payment_application_create',
                'permission': 'settlement_center.payment.view',
            },
        ]
    },
    {
        'id': 'payment_record',
        'label': '回款记录',
        'icon': '💰',
        'permission': 'settlement_center.payment.view',
        'children': [
            {
                'id': 'payment_record_list',
                'label': '回款记录列表',
                'icon': '📝',
                'url_name': 'settlement_pages:payment_record_list',
                'permission': 'settlement_center.payment.view',
            },
            {
                'id': 'payment_record_create_standalone',
                'label': '新建回款记录',
                'icon': '➕',
                'url_name': 'settlement_pages:payment_record_create_standalone',
                'permission': 'settlement_center.payment.view',
            },
        ]
    },
]
    
def _build_payment_sidebar_nav(permission_set, request_path=None, active_id=None):
    """生成回款管理左侧菜单（统一格式）"""
    # 使用统一的菜单构建函数
    return _build_unified_sidebar_nav(PAYMENT_MENU_STRUCTURE, permission_set, active_id=active_id)


@login_required
def payment_plan_list(request):
    """回款计划列表页面"""
    # 注意：项目回款计划模型已从project_center模块删除，现在只使用商务回款计划
    from backend.apps.production_management.models import BusinessPaymentPlan
    
    permission_codes = get_user_permission_codes(request.user)
    
    # 权限检查：暂时注释掉，因为权限可能还未创建
    # if not _permission_granted('payment_management.payment_plan.view', permission_codes):
    #     messages.error(request, '您没有权限查看回款计划')
    #     return redirect('home')
    
    # 获取筛选参数
    search = request.GET.get('search', '')
    status_filter = request.GET.get('status', '')
    plan_type = request.GET.get('plan_type', '')  # 'project' or 'business'
    
    # 获取商务回款计划
    business_plans = BusinessPaymentPlan.objects.select_related('contract', 'contract__client').all()
    
    # 项目回款计划已不存在，设置为空
    project_plans = BusinessPaymentPlan.objects.none()
    
    # 应用筛选
    if search:
        business_plans = business_plans.filter(
            Q(phase_name__icontains=search) |
            Q(contract__contract_number__icontains=search) |
            Q(contract__client__name__icontains=search)
        )
    
    if status_filter:
        business_plans = business_plans.filter(status=status_filter)
    
    if plan_type == 'project':
        # 项目回款计划已不存在，返回空结果
        business_plans = business_plans.none()
    
    # 合并数据并排序
    all_plans = []
    # 注意：项目回款计划模型已删除，现在只处理商务回款计划
    for plan in business_plans:
        all_plans.append({
            'id': plan.id,
            'type': 'business',
            'phase_name': plan.phase_name,
            'planned_amount': plan.planned_amount,
            'actual_amount': plan.actual_amount or Decimal('0'),
            'planned_date': plan.planned_date,
            'actual_date': plan.actual_date,
            'status': plan.status,
            'related_name': plan.contract.client.name if plan.contract and plan.contract.client else '',
            'related_number': plan.contract.contract_number if plan.contract else '',
        })
    
    # 按计划日期排序
    all_plans.sort(key=lambda x: x['planned_date'], reverse=True)
    
    # 分页
    page_size = request.GET.get('page_size', '10')
    try:
        per_page = int(page_size)
        if per_page not in [10, 20, 50]:
            per_page = 10
    except (ValueError, TypeError):
        per_page = 10
    paginator = Paginator(all_plans, per_page)
    page_number = request.GET.get('page', 1)
    page_obj = paginator.get_page(page_number)
    
    # 统计信息
    total_plans = len(all_plans)
    total_planned_amount = sum(p['planned_amount'] for p in all_plans)
    total_actual_amount = sum(p['actual_amount'] for p in all_plans)
    
    summary_cards = []
    
    context = _context(
        "回款计划管理",
        "💳",
        "统一管理项目回款计划和商务合同回款计划",
        summary_cards=summary_cards,
        request=request,
    )
    context.update({
        'page_obj': page_obj,
        'search': search,
        'status_filter': status_filter,
        'plan_type': plan_type,
        'status_choices': BusinessPaymentPlan.STATUS_CHOICES,
    })
    return render(request, "settlement_center/payment_plan_list.html", context)


@login_required
def payment_plan_create(request):
    """新建回款计划页面"""
    from backend.apps.production_management.models import BusinessPaymentPlan, BusinessContract
    
    permission_codes = get_user_permission_codes(request.user)
    
    # 权限检查
    if not _permission_granted('settlement_center.view_payment', permission_codes):
        messages.error(request, '您没有权限创建回款计划')
        return redirect('settlement_pages:payment_plan_list')
    
    if request.method == 'POST':
        try:
            contract_id = request.POST.get('contract_id')
            phase_name = request.POST.get('phase_name', '').strip()
            phase_description = request.POST.get('phase_description', '').strip()
            planned_amount = request.POST.get('planned_amount', '0')
            planned_date = request.POST.get('planned_date')
            trigger_condition = request.POST.get('trigger_condition', '').strip()
            condition_detail = request.POST.get('condition_detail', '').strip()
            notes = request.POST.get('notes', '').strip()
            
            if not contract_id:
                messages.error(request, '请选择合同')
            elif not phase_name:
                messages.error(request, '请填写回款阶段名称')
            elif not planned_amount or Decimal(planned_amount) <= 0:
                messages.error(request, '请填写有效的计划金额')
            elif not planned_date:
                messages.error(request, '请选择计划日期')
            else:
                contract = get_object_or_404(BusinessContract, id=contract_id)
                payment_plan = BusinessPaymentPlan.objects.create(
                    contract=contract,
                    phase_name=phase_name,
                    phase_description=phase_description,
                    planned_amount=Decimal(planned_amount),
                    planned_date=planned_date,
                    trigger_condition=trigger_condition,
                    condition_detail=condition_detail,
                    notes=notes,
                    status='pending',
                )
                messages.success(request, f'回款计划 "{payment_plan.phase_name}" 创建成功')
                return redirect('settlement_pages:payment_plan_list')
        except Exception as e:
            import logging
            logger = logging.getLogger(__name__)
            logger.exception('创建回款计划失败: %s', str(e))
            messages.error(request, f'创建回款计划失败：{str(e)}')
    
    # 获取可用的商务合同列表
    contracts = BusinessContract.objects.select_related('client', 'project').filter(
        status__in=['signed', 'executing']
    ).order_by('-contract_date', '-created_time')
    
    context = _context(
        "新建回款计划",
        "➕",
        "为商务合同创建新的回款计划",
        request=request,
        active_menu_id='payment_plan_create',
    )
    context.update({
        'contracts': contracts,
        'status_choices': BusinessPaymentPlan.STATUS_CHOICES,
    })
    return render(request, "settlement_center/payment_plan_form.html", context)


@login_required
def payment_plan_detail(request, plan_type, plan_id):
    """回款计划详情页面"""
    # 注意：项目回款计划模型已从project_center模块删除，现在只使用商务回款计划
    from backend.apps.production_management.models import BusinessPaymentPlan
    
    permission_codes = get_user_permission_codes(request.user)
    
    # 根据类型获取回款计划
    if plan_type == 'project':
        # 项目回款计划已不存在，返回错误
        messages.error(request, '项目回款计划功能已移除，请使用商务回款计划')
        return redirect('settlement_pages:payment_plan_list')
    elif plan_type == 'business':
        plan = get_object_or_404(BusinessPaymentPlan, id=plan_id)
        related_obj = plan.contract
    else:
        messages.error(request, '无效的回款计划类型')
        return redirect('settlement_pages:payment_plan_list')
    
    # 获取关联的回款记录
    payment_records = PaymentRecord.objects.filter(
        payment_plan_type=plan_type,
        payment_plan_id=plan_id
    ).select_related('created_by', 'confirmed_by').order_by('-payment_date', '-created_time')
    
    # 计算已回款总额
    total_received = payment_records.filter(status='confirmed').aggregate(
        total=Sum('payment_amount')
    )['total'] or Decimal('0')
    
    context = _context(
        f"回款计划详情 - {plan.phase_name}",
        "💳",
        f"计划金额：¥{plan.planned_amount:,.2f}",
        request=request,
    )
    context.update({
        'plan': plan,
        'plan_type': plan_type,
        'related_obj': related_obj,
        'payment_records': payment_records,
        'total_received': total_received,
        'remaining_amount': plan.planned_amount - total_received,
    })
    return render(request, "settlement_center/payment_plan_detail.html", context)


@login_required
def payment_plan_edit(request, plan_type, plan_id):
    """编辑回款计划"""
    from backend.apps.production_management.models import BusinessPaymentPlan, BusinessContract
    
    permission_codes = get_user_permission_codes(request.user)
    
    # 权限检查
    if not _permission_granted('settlement_center.view_payment', permission_codes):
        messages.error(request, '您没有权限编辑回款计划')
        return redirect('settlement_pages:payment_plan_list')
    
    # 根据类型获取回款计划
    if plan_type == 'project':
        messages.error(request, '项目回款计划功能已移除，请使用商务回款计划')
        return redirect('settlement_pages:payment_plan_list')
    elif plan_type == 'business':
        plan = get_object_or_404(BusinessPaymentPlan, id=plan_id)
    else:
        messages.error(request, '无效的回款计划类型')
        return redirect('settlement_pages:payment_plan_list')
    
    if request.method == 'POST':
        try:
            phase_name = request.POST.get('phase_name', '').strip()
            phase_description = request.POST.get('phase_description', '').strip()
            planned_amount = request.POST.get('planned_amount', '0')
            planned_date = request.POST.get('planned_date')
            trigger_condition = request.POST.get('trigger_condition', '').strip()
            condition_detail = request.POST.get('condition_detail', '').strip()
            notes = request.POST.get('notes', '').strip()
            status = request.POST.get('status', 'pending')
            
            if not phase_name:
                messages.error(request, '请填写回款阶段名称')
            elif not planned_amount or Decimal(planned_amount) <= 0:
                messages.error(request, '请填写有效的计划金额')
            elif not planned_date:
                messages.error(request, '请选择计划日期')
            else:
                plan.phase_name = phase_name
                plan.phase_description = phase_description
                plan.planned_amount = Decimal(planned_amount)
                plan.planned_date = planned_date
                plan.trigger_condition = trigger_condition
                plan.condition_detail = condition_detail
                plan.notes = notes
                plan.status = status
                plan.save()
                
                messages.success(request, f'回款计划 "{plan.phase_name}" 更新成功')
                return redirect('settlement_pages:payment_plan_detail', plan_type=plan_type, plan_id=plan_id)
        except Exception as e:
            import logging
            logger = logging.getLogger(__name__)
            logger.exception('更新回款计划失败: %s', str(e))
            messages.error(request, f'更新回款计划失败：{str(e)}')
    
    # 获取可用的商务合同列表（用于显示，编辑时不能修改）
    contracts = BusinessContract.objects.select_related('client', 'project').filter(
        status__in=['signed', 'executing']
    ).order_by('-contract_date', '-created_time')
    
    context = _context(
        "编辑回款计划",
        "✏️",
        f"编辑回款计划：{plan.phase_name}",
        request=request,
        active_menu_id='payment_plan_list',
    )
    context.update({
        'plan': plan,
        'plan_type': plan_type,
        'contracts': contracts,
        'status_choices': BusinessPaymentPlan.STATUS_CHOICES,
    })
    return render(request, "settlement_center/payment_plan_form.html", context)


@login_required
def payment_plan_delete(request, plan_type, plan_id):
    """删除回款计划"""
    from backend.apps.production_management.models import BusinessPaymentPlan
    
    permission_codes = get_user_permission_codes(request.user)
    
    # 权限检查
    if not _permission_granted('settlement_center.view_payment', permission_codes):
        messages.error(request, '您没有权限删除回款计划')
        return redirect('settlement_pages:payment_plan_list')
    
    # 根据类型获取回款计划
    if plan_type == 'project':
        messages.error(request, '项目回款计划功能已移除，请使用商务回款计划')
        return redirect('settlement_pages:payment_plan_list')
    elif plan_type == 'business':
        plan = get_object_or_404(BusinessPaymentPlan, id=plan_id)
    else:
        messages.error(request, '无效的回款计划类型')
        return redirect('settlement_pages:payment_plan_list')
    
    if request.method == 'POST':
        try:
            # 检查是否有关联的回款记录
            payment_records = PaymentRecord.objects.filter(
                payment_plan_type=plan_type,
                payment_plan_id=plan_id
            )
            
            if payment_records.exists():
                messages.error(request, f'该回款计划已有 {payment_records.count()} 条回款记录，无法删除。请先删除或转移相关回款记录。')
                return redirect('settlement_pages:payment_plan_detail', plan_type=plan_type, plan_id=plan_id)
            
            plan_name = plan.phase_name
            plan.delete()
            messages.success(request, f'回款计划 "{plan_name}" 已删除')
            return redirect('settlement_pages:payment_plan_list')
        except Exception as e:
            import logging
            logger = logging.getLogger(__name__)
            logger.exception('删除回款计划失败: %s', str(e))
            messages.error(request, f'删除回款计划失败：{str(e)}')
    
    # GET请求，显示确认页面
    context = _context(
        "删除回款计划",
        "🗑️",
        f"确认删除回款计划：{plan.phase_name}",
        request=request,
        active_menu_id='payment_plan_list',
    )
    context.update({
        'plan': plan,
        'plan_type': plan_type,
        'payment_records_count': PaymentRecord.objects.filter(
            payment_plan_type=plan_type,
            payment_plan_id=plan_id
        ).count(),
    })
    return render(request, "settlement_center/payment_plan_delete_confirm.html", context)


@login_required
def payment_record_list(request):
    """回款记录列表页面"""
    permission_codes = get_user_permission_codes(request.user)
    
    # 获取筛选参数
    search = request.GET.get('search', '')
    status_filter = request.GET.get('status', '')
    start_date = request.GET.get('start_date', '')
    end_date = request.GET.get('end_date', '')
    
    # 获取回款记录
    payment_records = PaymentRecord.objects.select_related(
        'created_by', 'confirmed_by'
    ).order_by('-payment_date', '-created_time')
    
    # 应用筛选
    if search:
        payment_records = payment_records.filter(
            Q(payment_number__icontains=search) |
            Q(invoice_number__icontains=search)
        )
    
    if status_filter:
        payment_records = payment_records.filter(status=status_filter)
    
    if start_date:
        try:
            from datetime import datetime
            start_date_obj = datetime.strptime(start_date, '%Y-%m-%d').date()
            payment_records = payment_records.filter(payment_date__gte=start_date_obj)
        except ValueError:
            pass
    
    if end_date:
        try:
            from datetime import datetime
            end_date_obj = datetime.strptime(end_date, '%Y-%m-%d').date()
            payment_records = payment_records.filter(payment_date__lte=end_date_obj)
        except ValueError:
            pass
    
    # 分页
    page_size = request.GET.get('page_size', '10')
    try:
        per_page = int(page_size)
        if per_page not in [10, 20, 50]:
            per_page = 10
    except (ValueError, TypeError):
        per_page = 10
    paginator = Paginator(payment_records, per_page)
    page_number = request.GET.get('page', 1)
    page_obj = paginator.get_page(page_number)
    
    # 统计信息
    total_records = payment_records.count()
    total_amount = payment_records.filter(status='confirmed').aggregate(
        total=Sum('payment_amount')
    )['total'] or Decimal('0')
    
    summary_cards = []
    
    context = _context(
        "回款记录管理",
        "💰",
        "管理所有实际回款记录",
        summary_cards=summary_cards,
        request=request,
    )
    context.update({
        'page_obj': page_obj,
        'search': search,
        'status_filter': status_filter,
        'start_date': start_date,
        'end_date': end_date,
        'status_choices': PaymentRecord._meta.get_field('status').choices,
        'payment_method_choices': PaymentRecord.PAYMENT_METHOD_CHOICES,
    })
    return render(request, "settlement_center/payment_record_list.html", context)


@login_required
def payment_record_detail(request, record_id):
    """回款记录详情页面"""
    permission_codes = get_user_permission_codes(request.user)
    
    record = get_object_or_404(PaymentRecord, id=record_id)
    plan = record.get_payment_plan()
    
    context = _context(
        f"回款记录详情 - {record.payment_number}",
        "💰",
        f"回款金额：¥{record.payment_amount:,.2f}",
        request=request,
        active_menu_id='payment_record_list',
    )
    context.update({
        'record': record,
        'plan': plan,
        'payment_method_choices': PaymentRecord.PAYMENT_METHOD_CHOICES,
    })
    return render(request, "settlement_center/payment_record_detail.html", context)


@login_required
def payment_record_create(request, plan_type, plan_id):
    """创建回款记录"""
    permission_codes = get_user_permission_codes(request.user)
    
    if not _permission_granted('payment_management.payment_record.create', permission_codes):
        messages.error(request, '您没有权限创建回款记录')
        return redirect('settlement_pages:payment_plan_list')
    
    # 获取回款计划
    if plan_type == 'project':
        # 项目回款计划已不存在，返回错误
        messages.error(request, '项目回款计划功能已移除，请使用商务回款计划')
        return redirect('settlement_pages:payment_plan_list')
    elif plan_type == 'business':
        from backend.apps.production_management.models import BusinessPaymentPlan
        plan = get_object_or_404(BusinessPaymentPlan, id=plan_id)
    else:
        messages.error(request, '无效的回款计划类型')
        return redirect('settlement_pages:payment_plan_list')
    
    if request.method == 'POST':
        try:
            payment_amount = Decimal(request.POST.get('payment_amount', '0'))
            payment_date = request.POST.get('payment_date')
            payment_method = request.POST.get('payment_method', 'bank_transfer')
            invoice_number = request.POST.get('invoice_number', '')
            bank_account = request.POST.get('bank_account', '')
            notes = request.POST.get('notes', '')
            
            if not payment_date:
                messages.error(request, '请填写回款日期')
            elif payment_amount <= 0:
                messages.error(request, '回款金额必须大于0')
            else:
                payment_record = PaymentRecord.objects.create(
                    payment_plan_id=plan_id,
                    payment_plan_type=plan_type,
                    payment_amount=payment_amount,
                    payment_date=payment_date,
                    payment_method=payment_method,
                    invoice_number=invoice_number,
                    bank_account=bank_account,
                    notes=notes,
                    created_by=request.user,
                )
                messages.success(request, f'回款记录 {payment_record.payment_number} 创建成功')
                return redirect('settlement_pages:payment_plan_detail', plan_type=plan_type, plan_id=plan_id)
        except Exception as e:
            import logging
            logger = logging.getLogger(__name__)
            logger.exception('创建回款记录失败: %s', str(e))
            messages.error(request, f'创建回款记录失败：{str(e)}')
    
    context = _context(
        "创建回款记录",
        "💰",
        f"回款计划：{plan.phase_name}",
        request=request,
    )
    context.update({
        'plan': plan,
        'plan_type': plan_type,
        'payment_method_choices': PaymentRecord.PAYMENT_METHOD_CHOICES,
    })
    return render(request, "settlement_center/payment_record_form.html", context)


@login_required
def payment_record_create_standalone(request):
    """新建回款记录（独立页面，可选择回款计划）"""
    permission_codes = get_user_permission_codes(request.user)
    
    if not _permission_granted('settlement_center.view_payment', permission_codes):
        messages.error(request, '您没有权限创建回款记录')
        return redirect('settlement_pages:payment_record_list')
    
    # 获取所有可用的商务回款计划
    from backend.apps.production_management.models import BusinessPaymentPlan
    payment_plans = BusinessPaymentPlan.objects.select_related(
        'contract', 'contract__client'
    ).filter(
        status__in=['pending', 'partial']
    ).order_by('-planned_date', '-created_time')
    
    if request.method == 'POST':
        try:
            plan_id = request.POST.get('payment_plan_id')
            if not plan_id:
                messages.error(request, '请选择回款计划')
            else:
                plan = get_object_or_404(BusinessPaymentPlan, id=plan_id)
                payment_amount = Decimal(request.POST.get('payment_amount', '0'))
                payment_date = request.POST.get('payment_date')
                payment_method = request.POST.get('payment_method', 'bank_transfer')
                invoice_number = request.POST.get('invoice_number', '')
                bank_account = request.POST.get('bank_account', '')
                notes = request.POST.get('notes', '')
                
                if not payment_date:
                    messages.error(request, '请填写回款日期')
                elif payment_amount <= 0:
                    messages.error(request, '回款金额必须大于0')
                else:
                    payment_record = PaymentRecord.objects.create(
                        payment_plan_id=plan_id,
                        payment_plan_type='business',
                        payment_amount=payment_amount,
                        payment_date=payment_date,
                        payment_method=payment_method,
                        invoice_number=invoice_number,
                        bank_account=bank_account,
                        notes=notes,
                        created_by=request.user,
                    )
                    messages.success(request, f'回款记录 {payment_record.payment_number} 创建成功')
                    return redirect('settlement_pages:payment_record_list')
        except Exception as e:
            import logging
            logger = logging.getLogger(__name__)
            logger.exception('创建回款记录失败: %s', str(e))
            messages.error(request, f'创建回款记录失败：{str(e)}')
    
    context = _context(
        "新建回款记录",
        "➕",
        "创建新的回款记录",
        request=request,
        active_menu_id='payment_record_create_standalone',
    )
    context.update({
        'payment_plans': payment_plans,
        'payment_method_choices': PaymentRecord.PAYMENT_METHOD_CHOICES,
    })
    return render(request, "settlement_center/payment_record_create_standalone.html", context)


@login_required
def payment_record_confirm(request, record_id):
    """确认回款记录"""
    permission_codes = get_user_permission_codes(request.user)
    
    record = get_object_or_404(PaymentRecord, id=record_id)
    
    # 权限检查：只有待确认状态的记录才能确认
    if record.status != 'pending':
        messages.error(request, f'该回款记录状态为"{record.get_status_display()}"，无法确认')
        return redirect('settlement_pages:payment_record_list')
    
    if request.method == 'POST':
        try:
            record.status = 'confirmed'
            record.confirmed_by = request.user
            record.confirmed_time = timezone.now()
            record.save(update_fields=['status', 'confirmed_by', 'confirmed_time', 'updated_time'])
            
            # 更新关联的回款计划的实际金额和状态
            plan = record.get_payment_plan()
            if plan:
                # 计算该计划的所有已确认回款记录的总金额
                confirmed_records = PaymentRecord.objects.filter(
                    payment_plan_type=record.payment_plan_type,
                    payment_plan_id=record.payment_plan_id,
                    status='confirmed'
                )
                total_actual = confirmed_records.aggregate(
                    total=Sum('payment_amount')
                )['total'] or Decimal('0')
                
                plan.actual_amount = total_actual
                plan.actual_date = record.payment_date
                
                # 更新计划状态
                if total_actual >= plan.planned_amount:
                    plan.status = 'completed'
                elif total_actual > 0:
                    plan.status = 'partial'
                else:
                    plan.status = 'pending'
                
                plan.save(update_fields=['actual_amount', 'actual_date', 'status', 'updated_time'])
            
            messages.success(request, f'回款记录 {record.payment_number} 已确认')
            return redirect('settlement_pages:payment_record_list')
        except Exception as e:
            import logging
            logger = logging.getLogger(__name__)
            logger.exception('确认回款记录失败: %s', str(e))
            messages.error(request, f'确认回款记录失败：{str(e)}')
    
    context = _context(
        "确认回款记录",
        "✅",
        f"确认回款记录：{record.payment_number}",
        request=request,
        active_menu_id='payment_record_list',
    )
    context.update({
        'record': record,
        'plan': record.get_payment_plan(),
        'payment_method_choices': PaymentRecord.PAYMENT_METHOD_CHOICES,
    })
    return render(request, "settlement_center/payment_record_confirm.html", context)


@login_required
def payment_record_edit(request, record_id):
    """编辑回款记录"""
    permission_codes = get_user_permission_codes(request.user)
    
    record = get_object_or_404(PaymentRecord, id=record_id)
    
    # 权限检查
    if not _permission_granted('settlement_center.view_payment', permission_codes):
        messages.error(request, '您没有权限编辑回款记录')
        return redirect('settlement_pages:payment_record_list')
    
    # 状态检查：已确认的记录不能编辑
    if record.status == 'confirmed':
        messages.error(request, '已确认的回款记录不能编辑')
        return redirect('settlement_pages:payment_record_detail', record_id=record_id)
    
    plan = record.get_payment_plan()
    
    if request.method == 'POST':
        try:
            payment_amount = Decimal(request.POST.get('payment_amount', '0'))
            payment_date = request.POST.get('payment_date')
            payment_method = request.POST.get('payment_method', 'bank_transfer')
            invoice_number = request.POST.get('invoice_number', '')
            bank_account = request.POST.get('bank_account', '')
            notes = request.POST.get('notes', '')
            
            if not payment_date:
                messages.error(request, '请填写回款日期')
            elif payment_amount <= 0:
                messages.error(request, '回款金额必须大于0')
            else:
                record.payment_amount = payment_amount
                record.payment_date = payment_date
                record.payment_method = payment_method
                record.invoice_number = invoice_number
                record.bank_account = bank_account
                record.notes = notes
                record.save()
                
                messages.success(request, f'回款记录 {record.payment_number} 更新成功')
                return redirect('settlement_pages:payment_record_detail', record_id=record_id)
        except Exception as e:
            import logging
            logger = logging.getLogger(__name__)
            logger.exception('更新回款记录失败: %s', str(e))
            messages.error(request, f'更新回款记录失败：{str(e)}')
    
    context = _context(
        "编辑回款记录",
        "✏️",
        f"编辑回款记录：{record.payment_number}",
        request=request,
        active_menu_id='payment_record_list',
    )
    context.update({
        'record': record,
        'plan': plan,
        'payment_method_choices': PaymentRecord.PAYMENT_METHOD_CHOICES,
    })
    return render(request, "settlement_center/payment_record_edit.html", context)


@login_required
def payment_record_delete(request, record_id):
    """删除回款记录"""
    permission_codes = get_user_permission_codes(request.user)
    
    record = get_object_or_404(PaymentRecord, id=record_id)
    
    # 权限检查
    if not _permission_granted('settlement_center.view_payment', permission_codes):
        messages.error(request, '您没有权限删除回款记录')
        return redirect('settlement_pages:payment_record_list')
    
    # 状态检查：已确认的记录不能删除
    if record.status == 'confirmed':
        messages.error(request, '已确认的回款记录不能删除')
        return redirect('settlement_pages:payment_record_detail', record_id=record_id)
    
    if request.method == 'POST':
        try:
            record_number = record.payment_number
            plan = record.get_payment_plan()
            record.delete()
            
            # 如果有关联的回款计划，更新计划的实际金额
            if plan:
                confirmed_records = PaymentRecord.objects.filter(
                    payment_plan_type=record.payment_plan_type,
                    payment_plan_id=record.payment_plan_id,
                    status='confirmed'
                )
                total_actual = confirmed_records.aggregate(
                    total=Sum('payment_amount')
                )['total'] or Decimal('0')
                
                plan.actual_amount = total_actual
                
                # 更新计划状态
                if total_actual >= plan.planned_amount:
                    plan.status = 'completed'
                elif total_actual > 0:
                    plan.status = 'partial'
                else:
                    plan.status = 'pending'
                
                plan.save(update_fields=['actual_amount', 'status', 'updated_time'])
            
            messages.success(request, f'回款记录 {record_number} 已删除')
            return redirect('settlement_pages:payment_record_list')
        except Exception as e:
            import logging
            logger = logging.getLogger(__name__)
            logger.exception('删除回款记录失败: %s', str(e))
            messages.error(request, f'删除回款记录失败：{str(e)}')
    
    context = _context(
        "删除回款记录",
        "🗑️",
        f"确认删除回款记录：{record.payment_number}",
        request=request,
        active_menu_id='payment_record_list',
    )
    context.update({
        'record': record,
        'plan': record.get_payment_plan(),
    })
    return render(request, "settlement_center/payment_record_delete_confirm.html", context)


@login_required
def payment_record_export(request):
    """导出回款记录"""
    from django.http import HttpResponse
    import csv
    
    permission_codes = get_user_permission_codes(request.user)
    
    # 权限检查
    if not _permission_granted('settlement_center.view_payment', permission_codes):
        messages.error(request, '您没有权限导出回款记录')
        return redirect('settlement_pages:payment_record_list')
    
    # 获取筛选条件（与列表页面相同）
    search = request.GET.get('search', '')
    status_filter = request.GET.get('status', '')
    start_date = request.GET.get('start_date', '')
    end_date = request.GET.get('end_date', '')
    
    records = PaymentRecord.objects.select_related(
        'created_by', 'confirmed_by'
    ).order_by('-payment_date', '-created_time')
    
    # 应用筛选
    if search:
        records = records.filter(
            Q(payment_number__icontains=search) |
            Q(invoice_number__icontains=search)
        )
    
    if status_filter:
        records = records.filter(status=status_filter)
    
    if start_date:
        try:
            from datetime import datetime
            start_date_obj = datetime.strptime(start_date, '%Y-%m-%d').date()
            records = records.filter(payment_date__gte=start_date_obj)
        except ValueError:
            pass
    
    if end_date:
        try:
            from datetime import datetime
            end_date_obj = datetime.strptime(end_date, '%Y-%m-%d').date()
            records = records.filter(payment_date__lte=end_date_obj)
        except ValueError:
            pass
    
    # 创建CSV响应
    response = HttpResponse(content_type='text/csv; charset=utf-8-sig')
    response['Content-Disposition'] = f'attachment; filename="回款记录_{timezone.now().strftime("%Y%m%d_%H%M%S")}.csv"'
    
    writer = csv.writer(response)
    
    # 写入表头
    headers = ['回款单号', '回款金额', '回款日期', '回款方式', '发票号码', '收款账户', 
               '状态', '创建人', '创建时间', '确认人', '确认时间', '备注']
    writer.writerow(headers)
    
    # 写入数据
    for record in records:
        plan = record.get_payment_plan()
        writer.writerow([
            record.payment_number,
            f'{record.payment_amount:,.2f}',
            record.payment_date.strftime('%Y-%m-%d') if record.payment_date else '',
            record.get_payment_method_display(),
            record.invoice_number or '',
            record.bank_account or '',
            record.get_status_display(),
            record.created_by.get_full_name() or record.created_by.username if record.created_by else '',
            record.created_time.strftime('%Y-%m-%d %H:%M:%S') if record.created_time else '',
            record.confirmed_by.get_full_name() or record.confirmed_by.username if record.confirmed_by else '',
            record.confirmed_time.strftime('%Y-%m-%d %H:%M:%S') if record.confirmed_time else '',
            record.notes or '',
        ])
    
    return response


@login_required
def payment_application_list(request):
    """回款申请列表页面"""
    permission_codes = get_user_permission_codes(request.user)
    
    # 权限检查
    if not _permission_granted('settlement_center.view_payment', permission_codes):
        messages.error(request, '您没有权限查看回款申请')
        return redirect('settlement_pages:payment_management_home')
    
    # 获取筛选参数
    search = request.GET.get('search', '')
    status_filter = request.GET.get('status', '')
    start_date = request.GET.get('start_date', '')
    end_date = request.GET.get('end_date', '')
    
    # 获取回款申请
    applications = PaymentApplication.objects.select_related(
        'contract', 'contract__client', 'created_by', 'submitted_by', 'approver'
    ).order_by('-application_date', '-created_time')
    
    # 应用筛选
    if search:
        applications = applications.filter(
            Q(application_number__icontains=search) |
            Q(contract__contract_number__icontains=search) |
            Q(contract__client__name__icontains=search)
        )
    
    if status_filter:
        applications = applications.filter(status=status_filter)
    
    if start_date:
        try:
            from datetime import datetime
            start_date_obj = datetime.strptime(start_date, '%Y-%m-%d').date()
            applications = applications.filter(application_date__gte=start_date_obj)
        except ValueError:
            pass
    
    if end_date:
        try:
            from datetime import datetime
            end_date_obj = datetime.strptime(end_date, '%Y-%m-%d').date()
            applications = applications.filter(application_date__lte=end_date_obj)
        except ValueError:
            pass
    
    # 分页
    page_size = request.GET.get('page_size', '10')
    try:
        per_page = int(page_size)
        if per_page not in [10, 20, 50]:
            per_page = 10
    except (ValueError, TypeError):
        per_page = 10
    
    paginator = Paginator(applications, per_page)
    page_number = request.GET.get('page', 1)
    page_obj = paginator.get_page(page_number)
    
    # 统计信息
    total_applications = PaymentApplication.objects.count()
    pending_applications = PaymentApplication.objects.filter(status='pending').count()
    approved_applications = PaymentApplication.objects.filter(status='approved').count()
    
    summary_cards = [
        {
            'label': '总申请数',
            'icon': '📋',
            'value': str(total_applications),
        },
        {
            'label': '待审核',
            'icon': '⏳',
            'value': str(pending_applications),
        },
        {
            'label': '已通过',
            'icon': '✅',
            'value': str(approved_applications),
        },
    ]
    
    context = _context(
        "回款申请列表",
        "📄",
        "查看和管理所有回款申请",
        summary_cards=summary_cards,
        request=request,
        active_menu_id='payment_application_list',
    )
    context.update({
        'page_obj': page_obj,
        'search': search,
        'status_filter': status_filter,
        'start_date': start_date,
        'end_date': end_date,
        'status_choices': PaymentApplication.STATUS_CHOICES,
    })
    return render(request, "settlement_center/payment_application_list.html", context)


@login_required
def payment_application_create(request):
    """新建回款申请页面"""
    permission_codes = get_user_permission_codes(request.user)
    
    # 权限检查
    if not _permission_granted('settlement_center.view_payment', permission_codes):
        messages.error(request, '您没有权限创建回款申请')
        return redirect('settlement_pages:payment_management_home')
    
    if request.method == 'POST':
        try:
            contract_id = request.POST.get('contract_id')
            application_amount = request.POST.get('application_amount', '0')
            application_date = request.POST.get('application_date')
            expected_date = request.POST.get('expected_date', '') or None
            reason = request.POST.get('reason', '').strip()
            notes = request.POST.get('notes', '').strip()
            submit = request.POST.get('submit', '') == 'submit'  # 是否直接提交审核
            
            if not contract_id:
                messages.error(request, '请选择合同')
            elif not application_amount or Decimal(application_amount) <= 0:
                messages.error(request, '请填写有效的申请金额')
            elif not application_date:
                messages.error(request, '请选择申请日期')
            elif not reason:
                messages.error(request, '请填写申请原因')
            else:
                from backend.apps.production_management.models import BusinessContract
                contract = get_object_or_404(BusinessContract, id=contract_id)
                
                application = PaymentApplication.objects.create(
                    contract=contract,
                    application_amount=Decimal(application_amount),
                    application_date=application_date,
                    expected_date=expected_date,
                    reason=reason,
                    notes=notes,
                    created_by=request.user,
                    status='pending' if submit else 'draft',
                )
                
                if submit:
                    application.submitted_by = request.user
                    application.submitted_time = timezone.now()
                    application.save()
                    messages.success(request, f'回款申请 {application.application_number} 已提交审核')
                else:
                    messages.success(request, f'回款申请 {application.application_number} 已保存为草稿')
                
                return redirect('settlement_pages:payment_application_list')
        except Exception as e:
            import logging
            logger = logging.getLogger(__name__)
            logger.exception('创建回款申请失败: %s', str(e))
            messages.error(request, f'创建回款申请失败：{str(e)}')
    
    # 获取合同列表（用于选择）
    contracts = []
    try:
        from backend.apps.production_management.models import BusinessContract
        contracts = BusinessContract.objects.select_related('client').filter(
            status__in=['signed', 'executing']
        ).order_by('-signed_date')[:100]
    except Exception:
        pass
    
    context = _context(
        "新建回款申请",
        "➕",
        "创建新的回款申请",
        request=request,
        active_menu_id='payment_application_create',
    )
    context.update({
        'contracts': contracts,
    })
    return render(request, "settlement_center/payment_application_form.html", context)


@login_required
def payment_application_detail(request, application_id):
    """回款申请详情页面"""
    permission_codes = get_user_permission_codes(request.user)
    
    application = get_object_or_404(PaymentApplication, id=application_id)
    
    context = _context(
        f"回款申请详情 - {application.application_number}",
        "📄",
        f"申请金额：¥{application.application_amount:,.2f}",
        request=request,
        active_menu_id='payment_application_list',
    )
    context.update({
        'application': application,
        'can_submit': application.status == 'draft' and application.created_by == request.user,
        'can_review': application.status == 'pending',
    })
    return render(request, "settlement_center/payment_application_detail.html", context)


@login_required
def payment_application_review(request, application_id):
    """审核回款申请"""
    permission_codes = get_user_permission_codes(request.user)
    
    application = get_object_or_404(PaymentApplication, id=application_id)
    
    # 权限检查
    if not _permission_granted('settlement_center.view_payment', permission_codes):
        messages.error(request, '您没有权限审核回款申请')
        return redirect('settlement_pages:payment_application_list')
    
    # 状态检查
    if application.status != 'pending':
        messages.error(request, f'该回款申请状态为"{application.get_status_display()}"，无法审核')
        return redirect('settlement_pages:payment_application_detail', application_id=application_id)
    
    if request.method == 'POST':
        try:
            action = request.POST.get('action')  # 'approve' 或 'reject'
            review_comment = request.POST.get('review_comment', '').strip()
            rejection_reason = request.POST.get('rejection_reason', '').strip()
            
            if action == 'approve':
                application.status = 'approved'
                application.approver = request.user
                application.approved_time = timezone.now()
                application.review_comment = review_comment
                application.save()
                messages.success(request, f'回款申请 {application.application_number} 已通过审核')
            elif action == 'reject':
                if not rejection_reason:
                    messages.error(request, '请填写拒绝原因')
                else:
                    application.status = 'rejected'
                    application.approver = request.user
                    application.approved_time = timezone.now()
                    application.rejection_reason = rejection_reason
                    application.review_comment = review_comment
                    application.save()
                    messages.success(request, f'回款申请 {application.application_number} 已拒绝')
            else:
                messages.error(request, '无效的操作')
                return redirect('settlement_pages:payment_application_review', application_id=application_id)
            
            return redirect('settlement_pages:payment_application_detail', application_id=application_id)
        except Exception as e:
            import logging
            logger = logging.getLogger(__name__)
            logger.exception('审核回款申请失败: %s', str(e))
            messages.error(request, f'审核回款申请失败：{str(e)}')
    
    context = _context(
        "审核回款申请",
        "✅",
        f"审核回款申请：{application.application_number}",
        request=request,
        active_menu_id='payment_application_list',
    )
    context.update({
        'application': application,
    })
    return render(request, "settlement_center/payment_application_review.html", context)


@login_required
def payment_application_submit(request, application_id):
    """提交回款申请（从草稿状态提交审核）"""
    permission_codes = get_user_permission_codes(request.user)
    
    application = get_object_or_404(PaymentApplication, id=application_id)
    
    # 权限检查：只有创建人可以提交
    if application.created_by != request.user:
        messages.error(request, '您只能提交自己创建的回款申请')
        return redirect('settlement_pages:payment_application_detail', application_id=application_id)
    
    # 状态检查
    if application.status != 'draft':
        messages.error(request, f'该回款申请状态为"{application.get_status_display()}"，无法提交')
        return redirect('settlement_pages:payment_application_detail', application_id=application_id)
    
    if request.method == 'POST':
        try:
            application.status = 'pending'
            application.submitted_by = request.user
            application.submitted_time = timezone.now()
            application.save()
            messages.success(request, f'回款申请 {application.application_number} 已提交审核')
            return redirect('settlement_pages:payment_application_detail', application_id=application_id)
        except Exception as e:
            import logging
            logger = logging.getLogger(__name__)
            logger.exception('提交回款申请失败: %s', str(e))
            messages.error(request, f'提交回款申请失败：{str(e)}')
    
    return redirect('settlement_pages:payment_application_detail', application_id=application_id)

# ==================== 产值阶段管理 ====================

@login_required
def output_value_stage_list(request):
    """产值阶段列表"""
    from backend.apps.system_management.services import user_has_permission
    has_permission = user_has_permission(request.user, 'settlement_center.manage_output')
    if not has_permission:
        raise PermissionDenied("您没有权限管理产值阶段。")
    
    stages = OutputValueStage.objects.all().order_by('order', 'created_time')
    
    permission_codes = get_user_permission_codes(request.user)
    context = _context(
        "产值阶段管理",
        "📊",
        "管理产值计算阶段配置",
        request=request,
        active_menu_id='output_value_template_manage',
    )
    context['stages'] = stages
    context['module_sidebar_nav'] = _build_output_value_sidebar_nav(
        permission_codes,
        request_path=request.path,
        active_id='output_value_template_manage'
    )
    return render(request, "settlement_center/output_value_stage_list.html", context)


@login_required
def output_value_stage_create(request):
    """创建产值阶段"""
    from backend.apps.system_management.services import user_has_permission
    has_permission = user_has_permission(request.user, 'settlement_center.manage_output')
    if not has_permission:
        raise PermissionDenied("您没有权限创建产值阶段。")
    
    if request.method == 'POST':
        try:
            stage = OutputValueStage.objects.create(
                name=request.POST.get('name'),
                code=request.POST.get('code'),
                stage_type=request.POST.get('stage_type'),
                stage_percentage=Decimal(request.POST.get('stage_percentage', '0')),
                base_amount_type=request.POST.get('base_amount_type'),
                description=request.POST.get('description', ''),
                order=int(request.POST.get('order', 0)),
                is_active=request.POST.get('is_active') == 'on',
            )
            messages.success(request, f'产值阶段 "{stage.name}" 创建成功')
            return redirect('settlement_pages:output_value_stage_list')
        except Exception as e:
            messages.error(request, f'创建失败：{str(e)}')
    
    permission_codes = get_user_permission_codes(request.user)
    context = _context(
        "创建产值阶段",
        "➕",
        "创建新的产值计算阶段",
        request=request,
        active_menu_id='output_value_template_manage',
    )
    context['stage_types'] = OutputValueStage.STAGE_TYPE_CHOICES
    context['base_amount_types'] = OutputValueStage.BASE_AMOUNT_CHOICES
    context['module_sidebar_nav'] = _build_output_value_sidebar_nav(
        permission_codes,
        request_path=request.path,
        active_id='output_value_template_manage'
    )
    return render(request, "settlement_center/output_value_stage_form.html", context)


@login_required
def output_value_stage_edit(request, stage_id):
    """编辑产值阶段"""
    from backend.apps.system_management.services import user_has_permission
    has_permission = user_has_permission(request.user, 'settlement_center.manage_output')
    if not has_permission:
        raise PermissionDenied("您没有权限编辑产值阶段。")
    
    stage = get_object_or_404(OutputValueStage, id=stage_id)
    
    if request.method == 'POST':
        try:
            stage.name = request.POST.get('name')
            stage.code = request.POST.get('code')
            stage.stage_type = request.POST.get('stage_type')
            stage.stage_percentage = Decimal(request.POST.get('stage_percentage', '0'))
            stage.base_amount_type = request.POST.get('base_amount_type')
            stage.description = request.POST.get('description', '')
            stage.order = int(request.POST.get('order', 0))
            stage.is_active = request.POST.get('is_active') == 'on'
            stage.save()
            messages.success(request, f'产值阶段 "{stage.name}" 更新成功')
            return redirect('settlement_pages:output_value_stage_list')
        except Exception as e:
            messages.error(request, f'更新失败：{str(e)}')
    
    permission_codes = get_user_permission_codes(request.user)
    context = _context(
        "编辑产值阶段",
        "✏️",
        f"编辑产值阶段：{stage.name}",
        request=request,
        active_menu_id='output_value_template_manage',
    )
    context['stage'] = stage
    context['stage_types'] = OutputValueStage.STAGE_TYPE_CHOICES
    context['base_amount_types'] = OutputValueStage.BASE_AMOUNT_CHOICES
    context['module_sidebar_nav'] = _build_output_value_sidebar_nav(
        permission_codes,
        request_path=request.path,
        active_id='output_value_template_manage'
    )
    return render(request, "settlement_center/output_value_stage_form.html", context)


@login_required
def output_value_stage_delete(request, stage_id):
    """删除产值阶段"""
    from backend.apps.system_management.services import user_has_permission
    has_permission = user_has_permission(request.user, 'settlement_center.manage_output')
    if not has_permission:
        raise PermissionDenied("您没有权限删除产值阶段。")
    
    stage = get_object_or_404(OutputValueStage, id=stage_id)
    
    if request.method == 'POST':
        try:
            stage_name = stage.name
            stage.delete()
            messages.success(request, f'产值阶段 "{stage_name}" 已删除')
        except Exception as e:
            messages.error(request, f'删除失败：{str(e)}')
    
    return redirect('settlement_pages:output_value_stage_list')

# ==================== 产值里程碑管理 ====================

@login_required
def output_value_milestone_list(request):
    """产值里程碑列表"""
    from backend.apps.system_management.services import user_has_permission
    has_permission = user_has_permission(request.user, 'settlement_center.manage_output')
    if not has_permission:
        raise PermissionDenied("您没有权限管理产值里程碑。")
    
    milestones = OutputValueMilestone.objects.select_related('stage').all().order_by('stage__order', 'order', 'created_time')
    
    permission_codes = get_user_permission_codes(request.user)
    context = _context(
        "产值里程碑管理",
        "🎯",
        "管理产值计算里程碑配置",
        request=request,
        active_menu_id='output_value_template_manage',
    )
    context['milestones'] = milestones
    context['module_sidebar_nav'] = _build_output_value_sidebar_nav(
        permission_codes,
        request_path=request.path,
        active_id='output_value_template_manage'
    )
    return render(request, "settlement_center/output_value_milestone_list.html", context)


@login_required
def output_value_milestone_create(request):
    """创建产值里程碑"""
    from backend.apps.system_management.services import user_has_permission
    has_permission = user_has_permission(request.user, 'settlement_center.manage_output')
    if not has_permission:
        raise PermissionDenied("您没有权限创建产值里程碑。")
    
    if request.method == 'POST':
        try:
            milestone = OutputValueMilestone.objects.create(
                stage_id=int(request.POST.get('stage')),
                name=request.POST.get('name'),
                code=request.POST.get('code'),
                milestone_percentage=Decimal(request.POST.get('milestone_percentage', '0')),
                description=request.POST.get('description', ''),
                order=int(request.POST.get('order', 0)),
                is_active=request.POST.get('is_active') == 'on',
            )
            messages.success(request, f'产值里程碑 "{milestone.name}" 创建成功')
            return redirect('settlement_pages:output_value_milestone_list')
        except Exception as e:
            messages.error(request, f'创建失败：{str(e)}')
    
    permission_codes = get_user_permission_codes(request.user)
    context = _context(
        "创建产值里程碑",
        "➕",
        "创建新的产值计算里程碑",
        request=request,
        active_menu_id='output_value_template_manage',
    )
    context['stages'] = OutputValueStage.objects.filter(is_active=True).order_by('order')
    context['module_sidebar_nav'] = _build_output_value_sidebar_nav(
        permission_codes,
        request_path=request.path,
        active_id='output_value_template_manage'
    )
    return render(request, "settlement_center/output_value_milestone_form.html", context)


@login_required
def output_value_milestone_edit(request, milestone_id):
    """编辑产值里程碑"""
    from backend.apps.system_management.services import user_has_permission
    has_permission = user_has_permission(request.user, 'settlement_center.manage_output')
    if not has_permission:
        raise PermissionDenied("您没有权限编辑产值里程碑。")
    
    milestone = get_object_or_404(OutputValueMilestone, id=milestone_id)
    
    if request.method == 'POST':
        try:
            milestone.stage_id = int(request.POST.get('stage'))
            milestone.name = request.POST.get('name')
            milestone.code = request.POST.get('code')
            milestone.milestone_percentage = Decimal(request.POST.get('milestone_percentage', '0'))
            milestone.description = request.POST.get('description', '')
            milestone.order = int(request.POST.get('order', 0))
            milestone.is_active = request.POST.get('is_active') == 'on'
            milestone.save()
            messages.success(request, f'产值里程碑 "{milestone.name}" 更新成功')
            return redirect('settlement_pages:output_value_milestone_list')
        except Exception as e:
            messages.error(request, f'更新失败：{str(e)}')
    
    permission_codes = get_user_permission_codes(request.user)
    context = _context(
        "编辑产值里程碑",
        "✏️",
        f"编辑产值里程碑：{milestone.name}",
        request=request,
        active_menu_id='output_value_template_manage',
    )
    context['milestone'] = milestone
    context['stages'] = OutputValueStage.objects.filter(is_active=True).order_by('order')
    context['module_sidebar_nav'] = _build_output_value_sidebar_nav(
        permission_codes,
        request_path=request.path,
        active_id='output_value_template_manage'
    )
    return render(request, "settlement_center/output_value_milestone_form.html", context)


@login_required
def output_value_milestone_delete(request, milestone_id):
    """删除产值里程碑"""
    from backend.apps.system_management.services import user_has_permission
    has_permission = user_has_permission(request.user, 'settlement_center.manage_output')
    if not has_permission:
        raise PermissionDenied("您没有权限删除产值里程碑。")
    
    milestone = get_object_or_404(OutputValueMilestone, id=milestone_id)
    
    if request.method == 'POST':
        try:
            milestone_name = milestone.name
            milestone.delete()
            messages.success(request, f'产值里程碑 "{milestone_name}" 已删除')
        except Exception as e:
            messages.error(request, f'删除失败：{str(e)}')
    
    return redirect('settlement_pages:output_value_milestone_list')


# ==================== 产值事件管理 ====================

@login_required
def output_value_event_list(request):
    """产值事件列表"""
    from backend.apps.system_management.services import user_has_permission
    has_permission = user_has_permission(request.user, 'settlement_center.manage_output')
    if not has_permission:
        raise PermissionDenied("您没有权限管理产值事件。")
    
    events = OutputValueEvent.objects.select_related('milestone__stage').all().order_by('milestone__stage__order', 'milestone__order', 'order', 'created_time')
    
    permission_codes = get_user_permission_codes(request.user)
    context = _context(
        "产值事件管理",
        "⚡",
        "管理产值计算事件配置",
        request=request,
        active_menu_id='output_value_template_manage',
    )
    context['events'] = events
    context['module_sidebar_nav'] = _build_output_value_sidebar_nav(
        permission_codes,
        request_path=request.path,
        active_id='output_value_template_manage'
    )
    return render(request, "settlement_center/output_value_event_list.html", context)


@login_required
def output_value_event_create(request):
    """创建产值事件"""
    from backend.apps.system_management.services import user_has_permission
    has_permission = user_has_permission(request.user, 'settlement_center.manage_output')
    if not has_permission:
        raise PermissionDenied("您没有权限创建产值事件。")
    
    if request.method == 'POST':
        try:
            event = OutputValueEvent.objects.create(
                milestone_id=int(request.POST.get('milestone')),
                name=request.POST.get('name'),
                code=request.POST.get('code'),
                event_percentage=Decimal(request.POST.get('event_percentage', '0')),
                responsible_role_code=request.POST.get('responsible_role_code', ''),
                description=request.POST.get('description', ''),
                trigger_condition=request.POST.get('trigger_condition', ''),
                order=int(request.POST.get('order', 0)),
                is_active=request.POST.get('is_active') == 'on',
            )
            messages.success(request, f'产值事件 "{event.name}" 创建成功')
            return redirect('settlement_pages:output_value_event_list')
        except Exception as e:
            messages.error(request, f'创建失败：{str(e)}')
    
    permission_codes = get_user_permission_codes(request.user)
    context = _context(
        "创建产值事件",
        "➕",
        "创建新的产值计算事件",
        request=request,
        active_menu_id='output_value_template_manage',
    )
    context['milestones'] = OutputValueMilestone.objects.filter(is_active=True).select_related('stage').order_by('stage__order', 'order')
    context['module_sidebar_nav'] = _build_output_value_sidebar_nav(
        permission_codes,
        request_path=request.path,
        active_id='output_value_template_manage'
    )
    return render(request, "settlement_center/output_value_event_form.html", context)


@login_required
def output_value_event_edit(request, event_id):
    """编辑产值事件"""
    from backend.apps.system_management.services import user_has_permission
    has_permission = user_has_permission(request.user, 'settlement_center.manage_output')
    if not has_permission:
        raise PermissionDenied("您没有权限编辑产值事件。")
    
    event = get_object_or_404(OutputValueEvent, id=event_id)
    
    if request.method == 'POST':
        try:
            event.milestone_id = int(request.POST.get('milestone'))
            event.name = request.POST.get('name')
            event.code = request.POST.get('code')
            event.event_percentage = Decimal(request.POST.get('event_percentage', '0'))
            event.responsible_role_code = request.POST.get('responsible_role_code', '')
            event.description = request.POST.get('description', '')
            event.trigger_condition = request.POST.get('trigger_condition', '')
            event.order = int(request.POST.get('order', 0))
            event.is_active = request.POST.get('is_active') == 'on'
            event.save()
            messages.success(request, f'产值事件 "{event.name}" 更新成功')
            return redirect('settlement_pages:output_value_event_list')
        except Exception as e:
            messages.error(request, f'更新失败：{str(e)}')
    
    permission_codes = get_user_permission_codes(request.user)
    context = _context(
        "编辑产值事件",
        "✏️",
        f"编辑产值事件：{event.name}",
        request=request,
        active_menu_id='output_value_template_manage',
    )
    context['event'] = event
    context['milestones'] = OutputValueMilestone.objects.filter(is_active=True).select_related('stage').order_by('stage__order', 'order')
    context['module_sidebar_nav'] = _build_output_value_sidebar_nav(
        permission_codes,
        request_path=request.path,
        active_id='output_value_template_manage'
    )
    return render(request, "settlement_center/output_value_event_form.html", context)


@login_required
def output_value_event_delete(request, event_id):
    """删除产值事件"""
    from backend.apps.system_management.services import user_has_permission
    has_permission = user_has_permission(request.user, 'settlement_center.manage_output')
    if not has_permission:
        raise PermissionDenied("您没有权限删除产值事件。")
    
    event = get_object_or_404(OutputValueEvent, id=event_id)
    
    if request.method == 'POST':
        try:
            event_name = event.name
            event.delete()
            messages.success(request, f'产值事件 "{event_name}" 已删除')
        except Exception as e:
            messages.error(request, f'删除失败：{str(e)}')
    
    return redirect('settlement_pages:output_value_event_list')
