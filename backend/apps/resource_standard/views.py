import json

from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.shortcuts import render, redirect, get_object_or_404
from django.urls import reverse, NoReverseMatch
from django.utils import timezone
from django.http import HttpResponse
from reportlab.lib.pagesizes import A4
from reportlab.lib.units import mm
from reportlab.pdfgen import canvas

from backend.apps.system_management.services import user_has_permission, get_user_permission_codes

# 导入菜单构建函数
try:
    from backend.core.views import _build_unified_sidebar_nav, _build_full_top_nav
except ImportError:
    # Fallback: 如果 _build_unified_sidebar_nav 不存在，提供简单实现
    from backend.core.views import _permission_granted, _build_full_top_nav
    
    def _build_unified_sidebar_nav(menu_structure, permission_set, active_id=None):
        """Fallback: 简单的侧边栏菜单构建函数（支持 url_name 转换）"""
        nav = []
        for item in menu_structure:
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
                'id': item.get('id'),
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
                        'id': child.get('id'),
                        'label': child.get('label', ''),
                        'icon': child.get('icon', ''),
                        'url': child_url,
                        'active': child.get('id') == active_id if active_id else False,
                    })
                
                if children:
                    nav_item['children'] = children
                    # 如果父菜单没有 url，使用第一个子菜单的 URL
                    if nav_item['url'] == '#':
                        nav_item['url'] = children[0].get('url', '#')
                    # 如果任意子菜单激活，父菜单也激活
                    if any(child.get('active') for child in children):
                        nav_item['active'] = True
                        nav_item['expanded'] = True
            
            nav.append(nav_item)
        return nav

from .forms import (
    StandardForm,
    StandardReviewItemFormSet,
    MaterialPriceForm,
    CostIndicatorForm,
    ReportTemplateForm,
    OpinionTemplateForm,
    KnowledgeTagForm,
    RiskCaseForm,
    TechnicalSolutionForm,
    ProfessionalCategoryForm,
    SystemParameterForm,
)
from .models import (
    Standard,
    MaterialPrice,
    CostIndicator,
    ReportTemplate,
    ReportTemplateVersion,
    OpinionTemplate,
    OpinionTemplateVersion,
    KnowledgeTag,
    RiskCase,
    TechnicalSolution,
    ProfessionalCategory,
    SystemParameter,
)


RESOURCE_PERMISSIONS = {
    "standard": "resource_center.manage_library",
    "material": "resource_center.manage_library",
    "cost": "resource_center.manage_library",
    "template": "resource_center.manage_library",
    "knowledge": "resource_center.view",
    "maintenance": "resource_center.data_maintenance",
}

# ==================== 菜单结构定义 ====================

