"""
重新计算计划状态（定时纠偏）
"""
from django.core.management.base import BaseCommand
from django.utils import timezone
from backend.apps.plan_management.models import Plan
from backend.apps.plan_management.services import recalc_plan_status


class Command(BaseCommand):
    help = "重新计算计划状态，避免状态漂移"

    def add_arguments(self, parser):
        parser.add_argument(
            "--dry-run",
            action="store_true",
            help="Dry run without saving"
        )
        parser.add_argument(
            "--company-id",
            type=int,
            default=None,
            help="只处理指定公司的计划"
        )

    def handle(self, *args, **options):
        qs = Plan.objects.all()
        
        if options["company_id"]:
            qs = qs.filter(company_id=options["company_id"])
            self.stdout.write(f"只处理公司 ID={options['company_id']} 的计划")

        now = timezone.now()
        changed = 0
        total = qs.count()

        self.stdout.write(f"开始处理 {total} 个计划...")

        for plan in qs.iterator():
            res = recalc_plan_status(plan)
            if res.changed:
                changed += 1
                self.stdout.write(
                    f"计划 {plan.plan_number} ({plan.name}): "
                    f"{res.old} -> {res.new}"
                )
                if not options["dry_run"]:
                    # 字段治理说明：这是 status 字段的写入口之一（定时任务自动纠偏）。
                    # 第四刀修正：完成日志统一由 Plan.save() 兜底保证，避免重复写 log。
                    # 如果状态变为 completed，Plan.save() 会自动写 completed log（changed_by=None, change_reason='系统自动完成：进度达到100%'）。
                    plan.save(update_fields=["status"])

        self.stdout.write(
            self.style.SUCCESS(
                f"完成。时间={now.isoformat()} "
                f"总数={total} 变更={changed} "
                f"dry_run={options['dry_run']}"
            )
        )

