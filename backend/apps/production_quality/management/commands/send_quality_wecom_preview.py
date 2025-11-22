from __future__ import annotations

from datetime import datetime
from typing import List

from django.conf import settings
from django.core.management import BaseCommand, CommandError

from backend.apps.production_quality.models import ProductionStatistic
from backend.apps.production_quality.utils.notifications import (
    NotificationMessage,
    send_wecom_notification,
)


class Command(BaseCommand):
    help = """向企业微信发送质量统计提醒预览消息。

    默认使用最新的质量统计快照，支持通过 --project 定位项目快照，
    通过 --to 指定接收人（企业微信 userid，支持多次传入）。
    """

    def add_arguments(self, parser):
        parser.add_argument(
            "--project",
            type=int,
            help="指定项目 ID，若不传则使用全局快照。",
        )
        parser.add_argument(
            "--stat-date",
            type=str,
            help="指定快照日期（YYYY-MM-DD），默认为最新。",
        )
        parser.add_argument(
            "--to",
            action="append",
            dest="recipients",
            help="企业微信接收人 userid，可多次传入；若不传则使用 WECOM_DEFAULT_TO_USER。",
        )

    def handle(self, *args, **options):
        recipients: List[str] = options.get("recipients") or []
        project_id: int | None = options.get("project")
        stat_date: str | None = options.get("stat_date")

        if not recipients:
            default_to = getattr(settings, "WECOM_DEFAULT_TO_USER", "") or ""
            if default_to:
                recipients = [user.strip() for user in default_to.split("|") if user.strip()]
        if not recipients:
            raise CommandError("请通过 --to 指定接收人，或在配置中设置 WECOM_DEFAULT_TO_USER。")

        queryset = ProductionStatistic.objects.filter(statistic_type="quality").order_by(
            "-snapshot_date", "-id"
        )
        if project_id:
            queryset = queryset.filter(project_id=project_id)
        else:
            queryset = queryset.filter(project__isnull=True)
        if stat_date:
            try:
                date_value = datetime.strptime(stat_date, "%Y-%m-%d").date()
            except ValueError as exc:  # noqa: BLE001
                raise CommandError("stat-date 格式应为 YYYY-MM-DD") from exc
            queryset = queryset.filter(snapshot_date=date_value)

        statistic = queryset.select_related("project").first()
        if not statistic:
            scope = f"项目 {project_id}" if project_id else "全局"
            raise CommandError(f"未找到 {scope} 的质量统计快照，请先运行 capture_opinion_stats。")

        payload = statistic.payload or {}
        pending = payload.get("pending", {}) or {}
        sla_payload = payload.get("sla", {}) or {}
        compliance = sla_payload.get("compliance", {}) or {}
        reminders = payload.get("reminders", {}) or {}

        response_rate = compliance.get("response_within_24h", {}).get("rate")
        cycle_rate = compliance.get("cycle_within_7d", {}).get("rate")

        subject = "【质量提醒预览】"
        if statistic.project:
            subject += f"{statistic.project.project_number} {statistic.project.name}"
        else:
            subject += "全局汇总"

        body_lines = [
            f"统计日期：{statistic.snapshot_date:%Y-%m-%d}",
            f"待审核：{pending.get('total', 0)}",
            f"未指派：{pending.get('unassigned', 0)}",
            f"超期：{pending.get('overdue', 0)}",
            f"24h 首响达成率：{response_rate:.1f}%" if response_rate is not None else "24h 首响达成率：--",
            f"7天结案达成率：{cycle_rate:.1f}%" if cycle_rate is not None else "7天结案达成率：--",
            f"未读提醒：{reminders.get('pending_total', 0)}",
        ]
        action_url = reminders.get("action_url")
        if action_url:
            body_lines.append(f"查看详情：{action_url}")

        message = NotificationMessage(
            subject=subject,
            body="\n".join(body_lines),
            to_wecom=recipients,
        )

        success = send_wecom_notification(message)
        if not success:
            raise CommandError("发送企业微信消息失败，请检查配置（corp_id / agent_secret / wechatpy）。")

        self.stdout.write(self.style.SUCCESS(f"已向 {', '.join(recipients)} 发送质量提醒预览。"))

