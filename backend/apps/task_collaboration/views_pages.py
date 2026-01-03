from datetime import timedelta

from django.contrib.auth.decorators import login_required
from django.db import transaction
from django.db.models import Q
from django.shortcuts import render
from django.urls import reverse
from django.utils import timezone

from backend.apps.production_management.models import Project, ProjectMilestone, ProjectTask
from backend.apps.system_management.services import get_user_permission_codes
from backend.core.views import _permission_granted, _build_full_top_nav, _build_unified_sidebar_nav
from django.contrib import messages
from django.shortcuts import redirect
from django.urls import reverse, NoReverseMatch
MILESTONE_PRESETS = {
    "result_optimization": [
        "优化前图纸",
        "咨询意见书",
        "三方沟通成果",
        "优化后图纸",
        "完工确认函",
    ],
    "process_optimization": [
        "过程优化报告",
        "核图意见书",
        "完工确认函",
    ],
    "detailed_review": [
        "咨询意见书",
        "三方沟通成果",
        "核图意见书",
        "完工确认函",
    ],
    "full_process_consulting": [
        "过程咨询报告",
        "核图意见书",
        "完工确认函",
    ],
}


def _ensure_project_milestones(project: Project) -> None:
    service_type_code = getattr(project.service_type, "code", None)
    preset = MILESTONE_PRESETS.get(service_type_code)
    if not preset:
        return

    existing = set(
        ProjectMilestone.objects.filter(project=project).values_list("name", flat=True)
    )
    missing = [name for name in preset if name not in existing]
    if not missing:
        return

    base_date = project.start_date or timezone.now().date()
    if project.start_date and project.end_date:
        total_days = (project.end_date - project.start_date).days
        interval_days = total_days // max(len(preset), 1)
        if interval_days <= 0:
            interval_days = 7
    else:
        interval_days = 14

    new_objects = []
    for index, name in enumerate(missing, start=1):
        planned_date = base_date + timedelta(days=interval_days * index)
        new_objects.append(
            ProjectMilestone(
                project=project,
                name=name,
                planned_date=planned_date,
                completion_rate=0,
                is_completed=False,
                description=f"{project.project_number} 自动生成的里程碑：{name}",
            )
        )
    if new_objects:
        with transaction.atomic():
            ProjectMilestone.objects.bulk_create(new_objects)


# 任务协作菜单结构定义
TASK_COLLABORATION_MENU_STRUCTURE = [
    {'id': 'task_collaboration_home', 'label': '任务协作首页', 'icon': '🏠', 'url_name': 'task_collaboration:task_collaboration_home', 'permission': None},
    {'id': 'task_board', 'label': '任务看板', 'icon': '🗂', 'url_name': 'task_collaboration:task_board', 'permission': None},
    {'id': 'workspace', 'label': '协作空间', 'icon': '🤝', 'url_name': 'task_collaboration:workspace', 'permission': None},
    {'id': 'process_engine', 'label': '流程引擎', 'icon': '⚙️', 'url_name': 'task_collaboration:process_engine', 'permission': None},
    {'id': 'timesheet', 'label': '工时记录', 'icon': '⏰', 'url_name': 'task_collaboration:timesheet', 'permission': None},
    {'id': 'message_center', 'label': '消息中心', 'icon': '💬', 'url_name': 'task_collaboration:message_center', 'permission': None},
]


def _build_task_collaboration_sidebar_nav(permission_set, request_path=None, active_id=None):
    """生成任务协作模块左侧菜单（统一格式）"""
    # 使用统一的菜单构建函数
    return _build_unified_sidebar_nav(TASK_COLLABORATION_MENU_STRUCTURE, permission_set, active_id=active_id)


def _build_context(page_title: str, page_icon: str, description: str, summary_cards=None, sections=None, request=None, active_menu_id=None):
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
        # 添加左侧菜单
        request_path = request.path
        context['module_sidebar_nav'] = _build_task_collaboration_sidebar_nav(permission_set, request_path, active_id=active_menu_id)
    else:
        context['full_top_nav'] = []
        context['module_sidebar_nav'] = []
    
    return context


