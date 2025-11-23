from django.contrib.auth.decorators import login_required
from django.shortcuts import render, get_object_or_404, redirect
from django.contrib import messages
from django.db.models import Count, Sum, Q, F, Max
from django.core.paginator import Paginator
from django.urls import reverse, NoReverseMatch
from django.utils import timezone
from django.forms import inlineformset_factory
from datetime import timedelta
from decimal import Decimal

from backend.apps.system_management.services import get_user_permission_codes
from .models import (
    AccountSubject, Voucher, VoucherEntry,
    Ledger, Budget, Invoice, FundFlow,
)
from .forms import (
    AccountSubjectForm, VoucherForm, VoucherEntryForm, BudgetForm, InvoiceForm, FundFlowForm
)


def _permission_granted(required_code, user_permissions: set) -> bool:
    """检查权限"""
    if not required_code:
        return True
    if '__all__' in user_permissions:
        return True
    return required_code in user_permissions


def _context(page_title, page_icon, description, summary_cards=None, request=None, use_financial_nav=False):
    """构建页面上下文"""
    context = {
        "page_title": page_title,
        "page_icon": page_icon,
        "description": description,
        "summary_cards": summary_cards or [],
    }
    
    if request and request.user.is_authenticated:
        permission_set = get_user_permission_codes(request.user)
        if use_financial_nav:
            context['full_top_nav'] = _build_financial_top_nav(permission_set)
        else:
            context['full_top_nav'] = []
    else:
        context['full_top_nav'] = []
    
    return context


def _build_financial_top_nav(permission_set):
    """生成财务管理专用的顶部导航菜单 - 6个子功能横向排列"""
    # 定义财务管理功能模块（从左到右的顺序）
    financial_modules = [
        {
            'label': '会计科目',
            'url_name': 'finance_pages:account_subject_management',
            'permission': 'financial_management.account.view',
            'icon': '📊',
        },
        {
            'label': '凭证管理',
            'url_name': 'finance_pages:voucher_management',
            'permission': 'financial_management.voucher.view',
            'icon': '📝',
        },
        {
            'label': '账簿管理',
            'url_name': 'finance_pages:ledger_management',
            'permission': 'financial_management.ledger.view',
            'icon': '📖',
        },
        {
            'label': '预算管理',
            'url_name': 'finance_pages:budget_management',
            'permission': 'financial_management.budget.view',
            'icon': '💰',
        },
        {
            'label': '发票管理',
            'url_name': 'finance_pages:invoice_management',
            'permission': 'financial_management.invoice.view',
            'icon': '🧾',
        },
        {
            'label': '资金流水',
            'url_name': 'finance_pages:fund_flow_management',
            'permission': 'financial_management.fund_flow.view',
            'icon': '💳',
        },
    ]
    
    # 过滤有权限的模块
    nav_items = []
    for module in financial_modules:
        if _permission_granted(module['permission'], permission_set):
            try:
                url = reverse(module['url_name'])
            except NoReverseMatch:
                url = '#'
            nav_items.append({
                'label': module['label'],
                'url': url,
                'icon': module.get('icon', ''),
            })
    
    return nav_items


@login_required
def financial_home(request):
    """财务管理主页"""
    permission_codes = get_user_permission_codes(request.user)
    today = timezone.now().date()
    this_month_start = today.replace(day=1)
    
    # 收集统计数据
    stats_cards = []
    
    try:
        # 会计科目统计
        if _permission_granted('financial_management.account.view', permission_codes):
            try:
                total_accounts = AccountSubject.objects.filter(is_active=True).count()
                accounts_by_type = AccountSubject.objects.filter(is_active=True).values('subject_type').annotate(count=Count('id'))
                
                stats_cards.append({
                    'label': '会计科目',
                    'icon': '📊',
                    'value': f'{total_accounts}',
                    'subvalue': f'启用科目',
                    'url': reverse('finance_pages:account_subject_management'),
                })
            except Exception:
                pass
        
        # 凭证管理统计
        if _permission_granted('financial_management.voucher.view', permission_codes):
            try:
                pending_vouchers = Voucher.objects.filter(status='submitted').count()
                this_month_vouchers = Voucher.objects.filter(voucher_date__gte=this_month_start).count()
                
                stats_cards.append({
                    'label': '凭证管理',
                    'icon': '📝',
                    'value': f'{pending_vouchers}',
                    'subvalue': f'待审核 · 本月 {this_month_vouchers} 张',
                    'url': reverse('finance_pages:voucher_management'),
                })
            except Exception:
                pass
        
        # 账簿管理统计
        if _permission_granted('financial_management.ledger.view', permission_codes):
            try:
                current_year = today.year
                current_month = today.month
                ledger_entries = Ledger.objects.filter(
                    period_year=current_year,
                    period_month=current_month
                ).count()
                
                stats_cards.append({
                    'label': '账簿管理',
                    'icon': '📖',
                    'value': f'{ledger_entries}',
                    'subvalue': f'本月账务记录',
                    'url': reverse('finance_pages:ledger_management'),
                })
            except Exception:
                pass
        
        # 预算管理统计
        if _permission_granted('financial_management.budget.view', permission_codes):
            try:
                executing_budgets = Budget.objects.filter(status='executing').count()
                total_budget = Budget.objects.filter(status='executing').aggregate(
                    total=Sum('budget_amount')
                )['total'] or Decimal('0')
                
                stats_cards.append({
                    'label': '预算管理',
                    'icon': '💰',
                    'value': f'{executing_budgets}',
                    'subvalue': f'执行中预算',
                    'extra': f'总额 ¥{total_budget:,.2f}',
                    'url': reverse('finance_pages:budget_management'),
                })
            except Exception:
                pass
        
        # 发票管理统计
        if _permission_granted('financial_management.invoice.view', permission_codes):
            try:
                unverified_invoices = Invoice.objects.filter(status='issued').count()
                this_month_invoices = Invoice.objects.filter(invoice_date__gte=this_month_start).count()
                
                stats_cards.append({
                    'label': '发票管理',
                    'icon': '🧾',
                    'value': f'{unverified_invoices}',
                    'subvalue': f'待认证 · 本月 {this_month_invoices} 张',
                    'url': reverse('finance_pages:invoice_management'),
                })
            except Exception:
                pass
        
        # 资金流水统计
        if _permission_granted('financial_management.fund_flow.view', permission_codes):
            try:
                this_month_flows = FundFlow.objects.filter(flow_date__gte=this_month_start).count()
                this_month_income = FundFlow.objects.filter(
                    flow_date__gte=this_month_start,
                    flow_type='income'
                ).aggregate(total=Sum('amount'))['total'] or Decimal('0')
                
                stats_cards.append({
                    'label': '资金流水',
                    'icon': '💳',
                    'value': f'{this_month_flows}',
                    'subvalue': f'本月流水',
                    'extra': f'收入 ¥{this_month_income:,.2f}',
                    'url': reverse('finance_pages:fund_flow_management'),
                })
            except Exception:
                pass
        
    except Exception as e:
        import logging
        logger = logging.getLogger(__name__)
        logger.exception('获取统计数据失败: %s', str(e))
    
    context = _context(
        "财务管理",
        "💵",
        "企业财务管理平台",
        summary_cards=stats_cards,
        request=request,
        use_financial_nav=True
    )
    return render(request, "financial_management/home.html", context)


