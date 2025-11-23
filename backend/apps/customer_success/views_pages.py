from decimal import Decimal

from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.db.models import Count, Sum, Q
from django.shortcuts import render, get_object_or_404, redirect
from django.utils import timezone
from django.urls import reverse, NoReverseMatch

from backend.apps.customer_success.models import (
    BusinessContract,
    BusinessPaymentPlan,
    Client,
    ClientProject,
    BusinessOpportunity,
    OpportunityFollowUp,
    OpportunityQuotation,
    OpportunityApproval,
    OpportunityStatusLog,
    QuotationRule,
)
from backend.apps.system_management.services import get_user_permission_codes
from backend.core.views import HOME_NAV_STRUCTURE, _permission_granted


def _build_full_top_nav(permission_set, user):
    """生成完整的顶部导航菜单，包含所有用户有权限的模块菜单项（按模块分类）"""
    full_nav = []
    
    for section in HOME_NAV_STRUCTURE:
        # 检查模块权限
        if not _permission_granted(section.get("permission"), permission_set):
            continue
        
        # 收集该模块下有权限的子菜单项
        section_items = []
        for child in section.get("children", []):
            # 检查子菜单项权限
            permission = child.get("permission")
            if permission and not _permission_granted(permission, permission_set):
                continue
            
            # 获取URL
            url_name = child.get("url_name")
            url = child.get("url")
            if url_name:
                try:
                    url = reverse(url_name)
                except NoReverseMatch:
                    url = url or '#'
            elif not url:
                url = '#'
            
            # 特殊处理：新建项目仅对商务经理可见
            if url_name == 'project_pages:project_create':
                if user and not user.roles.filter(code='business_manager').exists():
                    continue
            
            # 特殊处理：系统设置相关功能仅对系统管理员可见
            if url_name and url_name.startswith('system_pages:'):
                system_settings_pages = [
                    'system_pages:system_settings',
                    'system_pages:operation_logs',
                    'system_pages:data_dictionary',
                ]
                if url_name in system_settings_pages:
                    is_system_admin = user.is_superuser or (user.roles.filter(code='system_admin').exists() if hasattr(user, 'roles') else False)
                    if not is_system_admin:
                        continue
            
            section_items.append({
                'label': child.get("label", ""),
                'url': url,
            })
        
        # 如果该模块有可访问的子菜单项，添加到导航
        if section_items:
            full_nav.append({
                'section_label': section.get("label", ""),
                'section_icon': section.get("icon", ""),
                'items': section_items,
            })
    
    return full_nav


def _context(page_title, page_icon, description, summary_cards=None, sections=None, request=None):
    context = {
        "page_title": page_title,
        "page_icon": page_icon,
        "description": description,
        "summary_cards": summary_cards or [],
        "sections": sections or [],
    }
    
    # 添加顶部导航菜单
    if request and request.user.is_authenticated:
        permission_set = get_user_permission_codes(request.user)
        context['full_top_nav'] = _build_full_top_nav(permission_set, request.user)
    else:
        context['full_top_nav'] = []
    
    return context


@login_required
def customer_management(request):
    clients = Client.objects.all()
    summary_cards = [
        {"label": "客户总数", "value": clients.count(), "hint": "系统中维护的客户数量"},
        {
            "label": "活跃客户",
            "value": clients.filter(is_active=True).count(),
            "hint": "状态为活跃的客户数量",
        },
        {
            "label": "VIP 客户",
            "value": clients.filter(client_level="vip").count(),
            "hint": "高价值客户数量",
        },
        {
            "label": "累计合同额",
            "value": f"¥{clients.aggregate(total=Sum('total_contract_amount'))['total'] or Decimal('0'):,.0f}",
            "hint": "录入客户的合同金额汇总",
        },
    ]
    top_clients = clients.order_by("-total_contract_amount")[:6]
    section_items = [
        {
            "label": client.name,
            "description": f"合同额 ¥{client.total_contract_amount:,.0f} · 回款 ¥{client.total_payment_amount:,.0f}",
            "url": "#",
            "icon": "🏢",
        }
        for client in top_clients
    ]
    context = _context(
        "客户管理",
        "🧾",
        "集中维护客户信息、联系人及信用情况，为项目交付与商务沟通提供支持。",
        summary_cards=summary_cards,
        sections=[
            {
                "title": "重点客户",
                "description": "合同金额排名靠前的客户。",
                "items": section_items or [
                    {
                        "label": "暂无客户数据",
                        "description": "请先录入客户基本信息。",
                        "url": "#",
                        "icon": "ℹ️",
                    }
                ],
            }
        ],
        request=request,
    )
    return render(request, "shared/center_dashboard.html", context)