RESOURCE_MANAGEMENT_MENU_STRUCTURE = [
    {
        'id': 'standard',
        'label': '审查标准',
        'icon': '📋',
        'permission': 'resource_center.manage_library',
        'children': [
            {'id': 'standard_list', 'label': '标准列表', 'icon': '📋', 'url_name': 'resource_standard:standard_list', 'permission': 'resource_center.manage_library'},
            {'id': 'standard_create', 'label': '新建标准', 'icon': '➕', 'url_name': 'resource_standard:standard_create', 'permission': 'resource_center.manage_library'},
        ]
    },
    {
        'id': 'material',
        'label': '综合单价',
        'icon': '💰',
        'permission': 'resource_center.manage_library',
        'children': [
            {'id': 'material_price_list', 'label': '单价列表', 'icon': '💰', 'url_name': 'resource_standard:material_price_list', 'permission': 'resource_center.manage_library'},
            {'id': 'material_price_create', 'label': '新增单价', 'icon': '➕', 'url_name': 'resource_standard:material_price_create', 'permission': 'resource_center.manage_library'},
        ]
    },
    {
        'id': 'cost',
        'label': '成本指标',
        'icon': '📊',
        'permission': 'resource_center.manage_library',
        'children': [
            {'id': 'cost_indicator_list', 'label': '指标列表', 'icon': '📊', 'url_name': 'resource_standard:cost_indicator_list', 'permission': 'resource_center.manage_library'},
            {'id': 'cost_indicator_create', 'label': '新建指标', 'icon': '➕', 'url_name': 'resource_standard:cost_indicator_create', 'permission': 'resource_center.manage_library'},
        ]
    },
    {
        'id': 'template',
        'label': '报告模板',
        'icon': '📄',
        'permission': 'resource_center.manage_library',
        'children': [
            {'id': 'report_template_list', 'label': '报告模板', 'icon': '📄', 'url_name': 'resource_standard:report_template_list', 'permission': 'resource_center.manage_library'},
            {'id': 'report_template_create', 'label': '新建模板', 'icon': '➕', 'url_name': 'resource_standard:report_template_create', 'permission': 'resource_center.manage_library'},
            {'id': 'opinion_template_list', 'label': '意见书模板', 'icon': '📝', 'url_name': 'resource_standard:opinion_template_list', 'permission': 'resource_center.manage_library'},
            {'id': 'opinion_template_create', 'label': '新建意见书', 'icon': '➕', 'url_name': 'resource_standard:opinion_template_create', 'permission': 'resource_center.manage_library'},
        ]
    },
    {
        'id': 'knowledge',
        'label': '知识库',
        'icon': '📚',
        'permission': 'resource_center.view',
        'children': [
            {'id': 'knowledge_tag_list', 'label': '标签管理', 'icon': '🏷️', 'url_name': 'resource_standard:knowledge_tag_list', 'permission': 'resource_center.view'},
            {'id': 'knowledge_tag_create', 'label': '新建标签', 'icon': '➕', 'url_name': 'resource_standard:knowledge_tag_create', 'permission': 'resource_center.view'},
            {'id': 'risk_case_list', 'label': '风险案例', 'icon': '⚠️', 'url_name': 'resource_standard:risk_case_list', 'permission': 'resource_center.view'},
            {'id': 'risk_case_create', 'label': '新建案例', 'icon': '➕', 'url_name': 'resource_standard:risk_case_create', 'permission': 'resource_center.view'},
            {'id': 'technical_solution_list', 'label': '技术方案', 'icon': '💡', 'url_name': 'resource_standard:technical_solution_list', 'permission': 'resource_center.view'},
            {'id': 'technical_solution_create', 'label': '新建方案', 'icon': '➕', 'url_name': 'resource_standard:technical_solution_create', 'permission': 'resource_center.view'},
        ]
    },
    {
        'id': 'maintenance',
        'label': '数据维护',
        'icon': '⚙️',
        'permission': 'resource_center.data_maintenance',
        'children': [
            {'id': 'professional_category_list', 'label': '专业分类', 'icon': '📁', 'url_name': 'resource_standard:professional_category_list', 'permission': 'resource_center.data_maintenance'},
            {'id': 'professional_category_create', 'label': '新建分类', 'icon': '➕', 'url_name': 'resource_standard:professional_category_create', 'permission': 'resource_center.data_maintenance'},
            {'id': 'system_parameter_list', 'label': '系统参数', 'icon': '🔧', 'url_name': 'resource_standard:system_parameter_list', 'permission': 'resource_center.data_maintenance'},
            {'id': 'system_parameter_create', 'label': '新建参数', 'icon': '➕', 'url_name': 'resource_standard:system_parameter_create', 'permission': 'resource_center.data_maintenance'},
        ]
    },
]


# ==================== 菜单生成函数 ====================

def _build_resource_sidebar_nav(permission_set, request_path=None, active_id=None):
    """生成资源管理左侧菜单（统一格式）"""
    return _build_unified_sidebar_nav(RESOURCE_MANAGEMENT_MENU_STRUCTURE, permission_set, active_id=active_id)


def _require_permission(request, code):
    if user_has_permission(request.user, code) or request.user.is_superuser:
        return True
    messages.error(request, "您没有权限执行此操作。")
    return False


def _wrap_text(text, max_chars=60):
    if not text:
        return []
    text = str(text).replace('\r', '').strip()
    lines = []
    while text:
        lines.append(text[:max_chars])
        text = text[max_chars:]
    return lines


