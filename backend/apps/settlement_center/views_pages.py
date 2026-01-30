from django.contrib.auth.decorators import login_required
from django.shortcuts import render, get_object_or_404, redirect
from django.contrib import messages
from django.core.exceptions import PermissionDenied
from django.db.models import Q, Sum, Count, F, Avg
from django.utils import timezone
from decimal import Decimal
from datetime import timedelta, datetime

from backend.apps.settlement_center.models import (
    OutputValueStage, OutputValueMilestone, OutputValueEvent, OutputValueRecord
)
# PaymentRecord已迁移到payment_management
from backend.apps.payment_management.models import PaymentRecord
from backend.apps.settlement_management.models import (
    ProjectSettlement, SettlementItem, ServiceFeeRate, ContractSettlement
)
# from backend.apps.production_quality.models import Opinion  # 已删除生产质量模块
from .forms import ProjectSettlementForm, ContractSettlementForm
from .services import get_project_output_value_for_settlement, get_project_output_value_summary
from backend.apps.production_management.models import Project
from backend.apps.system_management.models import User
from backend.apps.system_management.services import get_user_permission_codes
from backend.core.views import _permission_granted, _build_full_top_nav
from backend.apps.contract_management.models import BusinessContract
from django.urls import reverse, NoReverseMatch
from django.core.paginator import Paginator
from django.db.models import Max



# ==================== 回款管理模块左侧菜单结构 =====================
SETTLEMENT_MENU = [
    {
        'id': 'settlement_home',
        'label': '回款管理',
        'icon': '💰',
        'url_name': 'settlement_pages:settlement_home',
        'permission': None,  # 首页不需要特殊权限
        'children': [
            {
                'id': 'settlement_home',
                'label': '首页',
                'icon': '👥',
                'url_name': 'settlement_pages:settlement_home',
                'permission': None,
            },
        ]
    },
    {
        'id': 'payment_plan',
        'label': '回款计划',
        'icon': '💳',
        'url_name': 'settlement_pages:payment_plan_list',
        'permission': 'payment_management.payment_plan.view',
    },
    {
        'id': 'output_value',
        'label': '产值管理',
        'icon': '📊',
        'permission': 'settlement_center.view_output_value',
        'children': [
            {
                'id': 'output_value_template',
                'label': '产值模板',
                'icon': '📋',
                'url_name': 'settlement_pages:output_value_template_manage',
                'permission': 'settlement_center.manage_output',
            },
            {
                'id': 'output_value_record',
                'label': '产值记录',
                'icon': '📝',
                'url_name': 'settlement_pages:output_value_record_list',
                'permission': 'settlement_center.view_output_value',
            },
            {
                'id': 'output_value_statistics',
                'label': '产值统计',
                'icon': '📈',
                'url_name': 'settlement_pages:output_value_statistics',
                'permission': 'settlement_center.view_output_value',
            },
        ]
    },
    {
        'id': 'project_settlement',
        'label': '项目结算',
        'icon': '💰',
        'url_name': 'settlement_pages:project_settlement_list',
        'permission': 'settlement_management.view_settlement',
    },
]


def _build_settlement_sidebar_nav(permission_set, request_path=None, active_id=None):
    """生成回款管理左侧菜单（统一格式）"""
    # 尝试导入统一的构建函数
    try:
        from backend.core.views import _build_unified_sidebar_nav
        return _build_unified_sidebar_nav(SETTLEMENT_MENU, permission_set, active_id=active_id)
    except ImportError:
        # Fallback: 如果 _build_unified_sidebar_nav 不存在，提供简单实现
        nav = []
        for item in SETTLEMENT_MENU:
            if item.get('permission'):
                if not _permission_granted(item['permission'], permission_set):
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


