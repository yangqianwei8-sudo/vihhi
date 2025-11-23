from django.db import transaction
from django.db.models import Avg, Count, Sum
from django.utils import timezone
from rest_framework import permissions, status, viewsets
from rest_framework.decorators import action
from rest_framework.exceptions import ValidationError
from rest_framework.response import Response

from backend.apps.project_center.models import Project
from backend.apps.system_management.models import User

from .models import (
    Opinion,
    OpinionParticipant,
    OpinionReview,
    OpinionWorkflowLog,
    ProductionReport,
    ProductionStatistic,
)
from .serializers import (
    OpinionListSerializer,
    OpinionReviewSerializer,
    OpinionSerializer,
    ProductionReportSerializer,
    ProductionStatisticSerializer,
)
from .services import infer_review_role, record_workflow_log


def _accessible_project_ids(user):
    if user.is_superuser:
        return Project.objects.values_list("id", flat=True)
    owned = Project.objects.filter(created_by=user).values_list("id", flat=True)
    managed = Project.objects.filter(project_manager=user).values_list("id", flat=True)
    business = Project.objects.filter(business_manager=user).values_list("id", flat=True)
    team = Project.objects.filter(team_members__user=user).values_list("id", flat=True)
    return set(owned) | set(managed) | set(business) | set(team)


