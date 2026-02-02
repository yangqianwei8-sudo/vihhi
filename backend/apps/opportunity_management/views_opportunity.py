# 商机管理 - 商机主体视图

from django import forms
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.shortcuts import get_object_or_404, redirect, render
from django.urls import reverse, NoReverseMatch


class _OpportunityFormPlaceholder(forms.Form):
    """占位表单，供 create_form_base 模板使用；提供所属部门、负责人、商机编号等基本信息固定字段。"""
    responsible_department = forms.ModelChoiceField(
        label='所属部门',
        queryset=None,
        required=False,
        widget=forms.Select(attrs={'class': 'form-select'}),
    )
    responsible_person = forms.ModelChoiceField(
        label='负责人',
        queryset=None,
        required=False,
        widget=forms.Select(attrs={'class': 'form-select'}),
    )
    form_number = forms.CharField(
        label='商机编号',
        required=False,
        widget=forms.TextInput(attrs={'class': 'form-control bg-light text-muted', 'readonly': 'readonly'}),
    )

    def __init__(self, *args, user=None, opportunity=None, preview_number=None, **kwargs):
        from backend.apps.system_management.models import User, Department
        super().__init__(*args, **kwargs)
        self.fields['responsible_department'].queryset = Department.objects.filter(is_active=True)
        self.fields['responsible_person'].queryset = User.objects.filter(is_active=True)
        number = ''
        if opportunity and getattr(opportunity, 'opportunity_number', None):
            number = opportunity.opportunity_number
        elif preview_number:
            number = preview_number
        self.fields['form_number'].initial = number or '（保存后自动生成）'
        self.fields['form_number'].widget.attrs['readonly'] = True
        if user:
            self.fields['responsible_person'].initial = user
            self.fields['responsible_person'].widget.attrs['disabled'] = True
            self.fields['responsible_person'].label = '负责人（默认，不可修改）'
            user_department = getattr(user, 'department', None)
            if user_department:
                self.fields['responsible_department'].initial = user_department
            self.fields['responsible_department'].widget.attrs['disabled'] = True
            self.fields['responsible_department'].label = '所属部门（默认，不可修改）'

from .views_common import (
    _context,
    _build_opportunity_management_sidebar_nav,
    _build_full_top_nav,
    _get_opportunities_safely,
    get_user_permission_codes,
    BusinessOpportunity,
    BusinessNegotiation,
    Client,
)
from backend.apps.base_data.models import DesignStage
from .perm_check import (
    opportunity_can_view,
    opportunity_can_view_all,
    opportunity_can_create,
    opportunity_can_edit,
    opportunity_can_delete,
    opportunity_can_manage,
    opportunity_can_access_detail,
    opportunity_can_access_edit,
)

def opportunity_management_home(request):
    """商机管理首页 - 数据展示中心"""
    permission_set = get_user_permission_codes(request.user)
    
    # 权限检查
    if not opportunity_can_view(permission_set):
        messages.error(request, '您没有权限访问商机管理')
        return redirect('home')
    
    from django.utils import timezone
    from datetime import timedelta
    from django.db.models import Sum, Count, Q
    from decimal import Decimal
    
    now = timezone.now()
    today = now.date()
    this_month_start = today.replace(day=1)
    seven_days_ago = today - timedelta(days=7)
    
    try:
        # 基础查询集（考虑权限，排除软删）
        base_queryset = BusinessOpportunity.objects.filter(is_active=True)
        if not opportunity_can_view_all(permission_set):
            base_queryset = base_queryset.filter(business_manager=request.user)
        
        # 统计信息
        total_opportunities = base_queryset.count()
        active_opportunities = base_queryset.exclude(status__in=['won', 'lost', 'cancelled']).count()
        total_estimated = base_queryset.exclude(status__in=['won', 'lost', 'cancelled']).aggregate(
            total=Sum('estimated_amount')
        )['total'] or Decimal('0')
        total_weighted_amount = base_queryset.exclude(status__in=['won', 'lost', 'cancelled']).aggregate(
            total=Sum('weighted_amount')
        )['total'] or Decimal('0')
        monthly_new = base_queryset.filter(
            created_time__year=now.year,
            created_time__month=now.month
        ).count()
        
        # 状态统计
        status_stats = base_queryset.values('status').annotate(count=Count('id'))
        status_dict = {stat['status']: stat['count'] for stat in status_stats}
        
        # 最近商机
        recent_opportunities = base_queryset.select_related('client', 'business_manager').order_by('-created_time')[:10]
        
    except Exception as e:
        import logging
        logger = logging.getLogger(__name__)
        logger.exception('获取商机统计信息失败: %s', str(e))
        total_opportunities = 0
        active_opportunities = 0
        total_estimated = Decimal('0')
        total_weighted_amount = Decimal('0')
        monthly_new = 0
        status_dict = {}
        recent_opportunities = []
    
    # 构建统计卡片
    summary_cards = []
    try:
        summary_cards.append({
            'label': '商机总数',
            'value': total_opportunities,
            'url': reverse('opportunity_pages:opportunity_management'),
            'variant': 'info'
        })
        summary_cards.append({
            'label': '进行中',
            'value': active_opportunities,
            'url': reverse('opportunity_pages:opportunity_management'),
            'variant': 'primary'
        })
        summary_cards.append({
            'label': '预计总额',
            'value': f'{total_estimated:,.0f}',
            'url': reverse('opportunity_pages:opportunity_management'),
            'variant': 'success'
        })
        summary_cards.append({
            'label': '加权总额',
            'value': f'{total_weighted_amount:,.0f}',
            'url': reverse('opportunity_pages:opportunity_management'),
            'variant': 'warning'
        })
        summary_cards.append({
            'label': '本月新增',
            'value': monthly_new,
            'url': reverse('opportunity_pages:opportunity_management'),
            'variant': 'info'
        })
    except Exception as e:
        logger.exception('构建统计卡片失败: %s', str(e))
    
    # 转换为core_cards格式（与计划管理一致）
    core_cards = []
    for card in summary_cards:
        core_cards.append({
            'label': card.get('label', ''),
            'icon': '💼',
            'value': str(card.get('value', 0)),
            'subvalue': '',
            'url': card.get('url', '#'),
        })
    
    # 顶部操作栏
    top_actions = []
    if opportunity_can_create(permission_set):
        try:
            top_actions.append({
                'label': '创建商机',
                'icon': '➕',
                'url': reverse('opportunity_pages:opportunity_create'),
            })
        except NoReverseMatch:
            pass
    
    # 风险预警
    risk_warnings = []
    overdue_opportunities_count = 0
    stale_opportunities_count = 0
    # TODO: 添加具体的风险预警逻辑
    
    # 待办事项
    todo_items = []
    pending_approval_count = 0
    upcoming_deadline_count = 0
    # TODO: 添加具体的待办事项逻辑
    
    # 我的工作
    my_work = {}
    
    # 最近活动（统一为字典格式，与计划管理一致）
    recent_activities = {}
    # 最近创建的商机
    recent_activities['recent_opportunities'] = [{
        'title': opp.name or f'商机 #{opp.id}',
        'creator': opp.business_manager.get_full_name() or opp.business_manager.username if opp.business_manager else '系统',
        'time': opp.created_time,
        'status': opp.get_status_display(),
        'estimated_amount': opp.estimated_amount or 0,
        'url': reverse('opportunity_pages:opportunity_detail', args=[opp.id]),
    } for opp in recent_opportunities[:5]]
    
    # 构建上下文
    context = {
        'page_title': '商机管理',
        'page_icon': '💼',
        'description': '从潜在客户到签约项目的全流程数字化管理，实现销售漏斗可视化和过程标准化。',
        'core_cards': core_cards,
        'top_actions': top_actions,
        'risk_warnings': risk_warnings,
        'todo_items': todo_items,
        'my_work': my_work,
        'recent_activities': recent_activities,
        'overdue_opportunities_count': overdue_opportunities_count,
        'stale_opportunities_count': stale_opportunities_count,
        'pending_approval_count': pending_approval_count,
        'upcoming_deadline_count': upcoming_deadline_count,
        'todo_summary_url': reverse('opportunity_pages:opportunity_management'),
        'summary_cards': summary_cards,  # 保持向后兼容
        'sections': [],
        'total_opportunities': total_opportunities,
        'active_opportunities': active_opportunities,
        'total_estimated': total_estimated,
        'total_weighted_amount': total_weighted_amount,
        'monthly_new': monthly_new,
        'status_dict': status_dict,
        'recent_opportunities': recent_opportunities,
        'sidebar_module_title': '商机管理',
        'sidebar_module_subtitle': 'Opportunity Management',
    }
    
    if request and request.user.is_authenticated:
        permission_set = get_user_permission_codes(request.user)
        context['full_top_nav'] = _build_full_top_nav(permission_set, request.user)
        context['sidebar_nav'] = _build_opportunity_management_sidebar_nav(permission_set, request.path, active_id='opportunity_home')
        context['sidebar_title'] = '商机管理'
        context['sidebar_subtitle'] = 'Opportunity Management'
    else:
        context['full_top_nav'] = []
        context['sidebar_nav'] = []
    
    context.update({
        'total_opportunities': total_opportunities,
        'active_opportunities': active_opportunities,
        'total_estimated': total_estimated,
        'total_weighted_amount': total_weighted_amount,
        'monthly_new': monthly_new,
        'status_dict': status_dict,
        'recent_opportunities': recent_opportunities,
    })
    
    return render(request, "opportunity_management/opportunity_home.html", context)