def _context(page_title, page_icon, description, summary_cards=None, sections=None, request=None):
    """统一的页面上下文生成函数"""
    context = {
        "page_title": page_title,
        "page_icon": page_icon,
        "description": description,
        "summary_cards": summary_cards or [],
        "sections": sections or [],
    }
    
    # 添加顶部导航栏和左侧菜单
    if request and request.user.is_authenticated:
        try:
            permission_set = get_user_permission_codes(request.user)
            context['full_top_nav'] = _build_full_top_nav(permission_set, request.user)
            # 添加左侧菜单
            context['sidebar_nav'] = _build_settlement_sidebar_nav(permission_set, request.path)
            context['sidebar_title'] = '结算中心'
            context['sidebar_subtitle'] = 'Settlement Center'
        except Exception as e:
            import logging
            logger = logging.getLogger(__name__)
            logger.exception('构建导航栏失败: %s', str(e))
            context['full_top_nav'] = []
            context['settlement_menu'] = []
            context['settlement_sidebar_nav'] = []
    else:
        context['full_top_nav'] = []
        context['settlement_menu'] = []
        context['settlement_sidebar_nav'] = []
    # 为所有可能的侧边栏变量设置默认值，避免模板错误
    context.setdefault('plan_menu', [])
    context.setdefault('sidebar_nav', [])
    context.setdefault('customer_menu', [])
    context.setdefault('sidebar_nav', [])
    context.setdefault('sidebar_nav', [])
    context.setdefault('sidebar_nav', [])
    context.setdefault('sidebar_nav', [])
    context.setdefault('sidebar_nav', [])
    context.setdefault('sidebar_nav', [])
    context.setdefault('sidebar_nav', [])
    context.setdefault('administrative_sidebar_nav', [])
    
    return context


@login_required
def output_value_template_manage(request):
    """产值模板管理页面"""
    # 检查权限
    from backend.apps.system_management.services import user_has_permission
    has_permission = user_has_permission(request.user, 'settlement_center.manage_output') or user_has_permission(request.user, 'system_management.manage_settings')
    if not has_permission:
        raise PermissionDenied("您没有权限访问产值模板管理。")
    
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
                "产值模板管理",
                "📊",
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
            "产值模板管理",
            "📊",
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
    
    context = _context(
        "产值模板管理",
        "📊",
        "配置和管理产值计算模板，包括阶段、里程碑和事件的设置。",
        summary_cards=summary_cards,
        sections=sections,
        request=request,
    )
    context['stages'] = stage_data
    
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
    
    # 分页（简单实现）
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
    
    context = _context(
        "产值记录查询",
        "📈",
        "查看和管理产值计算记录，了解产值分配情况。",
        summary_cards=summary_cards,
        request=request,
    )
    context['records'] = page_obj
    context['projects'] = Project.objects.filter(status__in=['in_progress', 'completed']).order_by('-created_time')
    
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
    
    context = _context(
        '确认产值记录',
        '✅',
        f'确认产值记录：{record.record_number}',
        request=request,
    )
    context['record'] = record
    return render(request, "settlement_center/output_value_record_confirm.html", context)


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
    })
    return render(request, "settlement_center/payment_record_list.html", context)


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


def _format_user_display(user, default='—'):
    """格式化用户显示名称"""
    if not user:
        return default
    if hasattr(user, 'get_full_name') and user.get_full_name():
        return user.get_full_name()
    if hasattr(user, 'name'):
        return user.name
    return user.username if hasattr(user, 'username') else str(user)