def _get_resource_context(request, active_id=None):
    """获取资源管理模块的通用上下文"""
    context = {}
    if request and request.user.is_authenticated:
        permission_set = get_user_permission_codes(request.user)
        context['resource_sidebar_nav'] = _build_resource_sidebar_nav(permission_set, request.path, active_id=active_id)
        context['module_sidebar_nav'] = _build_resource_sidebar_nav(permission_set, request.path, active_id=active_id)
        context['sidebar_title'] = '资源管理'
        context['sidebar_subtitle'] = 'Resource Management'
        try:
            context['full_top_nav'] = _build_full_top_nav(permission_set, request.user)
        except Exception:
            context['full_top_nav'] = []
    else:
        context['resource_sidebar_nav'] = []
        context['module_sidebar_nav'] = []
        context['sidebar_title'] = '资源管理'
        context['sidebar_subtitle'] = 'Resource Management'
        context['full_top_nav'] = []
    return context


@login_required
def standard_list(request):
    if not _require_permission(request, RESOURCE_PERMISSIONS["standard"]):
        return redirect("home")

    standards = Standard.objects.select_related("created_by", "updated_by").prefetch_related("editable_roles")
    context = _get_resource_context(request, active_id='standard_list')
    context.update({
        "standards": standards,
    })
    return render(request, "resource_standard/standard_list.html", context)


@login_required
def standard_create(request):
    if not _require_permission(request, RESOURCE_PERMISSIONS["standard"]):
        return redirect("home")

    if request.method == "POST":
        form = StandardForm(request.POST)
        items_formset = StandardReviewItemFormSet(request.POST)
        if form.is_valid() and items_formset.is_valid():
            standard = form.save(commit=False)
            standard.created_by = request.user
            standard.updated_by = request.user
            standard.save()
            form.save_m2m()
            items_formset.instance = standard
            items_formset.save()
            messages.success(request, "标准创建成功")
            return redirect(reverse("resource_standard:standard_detail", args=[standard.pk]))
    else:
        form = StandardForm()
        items_formset = StandardReviewItemFormSet()

    context = _get_resource_context(request, active_id='standard_create')
    context.update({
        "form": form,
        "items_formset": items_formset,
        "mode": "create",
    })
    return render(request, "resource_standard/standard_form.html", context)


@login_required
def standard_detail(request, pk):
    if not _require_permission(request, RESOURCE_PERMISSIONS["standard"]):
        return redirect("home")
    standard = get_object_or_404(
        Standard.objects.prefetch_related("review_items"),
        pk=pk,
    )
    context = _get_resource_context(request, active_id='standard_list')
    context.update({
        "standard": standard,
    })
    return render(request, "resource_standard/standard_detail.html", context)


@login_required
def standard_edit(request, pk):
    if not _require_permission(request, RESOURCE_PERMISSIONS["standard"]):
        return redirect("home")
    standard = get_object_or_404(Standard, pk=pk)

    if request.method == "POST":
        form = StandardForm(request.POST, instance=standard)
        items_formset = StandardReviewItemFormSet(request.POST, instance=standard)
        if form.is_valid() and items_formset.is_valid():
            standard = form.save(commit=False)
            standard.updated_by = request.user
            standard.save()
            form.save_m2m()
            items_formset.save()
            messages.success(request, "标准更新成功")
            return redirect(reverse("resource_standard:standard_detail", args=[standard.pk]))
    else:
        form = StandardForm(instance=standard)
        items_formset = StandardReviewItemFormSet(instance=standard)

    context = _get_resource_context(request, active_id='standard_list')
    context.update({
        "form": form,
        "items_formset": items_formset,
        "mode": "edit",
        "standard": standard,
    })
    return render(request, "resource_standard/standard_form.html", context)


@login_required
def material_price_list(request):
    if not _require_permission(request, RESOURCE_PERMISSIONS["material"]):
        return redirect("home")
    materials = MaterialPrice.objects.all()
    context = _get_resource_context(request, active_id='material_price_list')
    context.update({
        "materials": materials,
    })
    return render(request, "resource_standard/material_price_list.html", context)


