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
from backend.core.views import _permission_granted, _build_full_top_nav, _build_unified_sidebar_nav
from django.urls import reverse


# ==================== 工作流程引擎左侧菜单结构 =====================
WORKFLOW_ENGINE_MENU = [
    {
        'id': 'workflow_engine_home',
        'label': '工作流引擎首页',
        'icon': '🏠',
        'url_name': 'workflow_engine:workflow_engine_home',
        'permission': 'workflow_engine.view',
    },
    {
        'id': 'workflow_management',
        'label': '流程模板管理',
        'icon': '🔄',
        'permission': 'workflow_engine.view',
        'children': [
            {
                'id': 'workflow_list',
                'label': '流程列表',
                'icon': '📋',
                'url_name': 'workflow_engine:workflow_list',
                'permission': 'workflow_engine.view',
            },
            {
                'id': 'workflow_create',
                'label': '创建流程',
                'icon': '➕',
                'url_name': 'workflow_engine:workflow_create',
                'permission': 'workflow_engine.create',
            },
            {
                'id': 'create_test_instance',
                'label': '审批实例创建',
                'icon': '🧪',
                'url_name': 'workflow_engine:create_test_instance_select',
                'permission': 'workflow_engine.create',
            },
        ]
    },
    {
        'id': 'approval_management',
        'label': '审批管理',
        'icon': '📝',
        'permission': 'workflow_engine.approve',
        'children': [
            {
                'id': 'approval_list',
                'label': '我的审批',
                'icon': '📋',
                'url_name': 'workflow_engine:approval_list',
                'permission': 'workflow_engine.approve',
            },
            {
                'id': 'approval_statistics',
                'label': '审批统计',
                'icon': '📊',
                'url_name': 'workflow_engine:approval_statistics',
                'permission': 'workflow_engine.approve',
            },
        ]
    },
    {
        'id': 'all_workflows',
        'label': '全部流程',
        'icon': '📑',
        'url_name': 'workflow_engine:all_workflows',
        'url_params': '?status=pending',
        'permission': 'workflow_engine.view',
        'children': [
            {
                'id': 'all_workflows_pending',
                'label': '进行中',
                'icon': '🔄',
                'url_name': 'workflow_engine:all_workflows',
                'url_params': '?status=pending',
                'permission': 'workflow_engine.view',
            },
            {
                'id': 'all_workflows_completed',
                'label': '已完成',
                'icon': '✅',
                'url_name': 'workflow_engine:all_workflows',
                'url_params': '?status=completed',
                'permission': 'workflow_engine.view',
            },
            {
                'id': 'all_workflows_archived',
                'label': '已归档',
                'icon': '📦',
                'url_name': 'workflow_engine:all_workflows',
                'url_params': '?status=archived',
                'permission': 'workflow_engine.view',
            },
        ]
    },
]


def _context(page_title, page_icon, description, summary_cards=None, sections=None, request=None, active_menu_id=None):
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
        
        # 构建侧边栏菜单
        context['module_sidebar_nav'] = _build_unified_sidebar_nav(
            WORKFLOW_ENGINE_MENU,
            permission_set,
            active_id=active_menu_id
        )
    else:
        context['full_top_nav'] = []
        context['module_sidebar_nav'] = []
    return context


@login_required
def workflow_engine_home(request):
    """工作流引擎首页"""
    permission_codes = get_user_permission_codes(request.user)
    
    # 权限检查
    if not _permission_granted('workflow_engine.view', permission_codes):
        messages.error(request, '您没有权限访问工作流引擎')
        return redirect('admin:index')
    
    # 收集统计数据
    summary_cards = []
    
    try:
        # 审批流程模板统计
        if _permission_granted('workflow_engine.view', permission_codes):
            try:
                total_templates = WorkflowTemplate.objects.count()
                active_templates = WorkflowTemplate.objects.filter(status='active').count()
                
                summary_cards.append({
                    'label': '流程模板',
                    'icon': '🔄',
                    'value': str(total_templates),
                    'subvalue': f'启用 {active_templates} 个',
                    'url': reverse('workflow_engine:workflow_list'),
                    'variant': 'info'
                })
            except Exception:
                pass
        
        # 待我审批统计
        if _permission_granted('workflow_engine.approve', permission_codes):
            try:
                # 通过ApprovalRecord查找待我审批的实例
                from backend.apps.workflow_engine.models import ApprovalRecord
                pending_records = ApprovalRecord.objects.filter(
                    approver=request.user,
                    result='pending'
                ).values('instance').distinct()
                pending_approvals = pending_records.count()
                
                summary_cards.append({
                    'label': '待我审批',
                    'icon': '📝',
                    'value': str(pending_approvals),
                    'subvalue': '待处理的审批',
                    'url': reverse('workflow_engine:approval_list'),
                    'variant': 'warning'
                })
            except Exception:
                pass
        
        # 我的申请统计
        try:
            my_applications = ApprovalInstance.objects.filter(
                applicant=request.user,
                status__in=['pending', 'draft']
            ).count()
            
            summary_cards.append({
                'label': '我的申请',
                'icon': '📋',
                'value': str(my_applications),
                'subvalue': '进行中的申请',
                'url': reverse('workflow_engine:approval_list'),
                'variant': 'info'
            })
        except Exception:
            pass
        
        # 本月审批统计
        try:
            from datetime import datetime, timedelta
            from django.utils import timezone
            month_start = timezone.now().replace(day=1, hour=0, minute=0, second=0, microsecond=0)
            month_approvals = ApprovalInstance.objects.filter(
                status='approved',
                completed_time__gte=month_start
            ).count()
            
            summary_cards.append({
                'label': '本月审批',
                'icon': '✅',
                'value': str(month_approvals),
                'subvalue': '已完成审批',
                'variant': 'success'
            })
        except Exception:
            pass
    except Exception as e:
        import logging
        logger = logging.getLogger(__name__)
        logger.exception('获取统计数据失败: %s', str(e))
    
    # 功能模块入口
    module_entries = []
    
    if _permission_granted('workflow_engine.view', permission_codes):
        try:
            module_entries.append({
                'label': '流程模板',
                'icon': '🔄',
                'description': '管理审批流程模板',
                'url': reverse('workflow_engine:workflow_list'),
                'link_label': '进入模块 →'
            })
        except Exception:
            pass
    
    if _permission_granted('workflow_engine.approve', permission_codes):
        try:
            module_entries.append({
                'label': '审批统计',
                'icon': '📊',
                'description': '查看审批数据和报表',
                'url': reverse('workflow_engine:approval_statistics'),
                'link_label': '查看统计 →'
            })
        except Exception:
            pass
    
    # 构建区域
    sections = []
    
    if module_entries:
        sections.append({
            'title': '功能模块',
            'description': '工作流引擎的各个功能模块入口',
            'items': module_entries,
            'layout': 'grid'
        })
    
    # 构建上下文
    context = _context(
        page_title="工作流引擎",
        page_icon="🔄",
        description="管理审批流程和工单",
        summary_cards=summary_cards,
        sections=sections,
        request=request,
        active_menu_id='workflow_engine_home',
    )
    
    return render(request, "workflow_engine/home.html", context)


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
    
    # 分页（固定为每页 10 条，符合 list_page_base.html 模板规定）
    per_page = 10
    paginator = Paginator(workflows, per_page)
    page_number = request.GET.get('page', 1)
    page_obj = paginator.get_page(page_number)
    
    # 构建上下文（符合 list_page_base.html 模板要求）
    context = _context(
        "审批流程管理",
        "⚙️",
        "配置和管理审批流程模板",
        request=request,
        active_menu_id='workflow_list',
    )
    # 列表模板必需字段
    context.update({
        'page_obj': page_obj,  # 分页对象，包含 object_list
        'page_title': '审批流程管理',  # 页面标题
        'search': search,  # 搜索关键词
        'selected_status': status,  # 选中的状态
        'status_choices': WorkflowTemplate.STATUS_CHOICES,  # 状态选项
    })
    
    return render(request, 'workflow_engine/workflow_list.html', context)


