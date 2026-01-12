"""
将业务角色（如 internal_zjl）同步到 Django Group 和权限
目标：让业务角色用户在 Django 权限体系里自动拥有对应权限
"""
from django.core.management.base import BaseCommand
from django.contrib.auth.models import Group, Permission
from django.contrib.contenttypes.models import ContentType
from django.contrib.auth import get_user_model
from django.db import transaction

from backend.apps.system_management.models import Role
from backend.apps.plan_management.models import Plan, StrategicGoal

User = get_user_model()

# 角色代码到 Group 名称的映射
ROLE_CODE_TO_GROUP = {
    "internal_zjl": "INTERNAL_ZJL",
}

# 最小权限集（先让系统能跑起来）
PLAN_PERMS = [
    "view_plan",
    "change_plan",
    "approve_plan",
]

GOAL_PERMS = [
    "view_strategicgoal",
    "change_strategicgoal",
    "approve_strategicgoal",
]


class Command(BaseCommand):
    help = "将业务角色（如 internal_zjl）同步到 Django Group 和权限"

    def add_arguments(self, parser):
        parser.add_argument(
            "--dry-run",
            action="store_true",
            help="仅显示将要执行的操作，不实际修改数据库"
        )
        parser.add_argument(
            "--role",
            type=str,
            default="",
            help="只同步指定角色代码（如 internal_zjl），不指定则同步所有配置的角色"
        )

    @transaction.atomic
    def handle(self, *args, **options):
        dry_run = options["dry_run"]
        role_filter = (options["role"] or "").strip()

        if dry_run:
            self.stdout.write(self.style.WARNING("🔍 模拟运行模式，不会实际修改数据"))

        self.stdout.write("开始同步业务角色到 Django Group...\n")

        total_changed_users = 0

        # 遍历配置的角色映射
        for role_code, group_name in ROLE_CODE_TO_GROUP.items():
            if role_filter and role_filter != role_code:
                continue

            self.stdout.write(f"处理角色: {role_code} -> Group: {group_name}")

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
                continue

            # 3) 获取权限对象
            plan_perms = Permission.objects.filter(
                content_type=plan_ct,
                codename__in=PLAN_PERMS
            )
            goal_perms = Permission.objects.filter(
                content_type=goal_ct,
                codename__in=GOAL_PERMS
            )

            wanted_perms = list(plan_perms) + list(goal_perms)

            # 检查缺失的权限
            existing_perm_ids = set(group.permissions.values_list('id', flat=True))
            missing_perms = [p for p in wanted_perms if p.id not in existing_perm_ids]

            if missing_perms:
                missing_codenames = [p.codename for p in missing_perms]
                self.stdout.write(
                    self.style.WARNING(
                        f"  ⚠ [{group_name}] 需要添加的权限: {', '.join(missing_codenames)}"
                    )
                )
                if not dry_run:
                    group.permissions.add(*missing_perms)
                    self.stdout.write(
                        self.style.SUCCESS(f"  ✓ 已为 Group {group_name} 添加 {len(missing_perms)} 个权限")
                    )
            else:
                self.stdout.write(f"  ✓ Group {group_name} 权限已完整")

            # 4) 找到该角色的用户并加入组
            # 注意：User.roles 是 ManyToManyField，不是 user.profile.role
            role = Role.objects.filter(code=role_code, is_active=True).first()
            if not role:
                self.stdout.write(self.style.WARNING(f"  ⚠ 未找到角色: {role_code}"))
                continue

            users = User.objects.filter(roles=role, is_active=True).distinct()
            self.stdout.write(f"  找到 {users.count()} 个具有 {role_code} 角色的用户")

            changed_count = 0
            for user in users:
                if group not in user.groups.all():
                    changed_count += 1
                    total_changed_users += 1
                    self.stdout.write(f"    - 将用户 {user.username} 加入 Group {group_name}")
                    if not dry_run:
                        user.groups.add(group)
                else:
                    self.stdout.write(f"    - 用户 {user.username} 已在 Group {group_name} 中")

            if changed_count > 0:
                if not dry_run:
                    self.stdout.write(
                        self.style.SUCCESS(f"  ✓ 已将 {changed_count} 个用户加入 Group {group_name}")
                    )
                else:
                    self.stdout.write(f"  将把 {changed_count} 个用户加入 Group {group_name}（模拟）")

        # 5) 输出摘要
        self.stdout.write("\n" + "=" * 60)
        if dry_run:
            self.stdout.write(self.style.WARNING("模拟运行摘要（未实际修改）"))
        else:
            self.stdout.write(self.style.SUCCESS("同步完成！"))
        self.stdout.write("=" * 60)

        for role_code, group_name in ROLE_CODE_TO_GROUP.items():
            if role_filter and role_filter != role_code:
                continue

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

        self.stdout.write(f"\n总计变更用户数: {total_changed_users}")
        self.stdout.write("=" * 60)

        self.stdout.write("\n提示：")
        self.stdout.write("  1. 同步后，用户可以通过 Django Group 获得权限")
        self.stdout.write("  2. 页面访问权限现在由 Django 权限控制（优先）+ 业务权限兜底")
        self.stdout.write("  3. 可以重复执行此命令（幂等操作）")

