import json

from django import forms
from django.core.exceptions import ValidationError
from django.forms import inlineformset_factory

from .models import (
    Standard,
    StandardReviewItem,
    MaterialPrice,
    CostIndicator,
    ReportTemplate,
    OpinionTemplate,
    KnowledgeTag,
    RiskCase,
    TechnicalSolution,
    ProfessionalCategory,
    SystemParameter,
)


class StandardForm(forms.ModelForm):
    applicable_professions = forms.MultipleChoiceField(
        choices=Standard.PROFESSION_CHOICES,
        widget=forms.CheckboxSelectMultiple,
        label="适用专业",
    )
    applicable_business_types = forms.MultipleChoiceField(
        choices=Standard.BUSINESS_TYPE_CHOICES,
        widget=forms.CheckboxSelectMultiple,
        required=False,
        label="适用业态",
    )
    visible_scope = forms.MultipleChoiceField(
        choices=Standard.SCOPE_CHOICES,
        widget=forms.CheckboxSelectMultiple,
        label="可见范围",
    )

    class Meta:
        model = Standard
        fields = [
            "name",
            "standard_type",
            "applicable_professions",
            "applicable_business_types",
            "effective_date",
            "status",
            "visible_scope",
            "editable_roles",
        ]
        widgets = {
            "standard_type": forms.RadioSelect,
            "status": forms.RadioSelect,
            "effective_date": forms.DateInput(attrs={"type": "date"}),
            "editable_roles": forms.SelectMultiple(attrs={"class": "form-select"}),
        }


class StandardReviewItemForm(forms.ModelForm):
    class Meta:
        model = StandardReviewItem
        fields = [
            "section_name",
            "review_point",
            "issue_category",
            "severity_level",
            "order",
        ]
        widgets = {
            "review_point": forms.Textarea(attrs={"rows": 3}),
        }


StandardReviewItemFormSet = inlineformset_factory(
    Standard,
    StandardReviewItem,
    form=StandardReviewItemForm,
    extra=1,
    can_delete=True,
)


class MaterialPriceForm(forms.ModelForm):
    applicable_regions = forms.MultipleChoiceField(
        choices=MaterialPrice.REGION_CHOICES,
        widget=forms.CheckboxSelectMultiple,
        label="适用地区",
    )

    class Meta:
        model = MaterialPrice
        fields = [
            "name",
            "specification",
            "unit",
            "brand_requirement",
            "applicable_regions",
            "price",
            "price_type",
            "price_source",
            "effective_date",
            "expire_date",
            "tax_rate",
            "change_note",
        ]
        widgets = {
            "effective_date": forms.DateInput(attrs={"type": "date"}),
            "expire_date": forms.DateInput(attrs={"type": "date"}),
        }


class CostIndicatorForm(forms.ModelForm):
    class Meta:
        model = CostIndicator
        fields = [
            "name",
            "business_type",
            "building_type",
            "region",
            "data_year",
            "steel_consumption",
            "concrete_consumption",
            "formwork_consumption",
            "masonry_consumption",
            "door_window_index",
            "decoration_index",
            "reference_project",
            "sample_size",
            "data_reliability",
            "update_frequency",
        ]
        widgets = {
            "data_year": forms.NumberInput(attrs={"min": 1990, "max": 2100}),
        }


class ReportTemplateForm(forms.ModelForm):
    service_types = forms.MultipleChoiceField(
        choices=Standard.BUSINESS_TYPE_CHOICES,
        widget=forms.CheckboxSelectMultiple,
        label="适用服务类型",
    )

    class Meta:
        model = ReportTemplate
        fields = [
            "name",
            "template_type",
            "service_types",
            "cover_content",
            "header_footer",
            "sections",
            "styles",
            "is_active",
        ]
        widgets = {
            "cover_content": forms.Textarea(attrs={"rows": 4}),
            "header_footer": forms.Textarea(attrs={"rows": 4, "placeholder": "{\n  \"header\": \"...\"\n}"}),
            "sections": forms.Textarea(attrs={"rows": 4, "placeholder": "[\n  {\n    \"title\": \"章节1\"\n  }\n]"}),
            "styles": forms.Textarea(attrs={"rows": 3, "placeholder": "{\n  \"font\": \"微软雅黑\"\n}"}),
        }

    def _parse_json(self, field_name):
        value = self.cleaned_data.get(field_name)
        if value in (None, "", []):
            return {} if field_name != "sections" else []
        if isinstance(value, (dict, list)):
            return value
        try:
            return json.loads(value)
        except json.JSONDecodeError as exc:
            raise ValidationError(f"字段格式需为合法 JSON：{exc}")

    def clean_header_footer(self):
        return self._parse_json("header_footer")

    def clean_sections(self):
        return self._parse_json("sections")

    def clean_styles(self):
        return self._parse_json("styles")

    def clean_service_types(self):
        return self.cleaned_data.get("service_types", [])


