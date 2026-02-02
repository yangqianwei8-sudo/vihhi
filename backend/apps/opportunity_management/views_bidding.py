# 商机管理 - 投标报价视图

from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.shortcuts import get_object_or_404, redirect, render
from django.db.models import Q

from .views_common import (
    _context,
    _build_opportunity_management_sidebar_nav,
    _build_full_top_nav,
    _get_opportunities_safely,
    get_user_permission_codes,
    BusinessOpportunity,
    BiddingQuotation,
)
from .perm_check import opportunity_can_view, opportunity_can_view_all

def opportunity_bidding_quotation(request):
    """投标报价页面"""
    permission_set = get_user_permission_codes(request.user)
    
    # 获取筛选参数
    search = request.GET.get('search', '')
    opportunity_id = request.GET.get('opportunity_id', '')
    status = request.GET.get('status', '')
    
    # 获取投标报价列表
    try:
        bidding_quotations = BiddingQuotation.objects.select_related(
            'opportunity', 'opportunity__client', 'opportunity__business_manager', 'created_by'
        ).order_by('-bidding_date', '-created_time')
        
        # 权限过滤：只能查看自己创建的或关联商机是自己负责的投标报价
        if not opportunity_can_view_all(permission_set):
            bidding_quotations = bidding_quotations.filter(
                Q(created_by=request.user) |
                Q(opportunity__business_manager=request.user)
            )
        
        # 应用筛选条件
        if search:
            bidding_quotations = bidding_quotations.filter(
                Q(bidding_number__icontains=search) |
                Q(opportunity__name__icontains=search) |
                Q(opportunity__opportunity_number__icontains=search) |
                Q(opportunity__client__name__icontains=search)
            )
        if opportunity_id:
            bidding_quotations = bidding_quotations.filter(opportunity_id=opportunity_id)
        if status:
            bidding_quotations = bidding_quotations.filter(status=status)
        
        # 分页
        from django.core.paginator import Paginator
        paginator = Paginator(bidding_quotations, 13)
        page_number = request.GET.get('page', 1)
        page_obj = paginator.get_page(page_number)
    except Exception as e:
        import logging
        logger = logging.getLogger(__name__)
        logger.exception('获取投标报价列表失败: %s', str(e))
        messages.error(request, f'获取投标报价列表失败：{str(e)}')
        page_obj = None
    
    context = _context(
        "投标报价",
        "💰",
        "商机投标报价管理",
        request=request,
    )
    if request and request.user.is_authenticated:
        context['full_top_nav'] = _build_full_top_nav(permission_set, request.user)
        # 生成左侧菜单（投标报价页面，激活"投标报价"菜单项）
        context['sidebar_nav'] = _build_opportunity_management_sidebar_nav(permission_set, active_id='bidding_quotation')
    else:
        context['full_top_nav'] = []
        context['sidebar_nav'] = []
    # 获取商机列表（用于筛选下拉框）
    try:
        opportunities = BusinessOpportunity.objects.filter(is_active=True).select_related('client', 'business_manager').order_by('-created_time')
        if not opportunity_can_view_all(permission_set):
            opportunities = opportunities.filter(business_manager=request.user)
        opportunities = opportunities[:100]  # 限制显示数量
    except Exception as e:
        opportunities = []
    
    # 获取状态选项
    from django.utils import timezone
    from django.db.models import Count, Q
    status_choices = BiddingQuotation.STATUS_CHOICES
    
    # 计算统计信息
    all_bidding_quotations = BiddingQuotation.objects.select_related('opportunity', 'created_by')
    if not opportunity_can_view_all(permission_set):
        all_bidding_quotations = all_bidding_quotations.filter(
            Q(created_by=request.user) |
            Q(opportunity__business_manager=request.user)
        )
    
    total_count = all_bidding_quotations.count()
    draft_count = all_bidding_quotations.filter(status='draft').count()
    preparing_count = all_bidding_quotations.filter(status='preparing').count()
    submitted_count = all_bidding_quotations.filter(status='submitted').count()
    won_count = all_bidding_quotations.filter(status='won').count()
    lost_count = all_bidding_quotations.filter(status='lost').count()
    
    context.update({
        'page_obj': page_obj,
        'search': search,
        'opportunity_id': opportunity_id,
        'status': status,
        'opportunities': opportunities,
        'status_choices': status_choices,
        'today': timezone.now().date(),
        'total_count': total_count,
        'draft_count': draft_count,
        'preparing_count': preparing_count,
        'submitted_count': submitted_count,
        'won_count': won_count,
        'lost_count': lost_count,
    })
    return render(request, "opportunity_management/opportunity_bidding_quotation.html", context)