@login_required
def opportunity_management(request):
    """商机管理列表页面（根据商机管理专项设计方案）"""
    from django.core.paginator import Paginator
    from datetime import datetime
    from django.utils import timezone
    from django.db.models import Sum, Q
    from decimal import Decimal
    
    # 获取筛选参数
    search = request.GET.get('search', '')
    status = request.GET.get('status', '')
    client_id = request.GET.get('client_id', '')
    business_manager_id = request.GET.get('business_manager_id', '')
    urgency = request.GET.get('urgency', '')
    expected_sign_date_from = request.GET.get('expected_sign_date_from', '')
    expected_sign_date_to = request.GET.get('expected_sign_date_to', '')
    
    # 获取权限
    permission_set = get_user_permission_codes(request.user)
    
    # 获取商机列表
    try:
        opportunities = BusinessOpportunity.objects.filter(is_active=True).select_related(
            'client', 'business_manager', 'created_by'
        ).prefetch_related('followups').order_by('-created_time')
        
        # 权限过滤：普通商务经理只能看自己负责的商机
        if not opportunity_can_view_all(permission_set):
            opportunities = opportunities.filter(business_manager=request.user)
        
        
        # 应用筛选条件
        if search:
            opportunities = opportunities.filter(
                Q(opportunity_number__icontains=search) |
                Q(name__icontains=search) |
                Q(project_name__icontains=search) |
                Q(client__name__icontains=search)
            )
        if status:
            opportunities = opportunities.filter(status=status)
        if client_id:
            opportunities = opportunities.filter(client_id=client_id)
        if business_manager_id:
            opportunities = opportunities.filter(business_manager_id=business_manager_id)
        if urgency:
            opportunities = opportunities.filter(urgency=urgency)
        if expected_sign_date_from:
            opportunities = opportunities.filter(expected_sign_date__gte=expected_sign_date_from)
        if expected_sign_date_to:
            opportunities = opportunities.filter(expected_sign_date__lte=expected_sign_date_to)
        
        # 分页
        page_size = request.GET.get('page_size', '10')
        try:
            per_page = int(page_size)
            if per_page not in [10, 20, 50]:
                per_page = 10
        except (ValueError, TypeError):
            per_page = 10
        paginator = Paginator(opportunities, per_page)
        page_number = request.GET.get('page', 1)
        page_obj = paginator.get_page(page_number)
    except Exception as e:
        import logging
        logger = logging.getLogger(__name__)
        logger.exception('获取商机列表失败: %s', str(e))
        messages.error(request, f'获取商机列表失败：{str(e)}')
        page_obj = None
    
    # 统计信息
    try:
        # 基础查询集（考虑权限，排除软删）
        base_queryset = BusinessOpportunity.objects.filter(is_active=True)
        if not opportunity_can_view_all(permission_set):
            base_queryset = base_queryset.filter(business_manager=request.user)
        
        total_opportunities = base_queryset.count()
        
        # 活跃商机（排除已结束状态）
        active_queryset = base_queryset.exclude(status__in=['won', 'lost', 'cancelled'])
        active_opportunities = active_queryset.count()
        
        # 预计金额总和
        total_estimated = active_queryset.aggregate(total=Sum('estimated_amount'))['total'] or Decimal('0')
        
        # 加权金额总和
        total_weighted_amount = active_queryset.aggregate(total=Sum('weighted_amount'))['total'] or Decimal('0')
        
        # 本月新增（当前月份创建的商机）
        now = timezone.now()
        monthly_new = base_queryset.filter(
            created_time__year=now.year,
            created_time__month=now.month
        ).count()
        
        summary_cards = []
    except Exception as e:
        import logging
        logger = logging.getLogger(__name__)
        logger.exception('获取统计信息失败: %s', str(e))
        summary_cards = []
        total_opportunities = 0
        active_opportunities = 0
        total_estimated = Decimal('0')
        total_weighted_amount = Decimal('0')
        monthly_new = 0
    
    # 获取筛选选项
    clients = Client.objects.filter(is_active=True).order_by('name')
    try:
        business_managers = request.user.__class__.objects.filter(
            roles__code='business_manager'
        ).distinct().order_by('username')
    except:
        business_managers = request.user.__class__.objects.all().order_by('username')[:50]
    
    context = _context(
        "商机列表",
        "💼",
        "查看和管理所有商机",
        request=request,
    )
    # 使用完整的顶部菜单
    if request and request.user.is_authenticated:
        context['full_top_nav'] = _build_full_top_nav(permission_set, request.user)
        # 生成左侧菜单（商机列表页面，激活商机列表项）
        context['sidebar_nav'] = _build_opportunity_management_sidebar_nav(permission_set, active_id='opportunity_list')
    else:
        context['full_top_nav'] = []
        context['sidebar_nav'] = []
    context.update({
        'page_obj': page_obj,
        'search': search,
        'status': status,
        'client_id': client_id,
        'business_manager_id': business_manager_id,
        'urgency': urgency,
        'expected_sign_date_from': expected_sign_date_from,
        'expected_sign_date_to': expected_sign_date_to,
        'clients': clients,
        'business_managers': business_managers,
        'status_choices': BusinessOpportunity.STATUS_CHOICES,
        'urgency_choices': BusinessOpportunity.URGENCY_CHOICES,
        'can_create': opportunity_can_create(permission_set),
        'user': request.user,
        # 统计信息
        'total_opportunities': total_opportunities,
        'active_opportunities': active_opportunities,
        'total_estimated': total_estimated,
        'total_weighted_amount': total_weighted_amount,
        'monthly_new': monthly_new,
        # 共享模板需要的数据格式
        'stats': [
            {'title': '商机总数', 'value': total_opportunities, 'cols': 2},
            {'title': '活跃商机', 'value': active_opportunities, 'cols': 2},
            {'title': '预计金额（万元）', 'value': f'{total_estimated:.2f}', 'cols': 2},
            {'title': '加权金额（万元）', 'value': f'{total_weighted_amount:.2f}', 'cols': 2},
            {'title': '本月新增', 'value': monthly_new, 'cols': 2},
        ],
        'show_filter_fields_settings_btn': True,
        'batch_delete_url': '',  # 商机列表暂无批量删除，供 list_page_base 模板使用
        'column_settings_btn': False,
        'filter_form_action': request.path,  # list_page_base 筛选表单 action
        'show_list_checkboxes': False,  # list_page_base 表头/行复选框
        'columns': None,  # 未使用 list_table 列配置时置空，避免模板 KeyError
        'data': None,
    })
    return render(request, "opportunity_management/opportunity_list.html", context)


@login_required
def opportunity_detail(request, opportunity_id):
    """商机详情页面（根据商机管理专项设计方案）"""
    opportunity = get_object_or_404(
        BusinessOpportunity.objects.select_related('client', 'business_manager', 'created_by', 'approver', 'project'),
        id=opportunity_id
    )
    
    permission_set = get_user_permission_codes(request.user)
    # 已软删：仅管理员可访问
    if not opportunity.is_active:
        if not request.user.is_superuser:
            messages.warning(request, '该商机已删除')
            return redirect('opportunity_pages:opportunity_management')
    else:
        # 权限检查：view_all 可看全部；普通用户只能看自己负责的
        if not opportunity_can_access_detail(request.user, opportunity, permission_set):
            messages.error(request, '您没有权限查看此商机')
            return redirect('opportunity_pages:opportunity_management')
    
    # 获取关联数据（开发库可能无 followup/quotations 表时容错）
    try:
        followups = list(
            opportunity.followups.select_related('created_by').order_by('-follow_date', '-created_time')[:100]
        )
    except Exception:
        followups = []
    try:
        quotations = list(opportunity.quotations.select_related('created_by').order_by('-version_number')[:10])
    except Exception:
        quotations = []
    
    # 获取审批信息
    approval_instance = None
    approval_records = []
    can_submit_approval = False
    try:
        from django.contrib.contenttypes.models import ContentType
        from backend.apps.workflow_engine.models import ApprovalInstance, ApprovalRecord
        
        content_type = ContentType.objects.get_for_model(BusinessOpportunity)
        # 用于展示：取最新的审批实例
        approval_instance = ApprovalInstance.objects.filter(
            content_type=content_type,
            object_id=opportunity.id
        ).select_related('workflow', 'applicant', 'current_node').order_by('-created_time').first()
        
        if approval_instance:
            approval_records = ApprovalRecord.objects.filter(
                instance=approval_instance
            ).select_related('node', 'approver', 'transferred_to').order_by('-approval_time')
        
        # 检查是否可以提交审批：有权限且没有正在进行的审批（pending）
        has_pending = ApprovalInstance.objects.filter(
            content_type=content_type,
            object_id=opportunity.id,
            status='pending'
        ).exists()
        can_submit_approval = opportunity_can_edit(permission_set) and not has_pending
    except Exception:
        pass
    
    # 计算健康度评分（如果未计算或需要更新）
    if not opportunity.health_score or opportunity.health_score == 0:
        try:
            # 调用模型的save方法更新健康度
            opportunity.save()
            # 重新获取以获取更新后的健康度
            opportunity.refresh_from_db()
        except Exception as e:
            import logging
            logger = logging.getLogger(__name__)
            logger.warning(f'更新商机健康度失败: {str(e)}')
    
    context = _context(
        f"商机详情 - {opportunity.name}",
        "💼",
        f"商机编号：{opportunity.opportunity_number or '未编号'}",
        request=request,
    )
    if request and request.user.is_authenticated:
        context['full_top_nav'] = _build_full_top_nav(permission_set, request.user)
        # 生成左侧菜单（商机详情页面，激活商机列表）
        context['sidebar_nav'] = _build_opportunity_management_sidebar_nav(permission_set, active_id='opportunity_list')
    else:
        context['full_top_nav'] = []
        context['sidebar_nav'] = []
    can_edit = opportunity_can_access_edit(request.user, opportunity, permission_set) and opportunity.is_active
    can_delete = can_edit  # 与编辑权限一致，供模板使用
    context.update({
        'opportunity': opportunity,
        'opportunity_is_deleted': not opportunity.is_active,
        'followups': followups,
        'quotations': quotations,
        'approval_instance': approval_instance,
        'approval_records': approval_records,
        'can_submit_approval': can_submit_approval and opportunity.is_active,
        'status_choices': BusinessOpportunity.STATUS_CHOICES,
        'urgency_choices': BusinessOpportunity.URGENCY_CHOICES,
        'can_edit': can_edit,
        'can_delete': can_delete,
        'user': request.user,
    })
    return render(request, "opportunity_management/opportunity_detail.html", context)