@login_required
def account_subject_management(request):
    """会计科目管理"""
    permission_codes = get_user_permission_codes(request.user)
    
    # 获取筛选参数
    search = request.GET.get('search', '')
    subject_type = request.GET.get('subject_type', '')
    is_active = request.GET.get('is_active', '')
    
    # 获取科目列表
    try:
        subjects = AccountSubject.objects.select_related('parent', 'created_by').order_by('code')
        
        # 应用筛选条件
        if search:
            subjects = subjects.filter(
                Q(code__icontains=search) |
                Q(name__icontains=search) |
                Q(description__icontains=search)
            )
        if subject_type:
            subjects = subjects.filter(subject_type=subject_type)
        if is_active == 'true':
            subjects = subjects.filter(is_active=True)
        elif is_active == 'false':
            subjects = subjects.filter(is_active=False)
        
        # 分页
        paginator = Paginator(subjects, 50)
        page_number = request.GET.get('page', 1)
        page_obj = paginator.get_page(page_number)
    except Exception as e:
        import logging
        logger = logging.getLogger(__name__)
        logger.exception('获取会计科目列表失败: %s', str(e))
        page_obj = None
    
    # 统计信息
    try:
        total_subjects = AccountSubject.objects.count()
        active_subjects = AccountSubject.objects.filter(is_active=True).count()
        subjects_by_type = AccountSubject.objects.filter(is_active=True).values('subject_type').annotate(count=Count('id'))
        
        summary_cards = [
            {"label": "科目总数", "value": total_subjects, "hint": "系统中维护的会计科目总数"},
            {"label": "启用科目", "value": active_subjects, "hint": "状态为启用的科目数量"},
        ]
    except Exception as e:
        import logging
        logger = logging.getLogger(__name__)
        logger.exception('获取统计信息失败: %s', str(e))
        summary_cards = []
    
    context = _context(
        "会计科目管理",
        "📊",
        "管理会计科目信息",
        summary_cards=summary_cards,
        request=request,
        use_financial_nav=True
    )
    context.update({
        'page_obj': page_obj,
        'subjects': page_obj.object_list if page_obj else [],
        'subject_type_choices': AccountSubject.TYPE_CHOICES,
        'current_search': search,
        'current_subject_type': subject_type,
        'current_is_active': is_active,
    })
    return render(request, "financial_management/account_subject_list.html", context)


@login_required
def account_subject_create(request):
    """新增会计科目"""
    permission_codes = get_user_permission_codes(request.user)
    if not _permission_granted('financial_management.account.manage', permission_codes):
        messages.error(request, '您没有权限新增会计科目')
        return redirect('finance_pages:account_subject_management')
    
    if request.method == 'POST':
        form = AccountSubjectForm(request.POST)
        if form.is_valid():
            account_subject = form.save(commit=False)
            account_subject.created_by = request.user
            # 如果选择了上级科目，自动计算级别
            if account_subject.parent:
                account_subject.level = account_subject.parent.level + 1
            account_subject.save()
            messages.success(request, f'会计科目 {account_subject.name} 创建成功！')
            return redirect('finance_pages:account_subject_detail', account_subject_id=account_subject.id)
    else:
        form = AccountSubjectForm()
    
    context = _context(
        "新增会计科目",
        "➕",
        "创建新的会计科目",
        request=request,
        use_financial_nav=True
    )
    context.update({
        'form': form,
        'is_create': True,
    })
    return render(request, "financial_management/account_subject_form.html", context)


