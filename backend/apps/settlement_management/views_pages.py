from django.contrib.auth.decorators import login_required
from django.shortcuts import render, get_object_or_404, redirect
from django.contrib import messages
from django.core.exceptions import PermissionDenied
from django.db.models import Q, Sum, Count, F, Avg
from django.utils import timezone
from decimal import Decimal
from datetime import timedelta, datetime

# 产值管理相关模型已迁移到output_value_management
# from backend.apps.settlement_center.models import (
#     OutputValueStage, OutputValueMilestone, OutputValueEvent, OutputValueRecord
# )
# PaymentRecord已迁移到payment_management
from backend.apps.payment_management.models import PaymentRecord
from backend.apps.settlement_management.models import (
    ProjectSettlement, SettlementItem, ServiceFeeRate, ContractSettlement
)
# from backend.apps.production_quality.models import Opinion  # 已删除生产质量模块
from .forms import ProjectSettlementForm, ContractSettlementForm
# 产值管理相关服务函数已迁移到output_value_management
# 结算管理仍需要调用产值管理的服务函数
from backend.apps.output_value_management.services import get_project_output_value_for_settlement
from backend.apps.production_management.models import Project
from backend.apps.system_management.models import User
from backend.apps.system_management.services import get_user_permission_codes
from backend.core.views import _permission_granted, _build_full_top_nav
from backend.apps.contract_management.models import BusinessContract
from django.urls import reverse, NoReverseMatch
from django.core.paginator import Paginator
from django.db.models import Max



# ==================== 结算管理模块左侧菜单结构 =====================
SETTLEMENT_MENU = [
    {
        'id': 'settlement_management_home',
        'label': '结算管理首页',
        'icon': '🏠',
        'url_name': 'settlement_pages:settlement_management_home',
        'permission': 'settlement_management.view',
    },
    {
        'id': 'project_settlement',
        'label': '项目结算',
        'icon': '💰',
        'url_name': 'settlement_pages:project_settlement_list',
        'permission': 'settlement_management.view',
    },
    {
        'id': 'contract_settlement',
        'label': '合同结算',
        'icon': '📄',
        'url_name': 'settlement_pages:project_settlement_list',  # 合同结算入口暂用项目结算列表，后续可单独实现
        'permission': 'settlement_management.view',
    },
]


def _build_settlement_sidebar_nav(permission_set, request_path=None, active_id=None):
    """生成回款管理左侧菜单（统一格式）"""
    # 尝试导入统一的构建函数
    try:
        from backend.core.views import _build_unified_sidebar_nav
        return _build_unified_sidebar_nav(SETTLEMENT_MENU, permission_set, active_id=active_id)
    except ImportError:
        # Fallback: 如果 _build_unified_sidebar_nav 不存在，提供简单实现
        nav = []
        for item in SETTLEMENT_MENU:
            if item.get('permission'):
                if not _permission_granted(item['permission'], permission_set):
                    continue
            
            # 处理 URL：优先使用 url_name 转换为真实 URL
            url = '#'
            url_name = item.get('url_name')
            if url_name:
                try:
                    url = reverse(url_name)
                except NoReverseMatch:
                    url = item.get('url', '#')
            else:
                url = item.get('url', '#')
            
            nav_item = {
                'label': item.get('label', ''),
                'icon': item.get('icon', ''),
                'url': url,
                'active': item.get('id') == active_id if active_id else False,
            }
            
            # 处理子菜单
            if 'children' in item:
                children = []
                for child in item['children']:
                    # 检查子菜单权限
                    if child.get('permission'):
                        if not _permission_granted(child['permission'], permission_set):
                            continue
                    
                    # 处理子菜单 URL
                    child_url = '#'
                    child_url_name = child.get('url_name')
                    if child_url_name:
                        try:
                            child_url = reverse(child_url_name)
                        except NoReverseMatch:
                            child_url = child.get('url', '#')
                    else:
                        child_url = child.get('url', '#')
                    
                    children.append({
                        'label': child.get('label', ''),
                        'icon': child.get('icon', ''),
                        'url': child_url,
                        'active': child.get('id') == active_id if active_id else False,
                    })
                
                nav_item['children'] = children
            
            nav.append(nav_item)
        
        return nav