@login_required
def opportunity_submit_for_approval(request, opportunity_id):
    """提交商机审批：创建 ApprovalInstance，更新 BusinessOpportunity.approval_status"""
    opportunity = get_object_or_404(BusinessOpportunity, id=opportunity_id)
    if not opportunity.is_active and not request.user.is_superuser:
        messages.warning(request, '该商机已删除')
        return redirect('opportunity_pages:opportunity_management')
    permission_set = get_user_permission_codes(request.user)
    can_submit = opportunity_can_access_edit(request.user, opportunity, permission_set)
    if not can_submit:
        messages.error(request, '您没有权限提交商机审批')
        return redirect('opportunity_pages:opportunity_detail', opportunity_id=opportunity_id)

    if request.method == 'POST':
        try:
            from django.contrib.contenttypes.models import ContentType
            from backend.apps.workflow_engine.models import WorkflowTemplate, ApprovalInstance
            from backend.apps.workflow_engine.services import ApprovalEngine

            content_type = ContentType.objects.get_for_model(BusinessOpportunity)
            existing = ApprovalInstance.objects.filter(
                content_type=content_type,
                object_id=opportunity.id,
                status='pending'
            ).first()
            if existing:
                messages.warning(request, f'该商机已有正在进行的审批（审批编号：{existing.instance_number}）')
                return redirect('opportunity_pages:opportunity_detail', opportunity_id=opportunity_id)

            try:
                workflow = WorkflowTemplate.objects.get(code='opportunity_approval', status='active')
            except WorkflowTemplate.DoesNotExist:
                workflow = WorkflowTemplate.objects.filter(
                    status='active',
                    applicable_models__contains=['businessopportunity']
                ).first()
                if not workflow:
                    messages.error(request, '商机审批流程未配置，请联系管理员运行: python manage.py setup_opportunity_approval_workflow')
                    return redirect('opportunity_pages:opportunity_detail', opportunity_id=opportunity_id)

            comment = request.POST.get('comment', f'申请审批商机：{opportunity.name}')
            instance = ApprovalEngine.start_approval(
                workflow=workflow,
                content_object=opportunity,
                applicant=request.user,
                comment=comment
            )
            opportunity.approval_status = 'pending'
            opportunity.save(update_fields=['approval_status'])
            messages.success(request, f'商机审批已提交（审批编号：{instance.instance_number}）')
            return redirect('opportunity_pages:opportunity_detail', opportunity_id=opportunity_id)
        except Exception as e:
            import logging
            logger = logging.getLogger(__name__)
            logger.exception('提交商机审批失败: %s', str(e))
            messages.error(request, f'提交审批失败：{str(e)}')
            return redirect('opportunity_pages:opportunity_detail', opportunity_id=opportunity_id)

    return redirect('opportunity_pages:opportunity_detail', opportunity_id=opportunity_id)


@login_required
def opportunity_create(request):
    """创建商机（根据商机管理专项设计方案）"""
    try:
        permission_set = get_user_permission_codes(request.user)
        if not opportunity_can_create(permission_set):
            messages.error(request, '您没有权限创建商机')
            return redirect('opportunity_pages:opportunity_management')
    except Exception as e:
        import logging
        logger = logging.getLogger(__name__)
        logger.exception('权限检查失败: %s', str(e))
        messages.error(request, f'权限检查失败：{str(e)}')
        return redirect('opportunity_pages:opportunity_management')
    
    if request.method == 'POST':
        try:
            # 获取并验证必填字段
            client_id = request.POST.get('client_id')
            
            if not client_id:
                messages.error(request, '请选择关联客户')
                return redirect('opportunity_pages:opportunity_create')
            
            # 获取客户信息
            client = Client.objects.get(id=client_id)
            
            # 获取项目名称，用于生成默认商机名称
            project_name = request.POST.get('project_name', '').strip()
            name = request.POST.get('name', '').strip()
            # 商机名称：表单有填则用表单，否则自动生成
            if not name:
                if project_name:
                    name = f"{client.name} - {project_name}"
                else:
                    name = client.name
            
            # 获取数值字段
            estimated_amount = Decimal(request.POST.get('estimated_amount', '0') or '0')
            success_probability = int(request.POST.get('success_probability', 10))
            building_area = request.POST.get('building_area')
            
            # 获取服务类型ID
            service_type_id = request.POST.get('service_type_id') or None
            
            # 获取图纸阶段ID
            drawing_stage_id = request.POST.get('drawing_stage') or None
            drawing_stage_obj = None
            if drawing_stage_id:
                try:
                    drawing_stage_obj = DesignStage.objects.filter(id=drawing_stage_id, is_active=True).first()
                except (ValueError, TypeError):
                    pass
            
            project_id = request.POST.get('project_id') or None
            if project_id:
                try:
                    project_id = int(project_id)
                except (ValueError, TypeError):
                    project_id = None
            opportunity = BusinessOpportunity.objects.create(
                name=name,
                client_id=client_id,
                business_manager=request.user,  # 表单由谁填写，商务就是谁
                status='potential',  # 新建商机默认状态为潜在客户
                opportunity_type=request.POST.get('opportunity_type') or None,
                service_type_id=service_type_id,
                urgency=request.POST.get('urgency', 'normal'),
                project_id=project_id,
                project_name=request.POST.get('project_name', '').strip(),
                project_address=request.POST.get('project_address', '').strip(),
                project_type=request.POST.get('project_type', '').strip(),
                building_area=Decimal(building_area) if building_area else None,
                drawing_stage=drawing_stage_obj,
                estimated_amount=estimated_amount,
                success_probability=success_probability,
                expected_sign_date=request.POST.get('expected_sign_date') or None,
                description=request.POST.get('description', '').strip(),
                notes=request.POST.get('notes', '').strip(),
                created_by=request.user,
            )
            # 计算加权金额
            opportunity.weighted_amount = estimated_amount * Decimal(success_probability) / Decimal('100')
            opportunity.save()
            messages.success(request, f'商机 "{opportunity.name}" 创建成功')
            return redirect('opportunity_pages:opportunity_detail', opportunity_id=opportunity.id)
        except ValueError as e:
            messages.error(request, f'数据格式错误：{str(e)}')
        except Exception as e:
            import logging
            logger = logging.getLogger(__name__)
            logger.exception('创建商机失败: %s', str(e))
            messages.error(request, f'创建商机失败：{str(e)}')
    
    # GET请求，显示表单
    try:
        from backend.apps.base_data.models import ServiceType
        from backend.apps.production_management.models import Project
        from django.db.models import Max
        from datetime import datetime
        
        clients = Client.objects.filter(is_active=True).order_by('name')
        service_types = ServiceType.objects.all().order_by('order', 'name')
        design_stages = DesignStage.objects.filter(is_active=True).order_by('order', 'id')
        
        # 生成商机编号预览
        current_date = datetime.now().strftime('%Y%m%d')
        date_prefix = f'SJ-{current_date}-'
        max_opp = BusinessOpportunity.objects.filter(
            opportunity_number__startswith=date_prefix
        ).aggregate(max_num=Max('opportunity_number'))['max_num']
        
        if max_opp:
            try:
                seq = int(max_opp.split('-')[-1]) + 1
            except (ValueError, IndexError):
                seq = 1
        else:
            seq = 1
        
        preview_opportunity_number = f'{date_prefix}{seq:04d}'
        
        context = _context(
            "创建商机",
            "➕",
            "填写以下信息创建新商机",
            request=request,
        )
        if request and request.user.is_authenticated:
            context['full_top_nav'] = _build_full_top_nav(permission_set, request.user)
            # 生成左侧菜单（商机创建页面，激活"商机创建"菜单项）
            context['sidebar_nav'] = _build_opportunity_management_sidebar_nav(permission_set, active_id='opportunity_create')
        else:
            context['full_top_nav'] = []
            context['sidebar_nav'] = []
        projects = Project.objects.filter(
            status__in=['configuring', 'waiting_start', 'in_progress', 'completed']
        ).order_by('-created_time')[:200]
        # 创建页无已有商机，传入占位对象供模板统一使用 opportunity.xxx|default
        from types import SimpleNamespace
        opportunity_placeholder = SimpleNamespace(
            id=None, opportunity_number=None, client_id=None, opportunity_type=None,
            service_type_id=None, project_name=None, project_id=None, project_address=None,
            project_type=None, building_area=None, drawing_stage_id=None, estimated_amount=None,
            success_probability=10, weighted_amount=None, expected_sign_date=None, urgency='normal',
            description=None,
        )
        context.update({
            'form': _OpportunityFormPlaceholder(
                user=request.user,
                opportunity=opportunity_placeholder,
                preview_number=preview_opportunity_number,
            ),
            'opportunity': opportunity_placeholder,
            'clients': clients,
            'service_types': service_types,
            'design_stages': design_stages,
            'urgency_choices': BusinessOpportunity.URGENCY_CHOICES,
            'business_types': Project.BUSINESS_TYPES,
            'preview_opportunity_number': preview_opportunity_number,
            'projects': projects,
        })
        return render(request, "opportunity_management/opportunity_form.html", context)
    except Exception as e:
        import logging
        logger = logging.getLogger(__name__)
        logger.exception('创建商机表单加载失败: %s', str(e))
        messages.error(request, f'加载创建商机表单失败：{str(e)}')
        return redirect('opportunity_pages:opportunity_management')


@login_required
def opportunity_edit(request, opportunity_id):
    """编辑商机（根据商机管理专项设计方案）"""
    opportunity = get_object_or_404(BusinessOpportunity, id=opportunity_id)
    if not opportunity.is_active and not request.user.is_superuser:
        messages.warning(request, '该商机已删除')
        return redirect('opportunity_pages:opportunity_management')
    
    # 权限检查：edit 权限可操作全部；否则仅可操作自己负责的
    permission_set = get_user_permission_codes(request.user)
    if not opportunity_can_access_edit(request.user, opportunity, permission_set):
        messages.error(request, '您没有权限编辑此商机')
        return redirect('opportunity_pages:opportunity_detail', opportunity_id=opportunity.id)
    
    if request.method == 'POST':
        try:
            # 获取并验证必填字段
            name = request.POST.get('name', '').strip()
            client_id = request.POST.get('client_id')
            
            if not client_id:
                messages.error(request, '请选择关联客户')
                return redirect('opportunity_pages:opportunity_edit', opportunity_id=opportunity.id)
            
            # 获取客户信息
            client = Client.objects.get(id=client_id)
            
            # 获取项目名称，用于生成默认商机名称
            project_name = request.POST.get('project_name', '').strip()
            
            # 如果表单中没有提供商机名称，则自动生成
            if not name:
                # 自动生成商机名称：客户名称 + 项目名称（如果有）
                if project_name:
                    name = f"{client.name} - {project_name}"
                else:
                    name = client.name
            
            # 获取数值字段
            estimated_amount = Decimal(request.POST.get('estimated_amount', '0') or '0')
            success_probability = int(request.POST.get('success_probability', 10))
            building_area = request.POST.get('building_area')
            
            opportunity.name = name
            opportunity.client_id = client_id
            # 负责商务和商机状态不可在编辑时修改
            # business_manager 保持不变（由创建人决定）
            # status 保持不变（通过状态流转功能修改）
            opportunity.opportunity_type = request.POST.get('opportunity_type') or None
            opportunity.service_type_id = request.POST.get('service_type_id') or None
            opportunity.urgency = request.POST.get('urgency')
            project_id_val = request.POST.get('project_id') or None
            if project_id_val:
                try:
                    opportunity.project_id = int(project_id_val)
                except (ValueError, TypeError):
                    opportunity.project_id = None
            else:
                opportunity.project_id = None
            opportunity.project_name = request.POST.get('project_name', '').strip()
            opportunity.project_address = request.POST.get('project_address', '').strip()
            opportunity.project_type = request.POST.get('project_type', '').strip()
            opportunity.building_area = Decimal(building_area) if building_area else None
            
            # 获取图纸阶段ID
            drawing_stage_id = request.POST.get('drawing_stage') or None
            drawing_stage_obj = None
            if drawing_stage_id:
                try:
                    drawing_stage_obj = DesignStage.objects.filter(id=drawing_stage_id, is_active=True).first()
                except (ValueError, TypeError):
                    pass
            opportunity.drawing_stage = drawing_stage_obj
            opportunity.estimated_amount = estimated_amount
            opportunity.success_probability = success_probability
            opportunity.expected_sign_date = request.POST.get('expected_sign_date') or None
            opportunity.description = request.POST.get('description', '').strip()
            opportunity.notes = request.POST.get('notes', '').strip()
            # 计算加权金额
            opportunity.weighted_amount = estimated_amount * Decimal(success_probability) / Decimal('100')
            opportunity.save()
            messages.success(request, f'商机 "{opportunity.name}" 更新成功')
            return redirect('opportunity_pages:opportunity_detail', opportunity_id=opportunity.id)
        except ValueError as e:
            messages.error(request, f'数据格式错误：{str(e)}')
        except Exception as e:
            import logging
            logger = logging.getLogger(__name__)
            logger.exception('更新商机失败: %s', str(e))
            messages.error(request, f'更新商机失败：{str(e)}')
    
    # GET请求，显示表单
    from backend.apps.base_data.models import ServiceType
    from backend.apps.production_management.models import Project
    
    clients = Client.objects.filter(is_active=True).select_related('responsible_user').order_by('name')
    service_types = ServiceType.objects.all().order_by('order', 'name')
    design_stages = DesignStage.objects.filter(is_active=True).order_by('order', 'id')
    projects = Project.objects.filter(
        status__in=['configuring', 'waiting_start', 'in_progress', 'completed']
    ).order_by('-created_time')[:200]
    
    context = _context(
        f"编辑商机 - {opportunity.name}",
        "✏️",
        f"商机编号：{opportunity.opportunity_number or '未编号'}",
        request=request,
    )
    if request and request.user.is_authenticated:
        context['full_top_nav'] = _build_full_top_nav(permission_set, request.user)
    else:
        context['full_top_nav'] = []
    context.update({
        'form': _OpportunityFormPlaceholder(user=request.user, opportunity=opportunity),
        'opportunity': opportunity,
        'clients': clients,
        'service_types': service_types,
        'design_stages': design_stages,
        'urgency_choices': BusinessOpportunity.URGENCY_CHOICES,
        'business_types': Project.BUSINESS_TYPES,
        'projects': projects,
    })
    return render(request, "opportunity_management/opportunity_form.html", context)