@login_required
def account_subject_update(request, account_subject_id):
    """编辑会计科目"""
    permission_codes = get_user_permission_codes(request.user)
    if not _permission_granted('financial_management.account.manage', permission_codes):
        messages.error(request, '您没有权限编辑会计科目')
        return redirect('finance_pages:account_subject_detail', account_subject_id=account_subject_id)
    
    account_subject = get_object_or_404(AccountSubject, id=account_subject_id)
    
    if request.method == 'POST':
        form = AccountSubjectForm(request.POST, instance=account_subject)
        if form.is_valid():
            account_subject = form.save(commit=False)
            # 如果选择了上级科目，自动计算级别
            if account_subject.parent:
                account_subject.level = account_subject.parent.level + 1
            account_subject.save()
            messages.success(request, f'会计科目 {account_subject.name} 更新成功！')
            return redirect('finance_pages:account_subject_detail', account_subject_id=account_subject.id)
    else:
        form = AccountSubjectForm(instance=account_subject)
    
    context = _context(
        f"编辑会计科目 - {account_subject.name}",
        "✏️",
        f"编辑会计科目 {account_subject.name}",
        request=request,
        use_financial_nav=True
    )
    context.update({
        'form': form,
        'account_subject': account_subject,
        'is_create': False,
    })
    return render(request, "financial_management/account_subject_form.html", context)


@login_required
def budget_create(request):
    """新增预算"""
    permission_codes = get_user_permission_codes(request.user)
    if not _permission_granted('financial_management.budget.create', permission_codes):
        messages.error(request, '您没有权限创建预算')
        return redirect('finance_pages:budget_management')
    
    if request.method == 'POST':
        form = BudgetForm(request.POST)
        if form.is_valid():
            budget = form.save(commit=False)
            # 自动生成预算编号
            if not budget.budget_number:
                current_year = timezone.now().year
                max_budget = Budget.objects.filter(
                    budget_number__startswith=f'BUDGET-{current_year}-'
                ).aggregate(max_num=Max('budget_number'))['max_num']
                if max_budget:
                    try:
                        seq = int(max_budget.split('-')[-1]) + 1
                    except (ValueError, IndexError):
                        seq = 1
                else:
                    seq = 1
                budget.budget_number = f'BUDGET-{current_year}-{seq:04d}'
            budget.remaining_amount = budget.budget_amount
            budget.created_by = request.user
            budget.save()
            messages.success(request, f'预算 {budget.name} 创建成功！')
            return redirect('finance_pages:budget_detail', budget_id=budget.id)
    else:
        form = BudgetForm()
    
    context = _context(
        "新增预算",
        "➕",
        "创建新的预算记录",
        request=request,
        use_financial_nav=True
    )
    context.update({
        'form': form,
        'is_create': True,
    })
    return render(request, "financial_management/budget_form.html", context)


@login_required
def budget_update(request, budget_id):
    """编辑预算"""
    permission_codes = get_user_permission_codes(request.user)
    if not _permission_granted('financial_management.budget.manage', permission_codes):
        messages.error(request, '您没有权限编辑预算')
        return redirect('finance_pages:budget_detail', budget_id=budget_id)
    
    budget = get_object_or_404(Budget, id=budget_id)
    
    if request.method == 'POST':
        form = BudgetForm(request.POST, instance=budget)
        if form.is_valid():
            budget = form.save(commit=False)
            # 重新计算剩余金额
            budget.remaining_amount = budget.budget_amount - budget.used_amount
            budget.save()
            messages.success(request, f'预算 {budget.name} 更新成功！')
            return redirect('finance_pages:budget_detail', budget_id=budget.id)
    else:
        form = BudgetForm(instance=budget)
    
    context = _context(
        f"编辑预算 - {budget.name}",
        "✏️",
        f"编辑预算 {budget.name}",
        request=request,
        use_financial_nav=True
    )
    context.update({
        'form': form,
        'budget': budget,
        'is_create': False,
    })
    return render(request, "financial_management/budget_form.html", context)


@login_required
def invoice_create(request):
    """新增发票"""
    permission_codes = get_user_permission_codes(request.user)
    if not _permission_granted('financial_management.invoice.create', permission_codes):
        messages.error(request, '您没有权限创建发票')
        return redirect('finance_pages:invoice_management')
    
    if request.method == 'POST':
        form = InvoiceForm(request.POST, request.FILES)
        if form.is_valid():
            invoice = form.save(commit=False)
            # 如果没有填写总金额，自动计算
            if not invoice.total_amount and invoice.amount and invoice.tax_amount:
                invoice.total_amount = invoice.amount + invoice.tax_amount
            elif not invoice.total_amount:
                invoice.total_amount = invoice.amount or Decimal('0.00')
            invoice.created_by = request.user
            invoice.save()
            messages.success(request, f'发票 {invoice.invoice_number} 创建成功！')
            return redirect('finance_pages:invoice_detail', invoice_id=invoice.id)
    else:
        form = InvoiceForm()
        # 默认当前日期
        form.fields['invoice_date'].initial = timezone.now().date()
    
    context = _context(
        "新增发票",
        "➕",
        "创建新的发票记录",
        request=request,
        use_financial_nav=True
    )
    context.update({
        'form': form,
        'is_create': True,
    })
    return render(request, "financial_management/invoice_form.html", context)