def _context(page_title, page_icon, description, summary_cards=None, sections=None, request=None):
    """统一的页面上下文生成函数"""
    context = {
        "page_title": page_title,
        "page_icon": page_icon,
        "description": description,
        "summary_cards": summary_cards or [],
        "sections": sections or [],
    }
    
    # 添加顶部导航栏和左侧菜单
    if request and request.user.is_authenticated:
        try:
            permission_set = get_user_permission_codes(request.user)
            context['full_top_nav'] = _build_full_top_nav(permission_set, request.user)
            # 添加左侧菜单
            context['sidebar_nav'] = _build_settlement_sidebar_nav(permission_set, request.path)
            context['sidebar_title'] = '结算管理'
            context['sidebar_subtitle'] = 'Settlement Management'
        except Exception as e:
            import logging
            logger = logging.getLogger(__name__)
            logger.exception('构建导航栏失败: %s', str(e))
            context['full_top_nav'] = []
            context['settlement_menu'] = []
            context['settlement_sidebar_nav'] = []
    else:
        context['full_top_nav'] = []
        context['settlement_menu'] = []
        context['settlement_sidebar_nav'] = []
    # 为所有可能的侧边栏变量设置默认值，避免模板错误
    context.setdefault('plan_menu', [])
    context.setdefault('sidebar_nav', [])
    context.setdefault('customer_menu', [])
    context.setdefault('sidebar_nav', [])
    context.setdefault('sidebar_nav', [])
    context.setdefault('sidebar_nav', [])
    context.setdefault('sidebar_nav', [])
    context.setdefault('sidebar_nav', [])
    context.setdefault('sidebar_nav', [])
    context.setdefault('sidebar_nav', [])
    context.setdefault('administrative_sidebar_nav', [])
    
    return context


# 产值管理相关视图函数已迁移到output_value_management
# 以下函数已删除：
# - output_value_template_manage
# - output_value_record_list
# - project_output_value_detail
# - output_value_record_confirm
# - output_value_statistics


# ==================== 结算管理辅助函数 ====================

def _generate_settlement_items_from_opinions(settlement, user):
    """从项目的Opinion生成结算明细项（已禁用：生产质量模块已删除）"""
    # 生产质量模块已删除，此功能已禁用
    # 保留函数定义以避免调用错误，但返回0表示未生成任何明细项
    import logging
    logger = logging.getLogger(__name__)
    logger.warning('尝试从Opinion生成结算明细项，但生产质量模块已删除')
    return 0


# ==================== 结算管理视图函数 ====================

@login_required
def project_settlement_list(request):
    """项目结算列表页"""
    permission_codes = get_user_permission_codes(request.user)
    if not _permission_granted('settlement_management.settlement.view', permission_codes):
        messages.error(request, '您没有权限查看项目结算')
        return redirect('settlement_pages:settlement_management_home')
    
    settlements = ProjectSettlement.objects.select_related(
        'project', 'contract', 'created_by'
    ).order_by('-settlement_date', '-created_time')
    
    # 权限过滤：如果不是管理员，只能查看自己创建的
    if not _permission_granted('settlement_management.settlement.manage', permission_codes):
        settlements = settlements.filter(created_by=request.user)
    
    # 筛选
    status_filter = request.GET.get('status')
    if status_filter:
        settlements = settlements.filter(status=status_filter)
    
    project_id = request.GET.get('project_id')
    if project_id:
        settlements = settlements.filter(project_id=project_id)
    
    # 分页
    page_size = request.GET.get('page_size', '10')
    try:
        per_page = int(page_size)
        if per_page not in [10, 20, 50]:
            per_page = 10
    except (ValueError, TypeError):
        per_page = 10
    paginator = Paginator(settlements, per_page)
    page_number = request.GET.get('page', 1)
    page_obj = paginator.get_page(page_number)
    
    # 统计信息
    total_count = settlements.count()
    total_amount = settlements.filter(status__in=['confirmed', 'reconciliation']).aggregate(
        total=Sum('total_settlement_amount')
    )['total'] or Decimal('0')
    pending_count = settlements.filter(status__in=['submitted', 'client_review', 'client_feedback', 'reconciliation']).count()
    
    summary_cards = []
    
    context = _context(
        "项目结算管理",
        "💰",
        "管理项目结算单，包括结算申请、审核和确认",
        summary_cards=summary_cards,
        request=request,
    )
    context.update({
        'settlements': page_obj,
        'projects': Project.objects.filter(status__in=['in_progress', 'completed']).order_by('-created_time'),
        'status_choices': ProjectSettlement.STATUS_CHOICES,
        'status_filter': status_filter,
        'project_id': project_id,
        'can_create': _permission_granted('settlement_management.settlement.create', permission_codes),
    })
    
    return render(request, "settlement_management/project_settlement_list.html", context)