@login_required
def opportunity_delete(request, opportunity_id):
    """删除商机（软删：设置 is_active=False）"""
    opportunity = get_object_or_404(BusinessOpportunity, id=opportunity_id)
    if not opportunity.is_active:
        messages.info(request, '该商机已删除')
        return redirect('opportunity_pages:opportunity_management')
    
    # 权限检查：与编辑/流转一致，edit 或负责人可删除
    permission_set = get_user_permission_codes(request.user)
    if not opportunity_can_access_edit(request.user, opportunity, permission_set):
        messages.error(request, '您没有权限删除此商机')
        return redirect('opportunity_pages:opportunity_detail', opportunity_id=opportunity.id)
    
    if request.method == 'POST':
        try:
            opportunity_name = opportunity.name
            opportunity.is_active = False
            opportunity.save(update_fields=['is_active'])
            messages.success(request, f'商机 "{opportunity_name}" 已删除')
            return redirect('opportunity_pages:opportunity_management')
        except Exception as e:
            import logging
            logger = logging.getLogger(__name__)
            logger.exception('删除商机失败: %s', str(e))
            messages.error(request, f'删除商机失败：{str(e)}')
    
    # GET请求，显示确认页面
    context = _context(
        "删除商机",
        "🗑️",
        f"确认删除商机：{opportunity.name}",
        request=request,
    )
    if request and request.user.is_authenticated:
        context['full_top_nav'] = _build_full_top_nav(permission_set, request.user)
    else:
        context['full_top_nav'] = []
    context.update({
        'opportunity': opportunity,
    })
    return render(request, "opportunity_management/opportunity_delete.html", context)


@login_required
def opportunity_status_transition(request, opportunity_id):
    """商机状态流转页面（根据总体设计方案）"""
    from .models import OpportunityStatusLog
    
    opportunity = get_object_or_404(
        BusinessOpportunity.objects.select_related('client', 'business_manager'),
        id=opportunity_id
    )
    if not opportunity.is_active and not request.user.is_superuser:
        messages.warning(request, '该商机已删除')
        return redirect('opportunity_pages:opportunity_management')
    
    # 权限检查：与编辑/删除一致
    permission_set = get_user_permission_codes(request.user)
    if not opportunity_can_access_edit(request.user, opportunity, permission_set):
        messages.error(request, '您没有权限修改此商机状态')
        return redirect('opportunity_pages:opportunity_detail', opportunity_id=opportunity_id)
    
    # 获取可流转的状态
    valid_transitions = BusinessOpportunity.get_valid_transitions(opportunity.status)
    transition_choices = [(status, dict(BusinessOpportunity.STATUS_CHOICES).get(status, status)) 
                          for status in valid_transitions]
    
    # 获取状态流转历史
    status_logs = opportunity.status_logs.select_related('actor').order_by('-created_time')[:20]
    
    if request.method == 'POST':
        target_status = request.POST.get('target_status')
        comment = request.POST.get('comment', '').strip()
        
        if not target_status:
            messages.error(request, '请选择目标状态')
        elif target_status not in valid_transitions:
            messages.error(request, '无效的状态流转')
        else:
            try:
                opportunity.transition_to(target_status, actor=request.user, comment=comment)
                messages.success(request, f'商机状态已从 {opportunity.get_status_display()} 流转到 {dict(BusinessOpportunity.STATUS_CHOICES).get(target_status, target_status)}')
                return redirect('opportunity_pages:opportunity_detail', opportunity_id=opportunity_id)
            except ValueError as e:
                messages.error(request, str(e))
            except Exception as e:
                import logging
                logger = logging.getLogger(__name__)
                logger.exception('状态流转失败: %s', str(e))
                messages.error(request, f'状态流转失败：{str(e)}')
    
    context = _context(
        f"状态流转 - {opportunity.name}",
        "🔄",
        f"商机编号：{opportunity.opportunity_number or '未编号'}",
        request=request,
    )
    if request and request.user.is_authenticated:
        context['full_top_nav'] = _build_full_top_nav(permission_set, request.user)
    else:
        context['full_top_nav'] = []
    context.update({
        'opportunity': opportunity,
        'transition_choices': transition_choices,
        'status_logs': status_logs,
        'status_choices': BusinessOpportunity.STATUS_CHOICES,
    })
    return render(request, "opportunity_management/opportunity_status_transition.html", context)


@login_required
def opportunity_followup_create(request, opportunity_id):
    """创建商机跟进记录（根据总体设计方案）"""
    from .models import OpportunityFollowUp
    from datetime import date
    
    opportunity = get_object_or_404(BusinessOpportunity, id=opportunity_id)
    
    # 权限检查
    permission_set = get_user_permission_codes(request.user)
    if not opportunity_can_view(permission_set):
        if opportunity.business_manager != request.user:
            messages.error(request, '您没有权限为此商机创建跟进记录')
            return redirect('opportunity_pages:opportunity_detail', opportunity_id=opportunity_id)
    
    if request.method == 'POST':
        try:
            follow_date = request.POST.get('follow_date')
            follow_type = request.POST.get('follow_type', 'phone')
            participants = request.POST.get('participants', '').strip()
            content = request.POST.get('content', '').strip()
            customer_feedback = request.POST.get('customer_feedback', '').strip()
            next_plan = request.POST.get('next_plan', '').strip()
            next_follow_date = request.POST.get('next_follow_date') or None
            
            # 验证必填字段
            if not follow_date:
                messages.error(request, '跟进日期不能为空')
            elif not content:
                messages.error(request, '跟进内容不能为空')
            else:
                followup = OpportunityFollowUp.objects.create(
                    opportunity=opportunity,
                    follow_date=follow_date,
                    follow_type=follow_type,
                    participants=participants,
                    content=content,
                    customer_feedback=customer_feedback,
                    next_plan=next_plan,
                    next_follow_date=next_follow_date,
                    created_by=request.user,
                )
                messages.success(request, '跟进记录创建成功')
                return redirect('opportunity_pages:opportunity_detail', opportunity_id=opportunity_id)
        except Exception as e:
            import logging
            logger = logging.getLogger(__name__)
            logger.exception('创建跟进记录失败: %s', str(e))
            messages.error(request, f'创建跟进记录失败：{str(e)}')
    
    context = _context(
        f"创建跟进记录 - {opportunity.name}",
        "📝",
        f"商机编号：{opportunity.opportunity_number or '未编号'}",
        request=request,
    )
    if request and request.user.is_authenticated:
        context['full_top_nav'] = _build_full_top_nav(permission_set, request.user)
    else:
        context['full_top_nav'] = []
    context.update({
        'form': _OpportunityFormPlaceholder(user=request.user, opportunity=opportunity),
        'opportunity': opportunity,
        'follow_type_choices': OpportunityFollowUp.FOLLOW_TYPE_CHOICES,
        'default_follow_date': date.today().isoformat(),
    })
    return render(request, "opportunity_management/opportunity_followup_form.html", context)