@login_required
def invoice_update(request, invoice_id):
    """编辑发票"""
    permission_codes = get_user_permission_codes(request.user)
    if not _permission_granted('financial_management.invoice.manage', permission_codes):
        messages.error(request, '您没有权限编辑发票')
        return redirect('finance_pages:invoice_detail', invoice_id=invoice_id)
    
    invoice = get_object_or_404(Invoice, id=invoice_id)
    
    if request.method == 'POST':
        form = InvoiceForm(request.POST, request.FILES, instance=invoice)
        if form.is_valid():
            invoice = form.save(commit=False)
            # 重新计算总金额
            if invoice.amount and invoice.tax_amount:
                invoice.total_amount = invoice.amount + invoice.tax_amount
            invoice.save()
            messages.success(request, f'发票 {invoice.invoice_number} 更新成功！')
            return redirect('finance_pages:invoice_detail', invoice_id=invoice.id)
    else:
        form = InvoiceForm(instance=invoice)
    
    context = _context(
        f"编辑发票 - {invoice.invoice_number}",
        "✏️",
        f"编辑发票 {invoice.invoice_number}",
        request=request,
        use_financial_nav=True
    )
    context.update({
        'form': form,
        'invoice': invoice,
        'is_create': False,
    })
    return render(request, "financial_management/invoice_form.html", context)


@login_required
def fund_flow_create(request):
    """新增资金流水"""
    permission_codes = get_user_permission_codes(request.user)
    if not _permission_granted('financial_management.fund_flow.create', permission_codes):
        messages.error(request, '您没有权限创建资金流水')
        return redirect('finance_pages:fund_flow_management')
    
    if request.method == 'POST':
        form = FundFlowForm(request.POST)
        if form.is_valid():
            fund_flow = form.save(commit=False)
            # 自动生成流水号
            if not fund_flow.flow_number:
                current_year = timezone.now().year
                max_flow = FundFlow.objects.filter(
                    flow_number__startswith=f'FLOW-{current_year}-'
                ).aggregate(max_num=Max('flow_number'))['max_num']
                if max_flow:
                    try:
                        seq = int(max_flow.split('-')[-1]) + 1
                    except (ValueError, IndexError):
                        seq = 1
                else:
                    seq = 1
                fund_flow.flow_number = f'FLOW-{current_year}-{seq:04d}'
            fund_flow.created_by = request.user
            fund_flow.save()
            messages.success(request, f'资金流水 {fund_flow.flow_number} 创建成功！')
            return redirect('finance_pages:fund_flow_detail', fund_flow_id=fund_flow.id)
    else:
        form = FundFlowForm()
        # 默认今天
        form.fields['flow_date'].initial = timezone.now().date()
    
    context = _context(
        "新增资金流水",
        "➕",
        "创建新的资金流水记录",
        request=request,
        use_financial_nav=True
    )
    context.update({
        'form': form,
        'is_create': True,
    })
    return render(request, "financial_management/fund_flow_form.html", context)


@login_required
def fund_flow_update(request, fund_flow_id):
    """编辑资金流水"""
    permission_codes = get_user_permission_codes(request.user)
    if not _permission_granted('financial_management.fund_flow.manage', permission_codes):
        messages.error(request, '您没有权限编辑资金流水')
        return redirect('finance_pages:fund_flow_detail', fund_flow_id=fund_flow_id)
    
    fund_flow = get_object_or_404(FundFlow, id=fund_flow_id)
    
    if request.method == 'POST':
        form = FundFlowForm(request.POST, instance=fund_flow)
        if form.is_valid():
            form.save()
            messages.success(request, f'资金流水 {fund_flow.flow_number} 更新成功！')
            return redirect('finance_pages:fund_flow_detail', fund_flow_id=fund_flow.id)
    else:
        form = FundFlowForm(instance=fund_flow)
    
    context = _context(
        f"编辑资金流水 - {fund_flow.flow_number}",
        "✏️",
        f"编辑资金流水 {fund_flow.flow_number}",
        request=request,
        use_financial_nav=True
    )
    context.update({
        'form': form,
        'fund_flow': fund_flow,
        'is_create': False,
    })
    return render(request, "financial_management/fund_flow_form.html", context)


# 创建凭证分录的内联表单集
VoucherEntryFormSet = inlineformset_factory(
    Voucher, VoucherEntry,
    form=VoucherEntryForm,
    extra=3,  # 默认显示3个空行
    can_delete=True,
    min_num=1,  # 至少需要1个分录
    validate_min=True,
)


@login_required
def voucher_create(request):
    """新增记账凭证"""
    permission_codes = get_user_permission_codes(request.user)
    if not _permission_granted('financial_management.voucher.create', permission_codes):
        messages.error(request, '您没有权限创建记账凭证')
        return redirect('finance_pages:voucher_management')
    
    if request.method == 'POST':
        form = VoucherForm(request.POST)
        formset = VoucherEntryFormSet(request.POST)
        
        if form.is_valid() and formset.is_valid():
            voucher = form.save(commit=False)
            # 自动生成凭证字号
            if not voucher.voucher_number:
                current_year = timezone.now().year
                max_voucher = Voucher.objects.filter(
                    voucher_number__startswith=f'VOUCHER-{current_year}-'
                ).aggregate(max_num=Max('voucher_number'))['max_num']
                if max_voucher:
                    try:
                        seq = int(max_voucher.split('-')[-1]) + 1
                    except (ValueError, IndexError):
                        seq = 1
                else:
                    seq = 1
                voucher.voucher_number = f'VOUCHER-{current_year}-{seq:04d}'
            if not voucher.preparer:
                voucher.preparer = request.user
            voucher.save()
            
            # 保存分录并计算合计
            entries = formset.save(commit=False)
            total_debit = Decimal('0.00')
            total_credit = Decimal('0.00')
            
            for entry in entries:
                entry.voucher = voucher
                entry.save()
                total_debit += entry.debit_amount or Decimal('0.00')
                total_credit += entry.credit_amount or Decimal('0.00')
            
            # 删除标记为删除的分录
            for obj in formset.deleted_objects:
                obj.delete()
            
            # 更新合计
            voucher.total_debit = total_debit
            voucher.total_credit = total_credit
            voucher.save()
            
            messages.success(request, f'记账凭证 {voucher.voucher_number} 创建成功！')
            return redirect('finance_pages:voucher_detail', voucher_id=voucher.id)
        else:
            messages.error(request, '请检查表单中的错误。')
    else:
        form = VoucherForm(initial={'voucher_date': timezone.now().date(), 'preparer': request.user})
        formset = VoucherEntryFormSet()
    
    # 获取所有会计科目供 JavaScript 使用
    account_subjects = AccountSubject.objects.filter(is_active=True).order_by('code')
    
    context = _context(
        "新增记账凭证",
        "➕",
        "创建新的记账凭证",
        request=request,
        use_financial_nav=True
    )
    context.update({
        'form': form,
        'formset': formset,
        'is_create': True,
        'account_subjects': account_subjects,
    })
    return render(request, "financial_management/voucher_form.html", context)


