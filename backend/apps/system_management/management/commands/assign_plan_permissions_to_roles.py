"""
为所有角色分配计划管理权限

根据角色类型，为每个角色分配相应的计划管理权限：
- 计划管理权限：plan_management.view、plan_management.plan.create、plan_management.plan.manage
- 审批权限：plan_management.approve_plan
- 目标管理权限：plan_management.manage_goal、plan_management.goal.view

使用方法：
    python manage.py assign_plan_permissions_to_roles
    python manage.py assign_plan_permissions_to_roles --dry-run  # 预览模式
"""
from django.core.management.base import BaseCommand
from django.db import transaction

from backend.apps.system_management.models import Role
from backend.apps.permission_management.models import PermissionItem


# 权限映射：用户提到的权限 -> 系统中实际存在的权限
PERMISSION_MAPPING = {
    'plan_management.view': 'plan_management.view',
    'plan_management.create': 'plan_management.plan.create',  # 映射到 plan.create
    'plan_management.edit': 'plan_management.plan.manage',     # 映射到 plan.manage
    'plan_management.delete': 'plan_management.plan.manage', # 映射到 plan.manage
    'plan_management.approve_plan': 'plan_management.approve_plan',
    'plan_management.manage_goal': 'plan_management.manage_goal',
    'plan_management.view_goal': 'plan_management.goal.view',  # 映射到 goal.view
}

# 角色权限分配规则
ROLE_PERMISSION_RULES = {
    # 计划管理相关角色
    'plan_manager': {
        'name': '计划管理员',
        'permissions': [
            'plan_management.view',
            'plan_management.plan.create',
            'plan_management.plan.manage',
            'plan_management.approve_plan',
            'plan_management.manage_goal',
            'plan_management.goal.view',
        ]
    },
    'project_manager': {
        'name': '项目经理',
        'permissions': [
            'plan_management.view',
            'plan_management.plan.create',
            'plan_management.plan.manage',
            'plan_management.goal.view',
        ]
    },
    'plan_approver': {
        'name': '计划审批人',
        'permissions': [
            'plan_management.view',
            'plan_management.approve_plan',
            'plan_management.goal.view',
        ]
    },
    'plan_viewer': {
        'name': '计划查看者',
        'permissions': [
            'plan_management.view',
            'plan_management.goal.view',
        ]
    },
    # 其他角色：根据角色名称推断权限
    'general_manager': {
        'name': '总经理',
        'permissions': [
            'plan_management.view',
            'plan_management.plan.create',
            'plan_management.plan.manage',
            'plan_management.approve_plan',
            'plan_management.manage_goal',
            'plan_management.goal.view',
        ]
    },
    'system_admin': {
        'name': '系统管理员',
        'permissions': [
            'plan_management.view',
            'plan_management.plan.create',
            'plan_management.plan.manage',
            'plan_management.approve_plan',
            'plan_management.manage_goal',
            'plan_management.goal.view',
        ]
    },
}