@login_required
def opportunity_bidding_quotation_application(request):
    """投标报价申请页面（第一步）"""
    permission_set = get_user_permission_codes(request.user)
    
    # 权限检查
    if not opportunity_can_view(permission_set):
        messages.error(request, '您没有权限访问投标报价申请功能')
        return redirect('opportunity_pages:opportunity_management')
    
    # 获取商机列表（用于表单下拉框）
    opportunities = BusinessOpportunity.objects.filter(is_active=True).select_related('client', 'business_manager').order_by('-created_time')
    if not opportunity_can_view_all(permission_set):
        opportunities = opportunities.filter(business_manager=request.user)
    opportunities = _get_opportunities_safely(opportunities, permission_set, request.user)
    
    if request.method == 'POST':
        # TODO: 处理表单提交
        messages.success(request, '投标报价申请已提交')
        return redirect('opportunity_pages:opportunity_bidding_quotation_application')
    
    context = _context(
        "投标报价申请",
        "📝",
        "提交投标报价申请",
        request=request,
    )
    if request and request.user.is_authenticated:
        context['full_top_nav'] = _build_full_top_nav(permission_set, request.user)
    else:
        context['full_top_nav'] = []
    context['opportunities'] = opportunities[:100]  # 限制显示数量
    return render(request, "opportunity_management/opportunity_bidding_quotation_application.html", context)


@login_required
def opportunity_bidding_document_preparation(request):
    """编制投标文件页面（第二步）"""
    permission_set = get_user_permission_codes(request.user)
    
    # 权限检查
    if not opportunity_can_view(permission_set):
        messages.error(request, '您没有权限访问编制投标文件功能')
        return redirect('opportunity_pages:opportunity_management')
    
    # 获取商机列表（用于表单下拉框）
    opportunities = BusinessOpportunity.objects.filter(is_active=True).select_related('client', 'business_manager').order_by('-created_time')
    if not opportunity_can_view_all(permission_set):
        opportunities = opportunities.filter(business_manager=request.user)
    opportunities = _get_opportunities_safely(opportunities, permission_set, request.user)
    
    if request.method == 'POST':
        # TODO: 处理表单提交
        messages.success(request, '投标文件编制信息已保存')
        return redirect('opportunity_pages:opportunity_bidding_document_preparation')
    
    context = _context(
        "编制投标文件",
        "📄",
        "编制投标文件信息管理",
        request=request,
    )
    if request and request.user.is_authenticated:
        context['full_top_nav'] = _build_full_top_nav(permission_set, request.user)
    else:
        context['full_top_nav'] = []
    context['opportunities'] = opportunities[:100]  # 限制显示数量
    return render(request, "opportunity_management/opportunity_bidding_document_preparation.html", context)