@login_required
def contract_management(request):
    """合同管理列表页面"""
    from django.core.paginator import Paginator
    from django.db.models import Q
    
    # 获取筛选参数
    search = request.GET.get('search', '')
    status = request.GET.get('status', '')
    contract_type = request.GET.get('contract_type', '')
    client_id = request.GET.get('client_id', '')
    project_id = request.GET.get('project_id', '')
    
    # 检查数据库表是否存在
    try:
        from django.db import connection
        with connection.cursor() as cursor:
            cursor.execute("""
                SELECT EXISTS (
                    SELECT FROM information_schema.tables 
                    WHERE table_schema = 'public' 
                    AND table_name = 'business_contract'
                );
            """)
            table_exists = cursor.fetchone()[0]
        
        if not table_exists:
            from django.contrib import messages
            messages.warning(request, '合同管理模块尚未初始化，请先运行数据库迁移：python manage.py migrate')
            return render(request, "customer_success/contract_list.html", _context(
                "合同管理",
                "📃",
                "合同管理模块尚未初始化，请先运行数据库迁移。",
                summary_cards=[],
                sections=[],
                request=request,
            ))
    except Exception as e:
        import logging
        logger = logging.getLogger(__name__)
        logger.exception('检查合同表失败: %s', str(e))
        from django.contrib import messages
        messages.error(request, f'检查数据库表失败：{str(e)}')
        return render(request, "customer_success/contract_list.html", _context(
            "合同管理",
            "📃",
            "无法访问数据库，请检查数据库配置。",
            summary_cards=[],
            sections=[],
            request=request,
        ))
    
    # 获取合同列表
    try:
        contracts = BusinessContract.objects.select_related('client', 'project', 'created_by').order_by('-created_time')
        
        # 应用筛选条件
        if search:
            contracts = contracts.filter(
                Q(contract_number__icontains=search) |
                Q(contract_name__icontains=search) |
                Q(client__name__icontains=search) |
                Q(project__project_number__icontains=search) |
                Q(project__name__icontains=search)
            )
        if status:
            contracts = contracts.filter(status=status)
        if contract_type:
            contracts = contracts.filter(contract_type=contract_type)
        if client_id:
            contracts = contracts.filter(client_id=client_id)
        if project_id:
            contracts = contracts.filter(project_id=project_id)
        
        # 分页
        paginator = Paginator(contracts, 20)
        page_number = request.GET.get('page', 1)
        page_obj = paginator.get_page(page_number)
    except Exception as e:
        import logging
        logger = logging.getLogger(__name__)
        logger.exception('获取合同列表失败: %s', str(e))
        from django.contrib import messages
        messages.error(request, f'获取合同列表失败：{str(e)}')
        page_obj = None
    
    # 统计信息
    try:
        total_contracts = BusinessContract.objects.count()
        total_amount = BusinessContract.objects.aggregate(total=Sum('contract_amount'))['total'] or Decimal('0')
        total_payment = BusinessContract.objects.aggregate(total=Sum('payment_amount'))['total'] or Decimal('0')
        signed_count = BusinessContract.objects.filter(status__in=['signed', 'effective', 'executing']).count()
        
        summary_cards = [
            {"label": "合同总数", "value": total_contracts, "hint": "系统中维护的合同数量"},
            {"label": "合同总额", "value": f"¥{total_amount:,.0f}", "hint": "所有合同的金额汇总"},
            {"label": "已回款", "value": f"¥{total_payment:,.0f}", "hint": "已确认到账的回款金额"},
            {"label": "已签订", "value": signed_count, "hint": "已签订的合同数量"},
        ]
    except Exception as e:
        import logging
        logger = logging.getLogger(__name__)
        logger.exception('获取统计信息失败: %s', str(e))
        summary_cards = [
            {"label": "合同总数", "value": 0, "hint": "统计信息获取失败"},
            {"label": "合同总额", "value": "¥0", "hint": "统计信息获取失败"},
            {"label": "已回款", "value": "¥0", "hint": "统计信息获取失败"},
            {"label": "已签订", "value": 0, "hint": "统计信息获取失败"},
        ]
    
    context = _context(
        "合同管理",
        "📃",
        "跟踪合同执行情况、回款进度及关键商务节点。",
        summary_cards=summary_cards,
        sections=[],
        request=request,
    )
    context.update({
        'contracts': page_obj,
        'clients': Client.objects.filter(is_active=True).order_by('name'),
        'projects': BusinessContract.objects.filter(project__isnull=False).values_list('project_id', 'project__project_number', 'project__name').distinct()[:20],
        'status_choices': BusinessContract.CONTRACT_STATUS_CHOICES,
        'type_choices': BusinessContract.CONTRACT_TYPE_CHOICES,
        'search': search,
        'selected_status': status,
        'selected_type': contract_type,
        'selected_client_id': client_id,
        'selected_project_id': project_id,
    })
    
    return render(request, "customer_success/contract_list.html", context)