@login_required
def material_price_create(request):
    if not _require_permission(request, RESOURCE_PERMISSIONS["material"]):
        return redirect("home")
    if request.method == "POST":
        form = MaterialPriceForm(request.POST)
        if form.is_valid():
            material = form.save(commit=False)
            material.changed_by = request.user
            material.save()
            messages.success(request, "综合单价创建成功")
            return redirect(reverse("resource_standard:material_price_list"))
    else:
        form = MaterialPriceForm()

    context = _get_resource_context(request, active_id='material_price_create')
    context.update({
        "form": form,
        "mode": "create",
    })
    return render(request, "resource_standard/material_price_form.html", context)


@login_required
def material_price_edit(request, pk):
    if not _require_permission(request, RESOURCE_PERMISSIONS["material"]):
        return redirect("home")
    material = get_object_or_404(MaterialPrice, pk=pk)
    if request.method == "POST":
        form = MaterialPriceForm(request.POST, instance=material)
        if form.is_valid():
            material = form.save(commit=False)
            material.changed_by = request.user
            material.version += 1
            material.changed_time = timezone.now()
            material.save()
            messages.success(request, "综合单价更新成功")
            return redirect(reverse("resource_standard:material_price_list"))
    else:
        form = MaterialPriceForm(instance=material)

    context = _get_resource_context(request, active_id='material_price_list')
    context.update({
        "form": form,
        "mode": "edit",
        "material": material,
    })
    return render(request, "resource_standard/material_price_form.html", context)


@login_required
def cost_indicator_list(request):
    if not _require_permission(request, RESOURCE_PERMISSIONS["cost"]):
        return redirect("home")
    indicators = CostIndicator.objects.all()
    context = _get_resource_context(request, active_id='cost_indicator_list')
    context.update({
        "indicators": indicators,
    })
    return render(request, "resource_standard/cost_indicator_list.html", context)


@login_required
def cost_indicator_create(request):
    if not _require_permission(request, RESOURCE_PERMISSIONS["cost"]):
        return redirect("home")
    if request.method == "POST":
        form = CostIndicatorForm(request.POST)
        if form.is_valid():
            indicator = form.save(commit=False)
            indicator.created_by = request.user
            indicator.save()
            messages.success(request, "成本指标创建成功")
            return redirect(reverse("resource_standard:cost_indicator_list"))
    else:
        form = CostIndicatorForm()

    context = _get_resource_context(request, active_id='cost_indicator_create')
    context.update({
        "form": form,
        "mode": "create",
    })
    return render(request, "resource_standard/cost_indicator_form.html", context)


@login_required
def cost_indicator_edit(request, pk):
    if not _require_permission(request, RESOURCE_PERMISSIONS["cost"]):
        return redirect("home")
    indicator = get_object_or_404(CostIndicator, pk=pk)
    if request.method == "POST":
        form = CostIndicatorForm(request.POST, instance=indicator)
        if form.is_valid():
            indicator = form.save()
            messages.success(request, "成本指标更新成功")
            return redirect(reverse("resource_standard:cost_indicator_list"))
    else:
        form = CostIndicatorForm(instance=indicator)

    context = _get_resource_context(request, active_id='cost_indicator_list')
    context.update({
        "form": form,
        "mode": "edit",
        "indicator": indicator,
    })
    return render(request, "resource_standard/cost_indicator_form.html", context)


@login_required
def report_template_list(request):
    if not _require_permission(request, RESOURCE_PERMISSIONS["template"]):
        return redirect("home")
    templates = ReportTemplate.objects.all()
    context = _get_resource_context(request, active_id='report_template_list')
    context.update({
        "templates": templates,
    })
    return render(request, "resource_standard/report_template_list.html", context)