@login_required
def opportunity_followup_edit(request, opportunity_id, followup_id):
    """编辑商机跟进记录（根据总体设计方案）"""
    from .models import OpportunityFollowUp
    from datetime import date
    
    opportunity = get_object_or_404(BusinessOpportunity, id=opportunity_id)
    followup = get_object_or_404(OpportunityFollowUp, id=followup_id, opportunity=opportunity)
    
    # 权限检查：仅创建人或管理员可编辑
    permission_set = get_user_permission_codes(request.user)
    if followup.created_by != request.user and not opportunity_can_edit(permission_set):
        messages.error(request, '您没有权限编辑此跟进记录')
        return redirect('opportunity_pages:opportunity_detail', opportunity_id=opportunity_id)
    
    if request.method == 'POST':
        try:
            follow_date = request.POST.get('follow_date')
            follow_type = request.POST.get('follow_type', 'phone')
            participants = request.POST.get('participants', '').strip()
            content = request.POST.get('content', '').strip()
            customer_feedback = request.POST.get('customer_feedback', '').strip()
            next_plan = request.POST.get('next_plan', '').strip()
            next_follow_date = request.POST.get('next_follow_date') or None
            
            # 验证必填字段
            if not follow_date:
                messages.error(request, '跟进日期不能为空')
            elif not content:
                messages.error(request, '跟进内容不能为空')
            else:
                followup.follow_date = follow_date
                followup.follow_type = follow_type
                followup.participants = participants
                followup.content = content
                followup.customer_feedback = customer_feedback
                followup.next_plan = next_plan
                followup.next_follow_date = next_follow_date
                followup.save()
                messages.success(request, '跟进记录已更新')
                return redirect('opportunity_pages:opportunity_detail', opportunity_id=opportunity_id)
        except Exception as e:
            import logging
            logger = logging.getLogger(__name__)
            logger.exception('更新跟进记录失败: %s', str(e))
            messages.error(request, f'更新跟进记录失败：{str(e)}')
    
    context = _context(
        f"编辑跟进记录 - {opportunity.name}",
        "✏️",
        f"商机编号：{opportunity.opportunity_number or '未编号'}",
        request=request,
    )
    if request and request.user.is_authenticated:
        context['full_top_nav'] = _build_full_top_nav(permission_set, request.user)
    else:
        context['full_top_nav'] = []
    context.update({
        'form': _OpportunityFormPlaceholder(user=request.user, opportunity=opportunity),
        'opportunity': opportunity,
        'followup': followup,
        'follow_type_choices': OpportunityFollowUp.FOLLOW_TYPE_CHOICES,
    })
    return render(request, "opportunity_management/opportunity_followup_form.html", context)


@login_required
def opportunity_followup_delete(request, opportunity_id, followup_id):
    """删除商机跟进记录（根据总体设计方案）"""
    from .models import OpportunityFollowUp
    
    opportunity = get_object_or_404(BusinessOpportunity, id=opportunity_id)
    followup = get_object_or_404(OpportunityFollowUp, id=followup_id, opportunity=opportunity)
    
    # 权限检查：仅创建人或管理员可删除
    permission_set = get_user_permission_codes(request.user)
    if followup.created_by != request.user and not opportunity_can_delete(permission_set):
        messages.error(request, '您没有权限删除此跟进记录')
        return redirect('opportunity_pages:opportunity_detail', opportunity_id=opportunity_id)
    
    if request.method == 'POST':
        try:
            followup.delete()
            messages.success(request, '跟进记录已删除')
            return redirect('opportunity_pages:opportunity_detail', opportunity_id=opportunity_id)
        except Exception as e:
            import logging
            logger = logging.getLogger(__name__)
            logger.exception('删除跟进记录失败: %s', str(e))
            messages.error(request, f'删除跟进记录失败：{str(e)}')
    
    context = _context(
        f"删除跟进记录 - {opportunity.name}",
        "🗑️",
        f"确认删除跟进记录：{followup.follow_date}",
        request=request,
    )
    if request and request.user.is_authenticated:
        context['full_top_nav'] = _build_full_top_nav(permission_set, request.user)
    else:
        context['full_top_nav'] = []
    context.update({
        'opportunity': opportunity,
        'followup': followup,
    })
    return render(request, "opportunity_management/opportunity_followup_delete.html", context)


@login_required
def opportunity_evaluation_application(request):
    """评估申请页面（根据总体设计方案）"""
    permission_set = get_user_permission_codes(request.user)
    
    # 权限检查
    if not opportunity_can_view(permission_set):
        messages.error(request, '您没有权限访问评估申请功能')
        return redirect('opportunity_pages:opportunity_management')
    
    # 获取商机列表（用于表单下拉框）
    opportunities = BusinessOpportunity.objects.filter(is_active=True).select_related('client', 'business_manager').order_by('-created_time')
    if not opportunity_can_view_all(permission_set):
        opportunities = opportunities.filter(business_manager=request.user)
    
    if request.method == 'POST':
        # TODO: 处理表单提交
        messages.success(request, '评估申请已提交')
        return redirect('opportunity_pages:opportunity_evaluation_application')
    
    context = _context(
        "评估申请",
        "📋",
        "提交图纸评估申请",
        request=request,
    )
    if request and request.user.is_authenticated:
        context['full_top_nav'] = _build_full_top_nav(permission_set, request.user)
    else:
        context['full_top_nav'] = []
    context['opportunities'] = opportunities[:100]  # 限制显示数量
    return render(request, "opportunity_management/opportunity_evaluation_application.html", context)


@login_required
def opportunity_warehouse_application(request):
    """入库申请页面"""
    permission_set = get_user_permission_codes(request.user)
    
    # 权限检查
    if not opportunity_can_view(permission_set):
        messages.error(request, '您没有权限访问入库申请功能')
        return redirect('opportunity_pages:opportunity_management')
    
    # 获取商机列表（用于表单下拉框）
    opportunities = BusinessOpportunity.objects.filter(is_active=True).select_related('client', 'business_manager').order_by('-created_time')
    if not opportunity_can_view_all(permission_set):
        opportunities = opportunities.filter(business_manager=request.user)
    opportunities = _get_opportunities_safely(opportunities, permission_set, request.user)
    
    if request.method == 'POST':
        # TODO: 处理表单提交
        messages.success(request, '入库申请已提交')
        return redirect('opportunity_pages:opportunity_warehouse_application')
    
    context = _context(
        "入库申请",
        "📦",
        "提交入库申请",
        request=request,
    )
    if request and request.user.is_authenticated:
        context['full_top_nav'] = _build_full_top_nav(permission_set, request.user)
    else:
        context['full_top_nav'] = []
    context['opportunities'] = opportunities[:100]  # 限制显示数量
    return render(request, "opportunity_management/opportunity_warehouse_application.html", context)


@login_required
def opportunity_warehouse_list(request):
    """入库列表页面"""
    from django.core.paginator import Paginator
    
    permission_set = get_user_permission_codes(request.user)
    
    # 权限检查
    if not opportunity_can_view(permission_set):
        messages.error(request, '您没有权限访问入库列表')
        return redirect('opportunity_pages:opportunity_management')
    
    # 获取筛选参数
    search = request.GET.get('search', '').strip()
    opportunity_id = request.GET.get('opportunity_id', '')
    status = request.GET.get('status', '')
    page_size = request.GET.get('page_size', '20')
    
    # 获取入库申请列表（这里暂时使用商机列表作为占位，实际应该查询入库申请记录）
    try:
        # TODO: 如果有入库申请模型，应该查询入库申请记录
        # warehouse_applications = WarehouseApplication.objects.select_related('opportunity', 'created_by').order_by('-created_time')
        
        # 暂时使用空列表，实际应该从数据库查询
        warehouse_applications = []
        
        # 应用搜索条件
        if search:
            # TODO: 如果有模型，应该应用搜索条件
            pass
        
        # 应用筛选条件
        if opportunity_id:
            # TODO: 如果有模型，应该应用筛选条件
            pass
        if status:
            # TODO: 如果有模型，应该应用筛选条件
            pass
        
        # 分页
        paginator = Paginator(warehouse_applications, int(page_size))
        page_number = request.GET.get('page', 1)
        page_obj = paginator.get_page(page_number)
        
    except Exception as e:
        import logging
        logger = logging.getLogger(__name__)
        logger.exception('获取入库列表失败: %s', str(e))
        messages.error(request, f'获取入库列表失败：{str(e)}')
        page_obj = None
    
    # 获取商机列表（用于筛选）
    opportunities = BusinessOpportunity.objects.filter(is_active=True).select_related('client', 'business_manager').order_by('-created_time')
    if not opportunity_can_view_all(permission_set):
        opportunities = opportunities.filter(business_manager=request.user)
    opportunities = _get_opportunities_safely(opportunities, permission_set, request.user)
    
    # 检查创建权限
    can_create = opportunity_can_manage(permission_set)
    
    context = _context(
        "入库列表",
        "📥",
        "管理所有入库申请记录",
        request=request,
    )
    
    # 生成左侧菜单
    context['sidebar_nav'] = _build_opportunity_management_sidebar_nav(
        permission_set, 
        request_path=request.path,
        active_id='warehouse_list'
    )
    
    context.update({
        'page_obj': page_obj,
        'search': search,
        'opportunity_id': opportunity_id,
        'status': status,
        'opportunities': opportunities[:100],  # 限制显示数量
        'can_create': can_create,
        'show_filter_fields_settings_btn': True,
    })
    return render(request, "opportunity_management/opportunity_warehouse_list.html", context)


@login_required
def opportunity_bid_bond_payment(request):
    """投标保证金支付申请页面"""
    permission_set = get_user_permission_codes(request.user)
    
    # 权限检查
    if not opportunity_can_view(permission_set):
        messages.error(request, '您没有权限访问投标保证金支付申请功能')
        return redirect('opportunity_pages:opportunity_management')
    
    # 获取商机列表（用于表单下拉框）
    opportunities = BusinessOpportunity.objects.filter(is_active=True).select_related('client', 'business_manager').order_by('-created_time')
    if not opportunity_can_view_all(permission_set):
        opportunities = opportunities.filter(business_manager=request.user)
    opportunities = _get_opportunities_safely(opportunities, permission_set, request.user)
    
    if request.method == 'POST':
        # TODO: 处理表单提交
        messages.success(request, '投标保证金支付申请已提交')
        return redirect('opportunity_pages:opportunity_bid_bond_payment')
    
    context = _context(
        "投标保证金支付申请",
        "💳",
        "提交投标保证金支付申请",
        request=request,
    )
    if request and request.user.is_authenticated:
        context['full_top_nav'] = _build_full_top_nav(permission_set, request.user)
    else:
        context['full_top_nav'] = []
    context['opportunities'] = opportunities[:100]  # 限制显示数量
    return render(request, "opportunity_management/opportunity_bid_bond_payment.html", context)


@login_required
def opportunity_tender_fee_payment(request):
    """标书费支付申请页面"""
    permission_set = get_user_permission_codes(request.user)
    
    # 权限检查
    if not opportunity_can_view(permission_set):
        messages.error(request, '您没有权限访问标书费支付申请功能')
        return redirect('opportunity_pages:opportunity_management')
    
    # 获取商机列表（用于表单下拉框）
    opportunities = BusinessOpportunity.objects.filter(is_active=True).select_related('client', 'business_manager').order_by('-created_time')
    if not opportunity_can_view_all(permission_set):
        opportunities = opportunities.filter(business_manager=request.user)
    opportunities = _get_opportunities_safely(opportunities, permission_set, request.user)
    
    if request.method == 'POST':
        # TODO: 处理表单提交
        messages.success(request, '标书费支付申请已提交')
        return redirect('opportunity_pages:opportunity_tender_fee_payment')
    
    context = _context(
        "标书费支付申请",
        "💵",
        "提交标书费支付申请",
        request=request,
    )
    if request and request.user.is_authenticated:
        context['full_top_nav'] = _build_full_top_nav(permission_set, request.user)
    else:
        context['full_top_nav'] = []
    context['opportunities'] = opportunities[:100]  # 限制显示数量
    return render(request, "opportunity_management/opportunity_tender_fee_payment.html", context)