@login_required
def contract_detail(request, contract_id):
    """合同详情页面"""
    contract = get_object_or_404(BusinessContract.objects.select_related('client', 'project', 'parent_contract', 'created_by', 'signed_by', 'approved_by'), id=contract_id)
    
    # 获取关联数据
    payment_plans = contract.payment_plans.all().order_by('planned_date')
    files = contract.files.all().order_by('-uploaded_time')
    approvals = contract.approvals.all().order_by('approval_level', '-created_time')
    changes = contract.changes.all().order_by('-created_time')
    sub_contracts = contract.sub_contracts.all().order_by('-created_time')
    status_logs = contract.status_logs.all().order_by('-created_time')
    
    # 获取可流转的状态列表（包含状态代码和标签）
    valid_transition_codes = BusinessContract.get_valid_transitions(contract.status)
    status_choices_dict = dict(BusinessContract.CONTRACT_STATUS_CHOICES)
    valid_transitions = [
        {'code': code, 'label': status_choices_dict.get(code, code)}
        for code in valid_transition_codes
    ]
    
    # 为状态日志添加状态标签
    status_logs_list = []
    for log in status_logs:
        log_dict = {
            'id': log.id,
            'from_status': log.from_status,
            'from_status_label': status_choices_dict.get(log.from_status, log.from_status) if log.from_status else '初始状态',
            'to_status': log.to_status,
            'to_status_label': status_choices_dict.get(log.to_status, log.to_status),
            'actor': log.actor,
            'comment': log.comment,
            'created_time': log.created_time,
        }
        status_logs_list.append(log_dict)
    
    context = {
        'contract': contract,
        'payment_plans': payment_plans,
        'files': files,
        'approvals': approvals,
        'changes': changes,
        'sub_contracts': sub_contracts,
        'status_logs': status_logs_list,
        'valid_transitions': valid_transitions,
        'status_choices': status_choices_dict,
        'page_title': f'合同详情 - {contract.contract_number}',
        'page_icon': '📃',
    }
    
    # 添加顶部导航菜单
    if request.user.is_authenticated:
        permission_set = get_user_permission_codes(request.user)
        context['full_top_nav'] = _build_full_top_nav(permission_set, request.user)
    else:
        context['full_top_nav'] = []
    
    return render(request, "customer_success/contract_detail.html", context)


@login_required
def contract_create(request):
    """新建合同页面"""
    from django.contrib import messages
    
    if request.method == 'POST':
        # 处理表单提交
        try:
            from .forms import ContractForm
            form = ContractForm(request.POST)
            if form.is_valid():
                contract = form.save(commit=False)
                contract.created_by = request.user
                contract.save()
                messages.success(request, f'合同 {contract.contract_number} 创建成功。')
                return redirect('business_pages:contract_detail', contract_id=contract.id)
            else:
                messages.error(request, '表单验证失败，请检查输入。')
        except Exception as e:
            import logging
            logger = logging.getLogger(__name__)
            logger.exception('创建合同失败: %s', str(e))
            messages.error(request, f'创建合同失败：{str(e)}')
    else:
        from .forms import ContractForm
        form = ContractForm()
    
    context = {
        'form': form,
        'page_title': '新建合同',
        'page_icon': '➕',
    }
    
    # 添加顶部导航菜单
    if request.user.is_authenticated:
        permission_set = get_user_permission_codes(request.user)
        context['full_top_nav'] = _build_full_top_nav(permission_set, request.user)
    else:
        context['full_top_nav'] = []
    
    return render(request, "customer_success/contract_form.html", context)


