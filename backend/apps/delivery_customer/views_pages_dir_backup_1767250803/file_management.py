"""
文件管理视图模块
包含文件分类和文件模板的维护功能
"""
import logging

from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.core.paginator import Paginator
from django.db.models import Q
from django.http import Http404, HttpResponseForbidden
from django.shortcuts import render, redirect, get_object_or_404
from django.urls import reverse

from backend.apps.delivery_customer.models import FileCategory, FileTemplate
from backend.apps.system_management.services import get_user_permission_codes
from backend.core.views import _permission_granted, _build_full_top_nav

from .common import _context, _build_delivery_sidebar_nav

logger = logging.getLogger(__name__)

# ==================== 文件分类维护 ====================

# 阶段配置映射
FILE_CATEGORY_STAGES = {
    'conversion': '转化阶段',
    'contract': '合同阶段',
    'production': '生产阶段',
    'settlement': '结算阶段',
    'payment': '回款阶段',
    'after_sales': '售后阶段',
    'litigation': '诉讼阶段',
}

@login_required
def file_category_manage(request):
    """文件分类维护 - 统一管理页面（包含阶段选择、列表和新增功能）"""
    permission_set = get_user_permission_codes(request.user)
    module_sidebar_nav = _build_delivery_sidebar_nav(permission_set, request.path)
    delivery_sidebar_nav = module_sidebar_nav  # 兼容旧模板
    
    if not _permission_granted('delivery_center.view', permission_set):
        return HttpResponseForbidden("无权限访问文件分类维护")
    
    # 获取选中的阶段（支持"全部"选项，默认为"全部"）
    selected_stage = request.GET.get('stage', 'all')
    show_all = False
    
    if selected_stage == 'all' or selected_stage == '':
        show_all = True
        selected_stage = 'all'
        stage_name = '全部阶段'
    elif selected_stage not in FILE_CATEGORY_STAGES:
        selected_stage = 'all'
        show_all = True
        stage_name = '全部阶段'
    else:
        stage_name = FILE_CATEGORY_STAGES[selected_stage]
    
    # 处理新增分类（POST请求）
    if request.method == 'POST' and _permission_granted('delivery_center.create', permission_set):
        try:
            # 分类名称从下拉选择获取（实际上是阶段代码）
            stage_code = request.POST.get('name', '').strip()
            category_name = request.POST.get('category_name', '').strip()
            
            if not stage_code or stage_code not in FILE_CATEGORY_STAGES:
                messages.error(request, '请选择阶段')
            elif not category_name:
                messages.error(request, '请输入分类名称')
            else:
                # 检查同一阶段内是否已存在同名分类
                if FileCategory.objects.filter(stage=stage_code, name=category_name).exists():
                    messages.error(request, f'该阶段已存在名为"{category_name}"的分类')
                else:
                    # 自动生成分类代码：阶段代码_序号（如：conversion_001）
                    stage_prefix = stage_code.upper()
                    # 获取该阶段已有的分类数量
                    existing_count = FileCategory.objects.filter(stage=stage_code).count()
                    # 生成代码：阶段代码_3位序号
                    category_code = f"{stage_prefix}_{existing_count + 1:03d}"
                    
                    # 确保代码唯一
                    while FileCategory.objects.filter(code=category_code).exists():
                        existing_count += 1
                        category_code = f"{stage_prefix}_{existing_count + 1:03d}"
                    
                    category = FileCategory(
                        name=category_name,
                        code=category_code,
                        stage=stage_code,
                        description=request.POST.get('description', '').strip(),
                        sort_order=int(request.POST.get('sort_order', 0) or 0),
                        is_active=request.POST.get('is_active') == 'on',
                        created_by=request.user,
                    )
                    category.save()
                    messages.success(request, f'文件分类"{category_name}"创建成功，代码：{category_code}')
                    # 刷新页面，显示新创建的分类
                    return redirect(f'{reverse("delivery_pages:file_category_manage")}?stage={stage_code}')
        except Exception as e:
            logger.error(f"创建文件分类失败: {str(e)}")
            messages.error(request, f'创建失败：{str(e)}')
    
    # 获取文件分类（如果选择"全部"则显示所有阶段）
    if show_all:
        queryset = FileCategory.objects.all().order_by('stage', 'sort_order', 'name')
    else:
        queryset = FileCategory.objects.filter(stage=selected_stage).order_by('sort_order', 'name')
    
    # 搜索功能
    search_keyword = request.GET.get('search', '').strip()
    if search_keyword:
        queryset = queryset.filter(
            Q(name__icontains=search_keyword) |
            Q(code__icontains=search_keyword) |
            Q(description__icontains=search_keyword)
        )
    
    # 状态筛选
    status_filter = request.GET.get('status', '')
    if status_filter == 'active':
        queryset = queryset.filter(is_active=True)
    elif status_filter == 'inactive':
        queryset = queryset.filter(is_active=False)
    
    # 分页
    paginator = Paginator(queryset, 20)
    page_num = request.GET.get('page', 1)
    try:
        page = paginator.get_page(page_num)
    except:
        page = paginator.get_page(1)
    
    context = _context(
        "创建文件分类",
        "➕",
        "管理各阶段的文件分类",
        request=request,
    )
    context["module_sidebar_nav"] = module_sidebar_nav
    context["delivery_sidebar_nav"] = module_sidebar_nav  # 兼容旧模板
    context["stage_code"] = selected_stage if not show_all else 'all'
    context["stage_name"] = stage_name
    context["show_all"] = show_all
    context["stages"] = FILE_CATEGORY_STAGES
    context["categories"] = page
    context["search_keyword"] = search_keyword
    context["status_filter"] = status_filter
    context["can_create"] = _permission_granted('delivery_center.create', permission_set)
    
    return render(request, "delivery_customer/file_category_manage.html", context)


