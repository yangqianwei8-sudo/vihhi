"""
审批流程引擎页面视图
"""
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.core.paginator import Paginator
from django.db.models import Q
from django.http import Http404
from django.urls import reverse, NoReverseMatch
from backend.apps.workflow_engine.models import WorkflowTemplate, ApprovalNode, ApprovalInstance, ApprovalRecord
from backend.apps.workflow_engine.forms import WorkflowTemplateForm
from backend.apps.system_management.services import get_user_permission_codes
from backend.apps.system_management.models import User, Role, Department
from backend.core.views import _build_full_top_nav, _permission_granted


# ==================== 审批引擎模块左侧菜单结构 =====================
WORKFLOW_ENGINE_MENU = [
    {
        'id': 'workflow_home',
        'label': '首页',
        'icon': '🏠',
        'url_name': 'workflow_engine:workflow_home_alt',
        'permission': 'workflow_engine.view',
        'path_keywords': ['home'],
    },
    # G1-5: 流程管理菜单已移除，流程配置仅允许在 Django Admin 中维护
    {
        'id': 'approval_management',
        'label': '审批管理',
        'icon': '📋',
        'permission': 'workflow_engine.view',
        'expanded': False,
        'children': [
            {
                'id': 'approval_list_pending',
                'label': '待我审批',
                'icon': '✅',
                'url_name': 'workflow_engine:approval_list_pending',
                'permission': 'workflow_engine.view',
                'path_keywords': ['approvals/pending', 'approvals/pending/'],
            },
            {
                'id': 'approval_list_history',
                'label': '历史审批',
                'icon': '📜',
                'url_name': 'workflow_engine:approval_list_history',
                'permission': 'workflow_engine.view',
                'path_keywords': ['approvals/history', 'approvals/history/'],
            },
            {
                'id': 'approval_list_my_submitted',
                'label': '我的申请',
                'icon': '📤',
                'url_name': 'workflow_engine:approval_list_my_submitted',
                'permission': 'workflow_engine.view',
                'path_keywords': ['approvals/my-submitted', 'approvals/my-submitted/'],
            },
        ],
    },
]


def _build_workflow_engine_sidebar_nav(permission_set, request_path=None, user=None):
    """生成审批引擎模块的左侧菜单导航（分组格式）
    
    Args:
        permission_set: 用户权限集合
        request_path: 当前请求路径，用于判断激活状态
        user: 当前用户
    
    Returns:
        list: 分组菜单项列表
    """
    sidebar_nav = []
    
    for group in WORKFLOW_ENGINE_MENU:
        # 检查分组权限
        if group.get('permission') and not _permission_granted(group['permission'], permission_set):
            continue
        
        # 如果是独立菜单项（没有children），直接添加
        if not group.get('children'):
            # 构建URL
            url = '#'
            if group.get('url_name'):
                try:
                    url = reverse(group['url_name'])
                except Exception:
                    pass
            
            # 判断是否激活
            is_active = False
            if request_path:
                # 检查是否有path_keywords匹配
                if group.get('path_keywords'):
                    for keyword in group['path_keywords']:
                        if keyword in request_path:
                            is_active = True
                            break
                # 如果没有path_keywords，检查URL是否匹配
                elif url != '#' and request_path.endswith(url.rstrip('/')):
                    is_active = True
            
            sidebar_nav.append({
                'id': group.get('id', ''),
                'label': group.get('label', ''),
                'icon': group.get('icon', ''),
                'url': url,
                'active': is_active,
                'badge': None,  # 添加 badge 字段以避免模板警告
            })
            continue
        
        # 构建子菜单
        children = []
        for item in group.get('children', []):
            # 检查子菜单项权限
            if item.get('permission') and not _permission_granted(item['permission'], permission_set):
                continue
            
            # 构建URL
            url = '#'
            if item.get('url_name'):
                try:
                    url = reverse(item['url_name'])
                except Exception:
                    pass
            
            # 判断是否激活
            is_active = False
            if request_path and item.get('path_keywords'):
                for keyword in item['path_keywords']:
                    if keyword in request_path:
                        is_active = True
                        break
            
            children.append({
                'id': item.get('id', ''),
                'label': item.get('label', ''),
                'icon': item.get('icon', ''),
                'url': url,
                'active': is_active,
                'badge': None,  # 添加 badge 字段以避免模板警告
            })
        
        if children:
            sidebar_nav.append({
                'id': group.get('id', ''),
                'label': group.get('label', ''),
                'icon': group.get('icon', ''),
                'url': '#',
                'active': any(child.get('active') for child in children),
                'expanded': group.get('expanded', False) or any(child.get('active') for child in children),
                'children': children,
                'badge': None,  # 添加 badge 字段以避免模板警告
            })
    
    return sidebar_nav