class OpinionViewSet(viewsets.ModelViewSet):
    permission_classes = [permissions.IsAuthenticated]
    serializer_class = OpinionSerializer

    def get_queryset(self):
        project_ids = _accessible_project_ids(self.request.user)
        queryset = (
            Opinion.objects.filter(project_id__in=project_ids)
            .select_related(
                "project",
                "professional_category",
                "created_by",
                "current_reviewer",
            )
            .prefetch_related(
                "review_points",
                "attachments",
                "reviews__reviewer",
            )
        )
        status_param = self.request.query_params.get("status")
        if status_param:
            status_list = [item.strip() for item in status_param.split(",") if item.strip()]
            if status_list:
                queryset = queryset.filter(status__in=status_list)
        project_param = self.request.query_params.get("project")
        if project_param:
            project_ids = [pid for pid in project_param.split(",") if pid.isdigit()]
            if project_ids:
                queryset = queryset.filter(project_id__in=project_ids)
        profession_param = self.request.query_params.get("professional_category")
        if profession_param:
            category_ids = [cid for cid in profession_param.split(",") if cid.isdigit()]
            if category_ids:
                queryset = queryset.filter(professional_category_id__in=category_ids)
        keyword = self.request.query_params.get("search")
        if keyword:
            queryset = queryset.filter(location_name__icontains=keyword)

        ordering = self.request.query_params.get("ordering", "-created_at")
        return queryset.order_by(ordering)

    def get_serializer_class(self):
        if self.action == "list":
            return OpinionListSerializer
        return OpinionSerializer

    def perform_create(self, serializer):
        opinion = serializer.save(created_by=self.request.user)
        if opinion.status == Opinion.OpinionStatus.SUBMITTED and not opinion.submitted_at:
            opinion.submitted_at = timezone.now()
            opinion.save(update_fields=["submitted_at"])

    def perform_update(self, serializer):
        opinion = serializer.save()
        if opinion.status == Opinion.OpinionStatus.SUBMITTED and not opinion.submitted_at:
            opinion.submitted_at = timezone.now()
            opinion.save(update_fields=["submitted_at"])

    @action(detail=True, methods=["post"])
    def submit(self, request, pk=None):
        opinion = self.get_object()
        if opinion.status not in [Opinion.OpinionStatus.DRAFT, Opinion.OpinionStatus.NEEDS_UPDATE]:
            return Response({"detail": "当前状态无法提交。"}, status=status.HTTP_400_BAD_REQUEST)
        previous_status = opinion.status
        serializer = self.get_serializer(
            opinion,
            data={"status": Opinion.OpinionStatus.SUBMITTED},
            partial=True,
        )
        serializer.is_valid(raise_exception=True)
        serializer.save(submitted_at=timezone.now())
        record_workflow_log(
            opinion=opinion,
            action=OpinionWorkflowLog.ActionType.SUBMITTED,
            operator=request.user,
            from_status=previous_status,
            to_status=Opinion.OpinionStatus.SUBMITTED,
            message="提交意见",
        )
        return Response(serializer.data)

    @action(detail=True, methods=["post"])
    def revert(self, request, pk=None):
        opinion = self.get_object()
        if opinion.status not in [Opinion.OpinionStatus.NEEDS_UPDATE, Opinion.OpinionStatus.REJECTED]:
            return Response({"detail": "仅驳回或需修改的意见可退回草稿。"}, status=status.HTTP_400_BAD_REQUEST)
        previous_status = opinion.status
        serializer = self.get_serializer(
            opinion,
            data={"status": Opinion.OpinionStatus.DRAFT},
            partial=True,
        )
        serializer.is_valid(raise_exception=True)
        serializer.save()
        record_workflow_log(
            opinion=opinion,
            action=OpinionWorkflowLog.ActionType.STATUS_CHANGED,
            operator=request.user,
            from_status=previous_status,
            to_status=Opinion.OpinionStatus.DRAFT,
            message="意见退回草稿",
        )
        return Response(serializer.data)

    @action(detail=True, methods=["post"])
    def assign(self, request, pk=None):
        opinion = self.get_object()
        reviewer_id = request.data.get("reviewer")
        if reviewer_id:
            try:
                reviewer = User.objects.get(pk=reviewer_id, is_active=True)
            except User.DoesNotExist:
                return Response({"detail": "指定的审核人不存在或未启用。"}, status=status.HTTP_400_BAD_REQUEST)
        else:
            reviewer = request.user
        opinion.current_reviewer = reviewer
        previous_status = opinion.status
        if opinion.status == Opinion.OpinionStatus.SUBMITTED:
            opinion.status = Opinion.OpinionStatus.IN_REVIEW
        now = timezone.now()
        update_fields = ["current_reviewer", "status", "updated_at"]
        if not opinion.first_assigned_at:
            opinion.first_assigned_at = now
            update_fields.append("first_assigned_at")
        opinion.save(update_fields=update_fields)
        record_workflow_log(
            opinion=opinion,
            action=OpinionWorkflowLog.ActionType.REASSIGNED,
            operator=request.user,
            from_status=previous_status,
            to_status=opinion.status,
            message=f"指派审核人：{reviewer.get_full_name() or reviewer.username}",
            payload={"reviewer_id": reviewer.id},
            operator_role=OpinionParticipant.ParticipantRole.PROJECT_MANAGER
            if opinion.project.project_manager_id == request.user.id
            else None,
        )
        serializer = self.get_serializer(opinion)
        return Response(serializer.data)

    @action(detail=False, methods=["post"])
    def bulk_review(self, request):
        opinion_ids = request.data.get("ids", [])
        target_status = request.data.get("status")
        comment = request.data.get("comment", "")
        role_value = request.data.get("role", OpinionReview.ReviewRole.PROJECT_LEAD)

        if not isinstance(opinion_ids, list) or not opinion_ids:
            return Response({"detail": "请选择至少一条意见。"}, status=status.HTTP_400_BAD_REQUEST)

        valid_status = {
            OpinionReview.ReviewStatus.APPROVED: Opinion.OpinionStatus.APPROVED,
            OpinionReview.ReviewStatus.REJECTED: Opinion.OpinionStatus.REJECTED,
            OpinionReview.ReviewStatus.NEEDS_UPDATE: Opinion.OpinionStatus.NEEDS_UPDATE,
        }

        if target_status not in valid_status:
            return Response({"detail": "不支持的审核状态。"}, status=status.HTTP_400_BAD_REQUEST)

        if role_value not in dict(OpinionReview.ReviewRole.choices):
            return Response({"detail": "无效的审核角色。"}, status=status.HTTP_400_BAD_REQUEST)

        project_ids = _accessible_project_ids(request.user)
        opinions = (
            Opinion.objects.filter(id__in=opinion_ids, project_id__in=project_ids)
            .select_related("project", "professional_category")
            .order_by("id")
        )
        if opinions.count() != len(set(opinion_ids)):
            return Response({"detail": "存在无权限或不存在的意见记录。"}, status=status.HTTP_400_BAD_REQUEST)

        now = timezone.now()
        changed = 0
        for opinion in opinions:
            if opinion.status not in [
                Opinion.OpinionStatus.SUBMITTED,
                Opinion.OpinionStatus.IN_REVIEW,
                Opinion.OpinionStatus.NEEDS_UPDATE,
            ]:
                continue
            previous_status = opinion.status
            target_opinion_status = valid_status[target_status]
            opinion.status = target_opinion_status
            if not opinion.first_response_at:
                opinion.first_response_at = now
            if target_opinion_status not in [
                Opinion.OpinionStatus.APPROVED,
                Opinion.OpinionStatus.REJECTED,
            ]:
                opinion.reviewed_at = None
                opinion.closed_at = None
            else:
                opinion.reviewed_at = now
                opinion.closed_at = now
            opinion.current_reviewer = None
            opinion.refresh_cycle_metrics()
            update_fields = [
                "status",
                "reviewed_at",
                "current_reviewer",
                "updated_at",
                "first_response_at",
                "closed_at",
                "cycle_time_hours",
            ]
            opinion.save(update_fields=update_fields)

            OpinionReview.objects.create(
                opinion=opinion,
                reviewer=request.user,
                role=role_value,
                status=target_status,
                comments=comment,
            )
            record_workflow_log(
                opinion=opinion,
                action=OpinionWorkflowLog.ActionType.REVIEWED,
                operator=request.user,
                from_status=previous_status,
                to_status=target_opinion_status,
                message=f"批量审核：{OpinionReview.ReviewStatus(target_status).label}",
                payload={"comment": comment},
                operator_role=role_value,
            )
            changed += 1

        return Response({"processed": changed})

    @action(detail=False, methods=["get"])
    def metrics(self, request):
        queryset = self.get_queryset()
        status_counts = {
            item["status"]: item["count"]
            for item in queryset.values("status").annotate(count=Count("id"))
        }
        priority_counts = {
            item["priority"]: item["count"]
            for item in queryset.values("priority").annotate(count=Count("id"))
        }
        professional_counts = {
            item["professional_category__name"]: item["count"]
            for item in queryset.values("professional_category__name").annotate(count=Count("id"))
            if item["professional_category__name"]
        }

        pending_status = [
            Opinion.OpinionStatus.SUBMITTED,
            Opinion.OpinionStatus.IN_REVIEW,
            Opinion.OpinionStatus.NEEDS_UPDATE,
        ]
        today = timezone.now().date()

        pending_total = queryset.filter(status__in=pending_status).count()
        pending_unassigned = queryset.filter(
            status__in=pending_status, current_reviewer__isnull=True
        ).count()
        overdue_total = queryset.filter(
            status__in=pending_status, response_deadline__lt=today
        ).count()

        cycle_avg = queryset.filter(cycle_time_hours__isnull=False).aggregate(
            avg=Avg("cycle_time_hours")
        )["avg"]
        saving_total = queryset.aggregate(total=Sum("saving_amount"))["total"]

        data = {
            "counts": {
                "status": status_counts,
                "priority": priority_counts,
                "professional": professional_counts,
            },
            "pending": {
                "total": pending_total,
                "unassigned": pending_unassigned,
                "overdue": overdue_total,
            },
            "averages": {
                "cycle_time_hours": float(cycle_avg) if cycle_avg is not None else None,
            },
            "financial": {
                "saving_amount_total": float(saving_total) if saving_total else 0.0,
            },
        }
        return Response(data)