@login_required
def opportunity_agency_fee_payment(request):
    """招标代理费支付申请页面"""
    permission_set = get_user_permission_codes(request.user)
    
    # 权限检查
    if not opportunity_can_view(permission_set):
        messages.error(request, '您没有权限访问招标代理费支付申请功能')
        return redirect('opportunity_pages:opportunity_management')
    
    # 获取商机列表（用于表单下拉框）
    opportunities = BusinessOpportunity.objects.filter(is_active=True).select_related('client', 'business_manager').order_by('-created_time')
    if not opportunity_can_view_all(permission_set):
        opportunities = opportunities.filter(business_manager=request.user)
    opportunities = _get_opportunities_safely(opportunities, permission_set, request.user)
    
    if request.method == 'POST':
        # TODO: 处理表单提交
        messages.success(request, '招标代理费支付申请已提交')
        return redirect('opportunity_pages:opportunity_agency_fee_payment')
    
    context = _context(
        "招标代理费支付申请",
        "💴",
        "提交招标代理费支付申请",
        request=request,
    )
    if request and request.user.is_authenticated:
        context['full_top_nav'] = _build_full_top_nav(permission_set, request.user)
    else:
        context['full_top_nav'] = []
    context['opportunities'] = opportunities[:100]  # 限制显示数量
    return render(request, "opportunity_management/opportunity_agency_fee_payment.html", context)


@login_required
def opportunity_drawing_evaluation(request):
    """图纸评估页面（根据总体设计方案）"""
    from backend.apps.base_data.models import ServiceProfession
    
    permission_set = get_user_permission_codes(request.user)
    
    # 权限检查
    if not opportunity_can_view(permission_set):
        messages.error(request, '您没有权限访问图纸评估功能')
        return redirect('opportunity_pages:opportunity_management')
    
    # 获取商机列表（用于表单下拉框）
    opportunities = BusinessOpportunity.objects.filter(is_active=True).select_related('client', 'business_manager').order_by('-created_time')
    if not opportunity_can_view_all(permission_set):
        opportunities = opportunities.filter(business_manager=request.user)
    
    # 获取所有服务专业（用于成本节省评估）
    service_professions = ServiceProfession.objects.select_related('service_type').order_by('service_type__order', 'order', 'name')
    
    if request.method == 'POST':
        # TODO: 处理表单提交
        messages.success(request, '图纸评估记录已保存')
        return redirect('opportunity_pages:opportunity_drawing_evaluation')
    
    context = _context(
        "图纸评估",
        "📐",
        "商机图纸评估功能",
        request=request,
    )
    if request and request.user.is_authenticated:
        context['full_top_nav'] = _build_full_top_nav(permission_set, request.user)
        # 生成左侧菜单（图纸评估页面，激活"图纸评估"菜单项）
        context['sidebar_nav'] = _build_opportunity_management_sidebar_nav(permission_set, active_id='drawing_evaluation')
    else:
        context['full_top_nav'] = []
        context['sidebar_nav'] = []
    context.update({
        'opportunities': opportunities[:100],  # 限制显示数量
        'service_professions': service_professions,
    })
    return render(request, "opportunity_management/opportunity_drawing_evaluation.html", context)


@login_required
def opportunity_tech_meeting(request):
    """技术沟通会页面（根据总体设计方案）"""
    permission_set = get_user_permission_codes(request.user)
    
    # 权限检查
    if not opportunity_can_view(permission_set):
        messages.error(request, '您没有权限访问技术沟通会功能')
        return redirect('opportunity_pages:opportunity_management')
    
    # 获取商机列表（用于表单下拉框）
    opportunities = BusinessOpportunity.objects.filter(is_active=True).select_related('client', 'business_manager').order_by('-created_time')
    if not opportunity_can_view_all(permission_set):
        opportunities = opportunities.filter(business_manager=request.user)
    
    if request.method == 'POST':
        # TODO: 处理表单提交
        messages.success(request, '技术沟通会记录已保存')
        return redirect('opportunity_pages:opportunity_tech_meeting')
    
    context = _context(
        "技术沟通会",
        "🤝",
        "商机技术沟通会功能",
        request=request,
    )
    if request and request.user.is_authenticated:
        context['full_top_nav'] = _build_full_top_nav(permission_set, request.user)
        # 生成左侧菜单（技术沟通会页面，激活"技术沟通会"菜单项）
        context['sidebar_nav'] = _build_opportunity_management_sidebar_nav(permission_set, active_id='tech_meeting')
    else:
        context['full_top_nav'] = []
        context['sidebar_nav'] = []
    context['opportunities'] = opportunities[:100]  # 限制显示数量
    return render(request, "opportunity_management/opportunity_tech_meeting.html", context)


@login_required
def opportunity_followup_list(request):
    """跟进记录列表页面（根据总体设计方案）"""
    permission_set = get_user_permission_codes(request.user)
    
    # 获取筛选参数
    search = request.GET.get('search', '')
    opportunity_id = request.GET.get('opportunity_id', '')
    follow_type = request.GET.get('follow_type', '')
    
    # 获取跟进记录
    try:
        followups = OpportunityFollowUp.objects.select_related(
            'opportunity', 'created_by', 'opportunity__client'
        ).order_by('-follow_date', '-created_time')
        
        # 权限过滤：普通商务经理只能看自己负责的商机的跟进记录
        if not opportunity_can_view_all(permission_set):
            followups = followups.filter(opportunity__business_manager=request.user)
        
        # 应用筛选条件
        if search:
            followups = followups.filter(
                Q(content__icontains=search) |
                Q(opportunity__name__icontains=search) |
                Q(opportunity__opportunity_number__icontains=search)
            )
        if opportunity_id:
            followups = followups.filter(opportunity_id=opportunity_id)
        if follow_type:
            followups = followups.filter(follow_type=follow_type)
        
        # 分页
        from django.core.paginator import Paginator
        paginator = Paginator(followups, 13)
        page_number = request.GET.get('page', 1)
        page_obj = paginator.get_page(page_number)
    except Exception as e:
        import logging
        logger = logging.getLogger(__name__)
        logger.exception('获取跟进记录列表失败: %s', str(e))
        messages.error(request, f'获取跟进记录列表失败：{str(e)}')
        page_obj = None
    
    context = _context(
        "跟进记录",
        "📝",
        "商机跟进记录管理",
        request=request,
    )
    if request and request.user.is_authenticated:
        context['full_top_nav'] = _build_full_top_nav(permission_set, request.user)
    else:
        context['full_top_nav'] = []
    context.update({
        'page_obj': page_obj,
        'search': search,
        'opportunity_id': opportunity_id,
        'follow_type': follow_type,
        'follow_type_choices': OpportunityFollowUp.FOLLOW_TYPE_CHOICES,
        'opportunities': BusinessOpportunity.objects.filter(is_active=True, business_manager=request.user
        ).order_by('-created_time')[:50] if not opportunity_can_view_all(permission_set) 
        else BusinessOpportunity.objects.filter(is_active=True).order_by('-created_time')[:100],
        'show_filter_fields_settings_btn': True,
    })
    return render(request, "opportunity_management/opportunity_followup_list.html", context)


@login_required
def opportunity_sales_forecast(request):
    """商机预测页面（根据总体设计方案，API已实现）"""
    from datetime import datetime
    from calendar import monthrange
    from django.db.models import Sum
    from django.utils import timezone
    
    permission_set = get_user_permission_codes(request.user)
    
    # 获取预测月份
    forecast_month = request.GET.get('month', '')
    if not forecast_month:
        today = timezone.now().date()
        forecast_month = f"{today.year}-{today.month:02d}"
    
    try:
        year, month = map(int, forecast_month.split('-'))
        start_date = datetime(year, month, 1).date()
        days_in_month = monthrange(year, month)[1]
        end_date = datetime(year, month, days_in_month).date()
    except (ValueError, IndexError):
        today = timezone.now().date()
        start_date = datetime(today.year, today.month, 1).date()
        days_in_month = monthrange(today.year, today.month)[1]
        end_date = datetime(today.year, today.month, days_in_month).date()
        forecast_month = f"{today.year}-{today.month:02d}"
    
    # 获取活跃商机
    active_opportunities = BusinessOpportunity.objects.filter(is_active=True).exclude(
        status__in=['won', 'lost', 'cancelled']
    )
    
    # 权限过滤
    if not opportunity_can_view_all(permission_set):
        active_opportunities = active_opportunities.filter(business_manager=request.user)
    
    # 计算本月预计签约的商机
    month_opportunities = active_opportunities.filter(
        expected_sign_date__gte=start_date,
        expected_sign_date__lte=end_date
    )
    
    # 统计基础数据
    total_active = active_opportunities.count()
    total_weighted_amount = float(active_opportunities.aggregate(
        total=Sum('weighted_amount')
    )['total'] or 0)
    month_weighted_amount = float(month_opportunities.aggregate(
        total=Sum('weighted_amount')
    )['total'] or 0)
    
    # 计算历史转化率
    historical_queryset = BusinessOpportunity.objects.filter(is_active=True, status__in=['initial_contact', 'requirement_confirmed', 'quotation', 'negotiation', 'won'])
    if not opportunity_can_view_all(permission_set):
        historical_queryset = historical_queryset.filter(business_manager=request.user)
    
    historical_initial = historical_queryset.count()
    historical_won = historical_queryset.filter(status='won').count()
    
    historical_conversion_rate = 35.0  # 默认值
    if historical_initial > 0:
        historical_conversion_rate = (historical_won / historical_initial) * 100
    
    # 计算预测值（转换为万元）
    optimistic_forecast = (month_weighted_amount * (historical_conversion_rate / 100) * 1.2) / 10000
    neutral_forecast = (month_weighted_amount * (historical_conversion_rate / 100)) / 10000
    conservative_forecast = (month_weighted_amount * (historical_conversion_rate / 100) * 0.8) / 10000
    
    # 目标差距分析
    monthly_target = (total_weighted_amount * 0.6) / 10000
    target_gap = monthly_target - neutral_forecast
    
    # 生成建议
    suggestions = []
    if target_gap > 0:
        suggestions.append('预测金额低于月度目标，建议加大商机开拓力度')
        suggestions.append('建议提升在途商机的转化率')
        suggestions.append('建议重点关注高价值商机，加快推进速度')
    else:
        suggestions.append('预测金额达到月度目标，继续保持')
        suggestions.append('建议持续跟进在途商机，确保按时签约')
    
    forecast_data = {
        'month': forecast_month,
        'active_opportunities': total_active,
        'weighted_amount': total_weighted_amount / 10000,  # 转换为万元
        'historical_conversion_rate': historical_conversion_rate,
        'optimistic': optimistic_forecast,
        'neutral': neutral_forecast,
        'conservative': conservative_forecast,
        'target_gap': {
            'monthly_target': monthly_target,
            'gap': target_gap,
            'suggestions': '\n'.join(suggestions)
        }
    }
    
    context = _context(
        "商机预测",
        "📈",
        "销售预测分析",
        request=request,
    )
    if request and request.user.is_authenticated:
        context['full_top_nav'] = _build_full_top_nav(permission_set, request.user)
        # 生成左侧菜单（商机预测页面，激活"商机预测"菜单项）
        context['sidebar_nav'] = _build_opportunity_management_sidebar_nav(permission_set, active_id='sales_forecast')
    else:
        context['full_top_nav'] = []
        context['sidebar_nav'] = []
    context['forecast_data'] = forecast_data
    
    return render(request, "opportunity_management/opportunity_sales_forecast.html", context)