def _context(page_title, page_icon, description, summary_cards=None, sections=None, request=None):
    """构建页面上下文"""
    context = {
        'page_title': page_title,
        'page_icon': page_icon,
        'description': description,
        'summary_cards': summary_cards or [],
        'sections': sections or [],
    }
    if request and request.user.is_authenticated:
        permission_set = get_user_permission_codes(request.user)
        context['user'] = request.user
        context['full_top_nav'] = _build_full_top_nav(permission_set, request.user)
        sidebar_nav = _build_workflow_engine_sidebar_nav(permission_set, request.path, request.user)
        context['sidebar_menu'] = sidebar_nav
        context['sidebar_nav'] = sidebar_nav  # 为三栏布局模板提供
        # 设置侧边栏标题和副标题
        context['sidebar_title'] = '审批引擎'
        context['sidebar_subtitle'] = 'Workflow Engine'
    return context


@login_required
def workflow_home(request):
    """
    审批引擎首页 - 数据展示中心
    
    首页结构：
    1. 核心指标卡片：流程模板、待审批、我的申请
    2. 状态分布统计：流程状态分布、审批状态分布
    3. 待办事项：待我审批、我的申请
    4. 最近活动：最近审批记录
    """
    permission_codes = get_user_permission_codes(request.user)
    
    # 权限检查
    if not _permission_granted('workflow_engine.view', permission_codes):
        messages.error(request, '您没有权限访问审批引擎')
        return redirect('admin:index')
    
    context = {}
    
    try:
        from .services import ApprovalEngine
        from django.db.models import Count, Q
        from django.utils import timezone
        from datetime import timedelta
        
        # ========== 核心指标卡片 ==========
        # 流程模板统计
        workflow_total = WorkflowTemplate.objects.count()
        workflow_active = WorkflowTemplate.objects.filter(status='active').count()
        workflow_draft = WorkflowTemplate.objects.filter(status='draft').count()
        
        # 待我审批统计
        pending_approvals = ApprovalEngine.get_pending_approvals(request.user)
        pending_count = len(pending_approvals)
        
        # 我的申请统计
        my_applications = ApprovalEngine.get_my_applications(request.user)
        my_applications_pending = [a for a in my_applications if a.status == 'pending']
        my_applications_approved = [a for a in my_applications if a.status == 'approved']
        my_applications_rejected = [a for a in my_applications if a.status == 'rejected']
        
        core_cards = [
            {
                'label': '流程模板',
                'icon': '⚙️',
                'value': str(workflow_total),
                'subvalue': f'启用 {workflow_active} | 草稿 {workflow_draft}',
                'url': None,  # G1-5: 流程模板管理已移除，仅允许在 Django Admin 中维护
                'variant': 'primary' if workflow_total > 0 else 'secondary'
            },
            {
                'label': '待我审批',
                'icon': '📋',
                'value': str(pending_count),
                'subvalue': f'待处理审批 {pending_count} 项',
                'url': reverse('workflow_engine:approval_list_pending'),
                'variant': 'primary' if pending_count > 0 else 'secondary'
            },
            {
                'label': '我的申请',
                'icon': '📝',
                'value': str(len(my_applications)),
                'subvalue': f'待审批 {len(my_applications_pending)} | 已通过 {len(my_applications_approved)} | 已驳回 {len(my_applications_rejected)}',
                'url': reverse('workflow_engine:approval_list_my_submitted'),
                'variant': 'primary' if len(my_applications) > 0 else 'secondary'
            },
        ]
        
        context['core_cards'] = core_cards
        
        # ========== 状态分布统计 ==========
        # 流程状态分布
        workflow_status_dist = {}
        workflow_status_rows = WorkflowTemplate.objects.values('status').annotate(count=Count('id'))
        status_label_map = dict(WorkflowTemplate.STATUS_CHOICES)
        
        for row in workflow_status_rows:
            code = row['status']
            cnt = row['count']
            workflow_status_dist[str(code)] = {
                'label': status_label_map.get(code, str(code)),
                'count': cnt
            }
        # 转换为 JSON 字符串供模板使用
        import json
        context['workflow_status_dist'] = json.dumps(workflow_status_dist) if workflow_status_dist else None
        
        # 审批状态分布（我的申请）
        approval_status_dist = {}
        if my_applications:
            status_counts = {}
            for app in my_applications:
                status = app.status
                status_counts[status] = status_counts.get(status, 0) + 1
            
            status_label_map = {
                'pending': '待审批',
                'approved': '已通过',
                'rejected': '已驳回',
                'cancelled': '已取消',
            }
            
            for status, count in status_counts.items():
                approval_status_dist[status] = {
                    'label': status_label_map.get(status, status),
                    'count': count
                }
        # 转换为 JSON 字符串供模板使用
        import json
        context['approval_status_dist'] = json.dumps(approval_status_dist) if approval_status_dist else None
        
        # ========== 待办事项 ==========
        # 待我审批（前5条）
        todo_items = []
        for approval in pending_approvals[:5]:
            content_type_name = '未知'
            if approval.content_type:
                content_type_name = approval.content_type.model
            todo_items.append({
                'title': f'{approval.workflow.name} - {content_type_name}',
                'type': 'approval',
                'url': reverse('workflow_engine:approval_detail', args=[approval.id]),
                'time': approval.created_time,
                'instance_number': approval.instance_number,
            })
        context['todo_items'] = todo_items
        context['pending_approval_count'] = pending_count
        
        # ========== 我的申请（待审批）==========
        my_pending_items = []
        for app in my_applications_pending[:5]:
            content_type_name = '未知'
            if app.content_type:
                content_type_name = app.content_type.model
            my_pending_items.append({
                'title': f'{app.workflow.name} - {content_type_name}',
                'type': 'my_application',
                'url': reverse('workflow_engine:approval_detail', args=[app.id]),
                'time': app.created_time,
                'instance_number': app.instance_number,
                'status': app.get_status_display() if hasattr(app, 'get_status_display') else app.status,
            })
        context['my_pending_items'] = my_pending_items
        context['my_pending_count'] = len(my_applications_pending)
        
        # ========== 最近活动 ==========
        recent_activities = {}
        
        # 最近审批记录（仅当前用户公司，按 applicant.company_id 过滤）
        recent_approvals = ApprovalInstance.objects.all().select_related(
            'workflow', 'applicant', 'content_type'
        ).order_by('-created_time')
        if getattr(request.user, 'company_id', None):
            recent_approvals = recent_approvals.filter(applicant__company_id=request.user.company_id)
        recent_approvals = recent_approvals[:10]
        
        recent_activities['recent_approvals'] = []
        for approval in recent_approvals:
            content_type_name = '未知'
            if approval.content_type:
                content_type_name = approval.content_type.model
            
            # 获取最新审批记录
            latest_record = approval.records.order_by('-approval_time', '-created_time').first()
            approver_name = latest_record.approver.get_full_name() if latest_record and latest_record.approver else '待审批'
            result = latest_record.get_result_display() if latest_record and hasattr(latest_record, 'get_result_display') else (latest_record.result if latest_record else '待审批')
            
            recent_activities['recent_approvals'].append({
                'title': f'{approval.workflow.name} - {content_type_name}',
                'approver': approver_name,
                'result': result,
                'time': latest_record.approval_time if latest_record and latest_record.approval_time else approval.created_time,
                'url': reverse('workflow_engine:approval_detail', args=[approval.id]),
                'instance_number': approval.instance_number,
            })
        
        context['recent_activities'] = recent_activities
        
    except Exception as e:
        import logging
        logger = logging.getLogger(__name__)
        logger.exception('获取统计数据失败: %s', str(e))
        # 设置默认值避免模板错误
        context.setdefault('core_cards', [])
        context.setdefault('workflow_status_dist', None)
        context.setdefault('approval_status_dist', None)
        context.setdefault('todo_items', [])
        context.setdefault('my_pending_items', [])
        context.setdefault('pending_approval_count', 0)
        context.setdefault('my_pending_count', 0)
        context.setdefault('recent_activities', {})
    
    # 构建页面上下文
    page_context = _context(
        page_title="审批引擎",
        page_icon="⚙️",
        description="数据展示中心 - 集中展示审批流程的关键指标、状态和待办事项",
        summary_cards=[],
        sections=[],
        request=request,
    )
    
    # 合并所有数据
    page_context.update(context)
    
    # 添加 sidebar_nav（如果 _context 中已设置，这里可以覆盖或保留）
    page_context['sidebar_menu'] = _build_workflow_engine_sidebar_nav(permission_codes, request_path=request.path, user=request.user)
    
    # 添加 top_actions 以避免模板警告（如果需要，可以在这里添加操作按钮）
    page_context.setdefault('top_actions', [])
    
    return render(request, "workflow_engine/workflow_home.html", page_context)


