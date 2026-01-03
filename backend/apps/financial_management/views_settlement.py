from django.contrib.auth.decorators import login_required
from django.shortcuts import render, get_object_or_404, redirect
from django.contrib import messages
from django.core.exceptions import PermissionDenied
from django.db.models import Q, Sum, Count, F
from django.utils import timezone
from decimal import Decimal

from .models_settlement import (
    OutputValueStage, OutputValueMilestone, OutputValueEvent, OutputValueRecord,
    ProjectSettlement, SettlementItem, ServiceFeeRate, ContractSettlement,
    PaymentRecord
)
# from backend.apps.production_quality.models import Opinion  # 已删除生产质量模块
from .forms_settlement import ProjectSettlementForm, ContractSettlementForm
from .services_settlement import get_project_output_value_for_settlement, get_project_output_value_summary
from backend.apps.production_management.models import Project
from backend.apps.system_management.models import User
from backend.apps.system_management.services import get_user_permission_codes
from backend.core.views import _permission_granted
from backend.apps.production_management.models import BusinessContract
from django.core.paginator import Paginator
from django.db.models import Max


def _context(page_title, page_icon, description, summary_cards=None, sections=None):
    """统一的页面上下文生成函数"""
    return {
        "page_title": page_title,
        "page_icon": page_icon,
        "description": description,
        "summary_cards": summary_cards or [],
        "sections": sections or [],
    }


@login_required
def output_value_template_manage(request):
    """产值模板管理页面"""
    # 检查权限
    from backend.apps.system_management.services import user_has_permission
    has_permission = user_has_permission(request.user, 'financial_management.settlement.manage_output') or user_has_permission(request.user, 'system_management.manage_settings')
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
        ))
    
    # 统计信息
    total_stages = stages.count()
    total_milestones = OutputValueMilestone.objects.filter(is_active=True).count()
    total_events = OutputValueEvent.objects.filter(is_active=True).count()
    
    summary_cards = [
        {"label": "产值阶段", "value": total_stages, "hint": "已配置的产值阶段数量"},
        {"label": "产值里程碑", "value": total_milestones, "hint": "已配置的里程碑数量"},
        {"label": "产值事件", "value": total_events, "hint": "已配置的事件数量"},
        {"label": "启用状态", "value": "正常", "hint": "产值模板配置状态"},
    ]
    
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
    )
    context['stages'] = stage_data
    
    return render(request, "settlement_center/output_value_template.html", context)


