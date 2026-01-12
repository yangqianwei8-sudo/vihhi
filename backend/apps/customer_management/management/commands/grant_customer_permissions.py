"""
为客户管理角色分配 Django 权限
复用 INTERNAL_ZJL 组，绑定 customer_management.view_client 权限
将拥有 internal_zjl/general_manager/system_admin 业务角色的用户加入该组
"""
from django.core.management.base import BaseCommand
from django.contrib.auth.models import Group, Permission
from django.contrib.contenttypes.models import ContentType
from django.contrib.auth import get_user_model
from django.db import transaction

from backend.apps.system_management.models import Role
from backend.apps.customer_management.models import Client

User = get_user_model()

# 复用 INTERNAL_ZJL 组（与 plan_management 保持一致）
GROUP_NAME = "INTERNAL_ZJL"

# 需要分配的角色代码
TARGET_ROLE_CODES = ["internal_zjl", "general_manager", "system_admin"]

# 客户管理权限列表
CUSTOMER_PERMS = [
    "view_client",  # 必要：查看客户
    "change_client",  # 可选：编辑客户
]

# 总工作台权限（添加到 INTERNAL_ZJL 组）
DASHBOARD_PERM = "core.view_dashboard"


class Command(BaseCommand):
    help = "为客户管理角色分配 Django 权限（复用 INTERNAL_ZJL 组）"

    def add_arguments(self, parser):
        parser.add_argument(
            "--dry-run",
            action="store_true",
            help="仅显示将要执行的操作，不实际修改数据库"
        )
        parser.add_argument(
            "--username",
            type=str,
            help="指定用户名，只给该用户分配权限（如果不指定，则给所有目标角色用户分配）"
        )

    @transaction.atomic
    def handle(self, *args, **options):
        dry_run = options["dry_run"]
        username = options.get("username")

        if dry_run:
            self.stdout.write(self.style.WARNING("🔍 模拟运行模式，不会实际修改数据"))

        self.stdout.write("开始为客户管理角色分配 Django 权限...\n")

        # 1) 创建或获取 INTERNAL_ZJL 组（复用，如果已存在）
        group, group_created = Group.objects.get_or_create(name=GROUP_NAME)
        if group_created:
            self.stdout.write(self.style.SUCCESS(f"  ✓ 创建 Group: {GROUP_NAME}"))
        else:
            self.stdout.write(f"  - Group 已存在: {GROUP_NAME}（复用）")

        # 2) 获取 ContentType
        try:
            client_ct = ContentType.objects.get_for_model(Client)
        except Exception as e:
            self.stdout.write(self.style.ERROR(f"  错误：无法获取 ContentType: {e}"))
            return

        # 3) 获取权限对象
        wanted_perms = []
        for codename in CUSTOMER_PERMS:
            try:
                perm = Permission.objects.get(content_type=client_ct, codename=codename)
                wanted_perms.append(perm)
                self.stdout.write(f"  ✓ 找到权限: customer_management.{codename}")
            except Permission.DoesNotExist:
                self.stdout.write(self.style.WARNING(f"  ⚠ 权限不存在: customer_management.{codename}，跳过"))

        # 3.1) 添加总工作台权限
        try:
            dashboard_ct = ContentType.objects.get(app_label='core', model='dashboard')
            dashboard_perm = Permission.objects.get(content_type=dashboard_ct, codename='view_dashboard')
            wanted_perms.append(dashboard_perm)
            self.stdout.write(f"  ✓ 找到权限: {DASHBOARD_PERM}")
        except (ContentType.DoesNotExist, Permission.DoesNotExist):
            self.stdout.write(self.style.WARNING(f"  ⚠ 权限不存在: {DASHBOARD_PERM}，跳过"))

        if not wanted_perms:
            self.stdout.write(self.style.ERROR("  错误：没有找到任何权限"))
            return

        # 4) 为组分配权限
        existing_perm_ids = set(group.permissions.values_list('id', flat=True))
        missing_perms = [p for p in wanted_perms if p.id not in existing_perm_ids]

        if missing_perms:
            missing_codenames = [p.codename for p in missing_perms]
            self.stdout.write(
                self.style.WARNING(
                    f"  ⚠ [{GROUP_NAME}] 需要添加的权限: {', '.join(missing_codenames)}"
                )
            )
            if not dry_run:
                group.permissions.add(*missing_perms)
                self.stdout.write(
                    self.style.SUCCESS(f"  ✓ 已为 Group {GROUP_NAME} 添加 {len(missing_perms)} 个权限")
                )
        else:
            self.stdout.write(f"  ✓ Group {GROUP_NAME} 客户管理权限已完整")

        # 5) 获取需要分配权限的用户
        if username:
            # 指定用户
            try:
                users = [User.objects.get(username=username)]
                self.stdout.write(f"  指定用户: {username}")
            except User.DoesNotExist:
                self.stdout.write(self.style.ERROR(f"  错误：用户 {username} 不存在"))
                return
        else:
            # 所有具有目标角色的用户
            roles = Role.objects.filter(code__in=TARGET_ROLE_CODES, is_active=True)
            if not roles.exists():
                self.stdout.write(self.style.WARNING(f"  ⚠ 未找到目标角色: {', '.join(TARGET_ROLE_CODES)}"))
                return

            # 显示找到的角色
            found_role_codes = []
            for role in roles:
                found_role_codes.append(role.code)
                self.stdout.write(f"  找到角色: {role.name} (code: {role.code})")

            # 查找具有任一角色的用户
            from django.db.models import Q
            role_filter = Q()
            for role in roles:
                role_filter |= Q(roles=role)

            users = User.objects.filter(role_filter, is_active=True).distinct()
            self.stdout.write(f"  找到 {users.count()} 个具有目标角色的用户")

        # 6) 将用户加入组
        self.stdout.write("")
        self.stdout.write(f"开始为用户分配组权限（共 {users.count()} 个用户）...")
        changed_count = 0
        for user in users:
            if group not in user.groups.all():
                changed_count += 1
                self.stdout.write(f"    - 将用户 {user.username} 加入 Group {GROUP_NAME}")
                if not dry_run:
                    user.groups.add(group)
            else:
                self.stdout.write(f"    - 用户 {user.username} 已在 Group {GROUP_NAME} 中")

        if changed_count > 0:
            if not dry_run:
                self.stdout.write(
                    self.style.SUCCESS(f"  ✓ 已将 {changed_count} 个用户加入 Group {GROUP_NAME}")
                )
            else:
                self.stdout.write(f"  将把 {changed_count} 个用户加入 Group {GROUP_NAME}（模拟）")

        # 7) 输出摘要
        self.stdout.write("\n" + "=" * 60)
        if dry_run:
            self.stdout.write(self.style.WARNING("模拟运行摘要（未实际修改）"))
        else:
            self.stdout.write(self.style.SUCCESS("权限配置完成！"))
        self.stdout.write("=" * 60)

        self.stdout.write(f"\nGroup: {GROUP_NAME}")
        self.stdout.write(f"  权限数: {group.permissions.count()}")
        self.stdout.write(f"  用户数: {group.user_set.count()}")

        # 显示客户管理相关权限
        customer_perms = group.permissions.filter(content_type__app_label='customer_management')
        if customer_perms.exists():
            self.stdout.write("  客户管理权限:")
            for perm in customer_perms.order_by('codename'):
                self.stdout.write(f"    - {perm.content_type.app_label}.{perm.codename}")

        self.stdout.write(f"\n用户列表（共 {users.count()} 个）：")
        for user in users:
            user_groups = [g.name for g in user.groups.all()]
            has_perm = user.has_perm('customer_management.view_client')
            status = '✓' if has_perm else '✗'
            self.stdout.write(f"  {status} {user.username}: 组={user_groups}, has_perm(view_client)={has_perm}")

        self.stdout.write("=" * 60)

        self.stdout.write("\n提示：")
        self.stdout.write("  1. 此命令复用 INTERNAL_ZJL 组（与 plan_management 保持一致）")
        self.stdout.write("  2. 客户管理页面访问权限现在由 Django 权限控制（优先）+ 业务权限兜底")
        self.stdout.write("  3. 可以重复执行此命令（幂等操作）")
        self.stdout.write("  4. 如需为其他用户分配权限，请使用 --username 参数")

