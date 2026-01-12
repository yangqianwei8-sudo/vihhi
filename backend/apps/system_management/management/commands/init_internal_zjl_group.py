"""
D1 收口：初始化 INTERNAL_ZJL Group 并绑定 plan_management 权限

目标：
- 创建 Django Group：INTERNAL_ZJL
- 自动绑定 plan_management 的所有 view_*, change_*, approve_* 权限
- 以后不再靠 __all__ 这种隐式逻辑救火

这是权限职责边界固化的关键一步，确保权限判断的唯一来源。
"""
from django.core.management.base import BaseCommand
from django.contrib.auth.models import Group, Permission
from django.contrib.contenttypes.models import ContentType
from django.db import transaction

from backend.apps.plan_management.models import Plan, StrategicGoal


# INTERNAL_ZJL Group 需要绑定的权限列表
PLAN_MANAGEMENT_PERMISSIONS = [
    # Plan 相关权限
    'plan_management.view_plan',
    'plan_management.change_plan',
    'plan_management.approve_plan',
    # StrategicGoal 相关权限
    'plan_management.view_strategicgoal',
    'plan_management.change_strategicgoal',
    'plan_management.approve_strategicgoal',
]


class Command(BaseCommand):
    help = "初始化 INTERNAL_ZJL Group 并绑定 plan_management 相关权限（D1 收口）"

    def add_arguments(self, parser):
        parser.add_argument(
            "--dry-run",
            action="store_true",
            help="仅显示将要执行的操作，不实际修改数据库"
        )

    @transaction.atomic
    def handle(self, *args, **options):
        dry_run = options["dry_run"]
        group_name = "INTERNAL_ZJL"

        if dry_run:
            self.stdout.write(self.style.WARNING("🔍 模拟运行模式，不会实际修改数据"))

        self.stdout.write(f"开始初始化 {group_name} Group...\n")

        # 1) 创建或获取 Group
        group, group_created = Group.objects.get_or_create(name=group_name)
        if group_created:
            self.stdout.write(self.style.SUCCESS(f"  ✓ 创建 Group: {group_name}"))
        else:
            self.stdout.write(f"  - Group 已存在: {group_name}")

        # 2) 获取 ContentType
        try:
            plan_ct = ContentType.objects.get_for_model(Plan)
            goal_ct = ContentType.objects.get_for_model(StrategicGoal)
        except Exception as e:
            self.stdout.write(self.style.ERROR(f"  错误：无法获取 ContentType: {e}"))
            return

        # 3) 收集所有需要绑定的权限
        wanted_perms = []
        for perm_codename in PLAN_MANAGEMENT_PERMISSIONS:
            # 解析权限：app_label.codename
            parts = perm_codename.split('.', 1)
            if len(parts) != 2:
                self.stdout.write(self.style.WARNING(f"  ⚠ 跳过无效权限格式: {perm_codename}"))
                continue

            app_label, codename = parts

            # 确定 ContentType
            if 'plan' in codename.lower() and 'goal' not in codename.lower():
                ct = plan_ct
            elif 'goal' in codename.lower() or 'strategicgoal' in codename.lower():
                ct = goal_ct
            else:
                # 默认使用 plan_ct
                ct = plan_ct

            # 查找权限
            try:
                perm = Permission.objects.get(
                    content_type=ct,
                    codename=codename
                )
                wanted_perms.append(perm)
                self.stdout.write(f"  ✓ 找到权限: {perm_codename}")
            except Permission.DoesNotExist:
                self.stdout.write(self.style.WARNING(f"  ⚠ 权限不存在: {perm_codename}"))
            except Permission.MultipleObjectsReturned:
                self.stdout.write(self.style.WARNING(f"  ⚠ 权限重复: {perm_codename}"))

        if not wanted_perms:
            self.stdout.write(self.style.ERROR("  错误：没有找到任何权限"))
            return

        # 4) 检查并添加缺失的权限
        existing_perm_ids = set(group.permissions.values_list('id', flat=True))
        missing_perms = [p for p in wanted_perms if p.id not in existing_perm_ids]

        if missing_perms:
            missing_codenames = [f"{p.content_type.app_label}.{p.codename}" for p in missing_perms]
            self.stdout.write(
                self.style.WARNING(
                    f"  ⚠ [{group_name}] 需要添加的权限 ({len(missing_perms)} 个):"
                )
            )
            for codename in missing_codenames:
                self.stdout.write(f"    - {codename}")

            if not dry_run:
                group.permissions.add(*missing_perms)
                self.stdout.write(
                    self.style.SUCCESS(f"  ✓ 已为 Group {group_name} 添加 {len(missing_perms)} 个权限")
                )
        else:
            self.stdout.write(f"  ✓ Group {group_name} 权限已完整")

        # 5) 输出摘要
        self.stdout.write("\n" + "=" * 60)
        if dry_run:
            self.stdout.write(self.style.WARNING("模拟运行摘要（未实际修改）"))
        else:
            self.stdout.write(self.style.SUCCESS("初始化完成！"))
        self.stdout.write("=" * 60)

        try:
            group = Group.objects.get(name=group_name)
            self.stdout.write(f"\nGroup: {group_name}")
            self.stdout.write(f"  权限数: {group.permissions.count()}")
            self.stdout.write(f"  用户数: {group.user_set.count()}")
            if group.permissions.exists():
                self.stdout.write("  权限列表:")
                for perm in group.permissions.all().order_by('content_type__app_label', 'codename'):
                    self.stdout.write(f"    - {perm.content_type.app_label}.{perm.codename}")
        except Group.DoesNotExist:
            pass

        self.stdout.write("=" * 60)

        self.stdout.write("\n提示：")
        self.stdout.write("  1. 此命令用于 D1 收口，固化权限职责边界")
        self.stdout.write("  2. 以后不再靠 __all__ 这种隐式逻辑救火")
        self.stdout.write("  3. 可以重复执行此命令（幂等操作）")
        self.stdout.write("  4. 将用户加入此 Group 后，用户将自动拥有 plan_management 相关权限")