@login_required
def contract_edit(request, contract_id):
    """编辑合同页面"""
    contract = get_object_or_404(BusinessContract, id=contract_id)
    
    if request.method == 'POST':
        # 处理表单提交
        try:
            from .forms import ContractForm
            form = ContractForm(request.POST, instance=contract)
            if form.is_valid():
                contract = form.save()
                messages.success(request, f'合同 {contract.contract_number} 更新成功。')
                return redirect('business_pages:contract_detail', contract_id=contract.id)
            else:
                messages.error(request, '表单验证失败，请检查输入。')
        except Exception as e:
            import logging
            logger = logging.getLogger(__name__)
            logger.exception('更新合同失败: %s', str(e))
            messages.error(request, f'更新合同失败：{str(e)}')
    else:
        from .forms import ContractForm
        form = ContractForm(instance=contract)
    
    context = {
        'form': form,
        'contract': contract,
        'page_title': f'编辑合同 - {contract.contract_number}',
        'page_icon': '✏️',
    }
    
    # 添加顶部导航菜单
    if request.user.is_authenticated:
        permission_set = get_user_permission_codes(request.user)
        context['full_top_nav'] = _build_full_top_nav(permission_set, request.user)
    else:
        context['full_top_nav'] = []
    
    return render(request, "customer_success/contract_form.html", context)


@login_required
def contract_status_transition(request, contract_id):
    """合同状态流转"""
    contract = get_object_or_404(BusinessContract, id=contract_id)
    
    if request.method == 'POST':
        target_status = request.POST.get('target_status')
        comment = request.POST.get('comment', '').strip()
        
        if not target_status:
            messages.error(request, '请选择目标状态。')
            return redirect('business_pages:contract_detail', contract_id=contract.id)
        
        try:
            # 使用模型的流转方法
            contract.transition_to(target_status, actor=request.user, comment=comment)
            target_status_label = dict(BusinessContract.CONTRACT_STATUS_CHOICES).get(target_status, target_status)
            messages.success(request, f'合同状态已成功流转至：{target_status_label}')
        except ValueError as e:
            messages.error(request, str(e))
        except Exception as e:
            import logging
            logger = logging.getLogger(__name__)
            logger.exception('合同状态流转失败: %s', str(e))
            messages.error(request, f'状态流转失败：{str(e)}')
        
        return redirect('business_pages:contract_detail', contract_id=contract.id)
    
    # GET 请求返回详情页
    return redirect('business_pages:contract_detail', contract_id=contract.id)


@login_required
def project_settlement(request):
    settlements = BusinessPaymentPlan.objects.select_related("contract__project")
    status_counts = settlements.values("status").annotate(total=Count("id"))
    status_map = {row["status"]: row["total"] for row in status_counts}
    summary_cards = [
        {"label": "待结算", "value": status_map.get("pending", 0), "hint": "尚未启动结算流程的节点"},
        {"label": "结算中", "value": status_map.get("partial", 0) + status_map.get("overdue", 0), "hint": "正在核对或逾期的结算节点"},
        {"label": "已结算", "value": status_map.get("completed", 0), "hint": "结算完成并归档的节点"},
        {
            "label": "结算项目",
            "value": settlements.values("project_id").distinct().count(),
            "hint": "涉及结算流程的项目数量",
        },
    ]
    latest_settlements = settlements.order_by("-planned_date")[:6]
    section_items = []
    for plan in latest_settlements:
        project = plan.contract.project if plan.contract and plan.contract.project_id else None
        section_items.append({
            'label': f"{project.project_number if project else '未关联'} · {plan.phase_name}",
            'description': f"计划金额 ¥{plan.planned_amount:,.0f} · 状态 {plan.get_status_display()}",
            'url': '#',
            'icon': '💰',
        })
    context = _context(
        "项目结算",
        "🧾",
        "统筹项目回款计划、结算单以及内部核算任务。",
        summary_cards=summary_cards,
        sections=[
            {
                "title": "结算进度",
                "description": "按项目维度查看结算节点和状态。",
                "items": section_items or [
                    {
                        "label": "暂无结算数据",
                        "description": "尚未创建结算计划。",
                        "url": "#",
                        "icon": "ℹ️",
                    }
                ],
            }
        ],
        request=request,
    )
    return render(request, "shared/center_dashboard.html", context)