class Command(BaseCommand):
    help = "为所有角色分配计划管理权限"

    def add_arguments(self, parser):
        parser.add_argument(
            '--dry-run',
            action='store_true',
            help='预览将要执行的操作，不实际修改数据库',
        )
        parser.add_argument(
            '--role-code',
            type=str,
            help='只处理指定角色代码（如：plan_manager）',
        )

    def handle(self, *args, **options):
        dry_run = options['dry_run']
        role_code_filter = options.get('role_code')

        if dry_run:
            self.stdout.write(self.style.WARNING('=== 预览模式（不会实际修改数据库）===\n'))

        # 获取所有权限
        all_permission_codes = set()
        for rule in ROLE_PERMISSION_RULES.values():
            all_permission_codes.update(rule['permissions'])
        
        permissions = PermissionItem.objects.filter(
            code__in=all_permission_codes,
            is_active=True
        )
        
        perm_dict = {p.code: p for p in permissions}
        
        # 检查缺失的权限
        missing_perms = all_permission_codes - set(perm_dict.keys())
        if missing_perms:
            self.stdout.write(
                self.style.ERROR(f'⚠ 警告：以下权限不存在：{", ".join(missing_perms)}')
            )
            self.stdout.write(
                self.style.WARNING('  请先运行: python manage.py seed_permissions')
            )

        # 获取所有角色（优先处理计划管理相关角色）
        if role_code_filter:
            roles = Role.objects.filter(code=role_code_filter, is_active=True)
        else:
            # 优先处理计划管理相关角色
            plan_role_codes = ['plan_manager', 'project_manager', 'plan_approver', 'plan_viewer', 'general_manager', 'system_admin']
            plan_roles = Role.objects.filter(code__in=plan_role_codes, is_active=True).order_by('code')
            other_roles = Role.objects.exclude(code__in=plan_role_codes).filter(is_active=True).order_by('code')
            roles = list(plan_roles) + list(other_roles)

        self.stdout.write(f'\n找到 {roles.count()} 个角色需要处理\n')

        updated_count = 0
        skipped_count = 0
        error_count = 0

        with transaction.atomic():
            for role in roles:
                try:
                    # 查找角色的权限规则
                    rule = ROLE_PERMISSION_RULES.get(role.code)
                    
                    if not rule:
                        # 如果没有特定规则，使用默认规则（只给查看权限）
                        rule = {
                            'name': role.name,
                            'permissions': [
                                'plan_management.view',
                                'plan_management.goal.view',
                            ]
                        }
                        self.stdout.write(
                            self.style.NOTICE(f'⊘ {role.name} ({role.code}) - 使用默认权限（仅查看）')
                        )
                    else:
                        self.stdout.write(
                            self.style.SUCCESS(f'✓ {role.name} ({role.code})')
                        )

                    # 获取要分配的权限
                    permission_codes = rule['permissions']
                    role_permissions = [perm_dict[code] for code in permission_codes if code in perm_dict]
                    
                    if not role_permissions:
                        self.stdout.write(
                            self.style.WARNING(f'  ⚠ 没有可分配的权限')
                        )
                        skipped_count += 1
                        continue

                    # 检查当前权限
                    current_perms = set(role.custom_permissions.filter(is_active=True).values_list('code', flat=True))
                    new_perms = {p.code for p in role_permissions}
                    
                    # 计算需要添加的权限
                    to_add = new_perms - current_perms
                    to_remove = current_perms - new_perms
                    
                    if not to_add and not to_remove:
                        self.stdout.write(
                            self.style.NOTICE(f'  ⊘ 权限已是最新，无需更新')
                        )
                        skipped_count += 1
                        continue

                    if not dry_run:
                        # 添加新权限
                        if to_add:
                            add_perms = [perm_dict[code] for code in to_add if code in perm_dict]
                            role.custom_permissions.add(*add_perms)
                        
                        # 移除不需要的权限（只移除计划管理相关权限）
                        if to_remove:
                            remove_perms = PermissionItem.objects.filter(
                                code__in=to_remove,
                                code__startswith='plan_management',
                                is_active=True
                            )
                            role.custom_permissions.remove(*remove_perms)

                    self.stdout.write(
                        f'  → 分配权限: {len(role_permissions)} 个'
                    )
                    if to_add:
                        self.stdout.write(
                            self.style.SUCCESS(f'    + 新增: {len(to_add)} 个')
                        )
                    if to_remove:
                        self.stdout.write(
                            self.style.WARNING(f'    - 移除: {len(to_remove)} 个')
                        )
                    
                    updated_count += 1

                except Exception as e:
                    error_count += 1
                    self.stdout.write(
                        self.style.ERROR(f'✗ 处理角色 {role.code} 时出错: {str(e)}')
                    )

            if dry_run:
                transaction.set_rollback(True)
                self.stdout.write(
                    self.style.WARNING('\n=== 预览模式：未实际修改数据库 ===')
                )

        # 输出总结
        self.stdout.write('\n' + '=' * 70)
        if dry_run:
            self.stdout.write(self.style.WARNING('预览结果：'))
        else:
            self.stdout.write(self.style.SUCCESS('执行结果：'))
        
        self.stdout.write(f'  处理角色: {roles.count()} 个')
        self.stdout.write(f'  更新角色: {updated_count} 个')
        self.stdout.write(f'  跳过角色: {skipped_count} 个')
        if error_count > 0:
            self.stdout.write(
                self.style.ERROR(f'  错误: {error_count} 个')
            )
        
        self.stdout.write('\n' + '=' * 70)
