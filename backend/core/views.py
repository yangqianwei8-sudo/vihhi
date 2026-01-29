from datetime import timedelta, datetime
import json

from django.shortcuts import render, redirect

# 构建探针标识（用于验证代码版本）
BUILD_PROBE = "HOME_HDR_PROBE_20260113_1"
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from django.contrib.auth import login, logout, authenticate
from django.contrib import messages
from django.db.models import Sum, Q
from django.utils import timezone
from django.urls import reverse, NoReverseMatch

# 注意：Project, ProjectTask 等模型改为延迟导入，避免在数据库表不存在时导致模块加载失败
# from backend.apps.project_center.models import Project, ProjectMilestone, ProjectTeamNotification, ProjectTask
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
    
    # 权限继承机制：manage 权限自动包含子权限
    # plan.manage 自动包含 plan.create、plan.edit、plan.delete
    if required_code == 'plan_management.plan.create' or \
       required_code == 'plan_management.plan.edit' or \
       required_code == 'plan_management.plan.delete':
        if 'plan_management.plan.manage' in user_permissions:
            return True
    
    # goal.manage 自动包含 goal.create、goal.edit、goal.delete、goal.decompose
    if required_code == 'plan_management.goal.create' or \
       required_code == 'plan_management.goal.edit' or \
       required_code == 'plan_management.goal.delete' or \
       required_code == 'plan_management.goal.decompose':
        if 'plan_management.goal.manage' in user_permissions or \
           'plan_management.manage_goal' in user_permissions:
            return True
    
    # 审批权限兼容性：approve_plan 和 approve 等同于 plan.approve_decision
    if required_code == 'plan_management.plan.approve_decision':
        if 'plan_management.plan.approve_decision' in user_permissions or \
           'plan_management.approve_plan' in user_permissions or \
           'plan_management.approve' in user_permissions:
            return True
    if required_code == 'plan_management.approve_plan' or required_code == 'plan_management.approve':
        if 'plan_management.plan.approve_decision' in user_permissions or \
           'plan_management.approve_plan' in user_permissions or \
           'plan_management.approve' in user_permissions:
            return True
    
    # 特殊处理：计划管理模块的权限检查
    # 如果要求 plan_management.view，但用户有审批权限或业务权限，也允许显示菜单
    if required_code == 'plan_management.view':
        # 检查是否有任何计划管理相关权限（包括审批权限和业务权限）
        plan_permissions = [
            'plan_management.view',  # 标准权限（菜单系统使用）
            'plan_management.approve',
            'plan_management.approve_plan',
            'plan_management.plan.approve_decision',
            'plan_management.plan.view',  # 业务权限（查看计划）
            'plan_management.goal.view',  # 业务权限（查看目标）
        ]
        for perm in plan_permissions:
            if perm in user_permissions:
                return True
    
    # 特殊处理：plan_management.plan.view 权限检查
    # 如果要求 plan_management.plan.view，也接受 plan_management.view（更宽泛的权限）
    if required_code == 'plan_management.plan.view':
        if 'plan_management.plan.view' in user_permissions:
            return True
        if 'plan_management.view' in user_permissions:
            return True
    
    # 特殊处理：plan_management.goal.view 权限检查
    # 如果要求 plan_management.goal.view，也接受 plan_management.view（更宽泛的权限）
    if required_code == 'plan_management.goal.view':
        if 'plan_management.goal.view' in user_permissions:
            return True
        if 'plan_management.view' in user_permissions:
            return True
    
    return False

HOME_ACTION_DEFINITIONS = [
    {
        "id": "project_create",
        "label": "新建项目",
        "icon": "➕",
        "url_name": "production_pages:project_create",
        "permission": "production_management.create",
    },
    {
        "id": "project_monitor",
        "label": "项目监控",
        "icon": "📊",
        "url_name": "production_pages:project_list",
        "permission": "production_management.view_all",
    },
    {
        "id": "schedule_meeting",
        "label": "安排会议",
        "icon": "🗓",
        "url_name": None,
        "permission": "task_collaboration.assign",
    },
]

# 菜单结构：直接对应home页左侧菜单，取消所有"中心"概念
HOME_NAV_STRUCTURE = [
    # 按数据库模块定义顺序排列，确保与数据库一致
    {'label': '客户管理', 'icon': '👥', 'url_name': 'customer_pages:customer_management_home_alt', 'permission': 'customer_management.client.view'},
    {'label': '商机管理', 'icon': '💼', 'url_name': 'opportunity_pages:opportunity_management_home_alt', 'permission': 'customer_management.opportunity.view'},
    {'label': '合同管理', 'icon': '📄', 'url_name': 'contract_pages:contract_management_home_alt', 'permission': 'customer_management.contract.view'},
    {'label': '回款管理', 'icon': '💰', 'url_name': 'settlement_pages:settlement_home', 'permission': 'payment_management.payment_plan.view'},  # 回款管理独立模块
    {'label': '生产管理', 'icon': '🏗️', 'url_name': 'production_pages:production_management_home', 'permission': 'production_management.view_assigned'},
    {'label': '资源管理', 'icon': '🗂️', 'url_name': 'resource_standard_pages:standard_list', 'permission': 'resource_center.view'},
    {'label': '任务协作', 'icon': '🤝', 'url_name': 'collaboration_pages:task_board', 'permission': 'task_collaboration.view'},
    {'label': '收文管理', 'icon': '📥', 'url_name': 'delivery_pages:incoming_document_home', 'permission': 'delivery_center.view'},
    {'label': '发文管理', 'icon': '📤', 'url_name': 'delivery_pages:outgoing_document_home', 'permission': 'delivery_center.view'},
    {'label': '档案管理', 'icon': '📁', 'url_name': 'archive_management:archive_management_home', 'permission': 'archive_management.view'},
    {'label': '计划管理', 'icon': '📅', 'url_name': 'plan_pages:plan_management_home', 'permission': 'plan_management.view'},
    {'label': '诉讼管理', 'icon': '⚖️', 'url_name': 'litigation_pages:litigation_management_home', 'permission': 'litigation_management.view'},
    {'label': '风险管理', 'icon': '⚠️', 'url_name': '#', 'permission': 'risk_management.view'},  # 占位，待实现
    {'label': '财务管理', 'icon': '💵', 'url_name': 'finance_pages:financial_management_home', 'permission': 'financial_management.view'},
    {'label': '人事管理', 'icon': '👤', 'url_name': 'personnel_pages:personnel_management_home', 'permission': 'personnel_management.view'},
    {'label': '行政管理', 'icon': '🏢', 'url_name': 'admin_pages:administrative_management_home', 'permission': 'administrative_management.view'},
    {'label': '审批引擎', 'icon': '✅', 'url_name': 'workflow_engine:workflow_home', 'permission': 'workflow_engine.view'},
    {'label': '系统管理', 'icon': '⚙️', 'url_name': 'system_pages:system_management_home', 'permission': 'system_management.view'},
    # 注意：权限管理仅保留在Django Admin后台管理中，不添加到前端导航栏
]


def _build_full_top_nav(permission_set, user=None):
    """构建完整的顶部导航菜单
    
    Args:
        permission_set: 用户权限集合
        user: 当前用户对象（可选）
    
    Returns:
        list: 导航菜单项列表
    """
    nav = []
    _admin = user and (getattr(user, 'username', None) == 'admin' or getattr(user, 'is_superuser', False))
    for item in HOME_NAV_STRUCTURE:
        # 仅 admin 可访问的菜单项（示例表单模块）
        if item.get('admin_only') and not _admin:
            continue
        # 检查权限
        if item.get('permission'):
            if not _permission_granted(item['permission'], permission_set):
                continue
        
        # 构建URL
        url = '#'
        if item.get('url_name'):
            try:
                url = reverse(item['url_name'])
            except NoReverseMatch:
                url = item.get('url', '#')
        else:
            url = item.get('url', '#')
        
        nav.append({
            'label': item['label'],
            'icon': item.get('icon', ''),
            'url': url,
        })
    
    return nav