@login_required
def output_analysis(request):
    contracts = BusinessContract.objects.select_related('project')
    payments = BusinessPaymentPlan.objects.all()
    total_contract = contracts.aggregate(total=Sum('amount'))['total'] or Decimal('0')
    total_payment = payments.aggregate(total=Sum('actual_amount'))['total'] or Decimal('0')
    summary_cards = [
        {"label": "合同数量", "value": contracts.count(), "hint": "已录入的商务合同数量"},
        {"label": "合同金额", "value": f"¥{total_contract:,.0f}", "hint": "合同金额汇总"},
        {"label": "已回款", "value": f"¥{total_payment:,.0f}", "hint": "实际到账金额"},
        {"label": "回款进度", "value": _calc_ratio(total_payment, total_contract), "hint": "回款金额占合同金额比例"},
    ]
    context = _context(
        "产值分析",
        "📊",
        "汇总商务合同与回款数据，为经营分析提供支持。",
        summary_cards=summary_cards,
        sections=[
            {
                "title": "常用报表",
                "description": "产值分析所需的核心报表与数据视图。",
                "items": [
                    {"label": "合同执行情况", "description": "查看合同签订、变更与执行情况。", "url": "#", "icon": "📑"},
                    {"label": "回款趋势分析", "description": "跟踪月度回款走势与贡献度。", "url": "#", "icon": "📈"},
                    {"label": "客户贡献榜", "description": "识别合同金额贡献度较高的客户。", "url": "#", "icon": "🏆"},
                ],
            }
        ],
        request=request,
    )
    return render(request, "shared/center_dashboard.html", context)


@login_required
def payment_tracking(request):
    plans = BusinessPaymentPlan.objects.select_related("contract__project").order_by("planned_date")[:8]
    outstanding = sum(
        max((plan.planned_amount or Decimal("0")) - (plan.actual_amount or Decimal("0")), Decimal("0"))
        for plan in plans
        if plan.status in {"pending", "partial", "overdue"}
    )
    summary_cards = [
        {"label": "待回款金额", "value": f"¥{outstanding:,.0f}", "hint": "尚未到账的计划金额"},
        {"label": "提醒节点", "value": plans.filter(status="pending").count(), "hint": "需要提醒的回款节点"},
        {"label": "已到账节点", "value": plans.filter(status="completed").count(), "hint": "已完成收款的节点数量"},
        {
            "label": "本月到期",
            "value": plans.filter(planned_date__month=timezone.now().month).count(),
            "hint": "本月即将到期的回款计划数量",
        },
    ]
    section_items = []
    for plan in plans:
        project = plan.contract.project if plan.contract and plan.contract.project_id else None
        section_items.append({
            'label': f"{project.project_number if project else '未关联'} · {plan.phase_name}",
            'description': f"计划金额 ¥{plan.planned_amount:,.0f} · 状态 {plan.get_status_display()}",
            'url': '#',
            'icon': '⏰',
        })
    context = _context(
        "收款跟踪",
        "💵",
        "统一跟踪项目回款节点、提醒通知与实际到账情况。",
        summary_cards=summary_cards,
        sections=[
            {
                "title": "回款计划",
                "description": "重点关注即将到期的回款与提醒。",
                "items": section_items or [
                    {
                        "label": "暂无回款计划",
                        "description": "请在项目中配置回款计划。",
                        "url": "#",
                        "icon": "ℹ️",
                    }
                ],
            }
        ],
        request=request,
    )
    return render(request, "shared/center_dashboard.html", context)


def _calc_progress(summary):
    expected = summary.get("planned_total") or Decimal("0")
    actual = summary.get("actual_total") or Decimal("0")
    if expected == 0:
        return "--"
    return f"{(actual / expected * 100):.0f}%"


def _calc_ratio(value, base):
    if not base:
        return "--"
    return f"{(value / base * 100):.1f}%"


# ==================== 商机管理视图 ====================