@login_required
def output_value_record_list(request):
    """产值计算记录列表"""
    # 检查权限
    from backend.apps.system_management.services import user_has_permission
    has_view_permission = user_has_permission(request.user, 'financial_management.settlement.view_analysis') or user_has_permission(request.user, 'financial_management.settlement.manage_output')
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
        ))
    
    # 如果是普通用户，只显示自己的记录
    has_manage_permission = user_has_permission(request.user, 'financial_management.settlement.manage_output')
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
    from django.core.paginator import Paginator
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
    
    summary_cards = [
        {"label": "产值记录总数", "value": records.count(), "hint": "所有产值计算记录的数量"},
        {"label": "已确认产值", "value": f"{float(confirmed_value):,.2f}", "hint": "已确认的产值总额"},
        {"label": "待确认记录", "value": records.filter(status='calculated').count(), "hint": "待确认的产值记录数量"},
        {"label": "本月产值", "value": f"{float(records.filter(calculated_time__month=timezone.now().month, calculated_time__year=timezone.now().year, status__in=['calculated', 'confirmed']).aggregate(total=Sum('calculated_value'))['total'] or Decimal('0')):,.2f}", "hint": "本月计算的产值总额"},
    ]
    
    context = _context(
        "产值记录查询",
        "📈",
        "查看和管理产值计算记录，了解产值分配情况。",
        summary_cards=summary_cards,
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
    has_view_permission = user_has_permission(request.user, 'financial_management.settlement.view_analysis') or user_has_permission(request.user, 'financial_management.settlement.manage_output')
    if not has_view_permission:
        # 检查是否是项目成员
        if not (project.project_manager == request.user or 
                project.business_manager == request.user or
                project.team_members.filter(user=request.user, is_active=True).exists()):
            messages.error(request, '您没有权限查看此项目的产值信息')
            return redirect('financial_pages:settlement_output_value_record_list')
    
    # 获取项目产值统计
    try:
        output_value_summary = get_project_output_value_summary(project)
    except Exception as e:
        import logging
        logger = logging.getLogger(__name__)
        logger.exception('获取项目产值统计失败: %s', str(e))
        messages.error(request, f'获取项目产值统计失败：{str(e)}')
        return redirect('financial_pages:settlement_output_value_record_list')
    
    # 检查权限
    has_manage_permission = user_has_permission(request.user, 'financial_management.settlement.manage_output')
    
    # 产值记录分页
    paginator = Paginator(output_value_summary['records'], 20)
    page_number = request.GET.get('page', 1)
    page_obj = paginator.get_page(page_number)
    
    context = _context(
        f"项目产值详情 - {project.project_number}",
        "📊",
        f"项目：{project.name}",
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
    has_manage_permission = user_has_permission(request.user, 'financial_management.settlement.manage_output')
    if record.responsible_user != request.user and not has_manage_permission:
        raise PermissionDenied("您没有权限确认此产值记录。")
    
    if request.method == 'POST':
        record.status = 'confirmed'
        record.confirmed_time = timezone.now()
        record.confirmed_by = request.user
        record.save(update_fields=['status', 'confirmed_time', 'confirmed_by', 'updated_time'])
        messages.success(request, '产值记录已确认。')
        return redirect('financial_pages:settlement_output_value_record_list')
    
    context = {
        'record': record,
        'page_title': '确认产值记录',
        'page_icon': '✅',
    }
    return render(request, "settlement_center/output_value_record_confirm.html", context)


@login_required
def output_value_statistics(request):
    """产值统计报表"""
    # 检查权限
    from backend.apps.system_management.services import user_has_permission
    has_view_permission = user_has_permission(request.user, 'financial_management.settlement.view_analysis') or user_has_permission(request.user, 'financial_management.settlement.manage_output')
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
    has_manage_permission = user_has_permission(request.user, 'financial_management.settlement.manage_output')
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
    
    summary_cards = [
        {"label": "总产值", "value": f"{float(total_stats['total_value'] or Decimal('0')):,.2f}", "hint": "所有已计算的产值总额"},
        {"label": "已确认产值", "value": f"{float(total_stats['confirmed_value'] or Decimal('0')):,.2f}", "hint": "已确认的产值总额"},
        {"label": "产值记录数", "value": total_stats['record_count'] or 0, "hint": "产值计算记录的总数量"},
        {"label": "参与人员", "value": len(user_stats), "hint": "参与产值分配的人员数量"},
    ]
    
    context = _context(
        "产值统计报表",
        "📊",
        "查看产值分配统计和分析报表。",
        summary_cards=summary_cards,
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
    """从项目的Opinion生成结算明细项"""
    # 获取项目下所有有节省金额的Opinion
    opinions = Opinion.objects.filter(
        project=settlement.project,
        saving_amount__gt=0  # 只选择有节省金额的意见
    ).select_related('professional_category')
    
    # 排除已经在其他结算单中使用过的Opinion（可选，如果需要避免重复结算）
    existing_opinion_ids = SettlementItem.objects.filter(
        settlement__project=settlement.project,
        settlement__status__in=['submitted', 'client_review', 'client_feedback', 'reconciliation', 'confirmed']
    ).values_list('opinion_id', flat=True)
    
    opinions = opinions.exclude(id__in=existing_opinion_ids)
    
    # 按创建时间排序
    opinions = opinions.order_by('created_at')
    
    # 获取当前结算单已存在的明细项数量（用于排序）
    existing_count = settlement.items.count()
    
    # 为每个Opinion创建结算明细项
    created_count = 0
    for idx, opinion in enumerate(opinions):
        # 检查是否已存在（避免重复创建）
        if SettlementItem.objects.filter(settlement=settlement, opinion=opinion).exists():
            continue
        
        # 获取专业分类名称
        professional_category_name = opinion.professional_category.name if opinion.professional_category else ''
        
        # 获取意见标题（使用推荐建议或问题描述作为标题）
        if opinion.recommendation:
            opinion_title = opinion.recommendation[:200]
        elif opinion.issue_description:
            opinion_title = opinion.issue_description[:200]
        else:
            opinion_title = f"意见 {opinion.opinion_number}"
        
        SettlementItem.objects.create(
            settlement=settlement,
            opinion=opinion,
            opinion_number=opinion.opinion_number,
            opinion_title=opinion_title,
            professional_category=professional_category_name,
            location_name=opinion.location_name or '',
            original_saving_amount=opinion.saving_amount or Decimal('0'),
            review_status='pending',
            order=existing_count + idx + 1,
            created_by=user,
        )
        created_count += 1
    
    # 保存结算单以触发自动计算节省金额汇总
    if created_count > 0:
        settlement.save()
    
    return created_count


# ==================== 结算管理视图函数 ====================

@login_required
def project_settlement_list(request):
    """项目结算列表页"""
    permission_codes = get_user_permission_codes(request.user)
    if not _permission_granted('financial_management.settlement.settlement.view', permission_codes):
        messages.error(request, '您没有权限查看项目结算')
        return redirect('financial_pages:settlement_output_value_record_list')
    
    settlements = ProjectSettlement.objects.select_related(
        'project', 'contract', 'created_by'
    ).order_by('-settlement_date', '-created_time')
    
    # 权限过滤：如果不是管理员，只能查看自己创建的
    if not _permission_granted('financial_management.settlement.settlement.manage', permission_codes):
        settlements = settlements.filter(created_by=request.user)
    
    # 筛选
    status_filter = request.GET.get('status')
    if status_filter:
        settlements = settlements.filter(status=status_filter)
    
    project_id = request.GET.get('project_id')
    if project_id:
        settlements = settlements.filter(project_id=project_id)
    
    # 分页
    paginator = Paginator(settlements, 20)
    page_number = request.GET.get('page', 1)
    page_obj = paginator.get_page(page_number)
    
    # 统计信息
    total_count = settlements.count()
    total_amount = settlements.filter(status__in=['confirmed', 'reconciliation']).aggregate(
        total=Sum('total_settlement_amount')
    )['total'] or Decimal('0')
    pending_count = settlements.filter(status__in=['submitted', 'client_review', 'client_feedback', 'reconciliation']).count()
    
    summary_cards = [
        {"label": "结算单总数", "value": total_count, "hint": "所有项目结算单数量"},
        {"label": "已确认结算金额", "value": f"{float(total_amount):,.2f}", "hint": "已确认的结算金额总额"},
        {"label": "待审核数量", "value": pending_count, "hint": "待审核的结算单数量"},
        {"label": "本月结算", "value": settlements.filter(
            settlement_date__year=timezone.now().year,
            settlement_date__month=timezone.now().month,
            status__in=['confirmed']
        ).count(), "hint": "本月已确认的结算单数量"},
    ]
    
    context = _context(
        "项目结算管理",
        "💰",
        "管理项目结算单，包括结算申请、审核和确认",
        summary_cards=summary_cards,
    )
    context.update({
        'settlements': page_obj,
        'projects': Project.objects.filter(status__in=['in_progress', 'completed']).order_by('-created_time'),
        'status_choices': ProjectSettlement.STATUS_CHOICES,
        'status_filter': status_filter,
        'project_id': project_id,
        'can_create': _permission_granted('financial_management.settlement.settlement.create', permission_codes),
    })
    
    return render(request, "settlement_center/project_settlement_list.html", context)


@login_required
def project_settlement_detail(request, settlement_id):
    """项目结算详情页"""
    settlement = get_object_or_404(ProjectSettlement, id=settlement_id)
    permission_codes = get_user_permission_codes(request.user)
    
    # 权限检查：只有有查看权限或创建人可以查看
    if not _permission_granted('financial_management.settlement.settlement.view', permission_codes):
        if settlement.created_by != request.user:
            messages.error(request, '您没有权限查看此结算单')
            return redirect('financial_pages:settlement_project_settlement_list')
    
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
        (_permission_granted('financial_management.settlement.settlement.manage', permission_codes) or
         settlement.created_by == request.user)
    )
    can_submit = (
        settlement.status == 'draft' and
        (_permission_granted('financial_management.settlement.settlement.manage', permission_codes) or
         settlement.created_by == request.user)
    )
    can_finance_review = (
        settlement.status == 'submitted' and
        _permission_granted('financial_management.settlement.settlement.finance_review', permission_codes)
    )
    can_manager_approve = (
        settlement.status == 'finance_review' and
        _permission_granted('financial_management.settlement.settlement.manager_approve', permission_codes)
    )
    can_gm_approve = (
        settlement.status == 'manager_approve' and
        _permission_granted('financial_management.settlement.settlement.gm_approve', permission_codes)
    )
    can_confirm = (
        settlement.status == 'approved' and
        _permission_granted('financial_management.settlement.settlement.confirm', permission_codes)
    )
    
    context = _context(
        f"项目结算 - {settlement.settlement_number}",
        "💰",
        f"项目：{settlement.project.name}",
    )
    # 获取结算明细项
    settlement_items = settlement.items.select_related('reviewed_by', 'created_by').order_by('order')
    
    # 检查是否有权限审核明细项（造价工程师或有管理权限）
    can_review_items = (
        settlement.status == 'draft' and
        (_permission_granted('financial_management.settlement.settlement.manage', permission_codes) or
         request.user.roles.filter(code='cost_engineer').exists())
    )
    
    # 检查是否可以重新生成明细项
    can_generate_items = (
        settlement.status == 'draft' and
        (_permission_granted('financial_management.settlement.settlement.manage', permission_codes) or
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
    if not _permission_granted('financial_management.settlement.settlement.create', permission_codes):
        messages.error(request, '您没有权限创建项目结算单')
        return redirect('financial_pages:settlement_project_settlement_list')
    
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
            
            return redirect('financial_pages:settlement_project_settlement_detail', settlement_id=settlement.id)
        else:
            messages.error(request, "请检查表单中的错误。")
    else:
        form = ProjectSettlementForm(user=request.user)
    
    context = _context(
        "新增项目结算单",
        "➕",
        "创建新的项目结算单",
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
        return redirect('financial_pages:settlement_project_settlement_detail', settlement_id=settlement.id)
    
    if not _permission_granted('financial_management.settlement.settlement.manage', permission_codes):
        if settlement.created_by != request.user:
            messages.error(request, '您没有权限编辑此结算单')
            return redirect('financial_pages:settlement_project_settlement_detail', settlement_id=settlement.id)
    
    if request.method == 'POST':
        form = ProjectSettlementForm(request.POST, request.FILES, instance=settlement, user=request.user)
        if form.is_valid():
            settlement = form.save()
            messages.success(request, f'项目结算单 {settlement.settlement_number} 更新成功！')
            return redirect('financial_pages:settlement_project_settlement_detail', settlement_id=settlement.id)
        else:
            messages.error(request, "请检查表单中的错误。")
    else:
        form = ProjectSettlementForm(instance=settlement, user=request.user)
    
    context = _context(
        f"编辑项目结算单 - {settlement.settlement_number}",
        "✏️",
        f"项目：{settlement.project.name}",
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
        return redirect('financial_pages:settlement_project_settlement_detail', settlement_id=settlement.id)
    
    if not _permission_granted('financial_management.settlement.settlement.manage', permission_codes):
        if settlement.created_by != request.user:
            messages.error(request, '您没有权限提交此结算单')
            return redirect('financial_pages:settlement_project_settlement_detail', settlement_id=settlement.id)
    
    if request.method == 'POST':
        settlement.status = 'submitted'
        settlement.submitted_by = request.user
        settlement.submitted_time = timezone.now()
        settlement.save(update_fields=['status', 'submitted_by', 'submitted_time', 'updated_time'])
        messages.success(request, '结算单已提交审核')
        return redirect('financial_pages:settlement_project_settlement_detail', settlement_id=settlement.id)
    
    context = _context(
        "提交结算单",
        "📤",
        f"确认提交结算单 {settlement.settlement_number} 进行审核？",
    )
    context.update({
        'settlement': settlement,
    })
    return render(request, "settlement_center/project_settlement_confirm.html", context)


# ==================== 回款管理模块 ====================

@login_required
def payment_plan_list(request):
    """回款计划列表页面"""
    from backend.apps.production_management.models import PaymentPlan as ProjectPaymentPlan
    from backend.apps.production_management.models import BusinessPaymentPlan
    
    permission_codes = get_user_permission_codes(request.user)
    
    # 获取筛选参数
    search = request.GET.get('search', '')
    status_filter = request.GET.get('status', '')
    plan_type = request.GET.get('plan_type', '')  # 'project' or 'business'
    
    # 获取项目回款计划
    project_plans = ProjectPaymentPlan.objects.select_related('project').all()
    
    # 获取商务回款计划
    business_plans = BusinessPaymentPlan.objects.select_related('contract').all()
    
    # 应用筛选
    if search:
        project_plans = project_plans.filter(
            Q(phase_name__icontains=search) |
            Q(project__name__icontains=search) |
            Q(project__project_number__icontains=search)
        )
        business_plans = business_plans.filter(
            Q(phase_name__icontains=search) |
            Q(contract__contract_number__icontains=search) |
            Q(contract__client__name__icontains=search)
        )
    
    if status_filter:
        project_plans = project_plans.filter(status=status_filter)
        business_plans = business_plans.filter(status=status_filter)
    
    if plan_type == 'project':
        business_plans = business_plans.none()
    elif plan_type == 'business':
        project_plans = project_plans.none()
    
    # 合并数据并排序
    all_plans = []
    for plan in project_plans:
        all_plans.append({
            'id': plan.id,
            'type': 'project',
            'phase_name': plan.phase_name,
            'planned_amount': plan.planned_amount,
            'actual_amount': plan.actual_amount or Decimal('0'),
            'planned_date': plan.planned_date,
            'actual_date': plan.actual_date,
            'status': plan.status,
            'related_name': plan.project.name if plan.project else '',
            'related_number': plan.project.project_number if plan.project else '',
        })
    
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
    paginator = Paginator(all_plans, 20)
    page_number = request.GET.get('page', 1)
    page_obj = paginator.get_page(page_number)
    
    # 统计信息
    total_plans = len(all_plans)
    total_planned_amount = sum(p['planned_amount'] for p in all_plans)
    total_actual_amount = sum(p['actual_amount'] for p in all_plans)
    
    summary_cards = [
        {"label": "回款计划总数", "value": total_plans, "hint": "所有回款计划数量"},
        {"label": "计划回款总额", "value": f"¥{total_planned_amount:,.2f}", "hint": "所有计划回款金额合计"},
        {"label": "实际回款总额", "value": f"¥{total_actual_amount:,.2f}", "hint": "所有实际回款金额合计"},
        {"label": "回款完成率", "value": f"{(total_actual_amount / total_planned_amount * 100) if total_planned_amount > 0 else 0:.1f}%", "hint": "实际回款/计划回款"},
    ]
    
    context = _context(
        "回款计划管理",
        "💳",
        "统一管理项目回款计划和商务合同回款计划",
        summary_cards=summary_cards,
    )
    context.update({
        'page_obj': page_obj,
        'search': search,
        'status_filter': status_filter,
        'plan_type': plan_type,
        'status_choices': ProjectPaymentPlan.STATUS_CHOICES,
    })
    return render(request, "settlement_center/payment_plan_list.html", context)


@login_required
def payment_plan_detail(request, plan_type, plan_id):
    """回款计划详情页面"""
    from backend.apps.production_management.models import PaymentPlan as ProjectPaymentPlan
    from backend.apps.production_management.models import BusinessPaymentPlan
    
    permission_codes = get_user_permission_codes(request.user)
    
    # 根据类型获取回款计划
    if plan_type == 'project':
        plan = get_object_or_404(ProjectPaymentPlan, id=plan_id)
        related_obj = plan.project
    elif plan_type == 'business':
        plan = get_object_or_404(BusinessPaymentPlan, id=plan_id)
        related_obj = plan.contract
    else:
        messages.error(request, '无效的回款计划类型')
        return redirect('financial_pages:settlement_payment_plan_list')
    
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
    paginator = Paginator(payment_records, 20)
    page_number = request.GET.get('page', 1)
    page_obj = paginator.get_page(page_number)
    
    # 统计信息
    total_records = payment_records.count()
    total_amount = payment_records.filter(status='confirmed').aggregate(
        total=Sum('payment_amount')
    )['total'] or Decimal('0')
    
    summary_cards = [
        {"label": "回款记录总数", "value": total_records, "hint": "所有回款记录数量"},
        {"label": "已确认回款总额", "value": f"¥{total_amount:,.2f}", "hint": "已确认的回款金额合计"},
    ]
    
    context = _context(
        "回款记录管理",
        "💰",
        "管理所有实际回款记录",
        summary_cards=summary_cards,
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
    
    if not _permission_granted('financial_management.settlement.payment_record.create', permission_codes):
        messages.error(request, '您没有权限创建回款记录')
        return redirect('financial_pages:settlement_payment_plan_list')
    
    # 获取回款计划
    if plan_type == 'project':
        from backend.apps.production_management.models import PaymentPlan as ProjectPaymentPlan
        plan = get_object_or_404(ProjectPaymentPlan, id=plan_id)
    elif plan_type == 'business':
        from backend.apps.production_management.models import BusinessPaymentPlan
        plan = get_object_or_404(BusinessPaymentPlan, id=plan_id)
    else:
        messages.error(request, '无效的回款计划类型')
        return redirect('financial_pages:settlement_payment_plan_list')
    
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
                return redirect('financial_pages:settlement_payment_plan_detail', plan_type=plan_type, plan_id=plan_id)
        except Exception as e:
            import logging
            logger = logging.getLogger(__name__)
            logger.exception('创建回款记录失败: %s', str(e))
            messages.error(request, f'创建回款记录失败：{str(e)}')
    
    context = _context(
        "创建回款记录",
        "💰",
        f"回款计划：{plan.phase_name}",
    )
    context.update({
        'plan': plan,
        'plan_type': plan_type,
        'payment_method_choices': PaymentRecord.PAYMENT_METHOD_CHOICES,
    })
    return render(request, "settlement_center/payment_record_form.html", context)