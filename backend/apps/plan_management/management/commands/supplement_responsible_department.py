"""
补充目标和计划的所属部门信息
从负责人的部门或创建人的部门获取
"""
from django.core.management.base import BaseCommand
from django.db import transaction
from django.db.models import Q

from backend.apps.plan_management.models import StrategicGoal, Plan
from backend.apps.system_management.models import Department


class Command(BaseCommand):
    help = "补充目标和计划的所属部门信息（从负责人或创建人的部门获取）"

    def add_arguments(self, parser):
        parser.add_argument(
            "--dry-run",
            action="store_true",
            help="只显示将要更新的数据，不实际更新"
        )
        parser.add_argument(
            "--model",
            type=str,
            choices=["goal", "plan", "all"],
            default="all",
            help="要处理的模型类型：goal（目标）、plan（计划）、all（全部）"
        )

    @transaction.atomic
    def handle(self, *args, **opts):
        dry_run = opts["dry_run"]
        model_type = opts["model"]

        # 处理目标
        if model_type in ["goal", "all"]:
            self.stdout.write("\n" + "=" * 60)
            self.stdout.write("处理战略目标（StrategicGoal）")
            self.stdout.write("=" * 60)
            self._process_goals(dry_run)

        # 处理计划
        if model_type in ["plan", "all"]:
            self.stdout.write("\n" + "=" * 60)
            self.stdout.write("处理计划（Plan）")
            self.stdout.write("=" * 60)
            self._process_plans(dry_run)

        if dry_run:
            self.stdout.write(self.style.WARNING("\n[DRY RUN] 以上操作未实际执行"))
            transaction.set_rollback(True)
        else:
            self.stdout.write(self.style.SUCCESS("\n✅ 所有操作完成！"))

    def _process_goals(self, dry_run):
        """处理战略目标的所属部门"""
        # 查找需要补充的目标（responsible_department 为空）
        goals = StrategicGoal.objects.filter(
            responsible_department__isnull=True
        ).select_related(
            "responsible_person",
            "responsible_person__department",
            "created_by",
            "created_by__department"
        )

        total = goals.count()

        if total == 0:
            self.stdout.write(self.style.SUCCESS("✓ 没有需要补充所属部门的目标"))
            return

        self.stdout.write(f"找到 {total} 个需要补充所属部门的目标")

        updated = 0
        skipped = 0
        stats = {
            "from_responsible": 0,
            "from_creator": 0,
            "no_department": 0
        }

        for goal in goals:
            department = None
            source = None

            # 策略1: 从负责人的部门获取
            if goal.responsible_person and goal.responsible_person.department:
                department = goal.responsible_person.department
                source = "负责人"
                stats["from_responsible"] += 1

            # 策略2: 从创建人的部门获取
            elif goal.created_by and goal.created_by.department:
                department = goal.created_by.department
                source = "创建人"
                stats["from_creator"] += 1

            # 策略3: 都没有，保持为空
            else:
                stats["no_department"] += 1
                if not dry_run:
                    self.stdout.write(
                        self.style.WARNING(
                            f"  ⚠ 目标 {goal.id} ({goal.goal_number}): "
                            f"负责人和创建人都没有部门，保持为空"
                        )
                    )
                else:
                    self.stdout.write(
                        f"  [DRY RUN] 目标 {goal.id} ({goal.goal_number}): "
                        f"负责人和创建人都没有部门，将保持为空"
                    )
                skipped += 1
                continue

            if dry_run:
                self.stdout.write(
                    f"  [DRY RUN] 目标 {goal.id} ({goal.goal_number}): "
                    f"responsible_department = {department.name} (来源: {source})"
                )
            else:
                goal.responsible_department = department
                goal.save(update_fields=["responsible_department"])
                self.stdout.write(
                    self.style.SUCCESS(
                        f"  ✓ 目标 {goal.id} ({goal.goal_number}): "
                        f"responsible_department = {department.name} (来源: {source})"
                    )
                )
                updated += 1

        # 输出统计信息
        self.stdout.write("\n统计信息:")
        self.stdout.write(f"  从负责人部门获取: {stats['from_responsible']} 个")
        self.stdout.write(f"  从创建人部门获取: {stats['from_creator']} 个")
        self.stdout.write(f"  无法获取部门: {stats['no_department']} 个")
        self.stdout.write(f"  总计更新: {updated} 个")
        self.stdout.write(f"  跳过: {skipped} 个")

    def _process_plans(self, dry_run):
        """处理计划的所属部门"""
        # 查找需要补充的计划（responsible_department 为空）
        plans = Plan.objects.filter(
            responsible_department__isnull=True
        ).select_related(
            "responsible_person",
            "responsible_person__department",
            "created_by",
            "created_by__department"
        )

        total = plans.count()

        if total == 0:
            self.stdout.write(self.style.SUCCESS("✓ 没有需要补充所属部门的计划"))
            return

        self.stdout.write(f"找到 {total} 个需要补充所属部门的计划")

        updated = 0
        skipped = 0
        stats = {
            "from_responsible": 0,
            "from_creator": 0,
            "no_department": 0
        }

        for plan in plans:
            department = None
            source = None

            # 策略1: 从负责人的部门获取
            if plan.responsible_person and plan.responsible_person.department:
                department = plan.responsible_person.department
                source = "负责人"
                stats["from_responsible"] += 1

            # 策略2: 从创建人的部门获取
            elif plan.created_by and plan.created_by.department:
                department = plan.created_by.department
                source = "创建人"
                stats["from_creator"] += 1

            # 策略3: 都没有，保持为空
            else:
                stats["no_department"] += 1
                if not dry_run:
                    self.stdout.write(
                        self.style.WARNING(
                            f"  ⚠ 计划 {plan.id} ({plan.plan_number}): "
                            f"负责人和创建人都没有部门，保持为空"
                        )
                    )
                else:
                    self.stdout.write(
                        f"  [DRY RUN] 计划 {plan.id} ({plan.plan_number}): "
                        f"负责人和创建人都没有部门，将保持为空"
                    )
                skipped += 1
                continue

            if dry_run:
                self.stdout.write(
                    f"  [DRY RUN] 计划 {plan.id} ({plan.plan_number}): "
                    f"responsible_department = {department.name} (来源: {source})"
                )
            else:
                plan.responsible_department = department
                plan.save(update_fields=["responsible_department"])
                self.stdout.write(
                    self.style.SUCCESS(
                        f"  ✓ 计划 {plan.id} ({plan.plan_number}): "
                        f"responsible_department = {department.name} (来源: {source})"
                    )
                )
                updated += 1

        # 输出统计信息
        self.stdout.write("\n统计信息:")
        self.stdout.write(f"  从负责人部门获取: {stats['from_responsible']} 个")
        self.stdout.write(f"  从创建人部门获取: {stats['from_creator']} 个")
        self.stdout.write(f"  无法获取部门: {stats['no_department']} 个")
        self.stdout.write(f"  总计更新: {updated} 个")
        self.stdout.write(f"  跳过: {skipped} 个")
