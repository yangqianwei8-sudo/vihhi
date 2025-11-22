from decimal import Decimal
from typing import Any, Optional
import json

from django import forms
from django.db.models import Q
from django.forms import inlineformset_factory

from backend.apps.project_center.models import Project
from backend.apps.resource_standard.models import (
    ProfessionalCategory,
    StandardReviewItem,
)

from .models import Opinion, OpinionAttachment, OpinionReview
from .services import (
    calculate_saving_amount,
    generate_opinion_number,
)


class OpinionForm(forms.ModelForm):
    """意见填报表单"""

    review_points = forms.ModelMultipleChoiceField(
        queryset=StandardReviewItem.objects.select_related("standard"),
        required=False,
        widget=forms.CheckboxSelectMultiple,
        label="关联审查要点",
    )

    class Meta:
        model = Opinion
        fields = [
            "project",
            "professional_category",
            "source",
            "priority",
            "drawing_number",
            "drawing_version",
            "location_name",
            "review_points",
            "issue_description",
            "current_practice",
            "recommendation",
            "issue_category",
            "severity_level",
            "reference_codes",
            "calculation_mode",
            "quantity_before",
            "quantity_after",
            "measure_unit",
            "unit_price_before",
            "unit_price_after",
            "saving_amount",
            "calculation_note",
            "impact_scope",
            "expected_complete_date",
            "actual_complete_date",
            "response_deadline",
        ]
        widgets = {
            "issue_description": forms.Textarea(attrs={"rows": 4, "class": "rich-text"}),
            "current_practice": forms.Textarea(attrs={"rows": 3, "class": "rich-text"}),
            "recommendation": forms.Textarea(attrs={"rows": 4, "class": "rich-text"}),
            "calculation_note": forms.Textarea(attrs={"rows": 3}),
            "impact_scope": forms.HiddenInput(),
            "expected_complete_date": forms.DateInput(attrs={"type": "date"}),
            "actual_complete_date": forms.DateInput(attrs={"type": "date"}),
            "response_deadline": forms.DateInput(attrs={"type": "date"}),
        }

    def __init__(self, *args: Any, user=None, project_queryset=None, **kwargs: Any) -> None:
        super().__init__(*args, **kwargs)
        self.fields["calculation_mode"].widget = forms.RadioSelect(
            choices=self.fields["calculation_mode"].choices
        )
        for name, field in self.fields.items():
            if name == "calculation_mode":
                continue
            widget = field.widget
            if name == "review_points":
                widget.attrs.setdefault("class", "form-check-input")
            elif isinstance(widget, (forms.Select, forms.SelectMultiple)):
                widget.attrs.setdefault("class", "form-select")
            elif hasattr(widget, "input_type"):
                widget.attrs.setdefault("class", "form-control")
        if user is not None:
            self._limit_project_queryset(user, project_queryset)
        if self.instance and self.instance.pk:
            self.fields["project"].disabled = True
            self.fields["professional_category"].disabled = True
        # impact scope initial value should be JSON string for front端
        impact_scope_value = self.initial.get("impact_scope") or self.instance.impact_scope if self.instance else []
        if impact_scope_value:
            try:
                serialized = json.dumps(impact_scope_value, ensure_ascii=False)
            except TypeError:
                serialized = json.dumps(list(impact_scope_value), ensure_ascii=False)
        else:
            serialized = "[]"
        self.fields["impact_scope"].initial = serialized

    def _limit_project_queryset(
        self, user, project_queryset: Optional[Any]
    ) -> None:
        """限制项目选择，仅展示当前用户可访问的项目"""
        base_qs = project_queryset if project_queryset is not None else Project.objects.all()
        if getattr(user, "is_superuser", False):
            self.fields["project"].queryset = base_qs.distinct()
            return

        accessible_ids = Project.objects.filter(
            Q(project_manager=user)
            | Q(business_manager=user)
            | Q(team_members__user=user)
            | Q(opinions__created_by=user)
        ).values_list("id", flat=True)

        if not accessible_ids:
            permission_codes = set(getattr(user, "permission_codes_cache", []) or [])
            if not permission_codes and hasattr(user, "get_permission_codes"):
                try:
                    permission_codes = set(user.get_permission_codes())
                except Exception:  # noqa: BLE001
                    permission_codes = set()
            if getattr(user, "is_staff", False) or "project_center.view_project" in permission_codes:
                self.fields["project"].queryset = base_qs.distinct()
                return

        self.fields["project"].queryset = base_qs.filter(id__in=accessible_ids).distinct()

    def clean(self) -> dict[str, Any]:
        cleaned_data = super().clean()
        mode = cleaned_data.get("calculation_mode")
        qb = cleaned_data.get("quantity_before")
        qa = cleaned_data.get("quantity_after")
        ub = cleaned_data.get("unit_price_before")
        ua = cleaned_data.get("unit_price_after")
        saving_amount = cleaned_data.get("saving_amount")

        if mode == Opinion.CalculationMode.AUTO:
            missing = [
                name
                for name, value in [
                    ("优化前工程量", qb),
                    ("优化后工程量", qa),
                    ("优化前综合单价", ub),
                    ("优化后综合单价", ua),
                ]
                if value in (None, "")
            ]
            if missing:
                raise forms.ValidationError(
                    f"自动计算模式下需填写：{', '.join(missing)}"
                )
            cleaned_data["saving_amount"] = calculate_saving_amount(qb, qa, ub, ua)
        else:
            if saving_amount is None:
                raise forms.ValidationError("手动输入模式需填写节省金额。")

        impact_scope_raw = cleaned_data.get("impact_scope", "[]")
        if isinstance(impact_scope_raw, str):
            try:
                scope_value = json.loads(impact_scope_raw or "[]")
            except json.JSONDecodeError:
                raise forms.ValidationError("影响范围数据格式不正确，请重新选择。")
        else:
            scope_value = impact_scope_raw or []
        if not isinstance(scope_value, list):
            raise forms.ValidationError("影响范围需为列表。")
        cleaned_data["impact_scope"] = scope_value

        return cleaned_data

    def save(self, commit: bool = True) -> Opinion:
        opinion = super().save(commit=False)
        if not opinion.opinion_number:
            opinion.opinion_number = generate_opinion_number(
                opinion.project, opinion.professional_category
            )
        if commit:
            opinion.save()
            self.save_m2m()
        return opinion