@login_required
def workflow_list_disabled(request):
    """审批流程模板列表（G1-5: 已禁用，流程配置仅允许在 Django Admin 中维护）"""
    from django.http import HttpResponseForbidden
    messages.error(request, '流程模板管理已移除，请使用 Django Admin 进行流程配置')
    return HttpResponseForbidden('流程模板管理已移除，请使用 Django Admin 进行流程配置')


@login_required
def workflow_detail_disabled(request, workflow_id):
    """审批流程模板详情（G1-5: 已禁用，流程配置仅允许在 Django Admin 中维护）"""
    from django.http import HttpResponseForbidden
    messages.error(request, '流程模板管理已移除，请使用 Django Admin 进行流程配置')
    return HttpResponseForbidden('流程模板管理已移除，请使用 Django Admin 进行流程配置')


@login_required
def workflow_create_disabled(request):
    """创建审批流程模板（G1-5: 已禁用，流程配置仅允许在 Django Admin 中维护）"""
    from django.http import HttpResponseForbidden
    messages.error(request, '流程模板管理已移除，请使用 Django Admin 进行流程配置')
    return HttpResponseForbidden('流程模板管理已移除，请使用 Django Admin 进行流程配置')


@login_required
def workflow_edit_disabled(request, workflow_id):
    """编辑审批流程模板（G1-5: 已禁用，流程配置仅允许在 Django Admin 中维护）"""
    from django.http import HttpResponseForbidden
    messages.error(request, '流程模板管理已移除，请使用 Django Admin 进行流程配置')
    return HttpResponseForbidden('流程模板管理已移除，请使用 Django Admin 进行流程配置')