@login_required
def task_collaboration_home(request):
    """任务协作首页"""
    permission_codes = get_user_permission_codes(request.user)
    today = timezone.now().date()
    
    # 权限检查
    if not _permission_granted('task_collaboration.view', permission_codes):
        messages.error(request, '您没有权限访问任务协作')
        return redirect('admin:index')
    
    # 收集统计数据
    summary_cards = []
    
    try:
        # 任务统计
        user = request.user
        accessible_projects = Project.objects.filter(
            Q(project_manager=user)
            | Q(team_members__user=user)
            | Q(business_manager=user)
            | Q(created_by=user)
        ).distinct()
        
        # 我的任务统计
        my_tasks = ProjectTask.objects.filter(
            assignee=user,
            status__in=['pending', 'in_progress']
        ).count()
        
        overdue_tasks = ProjectTask.objects.filter(
            assignee=user,
            status__in=['pending', 'in_progress'],
            due_time__lt=timezone.now()
        ).count()
        
        # 里程碑任务统计
        milestones = ProjectMilestone.objects.filter(
            project__in=accessible_projects
        )
        
        overdue_milestones = milestones.filter(
            planned_date__lt=today,
            is_completed=False
        ).count()
        
        due_today_milestones = milestones.filter(
            planned_date=today,
            is_completed=False
        ).count()
        
        summary_cards.append({
            'label': '我的任务',
            'icon': '📝',
            'value': str(my_tasks),
            'subvalue': f'逾期 {overdue_tasks} 个',
            'url': reverse('task_collaboration:task_board'),
            'variant': 'danger' if overdue_tasks > 0 else 'warning' if my_tasks > 0 else 'success'
        })
        
        summary_cards.append({
            'label': '里程碑任务',
            'icon': '🎯',
            'value': str(overdue_milestones + due_today_milestones),
            'subvalue': f'逾期 {overdue_milestones} 个 · 今日 {due_today_milestones} 个',
            'url': reverse('task_collaboration:task_board'),
            'variant': 'danger' if overdue_milestones > 0 else 'warning' if due_today_milestones > 0 else 'info'
        })
        
        summary_cards.append({
            'label': '参与项目',
            'icon': '🏗️',
            'value': str(accessible_projects.count()),
            'subvalue': '我参与的项目',
            'url': reverse('production_pages:project_list'),
            'variant': 'info'
        })
        
    except Exception as e:
        import logging
        logger = logging.getLogger(__name__)
        logger.exception('获取统计数据失败: %s', str(e))
    
    # 快捷操作
    quick_actions = []
    
    if _permission_granted('task_collaboration.assign', permission_codes):
        try:
            quick_actions.append({
                'label': '查看任务看板',
                'icon': '📋',
                'description': '查看所有任务和里程碑',
                'url': reverse('task_collaboration:task_board'),
                'link_label': '查看看板 →'
            })
        except Exception:
            pass
    
    # 功能模块入口
    module_entries = []
    
    if _permission_granted('task_collaboration.view', permission_codes):
        try:
            module_entries.append({
                'label': '任务看板',
                'icon': '📋',
                'description': '查看和管理所有任务',
                'url': reverse('task_collaboration:task_board'),
                'link_label': '进入模块 →'
            })
            
            module_entries.append({
                'label': '协作空间',
                'icon': '🤝',
                'description': '跨部门协作讨论和会议',
                'url': reverse('task_collaboration:workspace'),
                'link_label': '进入模块 →'
            })
            
            module_entries.append({
                'label': '流程引擎',
                'icon': '🔄',
                'description': '管理协作流程',
                'url': reverse('task_collaboration:process_engine'),
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
            'description': '任务协作的各个功能模块入口',
            'items': module_entries,
            'layout': 'grid'
        })
    
    # 构建上下文
    context = _build_context(
        page_title="任务协作",
        page_icon="🤝",
        description="管理团队任务和协作流程",
        summary_cards=summary_cards,
        sections=sections,
        request=request,
    )
    
    return render(request, "task_collaboration/home.html", context)


def _build_context_old(page_title: str, page_icon: str, description: str, summary_cards=None, sections=None):
    return {
        "page_title": page_title,
        "page_icon": page_icon,
        "description": description,
        "summary_cards": summary_cards or [],
        "sections": sections or [],
    }


