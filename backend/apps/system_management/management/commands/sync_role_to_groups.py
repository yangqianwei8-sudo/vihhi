"""
D1-2: 将业务角色同步到 Django Group 和权限
目标：Role.code / Role.custom_permissions 作为"给用户分配 Django Group/Permission"的来源
"""
from django.core.management.base import BaseCommand
from django.contrib.auth.models import Group, Permission
from django.contrib.contenttypes.models import ContentType
from django.contrib.auth import get_user_model
from django.db import transaction

from backend.apps.system_management.models import Role
from backend.apps.permission_management.models import PermissionItem
from backend.core.permission_mapping import PLAN_MANAGEMENT_PERMISSION_MAPPING, map_business_to_django

User = get_user_model()

# 特殊角色（拥有 __all__ 权限的角色）
SPECIAL_ROLES_WITH_ALL = ['system_admin', 'general_manager', 'internal_zjl']

# 特殊角色的 Django 权限（如果角色拥有 __all__，则分配这些权限）
SPECIAL_ROLE_DJANGO_PERMS = {
    'system_admin': [],  # 超级管理员通常不需要额外权限
    'general_manager': [],  # 待定义
    'internal_zjl': [
        'plan_management.view_plan',
        'plan_management.change_plan',
        'plan_management.approve_plan',
        'plan_management.view_strategicgoal',
        'plan_management.change_strategicgoal',
        'plan_management.approve_strategicgoal',
    ],
}


class Command(BaseCommand):
    help = "将业务角色（Role）同步到 Django Group 和权限"

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
            help="只同步指定角色代码（如 internal_zjl），不指定则同步所有角色"
        )

    @transaction.atomic
    def handle(self, *args, **options):
        dry_run = options["dry_run"]
        role_filter = (options["role"] or "").strip()

        if dry_run:
            self.stdout.write(self.style.WARNING("🔍 模拟运行模式，不会实际修改数据"))

        self.stdout.write("开始同步业务角色到 Django Group...\n")

        # 获取所有需要同步的角色
        roles_to_sync = Role.objects.filter(is_active=True)
        if role_filter:
            roles_to_sync = roles_to_sync.filter(code=role_filter)

        total_changed_users = 0

        for role in roles_to_sync:
            self.stdout.write(f"\n处理角色: {role.code} ({role.name})")

            # 1) 创建或获取 Group（使用角色名称）
            group_name = f"{role.name} (Django)"
            group, group_created = Group.objects.get_or_create(name=group_name)
            if group_created:
                self.stdout.write(self.style.SUCCESS(f"  ✓ 创建 Group: {group_name}"))
            else:
                self.stdout.write(f"  - Group 已存在: {group_name}")

            # 2) 确定该角色应该拥有的 Django 权限
            django_perm_codenames = set()

            # 2.1) 如果是特殊角色（拥有 __all__），使用预定义的权限
            if role.code in SPECIAL_ROLES_WITH_ALL:
                if role.code in SPECIAL_ROLE_DJANGO_PERMS:
                    django_perm_codenames.update(SPECIAL_ROLE_DJANGO_PERMS[role.code])
                    self.stdout.write(f"  - 特殊角色 {role.code}，使用预定义权限")

            # 2.2) 从角色的业务权限（PermissionItem）映射到 Django 权限
            business_perms = role.custom_permissions.filter(is_active=True)
            for business_perm in business_perms:
                mapped_perms = map_business_to_django(business_perm.code)
                if mapped_perms:
                    django_perm_codenames.update(mapped_perms)
                    self.stdout.write(f"    - 业务权限 {business_perm.code} -> {', '.join(mapped_perms)}")
                else:
                    # 如果映射表中没有，尝试直接使用业务权限代码作为 Django codename
                    # 这适用于已经统一为 Django codename 的业务权限
                    django_perm_codenames.add(business_perm.code)
                    self.stdout.write(f"    - 业务权限 {business_perm.code}（直接使用）")

            if not django_perm_codenames:
                self.stdout.write(self.style.WARNING(f"  ⚠ 角色 {role.code} 没有映射到任何 Django 权限"))
                continue

            # 3) 获取 Django Permission 对象
            django_perms = []
            for perm_codename in django_perm_codenames:
                try:
                    # 解析 app_label 和 codename
                    if '.' in perm_codename:
                        app_label, codename = perm_codename.split('.', 1)
                    else:
                        self.stdout.write(self.style.WARNING(f"    ⚠ 权限格式错误: {perm_codename}"))
                        continue

                    # 查找 ContentType（需要知道是哪个模型）
                    # 这里简化处理：先尝试通过 codename 查找
                    perm = Permission.objects.filter(
                        content_type__app_label=app_label,
                        codename=codename
                    ).first()

                    if perm:
                        django_perms.append(perm)
                    else:
                        self.stdout.write(self.style.WARNING(f"    ⚠ 未找到 Django 权限: {perm_codename}"))
                except Exception as e:
                    self.stdout.write(self.style.ERROR(f"    ✗ 处理权限 {perm_codename} 时出错: {e}"))

            # 4) 将权限添加到 Group
            existing_perm_ids = set(group.permissions.values_list('id', flat=True))
            missing_perms = [p for p in django_perms if p.id not in existing_perm_ids]

            if missing_perms:
                missing_codenames = [f"{p.content_type.app_label}.{p.codename}" for p in missing_perms]
                self.stdout.write(
                    self.style.WARNING(f"  ⚠ [{group_name}] 需要添加的权限: {', '.join(missing_codenames)}")
                )
                if not dry_run:
                    group.permissions.add(*missing_perms)
                    self.stdout.write(
                        self.style.SUCCESS(f"  ✓ 已为 Group {group_name} 添加 {len(missing_perms)} 个权限")
                    )
            else:
                self.stdout.write(f"  ✓ Group {group_name} 权限已完整")

            # 5) 找到该角色的用户并加入组
            users = User.objects.filter(roles=role, is_active=True).distinct()
            self.stdout.write(f"  找到 {users.count()} 个具有 {role.code} 角色的用户")

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

        # 6) 输出摘要
        self.stdout.write("\n" + "=" * 60)
        if dry_run:
            self.stdout.write(self.style.WARNING("模拟运行摘要（未实际修改）"))
        else:
            self.stdout.write(self.style.SUCCESS("同步完成！"))
        self.stdout.write("=" * 60)

        for role in roles_to_sync:
            group_name = f"{role.name} (Django)"
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

