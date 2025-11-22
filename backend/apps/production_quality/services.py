from __future__ import annotations

from datetime import timedelta
from decimal import Decimal
from typing import Iterable, Optional, Set

from django.conf import settings
from django.db.models import Avg, Count, DurationField, ExpressionWrapper, F, Sum
from django.urls import reverse
from django.utils import timezone

from backend.apps.system_management.models import User

from backend.apps.project_center.models import Project, ProjectTeamNotification
from backend.apps.resource_standard.models import ProfessionalCategory

from .models import (
    Opinion,
    OpinionParticipant,
    OpinionReview,
    OpinionSavingItem,
    OpinionWorkflowLog,
    ProductionStatistic,
)
from .utils.notifications import NotificationMessage, send_email_notification, send_wecom_notification


def generate_opinion_number(
    project: Project, professional_category: ProfessionalCategory
) -> str:
    """生成意见编号：OPIN-{项目编号}-{专业代码}-{序列号}"""
    project_number = project.project_number or "UNKNOWN"
    profession_code = professional_category.code if professional_category else "GEN"
    prefix = f"OPIN-{project_number}-{profession_code}-"
    last_number = (
        Opinion.objects.filter(opinion_number__startswith=prefix)
        .order_by("-opinion_number")
        .values_list("opinion_number", flat=True)
        .first()
    )
    if last_number:
        try:
            sequence = int(last_number.split("-")[-1]) + 1
        except ValueError:
            sequence = 1
    else:
        sequence = 1
    return f"{prefix}{sequence:03d}"


def calculate_saving_amount(
    quantity_before: Optional[Decimal],
    quantity_after: Optional[Decimal],
    unit_price_before: Optional[Decimal],
    unit_price_after: Optional[Decimal],
) -> Decimal:
    """根据工程量与单价计算节省金额"""
    qb = Decimal(quantity_before or 0)
    qa = Decimal(quantity_after or 0)
    upb = Decimal(unit_price_before or 0)
    upa = Decimal(unit_price_after or 0)
    return (qb * upb) - (qa * upa)


def sync_opinion_participants(
    opinion: Opinion,
    participants_payload: Iterable[dict],
    operator=None,
) -> None:
    """同步意见参与人配置"""
    keep_ids = set()
    for item in participants_payload:
        user_value = item.get("user")
        if not user_value:
            continue
        if isinstance(user_value, dict):
            user_id = user_value.get("id")
        else:
            user_id = user_value
        try:
            user = User.objects.get(id=user_id, is_active=True)
        except (User.DoesNotExist, ValueError, TypeError):
            continue
        role = item.get("role") or OpinionParticipant.ParticipantRole.OBSERVER
        is_primary = bool(item.get("is_primary"))
        extra_info = item.get("extra_info") or {}
        participant, _ = OpinionParticipant.objects.update_or_create(
            opinion=opinion,
            user=user,
            role=role,
            defaults={
                "is_primary": is_primary,
                "extra_info": extra_info,
                "removed_at": None,
            },
        )
        keep_ids.add(participant.id)
    # 将未出现在 payload 中的记录标记为移除
    qs = OpinionParticipant.objects.filter(opinion=opinion)
    if keep_ids:
        qs.exclude(id__in=keep_ids).update(removed_at=timezone.now())
    else:
        qs.update(removed_at=timezone.now())


def sync_opinion_saving_items(
    opinion: Opinion,
    saving_items_payload: Iterable[dict],
) -> None:
    """同步节省金额分项"""
    existing_items = {item.id: item for item in opinion.saving_items.all()}
    keep_ids = set()
    for payload in saving_items_payload:
        item_id = payload.get("id")
        if item_id and item_id in existing_items:
            item = existing_items[item_id]
            for attr in ["category", "description", "quantity", "unit", "unit_saving", "total_saving", "notes"]:
                setattr(item, attr, payload.get(attr, getattr(item, attr)))
            if item.quantity is not None and item.unit_saving is not None:
                item.recalculate_total()
            item.save()
            keep_ids.add(item.id)
        else:
            item = OpinionSavingItem.objects.create(
                opinion=opinion,
                category=payload.get("category", OpinionSavingItem.SavingCategory.OTHER),
                description=payload.get("description", ""),
                quantity=payload.get("quantity"),
                unit=payload.get("unit", ""),
                unit_saving=payload.get("unit_saving"),
                total_saving=payload.get("total_saving"),
                notes=payload.get("notes", ""),
            )
            if item.quantity is not None and item.unit_saving is not None and item.total_saving in (None, 0):
                item.recalculate_total()
                item.save()
            keep_ids.add(item.id)
    if keep_ids:
        OpinionSavingItem.objects.filter(opinion=opinion).exclude(id__in=keep_ids).delete()
    else:
        opinion.saving_items.all().delete()