@login_required
def node_create_disabled(request, workflow_id):
    """创建审批节点（G1-5: 已禁用，流程配置仅允许在 Django Admin 中维护）"""
    from django.http import HttpResponseForbidden
    messages.error(request, '流程模板管理已移除，请使用 Django Admin 进行流程配置')
    return HttpResponseForbidden('流程模板管理已移除，请使用 Django Admin 进行流程配置')


@login_required
def node_edit_disabled(request, node_id):
    """编辑审批节点（G1-5: 已禁用，流程配置仅允许在 Django Admin 中维护）"""
    from django.http import HttpResponseForbidden
    messages.error(request, '流程模板管理已移除，请使用 Django Admin 进行流程配置')
    return HttpResponseForbidden('流程模板管理已移除，请使用 Django Admin 进行流程配置')


@login_required
def node_delete_disabled(request, node_id):
    """删除审批节点（G1-5: 已禁用，流程配置仅允许在 Django Admin 中维护）"""
    from django.http import HttpResponseForbidden
    messages.error(request, '流程模板管理已移除，请使用 Django Admin 进行流程配置')
    return HttpResponseForbidden('流程模板管理已移除，请使用 Django Admin 进行流程配置')


@login_required
def approval_list(request, mode='pending'):
    """审批列表（一分为三：待我审批 / 历史审批 / 我的申请，由 URL mode 区分）"""
    from .services import ApprovalEngine
    from django.core.paginator import Paginator
    
    # 处理批量审批POST请求
    if request.method == 'POST':
        action = request.POST.get('action')  # 'approve' 或 'reject'
        instance_ids = request.POST.getlist('instance_ids')
        
        if not instance_ids:
            messages.error(request, '请至少选择一个审批实例')
            return redirect('workflow_engine:approval_list_pending')
        
        if action not in ['approve', 'reject']:
            messages.error(request, '无效的操作类型')
            return redirect('workflow_engine:approval_list_pending')
        
        # 获取待审批的实例（确保用户有权限审批）
        pending_approvals = ApprovalEngine.get_pending_approvals(request.user)
        instances = pending_approvals.filter(id__in=instance_ids)
        
        if instances.count() != len(instance_ids):
            messages.warning(request, '部分审批实例不存在或您没有权限审批')
        
        success_count = 0
        error_count = 0
        error_messages = []
        
        for instance in instances:
            try:
                result = 'approved' if action == 'approve' else 'rejected'
                comment = f'批量{"通过" if action == "approve" else "驳回"}'
                
                success = ApprovalEngine.approve(
                    instance=instance,
                    approver=request.user,
                    result=result,
                    comment=comment
                )
                
                if success:
                    success_count += 1
                else:
                    error_count += 1
                    error_messages.append(f'{instance.instance_number}: 审批失败（状态不正确或已处理）')
            except Exception as e:
                error_count += 1
                error_messages.append(f'{instance.instance_number}: {str(e)}')
        
        # 审批结果走通知中心，不写入 messages，避免出现在登录页等
        if error_count > 0 and success_count == 0:
            messages.error(request, f'{error_count} 个审批处理失败')
        elif error_count > 0:
            messages.warning(request, f'{success_count} 个已处理，{error_count} 个失败')
        
        return redirect('workflow_engine:approval_list_pending')
    
    # GET请求：显示列表（一分为三：待我审批 / 历史审批 / 我的申请，由 URL 区分）
    tab = mode  # 'pending' | 'historical' | 'my_submitted'
    per_page = request.GET.get('per_page', 13)
    
    # 获取筛选参数
    search = request.GET.get('search', '').strip()
    status_filter = request.GET.get('status', '')
    workflow_id = request.GET.get('workflow', '')
    
    # 待我审批
    pending_approvals = ApprovalEngine.get_pending_approvals(request.user)
    
    # 历史审批 - 用户作为审批人审批过的所有记录（已完成的）
    historical_approvals = ApprovalEngine.get_my_historical_approvals(request.user)
    
    # 我提交的审批（所有我作为申请人提交的审批）
    my_applications = ApprovalEngine.get_my_applications(request.user)
    my_submitted_approvals = my_applications
    
    # 根据标签页选择数据
    if tab == 'historical':
        items = historical_approvals
    elif tab == 'my_submitted':
        items = my_submitted_approvals
    else:
        items = pending_approvals
    
    # 应用筛选条件
    if search:
        from django.db.models import Q
        items = items.filter(
            Q(instance_number__icontains=search) |
            Q(workflow__name__icontains=search) |
            Q(applicant__username__icontains=search) |
            Q(applicant__first_name__icontains=search) |
            Q(applicant__last_name__icontains=search)
        )
    
    if status_filter:
        items = items.filter(status=status_filter)
    
    if workflow_id:
        try:
            workflow_id_int = int(workflow_id)
            items = items.filter(workflow_id=workflow_id_int)
        except (ValueError, TypeError):
            pass
    
    # 获取所有流程列表（用于筛选下拉框）
    from backend.apps.workflow_engine.models import WorkflowTemplate
    workflows = WorkflowTemplate.objects.filter(status='active').order_by('name')
    
    # 分页
    paginator = Paginator(items, per_page)
    page_number = request.GET.get('page', 1)
    page_obj = paginator.get_page(page_number)
    
    _titles = {
        'pending': ("审批引擎 - 待我审批", "📋", "需要我审批的申请"),
        'historical': ("审批引擎 - 历史审批", "📋", "我审批过的记录"),
        'my_submitted': ("审批引擎 - 我的申请", "📋", "我提交的审批申请"),
    }
    title, icon, desc = _titles.get(tab, _titles['pending'])
    context = _context(title, icon, desc, request=request)
    context.update({
        'tab': tab,
        'pending_approvals': pending_approvals,
        'historical_approvals': historical_approvals,
        'my_submitted_approvals': my_submitted_approvals,
        'page_obj': page_obj,
        'pending_count': pending_approvals.count(),
        'historical_count': historical_approvals.count(),
        'my_submitted_count': my_submitted_approvals.count(),
        'column_settings_btn': True,  # 启用列设置按钮
        'workflows': workflows,  # 流程列表，用于筛选
    })
    
    return render(request, 'workflow_engine/approval_list.html', context)