@login_required
def workflow_detail(request, workflow_id):
    """审批流程模板详情"""
    workflow = get_object_or_404(WorkflowTemplate, id=workflow_id)
    nodes = workflow.nodes.all().order_by('sequence')
    
    # 统计信息
    from django.db.models import Count, Q
    from django.utils import timezone
    from datetime import timedelta
    
    # 流程实例统计
    total_instances = ApprovalInstance.objects.filter(workflow=workflow).count()
    pending_instances = ApprovalInstance.objects.filter(workflow=workflow, status='pending').count()
    approved_instances = ApprovalInstance.objects.filter(workflow=workflow, status='approved').count()
    rejected_instances = ApprovalInstance.objects.filter(workflow=workflow, status='rejected').count()
    
    # 计算通过率
    completed_count = approved_instances + rejected_instances
    approval_rate = (approved_instances / completed_count * 100) if completed_count > 0 else 0
    
    # 最近30天的使用情况
    thirty_days_ago = timezone.now() - timedelta(days=30)
    recent_instances = ApprovalInstance.objects.filter(
        workflow=workflow,
        created_time__gte=thirty_days_ago
    ).count()
    
    # 平均审批时长（已完成实例）
    completed_instances = ApprovalInstance.objects.filter(
        workflow=workflow,
        status__in=['approved', 'rejected'],
        completed_time__isnull=False
    ).exclude(apply_time__isnull=True)
    
    avg_duration = None
    if completed_instances.exists():
        durations = []
        for instance in completed_instances:
            if instance.apply_time and instance.completed_time:
                duration = (instance.completed_time - instance.apply_time).total_seconds() / 3600  # 转换为小时
                durations.append(duration)
        if durations:
            avg_duration = sum(durations) / len(durations)
    
    # 节点统计
    node_stats = []
    for node in nodes:
        if node.node_type == 'approval':
            node_records = ApprovalRecord.objects.filter(
                instance__workflow=workflow,
                node=node
            )
            node_pending = node_records.filter(result='pending').count()
            node_approved = node_records.filter(result='approved').count()
            node_rejected = node_records.filter(result='rejected').count()
            node_stats.append({
                'node': node,
                'pending': node_pending,
                'approved': node_approved,
                'rejected': node_rejected,
                'total': node_pending + node_approved + node_rejected,
            })
    
    context = _context(
        f"流程详情 - {workflow.name}",
        "⚙️",
        workflow.description or "查看和配置审批流程节点",
        request=request,
        active_menu_id='workflow_list',
    )
    context.update({
        'workflow': workflow,
        'nodes': nodes,
        'total_instances': total_instances,
        'pending_instances': pending_instances,
        'approved_instances': approved_instances,
        'rejected_instances': rejected_instances,
        'approval_rate': approval_rate,
        'recent_instances': recent_instances,
        'avg_duration': avg_duration,
        'node_stats': node_stats,
    })
    
    return render(request, 'workflow_engine/workflow_detail.html', context)


@login_required
def create_test_approval_instance(request, workflow_id):
    """创建测试审批实例"""
    workflow = get_object_or_404(WorkflowTemplate, id=workflow_id)
    
    # 检查流程是否有节点
    if not workflow.nodes.exists():
        messages.error(request, '流程还没有配置节点，无法创建审批实例')
        return redirect('workflow_engine:workflow_detail', workflow_id=workflow_id)
    
    # 检查流程状态
    if workflow.status != 'active':
        messages.warning(request, '流程未启用，建议先启用流程后再创建测试实例')
    
    try:
        from backend.apps.workflow_engine.services import ApprovalEngine
        from django.contrib.contenttypes.models import ContentType
        
        # 创建一个测试业务对象（使用一个简单的测试模型）
        # 如果没有测试模型，我们可以创建一个简单的测试对象
        # 这里我们使用一个虚拟对象，通过ContentType框架关联
        
        # 创建一个测试对象类（临时）
        class TestContentObject:
            """测试用的业务对象"""
            def __init__(self):
                self.id = 999999  # 使用一个特殊的ID
                self.title = f'测试审批对象 - {workflow.name}'
                self.name = self.title
            
            def __str__(self):
                return self.title
        
        test_object = TestContentObject()
        
        # 获取或创建ContentType（使用一个通用的模型，比如User）
        # 或者创建一个专门的测试模型
        # 这里我们使用User模型作为测试对象类型
        from backend.apps.system_management.models import User
        content_type = ContentType.objects.get_for_model(User)
        
        # 检查是否已有测试实例
        existing_instance = ApprovalInstance.objects.filter(
            workflow=workflow,
            content_type=content_type,
            object_id=test_object.id,
            applicant=request.user
        ).first()
        
        if existing_instance and existing_instance.status == 'pending':
            messages.info(request, f'您已有一个待审批的测试实例：{existing_instance.instance_number}')
            return redirect('workflow_engine:approval_detail', instance_id=existing_instance.id)
        
        # 创建审批实例
        # 由于ApprovalEngine.start_approval需要真实的业务对象，我们需要创建一个真实的测试对象
        # 或者修改ApprovalEngine以支持测试模式
        
        # 方案：创建一个真实的测试用户对象作为业务对象
        test_user, created = User.objects.get_or_create(
            username=f'test_approval_{workflow.id}',
            defaults={
                'is_active': False,  # 标记为不活跃，表示这是测试对象
                'user_type': 'internal',
            }
        )
        
        # 启动审批流程
        instance = ApprovalEngine.start_approval(
            workflow=workflow,
            content_object=test_user,  # 使用测试用户作为业务对象
            applicant=request.user,
            comment=f'测试审批实例 - 流程：{workflow.name}'
        )
        
        messages.success(
            request, 
            f'测试审批实例创建成功！实例编号：{instance.instance_number}。'
            f'当前节点：{instance.current_node.name if instance.current_node else "无"}'
        )
        
        return redirect('workflow_engine:approval_detail', instance_id=instance.id)
        
    except Exception as e:
        import logging
        logger = logging.getLogger(__name__)
        logger.exception('创建测试审批实例失败: %s', str(e))
        messages.error(request, f'创建测试审批实例失败：{str(e)}')
        return redirect('workflow_engine:workflow_detail', workflow_id=workflow_id)


