# 回款管理视图
# 从settlement_center迁移而来

from django.contrib.auth.decorators import login_required
from django.shortcuts import render, get_object_or_404, redirect
from django.contrib import messages
from django.core.exceptions import PermissionDenied
from django.db.models import Q, Sum, Count, F, Avg
from django.utils import timezone
from decimal import Decimal
from datetime import timedelta, datetime

from backend.apps.settlement_center.models import (
    OutputValueStage, OutputValueMilestone, OutputValueEvent, OutputValueRecord,
)
from backend.apps.settlement_management.models import (
    ProjectSettlement, SettlementItem, ServiceFeeRate, ContractSettlement
)
# from backend.apps.production_quality.models import Opinion  # 已删除生产质量模块
# from .forms import ProjectSettlementForm, ContractSettlementForm  # 表单将在迁移后添加
# from .services import get_project_output_value_for_settlement, get_project_output_value_summary  # 服务将在迁移后添加
from backend.apps.production_management.models import Project
from backend.apps.system_management.models import User
from backend.apps.system_management.services import get_user_permission_codes
from backend.core.views import _permission_granted, _build_full_top_nav
from backend.apps.contract_management.models import BusinessContract
from django.urls import reverse, NoReverseMatch
from django.core.paginator import Paginator
from django.db.models import Max



# 回款管理模型
from backend.apps.payment_management.models import PaymentRecord

# ==================== 回款管理模块左侧菜单结构 =====================
PAYMENT_MENU = [
    {
        'id': 'payment_home',
        'label': '回款管理',
        'icon': '💰',
        'url_name': 'payment_pages:payment_home',
        'permission': None,
        'children': [
            {
                'id': 'payment_home',
                'label': '首页',
                'icon': '👥',
                'url_name': 'payment_pages:payment_home',
                'permission': None,
            },
        ]
    },
    {
        'id': 'payment_plan',
        'label': '回款计划',
        'icon': '💳',
        'url_name': 'payment_pages:payment_plan_list',
        'permission': 'payment_management.payment_plan.view',
    },
    {
        'id': 'payment_record',
        'label': '回款记录',
        'icon': '📝',
        'url_name': 'payment_pages:payment_record_list',
        'permission': 'payment_management.payment_record.view',
    },
]

def _build_payment_sidebar_nav(permission_set, request_path=None, active_id=None):
    """生成回款管理左侧菜单（统一格式）"""
    try:
        from backend.core.views import _build_unified_sidebar_nav
        return _build_unified_sidebar_nav(PAYMENT_MENU, permission_set, active_id=active_id)
    except ImportError:
        # Fallback实现
        from backend.core.views import _permission_granted
        nav = []
        for item in PAYMENT_MENU:
            if item.get('permission'):
                if not _permission_granted(item['permission'], permission_set):
                    continue
            nav.append(item)
        return nav

# ==================== 回款管理视图函数 =====================

def payment_plan_list(request):
    """回款计划列表页面"""
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
    return render(request, "settlement_center/payment_plan_list.html", context)


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
        return redirect('payment_pages:payment_plan_list')
    elif plan_type == 'business':
        plan = get_object_or_404(BusinessPaymentPlan, id=plan_id)
        related_obj = plan.contract
    else:
        messages.error(request, '无效的回款计划类型')
        return redirect('payment_pages:payment_plan_list')
    
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
    return render(request, "settlement_center/payment_plan_detail.html", context)


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
    return render(request, "settlement_center/payment_record_list.html", context)


@login_required


def payment_record_create(request, plan_type, plan_id):
    """创建回款记录"""
    permission_codes = get_user_permission_codes(request.user)
    
    if not _permission_granted('payment_management.payment_record.create', permission_codes):
        messages.error(request, '您没有权限创建回款记录')
        return redirect('payment_pages:payment_plan_list')
    
    # 获取回款计划
    if plan_type == 'project':
        # 项目回款计划已不存在，返回错误
        messages.error(request, '项目回款计划功能已移除，请使用商务回款计划')
        return redirect('payment_pages:payment_plan_list')
    elif plan_type == 'business':
        from backend.apps.production_management.models import BusinessPaymentPlan
        plan = get_object_or_404(BusinessPaymentPlan, id=plan_id)
    else:
        messages.error(request, '无效的回款计划类型')
        return redirect('payment_pages:payment_plan_list')
    
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
                return redirect('payment_pages:payment_plan_detail', plan_type=plan_type, plan_id=plan_id)
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
    return render(request, "settlement_center/payment_record_form.html", context)