@login_required
def report_template_create(request):
    if not _require_permission(request, RESOURCE_PERMISSIONS["template"]):
        return redirect("home")
    if request.method == "POST":
        form = ReportTemplateForm(request.POST)
        change_note = request.POST.get("change_note", "初始创建")
        if form.is_valid():
            template = form.save(commit=False)
            template.created_by = request.user
            template.save()
            form.save_m2m()
            ReportTemplateVersion.objects.create(
                template=template,
                version=template.version,
                cover_content=template.cover_content,
                header_footer=template.header_footer,
                sections=template.sections,
                styles=template.styles,
                change_note=change_note,
            )
            messages.success(request, "报告模板创建成功")
            return redirect(reverse("resource_standard:report_template_list"))
    else:
        form = ReportTemplateForm()

    context = _get_resource_context(request, active_id='report_template_create')
    context.update({
        "form": form,
        "mode": "create",
    })
    return render(request, "resource_standard/report_template_form.html", context)


@login_required
def report_template_edit(request, pk):
    if not _require_permission(request, RESOURCE_PERMISSIONS["template"]):
        return redirect("home")
    template = get_object_or_404(ReportTemplate, pk=pk)
    if request.method == "POST":
        form = ReportTemplateForm(request.POST, instance=template)
        change_note = request.POST.get("change_note", "版本更新")
        if form.is_valid():
            template = form.save(commit=False)
            template.version += 1
            template.updated_time = timezone.now()
            template.save()
            form.save_m2m()
            ReportTemplateVersion.objects.create(
                template=template,
                version=template.version,
                cover_content=template.cover_content,
                header_footer=template.header_footer,
                sections=template.sections,
                styles=template.styles,
                change_note=change_note,
            )
            messages.success(request, "报告模板更新成功")
            return redirect(reverse("resource_standard:report_template_list"))
    else:
        form = ReportTemplateForm(instance=template)
        form.initial["header_footer"] = json.dumps(template.header_footer, ensure_ascii=False, indent=2)
        form.initial["sections"] = json.dumps(template.sections, ensure_ascii=False, indent=2)
        form.initial["styles"] = json.dumps(template.styles, ensure_ascii=False, indent=2)

    context = _get_resource_context(request, active_id='report_template_list')
    context.update({
        "form": form,
        "mode": "edit",
        "template_obj": template,
        "histories": template.history.all(),
    })
    return render(request, "resource_standard/report_template_form.html", context)


@login_required
def opinion_template_list(request):
    if not _require_permission(request, RESOURCE_PERMISSIONS["template"]):
        return redirect("home")
    templates = OpinionTemplate.objects.prefetch_related("default_review_points__standard")
    context = _get_resource_context(request, active_id='opinion_template_list')
    context.update({
        "templates": templates,
    })
    return render(request, "resource_standard/opinion_template_list.html", context)


@login_required
def opinion_template_create(request):
    if not _require_permission(request, RESOURCE_PERMISSIONS["template"]):
        return redirect("home")
    if request.method == "POST":
        form = OpinionTemplateForm(request.POST)
        change_note = request.POST.get("change_note", "初始创建")
        if form.is_valid():
            template = form.save(commit=False)
            template.created_by = request.user
            template.save()
            form.save_m2m()
            OpinionTemplateVersion.objects.create(
                template=template,
                version=template.version,
                auto_fields=template.auto_fields,
                category_templates=template.category_templates,
                calculation_rules=template.calculation_rules,
                change_note=change_note,
            )
            messages.success(request, "意见书模板创建成功")
            return redirect(reverse("resource_standard:opinion_template_list"))
    else:
        form = OpinionTemplateForm()

    context = _get_resource_context(request, active_id='opinion_template_create')
    context.update({
        "form": form,
        "mode": "create",
    })
    return render(request, "resource_standard/opinion_template_form.html", context)


