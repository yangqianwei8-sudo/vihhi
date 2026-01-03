from django.contrib.auth.decorators import login_required
from django.shortcuts import render, redirect
from django.urls import reverse, NoReverseMatch
from django.views.decorators.csrf import csrf_exempt
from django.http import JsonResponse
from django.utils import timezone
from django.contrib import messages
import logging

from backend.apps.system_management.services import get_user_permission_codes
from backend.core.views import HOME_NAV_STRUCTURE, _permission_granted, _build_full_top_nav, _build_unified_sidebar_nav
from .common import _context, _build_delivery_sidebar_nav

logger = logging.getLogger(__name__)


@login_required
def express_company_list(request):
    """快递公司列表"""
    from django.core.paginator import Paginator
    from django.db.models import Q
    from backend.apps.delivery_customer.models import ExpressCompany
    
    permission_set = get_user_permission_codes(request.user)
    
    # 获取查询参数
    search = request.GET.get('search', '').strip()
    status_filter = request.GET.get('status', '')  # 空字符串表示全部
    
    # 查询快递公司
    companies = ExpressCompany.objects.all().order_by('sort_order', 'name')
    
    # 搜索过滤
    if search:
        companies = companies.filter(
            Q(name__icontains=search) |
            Q(code__icontains=search) |
            Q(alias__icontains=search) |
            Q(contact_phone__icontains=search)
        )
    
    # 状态过滤
    if status_filter == 'active':
        companies = companies.filter(is_active=True)
    elif status_filter == 'inactive':
        companies = companies.filter(is_active=False)
    
    # 分页（固定为每页 10 条，符合 list_page_base.html 模板规定）
    per_page = 10
    paginator = Paginator(companies, per_page)
    page_number = request.GET.get('page', 1)
    page_obj = paginator.get_page(page_number)
    
    # 构建上下文（符合 list_page_base.html 模板要求）
    context = _context(
        "快递公司列表",
        "🚚",
        "管理快递公司信息",
        request=request,
        active_menu_id='express_company_list',
    )
    # 列表模板必需字段
    context.update({
        'page_obj': page_obj,  # 分页对象，包含 object_list
        'page_title': '快递公司列表',  # 页面标题
        'search': search,  # 搜索关键词
        'selected_status': status_filter,  # 选中的状态
        'status_choices': [('', '全部状态'), ('active', '启用'), ('inactive', '禁用')],  # 状态选项
    })
    
    return render(request, "delivery_customer/express_company_list.html", context)


@login_required
def express_company_create(request):
    """创建快递公司"""
    from django.shortcuts import redirect
    from django.contrib import messages
    from backend.apps.delivery_customer.models import ExpressCompany
    
    permission_set = get_user_permission_codes(request.user)
    module_sidebar_nav = _build_delivery_sidebar_nav(permission_set, request.path)
    delivery_sidebar_nav = module_sidebar_nav  # 兼容旧模板
    
    if not _permission_granted('delivery_center.create', permission_set):
        messages.error(request, '您没有创建快递公司的权限')
        return redirect('delivery_pages:express_company_list')
    
    if request.method == 'POST':
        try:
            name = request.POST.get('name', '').strip()
            if not name:
                messages.error(request, '快递公司名称不能为空')
            elif ExpressCompany.objects.filter(name=name).exists():
                messages.error(request, f'快递公司"{name}"已存在')
            else:
                company = ExpressCompany(
                    name=name,
                    code=request.POST.get('code', '').strip(),
                    alias=request.POST.get('alias', '').strip(),
                    contact_phone=request.POST.get('contact_phone', '').strip(),
                    contact_email=request.POST.get('contact_email', '').strip(),
                    website=request.POST.get('website', '').strip(),
                    is_active=request.POST.get('is_active') == 'on',
                    is_default=request.POST.get('is_default') == 'on',
                    sort_order=int(request.POST.get('sort_order', 0) or 0),
                    notes=request.POST.get('notes', '').strip(),
                    created_by=request.user,
                )
                company.save()
                
                # 如果设为默认，取消其他默认设置
                if company.is_default:
                    ExpressCompany.objects.filter(is_default=True).exclude(id=company.id).update(is_default=False)
                
                messages.success(request, f'快递公司"{name}"创建成功')
                return redirect('delivery_pages:express_company_detail', company_id=company.id)
        except Exception as e:
            logger.error(f"创建快递公司失败: {str(e)}")
            messages.error(request, f'创建失败：{str(e)}')
    
    context = _context(
        "创建快递公司",
        "➕",
        "添加新的快递公司",
        request=request,
    )
    context["module_sidebar_nav"] = module_sidebar_nav
    context["delivery_sidebar_nav"] = module_sidebar_nav  # 兼容旧模板
    return render(request, "delivery_customer/express_company_create.html", context)