@login_required
def file_category_list(request, stage_code):
    """文件分类维护 - 列表页（统一视图，通过stage_code参数区分阶段）"""
    if stage_code not in FILE_CATEGORY_STAGES:
        raise Http404("阶段不存在")
    
    stage_name = FILE_CATEGORY_STAGES[stage_code]
    
    permission_set = get_user_permission_codes(request.user)
    module_sidebar_nav = _build_delivery_sidebar_nav(permission_set, request.path)
    delivery_sidebar_nav = module_sidebar_nav  # 兼容旧模板
    
    if not _permission_granted('delivery_center.view', permission_set):
        return HttpResponseForbidden("无权限访问文件分类维护")
    
    # 获取该阶段的所有文件分类
    queryset = FileCategory.objects.filter(stage=stage_code).order_by('sort_order', 'name')
    
    # 搜索功能
    search_keyword = request.GET.get('search', '').strip()
    if search_keyword:
        queryset = queryset.filter(
            Q(name__icontains=search_keyword) |
            Q(code__icontains=search_keyword) |
            Q(description__icontains=search_keyword)
        )
    
    # 状态筛选
    status_filter = request.GET.get('status', '')
    if status_filter == 'active':
        queryset = queryset.filter(is_active=True)
    elif status_filter == 'inactive':
        queryset = queryset.filter(is_active=False)
    
    # 分页
    paginator = Paginator(queryset, 20)
    page_num = request.GET.get('page', 1)
    try:
        page = paginator.get_page(page_num)
    except:
        page = paginator.get_page(1)
    
    context = _context(
        f"文件分类维护 - {stage_name}",
        "📂",
        f"管理{stage_name}的文件分类",
        request=request,
    )
    context["module_sidebar_nav"] = module_sidebar_nav
    context["delivery_sidebar_nav"] = module_sidebar_nav  # 兼容旧模板
    context["stage_code"] = stage_code
    context["stage_name"] = stage_name
    context["categories"] = page
    context["search_keyword"] = search_keyword
    context["status_filter"] = status_filter
    context["can_create"] = _permission_granted('delivery_center.create', permission_set)
    
    return render(request, "delivery_customer/file_category_list.html", context)