@login_required
def opinion_template_edit(request, pk):
    if not _require_permission(request, RESOURCE_PERMISSIONS["template"]):
        return redirect("home")
    template = get_object_or_404(OpinionTemplate, pk=pk)
    if request.method == "POST":
        form = OpinionTemplateForm(request.POST, instance=template)
        change_note = request.POST.get("change_note", "版本更新")
        if form.is_valid():
            template = form.save(commit=False)
            template.version += 1
            template.updated_time = timezone.now()
            template.save()
            form.save_m2m()
            OpinionTemplateVersion.objects.create(
                template=template,
                version=template.version,
                auto_fields=template.auto_fields,
                category_templates=template.category_templates,
                calculation_rules=template.calculation_rules,
                change_note=change_note,
            )
            messages.success(request, "意见书模板更新成功")
            return redirect(reverse("resource_standard:opinion_template_list"))
    else:
        form = OpinionTemplateForm(instance=template)
        form.initial["auto_fields"] = json.dumps(template.auto_fields, ensure_ascii=False, indent=2)
        form.initial["category_templates"] = json.dumps(template.category_templates, ensure_ascii=False, indent=2)
        form.initial["calculation_rules"] = json.dumps(template.calculation_rules, ensure_ascii=False, indent=2)

    context = _get_resource_context(request, active_id='opinion_template_list')
    context.update({
        "form": form,
        "mode": "edit",
        "template_obj": template,
        "histories": template.history.all(),
    })
    return render(request, "resource_standard/opinion_template_form.html", context)


@login_required
def knowledge_tag_list(request):
    if not _require_permission(request, RESOURCE_PERMISSIONS["knowledge"]):
        return redirect("home")
    tags = KnowledgeTag.objects.all()
    context = _get_resource_context(request, active_id='knowledge_tag_list')
    context.update({"tags": tags})
    return render(request, "resource_standard/knowledge_tag_list.html", context)


@login_required
def knowledge_tag_create(request):
    if not _require_permission(request, RESOURCE_PERMISSIONS["knowledge"]):
        return redirect("home")
    if request.method == "POST":
        form = KnowledgeTagForm(request.POST)
        if form.is_valid():
            form.save()
            messages.success(request, "标签创建成功")
            return redirect("resource_standard:knowledge_tag_list")
    else:
        form = KnowledgeTagForm()
    context = _get_resource_context(request, active_id='knowledge_tag_create')
    context.update({"form": form})
    return render(request, "resource_standard/knowledge_tag_form.html", context)


@login_required
def knowledge_tag_edit(request, pk):
    if not _require_permission(request, RESOURCE_PERMISSIONS["knowledge"]):
        return redirect("home")
    tag = get_object_or_404(KnowledgeTag, pk=pk)
    if request.method == "POST":
        form = KnowledgeTagForm(request.POST, instance=tag)
        if form.is_valid():
            form.save()
            messages.success(request, "标签更新成功")
            return redirect("resource_standard:knowledge_tag_list")
    else:
        form = KnowledgeTagForm(instance=tag)
    context = _get_resource_context(request, active_id='knowledge_tag_list')
    context.update({"form": form, "tag": tag})
    return render(request, "resource_standard/knowledge_tag_form.html", context)


@login_required
def risk_case_list(request):
    if not _require_permission(request, RESOURCE_PERMISSIONS["knowledge"]):
        return redirect("home")
    cases = RiskCase.objects.select_related("project")
    context = _get_resource_context(request, active_id='risk_case_list')
    context.update({"cases": cases})
    return render(request, "resource_standard/risk_case_list.html", context)


@login_required
def risk_case_create(request):
    if not _require_permission(request, RESOURCE_PERMISSIONS["knowledge"]):
        return redirect("home")
    if request.method == "POST":
        form = RiskCaseForm(request.POST)
        if form.is_valid():
            case = form.save(commit=False)
            case.created_by = request.user
            case.save()
            form.save_m2m()
            messages.success(request, "风险案例创建成功")
            return redirect("resource_standard:risk_case_list")
    else:
        form = RiskCaseForm()
    context = _get_resource_context(request, active_id='risk_case_create')
    context.update({"form": form, "mode": "create"})
    return render(request, "resource_standard/risk_case_form.html", context)


@login_required
def risk_case_edit(request, pk):
    if not _require_permission(request, RESOURCE_PERMISSIONS["knowledge"]):
        return redirect("home")
    case = get_object_or_404(RiskCase, pk=pk)
    if request.method == "POST":
        form = RiskCaseForm(request.POST, instance=case)
        if form.is_valid():
            form.save()
            messages.success(request, "风险案例更新成功")
            return redirect("resource_standard:risk_case_list")
    else:
        form = RiskCaseForm(instance=case)
    context = _get_resource_context(request, active_id='risk_case_list')
    context.update({"form": form, "mode": "edit", "case": case})
    return render(request, "resource_standard/risk_case_form.html", context)