class OpinionTemplateForm(forms.ModelForm):
    default_review_points = forms.ModelMultipleChoiceField(
        queryset=StandardReviewItem.objects.select_related("standard"),
        required=False,
        widget=forms.SelectMultiple(attrs={"class": "form-select"}),
        label="默认审查要点",
    )

    class Meta:
        model = OpinionTemplate
        fields = [
            "name",
            "professional_type",
            "default_review_points",
            "auto_fields",
            "category_templates",
            "calculation_rules",
        ]
        widgets = {
            "auto_fields": forms.Textarea(attrs={"rows": 3, "placeholder": "[\n  \"字段1\"\n]"}),
            "category_templates": forms.Textarea(attrs={"rows": 4, "placeholder": "{\n  \"类别\": {\n    \"默认描述\": \"...\"\n  }\n}"}),
            "calculation_rules": forms.Textarea(attrs={"rows": 4, "placeholder": "{\n  \"公式\": \"...\"\n}"}),
        }

    def _parse_json(self, field_name, default):
        value = self.cleaned_data.get(field_name)
        if value in (None, "", []):
            return default
        if isinstance(value, (dict, list)):
            return value
        try:
            return json.loads(value)
        except json.JSONDecodeError as exc:
            raise ValidationError(f"字段格式需为合法 JSON：{exc}")

    def clean_auto_fields(self):
        return self._parse_json("auto_fields", [])

    def clean_category_templates(self):
        return self._parse_json("category_templates", {})

    def clean_calculation_rules(self):
        return self._parse_json("calculation_rules", {})


class KnowledgeTagForm(forms.ModelForm):
    class Meta:
        model = KnowledgeTag
        fields = ["name", "description"]


class RiskCaseForm(forms.ModelForm):
    tags = forms.ModelMultipleChoiceField(
        queryset=KnowledgeTag.objects.all(),
        required=False,
        widget=forms.SelectMultiple(attrs={"class": "form-select"}),
        label="关联标签",
    )

    class Meta:
        model = RiskCase
        fields = [
            "title",
            "case_type",
            "project",
            "occurred_on",
            "risk_description",
            "root_cause",
            "impact_scope",
            "loss_estimation",
            "counter_measure",
            "prevention",
            "outcome",
            "lessons",
            "tags",
            "recommend_score",
            "applicable_scenarios",
            "is_published",
        ]
        widgets = {
            "occurred_on": forms.DateInput(attrs={"type": "date"}),
            "risk_description": forms.Textarea(attrs={"rows": 3}),
            "root_cause": forms.Textarea(attrs={"rows": 2}),
            "impact_scope": forms.Textarea(attrs={"rows": 2}),
            "counter_measure": forms.Textarea(attrs={"rows": 3}),
            "prevention": forms.Textarea(attrs={"rows": 2}),
            "outcome": forms.Textarea(attrs={"rows": 2}),
            "lessons": forms.Textarea(attrs={"rows": 2}),
            "applicable_scenarios": forms.Textarea(attrs={"rows": 2, "placeholder": "[\n  \"住宅项目\",\n  \"大型综合体\"\n]"}),
        }

    def clean_applicable_scenarios(self):
        value = self.cleaned_data.get("applicable_scenarios")
        if not value:
            return []
        if isinstance(value, list):
            return value
        try:
            scenarios = json.loads(value)
            if not isinstance(scenarios, list):
                raise ValidationError("适用场景需为 JSON 数组")
            return scenarios
        except json.JSONDecodeError as exc:
            raise ValidationError(f"适用场景需为合法 JSON：{exc}")


class TechnicalSolutionForm(forms.ModelForm):
    tags = forms.ModelMultipleChoiceField(
        queryset=KnowledgeTag.objects.all(),
        required=False,
        widget=forms.SelectMultiple(attrs={"class": "form-select"}),
        label="关联标签",
    )

    class Meta:
        model = TechnicalSolution
        fields = [
            "name",
            "domain",
            "issue_type",
            "problem_description",
            "traditional_method",
            "optimized_solution",
            "technical_principle",
            "conditions",
            "cost_comparison",
            "saving_effect",
            "difficulty",
            "promotion_value",
            "calculation_file",
            "drawing_sample",
            "effect_picture",
            "reference_codes",
            "tags",
            "is_published",
        ]
        widgets = {
            "problem_description": forms.Textarea(attrs={"rows": 3}),
            "traditional_method": forms.Textarea(attrs={"rows": 3}),
            "optimized_solution": forms.Textarea(attrs={"rows": 4}),
            "technical_principle": forms.Textarea(attrs={"rows": 3}),
            "conditions": forms.Textarea(attrs={"rows": 3}),
            "cost_comparison": forms.Textarea(attrs={"rows": 3, "placeholder": "{\n  \"传统方案\": 1200,\n  \"优化方案\": 980\n}"}),
            "reference_codes": forms.Textarea(attrs={"rows": 2}),
        }

    def clean_cost_comparison(self):
        value = self.cleaned_data.get("cost_comparison")
        if not value:
            return {}
        if isinstance(value, dict):
            return value
        try:
            comparison = json.loads(value)
            if not isinstance(comparison, dict):
                raise ValidationError("成本对比需为 JSON 对象")
            return comparison
        except json.JSONDecodeError as exc:
            raise ValidationError(f"成本对比需为合法 JSON：{exc}")


class ProfessionalCategoryForm(forms.ModelForm):
    service_types = forms.MultipleChoiceField(
        choices=Standard.BUSINESS_TYPE_CHOICES,
        required=False,
        widget=forms.CheckboxSelectMultiple,
        label="适用服务类型",
    )

    class Meta:
        model = ProfessionalCategory
        fields = [
            "code",
            "name",
            "category",
            "order",
            "service_types",
            "default_owner",
            "workflow_template",
            "data_permissions",
            "operation_permissions",
        ]
        widgets = {
            "data_permissions": forms.SelectMultiple(attrs={"class": "form-select"}),
            "operation_permissions": forms.SelectMultiple(attrs={"class": "form-select"}),
        }

    def clean_service_types(self):
        return self.cleaned_data.get("service_types", [])


class SystemParameterForm(forms.ModelForm):
    class Meta:
        model = SystemParameter
        fields = ["key", "value", "description", "category"]