@login_required
def workflow_create(request):
    """创建审批流程模板"""
    if request.method == 'POST':
        # 检查是否是保存草稿操作
        action = request.POST.get('action', '')
        is_draft = action == 'save_draft' or request.POST.get('status') == 'draft'
        
        try:
            from django.db import transaction
            import re
            from datetime import datetime
            
            # 流程代码必须由系统自动生成，忽略前端提交的任何code值
            workflow_name = request.POST.get('name', '').strip()
            if not workflow_name:
                messages.error(request, '流程名称不能为空')
                return redirect('workflow_engine:workflow_create')
            
            # 生成基础代码：从流程名称提取有效字符
            # 移除特殊字符，保留字母、数字和中文
            base_code = re.sub(r'[^a-zA-Z0-9\u4e00-\u9fa5]', '', workflow_name)
            
            # 如果是纯中文，转换为拼音首字母（简化处理：使用拼音库或手动映射）
            # 这里使用简化方案：提取前几个字符的拼音首字母
            # 实际项目中可以使用 pypinyin 库：from pypinyin import lazy_pinyin
            # 暂时使用时间戳 + 随机数确保唯一性
            import random
            timestamp = datetime.now().strftime('%Y%m%d%H%M%S')
            random_suffix = random.randint(1000, 9999)
            
            # 处理中文：如果包含中文，使用简化处理
            if re.search(r'[\u4e00-\u9fa5]', base_code):
                # 包含中文，使用固定前缀 + 时间戳
                base_code = 'wf'  # workflow 的缩写
            else:
                # 纯英文或数字，使用前20个字符
                base_code = base_code[:20].lower() if base_code else 'wf'
            
            # 生成唯一代码：wf_时间戳_随机数
            workflow_code = f"{base_code}_{timestamp}_{random_suffix}"
            
            # 确保唯一性（如果冲突，增加随机数）
            counter = 1
            while WorkflowTemplate.objects.filter(code=workflow_code).exists():
                random_suffix = random.randint(1000, 9999)
                workflow_code = f"{base_code}_{timestamp}_{random_suffix}"
                counter += 1
                if counter > 100:  # 防止无限循环
                    # 如果100次都冲突，使用UUID
                    import uuid
                    workflow_code = f"{base_code}_{uuid.uuid4().hex[:8]}"
                    break
            
            # 注意：完全忽略 request.POST.get('code')，始终使用自动生成的代码
            
            with transaction.atomic():
                # 创建流程模板（使用自动生成的代码）
                # 如果是保存草稿，强制设置为draft状态
                workflow_status = 'draft' if is_draft else request.POST.get('status', 'draft')
                
                workflow = WorkflowTemplate.objects.create(
                    name=workflow_name,
                    code=workflow_code,  # 使用自动生成的代码
                    description=request.POST.get('description', ''),
                    category=request.POST.get('category', ''),
                    status=workflow_status,  # 使用处理后的状态
                    allow_withdraw=request.POST.get('allow_withdraw') == 'on',
                    allow_reject=request.POST.get('allow_reject') == 'on',
                    allow_transfer=request.POST.get('allow_transfer') == 'on',
                    timeout_hours=int(request.POST.get('timeout_hours', 0) or 0) or None,
                    timeout_action=request.POST.get('timeout_action', 'notify'),
                    created_by=request.user,
                )
                
                # 处理节点数据（如果通过AJAX提交）
                nodes_data = request.POST.get('nodes_data', '')
                if nodes_data:
                    import json
                    try:
                        nodes = json.loads(nodes_data)
                        for node_data in nodes:
                            node = ApprovalNode.objects.create(
                                workflow=workflow,
                                name=node_data.get('name', ''),
                                node_type=node_data.get('node_type', 'approval'),
                                sequence=int(node_data.get('sequence', 1)),
                                approver_type=node_data.get('approver_type', ''),
                                approval_mode=node_data.get('approval_mode', 'single'),
                                is_required=node_data.get('is_required', True),
                                can_reject=node_data.get('can_reject', True),
                                can_transfer=node_data.get('can_transfer', False),
                                timeout_hours=int(node_data.get('timeout_hours', 0) or 0) or None,
                                description=node_data.get('description', ''),
                                condition_expression=node_data.get('condition_expression', ''),
                            )
                            
                            # 设置审批人（如果需要）
                            if node_data.get('approver_user_ids'):
                                node.approver_users.set(node_data.get('approver_user_ids'))
                            if node_data.get('approver_role_ids'):
                                node.approver_roles.set(node_data.get('approver_role_ids'))
                            if node_data.get('approver_dept_ids'):
                                node.approver_departments.set(node_data.get('approver_dept_ids'))
                    except json.JSONDecodeError:
                        pass  # 忽略JSON解析错误，节点可以在详情页面添加
                
                if is_draft:
                    # 保存草稿
                    success_message = f'草稿已保存：{workflow.name}'
                else:
                    success_message = f'审批流程 {workflow.name} 创建成功'
                
                messages.success(request, success_message)
                
                # 如果是AJAX请求，返回JSON
                if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
                    from django.http import JsonResponse
                    return JsonResponse({
                        'success': True,
                        'message': success_message,
                        'workflow_id': workflow.id,
                        'redirect_url': reverse('workflow_engine:workflow_detail', args=[workflow.id]) if not is_draft else None
                    })
                
                if is_draft:
                    # 保存草稿后，跳转到编辑页面
                    return redirect('workflow_engine:workflow_edit', workflow_id=workflow.id)
                
                return redirect('workflow_engine:workflow_detail', workflow_id=workflow.id)
        except Exception as e:
            import logging
            logger = logging.getLogger(__name__)
            logger.exception('创建审批流程失败: %s', str(e))
            error_message = f'创建审批流程失败：{str(e)}'
            messages.error(request, error_message)
            
            # 如果是AJAX请求，返回JSON错误
            if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
                from django.http import JsonResponse
                return JsonResponse({
                    'success': False,
                    'message': error_message
                }, status=400)
    
    # 获取所有流程模板（用于复制）
    existing_workflows = WorkflowTemplate.objects.all().order_by('-created_time')[:10]
    
    # 获取用户、角色、部门列表（用于节点配置）
    from backend.apps.system_management.models import User, Role, Department
    users = User.objects.filter(is_active=True).order_by('username')[:100]  # 限制数量避免性能问题
    roles = Role.objects.filter(is_active=True).order_by('name')
    departments = Department.objects.filter(is_active=True).order_by('name')
    
    context = _context(
        "创建审批流程",
        "➕",
        "创建新的审批流程模板",
        request=request,
        active_menu_id='workflow_create',
    )
    context.update({
        'status_choices': WorkflowTemplate.STATUS_CHOICES,
        'timeout_action_choices': WorkflowTemplate._meta.get_field('timeout_action').choices,
        'existing_workflows': existing_workflows,
        'approver_type_choices': ApprovalNode.APPROVER_TYPE_CHOICES,
        'approval_mode_choices': ApprovalNode.APPROVAL_MODE_CHOICES,
        'users': users,
        'roles': roles,
        'departments': departments,
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
        active_menu_id='workflow_list',
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
        active_menu_id='workflow_list',
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
        active_menu_id='workflow_list',
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
def my_applications(request):
    """我的申请列表"""
    from .services import ApprovalEngine
    
    # 我的申请
    my_applications = ApprovalEngine.get_my_applications(request.user).select_related(
        'applicant', 'workflow', 'current_node', 'content_type'
    )
    
    # 为每个审批实例加载关联的业务对象
    for instance in my_applications:
        if instance.content_type and instance.object_id:
            try:
                content_object = instance.content_type.get_object_for_this_type(id=instance.object_id)
                instance.content_object = content_object
            except Exception:
                instance.content_object = None
    
    context = _context(
        "我的申请",
        "📤",
        "查看我提交的所有申请",
        request=request,
        active_menu_id='my_applications',
    )
    context.update({
        'my_applications': my_applications,
        'show_only_my_applications': True,  # 标记只显示我的申请
    })
    
    return render(request, 'workflow_engine/approval_list.html', context)


@login_required
def approval_list(request):
    """我的审批列表"""
    from .services import ApprovalEngine
    from django.core.paginator import Paginator
    
    # 获取标签页参数
    tab = request.GET.get('tab', 'pending')
    
    # 待我审批
    pending_approvals = ApprovalEngine.get_pending_approvals(request.user).select_related(
        'applicant', 'workflow', 'current_node', 'content_type'
    )
    
    # 为每个审批实例加载关联的业务对象
    for instance in pending_approvals:
        if instance.content_type and instance.object_id:
            try:
                content_object = instance.content_type.get_object_for_this_type(id=instance.object_id)
                instance.content_object = content_object
            except Exception:
                instance.content_object = None
    
    # 历史审批：用户已经审批过的实例（不管最终状态如何）
    # 查找用户参与过审批的记录，然后获取对应的实例
    from backend.apps.workflow_engine.models import ApprovalRecord
    historical_record_ids = ApprovalRecord.objects.filter(
        approver=request.user,
        result__in=['approved', 'rejected', 'transferred']  # 已审批过的记录
    ).values_list('instance_id', flat=True).distinct()
    
    historical_approvals = ApprovalInstance.objects.filter(
        id__in=historical_record_ids
    ).select_related(
        'applicant', 'workflow', 'current_node', 'content_type'
    ).order_by('-completed_time', '-created_time')
    
    # 为每个历史审批实例加载关联的业务对象
    for instance in historical_approvals:
        if instance.content_type and instance.object_id:
            try:
                content_object = instance.content_type.get_object_for_this_type(id=instance.object_id)
                instance.content_object = content_object
            except Exception:
                instance.content_object = None
    
    # 根据标签页选择要显示的数据
    if tab == 'historical':
        # 显示历史审批，使用分页
        per_page = 10
        paginator = Paginator(historical_approvals, per_page)
        page_number = request.GET.get('page', 1)
        try:
            page_obj = paginator.page(page_number)
        except:
            page_obj = paginator.page(1)
        
        # 为分页后的数据加载业务对象
        for instance in page_obj:
            if instance.content_type and instance.object_id:
                try:
                    content_object = instance.content_type.get_object_for_this_type(id=instance.object_id)
                    instance.content_object = content_object
                except Exception:
                    instance.content_object = None
    else:
        # 显示待审批，使用分页
        per_page = 10
        paginator = Paginator(pending_approvals, per_page)
        page_number = request.GET.get('page', 1)
        try:
            page_obj = paginator.page(page_number)
        except:
            page_obj = paginator.page(1)
        
        # 为分页后的数据加载业务对象
        for instance in page_obj:
            if instance.content_type and instance.object_id:
                try:
                    content_object = instance.content_type.get_object_for_this_type(id=instance.object_id)
                    instance.content_object = content_object
                except Exception:
                    instance.content_object = None
    
    context = _context(
        "我的审批",
        "📋",
        "查看待审批和历史审批",
        request=request,
        active_menu_id='approval_list',
    )
    context.update({
        'pending_approvals': pending_approvals,  # 原始待审批查询集（用于计数）
        'historical_approvals': historical_approvals,  # 原始历史审批查询集（用于计数）
        'page_obj': page_obj,  # 当前页的数据（分页后的）
        'tab': tab,  # 当前标签页
    })
    
    return render(request, 'workflow_engine/approval_list.html', context)


@login_required
def approval_detail(request, instance_id):
    """审批详情"""
    from django.views.decorators.cache import never_cache
    from django.utils.decorators import method_decorator
    
    # 先尝试获取实例，强制从数据库重新查询
    try:
        instance = ApprovalInstance.objects.select_related('workflow', 'applicant', 'current_node', 'content_type').get(id=instance_id)
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
    # 强制从数据库重新查询，避免使用缓存
    records_queryset = instance.records.select_related('node', 'approver', 'transferred_to').order_by('node__sequence', 'approval_time', 'created_time')
    
    # 对于已完成的审批流程，优化显示逻辑
    # 按节点分组，标记每个节点的最终状态
    from collections import defaultdict
    records_by_node = defaultdict(list)
    node_status = {}
    record_is_obsolete = {}  # 记录哪些审批记录是过时的（节点已由他人处理完成）
    
    # 将查询集转换为列表，用于模板渲染
    records = list(records_queryset)
    
    for record in records:
        # 使用字符串作为 key，与模板中的 get_item 保持一致
        node_id_str = str(record.node_id)
        records_by_node[node_id_str].append(record)
        # 记录每个节点的最终状态（优先显示已通过/已驳回的记录）
        if node_id_str not in node_status:
            node_status[node_id_str] = record.result
        elif record.result in ['approved', 'rejected']:
            node_status[node_id_str] = record.result
    
    # 标记过时的记录（已完成流程中，节点已通过/驳回，但记录仍为pending的）
    # 同时为每个记录对象添加 is_obsolete 属性，方便模板使用
    if instance.status != 'pending':
        for record in records:
            node_id_str = str(record.node_id)
            node_final_status = node_status.get(node_id_str, '')
            is_obsolete = record.result == 'pending' and node_final_status in ['approved', 'rejected']
            record_is_obsolete[record.id] = is_obsolete
            record.is_obsolete = is_obsolete  # 添加属性到记录对象
    else:
        for record in records:
            record.is_obsolete = False
    
    # 检查是否可以审批
    can_approve = False
    if instance.status == 'pending' and instance.current_node:
        pending_record = records_queryset.filter(
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
            # 对于outgoingdocument类型，使用select_related预加载client等关联对象
            model_name = instance.content_type.model
            if model_name == 'outgoingdocument':
                from backend.apps.delivery_customer.models import OutgoingDocument
                content_object = OutgoingDocument.objects.select_related('client', 'client_contact', 'project', 'file_category').get(id=instance.object_id)
            else:
                content_object = instance.content_type.get_object_for_this_type(id=instance.object_id)
            
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
            elif model_name == 'outgoingdocument':
                from django.urls import reverse
                try:
                    content_object_detail_url = reverse('delivery_pages:outgoing_document_detail', args=[instance.object_id])
                    content_object_type_name = '发文'
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
        active_menu_id='approval_list',
    )
    # 获取可转交的用户列表（如果允许转交）
    transfer_users = []
    if instance.workflow.allow_transfer and can_approve:
        transfer_users = User.objects.filter(is_active=True).exclude(id=request.user.id).order_by('username')
    
    # 处理发文对象的报送方式列表（如果存在）
    delivery_methods_list = []
    tracking_records = None
    if content_object and hasattr(content_object, 'delivery_methods') and content_object.delivery_methods:
        delivery_methods_list = [method.strip() for method in content_object.delivery_methods.split(',') if method.strip()]
    
    # 获取发文对象的跟踪记录（每种报送方式的详细配置）
    if content_object and hasattr(content_object, 'tracking_records'):
        tracking_records = content_object.tracking_records.select_related('delivery_method', 'document').order_by('created_at')
        # 解析每个跟踪记录中的收件人信息 JSON
        import json
        import re
        for tracking in tracking_records:
            if tracking.notes:
                # 解析邮件收件人信息
                if 'EMAIL_RECIPIENTS_JSON:' in tracking.notes:
                    json_part = tracking.notes.split('EMAIL_RECIPIENTS_JSON:')[1].strip()
                    # 如果有多行，只取第一行（JSON 部分）
                    if '\n' in json_part:
                        json_part = json_part.split('\n')[0].strip()
                    try:
                        tracking.email_recipients_list = json.loads(json_part)
                    except (json.JSONDecodeError, ValueError):
                        tracking.email_recipients_list = []
                else:
                    tracking.email_recipients_list = []
                
                # 解析快递收件人信息
                if 'EXPRESS_RECIPIENTS_JSON:' in tracking.notes:
                    json_part = tracking.notes.split('EXPRESS_RECIPIENTS_JSON:')[1].strip()
                    # 如果有多行，只取第一行（JSON 部分）
                    if '\n' in json_part:
                        json_part = json_part.split('\n')[0].strip()
                    try:
                        tracking.express_recipients_list = json.loads(json_part)
                    except (json.JSONDecodeError, ValueError):
                        tracking.express_recipients_list = []
                else:
                    tracking.express_recipients_list = []
                
                # 解析短信收件人信息
                if 'SMS_RECIPIENTS_JSON:' in tracking.notes:
                    json_part = tracking.notes.split('SMS_RECIPIENTS_JSON:')[1].strip()
                    # 如果有多行，只取第一行（JSON 部分）
                    if '\n' in json_part:
                        json_part = json_part.split('\n')[0].strip()
                    try:
                        tracking.sms_recipients_list = json.loads(json_part)
                    except (json.JSONDecodeError, ValueError):
                        tracking.sms_recipients_list = []
                else:
                    tracking.sms_recipients_list = []
                
                # 清理备注字段，移除 JSON 部分，只保留真正的备注内容
                cleaned_notes = tracking.notes
                # 移除 EMAIL_RECIPIENTS_JSON 行
                cleaned_notes = re.sub(r'EMAIL_RECIPIENTS_JSON:.*?(?:\n|$)', '', cleaned_notes, flags=re.MULTILINE)
                # 移除 EXPRESS_RECIPIENTS_JSON 行
                cleaned_notes = re.sub(r'EXPRESS_RECIPIENTS_JSON:.*?(?:\n|$)', '', cleaned_notes, flags=re.MULTILINE)
                # 移除 SMS_RECIPIENTS_JSON 行
                cleaned_notes = re.sub(r'SMS_RECIPIENTS_JSON:.*?(?:\n|$)', '', cleaned_notes, flags=re.MULTILINE)
                # 移除 EMAIL_RECIPIENTS 行（旧格式）
                cleaned_notes = re.sub(r'EMAIL_RECIPIENTS:.*?(?:\n|$)', '', cleaned_notes, flags=re.MULTILINE)
                # 清理多余的空行
                cleaned_notes = re.sub(r'\n\s*\n', '\n', cleaned_notes)
                cleaned_notes = cleaned_notes.strip()
                # 如果清理后为空，设置为空字符串
                tracking.notes_display = cleaned_notes if cleaned_notes else ''
            else:
                tracking.email_recipients_list = []
                tracking.express_recipients_list = []
                tracking.sms_recipients_list = []
                tracking.notes_display = ''
    else:
        tracking_records = None
    
    # 获取快递公司列表（用于更新快递信息）
    express_companies = []
    if tracking_records:
        from backend.apps.delivery_customer.models import ExpressCompany
        express_companies = ExpressCompany.objects.filter(is_active=True).order_by('sort_order', 'name')
    
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
        'transfer_users': transfer_users,
        'delivery_methods_list': delivery_methods_list,  # 报送方式列表
        'tracking_records': tracking_records,  # 跟踪记录（报送配置详情）
        'express_companies': express_companies,  # 快递公司列表（用于更新快递信息）
    })
    
    # 获取当前节点的审批人列表
    current_node_approvers = []
    if instance.current_node:
        from backend.apps.workflow_engine.services import ApprovalEngine
        current_node_approvers = ApprovalEngine._get_approvers(instance.current_node, instance)
    context['current_node_approvers'] = current_node_approvers
    
    # 为每个节点计算实际的审批人列表（用于显示未开始节点的审批人姓名）
    from backend.apps.workflow_engine.services import ApprovalEngine
    approvers_by_node = {}
    for node in instance.workflow.nodes.all():
        # 只处理审批节点，其他类型节点不需要审批人
        if node.node_type == 'approval':
            # 使用字符串作为 key，与 records_by_node 保持一致
            try:
                approvers = ApprovalEngine._get_approvers(node, instance)
                approvers_by_node[str(node.id)] = approvers
            except Exception as e:
                import logging
                logger = logging.getLogger(__name__)
                logger.error(f'计算节点 {node.name} 的审批人时出错: {str(e)}')
                approvers_by_node[str(node.id)] = []
    context['approvers_by_node'] = approvers_by_node
    
    return render(request, 'workflow_engine/approval_detail.html', context)