@login_required
def voucher_update(request, voucher_id):
    """编辑记账凭证"""
    permission_codes = get_user_permission_codes(request.user)
    if not _permission_granted('financial_management.voucher.manage', permission_codes):
        messages.error(request, '您没有权限编辑记账凭证')
        return redirect('finance_pages:voucher_detail', voucher_id=voucher_id)
    
    voucher = get_object_or_404(Voucher.objects.prefetch_related('entries'), id=voucher_id)
    
    # 已过账的凭证不能编辑
    if voucher.status == 'posted':
        messages.error(request, '已过账的凭证不能编辑')
        return redirect('finance_pages:voucher_detail', voucher_id=voucher.id)
    
    if request.method == 'POST':
        form = VoucherForm(request.POST, instance=voucher)
        formset = VoucherEntryFormSet(request.POST, instance=voucher)
        
        if form.is_valid() and formset.is_valid():
            voucher = form.save()
            
            # 保存分录并计算合计
            entries = formset.save(commit=False)
            total_debit = Decimal('0.00')
            total_credit = Decimal('0.00')
            
            for entry in entries:
                entry.voucher = voucher
                entry.save()
                total_debit += entry.debit_amount or Decimal('0.00')
                total_credit += entry.credit_amount or Decimal('0.00')
            
            # 删除标记为删除的分录
            for obj in formset.deleted_objects:
                obj.delete()
            
            # 更新合计
            voucher.total_debit = total_debit
            voucher.total_credit = total_credit
            voucher.save()
            
            messages.success(request, f'记账凭证 {voucher.voucher_number} 更新成功！')
            return redirect('finance_pages:voucher_detail', voucher_id=voucher.id)
        else:
            messages.error(request, '请检查表单中的错误。')
    else:
        form = VoucherForm(instance=voucher)
        formset = VoucherEntryFormSet(instance=voucher)
    
    # 获取所有会计科目供 JavaScript 使用
    account_subjects = AccountSubject.objects.filter(is_active=True).order_by('code')
    
    context = _context(
        f"编辑记账凭证 - {voucher.voucher_number}",
        "✏️",
        f"编辑记账凭证 {voucher.voucher_number}",
        request=request,
        use_financial_nav=True
    )
    context.update({
        'form': form,
        'formset': formset,
        'voucher': voucher,
        'is_create': False,
        'account_subjects': account_subjects,
    })
    return render(request, "financial_management/voucher_form.html", context)


@login_required
def voucher_management(request):
    """凭证管理"""
    permission_codes = get_user_permission_codes(request.user)
    
    # 获取筛选参数
    search = request.GET.get('search', '')
    status = request.GET.get('status', '')
    date_from = request.GET.get('date_from', '')
    date_to = request.GET.get('date_to', '')
    
    # 获取凭证列表
    try:
        vouchers = Voucher.objects.select_related('preparer', 'reviewer', 'posted_by').order_by('-voucher_date', '-voucher_number')
        
        # 应用筛选条件
        if search:
            vouchers = vouchers.filter(
                Q(voucher_number__icontains=search) |
                Q(notes__icontains=search)
            )
        if status:
            vouchers = vouchers.filter(status=status)
        if date_from:
            vouchers = vouchers.filter(voucher_date__gte=date_from)
        if date_to:
            vouchers = vouchers.filter(voucher_date__lte=date_to)
        
        # 分页
        paginator = Paginator(vouchers, 20)
        page_number = request.GET.get('page', 1)
        page_obj = paginator.get_page(page_number)
    except Exception as e:
        import logging
        logger = logging.getLogger(__name__)
        logger.exception('获取凭证列表失败: %s', str(e))
        page_obj = None
    
    # 统计信息
    try:
        total_vouchers = Voucher.objects.count()
        pending_vouchers = Voucher.objects.filter(status='submitted').count()
        approved_vouchers = Voucher.objects.filter(status='approved').count()
        posted_vouchers = Voucher.objects.filter(status='posted').count()
        
        summary_cards = [
            {"label": "凭证总数", "value": total_vouchers, "hint": "系统中维护的记账凭证总数"},
            {"label": "待审核", "value": pending_vouchers, "hint": "状态为已提交的凭证数量"},
            {"label": "已审核", "value": approved_vouchers, "hint": "状态为已审核的凭证数量"},
            {"label": "已过账", "value": posted_vouchers, "hint": "状态为已过账的凭证数量"},
        ]
    except Exception as e:
        import logging
        logger = logging.getLogger(__name__)
        logger.exception('获取统计信息失败: %s', str(e))
        summary_cards = []
    
    context = _context(
        "凭证管理",
        "📝",
        "管理记账凭证",
        summary_cards=summary_cards,
        request=request,
        use_financial_nav=True
    )
    context.update({
        'page_obj': page_obj,
        'vouchers': page_obj.object_list if page_obj else [],
        'status_choices': Voucher.STATUS_CHOICES,
        'current_search': search,
        'current_status': status,
        'current_date_from': date_from,
        'current_date_to': date_to,
    })
    return render(request, "financial_management/voucher_list.html", context)