@login_required
def opportunity_bidding_document_submission(request):
    """递交投标文件页面（第三步）"""
    permission_set = get_user_permission_codes(request.user)
    
    # 权限检查
    if not opportunity_can_view(permission_set):
        messages.error(request, '您没有权限访问递交投标文件功能')
        return redirect('opportunity_pages:opportunity_management')
    
    # 获取商机列表（用于表单下拉框）
    opportunities = BusinessOpportunity.objects.filter(is_active=True).select_related('client', 'business_manager').order_by('-created_time')
    if not opportunity_can_view_all(permission_set):
        opportunities = opportunities.filter(business_manager=request.user)
    opportunities = _get_opportunities_safely(opportunities, permission_set, request.user)
    
    if request.method == 'POST':
        # TODO: 处理表单提交
        messages.success(request, '投标文件递交信息已保存')
        return redirect('opportunity_pages:opportunity_bidding_document_submission')
    
    context = _context(
        "递交投标文件",
        "📤",
        "递交投标文件信息管理",
        request=request,
    )
    if request and request.user.is_authenticated:
        context['full_top_nav'] = _build_full_top_nav(permission_set, request.user)
    else:
        context['full_top_nav'] = []
    context['opportunities'] = opportunities[:100]  # 限制显示数量
    return render(request, "opportunity_management/opportunity_bidding_document_submission.html", context)


@login_required
def bidding_quotation_create(request):
    """创建投标报价页面"""
    permission_set = get_user_permission_codes(request.user)
    
    if request.method == 'POST':
        try:
            # 获取并验证必填字段
            opportunity_id = request.POST.get('opportunity_id')
            bidding_date = request.POST.get('bidding_date')
            submission_deadline = request.POST.get('submission_deadline')
            
            if not opportunity_id:
                messages.error(request, '请选择关联商机')
                return redirect('opportunity_pages:opportunity_bidding_quotation_create')
            if not bidding_date:
                messages.error(request, '投标日期不能为空')
                return redirect('opportunity_pages:opportunity_bidding_quotation_create')
            if not submission_deadline:
                messages.error(request, '提交截止日期不能为空')
                return redirect('opportunity_pages:opportunity_bidding_quotation_create')
            
            # 获取商机
            opportunity = get_object_or_404(BusinessOpportunity, id=opportunity_id)
            
            # 创建投标报价记录
            bidding_quotation = BiddingQuotation.objects.create(
                opportunity=opportunity,
                bidding_number=request.POST.get('bidding_number', '').strip(),
                bidding_date=bidding_date,
                submission_deadline=submission_deadline,
                status=request.POST.get('status', 'draft'),
                tender_requirements=request.POST.get('tender_requirements', '').strip(),
                notes=request.POST.get('notes', '').strip(),
                created_by=request.user,
            )
            
            messages.success(request, f'投标报价 "{bidding_quotation.bidding_number or "新建"}" 创建成功')
            return redirect('opportunity_pages:opportunity_bidding_quotation')
        except Exception as e:
            import logging
            logger = logging.getLogger(__name__)
            logger.exception('创建投标报价失败: %s', str(e))
            messages.error(request, f'创建投标报价失败：{str(e)}')
    
    # GET请求，显示表单
    # 获取可用的商机列表
    opportunities = BusinessOpportunity.objects.filter(is_active=True).select_related('client', 'business_manager').order_by('-created_time')
    
    # 权限过滤
    if not opportunity_can_view_all(permission_set):
        opportunities = opportunities.filter(business_manager=request.user)
    
    context = _context(
        "创建投标报价",
        "➕",
        "填写以下信息创建新的投标报价",
        request=request,
    )
    if request and request.user.is_authenticated:
        context['full_top_nav'] = _build_full_top_nav(permission_set, request.user)
        # 生成左侧菜单（投标报价页面，激活"投标报价"菜单项）
        context['sidebar_nav'] = _build_opportunity_management_sidebar_nav(permission_set, active_id='bidding_quotation')
    else:
        context['full_top_nav'] = []
        context['sidebar_nav'] = []
    context.update({
        'opportunities': opportunities[:100],  # 限制显示数量
        'status_choices': BiddingQuotation.STATUS_CHOICES,
    })
    return render(request, "customer_management/bidding_quotation_form.html", context)