def record_workflow_log(
    opinion: Opinion,
    action: OpinionWorkflowLog.ActionType,
    operator=None,
    from_status: Optional[str] = None,
    to_status: Optional[str] = None,
    message: str = "",
    payload: Optional[dict] = None,
    operator_role: Optional[str] = None,
) -> OpinionWorkflowLog:
    """记录意见流程日志"""
    return OpinionWorkflowLog.objects.create(
        opinion=opinion,
        action=action,
        from_status=from_status,
        to_status=to_status,
        operator=operator,
        operator_role=operator_role,
        message=message or "",
        payload=payload or {},
    )


def infer_review_role(opinion: Opinion, user: User) -> str:
    """根据项目角色与参与人信息推断审核角色"""
    if not user or not getattr(user, "is_authenticated", False):
        return OpinionReview.ReviewRole.PROFESSIONAL_LEAD

    if opinion.project and opinion.project.project_manager_id == user.id:
        return OpinionReview.ReviewRole.PROJECT_LEAD

    participant_roles: Set[str] = set(
        opinion.participants.filter(user=user).values_list("role", flat=True)
    )

    if OpinionParticipant.ParticipantRole.QUALITY_MANAGER in participant_roles:
        return OpinionReview.ReviewRole.QUALITY_MANAGER
    if OpinionParticipant.ParticipantRole.PROJECT_MANAGER in participant_roles:
        return OpinionReview.ReviewRole.PROJECT_LEAD
    if OpinionParticipant.ParticipantRole.PROFESSIONAL_LEAD in participant_roles:
        return OpinionReview.ReviewRole.PROFESSIONAL_LEAD

    return OpinionReview.ReviewRole.PROFESSIONAL_LEAD


