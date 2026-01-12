"""
授予计划管理页面权限给用户（通过组）
"""
from django.core.management.base import BaseCommand
from django.contrib.auth.models import Group, Permission
from django.contrib.contenttypes.models import ContentType
from django.contrib.auth import get_user_model

from backend.apps.plan_management.models import Plan, StrategicGoal

User = get_user_model()


class Command(BaseCommand):
    help = "Grant plan_management page permissions to a user via group"

    def add_arguments(self, parser):
        parser.add_argument("--username", default="tester1")
        parser.add_argument("--group", default="Plan Viewer")
        parser.add_argument("--with-change", action="store_true", help="Also grant change permissions")

    def handle(self, *args, **options):
        username = options["username"]
        group_name = options["group"]
        with_change = options["with_change"]

        try:
            user = User.objects.get(username=username)
        except User.DoesNotExist:
            self.stdout.write(self.style.ERROR(f"用户 {username} 不存在"))
            return

        group, created = Group.objects.get_or_create(name=group_name)
        if created:
            self.stdout.write(self.style.SUCCESS(f"✓ 创建组：{group_name}"))
        else:
            self.stdout.write(f"  组已存在：{group_name}")

        # 获取 ContentType
        plan_ct = ContentType.objects.get_for_model(Plan)
        goal_ct = ContentType.objects.get_for_model(StrategicGoal)

        # 基础权限（view）
        perms = []
        perms.append(Permission.objects.get(content_type=plan_ct, codename="view_plan"))
        perms.append(Permission.objects.get(content_type=goal_ct, codename="view_strategicgoal"))

        if with_change:
            perms.append(Permission.objects.get(content_type=plan_ct, codename="change_plan"))
            perms.append(Permission.objects.get(content_type=goal_ct, codename="change_strategicgoal"))

        # 添加权限到组
        added_count = 0
        for p in perms:
            if p not in group.permissions.all():
                group.permissions.add(p)
                added_count += 1

        if added_count > 0:
            self.stdout.write(self.style.SUCCESS(f"✓ 为组添加 {added_count} 个权限"))
        else:
            self.stdout.write("  组权限已完整")

        # 将用户添加到组
        if group not in user.groups.all():
            user.groups.add(group)
            self.stdout.write(self.style.SUCCESS(f"✓ 将用户 {username} 加入组 {group_name}"))
        else:
            self.stdout.write(f"  用户 {username} 已在组 {group_name} 中")

        self.stdout.write(self.style.SUCCESS(
            f"\n✅ 完成！用户={username} 组={group_name} 权限={[p.codename for p in perms]}"
        ))