@login_required
def ledger_management(request):
    """账簿管理"""
    permission_codes = get_user_permission_codes(request.user)
    today = timezone.now().date()
    
    # 获取筛选参数
    search = request.GET.get('search', '')
    period_year = request.GET.get('period_year', str(today.year))
    period_month = request.GET.get('period_month', '')
    account_subject_id = request.GET.get('account_subject_id', '')
    
    # 获取总账列表
    try:
        ledgers = Ledger.objects.select_related('account_subject').order_by('-period_date', 'account_subject__code')
        
        # 应用筛选条件
        if search:
            ledgers = ledgers.filter(
                Q(account_subject__code__icontains=search) |
                Q(account_subject__name__icontains=search)
            )
        if period_year:
            ledgers = ledgers.filter(period_year=int(period_year))
        if period_month:
            ledgers = ledgers.filter(period_month=int(period_month))
        if account_subject_id:
            ledgers = ledgers.filter(account_subject_id=int(account_subject_id))
        
        # 分页
        paginator = Paginator(ledgers, 50)
        page_number = request.GET.get('page', 1)
        page_obj = paginator.get_page(page_number)
    except Exception as e:
        import logging
        logger = logging.getLogger(__name__)
        logger.exception('获取总账列表失败: %s', str(e))
        page_obj = None
    
    # 统计信息
    try:
        current_year = int(period_year) if period_year else today.year
        current_month = int(period_month) if period_month else today.month
        ledger_count = Ledger.objects.filter(
            period_year=current_year,
            period_month=current_month
        ).count()
        
        summary_cards = [
            {"label": "账务记录", "value": ledger_count, "hint": f"{current_year}年{current_month}月的账务记录数"},
        ]
    except Exception as e:
        import logging
        logger = logging.getLogger(__name__)
        logger.exception('获取统计信息失败: %s', str(e))
        summary_cards = []
    
    context = _context(
        "账簿管理",
        "📖",
        "管理总账、明细账等",
        summary_cards=summary_cards,
        request=request,
        use_financial_nav=True
    )
    context.update({
        'page_obj': page_obj,
        'ledgers': page_obj.object_list if page_obj else [],
        'current_search': search,
        'current_period_year': period_year,
        'current_period_month': period_month,
        'current_account_subject_id': account_subject_id,
        'years': range(today.year - 2, today.year + 2),
        'months': range(1, 13),
    })
    return render(request, "financial_management/ledger_list.html", context)


@login_required
def budget_management(request):
    """预算管理"""
    permission_codes = get_user_permission_codes(request.user)
    today = timezone.now().date()
    
    # 获取筛选参数
    search = request.GET.get('search', '')
    status = request.GET.get('status', '')
    budget_year = request.GET.get('budget_year', '')
    
    # 获取预算列表
    try:
        budgets = Budget.objects.select_related('department', 'account_subject', 'approver', 'created_by').order_by('-budget_year', '-created_time')
        
        # 应用筛选条件
        if search:
            budgets = budgets.filter(
                Q(budget_number__icontains=search) |
                Q(name__icontains=search) |
                Q(description__icontains=search)
            )
        if status:
            budgets = budgets.filter(status=status)
        if budget_year:
            budgets = budgets.filter(budget_year=int(budget_year))
        
        # 分页
        paginator = Paginator(budgets, 20)
        page_number = request.GET.get('page', 1)
        page_obj = paginator.get_page(page_number)
    except Exception as e:
        import logging
        logger = logging.getLogger(__name__)
        logger.exception('获取预算列表失败: %s', str(e))
        page_obj = None
    
    # 统计信息
    try:
        total_budgets = Budget.objects.count()
        executing_budgets = Budget.objects.filter(status='executing').count()
        total_budget_amount = Budget.objects.filter(status='executing').aggregate(
            total=Sum('budget_amount')
        )['total'] or Decimal('0')
        total_used_amount = Budget.objects.filter(status='executing').aggregate(
            total=Sum('used_amount')
        )['total'] or Decimal('0')
        
        summary_cards = [
            {"label": "预算总数", "value": total_budgets, "hint": "系统中维护的预算总数"},
            {"label": "执行中", "value": executing_budgets, "hint": "状态为执行中的预算数量"},
            {"label": "预算总额", "value": f"¥{total_budget_amount:,.2f}", "hint": "执行中预算的总额"},
            {"label": "已用金额", "value": f"¥{total_used_amount:,.2f}", "hint": "执行中预算的已用金额"},
        ]
    except Exception as e:
        import logging
        logger = logging.getLogger(__name__)
        logger.exception('获取统计信息失败: %s', str(e))
        summary_cards = []
    
    context = _context(
        "预算管理",
        "💰",
        "管理预算编制和执行",
        summary_cards=summary_cards,
        request=request,
        use_financial_nav=True
    )
    context.update({
        'page_obj': page_obj,
        'budgets': page_obj.object_list if page_obj else [],
        'status_choices': Budget.STATUS_CHOICES,
        'current_search': search,
        'current_status': status,
        'current_budget_year': budget_year,
        'years': range(today.year - 2, today.year + 2),
    })
    return render(request, "financial_management/budget_list.html", context)


