from datetime import timedelta

from django.shortcuts import render, redirect
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from django.contrib.auth import login, logout, authenticate
from django.contrib import messages
from django.db.models import Sum, Q
from django.utils import timezone
from django.urls import reverse, NoReverseMatch

from backend.apps.project_center.models import Project, ProjectMilestone, ProjectTeamNotification, ProjectTask
from backend.apps.project_center.views_pages import _user_matches_role
from backend.apps.system_management.services import get_user_permission_codes


def _permission_granted(required_code, user_permissions: set) -> bool:
    if not required_code:
        return True
    # 检查是否有所有权限
    if '__all__' in user_permissions:
        return True
    if required_code in user_permissions:
        return True
    if isinstance(required_code, str) and required_code.endswith('.view_assigned'):
        return required_code.replace('view_assigned', 'view_all') in user_permissions
    return False

HOME_ACTION_DEFINITIONS = [
    {
        "id": "project_create",
        "label": "新建项目",
        "icon": "➕",
        "url_name": "project_pages:project_create",
        "permission": "project_center.create",
    },
    {
        "id": "project_monitor",
        "label": "项目监控",
        "icon": "📊",
        "url_name": "project_pages:project_list",
        "permission": "project_center.view_all",
    },
    {
        "id": "schedule_meeting",
        "label": "安排会议",
        "icon": "🗓",
        "url_name": None,
        "permission": "task_collaboration.assign",
    },
]

HOME_NAV_STRUCTURE = [{'label': '项目中心',
  'icon': '📊',
  'permission': 'project_center.view_assigned',
  'children': [{'label': '项目总览',
                'url_name': 'project_pages:project_list',
                'permission': 'project_center.view_assigned'},
               {'label': '项目立项', 'url_name': 'project_pages:project_initiation_list', 'permission': 'project_center.create'},
               {'label': '项目创建', 'url_name': 'project_pages:project_create', 'permission': 'project_center.create'},
               {'label': '团队配置', 'url_name': 'project_pages:project_list', 'permission': 'project_center.configure_team'},
               {'label': '项目监控', 'url_name': 'project_pages:project_monitor', 'permission': 'project_center.monitor'},
               {'label': '项目档案', 'url_name': 'project_pages:project_list', 'permission': 'project_center.archive'}]},
 {'label': '生产中心',
  'icon': '🏭',
  'permission': None,
  'children': [{'label': '生产启动', 'url_name': 'production_quality_pages:production_startup_list', 'permission': None},
               {'label': '意见填报', 'url_name': 'production_quality_pages:opinion_create', 'permission': None},
               {'label': '质量审核',
                'url_name': 'production_quality_pages:opinion_review',
                'permission': 'production_quality.professional_review'},
               {'label': '报告生成',
                'url_name': 'production_quality_pages:report_generate',
                'permission': 'production_quality.generate_report'},
               {'label': '生产统计',
                'url_name': 'production_quality_pages:production_stats',
                'permission': 'production_quality.view_statistics'}]},
 {'label': '商务中心',
  'icon': '💼',
  'permission': 'customer_success.view',
  'children': [{'label': '客户管理', 'url_name': 'business_pages:customer_management', 'permission': 'customer_success.manage'},
               {'label': '合同管理', 'url_name': 'business_pages:contract_management', 'permission': 'customer_success.manage'},
               {'label': '项目结算', 'url_name': 'business_pages:project_settlement', 'permission': 'settlement_center.initiate'},
               {'label': '产值分析', 'url_name': 'business_pages:output_analysis', 'permission': 'settlement_center.view_analysis'},
               {'label': '收款跟踪', 'url_name': 'business_pages:payment_tracking', 'permission': 'settlement_center.manage_finance'}]},
 {'label': '协作中心',
  'icon': '🤝',
  'permission': 'task_collaboration.execute',
  'children': [{'label': '协作空间', 'url_name': 'collaboration_pages:workspace', 'permission': 'task_collaboration.assign'},
               {'label': '流程引擎', 'url_name': 'collaboration_pages:process_engine', 'permission': 'task_collaboration.manage'},
               {'label': '工时填报',
                'url_name': 'collaboration_pages:timesheet',
                'permission': 'task_collaboration.audit_timesheet'},
               {'label': '消息中心', 'url_name': 'collaboration_pages:message_center', 'permission': 'task_collaboration.assign'}]},
 {'label': '知识中心',
  'icon': '📚',
  'permission': 'resource_center.view',
  'children': [{'label': '标准规范库',
                'url_name': 'resource_standard:standard_list',
                'permission': 'resource_center.manage_library'},
               {'label': '报告模板库',
                'url_name': 'resource_standard:report_template_list',
                'permission': 'resource_center.manage_library'},
               {'label': '知识案例库', 'url_name': 'resource_standard:risk_case_list', 'permission': 'resource_center.view'},
               {'label': '专业分类库',
                'url_name': 'resource_standard:professional_category_list',
                'permission': 'resource_center.data_maintenance'}]}]


