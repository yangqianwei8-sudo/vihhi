from decimal import Decimal

from django.db import transaction
from django.utils import timezone
from rest_framework import serializers

from backend.apps.resource_standard.models import StandardReviewItem

from .models import (
    Opinion,
    OpinionAttachment,
    OpinionParticipant,
    OpinionReview,
    OpinionSavingItem,
    OpinionWorkflowLog,
    ProductionReport,
    ProductionReportSection,
    ProductionStatistic,
)
from .services import (
    calculate_saving_amount,
    generate_opinion_number,
    sync_opinion_participants,
    sync_opinion_saving_items,
    record_workflow_log,
)


class OpinionAttachmentSerializer(serializers.ModelSerializer):
    uploaded_by_name = serializers.SerializerMethodField()

    class Meta:
        model = OpinionAttachment
        fields = [
            "id",
            "attachment_type",
            "file",
            "uploaded_by",
            "uploaded_by_name",
            "uploaded_at",
        ]
        read_only_fields = ["id", "uploaded_by_name", "uploaded_at"]

    def get_uploaded_by_name(self, obj):
        return obj.uploaded_by.get_full_name() if obj.uploaded_by else ""


class OpinionReviewSerializer(serializers.ModelSerializer):
    reviewer_name = serializers.SerializerMethodField()

    class Meta:
        model = OpinionReview
        fields = [
            "id",
            "opinion",
            "role",
            "status",
            "comments",
            "technical_score",
            "economic_score",
            "internal_note",
            "reviewer",
            "reviewer_name",
            "created_at",
            "updated_at",
        ]
        read_only_fields = ["id", "reviewer", "reviewer_name", "created_at", "updated_at"]
        extra_kwargs = {
            "role": {"required": False},
        }

    def get_reviewer_name(self, obj):
        return obj.reviewer.get_full_name() if obj.reviewer_id else ""

    def validate(self, attrs):
        attrs = super().validate(attrs)
        status_value = attrs.get("status")
        comments = (attrs.get("comments") or "").strip()
        if status_value in [
            OpinionReview.ReviewStatus.REJECTED,
            OpinionReview.ReviewStatus.NEEDS_UPDATE,
        ] and not comments:
            raise serializers.ValidationError(
                {"comments": "驳回或需修改时必须填写审核意见。"}
            )
        return attrs

    def validate_technical_score(self, value):
        if value is None:
            return value
        if not (1 <= value <= 5):
            raise serializers.ValidationError("技术评分需在 1-5 分之间。")
        return value

    def validate_economic_score(self, value):
        if value is None:
            return value
        if not (1 <= value <= 5):
            raise serializers.ValidationError("经济评分需在 1-5 分之间。")
        return value


class OpinionParticipantSerializer(serializers.ModelSerializer):
    user_name = serializers.SerializerMethodField()

    class Meta:
        model = OpinionParticipant
        fields = [
            "id",
            "user",
            "user_name",
            "role",
            "is_primary",
            "joined_at",
            "removed_at",
            "extra_info",
        ]
        read_only_fields = ["id", "user_name", "joined_at", "removed_at"]

    def get_user_name(self, obj):
        return obj.user.get_full_name() if obj.user_id else ""


class OpinionSavingItemSerializer(serializers.ModelSerializer):
    class Meta:
        model = OpinionSavingItem
        fields = [
            "id",
            "category",
            "description",
            "quantity",
            "unit",
            "unit_saving",
            "total_saving",
            "notes",
        ]
        read_only_fields = ["id"]


class OpinionWorkflowLogSerializer(serializers.ModelSerializer):
    operator_name = serializers.SerializerMethodField()

    class Meta:
        model = OpinionWorkflowLog
        fields = [
            "id",
            "action",
            "from_status",
            "to_status",
            "operator",
            "operator_name",
            "operator_role",
            "message",
            "payload",
            "created_at",
        ]
        read_only_fields = fields

    def get_operator_name(self, obj):
        return obj.operator.get_full_name() if obj.operator_id else ""