@login_required
def bidding_quotation_detail(request, bidding_id):
    """投标报价详情页面"""
    permission_set = get_user_permission_codes(request.user)
    
    # 权限检查
    if not opportunity_can_view(permission_set):
        messages.error(request, '您没有权限查看投标报价详情')
        return redirect('opportunity_pages:opportunity_bidding_quotation')
    
    try:
        from django.shortcuts import get_object_or_404
        
        bidding_quotation = get_object_or_404(
            BiddingQuotation.objects.select_related(
                'opportunity', 'opportunity__client', 'opportunity__business_manager', 'created_by'
            ),
            id=bidding_id
        )
        
        # 权限过滤：只能查看自己创建的或关联商机是自己负责的投标报价
        if not opportunity_can_view_all(permission_set):
            if bidding_quotation.created_by != request.user and bidding_quotation.opportunity.business_manager != request.user:
                messages.error(request, '您没有权限查看此投标报价')
                return redirect('opportunity_pages:opportunity_bidding_quotation')
        
        # 获取关联的类似业绩
        similar_projects = bidding_quotation.similar_projects.select_related('client')[:20]
        
        context = _context(
            f"投标报价详情 - {bidding_quotation.bidding_number or '未编号'}",
            "📋",
            "查看投标报价详细信息",
            request=request,
        )
        if request and request.user.is_authenticated:
            context['full_top_nav'] = _build_full_top_nav(permission_set, request.user)
        else:
            context['full_top_nav'] = []
        from django.utils import timezone
        context.update({
            'bidding_quotation': bidding_quotation,
            'similar_projects': similar_projects,
            'today': timezone.now().date(),
        })
        return render(request, "customer_management/bidding_quotation_detail.html", context)
    except Exception as e:
        import logging
        logger = logging.getLogger(__name__)
        logger.exception('查看投标报价详情失败: %s', str(e))
        messages.error(request, f'查看投标报价详情失败：{str(e)}')
        return redirect('opportunity_pages:opportunity_bidding_quotation')


