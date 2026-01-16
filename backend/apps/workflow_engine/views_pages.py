"""
审批流程引擎页面视图
"""
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.core.paginator import Paginator
from django.db.models import Q
from django.http import Http404
from backend.apps.workflow_engine.models import WorkflowTemplate, ApprovalNode, ApprovalInstance, ApprovalRecord
from backend.apps.system_management.services import get_user_permission_codes
from backend.apps.system_management.models import User, Role, Department


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
        # 这里可以添加顶部菜单构建逻辑
    return context


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
        "审批流程管理",
        "⚙️",
        "配置和管理审批流程模板",
        request=request,
    )
    context.update({
        'workflows': page_obj,
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
    
    # 待我审批
    pending_approvals = ApprovalEngine.get_pending_approvals(request.user)
    
    # 我的申请
    my_applications = ApprovalEngine.get_my_applications(request.user)
    
    context = _context(
        "我的审批",
        "📋",
        "查看待审批和我的申请",
        request=request,
    )
    context.update({
        'pending_approvals': pending_approvals,
        'my_applications': my_applications,
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
    context.update({
        'instance': instance,
        'records': records,
        'records_by_node': dict(records_by_node),
        'node_status': node_status,
        'record_is_obsolete': record_is_obsolete,
        'can_approve': can_approve,
        'content_object': content_object,
        'content_object_detail_url': content_object_detail_url,
        'content_object_type_name': content_object_type_name,
    })
    
    return render(request, 'workflow_engine/approval_detail.html', context)


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
                if success:
                    messages.success(request, '审批通过')
                else:
                    messages.error(request, '审批操作失败')
            
            elif action == 'reject':
                success = ApprovalEngine.approve(
                    instance=instance,
                    approver=request.user,
                    result='rejected',
                    comment=comment
                )
                if success:
                    messages.success(request, '审批已驳回')
                else:
                    messages.error(request, '驳回操作失败')
            
            elif action == 'transfer' and transferred_to_id:
                transferred_to = get_object_or_404(User, id=transferred_to_id)
                success = ApprovalEngine.approve(
                    instance=instance,
                    approver=request.user,
                    result='transferred',
                    comment=comment,
                    transferred_to=transferred_to
                )
                if success:
                    messages.success(request, f'审批已转交给 {transferred_to.username}')
                else:
                    messages.error(request, '转交操作失败')
            
            return redirect('workflow_engine:approval_detail', instance_id=instance.id)
            
        except Exception as e:
            import logging
            logger = logging.getLogger(__name__)
            logger.exception('审批操作失败: %s', str(e))
            messages.error(request, f'审批操作失败：{str(e)}')
    
    return redirect('workflow_engine:approval_detail', instance_id=instance.id)