@login_required
def task_board(request):
    user = request.user
    today = timezone.now().date()

    project_id = request.GET.get("project")

    project_queryset = Project.objects.select_related("project_manager").prefetch_related("team_members__user")
    accessible_projects = project_queryset.filter(
        Q(project_manager=user)
        | Q(team_members__user=user)
        | Q(business_manager=user)
        | Q(created_by=user)
    ).distinct()

    if project_id and project_id.isdigit():
        accessible_projects = accessible_projects.filter(id=int(project_id))

    accessible_projects = list(accessible_projects)

    for proj in accessible_projects:
        _ensure_project_milestones(proj)

    milestones = (
        ProjectMilestone.objects.filter(project__in=accessible_projects)
        .select_related("project")
        .order_by("planned_date")
    )

    overdue_tasks = []
    due_today_tasks = []
    upcoming_tasks = []
    completed_tasks = []

    lookahead_date = today + timedelta(days=7)

    for milestone in milestones:
        if milestone.is_completed:
            if milestone.actual_date and milestone.actual_date >= today - timedelta(days=7):
                completed_tasks.append(milestone)
            continue

        if milestone.planned_date and milestone.planned_date < today:
            overdue_tasks.append(milestone)
        elif milestone.planned_date == today:
            due_today_tasks.append(milestone)
        elif milestone.planned_date and milestone.planned_date <= lookahead_date:
            upcoming_tasks.append(milestone)
        else:
            upcoming_tasks.append(milestone)

    def _build_task_card(milestone, icon, status_hint):
        planned = milestone.planned_date.strftime("%Y-%m-%d") if milestone.planned_date else "待定"
        completion = f"完成率 {milestone.completion_rate}%" if milestone.completion_rate else "尚未更新进度"
        url = f"{reverse('production_pages:project_detail', args=[milestone.project_id])}?tab=progress&milestone={milestone.id}"
        return {
            "icon": icon,
            "label": f"{milestone.project.project_number} · {milestone.name}",
            "description": f"{status_hint} · 计划 {planned} · {completion}",
            "url": url,
            "link_label": "查看任务 →",
        }

    summary_cards = []

    sections = []
    if overdue_tasks:
        overdue_items = []
        for task in overdue_tasks[:8]:
            if task.planned_date:
                days = (today - task.planned_date).days
                status_message = f"已逾期 {days} 天" if days > 0 else "已逾期"
            else:
                status_message = "已逾期"
            overdue_items.append(_build_task_card(task, "⏰", status_message))
        sections.append({
            "title": "逾期任务",
            "description": "计划日期已过但尚未完成的任务，请优先处理。",
            "items": overdue_items,
        })

    if due_today_tasks:
        sections.append({
            "title": "今日到期",
            "description": "今天截止的任务，建议立即跟进。",
            "items": [
                _build_task_card(task, "📌", "今日到期")
                for task in due_today_tasks[:8]
            ],
        })

    if upcoming_tasks:
        upcoming_items = []
        for task in upcoming_tasks[:8]:
            if task.planned_date:
                days = (task.planned_date - today).days
                status_message = f"剩余 {days} 天" if days > 0 else "即将到期"
            else:
                status_message = "待安排计划"
            upcoming_items.append(_build_task_card(task, "🗂", status_message))
        sections.append({
            "title": "即将到期",
            "description": "未来 7 天内到期的任务，提前做好准备。",
            "items": upcoming_items,
        })

    if completed_tasks:
        sections.append({
            "title": "最近完成",
            "description": "最近 7 天完成的任务，注意做好经验沉淀与复盘。",
            "items": [
                _build_task_card(task, "✅", f"完成于 {task.actual_date.strftime('%Y-%m-%d')}" if task.actual_date else "已完成")
                for task in completed_tasks[:8]
            ],
        })

    if not sections:
        sections.append({
            "title": "任务概览",
            "description": "当前尚无分配给您的项目里程碑任务。",
            "items": [
                {
                    "icon": "🎉",
                    "label": "暂无任务",
                    "description": "近期没有需要处理的任务，您可以关注项目动态或创建新的协作事项。",
                    "url": reverse("production_pages:project_list"),
                    "link_label": "前往项目总览 →",
                }
            ],
        })

    context = _build_context(
        "任务看板",
        "🗂",
        "集中查看个人与团队任务，聚焦逾期、当日与即将到期的项目里程碑。",
        summary_cards=summary_cards,
        sections=sections,
        request=request,
        active_menu_id='task_board',
    )
    return render(request, "task_collaboration/home.html", context)


@login_required
def collaboration_workspace(request):
    context = _build_context(
        "协作空间",
        "🤝",
        "沉淀跨部门协作讨论、会议纪要与决策留痕，实现对外对内统一协同。",
        summary_cards=[
            {"label": "活跃讨论", "value": "0", "hint": "最近 7 天活跃的协作议题"},
            {"label": "会议纪要", "value": "0", "hint": "记录在案的会议纪要数量"},
            {"label": "外部协作方", "value": "0", "hint": "参与项目的外部合作单位数量"},
            {"label": "最新更新", "value": "--", "hint": "最近一次协作动态更新时间"},
        ],
        sections=[
            {
                "title": "协作功能",
                "description": "分主题管理讨论、会议与任务跟进。",
                "items": [
                    {
                        "label": "建立协作专题",
                        "description": "为项目或任务创建独立协作空间。",
                        "url": "#",
                        "icon": "🗂",
                    },
                    {
                        "label": "会议安排",
                        "description": "安排会议并同步通知参会人。",
                        "url": "#",
                        "icon": "🗓",
                    },
                    {
                        "label": "纪要归档",
                        "description": "在线编辑并归档会议纪要。",
                        "url": "#",
                        "icon": "📝",
                    },
                ],
            }
        ],
        request=request,
        active_menu_id='workspace',
    )
    return render(request, "task_collaboration/home.html", context)