def _serialize_task_for_home(task):
    project = task.project
    project_number = project.project_number if project else ''
    project_name = project.name if project else '关联项目'
    
    # 根据任务类型设置跳转URL
    url = '#'
    if project:
        if task.task_type == 'project_complete_info':
            # 完善项目信息 -> 跳转到项目信息完善页面
            url = reverse('project_pages:project_complete', args=[project.id])
        elif task.task_type == 'configure_team':
            # 配置项目团队 -> 跳转到团队配置页面
            url = reverse('project_pages:project_team', args=[project.id])
        else:
            # 其他任务 -> 跳转到项目详情页面
            url = reverse('project_pages:project_detail', args=[project.id])
    
    return {
        'id': task.id,
        'title': task.title,
        'project_name': project_name,
        'project_number': project_number,
        'status': task.status,
        'status_label': task.get_status_display(),
        'due_time': task.due_time,
        'completed_time': getattr(task, 'completed_time', None),
        'description': task.description,
        'url': url,
    }


def home(request):
    """系统首页"""
    if not request.user.is_authenticated:
        return redirect('login')
    # 登录后不再强制进入资料完善页面，直接进入工作台

    try:
        user = request.user
        today = timezone.now().date()
        week_ahead = today + timedelta(days=7)

        # 使用 try-except 包裹所有数据库查询，避免数据库连接问题导致页面崩溃
        try:
            task_queryset = ProjectTask.objects.filter(
                status__in=ProjectTask.ACTIVE_STATUSES
            ).select_related(
                'project',
                'project__project_manager',
                'project__business_manager',
                'project__client_leader',
                'project__design_leader',
                'assigned_to',
            ).prefetch_related('project__team_members', 'project__team_members__user').order_by('due_time', 'created_time')
        except Exception as e:
            import logging
            logger = logging.getLogger(__name__)
            logger.error('查询任务列表失败: %s', str(e))
            # 使用空查询集，避免后续代码出错
            task_queryset = ProjectTask.objects.none()

        user_active_tasks = []
        for task in task_queryset:
            try:
                project = task.project
                if task.assigned_to_id == user.id or _user_matches_role(user, project, task.assigned_role):
                    user_active_tasks.append(task)
            except Exception:
                # 跳过有问题的任务，继续处理下一个
                continue

        # 查找已完成的任务：分配给当前用户的任务，或者由当前用户完成的任务
        try:
            recent_completed_tasks = ProjectTask.objects.filter(
                status='completed',
            ).filter(
                Q(assigned_to=user) | Q(completed_by=user)
            ).select_related('project', 'assigned_to', 'completed_by').order_by('-completed_time')[:5]
        except Exception as e:
            import logging
            logger = logging.getLogger(__name__)
            logger.error('查询已完成任务失败: %s', str(e))
            recent_completed_tasks = ProjectTask.objects.none()

        due_today_tasks = [
            task for task in user_active_tasks
            if task.due_time and task.due_time.date() == today
        ]
        overdue_tasks = [
            task for task in user_active_tasks
            if task.due_time and task.due_time.date() < today
        ]

        task_board = {
            'pending': [_serialize_task_for_home(t) for t in user_active_tasks if t.status == 'pending'][:4],
            'in_progress': [_serialize_task_for_home(t) for t in user_active_tasks if t.status == 'in_progress'][:4],
            'completed': [_serialize_task_for_home(t) for t in recent_completed_tasks],
        }
        task_counts = {
            'total': len(user_active_tasks),
            'due_today': len(due_today_tasks),
            'overdue': len(overdue_tasks),
        }

        # 所有数据库查询都包装在 try-except 中
        try:
            projects_all = Project.objects.all()
            project_total = projects_all.count()
            project_in_progress = projects_all.filter(status='in_progress').count()
            project_completed = projects_all.filter(status='completed').count()
            project_waiting = projects_all.filter(status__in=['waiting_start', 'configuring']).count()

            user_projects = projects_all.filter(
                Q(project_manager=request.user) | Q(team_members__user=request.user, team_members__is_active=True)
            ).distinct()
            my_projects_count = user_projects.count()

            user_milestones = ProjectMilestone.objects.filter(project__in=user_projects)
            pending_milestones = user_milestones.filter(is_completed=False)
            due_today = pending_milestones.filter(planned_date=today)
            overdue = pending_milestones.filter(planned_date__lt=today)
            upcoming = pending_milestones.filter(planned_date__gte=today, planned_date__lte=week_ahead)
        except Exception as e:
            import logging
            logger = logging.getLogger(__name__)
            logger.error('查询项目数据失败: %s', str(e))
            # 设置默认值，避免后续代码出错
            projects_all = Project.objects.none()
            project_total = 0
            project_in_progress = 0
            project_completed = 0
            project_waiting = 0
            user_projects = Project.objects.none()
            my_projects_count = 0
            user_milestones = ProjectMilestone.objects.none()
            pending_milestones = ProjectMilestone.objects.none()
            due_today = ProjectMilestone.objects.none()
            overdue = ProjectMilestone.objects.none()
            upcoming = ProjectMilestone.objects.none()

        project_cards = []
        try:
            for project in user_projects.order_by('-updated_time')[:4]:
                try:
                    milestones = ProjectMilestone.objects.filter(project=project)
                    total = milestones.count()
                    completed = milestones.filter(is_completed=True).count()
                    progress = int(completed / total * 100) if total else 0
                    project_cards.append({
                        'id': project.id,
                        'number': project.project_number,
                        'name': project.name,
                        'manager': project.project_manager.get_full_name() if project.project_manager else '待分配',
                        'business_manager': project.business_manager.get_full_name() if project.business_manager else '待分配',
                        'progress': progress,
                        'status_display': project.get_status_display(),
                    })
                except Exception:
                    continue
        except Exception as e:
            import logging
            logger = logging.getLogger(__name__)
            logger.error('构建项目卡片失败: %s', str(e))

        user_roles = request.user.roles.prefetch_related("custom_permissions")
        # 使用 get_user_permission_codes 来正确处理 __all__ 权限
        user_permissions = get_user_permission_codes(request.user)
        user_role_label = request.user.position or next(
            (role.name for role in user_roles if role.name),
            "角色未配置",
        )

        lead_projects = user_projects.filter(project_manager=request.user)
        lead_project_cards = []
        try:
            for project in lead_projects.order_by('-updated_time')[:4]:
                risk_level = '良好'
                if project.status == 'suspended':
                    risk_level = '暂停'
                elif project.status in ['waiting_start', 'configuring']:
                    risk_level = '待开工'
                lead_project_cards.append({
                    'id': project.id,
                    'number': project.project_number,
                    'name': project.name,
                    'status': project.get_status_display(),
                    'risk': risk_level,
                    'progress': min(100, max(0, ProjectMilestone.objects.filter(project=project, is_completed=True).count() * 20)),
                })
        except Exception:
            pass  # 如果没有项目，保持空列表

        kanban = {
            'todo': user_projects.filter(status__in=['waiting_start', 'configuring'])[:5],
            'in_progress': user_projects.filter(status='in_progress')[:5],
            'done': user_projects.filter(status__in=['completed', 'archived'])[:5],
        }

        activities = []
        try:
            for milestone in user_milestones.order_by('-actual_date', '-planned_date')[:5]:
                activities.append({
                    'icon': '📁' if milestone.is_completed else '🗂',
                    'title': f"{milestone.project.project_number} · {milestone.name}",
                    'description': '里程碑已完成' if milestone.is_completed else '待完成里程碑',
                    'time': milestone.actual_date.strftime('%Y-%m-%d') if milestone.actual_date else (milestone.planned_date.strftime('%Y-%m-%d') if milestone.planned_date else '待定'),
                })
        except Exception:
            pass

        schedule_items = []
        try:
            for milestone in upcoming.order_by('planned_date')[:4]:
                schedule_items.append({
                    'time': milestone.planned_date.strftime('%m-%d') if milestone.planned_date else '待定',
                    'title': milestone.name,
                    'project': milestone.project.name,
                })
        except Exception:
            pass

        centers_navigation = []
        for section in HOME_NAV_STRUCTURE:
            if not _permission_granted(section["permission"], user_permissions):
                continue
            children = []
            for child in section["children"]:
                permission = child.get("permission")
                if permission and not _permission_granted(permission, user_permissions):
                    continue
                url = child.get("url")
                if not url:
                    url_name = child.get("url_name")
                    if url_name:
                        try:
                            url = reverse(url_name)
                        except NoReverseMatch:
                            url = '#'
                    else:
                        url = '#'
                # 已移除系统管理、交付中心、行政管理模块（但保留在home页侧边栏的链接）
                url_name = child.get("url_name")
                # 跳过已移除的模块（仅从顶部导航菜单移除，侧边栏链接保留）
                if url_name and (url_name.startswith('system_pages:') or 
                                 url_name.startswith('delivery_pages:') or
                                 url_name.startswith('admin_pages:')):
                    continue
                
                # 移除所有二级子菜单
                child_payload = {
                    "label": child["label"],
                    "url": url,
                    "subitems": [],  # 清空二级子菜单
                }
                children.append(child_payload)
            if not children:
                continue
            centers_navigation.append({
                "label": section["label"],
                "icon": section["icon"],
                "items": children,
            })

        quick_actions = []
        for action in HOME_ACTION_DEFINITIONS:
            if action["permission"] not in user_permissions:
                continue
            
            # 新建项目仅对商务经理可见
            if action.get("id") == "project_create":
                has_business_manager_role = user.roles.filter(code='business_manager').exists()
                if not has_business_manager_role:
                    continue
            
            url = '#'
            if action.get("url_name"):
                try:
                    url = reverse(action["url_name"])
                except NoReverseMatch:
                    url = '#'
            
            quick_actions.append({
                "label": action["label"],
                "icon": action["icon"],
                "url": url,
            })

        try:
            notifications_qs = ProjectTeamNotification.objects.filter(
                recipient=user,
            ).select_related('project').order_by('is_read', '-created_time')[:20]
        except Exception:
            notifications_qs = ProjectTeamNotification.objects.none()

        notification_center = []
        if notifications_qs:
            team_items = []
            quality_items = []
            team_unread = 0
            quality_unread = 0

            def _build_entry(notification_obj):
                project = notification_obj.project
                context_data = notification_obj.context or {}
                base_url = '#'
                if project:
                    # 项目立项相关通知，使用立项详情页
                    if context_data.get('action') in {'pending_receive', 'received', 'rejected'} or '项目立项' in notification_obj.title:
                        base_url = reverse('project_pages:project_initiation_detail', args=[project.id])
                    elif context_data.get('action') in {'project_received', 'assigned_project_manager'} and project.status in {'waiting_receive', 'configuring'} and notification_obj.recipient.roles.filter(code='project_manager').exists():
                        base_url = reverse('project_pages:project_complete', args=[project.id])
                    else:
                        base_url = reverse('project_pages:project_detail', args=[project.id])
                link_url = notification_obj.action_url or base_url
                return {
                    'id': notification_obj.id,
                    'title': notification_obj.title,
                    'subtitle': project.project_number if project else '',
                    'detail': notification_obj.message,
                    'is_unread': not notification_obj.is_read,
                    'url': link_url,
                }

            for notif in notifications_qs:
                entry = _build_entry(notif)
                if notif.category == 'quality_alert':
                    if entry['is_unread']:
                        quality_unread += 1
                    if len(quality_items) < 6:
                        quality_items.append(entry)
                else:
                    if entry['is_unread']:
                        team_unread += 1
                    if len(team_items) < 6:
                        team_items.append(entry)

            if quality_items:
                notification_center.append({
                    'title': '质量提醒',
                    'icon': '⚠️',
                    'unread_count': quality_unread,
                    'items': quality_items,
                })

            if team_items:
                notification_center.append({
                    'title': '团队通知',
                    'icon': '👥',
                    'unread_count': team_unread,
                    'items': team_items,
                })
            if 'task_collaboration.execute' in user_permissions:
                todo_tasks = kanban['todo'][:3]
                task_board_url = reverse('collaboration_pages:task_board')
                task_items = []
                for task in todo_tasks:
                    task_items.append({
                        'title': task.name,
                        'subtitle': task.project_number,
                        'detail': task.get_status_display() if hasattr(task, 'get_status_display') else task.status,
                        'url': f"{task_board_url}?project={task.id}",
                    })
                notification_center.append({
                    'title': '任务提醒',
                    'icon': '✅',
                    'items': task_items,
                })

        if upcoming:
            notification_center.append({
                'title': '里程碑提醒',
                'icon': '🗂',
                'items': [
                    {
                        'title': milestone.project.name if milestone.project else '未知项目',
                        'subtitle': milestone.name,
                        'detail': milestone.planned_date.strftime('%m-%d') if milestone.planned_date else '待定',
                    }
                    for milestone in upcoming[:4]
                ],
            })

        is_technical_manager = user.roles.filter(code='technical_manager').exists() or user.is_superuser
        if is_technical_manager:
            try:
                waiting_receive_qs = Project.objects.filter(
                    status='waiting_receive',
                    project_manager__isnull=True,
                ).order_by('created_time')[:6]
                if waiting_receive_qs.exists():
                    items = []
                    for proj in waiting_receive_qs:
                        items.append({
                            'title': proj.project_number or proj.name,
                            'subtitle': proj.name,
                            'detail': f"商务经理：{proj.business_manager.get_full_name() if proj.business_manager else '未指定'}",
                            'url': reverse('project_pages:project_receive', args=[proj.id]),
                            'is_unread': True,
                        })
                    notification_center.append({
                        'title': '项目待接收',
                        'icon': '📬',
                        'unread_count': waiting_receive_qs.count(),
                        'items': items,
                    })
            except Exception:
                pass

        this_month_start = today.replace(day=1)
        milestones_completed = user_milestones.filter(is_completed=True, actual_date__gte=this_month_start).count()
        data_cards = {
            'personal': {
                'title': '个人指标',
                'value': f"本月完成任务 {milestones_completed}",
                'extra': f"逾期 {overdue.count()} · 待办 {pending_milestones.count()}",
            },
            'team': {
                'title': '团队指标',
                'value': f"管理项目 {lead_projects.count()}",
                'extra': f"参与项目 {user_projects.count()} · 进行中 {user_projects.filter(status='in_progress').count()}",
            },
            'company': {
                'title': '公司指标',
                'value': f"项目总数 {project_total}",
                'extra': f"在建 {project_in_progress} · 已完成 {project_completed}",
            },
        }

        nav_sections = [
            {
                'title': None,
                'items': [
                    {'label': '我的工作台', 'icon': '🧰', 'url': reverse('home'), 'active': True},
                ]
            }
        ]
        for section in centers_navigation:
            module_entries = []
            for module in section['items']:
                subgroups = []
                for sub in module.get('subitems', []):
                    if isinstance(sub, dict):
                        subgroups.append(
                            {
                                'label': sub.get('label', '功能开发中'),
                                'url': sub.get('url', '#'),
                                'subitems': sub.get('subitems', []),
                            }
                        )
                    else:
                        subgroups.append(
                            {
                                'label': str(sub),
                                'url': module.get('url', '#'),
                                'subitems': [],
                            }
                        )
                module_entries.append(
                    {
                        'label': module['label'],
                        'url': module.get('url', '#'),
                        'subitems': subgroups,
                    }
                )
            if module_entries:
                nav_sections.append({
                    'title': section['label'],
                    'items': module_entries,
                    'icon': section['icon'],
                })

        stats_cards = [
            {
                'label': '项目总数',
                'value': project_total,
                'trend': f'进行中 {project_in_progress} · 已完成 {project_completed}',
                'variant': 'default'
            },
            {
                'label': '待办任务',
                'value': pending_milestones.count(),
                'trend': f'今日 {due_today.count()} · 逾期 {overdue.count()}',
                'variant': 'warning'
            },
            {
                'label': '风险项目',
                'value': project_waiting,
                'trend': '需关注开工与配置进度',
                'variant': 'danger'
            },
            {
                'label': '今日里程碑',
                'value': due_today.count(),
                'trend': f"剩余 {pending_milestones.count()} 个待办",
                'variant': 'success'
            },
            {
                'label': '参与项目',
                'value': my_projects_count,
                'trend': f'管理中 {lead_projects.count()}',
                'variant': 'default'
            },
        ]

        announcements = [
            {'title': '生产系统 1.3.0 版本上线', 'content': '新增项目总览仪表盘、自定义权限模板等功能。', 'date': today.strftime('%Y-%m-%d')},
            {'title': '12 月安全生产月', 'content': '请各项目部及时提交安全排查报告。', 'date': (today - timedelta(days=1)).strftime('%Y-%m-%d')},
        ]

        
        context = {
            'nav_sections': nav_sections,
            'stats_cards': stats_cards,
            'kanban': kanban,
            'project_cards': project_cards,
            'lead_project_cards': lead_project_cards,
            'pending_counts': {
                'personal': task_counts['total'],
                'due_today': task_counts['due_today'],
                'overdue': task_counts['overdue'],
            },
            'project_counts': {
                'total': project_total,
                'in_progress': project_in_progress,
                'completed': project_completed,
                'waiting': project_waiting,
            },
            'my_projects_count': my_projects_count,
            'lead_projects_count': lead_projects.count(),
            'activities': activities,
            'schedule_items': schedule_items,
            'announcements': announcements,
            'status_bar': {
                'online_users': 18,
                'uptime_hours': 168,
                'last_sync': '5 分钟前',
            },
            'quick_actions': quick_actions,
            'notification_center': notification_center,
            'data_cards': data_cards,
            'user_role_label': user_role_label,
            'task_board': task_board,
            'task_counts': task_counts,
        }

        return render(request, 'home.html', context)
    except Exception as e:
        import logging
        logger = logging.getLogger(__name__)
        logger.exception('首页加载失败: %s', str(e))
        # 返回一个简化的错误页面，而不是 500 错误
        from django.http import HttpResponseServerError
        return HttpResponseServerError(f'<h1>页面加载错误</h1><p>请联系管理员。错误信息：{str(e)}</p>')


def login_view(request):
    """登录页面"""
    if request.user.is_authenticated:
        return redirect('home')

    if request.method == 'POST':
        username = request.POST.get('username')
        password = request.POST.get('password')

        if username and password:
            user = authenticate(request, username=username, password=password)
            if user:
                if user.is_active:
                    login(request, user)
                    if not user.profile_completed:
                        return redirect('complete_profile')
                    next_url = request.GET.get('next', 'home')
                    return redirect(next_url)
                else:
                    messages.error(request, '用户账户已被禁用')
            else:
                messages.error(request, '用户名或密码错误')
        else:
            messages.error(request, '请输入用户名和密码')

    return render(request, 'login.html')


def logout_view(request):
    """登出页面"""
    logout(request)
    messages.success(request, '您已成功退出登录')
    return redirect('login')


@csrf_exempt
def health_check(request):
    """健康检查端点"""
    return JsonResponse({
        'status': 'healthy',
        'service': '维海科技信息化管理平台',
        'version': '1.0.0',
        'timestamp': '2025-11-06T14:01:28Z'
    })