@login_required
def risk_case_export(request):
    if not _require_permission(request, RESOURCE_PERMISSIONS["knowledge"]):
        return redirect("home")

    cases = RiskCase.objects.select_related("project").order_by("-occurred_on", "case_code")

    response = HttpResponse(content_type="application/pdf")
    filename = timezone.now().strftime("risk_cases_%Y%m%d_%H%M%S.pdf")
    response["Content-Disposition"] = f"attachment; filename=\"{filename}\""

    pdf = canvas.Canvas(response, pagesize=A4)
    width, height = A4
    margin_x = 20 * mm
    margin_y = 20 * mm
    y = height - margin_y

    pdf.setFont("Helvetica-Bold", 16)
    pdf.drawString(margin_x, y, "风险案例导出报表")
    y -= 10 * mm
    pdf.setFont("Helvetica", 10)
    pdf.drawString(margin_x, y, f"导出时间：{timezone.now().strftime('%Y-%m-%d %H:%M')}")
    y -= 8 * mm

    pdf.setFont("Helvetica", 10)
    for case in cases:
        if y < margin_y + 40:
            pdf.showPage()
            y = height - margin_y
            pdf.setFont("Helvetica", 10)

        pdf.setFont("Helvetica-Bold", 11)
        pdf.drawString(margin_x, y, f"[{case.case_code}] {case.title}")
        y -= 6 * mm

        pdf.setFont("Helvetica", 10)
        subtitle = f"类型：{case.get_case_type_display()}  项目：{case.project.name if case.project else '—'}  时间：{case.occurred_on or '—'}"
        pdf.drawString(margin_x, y, subtitle)
        y -= 6 * mm

        for label, content in (
            ("风险描述", case.risk_description),
            ("根本原因", case.root_cause),
            ("影响评估", case.impact_scope),
            ("应对措施", case.counter_measure),
            ("预防措施", case.prevention),
            ("经验教训", case.lessons),
        ):
            lines = _wrap_text(content, max_chars=70)
            if lines:
                pdf.setFont("Helvetica-Bold", 9)
                pdf.drawString(margin_x, y, f"{label}：")
                y -= 5 * mm
                pdf.setFont("Helvetica", 9)
                for line in lines:
                    if y < margin_y + 20:
                        pdf.showPage()
                        y = height - margin_y
                        pdf.setFont("Helvetica", 9)
                    pdf.drawString(margin_x + 8 * mm, y, line)
                    y -= 4.5 * mm
            else:
                pdf.setFont("Helvetica-Bold", 9)
                pdf.drawString(margin_x, y, f"{label}：—")
                y -= 5 * mm

        y -= 3 * mm
        pdf.line(margin_x, y, width - margin_x, y)
        y -= 6 * mm

    pdf.save()
    return response


@login_required
def technical_solution_list(request):
    if not _require_permission(request, RESOURCE_PERMISSIONS["knowledge"]):
        return redirect("home")
    solutions = TechnicalSolution.objects.prefetch_related("tags")
    context = _get_resource_context(request, active_id='technical_solution_list')
    context.update({"solutions": solutions})
    return render(request, "resource_standard/technical_solution_list.html", context)


@login_required
def technical_solution_create(request):
    if not _require_permission(request, RESOURCE_PERMISSIONS["knowledge"]):
        return redirect("home")
    if request.method == "POST":
        form = TechnicalSolutionForm(request.POST, request.FILES)
        if form.is_valid():
            solution = form.save(commit=False)
            solution.created_by = request.user
            solution.save()
            form.save_m2m()
            messages.success(request, "技术解决方案创建成功")
            return redirect("resource_standard:technical_solution_list")
    else:
        form = TechnicalSolutionForm()
    context = _get_resource_context(request, active_id='technical_solution_create')
    context.update({"form": form, "mode": "create"})
    return render(request, "resource_standard/technical_solution_form.html", context)