@login_required
def process_engine(request):
    context = _build_context(
        "流程引擎",
        "🛠",
        "统一设计和配置业务流程模板，支撑任务审批、意见流转与项目里程碑控制。",
        summary_cards=[
            {"label": "流程模板", "value": "0", "hint": "当前启用的流程模板数量"},
            {"label": "运行流程", "value": "0", "hint": "正在执行的流程实例"},
            {"label": "审批平均耗时", "value": "--", "hint": "近 30 日审批平均时长"},
            {"label": "异常流程", "value": "0", "hint": "等待处理的异常流程"},
        ],
        sections=[
            {
                "title": "流程工具",
                "description": "构建标准化审批与协作流程。",
                "items": [
                    {
                        "label": "流程模板库",
                        "description": "维护标准流程模板与节点配置。",
                        "url": "#",
                        "icon": "📚",
                    },
                    {
                        "label": "流程监控",
                        "description": "实时跟踪流程运行状态与瓶颈。",
                        "url": "#",
                        "icon": "📡",
                    },
                    {
                        "label": "异常处理",
                        "description": "快速定位并处理流程异常。",
                        "url": "#",
                        "icon": "🚨",
                    },
                ],
            }
        ],
        request=request,
        active_menu_id='process_engine',
    )
    return render(request, "task_collaboration/home.html", context)


@login_required
def timesheet(request):
    context = _build_context(
        "工时填报",
        "⏱",
        "统一管理人员工时填报、审核与统计，支撑项目成本与效率分析。",
        summary_cards=[
            {"label": "本周填报", "value": "0", "hint": "本周已填报工时的人员数量"},
            {"label": "待审核", "value": "0", "hint": "需要审批的工时记录"},
            {"label": "总工时", "value": "--", "hint": "近 30 日累计工时"},
            {"label": "核准率", "value": "--", "hint": "工时审核通过占比"},
        ],
        sections=[
            {
                "title": "工时流程",
                "description": "收集、审核并导出工时数据。",
                "items": [
                    {
                        "label": "填报入口",
                        "description": "进入个人工时填报界面。",
                        "url": "#",
                        "icon": "📝",
                    },
                    {
                        "label": "工时审核",
                        "description": "审批、驳回或调整提交的工时。",
                        "url": "#",
                        "icon": "✅",
                    },
                    {
                        "label": "统计报表",
                        "description": "分析团队投入与项目效率。",
                        "url": "#",
                        "icon": "📈",
                    },
                ],
            }
        ],
        request=request,
        active_menu_id='timesheet',
    )
    return render(request, "task_collaboration/home.html", context)


@login_required
def message_center(request):
    context = _build_context(
        "消息中心",
        "💬",
        "统一管理系统通知、协作提醒与审批消息，支持分类筛选与阅读确认。",
        summary_cards=[
            {"label": "未读通知", "value": "0", "hint": "等待处理的通知消息"},
            {"label": "审批提醒", "value": "0", "hint": "需要审批的流程提醒"},
            {"label": "协作动态", "value": "0", "hint": "协作空间的实时更新"},
            {"label": "订阅频道", "value": "--", "hint": "已订阅的消息频道数量"},
        ],
        sections=[
            {
                "title": "消息分类",
                "description": "按类型查看并处理消息。",
                "items": [
                    {
                        "label": "系统通知",
                        "description": "系统运营提示与公告。",
                        "url": "#",
                        "icon": "📢",
                    },
                    {
                        "label": "审核提醒",
                        "description": "待审批事项快速入口。",
                        "url": "#",
                        "icon": "🧾",
                    },
                    {
                        "label": "协作消息",
                        "description": "来自协作空间的讨论动态。",
                        "url": "#",
                        "icon": "🤝",
                    },
                ],
            }
        ],
        request=request,
        active_menu_id='message_center',
    )
    return render(request, "task_collaboration/home.html", context)