def build_opinion_statistics(
    project: Optional[Project] = None,
    as_of=None,
) -> dict:
    """构建意见统计数据"""
    as_of = as_of or timezone.now()
    snapshot_date = timezone.localdate(as_of)

    queryset = Opinion.objects.all()
    if project:
        queryset = queryset.filter(project=project)

    queryset = queryset.select_related("project", "professional_category")

    status_counts = {
        item["status"]: item["count"]
        for item in queryset.values("status").annotate(count=Count("id"))
    }

    pending_status = [
        Opinion.OpinionStatus.SUBMITTED,
        Opinion.OpinionStatus.IN_REVIEW,
        Opinion.OpinionStatus.NEEDS_UPDATE,
    ]
    pending_qs = queryset.filter(status__in=pending_status)
    pending_total = pending_qs.count()
    pending_unassigned = pending_qs.filter(current_reviewer__isnull=True).count()
    pending_overdue = pending_qs.filter(
        response_deadline__lt=snapshot_date, response_deadline__isnull=False
    ).count()

    cycle_avg = queryset.filter(cycle_time_hours__isnull=False).aggregate(
        avg=Avg("cycle_time_hours")
    )["avg"]
    avg_cycle_hours = float(cycle_avg) if cycle_avg is not None else None

    response_base_qs = queryset.filter(
        submitted_at__isnull=False,
        first_response_at__isnull=False,
        first_response_at__gte=F("submitted_at"),
    )
    response_delta = response_base_qs.aggregate(
        avg=Avg(
            ExpressionWrapper(
                F("first_response_at") - F("submitted_at"),
                output_field=DurationField(),
            )
        )
    )["avg"]
    if response_delta:
        avg_response_hours = round(response_delta.total_seconds() / 3600, 2)
    else:
        avg_response_hours = None

    response_within_24h = response_base_qs.annotate(
        delta=ExpressionWrapper(
            F("first_response_at") - F("submitted_at"),
            output_field=DurationField(),
        )
    ).filter(delta__lte=timedelta(hours=24)).count()
    response_total = response_base_qs.count()

    cycle_base_qs = queryset.filter(
        submitted_at__isnull=False,
        closed_at__isnull=False,
        closed_at__gte=F("submitted_at"),
    )
    cycle_within_7d = cycle_base_qs.annotate(
        delta=ExpressionWrapper(
            F("closed_at") - F("submitted_at"),
            output_field=DurationField(),
        )
    ).filter(delta__lte=timedelta(days=7)).count()
    cycle_total = cycle_base_qs.count()

    total_saving = queryset.aggregate(total=Sum("saving_amount"))["total"] or Decimal("0")
    recent_cutoff = as_of - timedelta(days=30)
    recent_saving = (
        queryset.filter(
            status=Opinion.OpinionStatus.APPROVED,
            reviewed_at__gte=recent_cutoff,
        ).aggregate(total=Sum("saving_amount"))["total"]
        or Decimal("0")
    )

    review_qs = OpinionReview.objects.filter(opinion__in=queryset)
    review_status_counts = {
        item["status"]: item["count"]
        for item in review_qs.values("status").annotate(count=Count("id"))
    }
    review_role_counts = {
        item["role"]: item["count"]
        for item in review_qs.values("role").annotate(count=Count("id"))
    }
    review_total = sum(review_status_counts.values())

    reminder_qs = ProjectTeamNotification.objects.filter(category="quality_alert")
    if project:
        reminder_qs = reminder_qs.filter(project=project)
    pending_reminders_qs = reminder_qs.filter(is_read=False)
    reminder_pending_counts = {
        (item["context__alert_type"] or "unknown"): item["count"]
        for item in pending_reminders_qs.values("context__alert_type").annotate(count=Count("id"))
    }
    reminder_window_start = as_of - timedelta(days=7)
    reminders_sent_7d = reminder_qs.filter(created_time__gte=reminder_window_start).count()
    reminders_ack_7d = reminder_qs.filter(
        is_read=True,
        read_time__isnull=False,
        read_time__gte=reminder_window_start,
    ).count()

    data = {
        "generated_at": as_of.isoformat(),
        "counts": {
            "status": status_counts,
        },
        "pending": {
            "total": pending_total,
            "unassigned": pending_unassigned,
            "overdue": pending_overdue,
        },
        "averages": {
            "cycle_time_hours": avg_cycle_hours,
            "first_response_hours": avg_response_hours,
        },
        "sla": {
            "averages": {
                "cycle_time_hours": avg_cycle_hours,
                "first_response_hours": avg_response_hours,
            },
            "compliance": {
                "response_within_24h": {
                    "met": response_within_24h,
                    "total": response_total,
                    "rate": round(response_within_24h / response_total * 100, 1)
                    if response_total
                    else None,
                },
                "cycle_within_7d": {
                    "met": cycle_within_7d,
                    "total": cycle_total,
                    "rate": round(cycle_within_7d / cycle_total * 100, 1)
                    if cycle_total
                    else None,
                },
            },
        },
        "financial": {
            "total_saving": float(total_saving),
            "recent_saving": float(recent_saving),
        },
        "reviews": {
            "total": review_total,
            "status": review_status_counts,
            "role": review_role_counts,
        },
        "reminders": {
            "pending_total": pending_reminders_qs.count(),
            "pending_by_type": reminder_pending_counts,
            "sent_last_7_days": reminders_sent_7d,
            "ack_last_7_days": reminders_ack_7d,
        },
    }
    return data


def capture_opinion_statistics(
    project: Optional[Project] = None,
    statistic_type: str = "quality",
    as_of=None,
) -> ProductionStatistic:
    """采集意见统计快照，并写入 ProductionStatistic"""
    as_of = as_of or timezone.now()
    snapshot_date = timezone.localdate(as_of)
    payload = build_opinion_statistics(project=project, as_of=as_of)
    statistic, _ = ProductionStatistic.objects.update_or_create(
        project=project,
        statistic_type=statistic_type,
        snapshot_date=snapshot_date,
        defaults={"payload": payload},
    )
    return statistic