class OpinionAttachmentForm(forms.ModelForm):
    def __init__(self, *args: Any, **kwargs: Any) -> None:
        super().__init__(*args, **kwargs)
        self.fields["attachment_type"].widget.attrs.setdefault("class", "form-select")
        self.fields["file"].widget.attrs.setdefault("class", "form-control")

    class Meta:
        model = OpinionAttachment
        fields = ["attachment_type", "file"]


OpinionAttachmentFormSet = inlineformset_factory(
    Opinion,
    OpinionAttachment,
    form=OpinionAttachmentForm,
    extra=1,
    can_delete=True,
)


class OpinionReviewForm(forms.ModelForm):
    def __init__(self, *args: Any, **kwargs: Any) -> None:
        super().__init__(*args, **kwargs)
        for name, field in self.fields.items():
            widget = field.widget
            if isinstance(widget, forms.Select):
                widget.attrs.setdefault("class", "form-select")
            elif hasattr(widget, "input_type"):
                widget.attrs.setdefault("class", "form-control")

    class Meta:
        model = OpinionReview
        fields = [
            "status",
            "comments",
            "technical_score",
            "economic_score",
            "internal_note",
        ]
        widgets = {
            "comments": forms.Textarea(attrs={"rows": 3, "class": "rich-text"}),
            "internal_note": forms.Textarea(attrs={"rows": 2}),
        }

    def clean(self) -> dict[str, Any]:
        data = super().clean()
        status = data.get("status")
        comments = data.get("comments")
        if status in {OpinionReview.ReviewStatus.REJECTED, OpinionReview.ReviewStatus.NEEDS_UPDATE} and not comments:
            raise forms.ValidationError("驳回或需修改时必须填写审核意见。")
        return data


class OpinionBulkImportForm(forms.Form):
    file = forms.FileField(label="导入文件（Excel）")

    def clean_file(self) -> Any:
        upload = self.cleaned_data["file"]
        if not upload.name.lower().endswith((".xlsx", ".xls")):
            raise forms.ValidationError("请上传 Excel 文件（.xls / .xlsx）。")
        if upload.size > 10 * 1024 * 1024:
            raise forms.ValidationError("文件大小不能超过 10MB。")
        return upload