# 场景分组配置
SCENE_GROUPS = [
    {
        'title': '销售与客户',
        'icon': 'fa-chart-line',
        'items': [
            {'label': '客户管理', 'icon': 'fa-users', 'url_name': 'customer_pages:customer_management_home_alt', 'permission': 'customer_management.client.view'},
            {'label': '商机管理', 'icon': 'fa-briefcase', 'url_name': 'opportunity_pages:opportunity_management_home_alt', 'permission': 'customer_management.opportunity.view'},
            {'label': '合同管理', 'icon': 'fa-file-contract', 'url_name': 'contract_pages:contract_management_home_alt', 'permission': 'customer_management.contract.view'},
            {'label': '回款管理', 'icon': 'fa-money-bill-wave', 'url_name': 'settlement_pages:settlement_home', 'permission': 'payment_management.payment_plan.view'},
        ]
    },
    {
        'title': '生产与运营',
        'icon': 'fa-industry',
        'items': [
            {'label': '生产管理', 'icon': 'fa-industry', 'url_name': 'production_pages:production_management_home', 'permission': 'production_management.view_assigned'},
            {'label': '资源管理', 'icon': 'fa-tools', 'url_name': 'resource_standard_pages:standard_list', 'permission': 'resource_center.view'},
            {'label': '任务协作', 'icon': 'fa-tasks', 'url_name': 'collaboration_pages:task_board', 'permission': 'task_collaboration.view'},
            {'label': '计划管理', 'icon': 'fa-calendar-alt', 'url_name': 'plan_pages:plan_management_home', 'permission': 'plan_management.view'},
        ]
    },
    {
        'title': '财务与人事',
        'icon': 'fa-chart-bar',
        'items': [
            {'label': '财务管理', 'icon': 'fa-chart-line', 'url_name': 'finance_pages:financial_management_home', 'permission': 'financial_management.view'},
            {'label': '人事管理', 'icon': 'fa-user-tie', 'url_name': 'personnel_pages:personnel_management_home', 'permission': 'personnel_management.view'},
        ]
    },
    {
        'title': '风控与合规',
        'icon': 'fa-shield-alt',
        'items': [
            {'label': '诉讼管理', 'icon': 'fa-gavel', 'url_name': 'litigation_pages:litigation_management_home', 'permission': 'litigation_management.view'},
            {'label': '风险管理', 'icon': 'fa-exclamation-triangle', 'url_name': '#', 'permission': 'risk_management.view'},
            {'label': '档案管理', 'icon': 'fa-archive', 'url_name': 'archive_management:archive_management_home', 'permission': 'archive_management.view'},
        ]
    },
    {
        'title': '行政与支持',
        'icon': 'fa-cogs',
        'items': [
            {'label': '行政管理', 'icon': 'fa-building', 'url_name': 'admin_pages:administrative_management_home', 'permission': 'administrative_management.view'},
            {'label': '系统管理', 'icon': 'fa-server', 'url_name': 'system_pages:system_management_home', 'permission': 'system_management.view'},
        ]
    },
]


def _build_scene_groups(permission_set, user=None):
    """构建场景分组菜单
    
    Args:
        permission_set: 用户权限集合
        user: 当前用户对象（可选）
    
    Returns:
        list: 场景分组列表，每个分组包含标题、图标和菜单项
    """
    scene_groups = []
    
    for group in SCENE_GROUPS:
        items = []
        for item in group['items']:
            # 检查权限
            if item.get('permission'):
                if not _permission_granted(item['permission'], permission_set):
                    continue
            
            # 构建URL
            url = '#'
            if item.get('url_name'):
                try:
                    url = reverse(item['url_name'])
                except NoReverseMatch:
                    url = item.get('url', '#')
            else:
                url = item.get('url', '#')
            
            items.append({
                'label': item['label'],
                'icon': item['icon'],
                'url': url,
            })
        
        # 只有当分组中有可见的菜单项时才添加该分组
        if items:
            scene_groups.append({
                'title': group['title'],
                'icon': group['icon'],
                'items': items,
                'count': len(items),
            })
    
    return scene_groups


def _serialize_task_for_home(task):
    """序列化任务对象为首页显示格式"""
    try:
        project = getattr(task, 'project', None)
        project_number = getattr(project, 'project_number', '') if project else ''
        project_name = getattr(project, 'name', '关联项目') if project else '关联项目'
        
        # 根据任务类型设置跳转URL
        url = '#'
        if project:
            try:
                task_type = getattr(task, 'task_type', None)
                if task_type == 'project_complete_info':
                    # 完善项目信息 -> 跳转到项目信息完善页面
                    url = reverse('production_pages:project_complete', args=[project.id])
                elif task_type == 'configure_team':
                    # 配置项目团队 -> 跳转到团队配置页面
                    url = reverse('production_pages:project_team', args=[project.id])
                else:
                    # 其他任务 -> 跳转到项目详情页面
                    url = reverse('production_pages:project_detail', args=[project.id])
            except (NoReverseMatch, AttributeError):
                url = '#'
        
        return {
            'id': getattr(task, 'id', None),
            'title': getattr(task, 'title', ''),
            'project_name': project_name,
            'project_number': project_number,
            'status': getattr(task, 'status', 'pending'),
            'status_label': getattr(task, 'get_status_display', lambda: '')() if hasattr(task, 'get_status_display') else '',
            'due_time': getattr(task, 'due_time', None),
            'completed_time': getattr(task, 'completed_time', None),
            'description': getattr(task, 'description', ''),
            'url': url,
        }
    except Exception as e:
        import logging
        logger = logging.getLogger(__name__)
        logger.warning(f'序列化任务失败: {e}', exc_info=True)
        # 返回一个基本的任务信息
        return {
            'id': getattr(task, 'id', None),
            'title': getattr(task, 'title', '未知任务'),
            'project_name': '未知项目',
            'project_number': '',
            'status': 'pending',
            'status_label': '',
            'due_time': None,
            'completed_time': None,
            'description': '',
            'url': '#',
        }