@login_required
def invoice_management(request):
    """发票管理"""
    permission_codes = get_user_permission_codes(request.user)
    today = timezone.now().date()
    this_month_start = today.replace(day=1)
    
    # 获取筛选参数
    search = request.GET.get('search', '')
    invoice_type = request.GET.get('invoice_type', '')
    status = request.GET.get('status', '')
    date_from = request.GET.get('date_from', '')
    date_to = request.GET.get('date_to', '')
    
    # 获取发票列表
    try:
        invoices = Invoice.objects.select_related('verified_by', 'created_by').order_by('-invoice_date', '-invoice_number')
        
        # 应用筛选条件
        if search:
            invoices = invoices.filter(
                Q(invoice_number__icontains=search) |
                Q(invoice_code__icontains=search) |
                Q(customer_name__icontains=search) |
                Q(supplier_name__icontains=search)
            )
        if invoice_type:
            invoices = invoices.filter(invoice_type=invoice_type)
        if status:
            invoices = invoices.filter(status=status)
        if date_from:
            invoices = invoices.filter(invoice_date__gte=date_from)
        if date_to:
            invoices = invoices.filter(invoice_date__lte=date_to)
        
        # 分页
        paginator = Paginator(invoices, 20)
        page_number = request.GET.get('page', 1)
        page_obj = paginator.get_page(page_number)
    except Exception as e:
        import logging
        logger = logging.getLogger(__name__)
        logger.exception('获取发票列表失败: %s', str(e))
        page_obj = None
    
    # 统计信息
    try:
        total_invoices = Invoice.objects.count()
        issued_invoices = Invoice.objects.filter(status='issued').count()
        this_month_invoices = Invoice.objects.filter(invoice_date__gte=this_month_start).count()
        this_month_amount = Invoice.objects.filter(invoice_date__gte=this_month_start).aggregate(
            total=Sum('total_amount')
        )['total'] or Decimal('0')
        
        summary_cards = [
            {"label": "发票总数", "value": total_invoices, "hint": "系统中维护的发票总数"},
            {"label": "待认证", "value": issued_invoices, "hint": "状态为已开具的发票数量"},
            {"label": "本月发票", "value": this_month_invoices, "hint": "本月开具的发票数量"},
            {"label": "本月金额", "value": f"¥{this_month_amount:,.2f}", "hint": "本月发票的价税合计总额"},
        ]
    except Exception as e:
        import logging
        logger = logging.getLogger(__name__)
        logger.exception('获取统计信息失败: %s', str(e))
        summary_cards = []
    
    context = _context(
        "发票管理",
        "🧾",
        "管理进项和销项发票",
        summary_cards=summary_cards,
        request=request,
        use_financial_nav=True
    )
    context.update({
        'page_obj': page_obj,
        'invoices': page_obj.object_list if page_obj else [],
        'invoice_type_choices': Invoice.TYPE_CHOICES,
        'status_choices': Invoice.STATUS_CHOICES,
        'current_search': search,
        'current_invoice_type': invoice_type,
        'current_status': status,
        'current_date_from': date_from,
        'current_date_to': date_to,
    })
    return render(request, "financial_management/invoice_list.html", context)


@login_required
def fund_flow_management(request):
    """资金流水"""
    permission_codes = get_user_permission_codes(request.user)
    today = timezone.now().date()
    this_month_start = today.replace(day=1)
    
    # 获取筛选参数
    search = request.GET.get('search', '')
    flow_type = request.GET.get('flow_type', '')
    date_from = request.GET.get('date_from', '')
    date_to = request.GET.get('date_to', '')
    
    # 获取资金流水列表
    try:
        fund_flows = FundFlow.objects.select_related('project', 'voucher', 'created_by').order_by('-flow_date', '-flow_number')
        
        # 应用筛选条件
        if search:
            fund_flows = fund_flows.filter(
                Q(flow_number__icontains=search) |
                Q(account_name__icontains=search) |
                Q(counterparty__icontains=search) |
                Q(summary__icontains=search)
            )
        if flow_type:
            fund_flows = fund_flows.filter(flow_type=flow_type)
        if date_from:
            fund_flows = fund_flows.filter(flow_date__gte=date_from)
        if date_to:
            fund_flows = fund_flows.filter(flow_date__lte=date_to)
        
        # 分页
        paginator = Paginator(fund_flows, 50)
        page_number = request.GET.get('page', 1)
        page_obj = paginator.get_page(page_number)
    except Exception as e:
        import logging
        logger = logging.getLogger(__name__)
        logger.exception('获取资金流水列表失败: %s', str(e))
        page_obj = None
    
    # 统计信息
    try:
        this_month_flows = FundFlow.objects.filter(flow_date__gte=this_month_start).count()
        this_month_income = FundFlow.objects.filter(
            flow_date__gte=this_month_start,
            flow_type='income'
        ).aggregate(total=Sum('amount'))['total'] or Decimal('0')
        this_month_expense = FundFlow.objects.filter(
            flow_date__gte=this_month_start,
            flow_type='expense'
        ).aggregate(total=Sum('amount'))['total'] or Decimal('0')
        
        summary_cards = [
            {"label": "本月流水", "value": this_month_flows, "hint": "本月发生的资金流水记录数"},
            {"label": "本月收入", "value": f"¥{this_month_income:,.2f}", "hint": "本月收入类流水总额"},
            {"label": "本月支出", "value": f"¥{this_month_expense:,.2f}", "hint": "本月支出类流水总额"},
        ]
    except Exception as e:
        import logging
        logger = logging.getLogger(__name__)
        logger.exception('获取统计信息失败: %s', str(e))
        summary_cards = []
    
    context = _context(
        "资金流水",
        "💳",
        "管理资金流入流出记录",
        summary_cards=summary_cards,
        request=request,
        use_financial_nav=True
    )
    context.update({
        'page_obj': page_obj,
        'fund_flows': page_obj.object_list if page_obj else [],
        'flow_type_choices': FundFlow.TYPE_CHOICES,
        'current_search': search,
        'current_flow_type': flow_type,
        'current_date_from': date_from,
        'current_date_to': date_to,
    })
    return render(request, "financial_management/fund_flow_list.html", context)