@login_required
def approval_detail(request, instance_id):
    """审批详情"""
    # 先尝试获取实例
    try:
        instance = ApprovalInstance.objects.get(id=instance_id)
    except ApprovalInstance.DoesNotExist:
        raise Http404("审批实例不存在")
    
    # 权限检查：只有申请人、审批人或管理员可以查看
    user = request.user
    has_permission = False
    
    # 超级用户或员工可以查看所有
    if user.is_superuser or user.is_staff:
        has_permission = True
    # 申请人和审批人可以查看
    elif instance.applicant == user:
        has_permission = True
    elif instance.records.filter(approver=user).exists():
        has_permission = True
    
    if not has_permission:
        raise Http404("您没有权限查看此审批实例")
    
    # 获取审批记录，按节点序号和时间排序
    records = instance.records.all().select_related('node', 'approver').order_by('node__sequence', 'approval_time', 'created_time')
    
    # 对于已完成的审批流程，优化显示逻辑
    # 按节点分组，标记每个节点的最终状态
    from collections import defaultdict
    records_by_node = defaultdict(list)
    node_status = {}
    record_is_obsolete = {}  # 记录哪些审批记录是过时的（节点已由他人处理完成）
    
    for record in records:
        records_by_node[record.node_id].append(record)
        # 记录每个节点的最终状态（优先显示已通过/已驳回的记录）
        if record.node_id not in node_status:
            node_status[record.node_id] = record.result
        elif record.result in ['approved', 'rejected']:
            node_status[record.node_id] = record.result
    
    # 标记过时的记录（已完成流程中，节点已通过/驳回，但记录仍为pending的）
    # 同时为每个记录对象添加 is_obsolete 属性，方便模板使用
    if instance.status != 'pending':
        for record in records:
            node_final_status = node_status.get(record.node_id, '')
            is_obsolete = record.result == 'pending' and node_final_status in ['approved', 'rejected']
            record_is_obsolete[record.id] = is_obsolete
            record.is_obsolete = is_obsolete  # 添加属性到记录对象
    else:
        for record in records:
            record.is_obsolete = False
    
    # 检查是否可以审批
    can_approve = False
    if instance.status == 'pending' and instance.current_node:
        pending_record = records.filter(
            approver=request.user,
            result='pending'
        ).first()
        can_approve = pending_record is not None
    
    # 获取关联的业务对象及其详细信息
    content_object = None
    content_object_detail_url = None
    content_object_type_name = None
    
    if instance.content_type and instance.object_id:
        try:
            model_name = instance.content_type.model
            # 按类型带 select_related 获取，便于审批页展示申请人提交的原始表单信息
            if model_name == 'businesscontract':
                from backend.apps.contract_management.models import BusinessContract
                content_object = BusinessContract.objects.select_related(
                    'client', 'project', 'opportunity', 'department', 'business_manager'
                ).filter(id=instance.object_id).first()
            elif model_name == 'businessopportunity':
                from backend.apps.opportunity_management.models import BusinessOpportunity
                content_object = BusinessOpportunity.objects.select_related(
                    'client', 'business_manager', 'service_type', 'drawing_stage', 'created_by'
                ).filter(id=instance.object_id).first()
            elif model_name == 'loanapplication':
                from backend.apps.administrative_management.models import LoanApplication
                content_object = LoanApplication.objects.select_related(
                    'applicant', 'department'
                ).filter(id=instance.object_id).first()
            else:
                content_object = instance.content_type.get_object_for_this_type(id=instance.object_id)

            # 根据不同的业务对象类型，生成业务详情页链接（非审批详情页）
            if model_name == 'client':
                try:
                    content_object_detail_url = reverse('customer_pages:customer_detail', args=[instance.object_id])
                    content_object_type_name = '客户'
                except Exception:
                    pass
            elif model_name == 'businesscontract':
                try:
                    content_object_detail_url = reverse('contract_pages:contract_detail', args=[instance.object_id])
                    content_object_type_name = '合同'
                except:
                    pass
            elif model_name == 'businessopportunity':
                try:
                    content_object_detail_url = reverse('opportunity_pages:opportunity_detail', args=[instance.object_id])
                    content_object_type_name = '商机'
                except:
                    pass
            elif model_name == 'project':
                try:
                    content_object_detail_url = reverse('production_pages:project_detail', args=[instance.object_id])
                    content_object_type_name = '项目'
                except:
                    pass
            elif model_name == 'plan':
                try:
                    content_object_detail_url = reverse('plan_pages:plan_detail', args=[instance.object_id])
                    content_object_type_name = '计划'
                except:
                    pass
            elif model_name == 'sealusage':
                try:
                    content_object_detail_url = reverse('admin_pages:seal_usage_detail', args=[instance.object_id])
                    content_object_type_name = '用印申请'
                except (NoReverseMatch, Exception) as e:
                    # 如果reverse失败，尝试直接构造URL路径（基于URL配置：/administrative/seals/usages/<usage_id>/）
                    import logging
                    logger = logging.getLogger(__name__)
                    logger.warning(f'无法通过reverse生成用印申请详情URL: {str(e)}，尝试直接构造URL')
                    try:
                        # 根据URL配置：path('administrative/', include(...)) + path("seals/usages/<int:usage_id>/", ...)
                        content_object_detail_url = f'/administrative/seals/usages/{instance.object_id}/'
                        content_object_type_name = '用印申请'
                    except Exception as e2:
                        logger.error(f'构造用印申请详情URL失败: {str(e2)}')
                        content_object_detail_url = None
                        content_object_type_name = '用印申请'
            elif model_name == 'sealborrowing':
                # 印章借用没有详情页，不设置详情链接
                content_object_detail_url = None
                content_object_type_name = '印章借用'
            elif model_name == 'loanapplication':
                try:
                    content_object_detail_url = reverse('admin_pages:loan_detail', args=[instance.object_id])
                    content_object_type_name = '借款申请'
                except Exception:
                    pass
            else:
                content_object_type_name = model_name
                # 对于其他类型，如果没有详情页，不设置详情链接（不显示按钮）
                # 不再使用admin链接，因为需要admin登录
        except Exception as e:
            import logging
            logger = logging.getLogger(__name__)
            logger.warning(f'获取关联对象失败: {str(e)}')
    
    context = _context(
        f"审批详情 - {instance.instance_number}",
        "📋",
        f"流程：{instance.workflow.name}",
        request=request,
    )
    
    # 获取用户列表（用于转交，仅同公司用户）
    from django.contrib.auth import get_user_model
    User = get_user_model()
    all_users = User.objects.filter(is_active=True).order_by('username')[:100]
    if getattr(request.user, 'company_id', None):
        all_users = all_users.filter(company_id=request.user.company_id)
    
    # 为审批记录添加排序后的记录列表（用于三栏布局）
    instance.records_sorted = sorted(
        records,
        key=lambda r: (r.node.sequence if r.node else 999, r.approval_time or r.created_time)
    )
    
    approval_allow_transfer = getattr(instance.workflow, 'allow_transfer', False) if instance.workflow else False
    approval_form_action = reverse('workflow_engine:approval_action', args=[instance.id]) if instance else ''
    transfer_form_action = reverse('workflow_engine:approval_action', args=[instance.id]) if instance and approval_allow_transfer else ''

    context.update({
        'instance': instance,
        'object': instance,  # 为三栏布局模板提供 object 变量
        'records': records,
        'records_by_node': dict(records_by_node),
        'node_status': node_status,
        'record_is_obsolete': record_is_obsolete,
        'can_approve': can_approve,
        'content_object': content_object,
        'content_object_detail_url': content_object_detail_url,
        'content_object_type_name': content_object_type_name,
        'all_users': all_users,  # 用于转交的用户列表
        'approval_allow_transfer': approval_allow_transfer,
        'approval_form_action': approval_form_action,
        'transfer_form_action': transfer_form_action,
    })
    
    # 统一使用三栏布局模板（旧的两栏布局已弃用）
    return render(request, "workflow_engine/approval_detail_three_column.html", context)