@login_required
def technical_solution_edit(request, pk):
    if not _require_permission(request, RESOURCE_PERMISSIONS["knowledge"]):
        return redirect("home")
    solution = get_object_or_404(TechnicalSolution, pk=pk)
    if request.method == "POST":
        form = TechnicalSolutionForm(request.POST, request.FILES, instance=solution)
        if form.is_valid():
            form.save()
            messages.success(request, "技术解决方案更新成功")
            return redirect("resource_standard:technical_solution_list")
    else:
        form = TechnicalSolutionForm(instance=solution)
    context = _get_resource_context(request, active_id='technical_solution_list')
    context.update({"form": form, "mode": "edit", "solution": solution})
    return render(request, "resource_standard/technical_solution_form.html", context)


@login_required
def professional_category_list(request):
    if not _require_permission(request, RESOURCE_PERMISSIONS["maintenance"]):
        return redirect("home")
    categories = ProfessionalCategory.objects.prefetch_related("data_permissions", "operation_permissions")
    context = _get_resource_context(request, active_id='professional_category_list')
    context.update({"categories": categories})
    return render(request, "resource_standard/professional_category_list.html", context)


@login_required
def professional_category_create(request):
    if not _require_permission(request, RESOURCE_PERMISSIONS["maintenance"]):
        return redirect("home")
    if request.method == "POST":
        form = ProfessionalCategoryForm(request.POST)
        if form.is_valid():
            form.save()
            messages.success(request, "专业分类创建成功")
            return redirect("resource_standard:professional_category_list")
    else:
        form = ProfessionalCategoryForm()
    context = _get_resource_context(request, active_id='professional_category_create')
    context.update({"form": form, "mode": "create"})
    return render(request, "resource_standard/professional_category_form.html", context)


@login_required
def professional_category_edit(request, pk):
    if not _require_permission(request, RESOURCE_PERMISSIONS["maintenance"]):
        return redirect("home")
    category = get_object_or_404(ProfessionalCategory, pk=pk)
    if request.method == "POST":
        form = ProfessionalCategoryForm(request.POST, instance=category)
        if form.is_valid():
            form.save()
            messages.success(request, "专业分类更新成功")
            return redirect("resource_standard:professional_category_list")
    else:
        form = ProfessionalCategoryForm(instance=category)
    context = _get_resource_context(request, active_id='professional_category_list')
    context.update({"form": form, "mode": "edit", "category": category})
    return render(request, "resource_standard/professional_category_form.html", context)


@login_required
def system_parameter_list(request):
    if not _require_permission(request, RESOURCE_PERMISSIONS["maintenance"]):
        return redirect("home")
    params = SystemParameter.objects.all()
    context = _get_resource_context(request, active_id='system_parameter_list')
    context.update({"params": params})
    return render(request, "resource_standard/system_parameter_list.html", context)


@login_required
def system_parameter_create(request):
    if not _require_permission(request, RESOURCE_PERMISSIONS["maintenance"]):
        return redirect("home")
    if request.method == "POST":
        form = SystemParameterForm(request.POST)
        if form.is_valid():
            form.save()
            messages.success(request, "系统参数创建成功")
            return redirect("resource_standard:system_parameter_list")
    else:
        form = SystemParameterForm()
    context = _get_resource_context(request, active_id='system_parameter_create')
    context.update({"form": form, "mode": "create"})
    return render(request, "resource_standard/system_parameter_form.html", context)


@login_required
def system_parameter_edit(request, pk):
    if not _require_permission(request, RESOURCE_PERMISSIONS["maintenance"]):
        return redirect("home")
    param = get_object_or_404(SystemParameter, pk=pk)
    if request.method == "POST":
        form = SystemParameterForm(request.POST, instance=param)
        if form.is_valid():
            form.save()
            messages.success(request, "系统参数更新成功")
            return redirect("resource_standard:system_parameter_list")
    else:
        form = SystemParameterForm(instance=param)
    context = _get_resource_context(request, active_id='system_parameter_list')
    context.update({"form": form, "mode": "edit", "param": param})
    return render(request, "resource_standard/system_parameter_form.html", context)
