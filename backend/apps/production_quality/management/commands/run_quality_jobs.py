from __future__ import annotations

from typing import List

from django.core.management import BaseCommand, CommandError, call_command


class Command(BaseCommand):
    help = """运行质量统计快照与提醒派发的组合任务。

    默认会先生成全局质量统计快照（capture_opinion_stats --type quality），
    针对传入的项目 ID 依次生成项目级快照，最后触发 issue_quality_alerts 发送提醒。
    可通过参数跳过其中部分步骤。"""

    def add_arguments(self, parser):
        parser.add_argument(
            "--project",
            action="append",
            dest="projects",
            type=int,
            help="指定需要额外生成统计快照的项目 ID，可多次传入。",
        )
        parser.add_argument(
            "--stat-type",
            default="quality",
            help="统计类型，对应 capture_opinion_stats 的 --type 参数，默认 quality。",
        )
        parser.add_argument(
            "--skip-global",
            action="store_true",
            help="跳过全局快照，仅对指定项目执行统计。",
        )
        parser.add_argument(
            "--skip-alerts",
            action="store_true",
            help="跳过 issue_quality_alerts，仅生成统计快照。",
        )

    def handle(self, *args, **options):
        projects: List[int] = options.get("projects") or []
        stat_type: str = options.get("stat_type") or "quality"
        skip_global: bool = options.get("skip_global", False)
        skip_alerts: bool = options.get("skip_alerts", False)

        self.stdout.write(self.style.MIGRATE_HEADING("[1/3] 质量统计快照"))
        try:
            if not skip_global:
                self._run_capture(stat_type=stat_type)
            for project_id in projects:
                self._run_capture(stat_type=stat_type, project_id=project_id)
        except CommandError as exc:
            raise CommandError(f"统计快照执行失败：{exc}") from exc

        if skip_alerts:
            self.stdout.write(self.style.WARNING("跳过提醒派发步骤 (--skip-alerts)。"))
            return

        self.stdout.write(self.style.MIGRATE_HEADING("[2/3] 质量提醒派发"))
        try:
            call_command("issue_quality_alerts")
        except CommandError as exc:
            raise CommandError(f"质量提醒派发失败：{exc}") from exc

        self.stdout.write(self.style.SUCCESS("[3/3] 质量统计与提醒任务执行完成。"))

    def _run_capture(self, *, stat_type: str, project_id: int | None = None) -> None:
        kwargs = {"type": stat_type}
        label = "全局"
        if project_id is not None:
            kwargs["project"] = project_id
            label = f"项目 {project_id}"
        self.stdout.write(self.style.NOTICE(f"生成 {label} {stat_type} 统计快照..."))
        call_command("capture_opinion_stats", **kwargs)