@login_required
def query_tracking_express(request, instance_id, tracking_id):
    """查询跟踪记录的快递物流信息"""
    from django.shortcuts import get_object_or_404, redirect
    from django.contrib import messages
    from backend.apps.delivery_customer.models import OutgoingDocumentTracking
    from backend.apps.delivery_customer.tracking_service import ExpressTrackingService
    from backend.apps.workflow_engine.models import ApprovalInstance
    
    # 验证审批实例
    instance = get_object_or_404(ApprovalInstance, id=instance_id)
    
    # 权限检查：只有申请人、审批人或管理员可以操作
    user = request.user
    has_permission = False
    if user.is_superuser or user.is_staff:
        has_permission = True
    elif instance.applicant == user:
        has_permission = True
    elif instance.records.filter(approver=user).exists():
        has_permission = True
    
    if not has_permission:
        messages.error(request, '您没有权限执行此操作')
        return redirect('workflow_engine:approval_detail', instance_id=instance_id)
    
    # 获取跟踪记录
    tracking = get_object_or_404(
        OutgoingDocumentTracking.objects.select_related('document', 'delivery_method'),
        id=tracking_id
    )
    
    # 检查是否为快递方式
    if not tracking.delivery_method or tracking.delivery_method.code != 'express':
        messages.error(request, '此跟踪记录不是快递方式，无法查询物流信息')
        return redirect('workflow_engine:approval_detail', instance_id=instance_id)
    
    # 检查是否有快递公司和快递单号
    express_company = tracking.express_company or (tracking.document.express_company if tracking.document else '')
    express_number = tracking.express_number or (tracking.document.express_number if tracking.document else '')
    
    if not express_company or not express_number:
        messages.error(request, '快递公司或快递单号为空，请先更新快递信息')
        return redirect('workflow_engine:approval_detail', instance_id=instance_id)
    
    try:
        # 查询快递状态
        success, message = ExpressTrackingService.query_express_status(tracking)
        
        if success:
            messages.success(request, f'物流查询成功：{message}')
        else:
            messages.warning(request, f'物流查询失败：{message}')
    except Exception as e:
        import logging
        logger = logging.getLogger(__name__)
        logger.error(f"查询快递物流信息失败: {str(e)}", exc_info=True)
        messages.error(request, f'查询失败：{str(e)}')
    
    return redirect('workflow_engine:approval_detail', instance_id=instance_id)