def payment_home(request):
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
        
        # 产值记录统计
        all_output_records = OutputValueRecord.objects.select_related('project', 'responsible_user').all()
        total_output_records = all_output_records.count()
        pending_output_records = all_output_records.filter(status='pending').count()
        confirmed_output_records = all_output_records.filter(status='confirmed').count()
        this_month_output_records = all_output_records.filter(calculated_time__gte=this_month_start).count()
        
        total_output_value = all_output_records.aggregate(
            total=Sum('calculated_value')
        )['total'] or Decimal('0')
        
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
        
        # 卡片3：产值记录
        try:
            output_url = reverse('payment_pages:output_value_record_list')
        except NoReverseMatch:
            output_url = '#'
        core_cards.append({
            'label': '产值记录',
            'icon': '📊',
            'value': str(total_output_records),
            'subvalue': f'待确认 {pending_output_records} | 已确认 {confirmed_output_records} | 本月 {this_month_output_records}',
            'url': output_url,
            'variant': 'dark' if pending_output_records > 0 else 'secondary'
        })
        
        # 卡片4：产值总额
        core_cards.append({
            'label': '产值总额',
            'icon': '📈',
            'value': f'¥{total_output_value:,.0f}',
            'subvalue': f'已确认产值',
            'url': output_url,
            'variant': 'secondary'
        })
        
        # 卡片5：项目结算
        try:
            settlement_url = reverse('payment_pages:project_settlement_list')
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
        
        # 卡片6：回款记录
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
        
        # 待确认产值记录（超过7天）
        stale_output_records = all_output_records.filter(
            status='pending',
            calculated_time__lt=seven_days_ago
        ).select_related('responsible_user', 'project')[:5]
        
        for record in stale_output_records:
            days_since_create = (today - record.calculated_time.date()).days
            responsible_name = _format_user_display(record.responsible_user) if record.responsible_user else '未知'
            project_name = record.project.project_number if record.project else '未知'
            risk_warnings.append({
                'type': 'output',
                'title': f'{project_name} - 产值记录待确认',
                'responsible': responsible_name,
                'days': days_since_create,
                'url': output_url
            })
        
        context['risk_warnings'] = risk_warnings[:5]
        context['overdue_plans_count'] = overdue_plan_list.count()
        context['stale_output_records_count'] = stale_output_records.count()
        
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
                'url': reverse('payment_pages:project_settlement_detail', args=[settlement.id])
            })
        
        context['todo_items'] = todo_items[:10]
        context['pending_approval_count'] = pending_payment_records + pending_settlements
        context['todo_summary_url'] = payment_record_url + '?status=pending'
        
        # ========== 我的工作 ==========
        my_work = {}
        
        # 我创建的产值记录
        my_output_records = all_output_records.filter(responsible_user=request.user).order_by('-calculated_time')[:3]
        my_work['my_output_records'] = [{
            'title': f'{record.project.project_number if record.project else "未知"} - {record.record_number}',
            'status': record.get_status_display(),
            'url': output_url
        } for record in my_output_records]
        my_work['my_output_records_count'] = all_output_records.filter(responsible_user=request.user).count()
        
        # 我创建的项目结算
        my_settlements = all_settlements.filter(created_by=request.user).order_by('-created_time')[:3]
        my_work['my_settlements'] = [{
            'title': f'{settlement.project.project_number if settlement.project else "未知"} - {settlement.settlement_number}',
            'status': settlement.get_status_display(),
            'url': reverse('payment_pages:project_settlement_detail', args=[settlement.id])
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
    settlement_sidebar_nav = _build_payment_sidebar_nav(permission_codes, request.path, active_id='settlement_home')
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