class OpinionSerializer(serializers.ModelSerializer):
    project_name = serializers.CharField(source="project.name", read_only=True)
    project_number = serializers.CharField(source="project.project_number", read_only=True)
    professional_category_name = serializers.CharField(
        source="professional_category.name", read_only=True
    )
    created_by_name = serializers.SerializerMethodField()
    current_reviewer_name = serializers.SerializerMethodField()
    attachments = OpinionAttachmentSerializer(many=True, read_only=True)
    reviews = OpinionReviewSerializer(many=True, read_only=True)
    review_points = serializers.PrimaryKeyRelatedField(
        many=True, queryset=StandardReviewItem.objects.all()
    )
    participants = OpinionParticipantSerializer(many=True, read_only=True)
    participants_payload = OpinionParticipantSerializer(
        many=True, write_only=True, required=False, source="participants_data"
    )
    saving_items = OpinionSavingItemSerializer(many=True, read_only=True)
    saving_items_payload = OpinionSavingItemSerializer(
        many=True, write_only=True, required=False, source="saving_items_data"
    )
    workflow_logs = OpinionWorkflowLogSerializer(many=True, read_only=True)

    class Meta:
        model = Opinion
        fields = [
            "id",
            "opinion_number",
            "status",
            "status_display",
            "project",
            "project_name",
            "project_number",
            "professional_category",
            "professional_category_name",
            "source",
            "priority",
            "created_by",
            "created_by_name",
            "current_reviewer",
            "current_reviewer_name",
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
            "is_template_applied",
            "submitted_at",
            "reviewed_at",
            "first_assigned_at",
            "first_response_at",
            "closed_at",
            "cycle_time_hours",
            "created_at",
            "updated_at",
            "attachments",
            "reviews",
            "participants",
            "saving_items",
            "workflow_logs",
            "participants_payload",
            "saving_items_payload",
        ]
        read_only_fields = [
            "opinion_number",
            "created_by",
            "created_by_name",
            "current_reviewer_name",
            "submitted_at",
            "reviewed_at",
            "first_assigned_at",
            "first_response_at",
            "closed_at",
            "cycle_time_hours",
            "created_at",
            "updated_at",
            "attachments",
            "reviews",
            "participants",
            "saving_items",
            "workflow_logs",
        ]

    def get_created_by_name(self, obj):
        return obj.created_by.get_full_name() if obj.created_by_id else ""

    def get_current_reviewer_name(self, obj):
        return obj.current_reviewer.get_full_name() if obj.current_reviewer_id else ""

    def validate(self, attrs):
        attrs = super().validate(attrs)
        mode = attrs.get("calculation_mode", self.instance.calculation_mode if self.instance else None)
        if mode == Opinion.CalculationMode.AUTO:
            qb = attrs.get("quantity_before")
            qa = attrs.get("quantity_after")
            ub = attrs.get("unit_price_before")
            ua = attrs.get("unit_price_after")
            missing = [
                label
                for label, value in [
                    ("优化前工程量", qb),
                    ("优化后工程量", qa),
                    ("优化前综合单价", ub),
                    ("优化后综合单价", ua),
                ]
                if value in (None, "")
            ]
            if missing:
                raise serializers.ValidationError(
                    {"saving_amount": f"自动计算模式下需填写：{', '.join(missing)}"}
                )
            attrs["saving_amount"] = calculate_saving_amount(qb, qa, ub, ua)
        else:
            if attrs.get("saving_amount") in (None, ""):
                raise serializers.ValidationError({"saving_amount": "手动输入模式需填写节省金额。"})
        return attrs

    def create(self, validated_data):
        review_points = validated_data.pop("review_points", [])
        participants_data = validated_data.pop("participants_data", [])
        saving_items_data = validated_data.pop("saving_items_data", [])
        request = self.context.get("request")
        user = request.user if request else None
        if user and not validated_data.get("created_by"):
            validated_data["created_by"] = user
        with transaction.atomic():
            opinion = Opinion(**validated_data)
            if not opinion.opinion_number:
                opinion.opinion_number = generate_opinion_number(
                    opinion.project, opinion.professional_category
                )
            if opinion.status == Opinion.OpinionStatus.SUBMITTED and not opinion.submitted_at:
                opinion.submitted_at = timezone.now()
            opinion.save()
            if review_points:
                opinion.review_points.set(review_points)
            if saving_items_data:
                sync_opinion_saving_items(opinion, saving_items_data)
            if participants_data:
                sync_opinion_participants(opinion, participants_data, operator=user)
            record_workflow_log(
                opinion=opinion,
                action=OpinionWorkflowLog.ActionType.CREATED,
                operator=user,
                from_status=None,
                to_status=opinion.status,
                message="创建意见",
            )
            opinion.refresh_cycle_metrics(commit=True)
        return opinion

    def update(self, instance, validated_data):
        review_points = validated_data.pop("review_points", None)
        participants_data = validated_data.pop("participants_data", None)
        saving_items_data = validated_data.pop("saving_items_data", None)
        old_status = instance.status
        with transaction.atomic():
            for attr, value in validated_data.items():
                setattr(instance, attr, value)
            if instance.status == Opinion.OpinionStatus.SUBMITTED and not instance.submitted_at:
                instance.submitted_at = timezone.now()
            instance.save()
            if review_points is not None:
                instance.review_points.set(review_points)
            if saving_items_data is not None:
                sync_opinion_saving_items(instance, saving_items_data)
            if participants_data is not None:
                request = self.context.get("request")
                user = request.user if request else None
                sync_opinion_participants(instance, participants_data, operator=user)
            if old_status != instance.status:
                request = self.context.get("request")
                user = request.user if request else None
                record_workflow_log(
                    opinion=instance,
                    action=OpinionWorkflowLog.ActionType.STATUS_CHANGED,
                    operator=user,
                    from_status=old_status,
                    to_status=instance.status,
                    message="状态更新",
                )
            instance.refresh_cycle_metrics(commit=True)
        return instance