@login_required
def approval_action(request, instance_id):
    """执行审批操作"""
    instance = get_object_or_404(ApprovalInstance, id=instance_id)
    
    if request.method == 'POST':
        from .services import ApprovalEngine
        
        action = request.POST.get('action')  # approve, reject, transfer
        comment = request.POST.get('comment', '')
        transferred_to_id = request.POST.get('transferred_to', '')
        
        try:
            if action == 'approve':
                success = ApprovalEngine.approve(
                    instance=instance,
                    approver=request.user,
                    result='approved',
                    comment=comment
                )
                if not success:
                    messages.error(request, '审批操作失败')
                # 审批结果走通知中心，不写入 success messages
            
            elif action == 'reject':
                success = ApprovalEngine.approve(
                    instance=instance,
                    approver=request.user,
                    result='rejected',
                    comment=comment
                )
                if not success:
                    messages.error(request, '驳回操作失败')
                # 审批结果走通知中心，不写入 success messages
            
            elif action == 'transfer' and transferred_to_id:
                transferred_to = get_object_or_404(User, id=transferred_to_id)
                success = ApprovalEngine.approve(
                    instance=instance,
                    approver=request.user,
                    result='transferred',
                    comment=comment,
                    transferred_to=transferred_to
                )
                if not success:
                    messages.error(request, '转交操作失败')
                # 审批结果走通知中心，不写入 success messages
            
            # 支持自定义重定向URL（通过 next 参数）
            next_url = request.POST.get('next') or request.GET.get('next')
            if next_url:
                return redirect(next_url)
            return redirect('workflow_engine:approval_list_pending')
            
        except Exception as e:
            import logging
            logger = logging.getLogger(__name__)
            logger.exception('审批操作失败: %s', str(e))
            messages.error(request, f'审批操作失败：{str(e)}')
    
    # 支持自定义重定向URL（通过 next 参数）
    next_url = request.GET.get('next')
    if next_url:
        return redirect(next_url)
    return redirect('workflow_engine:approval_list_pending')