@login_required
def opportunity_management(request):
    """商机管理列表页面"""
    from django.core.paginator import Paginator
    
    # 获取筛选参数
    search = request.GET.get('search', '')
    status = request.GET.get('status', '')
    client_id = request.GET.get('client_id', '')
    business_manager_id = request.GET.get('business_manager_id', '')
    urgency = request.GET.get('urgency', '')
    
    # 获取权限
    permission_set = get_user_permission_codes(request.user)
    
    # 获取商机列表
    try:
        opportunities = BusinessOpportunity.objects.select_related(
            'client', 'business_manager', 'created_by'
        ).prefetch_related('followups').order_by('-created_time')
        
        # 权限过滤：普通商务经理只能看自己负责的商机
        if not _permission_granted('customer_success.opportunity.view_all', permission_set):
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
        
        # 分页
        paginator = Paginator(opportunities, 20)
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
        total_opportunities = BusinessOpportunity.objects.count()
        active_opportunities = BusinessOpportunity.objects.exclude(
            status__in=['won', 'lost', 'cancelled']
        ).count()
        total_weighted_amount = BusinessOpportunity.objects.exclude(
            status__in=['won', 'lost', 'cancelled']
        ).aggregate(total=Sum('weighted_amount'))['total'] or Decimal('0')
        won_count = BusinessOpportunity.objects.filter(status='won').count()
        
        summary_cards = [
            {"label": "商机总数", "value": total_opportunities, "hint": "系统中维护的商机数量"},
            {"label": "活跃商机", "value": active_opportunities, "hint": "状态为活跃的商机数量"},
            {"label": "加权金额", "value": f"¥{total_weighted_amount:,.0f}万", "hint": "按成功概率加权的预计金额"},
            {"label": "赢单数量", "value": won_count, "hint": "已赢单的商机数量"},
        ]
    except Exception as e:
        import logging
        logger = logging.getLogger(__name__)
        logger.exception('获取统计信息失败: %s', str(e))
        summary_cards = []
    
    # 获取筛选选项
    clients = Client.objects.filter(is_active=True).order_by('name')
    business_managers = request.user.__class__.objects.filter(
        roles__code='business_manager'
    ).distinct().order_by('username')
    
    context = _context(
        "商机管理",
        "💼",
        "从潜在客户到签约项目的全流程数字化管理，实现销售漏斗可视化和过程标准化。",
        summary_cards=summary_cards,
        request=request,
    )
    context.update({
        'page_obj': page_obj,
        'search': search,
        'status': status,
        'client_id': client_id,
        'business_manager_id': business_manager_id,
        'urgency': urgency,
        'clients': clients,
        'business_managers': business_managers,
        'status_choices': BusinessOpportunity.STATUS_CHOICES,
        'urgency_choices': BusinessOpportunity.URGENCY_CHOICES,
    })
    return render(request, "customer_success/opportunity_list.html", context)


@login_required
def opportunity_detail(request, opportunity_id):
    """商机详情页面"""
    opportunity = get_object_or_404(
        BusinessOpportunity.objects.select_related('client', 'business_manager', 'created_by', 'approver'),
        id=opportunity_id
    )
    
    # 权限检查
    permission_set = get_user_permission_codes(request.user)
    if not _permission_granted('customer_success.opportunity.view', permission_set):
        if opportunity.business_manager != request.user:
            messages.error(request, '您没有权限查看此商机')
            return redirect('business_pages:opportunity_management')
    
    # 获取关联数据
    followups = opportunity.followups.select_related('created_by').order_by('-follow_date', '-created_time')
    quotations = opportunity.quotations.select_related('created_by', 'quotation_rule').order_by('-version_number')
    approvals = opportunity.approvals.select_related('approver').order_by('approval_level', '-created_time')
    status_logs = opportunity.status_logs.select_related('actor').order_by('-created_time')
    
    context = _context(
        f"商机详情 - {opportunity.name}",
        "💼",
        f"商机编号：{opportunity.opportunity_number}",
        request=request,
    )
    context.update({
        'opportunity': opportunity,
        'followups': followups,
        'quotations': quotations,
        'approvals': approvals,
        'status_logs': status_logs,
        'can_edit': _permission_granted('customer_success.opportunity.manage', permission_set) or opportunity.business_manager == request.user,
        'can_approve': _permission_granted('customer_success.opportunity.approve', permission_set),
    })
    return render(request, "customer_success/opportunity_detail.html", context)