def home(request):
    """系统首页 - Django工作台页面"""
    import logging
    logger = logging.getLogger(__name__)
    
    try:
        from django.contrib.auth.decorators import login_required
        from django.db.models import Count, Q, Sum
        from datetime import timedelta
        
        # 如果未登录，重定向到前端登录页面
        if not request.user.is_authenticated:
            next_url = request.path
            resp = redirect(f"/login/?next={next_url}")
            resp["X-Hit-Home-View"] = "1"
            resp["X-Home-Branch"] = "redirect-frontend-login"
            resp["X-Build-Probe"] = "HOME_HDR_PROBE_20260113_1"
            return resp
        
        user = request.user

        # 获取用户权限（可能因为数据库连接失败而抛出异常）
        try:
            permission_set = get_user_permission_codes(user)
        except Exception as e:
            logger.warning(f'获取用户权限失败: {e}', exc_info=True)
            permission_set = set()  # 使用空权限集合作为默认值
        
        # 构建导航菜单（centers_navigation）
        try:
            centers_navigation = _build_full_top_nav(permission_set, user)
        except Exception as e:
            logger.warning(f'构建导航菜单失败: {e}', exc_info=True)
            centers_navigation = []
        
        # 构建场景分组菜单
        try:
            scene_groups = _build_scene_groups(permission_set, user)
        except Exception as e:
            logger.warning(f'构建场景分组菜单失败: {e}', exc_info=True)
            scene_groups = []
        
        # 初始化统计数据
        pending_counts = {'personal': 0, 'due_today': 0, 'overdue': 0}
        approval_stats = {'my_pending': 0, 'my_submitted': 0}
        delivery_stats = {'pending': 0}
        stats_cards = []
        task_board = {'pending': [], 'in_progress': [], 'completed': []}
        
        # 获取待办任务统计
        try:
            today = timezone.now().date()
            from backend.apps.production_management.models import ProjectTask
            user_tasks = ProjectTask.objects.filter(
                Q(assigned_to=user) | Q(created_by=user)
            ).exclude(status='completed')
            
            pending_counts['personal'] = user_tasks.count()
            pending_counts['due_today'] = user_tasks.filter(due_time__date=today).count()
            pending_counts['overdue'] = user_tasks.filter(due_time__lt=timezone.now()).exclude(status='completed').count()
            
            # 构建任务看板（移除限制，显示所有数据）
            pending_tasks = user_tasks.filter(status='pending')
            in_progress_tasks = user_tasks.filter(status='in_progress')
            completed_tasks = ProjectTask.objects.filter(
                Q(assigned_to=user) | Q(created_by=user),
                status='completed'
            ).order_by('-completed_time')
            
            task_board['pending'] = [_serialize_task_for_home(task) for task in pending_tasks]
            task_board['in_progress'] = [_serialize_task_for_home(task) for task in in_progress_tasks]
            task_board['completed'] = [_serialize_task_for_home(task) for task in completed_tasks]
        except Exception as e:
            logger.exception('获取任务统计失败: %s', str(e))
        
        # 获取审批统计
        try:
            from backend.apps.workflow_engine.models import ApprovalInstance
            
            approval_stats['my_pending'] = ApprovalInstance.objects.filter(
                status='pending',
                records__approver=user,
                records__result='pending'
            ).distinct().count()
            
            approval_stats['my_submitted'] = ApprovalInstance.objects.filter(
                applicant=user
            ).count()
        except Exception as e:
            logger.exception('获取审批统计失败: %s', str(e))
        
        # 获取交付统计
        try:
            from backend.apps.delivery_customer.models import DeliveryReport
            
            delivery_stats['pending'] = DeliveryReport.objects.filter(
                status='pending'
            ).count()
        except Exception as e:
            logger.exception('获取交付统计失败: %s', str(e))
        
        # 构建统计卡片
        try:
            # 进行中项目数
            try:
                from backend.apps.production_management.models import Project
                active_projects = Project.objects.filter(
                    status__in=['in_progress', 'planning']
                ).count()
                stats_cards.append({
                    'label': '进行中项目',
                    'value': active_projects,
                    'url': reverse('production_pages:project_list'),
                    'variant': 'info'
                })
            except Exception:
                pass
            
            # 本月完成项目数
            try:
                this_month = timezone.now().replace(day=1)
                completed_projects = Project.objects.filter(
                    status='completed',
                    updated_time__gte=this_month
                ).count()
                stats_cards.append({
                    'label': '本月完成',
                    'value': completed_projects,
                    'url': reverse('production_pages:project_list'),
                    'variant': 'success'
                })
            except Exception:
                pass
            
            # 待审批任务
            if approval_stats['my_pending'] > 0:
                stats_cards.append({
                    'label': '待审批',
                    'value': approval_stats['my_pending'],
                    'url': reverse('workflow_engine:approval_list') + '?status=pending',
                    'variant': 'danger'
                })
            
            # 待处理事项
            try:
                from backend.apps.administrative_management.models import AdministrativeAffair
                pending_affairs = AdministrativeAffair.objects.filter(
                    status='pending',
                    responsible_user=user
                ).count()
                if pending_affairs > 0:
                    stats_cards.append({
                        'label': '待处理事项',
                        'value': pending_affairs,
                        'url': reverse('admin_pages:affair_list'),
                        'variant': 'warning'
                    })
            except Exception:
                pass
        except Exception as e:
            logger.exception('构建统计卡片失败: %s', str(e))
        
        # ========== 构建核心指标卡片（类似计划管理首页） ==========
        core_cards = []
        
        # 卡片1：待办任务
        core_cards.append({
            'label': '待办任务',
            'icon': '📋',
            'value': str(pending_counts['personal']),
            'subvalue': f'今日到期 {pending_counts["due_today"]} | 已逾期 {pending_counts["overdue"]}',
            'url': '#',
            'variant': 'info'
        })
        
        # 卡片2：进行中项目
        try:
            from backend.apps.production_management.models import Project
            active_projects = Project.objects.filter(
                status__in=['in_progress', 'planning']
            ).count()
            core_cards.append({
                'label': '进行中项目',
                'icon': '🏗️',
                'value': str(active_projects),
                'subvalue': '正在执行的项目',
                'url': reverse('production_pages:project_list'),
                'variant': 'warning'
            })
        except Exception:
            pass
        
        # 卡片3：本月完成
        try:
            this_month = timezone.now().replace(day=1)
            completed_projects = Project.objects.filter(
                status='completed',
                updated_time__gte=this_month
            ).count()
            core_cards.append({
                'label': '本月完成',
                'icon': '✅',
                'value': str(completed_projects),
                'subvalue': '本月完成的项目数',
                'url': reverse('production_pages:project_list'),
                'variant': 'success'
            })
        except Exception:
            pass
        
        # 卡片4：待审批
        if approval_stats['my_pending'] > 0:
            core_cards.append({
                'label': '待审批',
                'icon': '📝',
                'value': str(approval_stats['my_pending']),
                'subvalue': '需要您审批的事项',
                'url': reverse('workflow_engine:approval_list') + '?status=pending',
                'variant': 'danger'
            })
        
        # 卡片5：待处理事项
        try:
            from backend.apps.administrative_management.models import AdministrativeAffair
            pending_affairs = AdministrativeAffair.objects.filter(
                status='pending',
                responsible_user=user
            ).count()
            if pending_affairs > 0:
                core_cards.append({
                    'label': '待处理事项',
                    'icon': '📌',
                    'value': str(pending_affairs),
                    'subvalue': '需要您处理的行政事务',
                    'url': reverse('admin_pages:affair_list'),
                    'variant': 'warning'
                })
        except Exception:
            pass
        
        # ========== 状态分布统计 ==========
        project_status_dist = {}
        task_status_dist = {}
        
        try:
            from backend.apps.production_management.models import Project
            total_projects = Project.objects.count()
            if total_projects > 0:
                for status_code in ['planning', 'in_progress', 'completed', 'cancelled']:
                    count = Project.objects.filter(status=status_code).count()
                    if count > 0:
                        status_labels = {
                            'planning': '规划中',
                            'in_progress': '执行中',
                            'completed': '已完成',
                            'cancelled': '已取消'
                        }
                        project_status_dist[status_code] = {
                            'label': status_labels.get(status_code, status_code),
                            'count': count,
                            'percentage': round(count / total_projects * 100, 1)
                        }
        except Exception:
            pass
        
        try:
            from backend.apps.production_management.models import ProjectTask
            total_tasks = ProjectTask.objects.count()
            if total_tasks > 0:
                for status_code in ['pending', 'in_progress', 'completed', 'cancelled']:
                    count = ProjectTask.objects.filter(status=status_code).count()
                    if count > 0:
                        status_labels = {
                            'pending': '待处理',
                            'in_progress': '进行中',
                            'completed': '已完成',
                            'cancelled': '已取消'
                        }
                        task_status_dist[status_code] = {
                            'label': status_labels.get(status_code, status_code),
                            'count': count,
                            'percentage': round(count / total_tasks * 100, 1)
                        }
        except Exception:
            pass
        
        # ========== 风险预警 ==========
        risk_warnings = []
        overdue_tasks_count = 0
        stale_tasks_count = 0
        
        try:
            from backend.apps.production_management.models import ProjectTask
            # 逾期任务
            overdue_tasks = ProjectTask.objects.filter(
                status__in=['pending', 'in_progress'],
                due_time__lt=timezone.now()
            ).select_related('assigned_to', 'project')[:5]
            
            overdue_tasks_count = ProjectTask.objects.filter(
                status__in=['pending', 'in_progress'],
                due_time__lt=timezone.now()
            ).count()
            
            for task in overdue_tasks:
                days = (today - task.due_time.date()).days if task.due_time else 0
                responsible = task.assigned_to.get_full_name() or task.assigned_to.username if task.assigned_to else '未分配'
                project_name = task.project.project_number if task.project else '未知项目'
                risk_warnings.append({
                    'type': 'overdue',
                    'title': f'{project_name} - {task.title}',
                    'responsible': responsible,
                    'days': days,
                    'url': f'/production/projects/{task.project.id}/' if task.project else '#'
                })
            
            # 7天未更新任务
            seven_days_ago = today - timedelta(days=7)
            stale_tasks = ProjectTask.objects.filter(
                status__in=['pending', 'in_progress'],
                updated_time__lt=timezone.make_aware(datetime.combine(seven_days_ago, datetime.min.time()))
            ).select_related('assigned_to', 'project')[:5]
            
            stale_tasks_count = ProjectTask.objects.filter(
                status__in=['pending', 'in_progress'],
                updated_time__lt=timezone.make_aware(datetime.combine(seven_days_ago, datetime.min.time()))
            ).count()
            
            for task in stale_tasks:
                days = (today - task.updated_time.date()).days
                responsible = task.assigned_to.get_full_name() or task.assigned_to.username if task.assigned_to else '未分配'
                project_name = task.project.project_number if task.project else '未知项目'
                risk_warnings.append({
                    'type': 'stale',
                    'title': f'{project_name} - {task.title}',
                    'responsible': responsible,
                    'days': days,
                    'url': f'/production/projects/{task.project.id}/' if task.project else '#'
                })
        except Exception as e:
            logger.exception('获取风险预警失败: %s', str(e))
        
        # ========== 员工风险对比数据（来源于 plan/home 的风险预警）==========
        employee_risk_data = []
        try:
            from backend.apps.system_management.models import User
            from backend.apps.plan_management.services.risk_query_service import get_responsible_risk_items
            
            # 统计所有员工：优先从 Employee 模型获取，如果没有则从 User 模型获取
            # 使用字典确保每个 user_id 只保留一个员工记录
            employee_users_dict = {}  # key: user_id, value: employee_info
            
            try:
                from backend.apps.personnel_management.models import Employee
                # 获取所有员工（不限制 status，统计全部）
                # 按 user_id 和 created_time 排序，确保每个 user_id 只保留最新的记录
                all_employees = Employee.objects.filter(
                    user__isnull=False
                ).select_related('user', 'department').order_by('user_id', '-created_time')
                
                # 使用字典来确保每个 user_id 只保留一个员工记录（保留最新的）
                for emp in all_employees:
                    if emp.user:
                        user_id = emp.user.id
                        # 如果该 user_id 还没有记录，或者当前记录更新，则更新
                        if user_id not in employee_users_dict:
                            employee_users_dict[user_id] = {
                                'user': emp.user,
                                'name': emp.name,
                                'department': emp.department.name if emp.department else '未分配部门',
                                'status': emp.status,
                            }
                        # 如果已存在，检查是否需要更新（保留最新的 Employee 记录）
                        # 由于已经按 created_time 降序排序，第一个就是最新的
                
            except Exception as e:
                logger.warning(f'从 Employee 模型获取员工失败: {e}')
            
            # 如果 Employee 模型没有数据或数据很少，则从 User 模型补充获取
            # 获取所有活跃用户（不限制 user_type，统计全部）
            all_users = User.objects.filter(is_active=True).select_related('department')
            
            for user in all_users:
                # 如果该用户还没有被添加到字典中，则添加
                if user.id not in employee_users_dict:
                    employee_users_dict[user.id] = {
                        'user': user,
                        'name': user.get_full_name() or user.username,
                        'department': user.department.name if user.department else '未分配部门',
                        'status': 'active',  # User 模型没有 status，默认为 active
                    }
            
            # 转换为列表（此时已经确保每个 user_id 只有一个记录）
            employee_users = list(employee_users_dict.values())
            
            # 验证：确保没有重复的 user_id
            user_ids_in_list = [emp_info['user'].id for emp_info in employee_users]
            if len(user_ids_in_list) != len(set(user_ids_in_list)):
                logger.error(f'警告：employee_users 列表中有重复用户！总数量: {len(user_ids_in_list)}, 去重后: {len(set(user_ids_in_list))}')
                # 强制去重
                unique_dict = {}
                for emp_info in employee_users:
                    user_id = emp_info['user'].id
                    if user_id not in unique_dict:
                        unique_dict[user_id] = emp_info
                employee_users = list(unique_dict.values())
            
            # 使用 plan/home 的风险预警服务统计每个员工的风险
            # 再次使用集合确保最终数据不重复
            processed_user_ids = set()
            
            for emp_info in employee_users:
                user = emp_info['user']
                user_name = emp_info['name']
                department_name = emp_info['department']
                
                # 防止重复处理同一个用户
                if user.id in processed_user_ids:
                    logger.warning(f'跳过重复用户: {user_name} (ID: {user.id})')
                    continue
                processed_user_ids.add(user.id)
                
                # 使用 plan/home 的风险预警服务获取该员工的风险项
                # plan/home 的逻辑：合并 owner 和 responsible_person 的风险
                try:
                    from backend.apps.plan_management.services.risk_query_service import get_user_risk_items, get_responsible_risk_items
                    
                    # 获取 owner 的风险
                    owner_risk_items = get_user_risk_items(
                        user=user,
                        limit=1000
                    )
                    
                    # 获取 responsible_person 的风险
                    responsible_risk_items = get_responsible_risk_items(
                        responsible_user=user,
                        limit=1000
                    )
                    
                    # 合并并去重（与 plan/home 逻辑完全一致）
                    all_risk_items = owner_risk_items + responsible_risk_items
                    seen_objects = set()
                    risk_items = []
                    for item in all_risk_items:
                        obj = item.get('object')
                        if obj:
                            obj_key = (item['type'], obj.id)
                            if obj_key not in seen_objects:
                                seen_objects.add(obj_key)
                                risk_items.append(item)
                    
                    # 统计风险指标
                    # 确保正确统计风险类型
                    goal_risk_count = 0
                    plan_risk_count = 0
                    for item in risk_items:
                        risk_type = item.get('type', '')
                        if risk_type == 'goal_risk':
                            goal_risk_count += 1
                        elif risk_type == 'plan_risk':
                            plan_risk_count += 1
                    total_risk_count = len(risk_items)
                    
                    # 验证：goal_risk_count + plan_risk_count 应该等于 total_risk_count
                    if goal_risk_count + plan_risk_count != total_risk_count:
                        logger.warning(f'员工 {user_name} 风险统计不一致: goal_risk={goal_risk_count}, plan_risk={plan_risk_count}, total={total_risk_count}')
                    
                    # 统计逾期天数
                    total_days_overdue = sum(item.get('days_overdue', 0) for item in risk_items)
                    avg_days_overdue = total_days_overdue / total_risk_count if total_risk_count > 0 else 0
                    
                    # 统计进度差距（实际进度与时间进度的差距）
                    total_progress_gap = 0
                    for item in risk_items:
                        actual = item.get('actual_progress', 0)
                        time_progress = item.get('time_progress', 0)
                        if time_progress > 0:
                            gap = max(0, time_progress - actual)
                            total_progress_gap += gap
                    avg_progress_gap = total_progress_gap / total_risk_count if total_risk_count > 0 else 0
                    
                    # 计算风险分数（基于风险数量和严重程度）
                    # 风险分数 = 风险数量 * 10 + 平均逾期天数 * 5 + 平均进度差距 * 2
                    total_risk_score = total_risk_count * 10 + avg_days_overdue * 5 + avg_progress_gap * 2
                    
                    employee_risk_data.append({
                        'user_id': user.id,
                        'user_name': user_name,
                        'username': user.username,
                        'department': department_name,
                        'goal_risk_count': goal_risk_count,  # 风险目标数
                        'plan_risk_count': plan_risk_count,  # 风险计划数
                        'total_risk_count': total_risk_count,  # 总风险数
                        'avg_days_overdue': round(avg_days_overdue, 1),  # 平均逾期天数
                        'avg_progress_gap': round(avg_progress_gap, 1),  # 平均进度差距
                        'total_risk_score': round(total_risk_score, 1),  # 总风险分数
                    })
                except Exception as e:
                    logger.warning(f'获取员工 {user_name} 的风险数据失败: {e}')
                    # 如果获取失败，添加空数据
                    employee_risk_data.append({
                        'user_id': user.id,
                        'user_name': user_name,
                        'username': user.username,
                        'department': department_name,
                        'goal_risk_count': 0,
                        'plan_risk_count': 0,
                        'total_risk_count': 0,
                        'avg_days_overdue': 0,
                        'avg_progress_gap': 0,
                        'total_risk_score': 0,
                    })
            
            # 最终去重：先按 user_id 去重，再按 user_name 去重（防止同名不同ID的情况）
            # 第一步：按 user_id 去重，保留风险分数最高的
            seen_user_ids = {}
            for emp_data in employee_risk_data:
                user_id = emp_data['user_id']
                if user_id not in seen_user_ids:
                    seen_user_ids[user_id] = emp_data
                else:
                    # 如果已存在，保留风险分数更高的
                    existing_score = seen_user_ids[user_id].get('total_risk_score', 0)
                    new_score = emp_data.get('total_risk_score', 0)
                    if new_score > existing_score:
                        logger.warning(f'发现重复 user_id，保留风险分数更高的: {emp_data.get("user_name")} (ID: {user_id})')
                        seen_user_ids[user_id] = emp_data
                    else:
                        logger.warning(f'发现重复 user_id，保留已存在的: {seen_user_ids[user_id].get("user_name")} (ID: {user_id})')
            
            # 转换为列表
            employee_risk_data = list(seen_user_ids.values())
            
            # 第二步：按 user_name 去重（防止同名不同ID的情况，如"杨乾维"）
            # 如果多个用户有相同的 user_name，只保留风险分数最高的
            seen_user_names = {}
            for emp_data in employee_risk_data:
                user_name = emp_data.get('user_name', '').strip()
                user_id = emp_data['user_id']
                
                if not user_name:
                    # 如果没有 user_name，使用 username
                    user_name = emp_data.get('username', '').strip()
                
                if user_name:
                    if user_name not in seen_user_names:
                        seen_user_names[user_name] = emp_data
                    else:
                        # 如果已存在同名用户，保留风险分数更高的
                        existing_score = seen_user_names[user_name].get('total_risk_score', 0)
                        new_score = emp_data.get('total_risk_score', 0)
                        if new_score > existing_score:
                            logger.warning(f'发现重复用户名，保留风险分数更高的: {user_name} (原ID: {seen_user_names[user_name]["user_id"]}, 新ID: {user_id})')
                            seen_user_names[user_name] = emp_data
                        else:
                            logger.warning(f'发现重复用户名，保留已存在的: {user_name} (保留ID: {seen_user_names[user_name]["user_id"]}, 跳过ID: {user_id})')
                else:
                    # 如果没有 user_name 也没有 username，按 user_id 保留
                    logger.warning(f'用户没有名称，使用 user_id: {user_id}')
            
            # 转换为最终列表并按风险分数排序
            employee_risk_data = list(seen_user_names.values())
            employee_risk_data.sort(key=lambda x: x.get('total_risk_score', 0), reverse=True)
            
            # 最终验证：确保没有重复的 user_id 和 user_name
            final_user_ids = [emp['user_id'] for emp in employee_risk_data]
            final_user_names = [emp.get('user_name', emp.get('username', '')) for emp in employee_risk_data]
            
            if len(final_user_ids) != len(set(final_user_ids)):
                logger.error(f'错误：最终数据中仍有重复 user_id！总数量: {len(final_user_ids)}, 去重后: {len(set(final_user_ids))}')
            
            if len(final_user_names) != len(set(final_user_names)):
                logger.error(f'错误：最终数据中仍有重复 user_name！总数量: {len(final_user_names)}, 去重后: {len(set(final_user_names))}')
                # 强制按 user_name 去重
                unique_by_name = {}
                for emp_data in employee_risk_data:
                    user_name = emp_data.get('user_name', emp_data.get('username', '')).strip()
                    if user_name and user_name not in unique_by_name:
                        unique_by_name[user_name] = emp_data
                    elif not user_name:
                        # 没有名称的，按 user_id 保留
                        user_id = emp_data['user_id']
                        if user_id not in unique_by_name:
                            unique_by_name[str(user_id)] = emp_data
                employee_risk_data = list(unique_by_name.values())
                employee_risk_data.sort(key=lambda x: x.get('total_risk_score', 0), reverse=True)
            
        except Exception as e:
            logger.exception('获取员工风险数据失败: %s', str(e))
            employee_risk_data = []
        
        # ========== 员工待办事项统计 ==========
        employee_todo_data = []
        try:
            # 使用与风险预警相同的员工列表
            if employee_users:
                processed_todo_user_ids = set()
                
                for emp_info in employee_users:
                    user = emp_info['user']
                    user_name = emp_info['name']
                    department_name = emp_info['department']
                    
                    # 防止重复处理同一个用户
                    if user.id in processed_todo_user_ids:
                        continue
                    processed_todo_user_ids.add(user.id)
                    
                    try:
                        from backend.apps.plan_management.services.todo_service import get_user_todos, get_responsible_todos
                        
                        # 获取 owner 的待办
                        owner_todos = get_user_todos(user=user)
                        
                        # 获取 responsible_person 的待办
                        responsible_todos = get_responsible_todos(responsible_user=user)
                        
                        # 合并并去重
                        all_todos = owner_todos + responsible_todos
                        seen_todos = set()
                        unique_todos = []
                        for todo in all_todos:
                            obj = todo.get('object')
                            if obj:
                                todo_key = (todo.get('type', ''), obj.id)
                                if todo_key not in seen_todos:
                                    seen_todos.add(todo_key)
                                    unique_todos.append(todo)
                            else:
                                # 如果没有 object，使用 title 和 type 作为唯一标识
                                todo_key = (todo.get('type', ''), todo.get('title', ''))
                                if todo_key not in seen_todos:
                                    seen_todos.add(todo_key)
                                    unique_todos.append(todo)
                        
                        # 统计待办指标
                        total_todos = len(unique_todos)
                        high_priority_count = sum(1 for t in unique_todos if t.get('priority') == 'high')
                        medium_priority_count = sum(1 for t in unique_todos if t.get('priority') == 'medium')
                        low_priority_count = sum(1 for t in unique_todos if t.get('priority') == 'low')
                        overdue_count = sum(1 for t in unique_todos if t.get('is_overdue', False))
                        
                        # 统计逾期天数
                        total_days_overdue = sum(t.get('overdue_days', 0) for t in unique_todos if t.get('is_overdue', False))
                        avg_days_overdue = total_days_overdue / overdue_count if overdue_count > 0 else 0
                        
                        # 统计待办类型分布
                        goal_accept_count = sum(1 for t in unique_todos if t.get('type') == 'goal_accept')
                        plan_accept_count = sum(1 for t in unique_todos if t.get('type') == 'plan_accept')
                        goal_execute_count = sum(1 for t in unique_todos if t.get('type') == 'goal_execute')
                        plan_execute_count = sum(1 for t in unique_todos if t.get('type') == 'plan_execute')
                        plan_today_count = sum(1 for t in unique_todos if t.get('type') == 'plan_today')
                        plan_risk_count = sum(1 for t in unique_todos if t.get('type') == 'plan_risk')
                        
                        # 计算待办分数（用于排序和对比）
                        # 待办分数 = 总待办数 * 5 + 高优先级 * 10 + 逾期数 * 15 + 平均逾期天数 * 2
                        todo_score = total_todos * 5 + high_priority_count * 10 + overdue_count * 15 + avg_days_overdue * 2
                        
                        employee_todo_data.append({
                            'user_id': user.id,
                            'user_name': user_name,
                            'username': user.username,
                            'department': department_name,
                            'total_todos': total_todos,
                            'high_priority_count': high_priority_count,
                            'medium_priority_count': medium_priority_count,
                            'low_priority_count': low_priority_count,
                            'overdue_count': overdue_count,
                            'avg_days_overdue': round(avg_days_overdue, 1),
                            'goal_accept_count': goal_accept_count,
                            'plan_accept_count': plan_accept_count,
                            'goal_execute_count': goal_execute_count,
                            'plan_execute_count': plan_execute_count,
                            'plan_today_count': plan_today_count,
                            'plan_risk_count': plan_risk_count,
                            'todo_score': round(todo_score, 1),
                        })
                    except Exception as e:
                        logger.warning(f'获取员工 {user_name} 的待办数据失败: {e}')
                        # 如果获取失败，添加空数据
                        employee_todo_data.append({
                            'user_id': user.id,
                            'user_name': user_name,
                            'username': user.username,
                            'department': department_name,
                            'total_todos': 0,
                            'high_priority_count': 0,
                            'medium_priority_count': 0,
                            'low_priority_count': 0,
                            'overdue_count': 0,
                            'avg_days_overdue': 0,
                            'goal_accept_count': 0,
                            'plan_accept_count': 0,
                            'goal_execute_count': 0,
                            'plan_execute_count': 0,
                            'plan_today_count': 0,
                            'plan_risk_count': 0,
                            'todo_score': 0,
                        })
                
                # 去重：按 user_id 去重，保留待办分数最高的
                seen_todo_user_ids = {}
                for emp_data in employee_todo_data:
                    user_id = emp_data['user_id']
                    if user_id not in seen_todo_user_ids:
                        seen_todo_user_ids[user_id] = emp_data
                    else:
                        existing_score = seen_todo_user_ids[user_id].get('todo_score', 0)
                        new_score = emp_data.get('todo_score', 0)
                        if new_score > existing_score:
                            seen_todo_user_ids[user_id] = emp_data
                
                # 按 user_name 去重
                seen_todo_user_names = {}
                for emp_data in seen_todo_user_ids.values():
                    user_name = emp_data.get('user_name', '').strip()
                    if not user_name:
                        user_name = emp_data.get('username', '').strip()
                    
                    if user_name:
                        if user_name not in seen_todo_user_names:
                            seen_todo_user_names[user_name] = emp_data
                        else:
                            existing_score = seen_todo_user_names[user_name].get('todo_score', 0)
                            new_score = emp_data.get('todo_score', 0)
                            if new_score > existing_score:
                                seen_todo_user_names[user_name] = emp_data
                
                # 转换为最终列表并按待办分数排序
                employee_todo_data = list(seen_todo_user_names.values())
                employee_todo_data.sort(key=lambda x: x.get('todo_score', 0), reverse=True)
                
        except Exception as e:
            logger.exception('获取员工待办数据失败: %s', str(e))
            employee_todo_data = []
        
        # ========== 员工工作计划统计 ==========
        employee_plan_data = []
        try:
            # 使用与风险预警相同的员工列表
            if employee_users:
                processed_plan_user_ids = set()
                from django.utils import timezone
                from backend.apps.plan_management.models import Plan
                from django.db.models import Q
                
                now = timezone.now()
                today = now.date()
                
                for emp_info in employee_users:
                    user = emp_info['user']
                    user_name = emp_info['name']
                    department_name = emp_info['department']
                    
                    # 防止重复处理同一个用户
                    if user.id in processed_plan_user_ids:
                        continue
                    processed_plan_user_ids.add(user.id)
                    
                    try:
                        # 获取 owner、responsible_person、created_by 的计划（与统计卡片保持一致）
                        all_plans = Plan.objects.filter(
                            Q(owner=user) | Q(responsible_person=user) | Q(created_by=user)
                        ).distinct()
                        
                        # 统计计划指标
                        total_plans = all_plans.count()
                        draft_count = all_plans.filter(status='draft').count()
                        published_count = all_plans.filter(status='published').count()
                        accepted_count = all_plans.filter(status='accepted').count()
                        in_progress_count = all_plans.filter(status='in_progress').count()
                        completed_count = all_plans.filter(status='completed').count()
                        cancelled_count = all_plans.filter(status='cancelled').count()
                        
                        # 统计逾期计划
                        overdue_plans = all_plans.filter(
                            status__in=['draft', 'published', 'accepted', 'in_progress'],
                            end_time__lt=now
                        )
                        overdue_count = overdue_plans.count()
                        
                        # 统计逾期天数
                        total_days_overdue = sum(plan.overdue_days or 0 for plan in overdue_plans if hasattr(plan, 'overdue_days'))
                        avg_days_overdue = total_days_overdue / overdue_count if overdue_count > 0 else 0
                        
                        # 统计今日应执行的计划
                        today_plans = all_plans.filter(
                            status__in=['draft', 'published', 'accepted', 'in_progress'],
                            start_time__lte=now,
                            end_time__gte=now
                        )
                        today_count = today_plans.count()
                        
                        # 统计平均进度
                        active_plans = all_plans.filter(status__in=['draft', 'published', 'accepted', 'in_progress'])
                        total_progress = sum(float(plan.progress or 0) for plan in active_plans if hasattr(plan, 'progress'))
                        avg_progress = total_progress / active_plans.count() if active_plans.count() > 0 else 0
                        
                        # 计算计划分数（用于排序和对比）
                        # 计划分数 = 总计划数 * 3 + 执行中 * 5 + 逾期数 * 10 + 平均逾期天数 * 2 - 已完成 * 1
                        plan_score = total_plans * 3 + in_progress_count * 5 + overdue_count * 10 + avg_days_overdue * 2 - completed_count * 1
                        
                        employee_plan_data.append({
                            'user_id': user.id,
                            'user_name': user_name,
                            'username': user.username,
                            'department': department_name,
                            'total_plans': total_plans,
                            'draft_count': draft_count,
                            'published_count': published_count,
                            'accepted_count': accepted_count,
                            'in_progress_count': in_progress_count,
                            'completed_count': completed_count,
                            'cancelled_count': cancelled_count,
                            'overdue_count': overdue_count,
                            'avg_days_overdue': round(avg_days_overdue, 1),
                            'today_count': today_count,
                            'avg_progress': round(avg_progress, 1),
                            'plan_score': round(plan_score, 1),
                        })
                    except Exception as e:
                        logger.warning(f'获取员工 {user_name} 的工作计划数据失败: {e}')
                        # 如果获取失败，添加空数据
                        employee_plan_data.append({
                            'user_id': user.id,
                            'user_name': user_name,
                            'username': user.username,
                            'department': department_name,
                            'total_plans': 0,
                            'draft_count': 0,
                            'published_count': 0,
                            'accepted_count': 0,
                            'in_progress_count': 0,
                            'completed_count': 0,
                            'cancelled_count': 0,
                            'overdue_count': 0,
                            'avg_days_overdue': 0,
                            'today_count': 0,
                            'avg_progress': 0,
                            'plan_score': 0,
                        })
                
                # 去重：按 user_id 去重，保留计划分数最高的
                seen_plan_user_ids = {}
                for emp_data in employee_plan_data:
                    user_id = emp_data['user_id']
                    if user_id not in seen_plan_user_ids:
                        seen_plan_user_ids[user_id] = emp_data
                    else:
                        existing_score = seen_plan_user_ids[user_id].get('plan_score', 0)
                        new_score = emp_data.get('plan_score', 0)
                        if new_score > existing_score:
                            seen_plan_user_ids[user_id] = emp_data
                
                # 按 user_name 去重
                seen_plan_user_names = {}
                for emp_data in seen_plan_user_ids.values():
                    user_name = emp_data.get('user_name', '').strip()
                    if not user_name:
                        user_name = emp_data.get('username', '').strip()
                    
                    if user_name:
                        if user_name not in seen_plan_user_names:
                            seen_plan_user_names[user_name] = emp_data
                        else:
                            existing_score = seen_plan_user_names[user_name].get('plan_score', 0)
                            new_score = emp_data.get('plan_score', 0)
                            if new_score > existing_score:
                                seen_plan_user_names[user_name] = emp_data
                
                # 转换为最终列表并按计划分数排序
                employee_plan_data = list(seen_plan_user_names.values())
                employee_plan_data.sort(key=lambda x: x.get('plan_score', 0), reverse=True)
                
        except Exception as e:
            logger.exception('获取员工工作计划数据失败: %s', str(e))
            employee_plan_data = []
        
        # ========== 员工战略目标统计 ==========
        employee_goal_data = []
        try:
            # 使用与风险预警相同的员工列表
            if employee_users:
                processed_goal_user_ids = set()
                from django.utils import timezone
                from backend.apps.plan_management.models import StrategicGoal
                from django.db.models import Q
                from datetime import timedelta
                
                now = timezone.now()
                today = now.date()
                
                for emp_info in employee_users:
                    user = emp_info['user']
                    user_name = emp_info['name']
                    department_name = emp_info['department']
                    
                    # 防止重复处理同一个用户
                    if user.id in processed_goal_user_ids:
                        continue
                    processed_goal_user_ids.add(user.id)
                    
                    try:
                        # 获取 owner、responsible_person、created_by 的目标（与统计卡片保持一致）
                        all_goals = StrategicGoal.objects.filter(
                            Q(owner=user) | Q(responsible_person=user) | Q(created_by=user)
                        ).distinct()
                        
                        # 统计目标指标
                        total_goals = all_goals.count()
                        draft_count = all_goals.filter(status='draft').count()
                        published_count = all_goals.filter(status='published').count()
                        accepted_count = all_goals.filter(status='accepted').count()
                        in_progress_count = all_goals.filter(status='in_progress').count()
                        completed_count = all_goals.filter(status='completed').count()
                        cancelled_count = all_goals.filter(status='cancelled').count()
                        
                        # 统计逾期目标
                        overdue_goals = all_goals.filter(
                            status__in=['draft', 'published', 'accepted', 'in_progress'],
                            end_date__lt=today
                        )
                        overdue_count = overdue_goals.count()
                        
                        # 统计逾期天数
                        total_days_overdue = 0
                        for goal in overdue_goals:
                            if goal.end_date:
                                days_overdue = (today - goal.end_date).days
                                total_days_overdue += max(0, days_overdue)
                        avg_days_overdue = total_days_overdue / overdue_count if overdue_count > 0 else 0
                        
                        # 统计本月需完成的目标
                        month_start = today.replace(day=1)
                        month_end = (month_start + timedelta(days=32)).replace(day=1) - timedelta(days=1)
                        this_month_goals = all_goals.filter(
                            status__in=['draft', 'published', 'accepted', 'in_progress'],
                            end_date__gte=month_start,
                            end_date__lte=month_end
                        )
                        this_month_count = this_month_goals.count()
                        
                        # 统计平均完成率
                        active_goals = all_goals.filter(status__in=['draft', 'published', 'accepted', 'in_progress'])
                        total_completion = sum(float(goal.completion_rate or 0) for goal in active_goals if hasattr(goal, 'completion_rate'))
                        avg_completion = total_completion / active_goals.count() if active_goals.count() > 0 else 0
                        
                        # 计算目标分数（用于排序和对比）
                        # 目标分数 = 总目标数 * 3 + 执行中 * 5 + 逾期数 * 10 + 平均逾期天数 * 2 - 已完成 * 1
                        goal_score = total_goals * 3 + in_progress_count * 5 + overdue_count * 10 + avg_days_overdue * 2 - completed_count * 1
                        
                        employee_goal_data.append({
                            'user_id': user.id,
                            'user_name': user_name,
                            'username': user.username,
                            'department': department_name,
                            'total_goals': total_goals,
                            'draft_count': draft_count,
                            'published_count': published_count,
                            'accepted_count': accepted_count,
                            'in_progress_count': in_progress_count,
                            'completed_count': completed_count,
                            'cancelled_count': cancelled_count,
                            'overdue_count': overdue_count,
                            'avg_days_overdue': round(avg_days_overdue, 1),
                            'this_month_count': this_month_count,
                            'avg_completion': round(avg_completion, 1),
                            'goal_score': round(goal_score, 1),
                        })
                    except Exception as e:
                        logger.warning(f'获取员工 {user_name} 的战略目标数据失败: {e}')
                        # 如果获取失败，添加空数据
                        employee_goal_data.append({
                            'user_id': user.id,
                            'user_name': user_name,
                            'username': user.username,
                            'department': department_name,
                            'total_goals': 0,
                            'draft_count': 0,
                            'published_count': 0,
                            'accepted_count': 0,
                            'in_progress_count': 0,
                            'completed_count': 0,
                            'cancelled_count': 0,
                            'overdue_count': 0,
                            'avg_days_overdue': 0,
                            'this_month_count': 0,
                            'avg_completion': 0,
                            'goal_score': 0,
                        })
                
                # 去重：按 user_id 去重，保留目标分数最高的
                seen_goal_user_ids = {}
                for emp_data in employee_goal_data:
                    user_id = emp_data['user_id']
                    if user_id not in seen_goal_user_ids:
                        seen_goal_user_ids[user_id] = emp_data
                    else:
                        existing_score = seen_goal_user_ids[user_id].get('goal_score', 0)
                        new_score = emp_data.get('goal_score', 0)
                        if new_score > existing_score:
                            seen_goal_user_ids[user_id] = emp_data
                
                # 按 user_name 去重
                seen_goal_user_names = {}
                for emp_data in seen_goal_user_ids.values():
                    user_name = emp_data.get('user_name', '').strip()
                    if not user_name:
                        user_name = emp_data.get('username', '').strip()
                    
                    if user_name:
                        if user_name not in seen_goal_user_names:
                            seen_goal_user_names[user_name] = emp_data
                        else:
                            existing_score = seen_goal_user_names[user_name].get('goal_score', 0)
                            new_score = emp_data.get('goal_score', 0)
                            if new_score > existing_score:
                                seen_goal_user_names[user_name] = emp_data
                
                # 转换为最终列表并按目标分数排序
                employee_goal_data = list(seen_goal_user_names.values())
                employee_goal_data.sort(key=lambda x: x.get('goal_score', 0), reverse=True)
                
        except Exception as e:
            logger.exception('获取员工战略目标数据失败: %s', str(e))
            employee_goal_data = []
        
        # ========== 待办事项 ==========
        todo_items = []
        pending_tasks_count = len(task_board.get('pending', []))
        
        # 将待处理任务转换为待办事项格式
        for task in task_board.get('pending', [])[:10]:
            todo_items.append({
                'title': task.get('title', '未知任务'),
                'project_name': task.get('project_name', ''),
                'due_time': task.get('due_time'),
                'url': task.get('url', '#')
            })
        
        # ========== 最近活动 ==========
        recent_activities = []
        
        # 已完成任务作为最近活动
        for task in task_board.get('completed', [])[:10]:
            recent_activities.append({
                'title': f'完成任务：{task.get("title", "未知任务")}',
                'project_name': task.get('project_name', ''),
                'time': task.get('completed_time') or task.get('due_time'),
                'url': task.get('url', '#')
            })
        
        # ========== 我的工作 ==========
        my_work = {}
        try:
            from backend.apps.production_management.models import Project, ProjectTask
            
            # 我负责的任务
            my_tasks = ProjectTask.objects.filter(
                assigned_to=user,
                status__in=['pending', 'in_progress']
            ).select_related('project')[:5]
            
            my_work['my_tasks'] = [{
                'title': task.title,
                'status': task.get_status_display(),
                'progress': getattr(task, 'progress', 0) or 0,
                'url': reverse('production_pages:project_detail', args=[task.project.id]) if task.project else '#'
            } for task in my_tasks]
            my_work['my_tasks_count'] = ProjectTask.objects.filter(
                assigned_to=user,
                status__in=['pending', 'in_progress']
            ).count()
            
            # 我参与的项目
            participating_projects = Project.objects.filter(
                Q(project_manager=user) | Q(team_members__user=user)
            ).distinct()[:5]
            
            my_work['participating_projects'] = []
            for project in participating_projects:
                role = '项目经理' if project.project_manager == user else '团队成员'
                my_work['participating_projects'].append({
                    'title': project.name,
                    'role': role,
                    'progress': getattr(project, 'progress', 0) or 0,
                    'url': reverse('production_pages:project_detail', args=[project.id])
                })
            my_work['participating_projects_count'] = Project.objects.filter(
                Q(project_manager=user) | Q(team_members__user=user)
            ).distinct().count()
        except Exception as e:
            logger.exception('获取我的工作数据失败: %s', str(e))
            my_work = {
                'my_tasks': [],
                'my_tasks_count': 0,
                'participating_projects': [],
                'participating_projects_count': 0
            }
        
        # ========== 顶部操作栏 ==========
        top_actions = []
        try:
            if _permission_granted('production_management.create', permission_set):
                top_actions.append({
                    'label': '创建项目',
                    'icon': '➕',
                    'url': reverse('production_pages:project_create')
                })
        except Exception:
            pass
        
        # ========== 运营中心模块卡片 ==========
        operation_center_sections = []
        
        # 计划管理模块卡片
        try:
            if _permission_granted('plan_management.view', permission_set):
                # 获取计划管理统计数据
                from backend.apps.plan_management.models import Plan, StrategicGoal
                total_plans = Plan.objects.count()
                in_progress_plans = Plan.objects.filter(status='in_progress').count()
                total_goals = StrategicGoal.objects.count()
                
                operation_center_sections.append({
                    'title': '计划管理',
                    'description': '管理计划、目标和审批流程',
                    'icon': '📅',
                    'url': reverse('plan_pages:plan_management_home'),
                    'stats': {
                        '计划总数': total_plans,
                        '执行中': in_progress_plans,
                        '目标总数': total_goals,
                    }
                })
        except Exception as e:
            logger.warning(f'获取计划管理统计数据失败: {e}')
        
        # 将 scene_groups 转换为侧边栏菜单格式
        sidebar_nav = []
        try:
            for group in scene_groups:
                if group.get('items'):
                    # 将场景分组转换为侧边栏菜单项（带子菜单）
                    sidebar_nav.append({
                        'label': group.get('title', ''),
                        'icon': group.get('icon', ''),
                        'url': '#',
                        'active': False,
                        'children': [
                            {
                                'label': item.get('label', ''),
                                'icon': item.get('icon', ''),
                                'url': item.get('url', '#'),
                                'active': False,
                            }
                            for item in group.get('items', [])
                        ]
                    })
        except Exception as e:
            logger.warning(f'转换场景分组为侧边栏菜单失败: {e}', exc_info=True)
            sidebar_nav = []
        
        # 构建上下文
        # 确保使用 request.user 而不是局部变量 user（防止被覆盖）
        context = {
            'user': request.user,  # 直接使用 request.user，确保是最新的用户对象
            'is_superuser': getattr(user, 'is_superuser', False),
            'centers_navigation': centers_navigation,
            'full_top_nav': centers_navigation,  # 顶部导航菜单（与计划管理模块一致）
            'scene_groups': scene_groups,  # 场景分组菜单（用于左侧栏场景式显示）
            'pending_counts': pending_counts,
            'approval_stats': approval_stats,
            'delivery_stats': delivery_stats,
            'stats_cards': stats_cards,
            'task_board': task_board,
            # 新增：计划管理首页风格的数据
            'core_cards': core_cards,
            'project_status_dist': project_status_dist,
            'task_status_dist': task_status_dist,
            'show_stats': bool(project_status_dist or task_status_dist),
            'risk_warnings': risk_warnings[:5],
            'overdue_tasks_count': overdue_tasks_count,
            'stale_tasks_count': stale_tasks_count,
            'employee_risk_data': employee_risk_data,  # 员工风险对比数据
            'employee_risk_data_json': json.dumps(employee_risk_data, ensure_ascii=False),  # JSON格式用于前端
            'employee_todo_data': employee_todo_data,  # 员工待办对比数据
            'employee_todo_data_json': json.dumps(employee_todo_data, ensure_ascii=False),  # JSON格式用于前端
            'employee_plan_data': employee_plan_data,  # 员工工作计划对比数据
            'employee_plan_data_json': json.dumps(employee_plan_data, ensure_ascii=False),  # JSON格式用于前端
            'employee_goal_data': employee_goal_data,  # 员工战略目标对比数据
            'employee_goal_data_json': json.dumps(employee_goal_data, ensure_ascii=False),  # JSON格式用于前端
            'todo_items': todo_items,
            'pending_tasks_count': pending_tasks_count,
            'recent_activities': recent_activities,
            'top_actions': top_actions,
            'my_work': my_work,
            'operation_center_sections': operation_center_sections,  # 运营中心模块卡片
            # 添加左侧栏数据
            'sidebar_nav': sidebar_nav,  # 从 scene_groups 转换而来的侧边栏菜单
            'sidebar_title': '总工作台',
            'sidebar_subtitle': 'Dashboard',
        }
        
        # 尝试渲染模板，如果模板不存在则返回简单HTML
        try:
            resp = render(request, 'dashboard.html', context)
            resp["X-Hit-Home-View"] = "1"
            resp["X-Home-Branch"] = "render-dashboard"
            resp["X-Build-Probe"] = "DASHBOARD_HDR_PROBE_20260113_1"
            return resp
        except Exception as template_error:
            logger.warning(f'模板渲染失败，返回简单HTML: {template_error}')
            # 如果模板不存在，返回一个简单的HTML页面
            from django.http import HttpResponse
            html_content = f"""
            <!DOCTYPE html>
            <html>
            <head>
                <title>维海科技信息化管理平台</title>
                <meta charset="UTF-8">
            </head>
            <body>
                <h1>维海科技信息化管理平台</h1>
                <p>欢迎，{user.username if user.is_authenticated else '访客'}</p>
                <p><a href="/admin/">访问管理后台</a></p>
            </body>
            </html>
            """
            return HttpResponse(html_content, content_type='text/html')
    except Exception as e:
        logger.exception('home 视图函数执行失败: %s', str(e))
        # 返回一个简单的错误页面，而不是让Django返回500错误
        try:
            from django.http import HttpResponse
            html_content = f"""
            <!DOCTYPE html>
            <html>
            <head>
                <title>系统错误</title>
                <meta charset="UTF-8">
            </head>
            <body>
                <h1>系统暂时无法访问</h1>
                <p>页面加载时发生错误，请稍后重试。</p>
                <p><a href="/login/">返回登录页</a></p>
            </body>
            </html>
            """
            return HttpResponse(html_content, content_type='text/html')
        except Exception as inner_e:
            logger.exception('生成错误页面也失败: %s', str(inner_e))
            # 如果连错误页面都生成不了，重定向到登录页
            return redirect('login')