class OpinionReviewViewSet(viewsets.ModelViewSet):
    serializer_class = OpinionReviewSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        project_ids = _accessible_project_ids(self.request.user)
        opinion_pk = self.kwargs.get("opinion_pk")
        queryset = OpinionReview.objects.filter(opinion__project_id__in=project_ids)
        if opinion_pk:
            queryset = queryset.filter(opinion_id=opinion_pk)
        return (
            queryset
            .select_related("opinion", "reviewer")
            .order_by("-created_at")
        )

    def perform_create(self, serializer):
        opinion = serializer.validated_data["opinion"]
        user = self.request.user
        pending_status = [
            Opinion.OpinionStatus.SUBMITTED,
            Opinion.OpinionStatus.IN_REVIEW,
            Opinion.OpinionStatus.NEEDS_UPDATE,
        ]
        if opinion.status not in pending_status:
            raise ValidationError({"detail": "当前状态不可提交审核意见。"})
        if opinion.current_reviewer_id and opinion.current_reviewer_id != user.id:
            raise ValidationError({"detail": "请先将该意见指派给自己后再审核。"})

        role = serializer.validated_data.get("role")
        if not role:
            role = infer_review_role(opinion, user)
            serializer.validated_data["role"] = role
        if role not in dict(OpinionReview.ReviewRole.choices):
            raise ValidationError({"role": "不支持的审核角色。"})
        if OpinionReview.objects.filter(opinion=opinion, reviewer=user, role=role).exists():
            raise ValidationError({"detail": "已提交过该角色的审核意见，无法重复提交。"})

        with transaction.atomic():
            serializer.validated_data["reviewer"] = user
            review = serializer.save()
            previous_status = opinion.status
            decision_time = timezone.now()
            if review.status == OpinionReview.ReviewStatus.APPROVED:
                opinion.status = Opinion.OpinionStatus.APPROVED
                opinion.reviewed_at = decision_time
                opinion.closed_at = opinion.reviewed_at
            elif review.status == OpinionReview.ReviewStatus.REJECTED:
                opinion.status = Opinion.OpinionStatus.REJECTED
                opinion.reviewed_at = decision_time
                opinion.closed_at = opinion.reviewed_at
            elif review.status == OpinionReview.ReviewStatus.NEEDS_UPDATE:
                opinion.status = Opinion.OpinionStatus.NEEDS_UPDATE
                opinion.closed_at = None
                opinion.reviewed_at = None
            else:
                opinion.status = Opinion.OpinionStatus.IN_REVIEW
                opinion.closed_at = None
                opinion.reviewed_at = None
            if not opinion.first_response_at:
                opinion.first_response_at = timezone.now()
            opinion.current_reviewer = None
            opinion.refresh_cycle_metrics()
            opinion.save(
                update_fields=[
                    "status",
                    "reviewed_at",
                    "current_reviewer",
                    "first_response_at",
                    "closed_at",
                    "cycle_time_hours",
                ]
            )
            record_workflow_log(
                opinion=opinion,
                action=OpinionWorkflowLog.ActionType.REVIEWED,
                operator=user,
                from_status=previous_status,
                to_status=opinion.status,
                message=review.comments or "",
                payload={
                    "review_id": review.id,
                    "review_status": review.status,
                    "role": review.role,
                },
                operator_role=review.role,
            )