@login_required
def opportunity_create(request):
    """创建商机"""
    from django import forms
    
    # 权限检查
    permission_set = get_user_permission_codes(request.user)
    if not _permission_granted('customer_success.opportunity.create', permission_set):
        messages.error(request, '您没有权限创建商机')
        return redirect('business_pages:opportunity_management')
    
    if request.method == 'POST':
        try:
            opportunity = BusinessOpportunity.objects.create(
                name=request.POST.get('name'),
                client_id=request.POST.get('client_id'),
                business_manager_id=request.POST.get('business_manager_id') or request.user.id,
                project_name=request.POST.get('project_name', ''),
                project_address=request.POST.get('project_address', ''),
                project_type=request.POST.get('project_type', ''),
                building_area=request.POST.get('building_area') or None,
                drawing_stage=request.POST.get('drawing_stage', ''),
                estimated_amount=request.POST.get('estimated_amount') or 0,
                success_probability=int(request.POST.get('success_probability', 10)),
                status=request.POST.get('status', 'potential'),
                urgency=request.POST.get('urgency', 'normal'),
                expected_sign_date=request.POST.get('expected_sign_date') or None,
                description=request.POST.get('description', ''),
                notes=request.POST.get('notes', ''),
                created_by=request.user,
            )
            messages.success(request, f'商机 {opportunity.opportunity_number} 创建成功')
            return redirect('business_pages:opportunity_detail', opportunity_id=opportunity.id)
        except Exception as e:
            import logging
            logger = logging.getLogger(__name__)
            logger.exception('创建商机失败: %s', str(e))
            messages.error(request, f'创建商机失败：{str(e)}')
    
    # GET请求，显示创建表单
    clients = Client.objects.filter(is_active=True).order_by('name')
    business_managers = request.user.__class__.objects.filter(
        roles__code='business_manager'
    ).distinct().order_by('username')
    
    context = _context(
        "创建商机",
        "➕",
        "录入新的商机信息，开始跟踪销售机会。",
        request=request,
    )
    context.update({
        'clients': clients,
        'business_managers': business_managers,
        'status_choices': BusinessOpportunity.STATUS_CHOICES,
        'urgency_choices': BusinessOpportunity.URGENCY_CHOICES,
        'default_business_manager': request.user,
    })
    return render(request, "customer_success/opportunity_form.html", context)


@login_required
def opportunity_edit(request, opportunity_id):
    """编辑商机"""
    opportunity = get_object_or_404(BusinessOpportunity, id=opportunity_id)
    
    # 权限检查
    permission_set = get_user_permission_codes(request.user)
    can_edit = _permission_granted('customer_success.opportunity.manage', permission_set) or opportunity.business_manager == request.user
    if not can_edit:
        messages.error(request, '您没有权限编辑此商机')
        return redirect('business_pages:opportunity_detail', opportunity_id=opportunity_id)
    
    if request.method == 'POST':
        try:
            opportunity.name = request.POST.get('name')
            opportunity.client_id = request.POST.get('client_id')
            opportunity.business_manager_id = request.POST.get('business_manager_id')
            opportunity.project_name = request.POST.get('project_name', '')
            opportunity.project_address = request.POST.get('project_address', '')
            opportunity.project_type = request.POST.get('project_type', '')
            opportunity.building_area = request.POST.get('building_area') or None
            opportunity.drawing_stage = request.POST.get('drawing_stage', '')
            opportunity.estimated_amount = request.POST.get('estimated_amount') or 0
            opportunity.success_probability = int(request.POST.get('success_probability', 10))
            opportunity.status = request.POST.get('status', 'potential')
            opportunity.urgency = request.POST.get('urgency', 'normal')
            opportunity.expected_sign_date = request.POST.get('expected_sign_date') or None
            opportunity.description = request.POST.get('description', '')
            opportunity.notes = request.POST.get('notes', '')
            opportunity.save(update_health=True)
            messages.success(request, '商机信息已更新')
            return redirect('business_pages:opportunity_detail', opportunity_id=opportunity.id)
        except Exception as e:
            import logging
            logger = logging.getLogger(__name__)
            logger.exception('更新商机失败: %s', str(e))
            messages.error(request, f'更新商机失败：{str(e)}')
    
    # GET请求，显示编辑表单
    clients = Client.objects.filter(is_active=True).order_by('name')
    business_managers = request.user.__class__.objects.filter(
        roles__code='business_manager'
    ).distinct().order_by('username')
    
    context = _context(
        f"编辑商机 - {opportunity.name}",
        "✏️",
        f"商机编号：{opportunity.opportunity_number}",
        request=request,
    )
    context.update({
        'opportunity': opportunity,
        'clients': clients,
        'business_managers': business_managers,
        'status_choices': BusinessOpportunity.STATUS_CHOICES,
        'urgency_choices': BusinessOpportunity.URGENCY_CHOICES,
    })
    return render(request, "customer_success/opportunity_form.html", context)


