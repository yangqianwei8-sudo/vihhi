"""
给总经理角色用户分配计划管理 Django 权限
创建或使用"总经理"组，分配 plan_management 相关权限，并将所有具有 general_manager 业务角色的用户加入该组
"""
from django.core.management.base import BaseCommand
from django.contrib.auth.models import Group, Permission
from django.contrib.contenttypes.models import ContentType
from django.contrib.auth import get_user_model
from django.db import transaction

from backend.apps.system_management.models import Role

User = get_user_model()


class Command(BaseCommand):
    help = '给总经理角色用户分配计划管理 Django 权限（通过组）'

    def add_arguments(self, parser):
        parser.add_argument(
            '--username',
            type=str,
            help='指定用户名，只给该用户分配权限（如果不指定，则给所有 general_manager 角色用户分配）'
        )
        parser.add_argument(
            '--dry-run',
            action='store_true',
            help='仅显示将要执行的操作，不实际执行'
        )

    @transaction.atomic
    def handle(self, *args, **options):
        dry_run = options.get('dry_run', False)
        username = options.get('username')

        if dry_run:
            self.stdout.write(self.style.WARNING('🔍 模拟运行模式，不会实际修改数据'))

        self.stdout.write('开始配置总经理计划管理权限...')
        self.stdout.write('')

        # 1. 获取或创建"总经理"组
        group_name = '总经理'
        group, group_created = Group.objects.get_or_create(name=group_name)
        if group_created:
            self.stdout.write(self.style.SUCCESS(f'✓ 创建组：{group_name}'))
        else:
            self.stdout.write(f'  组已存在：{group_name}')

        # 2. 获取 ContentType 和权限
        try:
            plan_ct = ContentType.objects.get(app_label='plan_management', model='plan')
            goal_ct = ContentType.objects.get(app_label='plan_management', model='strategicgoal')
        except ContentType.DoesNotExist as e:
            self.stdout.write(self.style.ERROR(f'错误：找不到 ContentType: {e}'))
            return

        # 需要分配的权限列表
        required_permissions = [
            ('view_plan', plan_ct, '查看计划'),
            ('view_strategicgoal', goal_ct, '查看目标'),
            ('add_plan', plan_ct, '创建计划'),
            ('change_plan', plan_ct, '修改计划'),
            ('delete_plan', plan_ct, '删除计划'),
            ('add_strategicgoal', goal_ct, '创建目标'),
            ('change_strategicgoal', goal_ct, '修改目标'),
            ('delete_strategicgoal', goal_ct, '删除目标'),
        ]

        # 尝试获取审批权限（如果存在）
        try:
            approve_plan_perm = Permission.objects.get(content_type=plan_ct, codename='approve_plan')
            required_permissions.append(('approve_plan', plan_ct, '审批计划'))
        except Permission.DoesNotExist:
            self.stdout.write(self.style.WARNING('  ⚠ 权限 plan_management.approve_plan 不存在，跳过'))

        try:
            approve_goal_perm = Permission.objects.get(content_type=goal_ct, codename='approve_strategicgoal')
            required_permissions.append(('approve_strategicgoal', goal_ct, '审批目标'))
        except Permission.DoesNotExist:
            self.stdout.write(self.style.WARNING('  ⚠ 权限 plan_management.approve_strategicgoal 不存在，跳过'))

        # 3. 为组分配权限
        added_perms = []
        for codename, content_type, desc in required_permissions:
            try:
                perm = Permission.objects.get(content_type=content_type, codename=codename)
                if perm not in group.permissions.all():
                    if not dry_run:
                        group.permissions.add(perm)
                    added_perms.append(perm)
                    self.stdout.write(f'  ✓ 添加权限：{content_type.app_label}.{codename} ({desc})')
                else:
                    self.stdout.write(f'  - 权限已存在：{content_type.app_label}.{codename} ({desc})')
            except Permission.DoesNotExist:
                self.stdout.write(self.style.WARNING(f'  ⚠ 权限不存在：{content_type.app_label}.{codename}，跳过'))

        if added_perms and not dry_run:
            self.stdout.write(self.style.SUCCESS(f'\n✓ 为组 {group_name} 添加了 {len(added_perms)} 个权限'))
        elif added_perms:
            self.stdout.write(self.style.SUCCESS(f'\n✓ 将为组 {group_name} 添加 {len(added_perms)} 个权限（模拟）'))

        # 4. 获取需要分配权限的用户
        if username:
            # 指定用户
            try:
                users = [User.objects.get(username=username)]
            except User.DoesNotExist:
                self.stdout.write(self.style.ERROR(f'错误：用户 {username} 不存在'))
                return
        else:
            # 所有具有 general_manager 或 internal_zjl 角色的用户
            gm_role = Role.objects.filter(code='general_manager', is_active=True).first()
            zjl_role = Role.objects.filter(code='internal_zjl', is_active=True).first()
            
            if not gm_role and not zjl_role:
                self.stdout.write(self.style.WARNING('⚠ 未找到 general_manager 或 internal_zjl 角色'))
                self.stdout.write('  提示：如果用户是通过其他方式标识为总经理的，请使用 --username 参数指定用户')
                return

            # 查找具有任一角色的用户
            from django.db.models import Q
            role_filter = Q()
            if gm_role:
                role_filter |= Q(roles=gm_role)
            if zjl_role:
                role_filter |= Q(roles=zjl_role)
            
            users = User.objects.filter(role_filter, is_active=True).distinct()
            if not users.exists():
                self.stdout.write(self.style.WARNING('⚠ 未找到具有总经理角色的用户'))
                self.stdout.write('  提示：请使用 --username 参数指定用户')
                return
            
            # 显示找到的角色
            if gm_role:
                self.stdout.write(f'  找到角色：{gm_role.name} (code: {gm_role.code})')
            if zjl_role:
                self.stdout.write(f'  找到角色：{zjl_role.name} (code: {zjl_role.code})')

        # 5. 将用户加入组
        self.stdout.write('')
        self.stdout.write(f'开始为用户分配组权限（共 {users.count()} 个用户）...')
        added_users = []
        for user in users:
            if group not in user.groups.all():
                if not dry_run:
                    user.groups.add(group)
                added_users.append(user)
                self.stdout.write(self.style.SUCCESS(f'  ✓ 将用户 {user.username} 加入组 {group_name}'))
            else:
                self.stdout.write(f'  - 用户 {user.username} 已在组 {group_name} 中')

        if added_users and not dry_run:
            self.stdout.write(self.style.SUCCESS(f'\n✓ 已将 {len(added_users)} 个用户加入组'))
        elif added_users:
            self.stdout.write(self.style.SUCCESS(f'\n✓ 将把 {len(added_users)} 个用户加入组（模拟）'))

        # 6. 输出摘要
        self.stdout.write('')
        self.stdout.write('=' * 60)
        if dry_run:
            self.stdout.write(self.style.WARNING('模拟运行摘要（未实际修改）'))
        else:
            self.stdout.write(self.style.SUCCESS('权限配置完成！'))
        self.stdout.write('=' * 60)
        self.stdout.write(f'\n组配置：{group_name}')
        self.stdout.write(f'  权限数：{group.permissions.count()}')
        for perm in group.permissions.all().order_by('content_type__app_label', 'codename'):
            self.stdout.write(f'    - {perm.content_type.app_label}.{perm.codename}')

        self.stdout.write(f'\n用户列表（共 {users.count()} 个）：')
        for user in users:
            user_groups = [g.name for g in user.groups.all()]
            has_perm = user.has_perm('plan_management.view_plan')
            status = '✓' if has_perm else '✗'
            self.stdout.write(f'  {status} {user.username}: 组={user_groups}, has_perm(view_plan)={has_perm}')

        self.stdout.write('=' * 60)

