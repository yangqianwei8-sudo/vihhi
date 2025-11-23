from __future__ import annotations

import csv
import io
from datetime import datetime

from django.core.management.base import BaseCommand, CommandError
from django.utils import timezone

from openpyxl import Workbook

from backend.apps.project_center.models import Project
from ...models import OpinionReview, ProductionStatistic


class Command(BaseCommand):
    help = "导出生产统计快照为 CSV/Excel/PDF 文件"

    def add_arguments(self, parser):
        parser.add_argument(
            "--project",
            type=int,
            help="指定项目 ID，仅导出该项目的快照；不传则导出全局快照。",
        )
        parser.add_argument(
            "--from",
            dest="date_from",
            type=str,
            help="起始日期 YYYY-MM-DD（含），默认无下限。",
        )
        parser.add_argument(
            "--to",
            dest="date_to",
            type=str,
            help="结束日期 YYYY-MM-DD（含），默认当天。",
        )
        parser.add_argument(
            "--output",
            type=str,
            default="statistics_export.csv",
            help="输出文件路径（默认 statistics_export.csv）。",
        )
        parser.add_argument(
            "--format",
            choices=["csv", "xlsx", "pdf"],
            help="导出格式，默认根据文件后缀自动判断。",
        )

    def handle(self, *args, **options):
        project_id = options.get("project")
        date_from_str = options.get("date_from")
        date_to_str = options.get("date_to")
        output_path = options.get("output")
        output_format = options.get("format")

        project = None
        if project_id is not None:
            try:
                project = Project.objects.get(pk=project_id)
            except Project.DoesNotExist as exc:
                raise CommandError(f"未找到项目 {project_id}") from exc

        queryset = ProductionStatistic.objects.filter(statistic_type="quality")
        if project:
            queryset = queryset.filter(project=project)
        else:
            queryset = queryset.filter(project__isnull=True)

        if date_from_str:
            try:
                date_from = datetime.strptime(date_from_str, "%Y-%m-%d").date()
                queryset = queryset.filter(snapshot_date__gte=date_from)
            except ValueError as exc:
                raise CommandError("起始日期格式应为 YYYY-MM-DD") from exc

        if date_to_str:
            try:
                date_to = datetime.strptime(date_to_str, "%Y-%m-%d").date()
                queryset = queryset.filter(snapshot_date__lte=date_to)
            except ValueError as exc:
                raise CommandError("结束日期格式应为 YYYY-MM-DD") from exc
        else:
            queryset = queryset.filter(snapshot_date__lte=timezone.localdate())

        queryset = queryset.order_by("snapshot_date", "project_id")

        if not output_format:
            lower_path = (output_path or "").lower()
            if lower_path.endswith(".xlsx"):
                output_format = "xlsx"
            elif lower_path.endswith(".pdf"):
                output_format = "pdf"
            else:
                output_format = "csv"

        headers = [
            "snapshot_date",
            "project_number",
            "pending_total",
            "pending_unassigned",
            "pending_overdue",
            "avg_cycle_hours",
            "avg_response_hours",
            "total_saving",
            "recent_saving",
            "response_within_24h_rate",
            "cycle_within_7d_rate",
            "review_total",
            "review_approved",
            "review_rejected",
            "reminders_pending",
            "reminders_sent_last_7_days",
            "reminders_ack_last_7_days",
        ]

        rows = []
        for stat in queryset.iterator():
            payload = stat.payload or {}
            pending = payload.get("pending", {})
            averages = payload.get("averages", {})
            financial = payload.get("financial", {})
            sla_payload = payload.get("sla", {}) or {}
            compliance_payload = sla_payload.get("compliance", {}) or {}
            reviews_payload = payload.get("reviews", {}) or {}
            reminders_payload = payload.get("reminders", {}) or {}
            review_status_payload = reviews_payload.get("status", {}) or {}
            rows.append([
                stat.snapshot_date.strftime("%Y-%m-%d"),
                stat.project.project_number if stat.project else "GLOBAL",
                pending.get("total", 0),
                pending.get("unassigned", 0),
                pending.get("overdue", 0),
                averages.get("cycle_time_hours", ""),
                averages.get("first_response_hours", ""),
                financial.get("total_saving", ""),
                financial.get("recent_saving", ""),
                compliance_payload.get("response_within_24h", {}).get("rate", ""),
                compliance_payload.get("cycle_within_7d", {}).get("rate", ""),
                reviews_payload.get("total", 0),
                review_status_payload.get(OpinionReview.ReviewStatus.APPROVED, 0),
                review_status_payload.get(OpinionReview.ReviewStatus.REJECTED, 0),
                reminders_payload.get("pending_total", 0),
                reminders_payload.get("sent_last_7_days", 0),
                reminders_payload.get("ack_last_7_days", 0),
            ])

        count = len(rows)

        if output_format == "csv":
            buffer = io.StringIO()
            writer = csv.writer(buffer)
            writer.writerow(headers)
            writer.writerows(rows)
            with open(output_path, "w", encoding="utf-8", newline="") as csvfile:
                csvfile.write(buffer.getvalue())
        elif output_format == "xlsx":
            workbook = Workbook()
            sheet = workbook.active
            sheet.title = "Statistics"
            sheet.append(headers)
            for row in rows:
                sheet.append(row)
            workbook.save(output_path)
        elif output_format == "pdf":
            try:
                from reportlab.lib import colors
                from reportlab.lib.pagesizes import A4
                from reportlab.lib.styles import getSampleStyleSheet
                from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph, Spacer
            except ImportError as exc:
                raise CommandError("生成 PDF 需要安装 reportlab 库，请先安装。") from exc

            doc = SimpleDocTemplate(output_path, pagesize=A4)
            styles = getSampleStyleSheet()
            table_data = [headers] + rows
            table = Table(table_data, repeatRows=1)
            table.setStyle(TableStyle([
                ("BACKGROUND", (0, 0), (-1, 0), colors.lightgrey),
                ("TEXTCOLOR", (0, 0), (-1, 0), colors.black),
                ("ALIGN", (0, 0), (-1, -1), "CENTER"),
                ("GRID", (0, 0), (-1, -1), 0.25, colors.grey),
                ("ROWBACKGROUNDS", (0, 1), (-1, -1), [colors.whitesmoke, colors.lightyellow]),
            ]))
            story = [Paragraph("生产统计快照导出", styles["Heading2"]), Spacer(1, 12), table]
            doc.build(story)
        else:
            raise CommandError(f"不支持的导出格式：{output_format}")

        self.stdout.write(
            self.style.SUCCESS(
                f"已导出 {count} 条统计记录到 {output_path}。"
            )
        )