@login_required
def opportunity_win_loss(request):
    """赢单与输单管理页面（根据商机管理专项设计方案）"""
    from django.core.paginator import Paginator
    from decimal import Decimal
    
    # 获取筛选参数
    search = request.GET.get('search', '')
    status_filter = request.GET.get('status', '')  # 'won' 或 'lost'
    client_id = request.GET.get('client_id', '')
    business_manager_id = request.GET.get('business_manager_id', '')
    date_from = request.GET.get('date_from', '')
    date_to = request.GET.get('date_to', '')
    
    # 获取权限
    permission_set = get_user_permission_codes(request.user)
    
    if not opportunity_can_view(permission_set):
        messages.error(request, '您没有权限查看赢单与输单信息')
        return redirect('opportunity_pages:opportunity_management')
    
    # 获取赢单和输单商机列表
    try:
        opportunities = BusinessOpportunity.objects.filter(is_active=True).select_related(
            'client', 'business_manager', 'created_by'
        ).filter(status__in=['won', 'lost']).order_by('-updated_time')
        
        # 权限过滤：普通商务经理只能看自己负责的商机
        if not opportunity_can_view_all(permission_set):
            opportunities = opportunities.filter(business_manager=request.user)
        
        # 应用筛选条件
        if search:
            opportunities = opportunities.filter(
                Q(opportunity_number__icontains=search) |
                Q(name__icontains=search) |
                Q(project_name__icontains=search) |
                Q(client__name__icontains=search)
            )
        if status_filter in ['won', 'lost']:
            opportunities = opportunities.filter(status=status_filter)
        if client_id:
            opportunities = opportunities.filter(client_id=client_id)
        if business_manager_id:
            opportunities = opportunities.filter(business_manager_id=business_manager_id)
        if date_from:
            opportunities = opportunities.filter(updated_time__gte=date_from)
        if date_to:
            opportunities = opportunities.filter(updated_time__lte=date_to)
        
        # 分页
        page_size = request.GET.get('page_size', '10')
        try:
            per_page = int(page_size)
            if per_page not in [10, 20, 50]:
                per_page = 10
        except (ValueError, TypeError):
            per_page = 10
        paginator = Paginator(opportunities, per_page)
        page_number = request.GET.get('page', 1)
        page_obj = paginator.get_page(page_number)
    except Exception as e:
        import logging
        logger = logging.getLogger(__name__)
        logger.exception('获取赢单与输单列表失败: %s', str(e))
        messages.error(request, f'获取赢单与输单列表失败：{str(e)}')
        page_obj = None
    
    # 统计信息
    try:
        # 基础查询集（考虑权限）
        base_queryset = BusinessOpportunity.objects.filter(is_active=True, status__in=['won', 'lost'])
        if not opportunity_can_view_all(permission_set):
            base_queryset = base_queryset.filter(business_manager=request.user)
        
        total_count = base_queryset.count()
        won_count = base_queryset.filter(status='won').count()
        lost_count = base_queryset.filter(status='lost').count()
        
        # 赢单金额统计
        won_amount = base_queryset.filter(status='won').aggregate(
            total=Sum('actual_amount')
        )['total'] or Decimal('0')
        
        # 输单金额统计（预计金额）
        lost_amount = base_queryset.filter(status='lost').aggregate(
            total=Sum('estimated_amount')
        )['total'] or Decimal('0')
        
        # 赢单率
        win_rate = 0.0
        if total_count > 0:
            win_rate = (won_count / total_count) * 100
        
        summary_cards = []
    except Exception as e:
        import logging
        logger = logging.getLogger(__name__)
        logger.exception('获取统计信息失败: %s', str(e))
        summary_cards = []
        won_amount = Decimal('0')
        lost_amount = Decimal('0')
    
    # 获取筛选选项
    clients = Client.objects.filter(is_active=True).order_by('name')
    try:
        business_managers = request.user.__class__.objects.filter(
            roles__code='business_manager'
        ).distinct().order_by('username')
    except:
        business_managers = request.user.__class__.objects.all().order_by('username')[:50]
    
    context = _context(
        "赢单与输单",
        "✅",
        "商机赢单与输单管理，记录商机最终结果和原因分析",
        summary_cards=summary_cards,
        request=request,
    )
    # 使用完整的顶部菜单
    if request and request.user.is_authenticated:
        context['full_top_nav'] = _build_full_top_nav(permission_set, request.user)
        # 生成左侧菜单（赢单与输单页面，激活"赢单与输单"菜单项）
        context['sidebar_nav'] = _build_opportunity_management_sidebar_nav(permission_set, active_id='win_loss')
    else:
        context['full_top_nav'] = []
        context['sidebar_nav'] = []
    context.update({
        'page_obj': page_obj,
        'search': search,
        'status': status_filter,
        'client_id': client_id,
        'business_manager_id': business_manager_id,
        'date_from': date_from,
        'date_to': date_to,
        'clients': clients,
        'business_managers': business_managers,
        'status_choices': [('won', '赢单'), ('lost', '输单')],
        'won_amount': won_amount,
        'lost_amount': lost_amount,
    })
    return render(request, "opportunity_management/opportunity_win_loss.html", context)


@login_required
def opportunity_win_loss_select(request):
    """选择商机并标记为赢单/输单页面"""
    from django.core.paginator import Paginator
    
    # 获取目标状态（won 或 lost）
    target_status = request.GET.get('target_status', '')
    if target_status not in ['won', 'lost']:
        messages.error(request, '无效的目标状态')
        return redirect('opportunity_pages:opportunity_win_loss')
    
    # 获取筛选参数
    search = request.GET.get('search', '')
    client_id = request.GET.get('client_id', '')
    business_manager_id = request.GET.get('business_manager_id', '')
    
    # 获取权限
    permission_set = get_user_permission_codes(request.user)
    
    if not opportunity_can_edit(permission_set):
        messages.error(request, '您没有权限标记商机为赢单/输单')
        return redirect('opportunity_pages:opportunity_win_loss')
    
    # 获取可以转换为赢单/输单的商机
    # 包括：1) 状态为"商务谈判"的商机 2) 有商务洽谈记录的商机（无论状态）
    try:
        # 获取有商务洽谈记录的商机ID列表
        negotiation_opportunity_ids = BusinessNegotiation.objects.values_list('opportunity_id', flat=True).distinct()
        
        # 获取可以转换的商机：状态为"商务谈判"或有商务洽谈记录
        opportunities = BusinessOpportunity.objects.select_related(
            'client', 'business_manager', 'created_by'
        ).filter(
            Q(status='negotiation') | Q(id__in=negotiation_opportunity_ids)
        ).exclude(
            status__in=['won', 'lost', 'cancelled']  # 排除已结束的商机
        ).order_by('-updated_time')
        
        # 权限过滤：普通商务经理只能看自己负责的商机
        if not opportunity_can_view_all(permission_set):
            opportunities = opportunities.filter(business_manager=request.user)
        
        # 应用筛选条件
        if search:
            opportunities = opportunities.filter(
                Q(opportunity_number__icontains=search) |
                Q(name__icontains=search) |
                Q(project_name__icontains=search) |
                Q(client__name__icontains=search)
            )
        if client_id:
            opportunities = opportunities.filter(client_id=client_id)
        if business_manager_id:
            opportunities = opportunities.filter(business_manager_id=business_manager_id)
        
        # 分页
        page_size = request.GET.get('page_size', '10')
        try:
            per_page = int(page_size)
            if per_page not in [10, 20, 50]:
                per_page = 10
        except (ValueError, TypeError):
            per_page = 10
        paginator = Paginator(opportunities, per_page)
        page_number = request.GET.get('page', 1)
        page_obj = paginator.get_page(page_number)
    except Exception as e:
        import logging
        logger = logging.getLogger(__name__)
        logger.exception('获取商机列表失败: %s', str(e))
        messages.error(request, f'获取商机列表失败：{str(e)}')
        page_obj = None
    
    # 获取筛选选项
    clients = Client.objects.filter(is_active=True).order_by('name')
    try:
        business_managers = request.user.__class__.objects.filter(
            roles__code='business_manager'
        ).distinct().order_by('username')
    except:
        business_managers = request.user.__class__.objects.all().order_by('username')[:50]
    
    status_label = '赢单' if target_status == 'won' else '输单'
    
    context = _context(
        f"选择商机 - 标记为{status_label}",
        "✅" if target_status == 'won' else "❌",
        f"选择要标记为{status_label}的商机",
        request=request,
    )
    if request and request.user.is_authenticated:
        context['full_top_nav'] = _build_full_top_nav(permission_set, request.user)
        context['sidebar_nav'] = _build_opportunity_management_sidebar_nav(permission_set, active_id='win_loss')
    else:
        context['full_top_nav'] = []
        context['sidebar_nav'] = []
    context.update({
        'page_obj': page_obj,
        'search': search,
        'client_id': client_id,
        'business_manager_id': business_manager_id,
        'clients': clients,
        'business_managers': business_managers,
        'target_status': target_status,
        'status_label': status_label,
    })
    return render(request, "opportunity_management/opportunity_win_loss_select.html", context)