@login_required
def update_tracking_express(request, instance_id, tracking_id):
    """更新跟踪记录的快递信息（在审批详情页面）"""
    from django.shortcuts import get_object_or_404, redirect
    from django.contrib import messages
    from backend.apps.delivery_customer.models import OutgoingDocumentTracking
    from backend.apps.delivery_customer.tracking_service import ExpressTrackingService
    from backend.apps.workflow_engine.models import ApprovalInstance
    import logging
    
    logger = logging.getLogger(__name__)
    
    # 验证审批实例
    instance = get_object_or_404(ApprovalInstance, id=instance_id)
    
    # 权限检查：只有申请人、审批人或管理员可以操作
    user = request.user
    has_permission = False
    if user.is_superuser or user.is_staff:
        has_permission = True
    elif instance.applicant == user:
        has_permission = True
    elif instance.records.filter(approver=user).exists():
        has_permission = True
    
    if not has_permission:
        messages.error(request, '您没有权限执行此操作')
        return redirect('workflow_engine:approval_detail', instance_id=instance_id)
    
    # 获取跟踪记录
    tracking = get_object_or_404(
        OutgoingDocumentTracking.objects.select_related('document', 'delivery_method'),
        id=tracking_id
    )
    
    # 检查是否为快递方式
    if not tracking.delivery_method or tracking.delivery_method.code != 'express':
        messages.error(request, '此跟踪记录不是快递方式，无法更新快递信息')
        return redirect('workflow_engine:approval_detail', instance_id=instance_id)
    
    if request.method == 'POST':
        # 优先使用手动输入的快递公司名称，如果没有则使用下拉选择的值
        express_company = request.POST.get('express_company', '').strip()
        if express_company == '__other__':
            express_company = request.POST.get('express_company_other', '').strip()
        express_number = request.POST.get('express_number', '').strip()
        
        if not express_number:
            messages.error(request, '请输入快递单号')
            return redirect('workflow_engine:approval_detail', instance_id=instance_id)
        
        try:
            # 更新快递信息
            success, message = ExpressTrackingService.update_express_info(
                tracking, express_company, express_number
            )
            
            if success:
                messages.success(request, f'快递信息已更新：{message}')
                # 同时更新到文档（如果文档中没有）
                document = tracking.document
                if document:
                    update_fields = []
                    if not document.express_company and express_company:
                        document.express_company = express_company
                        update_fields.append('express_company')
                    if not document.express_number and express_number:
                        document.express_number = express_number
                        update_fields.append('express_number')
                    if update_fields:
                        document.save(update_fields=update_fields)
                        logger.info(f"同步快递信息到文档: document_id={document.id}, 字段={update_fields}")
            else:
                messages.warning(request, f'快递信息已保存，但查询状态失败：{message}')
            
            logger.info(f"更新跟踪记录快递信息: tracking_id={tracking_id}, 快递公司={express_company}, 快递单号={express_number}")
            
        except Exception as e:
            logger.error(f"更新跟踪记录快递信息失败: {str(e)}", exc_info=True)
            messages.error(request, f'更新失败：{str(e)}')
    
    return redirect('workflow_engine:approval_detail', instance_id=instance_id)


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
                # 保存审批前的状态，用于判断流程是否完成
                old_status = instance.status
                old_current_node_id = instance.current_node_id if instance.current_node else None
                
                success = ApprovalEngine.approve(
                    instance=instance,
                    approver=request.user,
                    result='approved',
                    comment=comment
                )
                if success:
                    # 重新获取实例以获取最新状态
                    instance.refresh_from_db()
                    
                    # 判断流程是否完成
                    if instance.status == 'approved':
                        messages.success(request, f'审批通过！流程已完成。审批编号：{instance.instance_number}')
                    elif instance.status == 'pending' and instance.current_node_id != old_current_node_id:
                        messages.success(request, f'审批通过！已进入下一节点：{instance.current_node.name if instance.current_node else "未知"}。')
                    else:
                        messages.success(request, f'审批通过！审批编号：{instance.instance_number}')
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
                    instance.refresh_from_db()
                    messages.success(request, f'审批已驳回。审批编号：{instance.instance_number}。')
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
                    instance.refresh_from_db()
                    messages.success(request, f'审批已转交给 {transferred_to.username}')
                else:
                    messages.error(request, '转交操作失败')
            
            elif action == 'withdraw':
                # 撤回审批
                success = ApprovalEngine.withdraw(instance=instance, user=request.user)
                if success:
                    messages.success(request, f'审批已撤回。审批编号：{instance.instance_number}')
                else:
                    # 检查失败原因
                    if instance.status != 'pending':
                        messages.error(request, '只能撤回审批中的申请')
                    elif instance.applicant != request.user:
                        messages.error(request, '只有申请人才能撤回申请')
                    elif not instance.workflow.allow_withdraw:
                        messages.error(request, '该流程模板不允许撤回')
                    else:
                        messages.error(request, '撤回失败：已有审批记录，无法撤回')
            
            # 检查是否有重定向参数
            redirect_to = request.POST.get('redirect_to')
            if redirect_to:
                # 添加时间戳参数，防止浏览器缓存
                from django.utils import timezone
                from urllib.parse import urlparse, urlencode, parse_qs
                parsed = urlparse(redirect_to)
                params = parse_qs(parsed.query)
                params['_'] = [str(timezone.now().timestamp())]  # 添加时间戳防止缓存
                redirect_to = f"{parsed.path}?{urlencode(params, doseq=True)}"
                return redirect(redirect_to)
            
            # 默认重定向回审批列表页（因为审批完成后，实例可能不再出现在待审批列表中）
            # 如果用户想查看详情，可以从列表页的"历史审批"标签中查看
            return redirect('workflow_engine:approval_list')
            
        except Exception as e:
            import logging
            logger = logging.getLogger(__name__)
            logger.exception('审批操作失败: %s', str(e))
            messages.error(request, f'审批操作失败：{str(e)}')
    
    # 检查是否有重定向参数
    redirect_to = request.GET.get('redirect_to') or request.POST.get('redirect_to')
    if redirect_to:
        return redirect(redirect_to)
    
    # 默认重定向回审批列表页
    return redirect('workflow_engine:approval_list')


