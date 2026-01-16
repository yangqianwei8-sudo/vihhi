"""
为用户分配计划管理角色

使用方法：
    python manage.py assign_user_plan_roles
    python manage.py assign_user_plan_roles --username tester1 --role plan_viewer
    python manage.py assign_user_plan_roles --dry-run  # 预览模式
"""
from django.core.management.base import BaseCommand, CommandError
from django.db import transaction

from backend.apps.system_management.models import User, Role


# 用户角色映射配置
USER_ROLE_MAPPING = {
    'tester1': 'plan_viewer',           # 普通用户 -> 计划查看者
    '13880399996': 'plan_approver',     # 审批人 -> 计划审批人
    '13666287899': 'project_manager',   # 项目经理 -> 项目经理
    '13281895910': 'plan_manager',      # 陈洁滢（计划管理员） -> 计划管理员
}


class Command(BaseCommand):
    help = "为用户分配计划管理角色"

    def add_arguments(self, parser):
        parser.add_argument(
            '--username',
            type=str,
            help='指定用户名（如果提供，只处理该用户）',
        )
        parser.add_argument(
            '--role',
            type=str,
            choices=['plan_viewer', 'plan_approver', 'project_manager', 'plan_manager'],
            help='指定角色代码（需要与--username一起使用）',
        )
        parser.add_argument(
            '--dry-run',
            action='store_true',
            help='预览将要执行的操作，不实际修改数据库',
        )
        parser.add_argument(
            '--clear-existing',
            action='store_true',
            help='清除用户现有的计划管理相关角色后再分配新角色',
        )

    def handle(self, *args, **options):
        dry_run = options['dry_run']
        username_filter = options.get('username')
        role_filter = options.get('role')
        clear_existing = options['clear_existing']

        if dry_run:
            self.stdout.write(self.style.WARNING('=== 预览模式（不会实际修改数据库）===\n'))

        # 获取所有角色
        role_codes = ['plan_viewer', 'plan_approver', 'project_manager', 'plan_manager']
        roles = {role.code: role for role in Role.objects.filter(code__in=role_codes, is_active=True)}
        
        missing_roles = set(role_codes) - set(roles.keys())
        if missing_roles:
            raise CommandError(f'以下角色不存在：{", ".join(missing_roles)}')

        # 确定要处理的用户
        if username_filter:
            if not role_filter:
                raise CommandError('使用--username时必须同时指定--role')
            users_to_process = [(username_filter, role_filter)]
        else:
            # 使用配置的映射
            users_to_process = list(USER_ROLE_MAPPING.items())

        self.stdout.write(f'\n准备处理 {len(users_to_process)} 个用户\n')

        updated_count = 0
        skipped_count = 0
        error_count = 0

        with transaction.atomic():
            for username, target_role_code in users_to_process:
                try:
                    user = User.objects.filter(username=username).first()
                    if not user:
                        self.stdout.write(
                            self.style.ERROR(f'✗ 用户不存在: {username}')
                        )
                        error_count += 1
                        continue

                    target_role = roles.get(target_role_code)
                    if not target_role:
                        self.stdout.write(
                            self.style.ERROR(f'✗ 角色不存在: {target_role_code}')
                        )
                        error_count += 1
                        continue

                    # 获取用户当前的计划管理相关角色
                    current_plan_roles = user.roles.filter(
                        code__in=role_codes,
                        is_active=True
                    )

                    # 检查是否需要更新
                    if current_plan_roles.filter(code=target_role_code).exists():
                        if len(current_plan_roles) == 1:
                            self.stdout.write(
                                self.style.NOTICE(f'⊘ {user.username} ({user.get_full_name() or "未设置姓名"}) - 已拥有角色: {target_role.name}')
                            )
                            skipped_count += 1
                            continue

                    # 显示当前状态
                    current_role_names = [r.name for r in current_plan_roles]
                    self.stdout.write(
                        self.style.SUCCESS(f'✓ {user.username} ({user.get_full_name() or "未设置姓名"})')
                    )
                    if current_role_names:
                        self.stdout.write(f'  当前计划管理角色: {", ".join(current_role_names)}')
                    else:
                        self.stdout.write(f'  当前计划管理角色: 无')

                    # 准备新的角色列表
                    if clear_existing:
                        # 清除所有计划管理角色，只保留新角色
                        new_roles = [target_role]
                        removed_roles = list(current_plan_roles)
                    else:
                        # 保留其他角色，只更新计划管理角色
                        other_roles = user.roles.exclude(code__in=role_codes).filter(is_active=True)
                        new_roles = list(other_roles) + [target_role]
                        removed_roles = [r for r in current_plan_roles if r.code != target_role_code]

                    if not dry_run:
                        # 移除旧角色
                        if removed_roles:
                            user.roles.remove(*removed_roles)
                        
                        # 添加新角色
                        if target_role not in user.roles.all():
                            user.roles.add(target_role)

                    self.stdout.write(f'  → 分配角色: {target_role.name} ({target_role_code})')
                    if removed_roles:
                        self.stdout.write(
                            self.style.WARNING(f'    - 移除: {", ".join([r.name for r in removed_roles])}')
                        )

                    updated_count += 1

                except Exception as e:
                    error_count += 1
                    self.stdout.write(
                        self.style.ERROR(f'✗ 处理用户 {username} 时出错: {str(e)}')
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
        
        self.stdout.write(f'  处理用户: {len(users_to_process)} 个')
        self.stdout.write(f'  更新用户: {updated_count} 个')
        self.stdout.write(f'  跳过用户: {skipped_count} 个')
        if error_count > 0:
            self.stdout.write(
                self.style.ERROR(f'  错误: {error_count} 个')
            )
        
        self.stdout.write('\n' + '=' * 70)
