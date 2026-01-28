"""
审批流程引擎页面视图
"""
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.core.paginator import Paginator
from django.db.models import Q
from django.http import Http404
from django.urls import reverse
from backend.apps.workflow_engine.models import WorkflowTemplate, ApprovalNode, ApprovalInstance, ApprovalRecord
from backend.apps.system_management.services import get_user_permission_codes
from backend.apps.system_management.models import User, Role, Department
from backend.core.views import _build_full_top_nav, _permission_granted


# ==================== 审批引擎模块左侧菜单结构 =====================
WORKFLOW_ENGINE_MENU = [
    {
        'id': 'workflow_home',
        'label': '审批引擎首页',
        'icon': '🏠',
        'url_name': 'workflow_engine:workflow_home_alt',
        'permission': 'workflow_engine.view',
        'path_keywords': ['home'],
    },
    {
        'id': 'workflow_management',
        'label': '流程管理',
        'icon': '⚙️',
        'permission': 'workflow_engine.view',
        'expanded': True,
        'children': [
            {
                'id': 'workflow_list',
                'label': '流程模板',
                'icon': '📄',
                'url_name': 'workflow_engine:workflow_list',
                'permission': 'workflow_engine.view',
                'path_keywords': ['workflow', 'workflows'],
            },
        ],
    },
    {
        'id': 'approval_management',
        'label': '审批管理',
        'icon': '📋',
        'permission': 'workflow_engine.view',
        'expanded': False,
        'children': [
            {
                'id': 'approval_list',
                'label': '我的审批',
                'icon': '✅',
                'url_name': 'workflow_engine:approval_list',
                'permission': 'workflow_engine.view',
                'path_keywords': ['approval', 'approvals'],
            },
            {
                'id': 'my_application_list',
                'label': '我的申请',
                'icon': '📝',
                'url_name': 'workflow_engine:my_application_list',
                'permission': 'workflow_engine.view',
                'path_keywords': ['my-application', 'my_applications'],
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
        # 注意：Django 的 auth 上下文处理器已经自动提供了 context['user'] = request.user
        # 这里不需要再次设置，避免覆盖或混淆
        # context['user'] = request.user  # 已移除：让 Django 上下文处理器自动处理
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
    1. 核心指标卡片：待审批、我的申请
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
        # 不再显示核心指标卡片，改为待办事项卡片形式
        context['core_cards'] = []
        
        # ========== 待办事项 ==========
        # 待我审批统计（使用数据库查询优化性能）
        pending_approvals_qs = ApprovalEngine.get_pending_approvals(request.user)
        pending_count = pending_approvals_qs.count()  # 使用 count() 而不是 len()
        
        # 待我审批（前5条）- 只在需要显示时才查询数据
        todo_items = []
        if pending_count > 0:
            pending_approvals_list = list(pending_approvals_qs[:5])
            for approval in pending_approvals_list:
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
        
        # ========== 我的申请 ==========
        # 我的申请统计（使用数据库查询优化性能）
        my_applications_qs = ApprovalEngine.get_my_applications(request.user)
        my_applications_total = my_applications_qs.count()
        my_applications_pending_count = my_applications_qs.filter(status='pending').count()
        my_applications_approved_count = my_applications_qs.filter(status='approved').count()
        my_applications_rejected_count = my_applications_qs.filter(status='rejected').count()
        
        # 我的申请（前5条）- 显示所有状态的申请，按创建时间排序
        my_pending_items = []
        if my_applications_total > 0:
            my_applications_list = list(my_applications_qs[:5])
            for app in my_applications_list:
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
        context['my_pending_count'] = my_applications_total
        context['my_applications_pending_count'] = my_applications_pending_count
        context['my_applications_approved_count'] = my_applications_approved_count
        context['my_applications_rejected_count'] = my_applications_rejected_count
        
    except Exception as e:
        import logging
        logger = logging.getLogger(__name__)
        logger.exception('获取统计数据失败: %s', str(e))
        # 设置默认值避免模板错误
        context.setdefault('core_cards', [])
        context.setdefault('todo_items', [])
        context.setdefault('my_pending_items', [])
        context.setdefault('pending_approval_count', 0)
        context.setdefault('my_pending_count', 0)
    
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
def workflow_list(request):
    """审批流程模板列表"""
    workflows = WorkflowTemplate.objects.all().order_by('-created_time')
    
    # 搜索
    search = request.GET.get('search', '')
    if search:
        workflows = workflows.filter(
            Q(name__icontains=search) |
            Q(code__icontains=search) |
            Q(description__icontains=search)
        )
    
    # 状态筛选
    status = request.GET.get('status', '')
    if status:
        workflows = workflows.filter(status=status)
    
    # 分页
    page_size = request.GET.get('page_size', '10')
    try:
        per_page = int(page_size)
        if per_page not in [10, 20, 50]:
            per_page = 10
    except (ValueError, TypeError):
        per_page = 10
    
    paginator = Paginator(workflows, per_page)
    page_number = request.GET.get('page', 1)
    page_obj = paginator.get_page(page_number)
    
    context = _context(
        "审批引擎 ----流程模板",
        "⚙️",
        "配置和管理审批流程模板",
        request=request,
    )
    context.update({
        'workflows': page_obj,
        'page_obj': page_obj,  # 为了兼容性，同时传递 page_obj
        'search': search,
        'selected_status': status,
        'status_choices': WorkflowTemplate.STATUS_CHOICES,
    })
    
    return render(request, 'workflow_engine/workflow_list.html', context)


@login_required
def workflow_detail(request, workflow_id):
    """审批流程模板详情"""
    workflow = get_object_or_404(WorkflowTemplate, id=workflow_id)
    nodes = workflow.nodes.all().order_by('sequence')
    
    context = _context(
        f"流程详情 - {workflow.name}",
        "⚙️",
        workflow.description or "查看和配置审批流程节点",
        request=request,
    )
    context.update({
        'workflow': workflow,
        'nodes': nodes,
    })
    
    return render(request, 'workflow_engine/workflow_detail.html', context)


@login_required
def workflow_create(request):
    """创建审批流程模板"""
    if request.method == 'POST':
        try:
            workflow = WorkflowTemplate.objects.create(
                name=request.POST.get('name'),
                code=request.POST.get('code'),
                description=request.POST.get('description', ''),
                category=request.POST.get('category', ''),
                status=request.POST.get('status', 'draft'),
                allow_withdraw=request.POST.get('allow_withdraw') == 'on',
                allow_reject=request.POST.get('allow_reject') == 'on',
                allow_transfer=request.POST.get('allow_transfer') == 'on',
                timeout_hours=int(request.POST.get('timeout_hours', 0) or 0) or None,
                timeout_action=request.POST.get('timeout_action', 'notify'),
                created_by=request.user,
            )
            messages.success(request, f'审批流程 {workflow.name} 创建成功')
            return redirect('workflow_engine:workflow_detail', workflow_id=workflow.id)
        except Exception as e:
            import logging
            logger = logging.getLogger(__name__)
            logger.exception('创建审批流程失败: %s', str(e))
            messages.error(request, f'创建审批流程失败：{str(e)}')
    
    context = _context(
        "创建审批流程",
        "➕",
        "创建新的审批流程模板",
        request=request,
    )
    context.update({
        'status_choices': WorkflowTemplate.STATUS_CHOICES,
        'timeout_action_choices': WorkflowTemplate._meta.get_field('timeout_action').choices,
    })
    
    return render(request, 'workflow_engine/workflow_form.html', context)


@login_required
def workflow_edit(request, workflow_id):
    """编辑审批流程模板"""
    workflow = get_object_or_404(WorkflowTemplate, id=workflow_id)
    
    if request.method == 'POST':
        try:
            workflow.name = request.POST.get('name')
            workflow.code = request.POST.get('code')
            workflow.description = request.POST.get('description', '')
            workflow.category = request.POST.get('category', '')
            workflow.status = request.POST.get('status', 'draft')
            workflow.allow_withdraw = request.POST.get('allow_withdraw') == 'on'
            workflow.allow_reject = request.POST.get('allow_reject') == 'on'
            workflow.allow_transfer = request.POST.get('allow_transfer') == 'on'
            timeout_hours = request.POST.get('timeout_hours', '')
            workflow.timeout_hours = int(timeout_hours) if timeout_hours else None
            workflow.timeout_action = request.POST.get('timeout_action', 'notify')
            workflow.save()
            
            messages.success(request, f'审批流程 {workflow.name} 更新成功')
            return redirect('workflow_engine:workflow_detail', workflow_id=workflow.id)
        except Exception as e:
            import logging
            logger = logging.getLogger(__name__)
            logger.exception('更新审批流程失败: %s', str(e))
            messages.error(request, f'更新审批流程失败：{str(e)}')
    
    context = _context(
        f"编辑审批流程 - {workflow.name}",
        "✏️",
        "编辑审批流程模板",
        request=request,
    )
    context.update({
        'workflow': workflow,
        'status_choices': WorkflowTemplate.STATUS_CHOICES,
        'timeout_action_choices': WorkflowTemplate._meta.get_field('timeout_action').choices,
    })
    
    return render(request, 'workflow_engine/workflow_form.html', context)


@login_required
def node_create(request, workflow_id):
    """创建审批节点"""
    workflow = get_object_or_404(WorkflowTemplate, id=workflow_id)
    
    if request.method == 'POST':
        try:
            node = ApprovalNode.objects.create(
                workflow=workflow,
                name=request.POST.get('name'),
                node_type=request.POST.get('node_type', 'approval'),
                sequence=int(request.POST.get('sequence', 1)),
                approver_type=request.POST.get('approver_type', ''),
                approval_mode=request.POST.get('approval_mode', 'single'),
                is_required=request.POST.get('is_required') == 'on',
                can_reject=request.POST.get('can_reject') == 'on',
                can_transfer=request.POST.get('can_transfer') == 'on',
                timeout_hours=int(request.POST.get('timeout_hours', 0) or 0) or None,
                description=request.POST.get('description', ''),
            )
            
            # 设置审批人
            approver_user_ids = request.POST.getlist('approver_users')
            if approver_user_ids:
                node.approver_users.set(approver_user_ids)
            
            approver_role_ids = request.POST.getlist('approver_roles')
            if approver_role_ids:
                node.approver_roles.set(approver_role_ids)
            
            approver_dept_ids = request.POST.getlist('approver_departments')
            if approver_dept_ids:
                node.approver_departments.set(approver_dept_ids)
            
            messages.success(request, f'审批节点 {node.name} 创建成功')
            return redirect('workflow_engine:workflow_detail', workflow_id=workflow.id)
        except Exception as e:
            import logging
            logger = logging.getLogger(__name__)
            logger.exception('创建审批节点失败: %s', str(e))
            messages.error(request, f'创建审批节点失败：{str(e)}')
    
    context = _context(
        f"创建审批节点 - {workflow.name}",
        "➕",
        "为审批流程添加审批节点",
        request=request,
    )
    context.update({
        'workflow': workflow,
        'node_type_choices': ApprovalNode.NODE_TYPE_CHOICES,
        'approver_type_choices': ApprovalNode.APPROVER_TYPE_CHOICES,
        'approval_mode_choices': ApprovalNode.APPROVAL_MODE_CHOICES,
        'users': User.objects.filter(is_active=True).order_by('username'),
        'roles': Role.objects.all().order_by('name'),
        'departments': Department.objects.all().order_by('name'),
    })
    
    return render(request, 'workflow_engine/node_form.html', context)


@login_required
def node_edit(request, node_id):
    """编辑审批节点"""
    node = get_object_or_404(ApprovalNode, id=node_id)
    workflow = node.workflow
    
    if request.method == 'POST':
        try:
            node.name = request.POST.get('name')
            node.node_type = request.POST.get('node_type', 'approval')
            node.sequence = int(request.POST.get('sequence', 1))
            node.approver_type = request.POST.get('approver_type', '')
            node.approval_mode = request.POST.get('approval_mode', 'single')
            node.is_required = request.POST.get('is_required') == 'on'
            node.can_reject = request.POST.get('can_reject') == 'on'
            node.can_transfer = request.POST.get('can_transfer') == 'on'
            timeout_hours = request.POST.get('timeout_hours', '')
            node.timeout_hours = int(timeout_hours) if timeout_hours else None
            node.description = request.POST.get('description', '')
            node.save()
            
            # 更新审批人
            approver_user_ids = request.POST.getlist('approver_users')
            node.approver_users.set(approver_user_ids)
            
            approver_role_ids = request.POST.getlist('approver_roles')
            node.approver_roles.set(approver_role_ids)
            
            approver_dept_ids = request.POST.getlist('approver_departments')
            node.approver_departments.set(approver_dept_ids)
            
            messages.success(request, f'审批节点 {node.name} 更新成功')
            return redirect('workflow_engine:workflow_detail', workflow_id=workflow.id)
        except Exception as e:
            import logging
            logger = logging.getLogger(__name__)
            logger.exception('更新审批节点失败: %s', str(e))
            messages.error(request, f'更新审批节点失败：{str(e)}')
    
    context = _context(
        f"编辑审批节点 - {node.name}",
        "✏️",
        "编辑审批节点配置",
        request=request,
    )
    context.update({
        'node': node,
        'workflow': workflow,
        'node_type_choices': ApprovalNode.NODE_TYPE_CHOICES,
        'approver_type_choices': ApprovalNode.APPROVER_TYPE_CHOICES,
        'approval_mode_choices': ApprovalNode.APPROVAL_MODE_CHOICES,
        'users': User.objects.filter(is_active=True).order_by('username'),
        'roles': Role.objects.all().order_by('name'),
        'departments': Department.objects.all().order_by('name'),
    })
    
    return render(request, 'workflow_engine/node_form.html', context)


@login_required
def node_delete(request, node_id):
    """删除审批节点"""
    node = get_object_or_404(ApprovalNode, id=node_id)
    workflow = node.workflow
    
    if request.method == 'POST':
        try:
            node_name = node.name
            node.delete()
            messages.success(request, f'审批节点 {node_name} 已删除')
        except Exception as e:
            import logging
            logger = logging.getLogger(__name__)
            logger.exception('删除审批节点失败: %s', str(e))
            messages.error(request, f'删除审批节点失败：{str(e)}')
    
    return redirect('workflow_engine:workflow_detail', workflow_id=workflow.id)


@login_required
def approval_list(request):
    """我的审批列表"""
    from .services import ApprovalEngine
    from django.core.paginator import Paginator
    
    # 处理批量审批POST请求
    if request.method == 'POST':
        action = request.POST.get('action')  # 'approve' 或 'reject'
        instance_ids = request.POST.getlist('instance_ids')
        
        if not instance_ids:
            messages.error(request, '请至少选择一个审批实例')
            return redirect('workflow_engine:approval_list')
        
        if action not in ['approve', 'reject']:
            messages.error(request, '无效的操作类型')
            return redirect('workflow_engine:approval_list')
        
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
        
        return redirect('workflow_engine:approval_list')
    
    # GET请求：显示列表
    # 获取标签页参数
    tab = request.GET.get('tab', 'pending')
    per_page = request.GET.get('per_page', 20)
    
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
    
    context = _context(
        "审批引擎 ----我的审批列表",
        "📋",
        "查看待审批和我的申请",
        request=request,
    )
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
def my_application_list(request):
    """我的申请列表"""
    from .services import ApprovalEngine
    from django.core.paginator import Paginator
    
    # 获取分页参数
    per_page = request.GET.get('per_page', 20)
    
    # 获取筛选参数
    search = request.GET.get('search', '').strip()
    status_filter = request.GET.get('status', '')
    workflow_id = request.GET.get('workflow', '')
    
    # 我提交的审批（所有我作为申请人提交的审批）
    my_applications = ApprovalEngine.get_my_applications(request.user)
    
    # 应用筛选条件
    if search:
        from django.db.models import Q
        my_applications = my_applications.filter(
            Q(instance_number__icontains=search) |
            Q(workflow__name__icontains=search) |
            Q(applicant__username__icontains=search) |
            Q(applicant__first_name__icontains=search) |
            Q(applicant__last_name__icontains=search)
        )
    
    if status_filter:
        my_applications = my_applications.filter(status=status_filter)
    
    if workflow_id:
        try:
            workflow_id_int = int(workflow_id)
            my_applications = my_applications.filter(workflow_id=workflow_id_int)
        except (ValueError, TypeError):
            pass
    
    # 获取所有流程列表（用于筛选下拉框）
    from backend.apps.workflow_engine.models import WorkflowTemplate
    workflows = WorkflowTemplate.objects.filter(status='active').order_by('name')
    
    # 统计各状态数量
    total_count = my_applications.count()
    pending_count = my_applications.filter(status='pending').count()
    approved_count = my_applications.filter(status='approved').count()
    rejected_count = my_applications.filter(status='rejected').count()
    withdrawn_count = my_applications.filter(status='withdrawn').count()
    
    # 分页
    paginator = Paginator(my_applications, per_page)
    page_number = request.GET.get('page', 1)
    page_obj = paginator.get_page(page_number)
    
    context = _context(
        "我的申请",
        "📝",
        "查看我提交的所有审批申请",
        request=request,
    )
    context.update({
        'page_obj': page_obj,
        'total_count': total_count,
        'pending_count': pending_count,
        'approved_count': approved_count,
        'rejected_count': rejected_count,
        'withdrawn_count': withdrawn_count,
        'column_settings_btn': True,  # 启用列设置按钮
        'workflows': workflows,  # 流程列表，用于筛选
    })
    
    return render(request, 'workflow_engine/my_application_list.html', context)


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
            content_object = instance.content_type.get_object_for_this_type(id=instance.object_id)
            model_name = instance.content_type.model
            
            # 根据不同的业务对象类型，生成详情页链接
            if model_name == 'client':
                from django.urls import reverse
                try:
                    content_object_detail_url = reverse('business:customer_detail', args=[instance.object_id])
                    content_object_type_name = '客户'
                except:
                    pass
            elif model_name == 'businesscontract':
                from django.urls import reverse
                try:
                    content_object_detail_url = reverse('business:contract_detail', args=[instance.object_id])
                    content_object_type_name = '合同'
                except:
                    pass
            elif model_name == 'businessopportunity':
                from django.urls import reverse
                try:
                    content_object_detail_url = reverse('business:opportunity_detail', args=[instance.object_id])
                    content_object_type_name = '商机'
                except:
                    pass
            elif model_name == 'project':
                from django.urls import reverse
                try:
                    content_object_detail_url = reverse('production_pages:project_detail', args=[instance.object_id])
                    content_object_type_name = '项目'
                except:
                    pass
            elif model_name == 'plan':
                from django.urls import reverse
                try:
                    content_object_detail_url = reverse('plan_pages:plan_detail', args=[instance.object_id])
                    content_object_type_name = '计划'
                except:
                    pass
            else:
                content_object_type_name = model_name
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
    
    # 获取所有用户列表（用于转交）
    from django.contrib.auth import get_user_model
    User = get_user_model()
    all_users = User.objects.filter(is_active=True).order_by('username')[:100]
    
    # 为审批记录添加排序后的记录列表（用于三栏布局）
    instance.records_sorted = sorted(
        records,
        key=lambda r: (r.node.sequence if r.node else 999, r.approval_time or r.created_time)
    )
    
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
    })
    
    # 默认使用三栏布局模板，可以通过URL参数切换回旧布局
    use_three_column = request.GET.get('layout') != 'old'
    template_name = "workflow_engine/approval_detail_three_column.html" if use_three_column else "workflow_engine/approval_detail.html"
    return render(request, template_name, context)


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
            return redirect('workflow_engine:approval_list')
            
        except Exception as e:
            import logging
            logger = logging.getLogger(__name__)
            logger.exception('审批操作失败: %s', str(e))
            messages.error(request, f'审批操作失败：{str(e)}')
    
    # 支持自定义重定向URL（通过 next 参数）
    next_url = request.GET.get('next')
    if next_url:
        return redirect(next_url)
    return redirect('workflow_engine:approval_list')


@login_required
def approval_withdraw(request, instance_id):
    """撤回审批"""
    instance = get_object_or_404(ApprovalInstance, id=instance_id)
    
    # 检查权限：只有申请人可以撤回
    if instance.applicant != request.user:
        messages.error(request, '您没有权限撤回此审批')
        return redirect('workflow_engine:approval_list')
    
    # 检查是否可以撤回 - 按优先级顺序检查，确保已结束的流程无法撤回
    
    # 第一优先级：检查已完成时间（最严格的检查）
    if instance.completed_time:
        messages.error(request, f'审批已完成（完成时间：{instance.completed_time.strftime("%Y-%m-%d %H:%M:%S")}），无法撤回')
        return redirect(reverse('workflow_engine:approval_list') + '?tab=my_submitted')
    
    # 第二优先级：检查状态 - 明确禁止已结束的流程被撤回
    if instance.status == 'approved':
        messages.error(request, '审批已通过，无法撤回')
        return redirect(reverse('workflow_engine:approval_list') + '?tab=my_submitted')
    
    if instance.status == 'rejected':
        messages.error(request, '审批已驳回，无法撤回')
        return redirect(reverse('workflow_engine:approval_list') + '?tab=my_submitted')
    
    if instance.status == 'withdrawn':
        messages.error(request, '审批已撤回，无法重复撤回')
        return redirect(reverse('workflow_engine:approval_list') + '?tab=my_submitted')
    
    if instance.status == 'cancelled':
        messages.error(request, '审批已取消，无法撤回')
        return redirect(reverse('workflow_engine:approval_list') + '?tab=my_submitted')
    
    # 第三优先级：只有审批中的状态才能撤回
    if instance.status != 'pending':
        messages.error(request, f'只有审批中的申请才能撤回，当前状态：{instance.get_status_display()}')
        return redirect(reverse('workflow_engine:approval_list') + '?tab=my_submitted')
    
    # 第四优先级：检查流程是否允许撤回
    if not instance.workflow.allow_withdraw:
        messages.error(request, '此流程不允许撤回')
        return redirect(reverse('workflow_engine:approval_list') + '?tab=my_submitted')
    
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
    
    # 使用 reverse() 生成URL字符串，然后拼接查询参数
    return redirect(reverse('workflow_engine:approval_list') + '?tab=my_submitted')