def _ensure_quality_notification(
    *,
    opinion: Opinion,
    recipient: User,
    alert_type: str,
    title: str,
    message: str,
) -> Optional[ProjectTeamNotification]:
    if recipient is None or not recipient.is_active:
        return None
    context = {"opinion_id": opinion.id, "alert_type": alert_type}
    existing = ProjectTeamNotification.objects.filter(
        recipient=recipient,
        project=opinion.project,
        category="quality_alert",
        context__opinion_id=opinion.id,
        context__alert_type=alert_type,
        is_read=False,
    ).first()
    action_url = reverse("production_quality_pages:opinion_review_detail", args=[opinion.id])
    if existing:
        if existing.message != message or existing.title != title:
            existing.message = message
            existing.title = title
            existing.action_url = action_url
            existing.context = context
            existing.save(update_fields=["message", "title", "action_url", "context"])
        return existing

    return ProjectTeamNotification.objects.create(
        project=opinion.project,
        recipient=recipient,
        operator=opinion.current_reviewer,
        title=title,
        message=message,
        category="quality_alert",
        action_url=action_url,
        context=context,
    )


def dispatch_quality_alerts(as_of=None) -> dict:
    """为超期或未指派的意见生成质量提醒"""
    as_of = as_of or timezone.now()
    snapshot_date = timezone.localdate(as_of)
    pending_status = [
        Opinion.OpinionStatus.SUBMITTED,
        Opinion.OpinionStatus.IN_REVIEW,
        Opinion.OpinionStatus.NEEDS_UPDATE,
    ]
    opinions = (
        Opinion.objects.filter(status__in=pending_status)
        .select_related(
            "project",
            "project__project_manager",
            "project__business_manager",
            "current_reviewer",
            "created_by",
        )
        .order_by("-submitted_at")
    )

    created_count = 0
    email_count = 0
    wecom_count = 0
    for opinion in opinions:
        project = opinion.project
        project_manager = getattr(project, "project_manager", None)
        business_manager = getattr(project, "business_manager", None)
        recipients_unassigned_ids: Set[int] = set()
        recipients_overdue_ids: Set[int] = set()

        alert_messages = []

        if opinion.current_reviewer is None:
            for user_obj in [project_manager, business_manager, opinion.created_by]:
                if user_obj and user_obj.is_active:
                    recipients_unassigned_ids.add(user_obj.id)
            alert_messages.append(
                (
                    "unassigned",
                    "待指派审核",
                    f"意见「{opinion.location_name}」尚未指派审核人，请尽快安排审核。",
                )
            )

        if opinion.response_deadline and opinion.response_deadline < snapshot_date:
            for user_obj in [
                opinion.current_reviewer or project_manager,
                project_manager,
                opinion.created_by,
            ]:
                if user_obj and user_obj.is_active:
                    recipients_overdue_ids.add(user_obj.id)
            alert_messages.append(
                (
                    "overdue",
                    "意见已超期",
                    f"意见「{opinion.location_name}」已于 {opinion.response_deadline.strftime('%m-%d')} 超过整改期限。",
                )
            )

        for alert_type, title, message in alert_messages:
            target_ids = recipients_unassigned_ids if alert_type == "unassigned" else recipients_overdue_ids
            for user_id in target_ids:
                recipient = User.objects.filter(id=user_id, is_active=True).first()
                notif = _ensure_quality_notification(
                    opinion=opinion,
                    recipient=recipient,
                    alert_type=alert_type,
                    title=title,
                    message=message,
                )
                if notif and recipient:
                    created_count += 1
                    email_address = getattr(recipient, "email", "")
                    if email_address:
                        sent_email = send_email_notification(
                            NotificationMessage(
                                subject=f"[质量提醒] {title}",
                                body=f"{message}\n项目：{opinion.project.name if opinion.project else '未关联'}",
                                to_emails=[email_address],
                            )
                        )
                        if sent_email:
                            email_count += 1
                    wecom_userid = getattr(recipient, "wecom_userid", "") or settings.WECOM_DEFAULT_TO_USER
                    if wecom_userid:
                        sent_wecom = send_wecom_notification(
                            NotificationMessage(
                                subject=title,
                                body=f"{message}\n项目：{opinion.project.project_number if opinion.project else ''}",
                                to_wecom=[wecom_userid] if wecom_userid else None,
                            )
                        )
                        if sent_wecom:
                            wecom_count += 1

    return {
        "created": created_count,
        "processed": opinions.count(),
        "email_sent": email_count,
        "wecom_sent": wecom_count,
    }