@login_required
def approval_statistics(request):
    """审批统计页面"""
    permission_set = get_user_permission_codes(request.user)
    
    if not _permission_granted('workflow_engine.approve', permission_set):
        messages.error(request, '您没有查看审批统计的权限')
        return redirect('workflow_engine:workflow_engine_home')
    
    # 统计数据
    from django.db.models import Count, Q
    from datetime import datetime, timedelta
    
    # 总审批实例数
    total_instances = ApprovalInstance.objects.count()
    
    # 按状态统计
    status_stats = ApprovalInstance.objects.values('status').annotate(count=Count('id'))
    
    # 按流程模板统计
    workflow_stats = ApprovalInstance.objects.values(
        'workflow__name'
    ).annotate(count=Count('id')).order_by('-count')[:10]
    
    # 最近30天的审批数据
    thirty_days_ago = datetime.now() - timedelta(days=30)
    recent_instances = ApprovalInstance.objects.filter(
        created_time__gte=thirty_days_ago
    ).count()
    
    # 待审批数量
    pending_count = ApprovalInstance.objects.filter(status='pending').count()
    
    # 通过率统计
    approved_count = ApprovalInstance.objects.filter(status='approved').count()
    rejected_count = ApprovalInstance.objects.filter(status='rejected').count()
    total_completed = approved_count + rejected_count
    approval_rate = (approved_count / total_completed * 100) if total_completed > 0 else 0
    
    # 构建页面上下文
    context = _context(
        "审批统计",
        "📊",
        "查看审批流程的统计数据",
        request=request,
        active_menu_id='approval_statistics',
    )
    
    context.update({
        'total_instances': total_instances,
        'status_stats': status_stats,
        'workflow_stats': workflow_stats,
        'recent_instances': recent_instances,
        'pending_count': pending_count,
        'approved_count': approved_count,
        'rejected_count': rejected_count,
        'approval_rate': round(approval_rate, 2),
    })
    
    return render(request, 'workflow_engine/approval_statistics.html', context)