class ProductionReportViewSet(viewsets.ModelViewSet):
    serializer_class = ProductionReportSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        project_ids = _accessible_project_ids(self.request.user)
        return (
            ProductionReport.objects.filter(project_id__in=project_ids)
            .select_related("project", "professional_category", "generated_by", "template")
            .prefetch_related("sections")
            .order_by("-generated_at", "-updated_at")
        )

    def perform_create(self, serializer):
        serializer.save(
            generated_by=self.request.user,
            status=ProductionReport.ReportStatus.GENERATED,
            generated_at=timezone.now(),
        )


class ProductionStatisticViewSet(viewsets.ReadOnlyModelViewSet):
    serializer_class = ProductionStatisticSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        project_ids = _accessible_project_ids(self.request.user)
        queryset = ProductionStatistic.objects.filter(project_id__in=project_ids)

        statistic_type = self.request.query_params.get("statistic_type")
        if statistic_type:
            queryset = queryset.filter(statistic_type=statistic_type)

        project_param = self.request.query_params.get("project")
        if project_param:
            if project_param.lower() == "null":
                queryset = queryset.filter(project__isnull=True)
            elif project_param.isdigit():
                queryset = queryset.filter(project_id=int(project_param))
        return queryset.select_related("project").order_by("-snapshot_date", "-id")

    @action(detail=False, methods=["get"])
    def latest(self, request):
        statistic = self.get_queryset().first()
        if not statistic:
            return Response({"detail": "暂无统计数据"}, status=status.HTTP_404_NOT_FOUND)
        serializer = self.get_serializer(statistic)
        return Response(serializer.data)

