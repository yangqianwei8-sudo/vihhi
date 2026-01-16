import json

from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.shortcuts import render, redirect, get_object_or_404
from django.urls import reverse
from django.utils import timezone
from django.http import HttpResponse
from reportlab.lib.pagesizes import A4
from reportlab.lib.units import mm
from reportlab.pdfgen import canvas

from backend.apps.system_management.services import user_has_permission

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


@login_required
def standard_list(request):
    if not _require_permission(request, RESOURCE_PERMISSIONS["standard"]):
        return redirect("home")

    standards = Standard.objects.select_related("created_by", "updated_by").prefetch_related("editable_roles")
    return render(request, "resource_standard/standard_list.html", {
        "standards": standards,
    })


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

    return render(request, "resource_standard/standard_form.html", {
        "form": form,
        "items_formset": items_formset,
        "mode": "create",
    })


@login_required
def standard_detail(request, pk):
    if not _require_permission(request, RESOURCE_PERMISSIONS["standard"]):
        return redirect("home")
    standard = get_object_or_404(
        Standard.objects.prefetch_related("review_items"),
        pk=pk,
    )
    return render(request, "resource_standard/standard_detail.html", {
        "standard": standard,
    })


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

    return render(request, "resource_standard/standard_form.html", {
        "form": form,
        "items_formset": items_formset,
        "mode": "edit",
        "standard": standard,
    })


@login_required
def material_price_list(request):
    if not _require_permission(request, RESOURCE_PERMISSIONS["material"]):
        return redirect("home")
    materials = MaterialPrice.objects.all()
    return render(request, "resource_standard/material_price_list.html", {
        "materials": materials,
    })


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

    return render(request, "resource_standard/material_price_form.html", {
        "form": form,
        "mode": "create",
    })


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

    return render(request, "resource_standard/material_price_form.html", {
        "form": form,
        "mode": "edit",
        "material": material,
    })


@login_required
def cost_indicator_list(request):
    if not _require_permission(request, RESOURCE_PERMISSIONS["cost"]):
        return redirect("home")
    indicators = CostIndicator.objects.all()
    return render(request, "resource_standard/cost_indicator_list.html", {
        "indicators": indicators,
    })


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

    return render(request, "resource_standard/cost_indicator_form.html", {
        "form": form,
        "mode": "create",
    })


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

    return render(request, "resource_standard/cost_indicator_form.html", {
        "form": form,
        "mode": "edit",
        "indicator": indicator,
    })


@login_required
def report_template_list(request):
    if not _require_permission(request, RESOURCE_PERMISSIONS["template"]):
        return redirect("home")
    templates = ReportTemplate.objects.all()
    return render(request, "resource_standard/report_template_list.html", {
        "templates": templates,
    })


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

    return render(request, "resource_standard/report_template_form.html", {
        "form": form,
        "mode": "create",
    })


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

    return render(request, "resource_standard/report_template_form.html", {
        "form": form,
        "mode": "edit",
        "template_obj": template,
        "histories": template.history.all(),
    })


@login_required
def opinion_template_list(request):
    if not _require_permission(request, RESOURCE_PERMISSIONS["template"]):
        return redirect("home")
    templates = OpinionTemplate.objects.prefetch_related("default_review_points__standard")
    return render(request, "resource_standard/opinion_template_list.html", {
        "templates": templates,
    })


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

    return render(request, "resource_standard/opinion_template_form.html", {
        "form": form,
        "mode": "create",
    })


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

    return render(request, "resource_standard/opinion_template_form.html", {
        "form": form,
        "mode": "edit",
        "template_obj": template,
        "histories": template.history.all(),
    })


@login_required
def knowledge_tag_list(request):
    if not _require_permission(request, RESOURCE_PERMISSIONS["knowledge"]):
        return redirect("home")
    tags = KnowledgeTag.objects.all()
    return render(request, "resource_standard/knowledge_tag_list.html", {"tags": tags})


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
    return render(request, "resource_standard/knowledge_tag_form.html", {"form": form})


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
    return render(request, "resource_standard/knowledge_tag_form.html", {"form": form, "tag": tag})


@login_required
def risk_case_list(request):
    if not _require_permission(request, RESOURCE_PERMISSIONS["knowledge"]):
        return redirect("home")
    cases = RiskCase.objects.select_related("project")
    return render(request, "resource_standard/risk_case_list.html", {"cases": cases})


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
    return render(request, "resource_standard/risk_case_form.html", {"form": form, "mode": "create"})


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
    return render(request, "resource_standard/risk_case_form.html", {"form": form, "mode": "edit", "case": case})


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
    return render(request, "resource_standard/technical_solution_list.html", {"solutions": solutions})


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
    return render(request, "resource_standard/technical_solution_form.html", {"form": form, "mode": "create"})


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
    return render(request, "resource_standard/technical_solution_form.html", {"form": form, "mode": "edit", "solution": solution})


@login_required
def professional_category_list(request):
    if not _require_permission(request, RESOURCE_PERMISSIONS["maintenance"]):
        return redirect("home")
    categories = ProfessionalCategory.objects.prefetch_related("data_permissions", "operation_permissions")
    return render(request, "resource_standard/professional_category_list.html", {"categories": categories})


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
    return render(request, "resource_standard/professional_category_form.html", {"form": form, "mode": "create"})


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
    return render(request, "resource_standard/professional_category_form.html", {"form": form, "mode": "edit", "category": category})


@login_required
def system_parameter_list(request):
    if not _require_permission(request, RESOURCE_PERMISSIONS["maintenance"]):
        return redirect("home")
    params = SystemParameter.objects.all()
    return render(request, "resource_standard/system_parameter_list.html", {"params": params})


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
    return render(request, "resource_standard/system_parameter_form.html", {"form": form, "mode": "create"})


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
    return render(request, "resource_standard/system_parameter_form.html", {"form": form, "mode": "edit", "param": param})