def dashboard(request):
    """总工作台首页 - 与home视图功能相同"""
    # 直接调用home视图的逻辑
    return home(request)


def login_view(request):
    """前端登录页面 - 与管理后台登录分开"""
    from django.contrib.auth import authenticate, login as auth_login
    
    # 如果已登录，重定向到首页
    if request.user.is_authenticated:
        next_url = request.GET.get('next', 'home')
        # 如果next参数指向admin，重定向到admin首页
        if next_url and ('admin' in next_url or next_url.startswith('/admin')):
            return redirect('admin:index')
        return redirect('home')
    
    # 处理POST请求（登录表单提交）
    if request.method == 'POST':
        username = request.POST.get('username')
        password = request.POST.get('password')
        
        if username and password:
            user = authenticate(request, username=username, password=password)
            if user:
                if user.is_active:
                    # 如果当前登录的用户与要登录的用户不同，先退出
                    if request.user.is_authenticated and request.user.id != user.id:
                        logout(request)
                    # 登录新用户（auth_login函数会自动处理会话）
                    auth_login(request, user)
                    # 检查是否需要完善资料
                    # if not user.profile_completed:
                    #     return redirect('complete_profile')  # 已注释：禁用资料完善页面
                    
                    # 根据next参数决定重定向目标
                    next_url = request.GET.get('next', 'home')
                    if next_url and ('admin' in next_url or next_url.startswith('/admin')):
                        # 如果next包含admin，重定向到后台管理
                        return redirect('admin:index')
                    else:
                        # 否则重定向到前端首页
                        return redirect('home')
                else:
                    messages.error(request, '用户账户已被禁用')
            else:
                messages.error(request, '用户名或密码错误')
        else:
            messages.error(request, '请输入用户名和密码')
    
    # GET请求：渲染前端登录页面
    # 清除所有之前的消息（登录页面不应该显示系统消息）
    storage = messages.get_messages(request)
    list(storage)  # 消费所有消息，清除它们
    
    return render(request, 'login.html')