@login_required
def approval_withdraw(request, instance_id):
    """撤回审批"""
    instance = get_object_or_404(ApprovalInstance, id=instance_id)
    
    # 检查权限：只有申请人可以撤回
    if instance.applicant != request.user:
        messages.error(request, '您没有权限撤回此审批')
        return redirect('workflow_engine:approval_list_my_submitted')
    
    # 检查是否可以撤回：只要状态是 pending（还没有审批完成），就允许撤回
    if instance.status != 'pending':
        messages.error(request, '只有审批中的申请才能撤回')
        return redirect('workflow_engine:approval_list_my_submitted')
    
    # 注意：不再检查 workflow.allow_withdraw，因为所有待审批的流程都应该允许撤回
    # 如果流程配置不允许撤回，可以在流程配置中设置，但默认允许撤回
    
    from .services import ApprovalEngine
    
    try:
        success = ApprovalEngine.withdraw(instance, request.user)
        if success:
            messages.success(request, '审批已成功撤回')
        else:
            messages.error(request, '撤回失败')
    except Exception as e:
        import logging
        logger = logging.getLogger(__name__)
        logger.exception('撤回审批失败: %s', str(e))
        messages.error(request, f'撤回失败：{str(e)}')
    
    return redirect('workflow_engine:approval_list_my_submitted')

