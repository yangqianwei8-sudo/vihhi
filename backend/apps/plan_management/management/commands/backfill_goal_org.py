"""
回填 StrategicGoal 的 company 和 org_department 字段（历史数据）

注意：当前 StrategicGoal 模型无 company/org_department 字段，本命令已废弃。
仅 Plan 模型有此字段，请使用 backfill_plan_org。
"""
from django.core.management.base import BaseCommand
from django.contrib.auth import get_user_model
from django.db import transaction

from backend.apps.plan_management.models import StrategicGoal

User = get_user_model()


class Command(BaseCommand):
    help = "Backfill StrategicGoal.company/org_department（已废弃：StrategicGoal 无此字段）"

    def add_arguments(self, parser):
        parser.add_argument("--dry-run", action="store_true", help="只显示将要更新的数据，不实际更新")

    @transaction.atomic
    def handle(self, *args, **opts):
        if not hasattr(StrategicGoal, "company") or not hasattr(StrategicGoal, "org_department"):
            self.stdout.write(self.style.WARNING(
                "跳过：StrategicGoal 模型无 company/org_department 字段。"
                "仅 Plan 有此字段，请使用 backfill_plan_org 命令。"
            ))
            return