def logout_view(request):
    """登出页面"""
    logout(request)
    # 不在登录页面显示退出消息，避免登录页面显示系统消息
    # messages.success(request, '您已成功退出登录')
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


def favicon_view(request):
    """Favicon视图"""
    from django.http import HttpResponse
    from django.conf import settings
    import os
    import logging
    
    logger = logging.getLogger(__name__)
    
    try:
        # 尝试多个可能的favicon路径
        possible_paths = []
        
        # 1. STATIC_ROOT
        try:
            if hasattr(settings, 'STATIC_ROOT') and settings.STATIC_ROOT:
                static_root_path = os.path.join(str(settings.STATIC_ROOT), 'favicon.ico')
                possible_paths.append(static_root_path)
        except Exception as e:
            logger.debug(f'无法获取STATIC_ROOT路径: {e}')
        
        # 2. STATICFILES_DIRS
        try:
            if hasattr(settings, 'STATICFILES_DIRS') and settings.STATICFILES_DIRS:
                for static_dir in settings.STATICFILES_DIRS:
                    try:
                        static_dir_path = os.path.join(str(static_dir), 'favicon.ico')
                        possible_paths.append(static_dir_path)
                    except Exception as e:
                        logger.debug(f'无法构建STATICFILES_DIRS路径: {e}')
                        continue
        except Exception as e:
            logger.debug(f'无法获取STATICFILES_DIRS: {e}')
        
        # 3. 前端构建目录
        try:
            if hasattr(settings, 'BASE_DIR'):
                base_dir = settings.BASE_DIR
                if hasattr(base_dir, 'parent'):
                    frontend_dist = os.path.join(str(base_dir.parent), 'frontend', 'dist', 'favicon.ico')
                    if os.path.exists(frontend_dist):
                        possible_paths.append(frontend_dist)
        except Exception as e:
            logger.debug(f'无法获取前端构建目录: {e}')
        
        # 4. 前端public目录
        try:
            if hasattr(settings, 'BASE_DIR'):
                base_dir = settings.BASE_DIR
                if hasattr(base_dir, 'parent'):
                    frontend_public = os.path.join(str(base_dir.parent), 'frontend', 'public', 'favicon.ico')
                    if os.path.exists(frontend_public):
                        possible_paths.append(frontend_public)
        except Exception as e:
            logger.debug(f'无法获取前端public目录: {e}')
        
        # 尝试每个路径
        for favicon_path in possible_paths:
            try:
                if os.path.exists(favicon_path):
                    with open(favicon_path, 'rb') as f:
                        return HttpResponse(f.read(), content_type='image/x-icon')
            except Exception as e:
                logger.debug(f'读取favicon文件失败 {favicon_path}: {e}')
                continue
        
        # 如果所有路径都失败，返回204 No Content
        return HttpResponse(status=204)
    except Exception as e:
        logger.warning(f'favicon_view处理异常: {e}', exc_info=True)
        # 返回204而不是500，避免影响页面加载
        return HttpResponse(status=204)


