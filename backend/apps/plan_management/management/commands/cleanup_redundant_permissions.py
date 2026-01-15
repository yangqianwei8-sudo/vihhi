"""
管理命令：彻底清理冗余的 Django 自动生成权限

删除 Django 为 Plan 和 StrategicGoal 模型自动生成的所有默认权限：
- plan_management.view_plan
- plan_management.add_plan
- plan_management.change_plan
- plan_management.delete_plan
- plan_management.view_strategicgoal
- plan_management.add_strategicgoal
- plan_management.change_strategicgoal
- plan_management.delete_strategicgoal

这些权限与自定义业务权限重复，统一使用业务权限系统。
注意：模型 Meta 类已设置 default_permissions = ()，新创建的模型不会再生成默认权限。
"""
from django.core.management.base import BaseCommand
from django.contrib.auth.models import Permission
from django.contrib.contenttypes.models import ContentType
from django.db import transaction
from django.contrib.auth import get_user_model
from backend.apps.plan_management.models import Plan, StrategicGoal

User = get_user_model()


class Command(BaseCommand):
    help = '清理冗余的 Django 自动生成权限（view_plan 和 view_strategicgoal）'

    def add_arguments(self, parser):
        parser.add_argument(
            '--dry-run',
            action='store_true',
            help='仅显示将要执行的操作，不实际执行',
        )
        parser.add_argument(
            '--force',
            action='store_true',
            help='跳过确认提示，直接删除',
        )

    def handle(self, *args, **options):
        dry_run = options.get('dry_run', False)
        force = options.get('force', False)

        if dry_run:
            self.stdout.write(self.style.WARNING('🔍 模拟运行模式，不会实际修改数据'))

        # 获取模型的 ContentType
        plan_content_type = ContentType.objects.get_for_model(Plan)
        goal_content_type = ContentType.objects.get_for_model(StrategicGoal)

        # 查找要删除的所有默认权限（view, add, change, delete）
        plan_perms = Permission.objects.filter(
            content_type=plan_content_type
        ).exclude(
            # 排除自定义权限（如果有的话）
            codename__startswith='custom_'
        )
        
        goal_perms = Permission.objects.filter(
            content_type=goal_content_type
        ).exclude(
            # 排除自定义权限（如果有的话）
            codename__startswith='custom_'
        )

        plan_count = plan_perms.count()
        goal_count = goal_perms.count()
        
        # 列出将要删除的权限
        plan_perm_list = list(plan_perms.values_list('codename', flat=True))
        goal_perm_list = list(goal_perms.values_list('codename', flat=True))

        self.stdout.write(self.style.WARNING('=' * 70))
        self.stdout.write(self.style.WARNING('彻底清理冗余的 Django 自动生成权限'))
        self.stdout.write(self.style.WARNING('=' * 70))
        self.stdout.write('')
        self.stdout.write('将删除的权限：')
        self.stdout.write(f'  - Plan 模型相关权限: {plan_count} 条')
        if plan_perm_list:
            for perm in plan_perm_list:
                self.stdout.write(f'      • plan_management.{perm}')
        self.stdout.write(f'  - StrategicGoal 模型相关权限: {goal_count} 条')
        if goal_perm_list:
            for perm in goal_perm_list:
                self.stdout.write(f'      • plan_management.{perm}')
        self.stdout.write('')
        self.stdout.write('注意：')
        self.stdout.write('  - 这些是 Django 自动生成的默认权限（view, add, change, delete）')
        self.stdout.write('  - 实际代码中使用的是业务权限：plan_management.plan.view 和 plan_management.goal.view')
        self.stdout.write('  - 删除后不会影响系统功能')
        self.stdout.write('  - 模型 Meta 类已设置 default_permissions = ()，新模型不会再生成默认权限')
        self.stdout.write('')

        if plan_count == 0 and goal_count == 0:
            self.stdout.write(self.style.SUCCESS('✓ 没有找到需要删除的权限'))
            return

        if not force and not dry_run:
            confirm = input('确认删除这些权限？输入 "YES" 继续：')
            if confirm != 'YES':
                self.stdout.write(self.style.ERROR('操作已取消'))
                return

        try:
            with transaction.atomic():
                # 删除 Plan 模型的所有默认权限
                if plan_count > 0:
                    if dry_run:
                        self.stdout.write(self.style.SUCCESS(f'  ✓ 将删除 {plan_count} 条 Plan 模型权限（模拟）'))
                        for perm in plan_perm_list:
                            self.stdout.write(f'      • plan_management.{perm}')
                    else:
                        # 先检查是否有用户或组在使用这些权限
                        from django.contrib.auth.models import Group
                        users_with_perms = User.objects.filter(user_permissions__in=plan_perms).distinct()
                        groups_with_perms = Group.objects.filter(permissions__in=plan_perms).distinct()
                        
                        if users_with_perms.exists() or groups_with_perms.exists():
                            self.stdout.write(self.style.WARNING('  ⚠ 发现以下用户或组正在使用这些权限：'))
                            if users_with_perms.exists():
                                for user in users_with_perms:
                                    self.stdout.write(f'      • 用户: {user.username}')
                            if groups_with_perms.exists():
                                for group in groups_with_perms:
                                    self.stdout.write(f'      • 组: {group.name}')
                            self.stdout.write(self.style.WARNING('  ⚠ 将自动从用户和组中移除这些权限'))
                            
                            # 从用户和组中移除权限
                            for user in users_with_perms:
                                user.user_permissions.remove(*plan_perms)
                            for group in groups_with_perms:
                                group.permissions.remove(*plan_perms)
                        
                        deleted_plan_count = plan_perms.delete()[0]
                        self.stdout.write(self.style.SUCCESS(f'  ✓ 已删除 {deleted_plan_count} 条 Plan 模型权限'))

                # 删除 StrategicGoal 模型的所有默认权限
                if goal_count > 0:
                    if dry_run:
                        self.stdout.write(self.style.SUCCESS(f'  ✓ 将删除 {goal_count} 条 StrategicGoal 模型权限（模拟）'))
                        for perm in goal_perm_list:
                            self.stdout.write(f'      • plan_management.{perm}')
                    else:
                        # 先检查是否有用户或组在使用这些权限
                        from django.contrib.auth.models import Group
                        users_with_perms = User.objects.filter(user_permissions__in=goal_perms).distinct()
                        groups_with_perms = Group.objects.filter(permissions__in=goal_perms).distinct()
                        
                        if users_with_perms.exists() or groups_with_perms.exists():
                            self.stdout.write(self.style.WARNING('  ⚠ 发现以下用户或组正在使用这些权限：'))
                            if users_with_perms.exists():
                                for user in users_with_perms:
                                    self.stdout.write(f'      • 用户: {user.username}')
                            if groups_with_perms.exists():
                                for group in groups_with_perms:
                                    self.stdout.write(f'      • 组: {group.name}')
                            self.stdout.write(self.style.WARNING('  ⚠ 将自动从用户和组中移除这些权限'))
                            
                            # 从用户和组中移除权限
                            for user in users_with_perms:
                                user.user_permissions.remove(*goal_perms)
                            for group in groups_with_perms:
                                group.permissions.remove(*goal_perms)
                        
                        deleted_goal_count = goal_perms.delete()[0]
                        self.stdout.write(self.style.SUCCESS(f'  ✓ 已删除 {deleted_goal_count} 条 StrategicGoal 模型权限'))

                if not dry_run:
                    self.stdout.write('')
                    self.stdout.write(self.style.SUCCESS('=' * 70))
                    self.stdout.write(self.style.SUCCESS('权限清理完成！'))
                    self.stdout.write(self.style.SUCCESS('=' * 70))
                    self.stdout.write('')
                    self.stdout.write('建议：')
                    self.stdout.write('  1. 确保所有代码已更新为使用业务权限（plan_management.plan.view）')
                    self.stdout.write('  2. 运行权限验证命令检查权限配置')
                    self.stdout.write('  3. 测试系统功能确保权限控制正常')

        except Exception as e:
            self.stdout.write('')
            self.stdout.write(self.style.ERROR('=' * 70))
            self.stdout.write(self.style.ERROR('权限清理失败！'))
            self.stdout.write(self.style.ERROR('=' * 70))
            self.stdout.write(self.style.ERROR(f'错误信息：{str(e)}'))
            import traceback
            self.stdout.write(self.style.ERROR(traceback.format_exc()))
            raise

