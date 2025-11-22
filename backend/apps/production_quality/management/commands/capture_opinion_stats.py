from datetime import datetime

from django.core.management.base import BaseCommand, CommandError
from django.utils import timezone

from backend.apps.project_center.models import Project

from ...models import ProductionStatistic
from ...services import capture_opinion_statistics


class Command(BaseCommand):
    help = "采集咨询意见统计快照并写入 ProductionStatistic"

    def add_arguments(self, parser):
        parser.add_argument(
            "--project",
            type=int,
            help="指定项目 ID，仅统计该项目意见；不传则统计全局数据",
        )
        parser.add_argument(
            "--date",
            type=str,
            help="快照日期，格式 YYYY-MM-DD；默认今天",
        )
        parser.add_argument(
            "--type",
            type=str,
            default="quality",
            choices=[choice[0] for choice in ProductionStatistic.STAT_TYPE_CHOICES],
            help="统计类型（默认 quality）",
        )

    def handle(self, *args, **options):
        project_id = options.get("project")
        snapshot_date_str = options.get("date")
        statistic_type = options.get("type")

        project = None
        if project_id is not None:
            try:
                project = Project.objects.get(pk=project_id)
            except Project.DoesNotExist as exc:
                raise CommandError(f"项目 {project_id} 不存在") from exc

        if snapshot_date_str:
            try:
                snapshot_date = datetime.strptime(snapshot_date_str, "%Y-%m-%d")
                as_of = timezone.make_aware(snapshot_date)
            except ValueError as exc:
                raise CommandError("日期格式错误，应为 YYYY-MM-DD") from exc
        else:
            as_of = timezone.now()

        statistic = capture_opinion_statistics(
            project=project,
            statistic_type=statistic_type,
            as_of=as_of,
        )

        target = f"项目 {project.id}" if project else "全局"
        self.stdout.write(
            self.style.SUCCESS(
                f"已生成 {target} {statistic_type} 统计快照（日期 {statistic.snapshot_date}）。"
            )
        )