@login_required
def voucher_detail(request, voucher_id):
    """凭证详情"""
    voucher = get_object_or_404(Voucher.objects.select_related('preparer', 'reviewer', 'posted_by'), id=voucher_id)
    
    # 获取凭证分录
    try:
        entries = voucher.entries.select_related('account_subject').order_by('line_number')
    except Exception:
        entries = []
    
    context = _context(
        f"凭证详情 - {voucher.voucher_number}",
        "📝",
        f"查看记账凭证 {voucher.voucher_number} 的详细信息和分录",
        request=request,
        use_financial_nav=True
    )
    context.update({
        'voucher': voucher,
        'entries': entries,
    })
    return render(request, "financial_management/voucher_detail.html", context)


@login_required
def budget_detail(request, budget_id):
    """预算详情"""
    budget = get_object_or_404(Budget.objects.select_related('department', 'account_subject', 'approver', 'created_by'), id=budget_id)
    
    # 计算使用率
    usage_rate = 0
    if budget.budget_amount > 0:
        usage_rate = (budget.used_amount / budget.budget_amount) * 100
    
    context = _context(
        f"预算详情 - {budget.budget_number}",
        "💰",
        f"查看预算 {budget.name} 的详细信息",
        request=request,
        use_financial_nav=True
    )
    context.update({
        'budget': budget,
        'usage_rate': usage_rate,
    })
    return render(request, "financial_management/budget_detail.html", context)


@login_required
def invoice_detail(request, invoice_id):
    """发票详情"""
    invoice = get_object_or_404(Invoice.objects.select_related('verified_by', 'created_by'), id=invoice_id)
    
    context = _context(
        f"发票详情 - {invoice.invoice_number}",
        "🧾",
        f"查看发票 {invoice.invoice_number} 的详细信息",
        request=request,
        use_financial_nav=True
    )
    context.update({
        'invoice': invoice,
    })
    return render(request, "financial_management/invoice_detail.html", context)


@login_required
def account_subject_detail(request, account_subject_id):
    """会计科目详情"""
    account_subject = get_object_or_404(
        AccountSubject.objects.select_related('parent', 'created_by'),
        id=account_subject_id
    )
    
    # 获取子科目
    try:
        children = AccountSubject.objects.filter(parent=account_subject).order_by('code')
    except Exception:
        children = []
    
    # 获取使用统计
    try:
        voucher_entry_count = account_subject.voucher_entries.count()
        ledger_entry_count = account_subject.ledger_entries.count()
    except Exception:
        voucher_entry_count = 0
        ledger_entry_count = 0
    
    context = _context(
        f"会计科目详情 - {account_subject.code} {account_subject.name}",
        "📊",
        f"查看会计科目 {account_subject.code} {account_subject.name} 的详细信息",
        request=request,
        use_financial_nav=True
    )
    context.update({
        'account_subject': account_subject,
        'children': children,
        'voucher_entry_count': voucher_entry_count,
        'ledger_entry_count': ledger_entry_count,
    })
    return render(request, "financial_management/account_subject_detail.html", context)


@login_required
def ledger_detail(request, ledger_id):
    """账簿详情"""
    ledger = get_object_or_404(
        Ledger.objects.select_related('account_subject'),
        id=ledger_id
    )
    
    # 获取同一科目的其他期间记录（最近6个月）
    try:
        related_ledgers = Ledger.objects.filter(
            account_subject=ledger.account_subject
        ).exclude(id=ledger.id).order_by('-period_date')[:6]
    except Exception:
        related_ledgers = []
    
    context = _context(
        f"账簿详情 - {ledger.account_subject.code} {ledger.period_date}",
        "📖",
        f"查看会计科目 {ledger.account_subject.code} 在 {ledger.period_date} 的账务记录",
        request=request,
        use_financial_nav=True
    )
    context.update({
        'ledger': ledger,
        'related_ledgers': related_ledgers,
    })
    return render(request, "financial_management/ledger_detail.html", context)


@login_required
def fund_flow_detail(request, fund_flow_id):
    """资金流水详情"""
    fund_flow = get_object_or_404(
        FundFlow.objects.select_related('project', 'voucher', 'created_by'),
        id=fund_flow_id
    )
    
    context = _context(
        f"资金流水详情 - {fund_flow.flow_number}",
        "💳",
        f"查看资金流水 {fund_flow.flow_number} 的详细信息",
        request=request,
        use_financial_nav=True
    )
    context.update({
        'fund_flow': fund_flow,
    })
    return render(request, "financial_management/fund_flow_detail.html", context)