@login_required
def opportunity_mark_win_loss(request, opportunity_id):
    """快速标记商机为赢单或输单"""
    opportunity = get_object_or_404(
        BusinessOpportunity.objects.select_related('client', 'business_manager'),
        id=opportunity_id
    )
    
    # 权限检查：与编辑/删除一致
    permission_set = get_user_permission_codes(request.user)
    if not opportunity_can_access_edit(request.user, opportunity, permission_set):
        messages.error(request, '您没有权限修改此商机状态')
        return redirect('opportunity_pages:opportunity_detail', opportunity_id=opportunity_id)
    
    # 获取目标状态
    target_status = request.GET.get('target_status', '')
    if target_status not in ['won', 'lost']:
        messages.error(request, '无效的目标状态')
        return redirect('opportunity_pages:opportunity_detail', opportunity_id=opportunity_id)
    
    # 检查是否可以转换
    # 允许转换的情况：1) 状态转换规则允许 2) 有商务洽谈记录（说明已进入商务阶段）
    can_transition = opportunity.can_transition_to(target_status)
    has_negotiation = BusinessNegotiation.objects.filter(opportunity=opportunity).exists()
    
    if not can_transition and not has_negotiation:
        messages.error(request, f'当前商机状态为"{opportunity.get_status_display()}"，无法直接标记为{"赢单" if target_status == "won" else "输单"}。请先将商机状态转换为"商务谈判"，或创建商务洽谈记录。')
        return redirect('opportunity_pages:opportunity_detail', opportunity_id=opportunity_id)
    
    # 如果有商务洽谈记录但状态不允许直接转换，先更新状态为"商务谈判"
    if not can_transition and has_negotiation and opportunity.status != 'negotiation':
        # 如果当前状态可以转换为"商务谈判"，先转换状态
        if opportunity.can_transition_to('negotiation'):
            try:
                opportunity.transition_to('negotiation', actor=request.user, comment='自动转换为商务谈判状态（因为有商务洽谈记录）')
            except Exception as e:
                import logging
                logger = logging.getLogger(__name__)
                logger.warning(f'自动转换状态失败: {str(e)}')
                # 继续执行，允许直接标记
    
    if request.method == 'POST':
        comment = request.POST.get('comment', '').strip()
        try:
            # 先更新额外信息字段（在状态转换之前）
            if target_status == 'won':
                actual_amount = request.POST.get('actual_amount', '').strip()
                contract_number = request.POST.get('contract_number', '').strip()
                actual_sign_date = request.POST.get('actual_sign_date', '').strip()
                win_reason = request.POST.get('win_reason', '').strip()
                
                if actual_amount:
                    try:
                        opportunity.actual_amount = Decimal(actual_amount)
                    except (ValueError, InvalidOperation):
                        pass
                if contract_number:
                    opportunity.contract_number = contract_number
                if actual_sign_date:
                    try:
                        from datetime import datetime
                        opportunity.actual_sign_date = datetime.strptime(actual_sign_date, '%Y-%m-%d').date()
                    except ValueError:
                        pass
                if win_reason:
                    opportunity.win_reason = win_reason
            elif target_status == 'lost':
                loss_reason = request.POST.get('loss_reason', '').strip()
                if loss_reason:
                    opportunity.loss_reason = loss_reason
            
            # 执行状态流转（这会保存所有字段，包括状态）
            opportunity.transition_to(target_status, actor=request.user, comment=comment)
            
            # 从数据库重新加载对象以确保状态已更新
            opportunity.refresh_from_db()
            
            # 验证状态是否已更新
            if opportunity.status != target_status:
                import logging
                logger = logging.getLogger(__name__)
                logger.error(f'状态更新失败：期望状态={target_status}，实际状态={opportunity.status}')
                messages.error(request, '状态更新失败，请重试')
                return redirect('opportunity_pages:opportunity_detail', opportunity_id=opportunity_id)
            
            status_label = '赢单' if target_status == 'won' else '输单'
            messages.success(request, f'商机已成功标记为{status_label}')
            return redirect('opportunity_pages:opportunity_win_loss')
        except ValueError as e:
            messages.error(request, str(e))
        except Exception as e:
            import logging
            logger = logging.getLogger(__name__)
            logger.exception('标记商机失败: %s', str(e))
            messages.error(request, f'标记商机失败：{str(e)}')
    
    # GET 请求，显示确认表单
    status_label = '赢单' if target_status == 'won' else '输单'
    context = _context(
        f"标记为{status_label} - {opportunity.name}",
        "✅" if target_status == 'won' else "❌",
        f"商机编号：{opportunity.opportunity_number or '未编号'}",
        request=request,
    )
    if request and request.user.is_authenticated:
        context['full_top_nav'] = _build_full_top_nav(permission_set, request.user)
        context['sidebar_nav'] = _build_opportunity_management_sidebar_nav(permission_set, active_id='win_loss')
    else:
        context['full_top_nav'] = []
        context['sidebar_nav'] = []
    context.update({
        'opportunity': opportunity,
        'target_status': target_status,
        'status_label': status_label,
    })
    return render(request, "opportunity_management/opportunity_mark_win_loss.html", context)


@login_required
def opportunity_business_negotiation(request):
    """商务洽谈页面（根据总体设计方案）"""
    permission_set = get_user_permission_codes(request.user)
    
    # 获取筛选参数
    search = request.GET.get('search', '')
    opportunity_id = request.GET.get('opportunity_id', '')
    
    # 获取商务洽谈记录列表
    try:
        negotiations = BusinessNegotiation.objects.select_related(
            'opportunity', 'opportunity__client', 'opportunity__business_manager', 'created_by'
        ).order_by('-negotiation_date', '-created_time')
        
        # 权限过滤：普通商务经理只能看自己负责的商机的洽谈记录
        if not opportunity_can_view_all(permission_set):
            negotiations = negotiations.filter(opportunity__business_manager=request.user)
        
        # 应用筛选条件
        if search:
            negotiations = negotiations.filter(
                Q(opportunity__name__icontains=search) |
                Q(opportunity__opportunity_number__icontains=search) |
                Q(opportunity__client__name__icontains=search) |
                Q(content__icontains=search)
            )
        if opportunity_id:
            negotiations = negotiations.filter(opportunity_id=opportunity_id)
        
        # 分页
        from django.core.paginator import Paginator
        paginator = Paginator(negotiations, 13)
        page_number = request.GET.get('page', 1)
        page_obj = paginator.get_page(page_number)
    except Exception as e:
        import logging
        logger = logging.getLogger(__name__)
        logger.exception('获取商务洽谈记录失败: %s', str(e))
        messages.error(request, f'获取商务洽谈记录失败：{str(e)}')
        page_obj = None
    
    # 获取商机列表（用于筛选下拉框）
    try:
        opportunities_for_filter = BusinessOpportunity.objects.filter(is_active=True).select_related(
            'client', 'business_manager'
        ).order_by('-created_time')
        
        # 权限过滤
        if not opportunity_can_view_all(permission_set):
            opportunities_for_filter = opportunities_for_filter.filter(business_manager=request.user)
        
        opportunities_for_filter = opportunities_for_filter[:100]  # 限制数量
    except Exception as e:
        opportunities_for_filter = []
    
    context = _context(
        "商务洽谈登记",
        "💬",
        "商机商务洽谈登记管理",
        request=request,
    )
    if request and request.user.is_authenticated:
        context['full_top_nav'] = _build_full_top_nav(permission_set, request.user)
        # 生成左侧菜单（商务洽谈登记页面，激活"商务洽谈登记"菜单项）
        context['sidebar_nav'] = _build_opportunity_management_sidebar_nav(permission_set, active_id='business_negotiation')
    else:
        context['full_top_nav'] = []
        context['sidebar_nav'] = []
    context.update({
        'page_obj': page_obj,
        'search': search,
        'opportunity_id': opportunity_id,
        'opportunities': opportunities_for_filter,
    })
    return render(request, "opportunity_management/opportunity_business_negotiation.html", context)


@login_required
def opportunity_business_negotiation_form(request, opportunity_id=None):
    """商务洽谈表单页面（创建/编辑）"""
    permission_set = get_user_permission_codes(request.user)
    
    if opportunity_id:
        opportunity = get_object_or_404(BusinessOpportunity, id=opportunity_id)
        # 权限检查
        if not opportunity_can_view(permission_set):
            if opportunity.business_manager != request.user:
                messages.error(request, '您没有权限查看此商机')
                return redirect('opportunity_pages:opportunity_business_negotiation')
    else:
        opportunity = None
    
    if request.method == 'POST':
        try:
            # 获取表单数据
            opportunity_id = request.POST.get('opportunity_id')
            if not opportunity_id:
                messages.error(request, '请选择关联商机')
                return redirect('opportunity_pages:opportunity_business_negotiation_form', opportunity_id=opportunity_id) if opportunity_id else redirect('opportunity_pages:opportunity_business_negotiation_form')
            
            opp = get_object_or_404(BusinessOpportunity, id=opportunity_id)
            
            # 权限检查
            if not opportunity_can_view(permission_set):
                if opp.business_manager != request.user:
                    messages.error(request, '您没有权限为此商机创建洽谈登记')
                    return redirect('opportunity_pages:opportunity_business_negotiation')
            
            # 创建商务洽谈记录
            negotiation = BusinessNegotiation.objects.create(
                opportunity=opp,
                negotiation_date=request.POST.get('negotiation_date'),
                negotiation_type=request.POST.get('negotiation_type'),
                participants=request.POST.get('participants', ''),
                content=request.POST.get('content'),
                client_feedback=request.POST.get('client_feedback', ''),
                next_plan=request.POST.get('next_plan', ''),
                discussed_amount=request.POST.get('discussed_amount') or None,
                payment_terms=request.POST.get('payment_terms', ''),
                contract_terms=request.POST.get('contract_terms', ''),
                created_by=request.user
            )
            
            messages.success(request, '商务洽谈登记已保存')
            return redirect('opportunity_pages:opportunity_business_negotiation')
        except Exception as e:
            import logging
            logger = logging.getLogger(__name__)
            logger.exception('保存商务洽谈记录失败: %s', str(e))
            messages.error(request, f'保存失败：{str(e)}')
    
    description = f"商机：{opportunity.name}" if opportunity else "创建新的商务洽谈登记"
    context = _context(
        f"{'编辑' if opportunity_id else '创建'}商务洽谈登记",
        "💬",
        description,
        request=request,
    )
    if request and request.user.is_authenticated:
        context['full_top_nav'] = _build_full_top_nav(permission_set, request.user)
    else:
        context['full_top_nav'] = []
    context.update({
        'form': _OpportunityFormPlaceholder(user=request.user, opportunity=opportunity),
        'opportunity': opportunity,
        'opportunities': BusinessOpportunity.objects.filter(is_active=True, business_manager=request.user
        ).order_by('-created_time')[:50] if not opportunity_can_view_all(permission_set)
        else BusinessOpportunity.objects.filter(is_active=True).order_by('-created_time')[:100],
    })
    return render(request, "opportunity_management/opportunity_business_negotiation_form.html", context)