def test_admin_page(request):
    """测试admin页面"""
    return redirect('admin:index')


def django_service_control(request):
    """Django服务控制"""
    return JsonResponse({'status': 'ok'})


def _get_current_module_from_path(request_path):
    """根据请求路径判断当前模块
    
    Args:
        request_path: 请求路径，例如 '/workflow/workflows/'
    
    Returns:
        str: 模块标识，例如 'workflow_engine'，如果无法判断则返回 None
    """
    if not request_path:
        return None
    
    # 模块路径映射
    module_path_map = {
        'workflow': 'workflow_engine',
        'production': 'production_management',
        'customers': 'customer_management',
        'opportunities': 'customer_management',
        'contracts': 'customer_management',
        'business': 'customer_management',
        'delivery': 'delivery_customer',
        'settlement': 'settlement_center',
        'plan': 'plan_management',
        'litigation': 'litigation_management',
        'financial': 'financial_management',
        'personnel': 'personnel_management',
        'administrative': 'administrative_management',
        'system-center': 'system_management',
        'archive': 'archive_management',
        'collaboration': 'task_collaboration',
        'resource': 'resource_standard',
    }
    
    # 检查路径是否匹配某个模块
    for path_prefix, module_name in module_path_map.items():
        if request_path.startswith(f'/{path_prefix}/'):
            return module_name
    
    return None