@login_required
def approval_statistics(request):
    """审批统计页面"""
    from datetime import datetime, timedelta
    from django.utils import timezone
    from django.db.models import Count, Q
    
    # 时间范围筛选
    date_range = request.GET.get('date_range', 'month')  # week, month, quarter, year
    start_date = None
    end_date = timezone.now()
    
    if date_range == 'week':
        start_date = end_date - timedelta(days=7)
    elif date_range == 'month':
        start_date = end_date.replace(day=1, hour=0, minute=0, second=0, microsecond=0)
    elif date_range == 'quarter':
        quarter = (end_date.month - 1) // 3 + 1
        start_date = end_date.replace(month=(quarter-1)*3+1, day=1, hour=0, minute=0, second=0, microsecond=0)
    elif date_range == 'year':
        start_date = end_date.replace(month=1, day=1, hour=0, minute=0, second=0, microsecond=0)
    
    # 统计数据
    stats = {}
    
    # 审批实例统计
    instances_query = ApprovalInstance.objects.filter(created_time__gte=start_date) if start_date else ApprovalInstance.objects.all()
    
    stats['total_instances'] = instances_query.count()
    stats['approved_count'] = instances_query.filter(status='approved').count()
    stats['rejected_count'] = instances_query.filter(status='rejected').count()
    stats['pending_count'] = instances_query.filter(status='pending').count()
    stats['withdrawn_count'] = instances_query.filter(status='withdrawn').count()
    
    # 审批效率统计
    completed_instances = instances_query.filter(status__in=['approved', 'rejected'], completed_time__isnull=False)
    if completed_instances.exists():
        durations = []
        for inst in completed_instances:
            if inst.apply_time and inst.completed_time:
                # 处理时区感知问题：如果时间不是时区感知的，假设为 UTC
                apply_time = inst.apply_time
                completed_time = inst.completed_time
                
                if not timezone.is_aware(apply_time):
                    apply_time = timezone.make_aware(apply_time, timezone.utc)
                if not timezone.is_aware(completed_time):
                    completed_time = timezone.make_aware(completed_time, timezone.utc)
                
                duration = (completed_time - apply_time).total_seconds() / 3600
                durations.append(duration)
        
        if durations:
            avg_duration = sum(durations) / len(durations)
            stats['avg_duration_hours'] = round(avg_duration, 2)
        else:
            stats['avg_duration_hours'] = 0
    else:
        stats['avg_duration_hours'] = 0
    
    # 流程模板使用统计
    workflow_stats = WorkflowTemplate.objects.annotate(
        instance_count=Count('instances', filter=Q(instances__created_time__gte=start_date) if start_date else Q())
    ).order_by('-instance_count')
    
    # 审批人统计
    approver_stats = ApprovalRecord.objects.filter(
        approval_time__gte=start_date if start_date else datetime.min.replace(tzinfo=timezone.utc)
    ).values('approver__username').annotate(
        count=Count('id'),
        approved_count=Count('id', filter=Q(result='approved'))
    ).order_by('-count')[:10]
    
    # 按日期统计（最近30天）
    daily_stats = []
    for i in range(30):
        date = end_date - timedelta(days=i)
        day_start = date.replace(hour=0, minute=0, second=0, microsecond=0)
        day_end = date.replace(hour=23, minute=59, second=59, microsecond=999999)
        
        day_instances = ApprovalInstance.objects.filter(
            created_time__gte=day_start,
            created_time__lte=day_end
        )
        
        daily_stats.append({
            'date': date.strftime('%m-%d'),
            'total': day_instances.count(),
            'approved': day_instances.filter(status='approved').count(),
            'rejected': day_instances.filter(status='rejected').count(),
        })
    
    daily_stats.reverse()  # 按时间正序
    
    context = _context(
        "审批统计",
        "📊",
        "查看审批数据和报表",
        request=request,
        active_menu_id='approval_statistics',
    )
    context.update({
        'stats': stats,
        'workflow_stats': workflow_stats,
        'approver_stats': approver_stats,
        'daily_stats': daily_stats,
        'date_range': date_range,
    })
    
    return render(request, 'workflow_engine/approval_statistics.html', context)


@login_required
def batch_approve(request):
    """批量审批"""
    if request.method != 'POST':
        messages.error(request, '无效的请求')
        return redirect('workflow_engine:approval_list')
    
    instance_ids = request.POST.getlist('instance_ids')
    action = request.POST.get('action')  # approve, reject
    comment = request.POST.get('comment', '')
    
    if not instance_ids:
        messages.error(request, '请选择要审批的实例')
        return redirect('workflow_engine:approval_list')
    
    from .services import ApprovalEngine
    success_count = 0
    fail_count = 0
    
    for instance_id in instance_ids:
        try:
            instance = ApprovalInstance.objects.get(id=instance_id)
            
            # 检查权限
            pending_record = ApprovalRecord.objects.filter(
                instance=instance,
                approver=request.user,
                result='pending'
            ).first()
            
            if not pending_record:
                fail_count += 1
                continue
            
            if action == 'approve':
                success = ApprovalEngine.approve(
                    instance=instance,
                    approver=request.user,
                    result='approved',
                    comment=comment
                )
            elif action == 'reject':
                success = ApprovalEngine.approve(
                    instance=instance,
                    approver=request.user,
                    result='rejected',
                    comment=comment
                )
            else:
                fail_count += 1
                continue
            
            if success:
                success_count += 1
            else:
                fail_count += 1
        except Exception as e:
            import logging
            logger = logging.getLogger(__name__)
            logger.exception(f'批量审批失败: instance_id={instance_id}, error={str(e)}')
            fail_count += 1
    
    if success_count > 0:
        messages.success(request, f'成功处理 {success_count} 个审批')
    if fail_count > 0:
        messages.warning(request, f'{fail_count} 个审批处理失败')
    
    return redirect('workflow_engine:approval_list')