@login_required
def bidding_quotation_edit(request, bidding_id):
    """投标报价编辑页面"""
    permission_set = get_user_permission_codes(request.user)
    
    # 权限检查
    if not opportunity_can_view(permission_set):
        messages.error(request, '您没有权限编辑投标报价')
        return redirect('opportunity_pages:opportunity_bidding_quotation')
    
    try:
        from django.shortcuts import get_object_or_404
        
        bidding_quotation = get_object_or_404(
            BiddingQuotation.objects.select_related('opportunity', 'opportunity__client'),
            id=bidding_id
        )
        
        # 权限过滤：只能编辑自己创建的或关联商机是自己负责的投标报价
        if not opportunity_can_view_all(permission_set):
            if bidding_quotation.created_by != request.user and bidding_quotation.opportunity.business_manager != request.user:
                messages.error(request, '您没有权限编辑此投标报价')
                return redirect('opportunity_pages:opportunity_bidding_quotation')
        
        if request.method == 'POST':
            # 处理表单提交
            bidding_quotation.bidding_number = request.POST.get('bidding_number', '').strip() or bidding_quotation.bidding_number
            bidding_quotation.bidding_date = request.POST.get('bidding_date') or bidding_quotation.bidding_date
            bidding_quotation.submission_deadline = request.POST.get('submission_deadline') or bidding_quotation.submission_deadline
            bidding_quotation.status = request.POST.get('status', bidding_quotation.status)
            bidding_quotation.tender_requirements = request.POST.get('tender_requirements', '').strip()
            bidding_quotation.notes = request.POST.get('notes', '').strip()
            
            # 处理技术标信息（JSON格式）
            technical_proposal = {}
            technical_proposal['technical_solution'] = request.POST.get('technical_solution', '').strip()
            technical_proposal['technical_capability'] = request.POST.get('technical_capability', '').strip()
            technical_proposal['technical_team'] = request.POST.get('technical_team', '').strip()
            technical_proposal['implementation_plan'] = request.POST.get('implementation_plan', '').strip()
            bidding_quotation.technical_proposal = technical_proposal
            
            # 处理商务标信息（JSON格式）
            commercial_proposal = {}
            commercial_proposal['quotation_mode'] = request.POST.get('quotation_mode', 'rate')
            commercial_proposal['saved_amount'] = float(request.POST.get('saved_amount', 0) or 0)
            commercial_proposal['mode_params'] = {}
            
            # 根据报价模式处理参数
            if commercial_proposal['quotation_mode'] == 'rate':
                commercial_proposal['mode_params']['rate'] = float(request.POST.get('rate', 0) or 0) / 100
            elif commercial_proposal['quotation_mode'] == 'base_fee_rate':
                commercial_proposal['mode_params']['base_fee'] = float(request.POST.get('base_fee', 0) or 0)
                commercial_proposal['mode_params']['rate'] = float(request.POST.get('rate', 0) or 0) / 100
            elif commercial_proposal['quotation_mode'] == 'fixed':
                commercial_proposal['mode_params']['fixed_amount'] = float(request.POST.get('fixed_amount', 0) or 0)
            
            commercial_proposal['cap_fee'] = float(request.POST.get('cap_fee', 0) or 0) if request.POST.get('cap_fee') else None
            commercial_proposal['service_fee'] = float(request.POST.get('service_fee', 0) or 0)
            commercial_proposal['payment_method'] = request.POST.get('payment_method', '').strip()
            commercial_proposal['service_commitment'] = request.POST.get('service_commitment', '').strip()
            bidding_quotation.commercial_proposal = commercial_proposal
            
            # 处理类似业绩（多对多关系）
            similar_project_ids = request.POST.getlist('similar_projects')
            bidding_quotation.save()
            if similar_project_ids:
                from backend.apps.production_management.models import Project
                similar_projects = Project.objects.filter(id__in=similar_project_ids)
                bidding_quotation.similar_projects.set(similar_projects)
            
            messages.success(request, f'投标报价 "{bidding_quotation.bidding_number or "未编号"}" 更新成功')
            return redirect('opportunity_pages:opportunity_bidding_quotation_detail', bidding_id=bidding_quotation.id)
        
        # GET请求，显示编辑表单
        # 获取可用的商机列表
        opportunities = BusinessOpportunity.objects.filter(is_active=True).select_related('client', 'business_manager').order_by('-created_time')
        if not opportunity_can_view_all(permission_set):
            opportunities = opportunities.filter(business_manager=request.user)
        
        # 获取已完成项目（类似业绩）
        from backend.apps.production_management.models import Project
        completed_projects = Project.objects.filter(
            status__in=['completed', 'delivered']
        ).select_related('client').order_by('-end_date')[:50]
        
        # 获取报价模式选项
        from backend.apps.opportunity_management.models import OpportunityQuotation
        quotation_mode_choices = OpportunityQuotation._meta.get_field('quotation_mode').choices
        
        context = _context(
            f"编辑投标报价 - {bidding_quotation.bidding_number or '未编号'}",
            "✏️",
            "编辑投标报价信息",
            request=request,
        )
        if request and request.user.is_authenticated:
            context['full_top_nav'] = _build_full_top_nav(permission_set, request.user)
        else:
            context['full_top_nav'] = []
        context.update({
            'bidding_quotation': bidding_quotation,
            'opportunities': opportunities[:100],
            'completed_projects': completed_projects,
            'status_choices': BiddingQuotation.STATUS_CHOICES,
            'quotation_mode_choices': quotation_mode_choices,
        })
        return render(request, "customer_management/bidding_quotation_edit.html", context)
    except Exception as e:
        import logging
        logger = logging.getLogger(__name__)
        logger.exception('编辑投标报价失败: %s', str(e))
        messages.error(request, f'编辑投标报价失败：{str(e)}')
        return redirect('opportunity_pages:opportunity_bidding_quotation')