def _get_sidebar_menu_for_module(module_name, permission_set, request_path=None, user=None):
    """获取指定模块的侧边栏菜单
    
    Args:
        module_name: 模块标识，例如 'workflow_engine'
        permission_set: 用户权限集合
        request_path: 当前请求路径（可选）
        user: 当前用户（可选）
    
    Returns:
        list: 侧边栏菜单项列表
    """
    if not module_name:
        return []
    
    # 模块菜单构建函数映射
    menu_builders = {
        'workflow_engine': 'backend.apps.workflow_engine.views_pages._build_workflow_engine_sidebar_nav',
        'production_management': 'backend.apps.production_management.views_pages._build_production_management_sidebar_nav',
        'customer_management': None,  # 客户管理模块可能有多个子模块，需要特殊处理
        'delivery_customer': 'backend.apps.delivery_customer.views_pages._build_delivery_sidebar_nav',
        'plan_management': 'backend.apps.plan_management.views_pages._build_plan_management_sidebar_nav',
        'litigation_management': None,  # 待实现
        'financial_management': None,  # 待实现
        'personnel_management': 'backend.apps.personnel_management.views_pages._build_personnel_sidebar_nav',
        'administrative_management': 'backend.apps.administrative_management.views_pages._build_administrative_sidebar_nav',
        'system_management': 'backend.apps.system_management.views_pages._build_system_management_sidebar_nav',
        'archive_management': None,  # 待实现
        'task_collaboration': None,  # 待实现
        'resource_standard': None,  # 待实现
        'settlement_center': None,  # 待实现
    }
    
    # 获取菜单构建函数路径
    builder_path = menu_builders.get(module_name)
    if not builder_path:
        return []
    
    # 动态导入并调用菜单构建函数
    try:
        module_path, function_name = builder_path.rsplit('.', 1)
        module = __import__(module_path, fromlist=[function_name])
        builder_func = getattr(module, function_name)
        return builder_func(permission_set, request_path, user)
    except (ImportError, AttributeError, Exception) as e:
        import logging
        logger = logging.getLogger(__name__)
        logger.warning(f'获取模块 {module_name} 的侧边栏菜单失败: {e}', exc_info=True)
        return []
