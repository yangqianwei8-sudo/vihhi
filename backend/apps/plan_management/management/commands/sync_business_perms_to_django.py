"""
将业务权限同步到 Django 权限系统
目标：把"业务权限/角色"同步成 Django Group+Permission
先只覆盖 plan_management 模块（避免发散）
"""
from django.core.management.base import BaseCommand
from django.contrib.auth.models import Group, Permission
from django.contrib.contenttypes.models import ContentType
from django.contrib.auth import get_user_model
from django.db import transaction

from backend.apps.system_management.models import Role
from backend.core.permission_mapping import get_all_django_perms_for_module

User = get_user_model()


class Command(BaseCommand):
    help = '将业务权限同步到 Django 权限系统（plan_management 模块）'

    def add_arguments(self, parser):
        parser.add_argument(
            '--dry-run',
            action='store_true',
            help='仅显示将要执行的操作，不实际执行'
        )
        parser.add_argument(
            '--role-code',
            type=str,
            help='只同步指定角色代码（如 internal_zjl），不指定则同步所有角色'
        )

    @transaction.atomic
    def handle(self, *args, **options):
        dry_run = options.get('dry_run', False)
        role_code = options.get('role_code')

        if dry_run:
            self.stdout.write(self.style.WARNING('🔍 模拟运行模式，不会实际修改数据'))

        self.stdout.write('开始同步业务权限到 Django 权限系统...\n')

        # 1. 获取所有 Django 权限
        django_perms = get_all_django_perms_for_module('plan_management')
        self.stdout.write(f'需要同步的 Django 权限（共 {len(django_perms)} 个）：')
        for perm in django_perms:
            self.stdout.write(f'  - {perm}')

        # 2. 获取 ContentType
        try:
            plan_ct = ContentType.objects.get(app_label='plan_management', model='plan')
            goal_ct = ContentType.objects.get(app_label='plan_management', model='strategicgoal')
        except ContentType.DoesNotExist as e:
            self.stdout.write(self.style.ERROR(f'错误：找不到 ContentType: {e}'))
            return

        # 3. 获取或创建 Django Permission 对象
        django_permission_objects = {}
        for perm_codename in django_perms:
            # 解析权限名称
            if 'plan' in perm_codename and 'strategicgoal' not in perm_codename:
                ct = plan_ct
                model_name = 'plan'
            elif 'strategicgoal' in perm_codename:
                ct = goal_ct
                model_name = 'strategicgoal'
            else:
                continue

            # 提取操作类型
            action = perm_codename.split('.')[-1].replace('_', ' ')
            
            try:
                perm = Permission.objects.get(content_type=ct, codename=perm_codename.split('.')[-1])
                django_permission_objects[perm_codename] = perm
                self.stdout.write(f'  ✓ 找到 Django 权限：{perm_codename}')
            except Permission.DoesNotExist:
                self.stdout.write(self.style.WARNING(f'  ⚠ Django 权限不存在：{perm_codename}'))

        if not django_permission_objects:
            self.stdout.write(self.style.ERROR('错误：没有找到任何 Django 权限'))
            return

        # 4. 获取需要同步的角色
        if role_code:
            roles = Role.objects.filter(code=role_code, is_active=True)
        else:
            # 获取所有有业务权限的角色
            from django.db.models import Q
            roles = Role.objects.filter(
                Q(custom_permissions__code__startswith='plan_management') |
                Q(code__in=['system_admin', 'general_manager', 'internal_zjl']),
                is_active=True
            ).distinct()

        if not roles.exists():
            self.stdout.write(self.style.WARNING('⚠ 未找到需要同步的角色'))
            return

        self.stdout.write(f'\n找到 {roles.count()} 个需要同步的角色：')
        for role in roles:
            self.stdout.write(f'  - {role.name} (code: {role.code})')

        # 5. 为每个角色创建或获取 Django Group，并分配权限
        self.stdout.write('\n开始同步角色权限...')
        synced_groups = []
        
        for role in roles:
            # 创建或获取对应的 Django Group
            group_name = f'{role.name} (Django)'
            group, created = Group.objects.get_or_create(name=group_name)
            
            if created:
                self.stdout.write(f'  ✓ 创建 Django Group：{group_name}')
            else:
                self.stdout.write(f'  - Django Group 已存在：{group_name}')

            # 判断是否需要分配所有权限（特殊角色）
            if role.code in ['system_admin', 'general_manager', 'internal_zjl']:
                # 这些角色拥有所有权限
                perms_to_add = list(django_permission_objects.values())
                self.stdout.write(f'    角色 {role.name} 拥有所有权限（特殊角色）')
            else:
                # 根据业务权限映射到 Django 权限
                from backend.apps.permission_management.models import PermissionItem
                from backend.core.permission_mapping import map_business_to_django
                
                business_perms = role.custom_permissions.filter(
                    code__startswith='plan_management',
                    is_active=True
                )
                
                perms_to_add = []
                for business_perm in business_perms:
                    django_perm_codes = map_business_to_django(business_perm.code)
                    for code in django_perm_codes:
                        if code in django_permission_objects:
                            perms_to_add.append(django_permission_objects[code])

            # 去重
            perms_to_add = list(set(perms_to_add))
            
            # 添加权限到 Group
            existing_perms = set(group.permissions.all())
            new_perms = [p for p in perms_to_add if p not in existing_perms]
            
            if new_perms:
                if not dry_run:
                    group.permissions.add(*new_perms)
                self.stdout.write(self.style.SUCCESS(
                    f'    ✓ 为 Group {group_name} 添加 {len(new_perms)} 个权限'
                ))
            else:
                self.stdout.write(f'    - Group {group_name} 权限已完整')

            # 将角色的所有用户加入该 Group
            role_users = User.objects.filter(roles=role, is_active=True).distinct()
            added_users = []
            for user in role_users:
                if group not in user.groups.all():
                    if not dry_run:
                        user.groups.add(group)
                    added_users.append(user.username)

            if added_users:
                if not dry_run:
                    self.stdout.write(self.style.SUCCESS(
                        f'    ✓ 将 {len(added_users)} 个用户加入 Group {group_name}'
                    ))
                else:
                    self.stdout.write(f'    将把 {len(added_users)} 个用户加入 Group {group_name}（模拟）')

            synced_groups.append((group, role))

        # 6. 输出摘要
        self.stdout.write('\n' + '=' * 60)
        if dry_run:
            self.stdout.write(self.style.WARNING('模拟运行摘要（未实际修改）'))
        else:
            self.stdout.write(self.style.SUCCESS('同步完成！'))
        self.stdout.write('=' * 60)
        
        for group, role in synced_groups:
            self.stdout.write(f'\n角色：{role.name} (code: {role.code})')
            self.stdout.write(f'  Django Group: {group.name}')
            self.stdout.write(f'  权限数：{group.permissions.count()}')
            self.stdout.write(f'  用户数：{group.user_set.count()}')

        self.stdout.write('\n' + '=' * 60)
        self.stdout.write('\n提示：')
        self.stdout.write('  1. 同步后，用户可以通过 Django Group 获得权限')
        self.stdout.write('  2. 业务权限系统仍保留，用于菜单显示等')
        self.stdout.write('  3. 页面访问权限现在由 Django 权限控制（优先）+ 业务权限兜底')