class OpinionListSerializer(OpinionSerializer):
    project_name = serializers.CharField(source="project.name", read_only=True)
    project_number = serializers.CharField(source="project.project_number", read_only=True)
    professional_category_name = serializers.CharField(
        source="professional_category.name", read_only=True
    )
    status_display = serializers.CharField(source="get_status_display", read_only=True)

    class Meta(OpinionSerializer.Meta):
        fields = [
            "id",
            "opinion_number",
            "status",
            "status_display",
            "project",
            "project_name",
            "project_number",
            "professional_category",
            "professional_category_name",
            "created_by",
            "created_by_name",
            "current_reviewer",
            "current_reviewer_name",
            "location_name",
            "issue_category",
            "severity_level",
            "saving_amount",
            "cycle_time_hours",
            "submitted_at",
            "reviewed_at",
            "created_at",
            "updated_at",
        ]


class ProductionReportSectionSerializer(serializers.ModelSerializer):
    class Meta:
        model = ProductionReportSection
        fields = ["id", "report", "title", "order", "content", "metadata"]


class ProductionReportSerializer(serializers.ModelSerializer):
    project_name = serializers.CharField(source="project.name", read_only=True)
    professional_category_name = serializers.CharField(
        source="professional_category.name", read_only=True
    )
    generated_by_name = serializers.SerializerMethodField()
    sections = ProductionReportSectionSerializer(many=True, read_only=True)

    class Meta:
        model = ProductionReport
        fields = [
            "id",
            "report_number",
            "name",
            "project",
            "project_name",
            "professional_category",
            "professional_category_name",
            "template",
            "generated_by",
            "generated_by_name",
            "summary",
            "configuration",
            "status",
            "generated_at",
            "updated_at",
            "sections",
        ]
        read_only_fields = [
            "report_number",
            "generated_by_name",
            "generated_at",
            "updated_at",
            "sections",
        ]

    def get_generated_by_name(self, obj):
        return obj.generated_by.get_full_name() if obj.generated_by_id else ""


class ProductionStatisticSerializer(serializers.ModelSerializer):
    project_name = serializers.CharField(source="project.name", read_only=True)
    project_number = serializers.CharField(source="project.project_number", read_only=True)

    class Meta:
        model = ProductionStatistic
        fields = [
            "id",
            "project",
            "project_name",
            "project_number",
            "statistic_type",
            "snapshot_date",
            "payload",
            "created_at",
        ]
        read_only_fields = ["created_at"]