@login_required
def file_category_create(request, stage_code):
    """文件分类维护 - 新增（统一视图，通过stage_code参数区分阶段）"""
    if stage_code not in FILE_CATEGORY_STAGES:
        raise Http404("阶段不存在")
    
    stage_name = FILE_CATEGORY_STAGES[stage_code]
    
    permission_set = get_user_permission_codes(request.user)
    module_sidebar_nav = _build_delivery_sidebar_nav(permission_set, request.path)
    delivery_sidebar_nav = module_sidebar_nav  # 兼容旧模板
    
    if not _permission_granted('delivery_center.create', permission_set):
        messages.error(request, '您没有创建文件分类的权限')
        return redirect('delivery_pages:file_category_list', stage_code=stage_code)
    
    if request.method == 'POST':
        try:
            name = request.POST.get('name', '').strip()
            if not name:
                messages.error(request, '分类名称不能为空')
            else:
                # 检查同一阶段内是否已存在同名分类
                if FileCategory.objects.filter(stage=stage_code, name=name).exists():
                    messages.error(request, f'该阶段已存在名为"{name}"的分类')
                else:
                    category = FileCategory(
                        name=name,
                        code=request.POST.get('code', '').strip(),
                        stage=stage_code,
                        description=request.POST.get('description', '').strip(),
                        sort_order=int(request.POST.get('sort_order', 0) or 0),
                        is_active=request.POST.get('is_active') == 'on',
                        created_by=request.user,
                    )
                    category.save()
                    messages.success(request, f'文件分类"{name}"创建成功')
                    return redirect('delivery_pages:file_category_list', stage_code=stage_code)
        except Exception as e:
            logger.error(f"创建文件分类失败: {str(e)}")
            messages.error(request, f'创建失败：{str(e)}')
    
    context = _context(
        f"新增文件分类 - {stage_name}",
        "➕",
        f"为{stage_name}新增文件分类",
        request=request,
    )
    context["module_sidebar_nav"] = module_sidebar_nav
    context["delivery_sidebar_nav"] = module_sidebar_nav  # 兼容旧模板
    context["stage_code"] = stage_code
    context["stage_name"] = stage_name
    
    return render(request, "delivery_customer/file_category_create.html", context)


# ==================== 文件模板维护 ====================

