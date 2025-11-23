from django.core.management.base import BaseCommand

from ...services import dispatch_quality_alerts


class Command(BaseCommand):
    help = "为超期或未指派的咨询意见生成质量提醒通知"

    def handle(self, *args, **options):
        result = dispatch_quality_alerts()
        created = result.get("created", 0)
        processed = result.get("processed", 0)
        self.stdout.write(
            self.style.SUCCESS(
                f"已处理 {processed} 条意见，新增质量提醒 {created} 条。"
            )
        )