@login_required
def express_company_detail(request, company_id):
    """快递公司详情"""
    from django.shortcuts import get_object_or_404
    from backend.apps.delivery_customer.models import ExpressCompany, DeliveryRecord
    
    permission_set = get_user_permission_codes(request.user)
    module_sidebar_nav = _build_delivery_sidebar_nav(permission_set, request.path)
    delivery_sidebar_nav = module_sidebar_nav  # 兼容旧模板
    
    company = get_object_or_404(ExpressCompany, id=company_id)
    
    # 统计使用次数
    usage_count = DeliveryRecord.objects.filter(express_company=company.name).count()
    
    context = _context(
        "快递公司详情",
        "🚚",
        "查看快递公司详细信息",
        request=request,
    )
    context["module_sidebar_nav"] = module_sidebar_nav
    context["delivery_sidebar_nav"] = module_sidebar_nav  # 兼容旧模板
    context["company"] = company
    context["usage_count"] = usage_count
    context["can_edit"] = _permission_granted('delivery_center.create', permission_set)
    return render(request, "delivery_customer/express_company_detail.html", context)


@login_required
def express_company_edit(request, company_id):
    """快递公司编辑"""
    from django.shortcuts import redirect, get_object_or_404
    from django.contrib import messages
    from backend.apps.delivery_customer.models import ExpressCompany
    
    permission_set = get_user_permission_codes(request.user)
    module_sidebar_nav = _build_delivery_sidebar_nav(permission_set, request.path)
    delivery_sidebar_nav = module_sidebar_nav  # 兼容旧模板
    
    if not _permission_granted('delivery_center.create', permission_set):
        messages.error(request, '您没有编辑快递公司的权限')
        return redirect('delivery_pages:express_company_list')
    
    company = get_object_or_404(ExpressCompany, id=company_id)
    
    if request.method == 'POST':
        try:
            name = request.POST.get('name', '').strip()
            if not name:
                messages.error(request, '快递公司名称不能为空')
            elif ExpressCompany.objects.filter(name=name).exclude(id=company.id).exists():
                messages.error(request, f'快递公司"{name}"已存在')
            else:
                company.name = name
                company.code = request.POST.get('code', '').strip()
                company.alias = request.POST.get('alias', '').strip()
                company.contact_phone = request.POST.get('contact_phone', '').strip()
                company.contact_email = request.POST.get('contact_email', '').strip()
                company.website = request.POST.get('website', '').strip()
                company.is_active = request.POST.get('is_active') == 'on'
                is_default = request.POST.get('is_default') == 'on'
                company.sort_order = int(request.POST.get('sort_order', 0) or 0)
                company.notes = request.POST.get('notes', '').strip()
                company.save()
                
                # 如果设为默认，取消其他默认设置
                if is_default and not company.is_default:
                    ExpressCompany.objects.filter(is_default=True).exclude(id=company.id).update(is_default=False)
                    company.is_default = True
                    company.save()
                elif not is_default and company.is_default:
                    company.is_default = False
                    company.save()
                
                messages.success(request, f'快递公司"{name}"更新成功')
                return redirect('delivery_pages:express_company_detail', company_id=company.id)
        except Exception as e:
            logger.error(f"编辑快递公司失败: {str(e)}")
            messages.error(request, f'更新失败：{str(e)}')
    
    context = _context(
        "快递公司编辑",
        "✏️",
        "编辑快递公司信息",
        request=request,
    )
    context["module_sidebar_nav"] = module_sidebar_nav
    context["delivery_sidebar_nav"] = module_sidebar_nav  # 兼容旧模板
    context["company"] = company
    return render(request, "delivery_customer/express_company_edit.html", context)


@login_required
def express_company_delete(request, company_id):
    """快递公司删除"""
    from django.shortcuts import redirect, get_object_or_404
    from django.contrib import messages
    from backend.apps.delivery_customer.models import ExpressCompany, DeliveryRecord
    
    permission_set = get_user_permission_codes(request.user)
    
    if not _permission_granted('delivery_center.create', permission_set):
        messages.error(request, '您没有删除快递公司的权限')
        return redirect('delivery_pages:express_company_list')
    
    company = get_object_or_404(ExpressCompany, id=company_id)
    
    # 检查是否被使用
    usage_count = DeliveryRecord.objects.filter(express_company=company.name).count()
    if usage_count > 0:
        messages.error(request, f'无法删除：该快递公司已被 {usage_count} 条交付记录使用')
        return redirect('delivery_pages:express_company_detail', company_id=company.id)
    
    company_name = company.name
    company.delete()
    messages.success(request, f'快递公司"{company_name}"已删除')
    return redirect('delivery_pages:express_company_list')