@login_required
def file_template_manage(request):
    """文件模板维护 - 统一管理页面（包含阶段选择、列表和新增功能）"""
    permission_set = get_user_permission_codes(request.user)
    module_sidebar_nav = _build_delivery_sidebar_nav(permission_set, request.path)
    delivery_sidebar_nav = module_sidebar_nav  # 兼容旧模板
    
    if not _permission_granted('delivery_center.view', permission_set):
        return HttpResponseForbidden("无权限访问文件模板维护")
    
    # 获取选中的阶段（支持"全部"选项，默认为"全部"）
    selected_stage = request.GET.get('stage', 'all')
    show_all = False
    
    if selected_stage == 'all' or selected_stage == '':
        show_all = True
        selected_stage = 'all'
        stage_name = '全部阶段'
    elif selected_stage not in FILE_CATEGORY_STAGES:
        selected_stage = 'all'
        show_all = True
        stage_name = '全部阶段'
    else:
        stage_name = FILE_CATEGORY_STAGES[selected_stage]
    
    # 处理新增模板（POST请求）
    if request.method == 'POST' and _permission_granted('delivery_center.create', permission_set):
        try:
            stage_code = request.POST.get('stage', '').strip()
            template_name = request.POST.get('template_name', '').strip()
            
            if not stage_code or stage_code not in FILE_CATEGORY_STAGES:
                messages.error(request, '请选择阶段')
            elif not template_name:
                messages.error(request, '请输入模板名称')
            else:
                # 检查同一阶段内是否已存在同名模板
                if FileTemplate.objects.filter(stage=stage_code, name=template_name).exists():
                    messages.error(request, f'该阶段已存在名为"{template_name}"的模板')
                else:
                    # 自动生成模板代码：阶段代码_序号（如：conversion_001）
                    stage_prefix = stage_code.upper()
                    # 获取该阶段已有的模板数量
                    existing_count = FileTemplate.objects.filter(stage=stage_code).count()
                    # 生成代码：阶段代码_3位序号
                    template_code = f"{stage_prefix}_TEMPLATE_{existing_count + 1:03d}"
                    
                    # 确保代码唯一
                    while FileTemplate.objects.filter(code=template_code).exists():
                        existing_count += 1
                        template_code = f"{stage_prefix}_TEMPLATE_{existing_count + 1:03d}"
                    
                    # 获取关联的分类（如果提供）
                    category_id = request.POST.get('category', '').strip()
                    category = None
                    if category_id:
                        try:
                            category = FileCategory.objects.get(id=category_id, stage=stage_code)
                        except FileCategory.DoesNotExist:
                            pass
                    
                    template = FileTemplate(
                        name=template_name,
                        code=template_code,
                        stage=stage_code,
                        category=category,
                        description=request.POST.get('description', '').strip(),
                        sort_order=int(request.POST.get('sort_order', 0) or 0),
                        is_active=request.POST.get('is_active') == 'on',
                        created_by=request.user,
                    )
                    
                    # 处理文件上传
                    if 'template_file' in request.FILES:
                        template.template_file = request.FILES['template_file']
                    
                    template.save()
                    messages.success(request, f'文件模板"{template_name}"创建成功，代码：{template_code}')
                    # 刷新页面，显示新创建的模板
                    return redirect(f'{reverse("delivery_pages:file_template_manage")}?stage={stage_code}')
        except Exception as e:
            logger.error(f"创建文件模板失败: {str(e)}")
            messages.error(request, f'创建失败：{str(e)}')
    
    # 获取文件模板（如果选择"全部"则显示所有阶段）
    if show_all:
        queryset = FileTemplate.objects.all().order_by('stage', 'sort_order', 'name')
    else:
        queryset = FileTemplate.objects.filter(stage=selected_stage).order_by('sort_order', 'name')
    
    # 搜索功能
    search_keyword = request.GET.get('search', '').strip()
    if search_keyword:
        queryset = queryset.filter(
            Q(name__icontains=search_keyword) |
            Q(code__icontains=search_keyword) |
            Q(description__icontains=search_keyword)
        )
    
    # 状态筛选
    status_filter = request.GET.get('status', '')
    if status_filter == 'active':
        queryset = queryset.filter(is_active=True)
    elif status_filter == 'inactive':
        queryset = queryset.filter(is_active=False)
    
    # 分页
    paginator = Paginator(queryset, 20)
    page_number = request.GET.get('page', 1)
    try:
        page = paginator.get_page(page_number)
    except:
        page = paginator.get_page(1)
    
    # 获取各阶段的文件分类（用于下拉选择）
    categories_by_stage = {}
    for stage_code in FILE_CATEGORY_STAGES.keys():
        categories_by_stage[stage_code] = FileCategory.objects.filter(
            stage=stage_code, 
            is_active=True
        ).order_by('sort_order', 'name')
    
    context = _context(
        "文件模板维护",
        "📄",
        "管理各阶段的文件模板",
        request=request,
    )
    context["module_sidebar_nav"] = module_sidebar_nav
    context["delivery_sidebar_nav"] = module_sidebar_nav  # 兼容旧模板
    context["stage_code"] = selected_stage if not show_all else 'all'
    context["stage_name"] = stage_name
    context["show_all"] = show_all
    context["stages"] = FILE_CATEGORY_STAGES
    context["templates"] = page
    context["search_keyword"] = search_keyword
    context["status_filter"] = status_filter
    context["can_create"] = _permission_granted('delivery_center.create', permission_set)
    context["categories_by_stage"] = categories_by_stage
    
    return render(request, "delivery_customer/file_template_manage.html", context)