@login_required
def settlement_home(request):
    """回款管理首页 - 数据展示中心"""
    permission_codes = get_user_permission_codes(request.user)
    now = timezone.now()
    today = now.date()
    this_month_start = today.replace(day=1)
    seven_days_ago = today - timedelta(days=7)
    
    context = {}
    
    try:
        from backend.apps.production_management.models import BusinessPaymentPlan
        
        # ========== 核心指标卡片 ==========
        core_cards = []
        
        # 回款计划统计
        all_plans = BusinessPaymentPlan.objects.select_related('contract', 'contract__client').all()
        total_plans = all_plans.count()
        pending_plans = all_plans.filter(status='pending').count()
        overdue_plans = all_plans.filter(
            status__in=['pending', 'partial'],
            planned_date__lt=today
        ).count()
        completed_plans = all_plans.filter(status='completed').count()
        
        total_planned_amount = all_plans.aggregate(
            total=Sum('planned_amount')
        )['total'] or Decimal('0')
        total_actual_amount = all_plans.aggregate(
            total=Sum('actual_amount')
        )['total'] or Decimal('0')
        this_month_plans = all_plans.filter(planned_date__gte=this_month_start).count()
        
        # 产值记录统计
        all_output_records = OutputValueRecord.objects.select_related('project', 'responsible_user').all()
        total_output_records = all_output_records.count()
        pending_output_records = all_output_records.filter(status='pending').count()
        confirmed_output_records = all_output_records.filter(status='confirmed').count()
        this_month_output_records = all_output_records.filter(calculated_time__gte=this_month_start).count()
        
        total_output_value = all_output_records.aggregate(
            total=Sum('calculated_value')
        )['total'] or Decimal('0')
        
        # 项目结算统计
        all_settlements = ProjectSettlement.objects.select_related('project', 'contract', 'created_by').all()
        total_settlements = all_settlements.count()
        pending_settlements = all_settlements.filter(
            status__in=['submitted', 'client_review', 'client_feedback', 'reconciliation']
        ).count()
        confirmed_settlements = all_settlements.filter(status='confirmed').count()
        this_month_settlements = all_settlements.filter(created_time__gte=this_month_start).count()
        
        total_settlement_amount = all_settlements.filter(status__in=['confirmed', 'reconciliation']).aggregate(
            total=Sum('total_settlement_amount')
        )['total'] or Decimal('0')
        
        # 回款记录统计
        all_payment_records = PaymentRecord.objects.select_related('confirmed_by').all()
        total_payment_records = all_payment_records.count()
        pending_payment_records = all_payment_records.filter(status='pending').count()
        confirmed_payment_records = all_payment_records.filter(status='confirmed').count()
        this_month_payment_records = all_payment_records.filter(payment_date__gte=this_month_start).count()
        
        this_month_payment_amount = all_payment_records.filter(
            payment_date__gte=this_month_start,
            status='confirmed'
        ).aggregate(total=Sum('payment_amount'))['total'] or Decimal('0')
        
        # 卡片1：回款计划
        try:
            plan_url = reverse('settlement_pages:payment_plan_list')
        except NoReverseMatch:
            plan_url = '#'
        core_cards.append({
            'label': '回款计划',
            'icon': '💳',
            'value': str(total_plans),
            'subvalue': f'待回款 {pending_plans} | 逾期 {overdue_plans} | 本月 {this_month_plans}',
            'url': plan_url,
            'variant': 'dark' if overdue_plans > 0 else 'secondary'
        })
        
        # 卡片2：计划金额
        core_cards.append({
            'label': '计划金额',
            'icon': '💰',
            'value': f'¥{total_planned_amount:,.0f}',
            'subvalue': f'已回款 ¥{total_actual_amount:,.0f} | 回款率 {int((total_actual_amount / total_planned_amount * 100) if total_planned_amount > 0 else 0)}%',
            'url': plan_url,
            'variant': 'secondary'
        })
        
        # 卡片3：产值记录
        try:
            output_url = reverse('settlement_pages:output_value_record_list')
        except NoReverseMatch:
            output_url = '#'
        core_cards.append({
            'label': '产值记录',
            'icon': '📊',
            'value': str(total_output_records),
            'subvalue': f'待确认 {pending_output_records} | 已确认 {confirmed_output_records} | 本月 {this_month_output_records}',
            'url': output_url,
            'variant': 'dark' if pending_output_records > 0 else 'secondary'
        })
        
        # 卡片4：产值总额
        core_cards.append({
            'label': '产值总额',
            'icon': '📈',
            'value': f'¥{total_output_value:,.0f}',
            'subvalue': f'已确认产值',
            'url': output_url,
            'variant': 'secondary'
        })
        
        # 卡片5：项目结算
        try:
            settlement_url = reverse('settlement_pages:project_settlement_list')
        except NoReverseMatch:
            settlement_url = '#'
        core_cards.append({
            'label': '项目结算',
            'icon': '🧾',
            'value': str(total_settlements),
            'subvalue': f'待处理 {pending_settlements} | 已确认 {confirmed_settlements} | 本月 {this_month_settlements}',
            'url': settlement_url,
            'variant': 'dark' if pending_settlements > 0 else 'secondary'
        })
        
        # 卡片6：回款记录
        try:
            payment_record_url = reverse('settlement_pages:payment_record_list')
        except NoReverseMatch:
            payment_record_url = '#'
        core_cards.append({
            'label': '回款记录',
            'icon': '💵',
            'value': str(total_payment_records),
            'subvalue': f'待确认 {pending_payment_records} | 本月回款 ¥{this_month_payment_amount:,.0f}',
            'url': payment_record_url,
            'variant': 'dark' if pending_payment_records > 0 else 'secondary'
        })
        
        context['core_cards'] = core_cards
        
        # ========== 风险预警 ==========
        risk_warnings = []
        
        # 逾期回款计划
        overdue_plan_list = all_plans.filter(
            status__in=['pending', 'partial'],
            planned_date__lt=today
        ).select_related('contract', 'contract__client')[:5]
        
        for plan in overdue_plan_list:
            days_overdue = (today - plan.planned_date).days
            client_name = plan.contract.client.name if plan.contract and plan.contract.client else '未知'
            risk_warnings.append({
                'type': 'plan',
                'title': f'{plan.phase_name} - {client_name}',
                'responsible': client_name,
                'days': days_overdue,
                'url': reverse('settlement_pages:payment_plan_detail', args=['business', plan.id])
            })
        
        # 待确认产值记录（超过7天）
        stale_output_records = all_output_records.filter(
            status='pending',
            calculated_time__lt=seven_days_ago
        ).select_related('responsible_user', 'project')[:5]
        
        for record in stale_output_records:
            days_since_create = (today - record.calculated_time.date()).days
            responsible_name = _format_user_display(record.responsible_user) if record.responsible_user else '未知'
            project_name = record.project.project_number if record.project else '未知'
            risk_warnings.append({
                'type': 'output',
                'title': f'{project_name} - 产值记录待确认',
                'responsible': responsible_name,
                'days': days_since_create,
                'url': output_url
            })
        
        context['risk_warnings'] = risk_warnings[:5]
        context['overdue_plans_count'] = overdue_plan_list.count()
        context['stale_output_records_count'] = stale_output_records.count()
        
        # ========== 待办事项 ==========
        todo_items = []
        
        # 待确认回款记录
        pending_payment_list = all_payment_records.filter(status='pending').select_related('confirmed_by')[:5]
        for payment in pending_payment_list:
            todo_items.append({
                'type': 'payment',
                'title': f'回款单号：{payment.payment_number}',
                'payment_number': payment.payment_number,
                'responsible': '待确认',
                'url': payment_record_url
            })
        
        # 待处理项目结算
        pending_settlement_list = all_settlements.filter(
            status__in=['submitted', 'client_review', 'client_feedback']
        ).select_related('created_by', 'project')[:5]
        for settlement in pending_settlement_list:
            creator_name = _format_user_display(settlement.created_by) if settlement.created_by else '未知'
            project_name = settlement.project.project_number if settlement.project else '未知'
            todo_items.append({
                'type': 'settlement',
                'title': f'{project_name} - {settlement.settlement_number}',
                'settlement_number': settlement.settlement_number,
                'responsible': creator_name,
                'url': reverse('settlement_pages:project_settlement_detail', args=[settlement.id])
            })
        
        context['todo_items'] = todo_items[:10]
        context['pending_approval_count'] = pending_payment_records + pending_settlements
        context['todo_summary_url'] = payment_record_url + '?status=pending'
        
        # ========== 我的工作 ==========
        my_work = {}
        
        # 我创建的产值记录
        my_output_records = all_output_records.filter(responsible_user=request.user).order_by('-calculated_time')[:3]
        my_work['my_output_records'] = [{
            'title': f'{record.project.project_number if record.project else "未知"} - {record.record_number}',
            'status': record.get_status_display(),
            'url': output_url
        } for record in my_output_records]
        my_work['my_output_records_count'] = all_output_records.filter(responsible_user=request.user).count()
        
        # 我创建的项目结算
        my_settlements = all_settlements.filter(created_by=request.user).order_by('-created_time')[:3]
        my_work['my_settlements'] = [{
            'title': f'{settlement.project.project_number if settlement.project else "未知"} - {settlement.settlement_number}',
            'status': settlement.get_status_display(),
            'url': reverse('settlement_pages:project_settlement_detail', args=[settlement.id])
        } for settlement in my_settlements]
        my_work['my_settlements_count'] = all_settlements.filter(created_by=request.user).count()
        
        my_work['summary_url'] = plan_url
        
        context['my_work'] = my_work
        
        # ========== 最近活动 ==========
        recent_activities = {}
        
        # 最近创建的回款计划
        recent_plans = all_plans.select_related('contract', 'contract__client').order_by('-created_time')[:5]
        recent_activities['recent_plans'] = [{
            'title': plan.phase_name,
            'creator': plan.contract.client.name if plan.contract and plan.contract.client else '未知',
            'time': plan.planned_date,
            'url': reverse('settlement_pages:payment_plan_detail', args=['business', plan.id])
        } for plan in recent_plans]
        
        # 最近创建的回款记录
        recent_payments = all_payment_records.select_related('confirmed_by').order_by('-payment_date')[:5]
        recent_activities['recent_payments'] = [{
            'title': payment.payment_number,
            'creator': _format_user_display(payment.confirmed_by) if payment.confirmed_by else '系统',
            'time': payment.payment_date,
            'url': payment_record_url
        } for payment in recent_payments]
        
        context['recent_activities'] = recent_activities
        
    except Exception as e:
        import logging
        logger = logging.getLogger(__name__)
        logger.exception('获取回款管理统计数据失败: %s', str(e))
        context.setdefault('core_cards', [])
        context.setdefault('risk_warnings', [])
        context.setdefault('todo_items', [])
        context.setdefault('my_work', {})
        context.setdefault('recent_activities', {})
    
    # 顶部操作栏
    top_actions = []
    if _permission_granted('payment_management.payment_plan.view', permission_codes):
        try:
            top_actions.append({
                'label': '查看回款计划',
                'url': reverse('settlement_pages:payment_plan_list'),
                'icon': '💳'
            })
        except Exception:
            pass
    
    context['top_actions'] = top_actions
    
    # 构建上下文
    page_context = _context(
        "回款管理",
        "💰",
        "数据展示中心 - 集中展示回款关键指标、状态与风险",
        request=request
    )
    
    # 设置侧边栏导航
    settlement_sidebar_nav = _build_settlement_sidebar_nav(permission_codes, request.path, active_id='settlement_home')
    page_context['settlement_menu'] = settlement_sidebar_nav
    page_context['settlement_sidebar_nav'] = settlement_sidebar_nav
    page_context['sidebar_title'] = '回款管理'
    page_context['sidebar_subtitle'] = 'Settlement Management'
    
    # 为所有可能的侧边栏变量设置默认值，避免模板错误
    page_context.setdefault('plan_menu', [])
    page_context.setdefault('sidebar_nav', [])
    page_context.setdefault('customer_menu', [])
    page_context.setdefault('sidebar_nav', [])
    page_context.setdefault('sidebar_nav', [])
    page_context.setdefault('sidebar_nav', [])
    page_context.setdefault('sidebar_nav', [])
    page_context.setdefault('sidebar_nav', [])
    page_context.setdefault('sidebar_nav', [])
    page_context.setdefault('sidebar_nav', [])
    page_context.setdefault('administrative_sidebar_nav', [])
    
    # 合并所有数据
    page_context.update(context)
    
    return render(request, "settlement_management/settlement_management_home.html", page_context)