@login_required
def opportunity_delete(request, opportunity_id):
    """删除商机"""
    opportunity = get_object_or_404(BusinessOpportunity, id=opportunity_id)
    
    # 权限检查
    permission_set = get_user_permission_codes(request.user)
    can_delete = _permission_granted('customer_success.opportunity.manage', permission_set) or opportunity.business_manager == request.user
    if not can_delete:
        messages.error(request, '您没有权限删除此商机')
        return redirect('business_pages:opportunity_detail', opportunity_id=opportunity_id)
    
    if request.method == 'POST':
        try:
            opportunity_number = opportunity.opportunity_number
            opportunity.delete()
            messages.success(request, f'商机 {opportunity_number} 已删除')
            return redirect('business_pages:opportunity_management')
        except Exception as e:
            import logging
            logger = logging.getLogger(__name__)
            logger.exception('删除商机失败: %s', str(e))
            messages.error(request, f'删除商机失败：{str(e)}')
    
    context = _context(
        f"删除商机 - {opportunity.name}",
        "🗑️",
        f"确认删除商机：{opportunity.opportunity_number}",
        request=request,
    )
    context.update({
        'opportunity': opportunity,
    })
    return render(request, "customer_success/opportunity_delete_confirm.html", context)


@login_required
def opportunity_status_transition(request, opportunity_id):
    """商机状态流转"""
    opportunity = get_object_or_404(BusinessOpportunity, id=opportunity_id)
    
    # 权限检查
    permission_set = get_user_permission_codes(request.user)
    can_manage = _permission_granted('customer_success.opportunity.manage', permission_set) or opportunity.business_manager == request.user
    if not can_manage:
        messages.error(request, '您没有权限操作此商机')
        return redirect('business_pages:opportunity_detail', opportunity_id=opportunity_id)
    
    if request.method == 'POST':
        target_status = request.POST.get('target_status')
        comment = request.POST.get('comment', '')
        
        try:
            # 执行状态流转
            opportunity.transition_to(target_status, actor=request.user, comment=comment)
            
            # 如果状态变为赢单，创建待办事项
            if target_status == 'won':
                actual_amount = request.POST.get('actual_amount')
                contract_number = request.POST.get('contract_number', '')
                win_reason = request.POST.get('win_reason', '')
                
                if actual_amount:
                    opportunity.actual_amount = Decimal(actual_amount)
                if contract_number:
                    opportunity.contract_number = contract_number
                if win_reason:
                    opportunity.win_reason = win_reason
                opportunity.actual_sign_date = timezone.now().date()
                opportunity.save()
                
                # 创建待办事项通知商务经理
                from backend.apps.project_center.models import ProjectTeamNotification
                ProjectTeamNotification.objects.create(
                    project=None,
                    recipient_user=opportunity.business_manager,
                    title=f'商机赢单：{opportunity.name}',
                    message=f'商机已赢单，实际签约金额：{opportunity.actual_amount or opportunity.estimated_amount}万元，请及时处理后续事项。',
                    notification_type='business_opportunity_won',
                    action_url=reverse('business_pages:opportunity_detail', args=[opportunity.id]),
                    operator=request.user,
                )
            
            messages.success(request, f'商机状态已更新为：{opportunity.get_status_display()}')
            return redirect('business_pages:opportunity_detail', opportunity_id=opportunity.id)
        except ValueError as e:
            messages.error(request, str(e))
        except Exception as e:
            import logging
            logger = logging.getLogger(__name__)
            logger.exception('状态流转失败: %s', str(e))
            messages.error(request, f'状态流转失败：{str(e)}')
    
    # GET请求，显示状态流转表单
    valid_transitions = opportunity.get_valid_transitions(opportunity.status)
    
    context = _context(
        f"状态流转 - {opportunity.name}",
        "🔄",
        f"当前状态：{opportunity.get_status_display()}",
        request=request,
    )
    context.update({
        'opportunity': opportunity,
        'valid_transitions': valid_transitions,
        'status_choices': BusinessOpportunity.STATUS_CHOICES,
    })
    return render(request, "customer_success/opportunity_status_transition.html", context)