@login_required
def project_settlement_detail(request, settlement_id):
    """项目结算详情页"""
    settlement = get_object_or_404(ProjectSettlement, id=settlement_id)
    permission_codes = get_user_permission_codes(request.user)
    
    # 权限检查：只有有查看权限或创建人可以查看
    if not _permission_granted('settlement_management.settlement.view', permission_codes):
        if settlement.created_by != request.user:
            messages.error(request, '您没有权限查看此结算单')
            return redirect('settlement_pages:project_settlement_list')
    
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
        (_permission_granted('settlement_management.settlement.manage', permission_codes) or
         settlement.created_by == request.user)
    )
    can_submit = (
        settlement.status == 'draft' and
        (_permission_granted('settlement_management.settlement.manage', permission_codes) or
         settlement.created_by == request.user)
    )
    can_finance_review = (
        settlement.status == 'submitted' and
        _permission_granted('settlement_management.settlement.finance_review', permission_codes)
    )
    can_manager_approve = (
        settlement.status == 'finance_review' and
        _permission_granted('settlement_management.settlement.manager_approve', permission_codes)
    )
    can_gm_approve = (
        settlement.status == 'manager_approve' and
        _permission_granted('settlement_management.settlement.gm_approve', permission_codes)
    )
    can_confirm = (
        settlement.status == 'approved' and
        _permission_granted('settlement_management.settlement.confirm', permission_codes)
    )
    
    context = _context(
        f"项目结算 - {settlement.settlement_number}",
        "💰",
        f"项目：{settlement.project.name}",
        request=request,
    )
    # 获取结算明细项
    settlement_items = settlement.items.select_related('reviewed_by', 'created_by').order_by('order')
    
    # 检查是否有权限审核明细项（造价工程师或有管理权限）
    can_review_items = (
        settlement.status == 'draft' and
        (_permission_granted('settlement_management.settlement.manage', permission_codes) or
         request.user.roles.filter(code='cost_engineer').exists())
    )
    
    # 检查是否可以重新生成明细项
    can_generate_items = (
        settlement.status == 'draft' and
        (_permission_granted('settlement_management.settlement.manage', permission_codes) or
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
    
    return render(request, "settlement_management/project_settlement_detail.html", context)


@login_required
def project_settlement_create(request):
    """创建项目结算单"""
    permission_codes = get_user_permission_codes(request.user)
    if not _permission_granted('settlement_management.settlement.create', permission_codes):
        messages.error(request, '您没有权限创建项目结算单')
        return redirect('settlement_pages:project_settlement_list')
    
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
            
            return redirect('settlement_pages:project_settlement_detail', settlement_id=settlement.id)
        else:
            messages.error(request, "请检查表单中的错误。")
    else:
        form = ProjectSettlementForm(user=request.user)
    
    context = _context(
        "新增项目结算单",
        "➕",
        "创建新的项目结算单",
        request=request,
    )
    context.update({
        'form': form,
        'is_create': True,
    })
    
    return render(request, "settlement_management/project_settlement_form.html", context)


@login_required
def project_settlement_update(request, settlement_id):
    """编辑项目结算单"""
    settlement = get_object_or_404(ProjectSettlement, id=settlement_id)
    permission_codes = get_user_permission_codes(request.user)
    
    # 权限检查：只有草稿状态才能编辑，且必须是创建人或管理员
    if settlement.status != 'draft':
        messages.error(request, '只有草稿状态的结算单才能编辑')
        return redirect('settlement_pages:project_settlement_detail', settlement_id=settlement.id)
    
    if not _permission_granted('settlement_management.settlement.manage', permission_codes):
        if settlement.created_by != request.user:
            messages.error(request, '您没有权限编辑此结算单')
            return redirect('settlement_pages:project_settlement_detail', settlement_id=settlement.id)
    
    if request.method == 'POST':
        form = ProjectSettlementForm(request.POST, request.FILES, instance=settlement, user=request.user)
        if form.is_valid():
            settlement = form.save()
            messages.success(request, f'项目结算单 {settlement.settlement_number} 更新成功！')
            return redirect('settlement_pages:project_settlement_detail', settlement_id=settlement.id)
        else:
            messages.error(request, "请检查表单中的错误。")
    else:
        form = ProjectSettlementForm(instance=settlement, user=request.user)
    
    context = _context(
        f"编辑项目结算单 - {settlement.settlement_number}",
        "✏️",
        f"项目：{settlement.project.name}",
        request=request,
    )
    context.update({
        'form': form,
        'settlement': settlement,
        'is_create': False,
    })
    
    return render(request, "settlement_management/project_settlement_form.html", context)


@login_required
def project_settlement_submit(request, settlement_id):
    """提交结算单审核"""
    settlement = get_object_or_404(ProjectSettlement, id=settlement_id)
    permission_codes = get_user_permission_codes(request.user)
    
    if settlement.status != 'draft':
        messages.error(request, '只有草稿状态的结算单才能提交')
        return redirect('settlement_pages:project_settlement_detail', settlement_id=settlement.id)
    
    if not _permission_granted('settlement_management.settlement.manage', permission_codes):
        if settlement.created_by != request.user:
            messages.error(request, '您没有权限提交此结算单')
            return redirect('settlement_pages:project_settlement_detail', settlement_id=settlement.id)
    
    if request.method == 'POST':
        settlement.status = 'submitted'
        settlement.submitted_by = request.user
        settlement.submitted_time = timezone.now()
        settlement.save(update_fields=['status', 'submitted_by', 'submitted_time', 'updated_time'])
        messages.success(request, '结算单已提交审核')
        return redirect('settlement_pages:project_settlement_detail', settlement_id=settlement.id)
    
    context = _context(
        "提交结算单",
        "📤",
        f"确认提交结算单 {settlement.settlement_number} 进行审核？",
        request=request,
    )
    context.update({
        'settlement': settlement,
    })
    return render(request, "settlement_management/project_settlement_confirm.html", context)


# ==================== 回款管理模块（已独立至 payment_management，入口 /payment/） ====================
# 以下视图未在 settlement_pages 注册，回款入口请使用 payment_pages（/payment/）

@login_required
def payment_plan_list(request):
    """回款计划列表页面（未挂路由，回款请访问 /payment/）"""
    # 注意：项目回款计划模型已从project_center模块删除，现在只使用商务回款计划
    from backend.apps.production_management.models import BusinessPaymentPlan
    
    permission_codes = get_user_permission_codes(request.user)
    
    # 权限检查：暂时注释掉，因为权限可能还未创建
    # if not _permission_granted('payment_management.payment_plan.view', permission_codes):
    #     messages.error(request, '您没有权限查看回款计划')
    #     return redirect('home')
    
    # 获取筛选参数
    search = request.GET.get('search', '')
    status_filter = request.GET.get('status', '')
    plan_type = request.GET.get('plan_type', '')  # 'project' or 'business'
    
    # 获取商务回款计划
    business_plans = BusinessPaymentPlan.objects.select_related('contract', 'contract__client').all()
    
    # 项目回款计划已不存在，设置为空
    project_plans = BusinessPaymentPlan.objects.none()
    
    # 应用筛选
    if search:
        business_plans = business_plans.filter(
            Q(phase_name__icontains=search) |
            Q(contract__contract_number__icontains=search) |
            Q(contract__client__name__icontains=search)
        )
    
    if status_filter:
        business_plans = business_plans.filter(status=status_filter)
    
    if plan_type == 'project':
        # 项目回款计划已不存在，返回空结果
        business_plans = business_plans.none()
    
    # 合并数据并排序
    all_plans = []
    # 注意：项目回款计划模型已删除，现在只处理商务回款计划
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
    page_size = request.GET.get('page_size', '10')
    try:
        per_page = int(page_size)
        if per_page not in [10, 20, 50]:
            per_page = 10
    except (ValueError, TypeError):
        per_page = 10
    paginator = Paginator(all_plans, per_page)
    page_number = request.GET.get('page', 1)
    page_obj = paginator.get_page(page_number)
    
    # 统计信息
    total_plans = len(all_plans)
    total_planned_amount = sum(p['planned_amount'] for p in all_plans)
    total_actual_amount = sum(p['actual_amount'] for p in all_plans)
    
    summary_cards = []
    
    context = _context(
        "回款计划管理",
        "💳",
        "统一管理项目回款计划和商务合同回款计划",
        summary_cards=summary_cards,
        request=request,
    )
    context.update({
        'page_obj': page_obj,
        'search': search,
        'status_filter': status_filter,
        'plan_type': plan_type,
        'status_choices': BusinessPaymentPlan.STATUS_CHOICES,
    })
    return render(request, "settlement_management/payment_plan_list.html", context)


@login_required
def payment_plan_detail(request, plan_type, plan_id):
    """回款计划详情页面"""
    # 注意：项目回款计划模型已从project_center模块删除，现在只使用商务回款计划
    from backend.apps.production_management.models import BusinessPaymentPlan
    
    permission_codes = get_user_permission_codes(request.user)
    
    # 根据类型获取回款计划
    if plan_type == 'project':
        # 项目回款计划已不存在，返回错误
        messages.error(request, '项目回款计划功能已移除，请使用商务回款计划')
        return redirect('settlement_pages:payment_plan_list')
    elif plan_type == 'business':
        plan = get_object_or_404(BusinessPaymentPlan, id=plan_id)
        related_obj = plan.contract
    else:
        messages.error(request, '无效的回款计划类型')
        return redirect('settlement_pages:payment_plan_list')
    
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
        request=request,
    )
    context.update({
        'plan': plan,
        'plan_type': plan_type,
        'related_obj': related_obj,
        'payment_records': payment_records,
        'total_received': total_received,
        'remaining_amount': plan.planned_amount - total_received,
    })
    return render(request, "settlement_management/payment_plan_detail.html", context)


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
    page_size = request.GET.get('page_size', '10')
    try:
        per_page = int(page_size)
        if per_page not in [10, 20, 50]:
            per_page = 10
    except (ValueError, TypeError):
        per_page = 10
    paginator = Paginator(payment_records, per_page)
    page_number = request.GET.get('page', 1)
    page_obj = paginator.get_page(page_number)
    
    # 统计信息
    total_records = payment_records.count()
    total_amount = payment_records.filter(status='confirmed').aggregate(
        total=Sum('payment_amount')
    )['total'] or Decimal('0')
    
    summary_cards = []
    
    context = _context(
        "回款记录管理",
        "💰",
        "管理所有实际回款记录",
        summary_cards=summary_cards,
        request=request,
    )
    context.update({
        'page_obj': page_obj,
        'search': search,
        'status_filter': status_filter,
        'start_date': start_date,
        'end_date': end_date,
        'status_choices': PaymentRecord._meta.get_field('status').choices,
    })
    return render(request, "settlement_management/payment_record_list.html", context)


@login_required
def payment_record_create(request, plan_type, plan_id):
    """创建回款记录"""
    permission_codes = get_user_permission_codes(request.user)
    
    if not _permission_granted('payment_management.payment_record.create', permission_codes):
        messages.error(request, '您没有权限创建回款记录')
        return redirect('settlement_pages:payment_plan_list')
    
    # 获取回款计划
    if plan_type == 'project':
        # 项目回款计划已不存在，返回错误
        messages.error(request, '项目回款计划功能已移除，请使用商务回款计划')
        return redirect('settlement_pages:payment_plan_list')
    elif plan_type == 'business':
        from backend.apps.production_management.models import BusinessPaymentPlan
        plan = get_object_or_404(BusinessPaymentPlan, id=plan_id)
    else:
        messages.error(request, '无效的回款计划类型')
        return redirect('settlement_pages:payment_plan_list')
    
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
                return redirect('settlement_pages:payment_plan_detail', plan_type=plan_type, plan_id=plan_id)
        except Exception as e:
            import logging
            logger = logging.getLogger(__name__)
            logger.exception('创建回款记录失败: %s', str(e))
            messages.error(request, f'创建回款记录失败：{str(e)}')
    
    context = _context(
        "创建回款记录",
        "💰",
        f"回款计划：{plan.phase_name}",
        request=request,
    )
    context.update({
        'plan': plan,
        'plan_type': plan_type,
        'payment_method_choices': PaymentRecord.PAYMENT_METHOD_CHOICES,
    })
    return render(request, "settlement_management/payment_record_form.html", context)


def _format_user_display(user, default='—'):
    """格式化用户显示名称"""
    if not user:
        return default
    if hasattr(user, 'get_full_name') and user.get_full_name():
        return user.get_full_name()
    if hasattr(user, 'name'):
        return user.name
    return user.username if hasattr(user, 'username') else str(user)


@login_required
def settlement_home(request):
    """回款管理首页 - 数据展示中心"""
    permission_codes = get_user_permission_codes(request.user)
    now = timezone.now()
    today = now.date()
    this_month_start = today.replace(day=1)
    seven_days_ago = today - timedelta(days=7)
    
    context = {}
    
    try:
        from backend.apps.production_management.models import BusinessPaymentPlan
        
        # ========== 核心指标卡片 ==========
        core_cards = []
        
        # 回款计划统计
        all_plans = BusinessPaymentPlan.objects.select_related('contract', 'contract__client').all()
        total_plans = all_plans.count()
        pending_plans = all_plans.filter(status='pending').count()
        overdue_plans = all_plans.filter(
            status__in=['pending', 'partial'],
            planned_date__lt=today
        ).count()
        completed_plans = all_plans.filter(status='completed').count()
        
        total_planned_amount = all_plans.aggregate(
            total=Sum('planned_amount')
        )['total'] or Decimal('0')
        total_actual_amount = all_plans.aggregate(
            total=Sum('actual_amount')
        )['total'] or Decimal('0')
        this_month_plans = all_plans.filter(planned_date__gte=this_month_start).count()
        
        # 产值模块已独立，结算首页不再展示产值卡片（产值入口在 /output-value/）

        # 项目结算统计
        all_settlements = ProjectSettlement.objects.select_related('project', 'contract', 'created_by').all()
        total_settlements = all_settlements.count()
        pending_settlements = all_settlements.filter(
            status__in=['submitted', 'client_review', 'client_feedback', 'reconciliation']
        ).count()
        confirmed_settlements = all_settlements.filter(status='confirmed').count()
        this_month_settlements = all_settlements.filter(created_time__gte=this_month_start).count()
        
        total_settlement_amount = all_settlements.filter(status__in=['confirmed', 'reconciliation']).aggregate(
            total=Sum('total_settlement_amount')
        )['total'] or Decimal('0')
        
        # 回款记录统计
        all_payment_records = PaymentRecord.objects.select_related('confirmed_by').all()
        total_payment_records = all_payment_records.count()
        pending_payment_records = all_payment_records.filter(status='pending').count()
        confirmed_payment_records = all_payment_records.filter(status='confirmed').count()
        this_month_payment_records = all_payment_records.filter(payment_date__gte=this_month_start).count()
        
        this_month_payment_amount = all_payment_records.filter(
            payment_date__gte=this_month_start,
            status='confirmed'
        ).aggregate(total=Sum('payment_amount'))['total'] or Decimal('0')
        
        # 卡片1：回款计划
        try:
            plan_url = reverse('payment_pages:payment_plan_list')
        except NoReverseMatch:
            plan_url = '#'
        core_cards.append({
            'label': '回款计划',
            'icon': '💳',
            'value': str(total_plans),
            'subvalue': f'待回款 {pending_plans} | 逾期 {overdue_plans} | 本月 {this_month_plans}',
            'url': plan_url,
            'variant': 'dark' if overdue_plans > 0 else 'secondary'
        })
        
        # 卡片2：计划金额
        core_cards.append({
            'label': '计划金额',
            'icon': '💰',
            'value': f'¥{total_planned_amount:,.0f}',
            'subvalue': f'已回款 ¥{total_actual_amount:,.0f} | 回款率 {int((total_actual_amount / total_planned_amount * 100) if total_planned_amount > 0 else 0)}%',
            'url': plan_url,
            'variant': 'secondary'
        })
        
        # 产值模块已独立至 /output-value/，此处仅展示结算与回款相关卡片

        # 卡片3：项目结算
        try:
            settlement_url = reverse('settlement_pages:project_settlement_list')
        except NoReverseMatch:
            settlement_url = '#'
        core_cards.append({
            'label': '项目结算',
            'icon': '🧾',
            'value': str(total_settlements),
            'subvalue': f'待处理 {pending_settlements} | 已确认 {confirmed_settlements} | 本月 {this_month_settlements}',
            'url': settlement_url,
            'variant': 'dark' if pending_settlements > 0 else 'secondary'
        })
        
        # 卡片4：回款记录
        try:
            payment_record_url = reverse('payment_pages:payment_record_list')
        except NoReverseMatch:
            payment_record_url = '#'
        core_cards.append({
            'label': '回款记录',
            'icon': '💵',
            'value': str(total_payment_records),
            'subvalue': f'待确认 {pending_payment_records} | 本月回款 ¥{this_month_payment_amount:,.0f}',
            'url': payment_record_url,
            'variant': 'dark' if pending_payment_records > 0 else 'secondary'
        })
        
        context['core_cards'] = core_cards
        
        # ========== 风险预警 ==========
        risk_warnings = []
        
        # 逾期回款计划
        overdue_plan_list = all_plans.filter(
            status__in=['pending', 'partial'],
            planned_date__lt=today
        ).select_related('contract', 'contract__client')[:5]
        
        for plan in overdue_plan_list:
            days_overdue = (today - plan.planned_date).days
            client_name = plan.contract.client.name if plan.contract and plan.contract.client else '未知'
            risk_warnings.append({
                'type': 'plan',
                'title': f'{plan.phase_name} - {client_name}',
                'responsible': client_name,
                'days': days_overdue,
                'url': reverse('payment_pages:payment_plan_detail', args=['business', plan.id])
            })
        
        # 产值模块已独立，不再在结算首页展示产值相关预警

        context['risk_warnings'] = risk_warnings[:5]
        context['overdue_plans_count'] = overdue_plan_list.count()
        context['stale_output_records_count'] = 0
        
        # ========== 待办事项 ==========
        todo_items = []
        
        # 待确认回款记录
        pending_payment_list = all_payment_records.filter(status='pending').select_related('confirmed_by')[:5]
        for payment in pending_payment_list:
            todo_items.append({
                'type': 'payment',
                'title': f'回款单号：{payment.payment_number}',
                'payment_number': payment.payment_number,
                'responsible': '待确认',
                'url': payment_record_url
            })
        
        # 待处理项目结算
        pending_settlement_list = all_settlements.filter(
            status__in=['submitted', 'client_review', 'client_feedback']
        ).select_related('created_by', 'project')[:5]
        for settlement in pending_settlement_list:
            creator_name = _format_user_display(settlement.created_by) if settlement.created_by else '未知'
            project_name = settlement.project.project_number if settlement.project else '未知'
            todo_items.append({
                'type': 'settlement',
                'title': f'{project_name} - {settlement.settlement_number}',
                'settlement_number': settlement.settlement_number,
                'responsible': creator_name,
                'url': reverse('settlement_pages:project_settlement_detail', args=[settlement.id])
            })
        
        context['todo_items'] = todo_items[:10]
        context['pending_approval_count'] = pending_payment_records + pending_settlements
        context['todo_summary_url'] = payment_record_url + '?status=pending'
        
        # ========== 我的工作 ==========
        my_work = {}
        
        # 产值模块已独立，产值记录入口在 /output-value/
        my_work['my_output_records'] = []
        my_work['my_output_records_count'] = 0

        # 我创建的项目结算
        my_settlements = all_settlements.filter(created_by=request.user).order_by('-created_time')[:3]
        my_work['my_settlements'] = [{
            'title': f'{settlement.project.project_number if settlement.project else "未知"} - {settlement.settlement_number}',
            'status': settlement.get_status_display(),
            'url': reverse('settlement_pages:project_settlement_detail', args=[settlement.id])
        } for settlement in my_settlements]
        my_work['my_settlements_count'] = all_settlements.filter(created_by=request.user).count()
        
        my_work['summary_url'] = plan_url
        
        context['my_work'] = my_work
        
        # ========== 最近活动 ==========
        recent_activities = {}
        
        # 最近创建的回款计划
        recent_plans = all_plans.select_related('contract', 'contract__client').order_by('-created_time')[:5]
        recent_activities['recent_plans'] = [{
            'title': plan.phase_name,
            'creator': plan.contract.client.name if plan.contract and plan.contract.client else '未知',
            'time': plan.planned_date,
            'url': reverse('payment_pages:payment_plan_detail', args=['business', plan.id])
        } for plan in recent_plans]
        
        # 最近创建的回款记录
        recent_payments = all_payment_records.select_related('confirmed_by').order_by('-payment_date')[:5]
        recent_activities['recent_payments'] = [{
            'title': payment.payment_number,
            'creator': _format_user_display(payment.confirmed_by) if payment.confirmed_by else '系统',
            'time': payment.payment_date,
            'url': payment_record_url
        } for payment in recent_payments]
        
        context['recent_activities'] = recent_activities
        
    except Exception as e:
        import logging
        logger = logging.getLogger(__name__)
        logger.exception('获取回款管理统计数据失败: %s', str(e))
        context.setdefault('core_cards', [])
        context.setdefault('risk_warnings', [])
        context.setdefault('todo_items', [])
        context.setdefault('my_work', {})
        context.setdefault('recent_activities', {})
    
    # 顶部操作栏
    top_actions = []
    if _permission_granted('payment_management.payment_plan.view', permission_codes):
        try:
            top_actions.append({
                'label': '查看回款计划',
                'url': reverse('payment_pages:payment_plan_list'),
                'icon': '💳'
            })
        except Exception:
            pass
    
    context['top_actions'] = top_actions
    
    # 构建上下文
    page_context = _context(
        "回款管理",
        "💰",
        "数据展示中心 - 集中展示回款关键指标、状态与风险",
        request=request
    )
    
    # 设置侧边栏导航
    settlement_sidebar_nav = _build_settlement_sidebar_nav(permission_codes, request.path, active_id='settlement_home')
    page_context['settlement_menu'] = settlement_sidebar_nav
    page_context['settlement_sidebar_nav'] = settlement_sidebar_nav
    page_context['sidebar_title'] = '回款管理'
    page_context['sidebar_subtitle'] = 'Settlement Management'
    
    # 为所有可能的侧边栏变量设置默认值，避免模板错误
    page_context.setdefault('plan_menu', [])
    page_context.setdefault('sidebar_nav', [])
    page_context.setdefault('customer_menu', [])
    page_context.setdefault('sidebar_nav', [])
    page_context.setdefault('sidebar_nav', [])
    page_context.setdefault('sidebar_nav', [])
    page_context.setdefault('sidebar_nav', [])
    page_context.setdefault('sidebar_nav', [])
    page_context.setdefault('sidebar_nav', [])
    page_context.setdefault('sidebar_nav', [])
    page_context.setdefault('administrative_sidebar_nav', [])
    
    # 合并所有数据
    page_context.update(context)
    
    return render(request, "settlement_management/settlement_management_home.html", page_context)


@login_required
def settlement_management_home(request):
    """结算管理首页 - 数据展示中心（只包含结算相关功能）"""
    permission_set = get_user_permission_codes(request.user)
    if not _permission_granted('settlement_management.view', permission_set):
        from django.http import HttpResponseForbidden
        return HttpResponseForbidden("无权限访问结算管理")

    now = timezone.now()
    today = now.date()
    this_month_start = today.replace(day=1)

    context = {}

    try:
        # ========== 核心指标卡片 ==========
        core_cards = []

        # 项目结算统计
        all_settlements = ProjectSettlement.objects.select_related('project', 'contract', 'created_by').all()
        total_settlements = all_settlements.count()
        draft_settlements = all_settlements.filter(status='draft').count()
        pending_settlements = all_settlements.filter(
            status__in=['submitted', 'client_review', 'client_feedback', 'reconciliation']
        ).count()
        confirmed_settlements = all_settlements.filter(status='confirmed').count()
        this_month_settlements = all_settlements.filter(created_time__gte=this_month_start).count()

        total_settlement_amount = all_settlements.filter(status__in=['confirmed', 'reconciliation']).aggregate(
            total=Sum('total_settlement_amount')
        )['total'] or Decimal('0')

        # 卡片1：项目结算总数
        try:
            settlement_url = reverse('settlement_pages:project_settlement_list')
        except NoReverseMatch:
            settlement_url = '#'
        core_cards.append({
            'label': '项目结算',
            'icon': '🧾',
            'value': str(total_settlements),
            'subvalue': f'草稿 {draft_settlements} | 待处理 {pending_settlements} | 已确认 {confirmed_settlements}',
            'url': settlement_url,
            'variant': 'dark' if pending_settlements > 0 else 'secondary'
        })

        # 卡片2：结算总金额
        core_cards.append({
            'label': '结算总金额',
            'icon': '💰',
            'value': f'¥{total_settlement_amount:,.2f}',
            'subvalue': f'已确认结算金额',
            'url': settlement_url,
            'variant': 'secondary'
        })

        # 卡片3：待处理结算
        core_cards.append({
            'label': '待处理结算',
            'icon': '⏳',
            'value': str(pending_settlements),
            'subvalue': f'需要处理',
            'url': settlement_url + '?status=submitted',
            'variant': 'dark' if pending_settlements > 0 else 'secondary'
        })

        # 卡片4：本月新增
        core_cards.append({
            'label': '本月新增',
            'icon': '📈',
            'value': str(this_month_settlements),
            'subvalue': f'新结算单 {this_month_settlements} 个',
            'url': settlement_url,
            'variant': 'secondary'
        })

        context['core_cards'] = core_cards

        # ========== 待办事项 ==========
        todo_items = []

        # 待处理项目结算
        pending_settlement_list = all_settlements.filter(
            status__in=['submitted', 'client_review', 'client_feedback']
        ).select_related('created_by', 'project')[:5]
        for settlement in pending_settlement_list:
            creator_name = _format_user_display(settlement.created_by) if settlement.created_by else '未知'
            project_name = settlement.project.project_number if settlement.project else '未知'
            todo_items.append({
                'type': 'settlement',
                'title': f'{project_name} - {settlement.settlement_number}',
                'settlement_number': settlement.settlement_number,
                'responsible': creator_name,
                'url': reverse('settlement_pages:project_settlement_detail', args=[settlement.id])
            })

        context['todo_items'] = todo_items[:10]
        context['pending_settlement_count'] = pending_settlements
        context['todo_summary_url'] = settlement_url + '?status=submitted'

        # ========== 我的工作 ==========
        my_work = {}

        # 我创建的项目结算
        my_settlements = all_settlements.filter(created_by=request.user).order_by('-created_time')[:3]
        my_work['my_settlements'] = [{
            'title': f'{settlement.project.project_number if settlement.project else "未知"} - {settlement.settlement_number}',
            'status': settlement.get_status_display(),
            'value': f'¥{settlement.total_settlement_amount:,.2f}',
            'url': reverse('settlement_pages:project_settlement_detail', args=[settlement.id])
        } for settlement in my_settlements]
        my_work['my_settlements_count'] = all_settlements.filter(created_by=request.user).count()
        my_work['my_total_settlement'] = all_settlements.filter(created_by=request.user).aggregate(
            total=Sum('total_settlement_amount')
        )['total'] or Decimal('0')

        my_work['summary_url'] = settlement_url + f'?created_by={request.user.id}'

        context['my_work'] = my_work

        # ========== 最近活动 ==========
        recent_activities = {}

        # 最近创建的项目结算
        recent_settlements = all_settlements.select_related('created_by', 'project').order_by('-created_time')[:5]
        recent_activities['recent_settlements'] = [{
            'title': f'{settlement.project.project_number if settlement.project else "未知"} - {settlement.settlement_number}',
            'creator': settlement.created_by.get_full_name() or settlement.created_by.username if settlement.created_by else '系统',
            'value': f'¥{settlement.total_settlement_amount:,.2f}',
            'time': settlement.created_time,
            'url': reverse('settlement_pages:project_settlement_detail', args=[settlement.id])
        } for settlement in recent_settlements]

        # 最近确认的项目结算
        recent_confirmed = all_settlements.filter(status='confirmed').select_related('confirmed_by', 'project').order_by('-confirmed_time')[:5]
        recent_activities['recent_confirmed'] = [{
            'title': f'{settlement.project.project_number if settlement.project else "未知"} - {settlement.settlement_number}',
            'confirmer': settlement.confirmed_by.get_full_name() or settlement.confirmed_by.username if settlement.confirmed_by else '系统',
            'value': f'¥{settlement.total_settlement_amount:,.2f}',
            'time': settlement.confirmed_time,
            'url': reverse('settlement_pages:project_settlement_detail', args=[settlement.id])
        } for settlement in recent_confirmed]

        context['recent_activities'] = recent_activities

    except Exception as e:
        import logging
        logger = logging.getLogger(__name__)
        logger.exception('获取结算管理统计数据失败: %s', str(e))
        context.setdefault('core_cards', [])
        context.setdefault('todo_items', [])
        context.setdefault('my_work', {})
        context.setdefault('recent_activities', {})

    # 顶部操作栏
    top_actions = []
    if _permission_granted('settlement_management.view', permission_set):
        try:
            top_actions.append({
                'label': '创建项目结算',
                'url': reverse('settlement_pages:project_settlement_create'),
                'icon': '➕'
            })
        except Exception:
            pass

    context['top_actions'] = top_actions

    # 构建上下文
    page_context = _context(
        "结算管理",
        "💼",
        "数据展示中心 - 集中展示结算关键指标、状态与统计",
        request=request,
    )

    # 设置侧边栏导航
    settlement_sidebar_nav = _build_settlement_sidebar_nav(permission_set, request.path, active_id='settlement_management_home')
    page_context['sidebar_nav'] = settlement_sidebar_nav
    page_context['module_sidebar_nav'] = settlement_sidebar_nav
    page_context['sidebar_title'] = '结算管理'
    page_context['sidebar_subtitle'] = 'Settlement Management'

    # 合并所有数据
    page_context.update(context)

    return render(request, "settlement_management/settlement_management_home.html", page_context)