@login_required
def export_approvals(request):
    """导出审批数据"""
    import csv
    from django.http import HttpResponse
    from django.utils import timezone
    
    # 获取筛选条件
    status = request.GET.get('status', '')
    date_from = request.GET.get('date_from', '')
    date_to = request.GET.get('date_to', '')
    
    # 构建查询
    queryset = ApprovalInstance.objects.all()
    
    if status:
        queryset = queryset.filter(status=status)
    
    if date_from:
        queryset = queryset.filter(created_time__gte=date_from)
    
    if date_to:
        queryset = queryset.filter(created_time__lte=date_to)
    
    # 只导出当前用户有权限查看的
    if not request.user.is_superuser:
        from django.db.models import Q
        queryset = queryset.filter(
            Q(applicant=request.user) | 
            Q(records__approver=request.user)
        ).distinct()
    
    # 创建HTTP响应
    response = HttpResponse(content_type='text/csv; charset=utf-8-sig')
    response['Content-Disposition'] = f'attachment; filename="approvals_{timezone.now().strftime("%Y%m%d_%H%M%S")}.csv"'
    
    # 写入CSV
    writer = csv.writer(response)
    writer.writerow([
        '实例编号', '流程名称', '申请人', '申请时间', '状态', 
        '当前节点', '完成时间', '关联对象类型', '关联对象ID'
    ])
    
    for instance in queryset.select_related('workflow', 'applicant', 'current_node', 'content_type'):
        # 处理申请时间：转换为本地时间（Asia/Shanghai）
        apply_time_str = ''
        if instance.apply_time:
            if timezone.is_aware(instance.apply_time):
                # 时区感知的时间，转换为本地时间
                apply_time_local = timezone.localtime(instance.apply_time)
                apply_time_str = apply_time_local.strftime('%Y-%m-%d %H:%M:%S')
            else:
                # 非时区感知的时间，假设是 UTC，转换为本地时间
                # 注意：旧数据可能是 naive datetime，需要假设为 UTC
                utc_tz = timezone.utc
                naive_dt = instance.apply_time
                aware_dt = timezone.make_aware(naive_dt, utc_tz)
                apply_time_local = timezone.localtime(aware_dt)
                apply_time_str = apply_time_local.strftime('%Y-%m-%d %H:%M:%S')
        
        # 处理完成时间：转换为本地时间（Asia/Shanghai）
        completed_time_str = ''
        if instance.completed_time:
            if timezone.is_aware(instance.completed_time):
                completed_time_local = timezone.localtime(instance.completed_time)
                completed_time_str = completed_time_local.strftime('%Y-%m-%d %H:%M:%S')
            else:
                # 非时区感知的时间，假设是 UTC，转换为本地时间
                utc_tz = timezone.utc
                naive_dt = instance.completed_time
                aware_dt = timezone.make_aware(naive_dt, utc_tz)
                completed_time_local = timezone.localtime(aware_dt)
                completed_time_str = completed_time_local.strftime('%Y-%m-%d %H:%M:%S')
        
        writer.writerow([
            instance.instance_number,
            instance.workflow.name,
            instance.applicant.username,
            apply_time_str,
            instance.get_status_display(),
            instance.current_node.name if instance.current_node else '',
            completed_time_str,
            instance.content_type.model if instance.content_type else '',
            instance.object_id,
        ])
    
    return response


@login_required
def all_workflows(request):
    """全部流程列表（系统管理员查看所有流程）"""
    from django.core.paginator import Paginator
    
    # 权限检查：使用业务权限系统，检查是否有 workflow_engine.view 权限或拥有全部权限
    permission_codes = get_user_permission_codes(request.user)
    if not _permission_granted('workflow_engine.view', permission_codes):
        messages.error(request, '您没有权限查看全部流程')
        return redirect('workflow_engine:approval_list')
    
    # 获取状态筛选参数
    status_filter = request.GET.get('status', 'pending')
    
    # 查询所有流程（系统管理员可以看到全公司所有流程，不做任何用户或部门过滤）
    queryset = ApprovalInstance.objects.select_related(
        'applicant', 'workflow', 'current_node', 'content_type'
    ).order_by('-created_time')
    
    # 状态映射
    if status_filter == 'pending':
        # 进行中：审批中的流程
        queryset = queryset.filter(status='pending')
    elif status_filter == 'completed':
        # 已完成：已通过或已驳回的流程
        queryset = queryset.filter(status__in=['approved', 'rejected'])
    elif status_filter == 'archived':
        # 已归档：暂时使用已通过且完成时间较早的流程（可以后续添加归档标记）
        # 或者可以添加一个 is_archived 字段
        from django.utils import timezone
        from datetime import timedelta
        # 归档条件：已完成且完成时间超过30天
        cutoff_date = timezone.now() - timedelta(days=30)
        queryset = queryset.filter(
            status__in=['approved', 'rejected'],
            completed_time__lt=cutoff_date
        )
    else:
        # 默认显示进行中
        queryset = queryset.filter(status='pending')
    
    # 分页
    paginator = Paginator(queryset, 20)  # 每页20条
    page_number = request.GET.get('page', 1)
    try:
        page_obj = paginator.page(page_number)
    except:
        page_obj = paginator.page(1)
    
    # 为每个审批实例加载关联的业务对象（分页后，提高性能）
    for instance in page_obj:
        if instance.content_type and instance.object_id:
            try:
                content_object = instance.content_type.get_object_for_this_type(id=instance.object_id)
                instance.content_object = content_object
            except Exception:
                instance.content_object = None
    
    # 状态标签映射
    status_labels = {
        'pending': '进行中',
        'completed': '已完成',
        'archived': '已归档',
    }
    
    # 确定激活的菜单ID
    active_menu_id = f'all_workflows_{status_filter}'
    
    context = _context(
        f"全部流程 - {status_labels.get(status_filter, '进行中')}",
        "📑",
        f"查看所有{status_labels.get(status_filter, '进行中')}的审批流程",
        request=request,
        active_menu_id=active_menu_id,
    )
    context.update({
        'page_obj': page_obj,
        'status_filter': status_filter,
        'status_labels': status_labels,
    })
    
    return render(request, 'workflow_engine/all_workflows.html', context)


@login_required
def create_test_instance_select(request):
    """选择流程创建测试审批实例"""
    # 获取所有有节点的启用流程
    workflows = WorkflowTemplate.objects.filter(
        status='active',
        nodes__isnull=False
    ).distinct().order_by('-created_time')
    
    # 如果通过workflow_id参数直接创建
    workflow_id = request.GET.get('workflow_id')
    if workflow_id:
        try:
            workflow = WorkflowTemplate.objects.get(id=workflow_id)
            if workflow.nodes.exists():
                return redirect('workflow_engine:create_test_approval_instance', workflow_id=workflow_id)
            else:
                messages.warning(request, '该流程还没有配置节点，无法创建审批实例')
        except WorkflowTemplate.DoesNotExist:
            messages.error(request, '流程不存在')
    
    context = _context(
        "创建测试审批实例",
        "🧪",
        "选择一个流程模板创建测试审批实例，用于验证流程配置",
        request=request,
        active_menu_id='create_test_instance',
    )
    context.update({
        'workflows': workflows,
    })
    
    return render(request, 'workflow_engine/create_test_instance_select.html', context)

