"""
管理命令：彻底清理所有冗余权限

此脚本会清理以下所有冗余权限：
1. Django 自动生成的权限（auth_permission 表）：
   - plan_management.view_plan
   - plan_management.add_plan
   - plan_management.change_plan
   - plan_management.delete_plan
   - plan_management.view_strategicgoal
   - plan_management.add_strategicgoal
   - plan_management.change_strategicgoal
   - plan_management.delete_strategicgoal

2. 业务权限表中的冗余权限（system_permission_item 表）：
   - plan_management.view_plan（应使用 plan_management.plan.view）
   - plan_management.view_strategicgoal（应使用 plan_management.goal.view）

3. 从用户、组、角色中移除这些权限

注意：模型 Meta 类已设置 default_permissions = ()，新创建的模型不会再生成默认权限。
"""
from django.core.management.base import BaseCommand
from django.contrib.auth.models import Permission, Group
from django.contrib.contenttypes.models import ContentType
from django.db import transaction
from django.contrib.auth import get_user_model
from backend.apps.plan_management.models import Plan, StrategicGoal
from backend.apps.permission_management.models import PermissionItem
from backend.apps.system_management.models import Role

User = get_user_model()


class Command(BaseCommand):
    help = '彻底清理所有冗余权限（Django 自动生成权限和业务权限表中的冗余项）'

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

        self.stdout.write(self.style.WARNING('=' * 70))
        self.stdout.write(self.style.WARNING('彻底清理所有冗余权限'))
        self.stdout.write(self.style.WARNING('=' * 70))
        self.stdout.write('')

        try:
            with transaction.atomic():
                # ========== 步骤 1：清理 Django 自动生成的权限 ==========
                self.stdout.write(self.style.SUCCESS('步骤 1：清理 Django 自动生成的权限（auth_permission 表）'))
                self.stdout.write('-' * 70)
                
                plan_content_type = ContentType.objects.get_for_model(Plan)
                goal_content_type = ContentType.objects.get_for_model(StrategicGoal)

                # 查找要删除的所有默认权限
                plan_perms = Permission.objects.filter(
                    content_type=plan_content_type
                ).exclude(
                    codename__startswith='custom_'
                )
                
                goal_perms = Permission.objects.filter(
                    content_type=goal_content_type
                ).exclude(
                    codename__startswith='custom_'
                )

                plan_count = plan_perms.count()
                goal_count = goal_perms.count()
                
                plan_perm_list = list(plan_perms.values_list('codename', flat=True))
                goal_perm_list = list(goal_perms.values_list('codename', flat=True))

                if plan_count > 0 or goal_count > 0:
                    self.stdout.write(f'  找到 Plan 模型权限: {plan_count} 条')
                    for perm in plan_perm_list:
                        self.stdout.write(f'    • plan_management.{perm}')
                    
                    self.stdout.write(f'  找到 StrategicGoal 模型权限: {goal_count} 条')
                    for perm in goal_perm_list:
                        self.stdout.write(f'    • plan_management.{perm}')
                    
                    if not dry_run:
                        # 从用户和组中移除权限
                        all_perms = list(plan_perms) + list(goal_perms)
                        
                        users_with_perms = User.objects.filter(user_permissions__in=all_perms).distinct()
                        groups_with_perms = Group.objects.filter(permissions__in=all_perms).distinct()
                        
                        if users_with_perms.exists():
                            self.stdout.write(self.style.WARNING(f'  ⚠ 从 {users_with_perms.count()} 个用户中移除权限'))
                            for user in users_with_perms:
                                user.user_permissions.remove(*all_perms)
                        
                        if groups_with_perms.exists():
                            self.stdout.write(self.style.WARNING(f'  ⚠ 从 {groups_with_perms.count()} 个组中移除权限'))
                            for group in groups_with_perms:
                                group.permissions.remove(*all_perms)
                        
                        # 删除权限
                        deleted_plan_count = plan_perms.delete()[0]
                        deleted_goal_count = goal_perms.delete()[0]
                        self.stdout.write(self.style.SUCCESS(f'  ✓ 已删除 {deleted_plan_count + deleted_goal_count} 条 Django 权限'))
                    else:
                        self.stdout.write(self.style.SUCCESS(f'  ✓ 将删除 {plan_count + goal_count} 条 Django 权限（模拟）'))
                else:
                    self.stdout.write(self.style.SUCCESS('  ✓ 没有找到需要删除的 Django 权限'))

                self.stdout.write('')

                # ========== 步骤 2：清理业务权限表中的冗余权限 ==========
                self.stdout.write(self.style.SUCCESS('步骤 2：清理业务权限表中的冗余权限（system_permission_item 表）'))
                self.stdout.write('-' * 70)
                
                redundant_business_perms = PermissionItem.objects.filter(
                    code__in=['plan_management.view_plan', 'plan_management.view_strategicgoal']
                )

                business_perm_count = redundant_business_perms.count()

                if business_perm_count > 0:
                    for perm in redundant_business_perms:
                        self.stdout.write(f'  • {perm.code}: {perm.name}')
                    
                    if not dry_run:
                        # 从角色中移除权限
                        roles_with_perms = Role.objects.filter(custom_permissions__in=redundant_business_perms).distinct()
                        
                        if roles_with_perms.exists():
                            self.stdout.write(self.style.WARNING(f'  ⚠ 从 {roles_with_perms.count()} 个角色中移除权限'))
                            for role in roles_with_perms:
                                role.custom_permissions.remove(*redundant_business_perms)
                        
                        # 删除权限项
                        deleted_business_count = redundant_business_perms.delete()[0]
                        self.stdout.write(self.style.SUCCESS(f'  ✓ 已删除 {deleted_business_count} 条业务权限项'))
                    else:
                        self.stdout.write(self.style.SUCCESS(f'  ✓ 将删除 {business_perm_count} 条业务权限项（模拟）'))
                else:
                    self.stdout.write(self.style.SUCCESS('  ✓ 没有找到需要删除的业务权限项'))

                self.stdout.write('')

                # ========== 步骤 3：验证清理结果 ==========
                self.stdout.write(self.style.SUCCESS('步骤 3：验证清理结果'))
                self.stdout.write('-' * 70)
                
                # 检查 Django 权限
                remaining_plan_perms = Permission.objects.filter(
                    content_type=plan_content_type
                ).exclude(codename__startswith='custom_').count()
                remaining_goal_perms = Permission.objects.filter(
                    content_type=goal_content_type
                ).exclude(codename__startswith='custom_').count()
                
                if remaining_plan_perms == 0 and remaining_goal_perms == 0:
                    self.stdout.write(self.style.SUCCESS('  ✓ Django 权限清理完成'))
                else:
                    self.stdout.write(self.style.WARNING(f'  ⚠ 仍有 {remaining_plan_perms + remaining_goal_perms} 条 Django 权限存在'))
                
                # 检查业务权限
                remaining_business_perms = PermissionItem.objects.filter(
                    code__in=['plan_management.view_plan', 'plan_management.view_strategicgoal']
                ).count()
                
                if remaining_business_perms == 0:
                    self.stdout.write(self.style.SUCCESS('  ✓ 业务权限清理完成'))
                else:
                    self.stdout.write(self.style.WARNING(f'  ⚠ 仍有 {remaining_business_perms} 条业务权限存在'))
                
                # 检查标准权限是否存在
                standard_perms = PermissionItem.objects.filter(
                    code__in=['plan_management.plan.view', 'plan_management.goal.view']
                )
                self.stdout.write('')
                self.stdout.write('标准业务权限状态：')
                for perm in standard_perms:
                    self.stdout.write(self.style.SUCCESS(f'  ✓ {perm.code}: {perm.name}'))
                
                if standard_perms.count() < 2:
                    self.stdout.write(self.style.WARNING('  ⚠ 警告：标准权限不完整，请运行 python manage.py seed_permissions'))

                if not dry_run:
                    self.stdout.write('')
                    self.stdout.write(self.style.SUCCESS('=' * 70))
                    self.stdout.write(self.style.SUCCESS('权限清理完成！'))
                    self.stdout.write(self.style.SUCCESS('=' * 70))
                    self.stdout.write('')
                    self.stdout.write('建议：')
                    self.stdout.write('  1. 运行 python manage.py migrate 确保数据库同步')
                    self.stdout.write('  2. 运行 python manage.py seed_permissions 确保标准权限存在')
                    self.stdout.write('  3. 检查角色配置，确保只使用标准权限（plan_management.plan.view）')
                    self.stdout.write('  4. 测试系统功能确保权限控制正常')

        except Exception as e:
            self.stdout.write('')
            self.stdout.write(self.style.ERROR('=' * 70))
            self.stdout.write(self.style.ERROR('权限清理失败！'))
            self.stdout.write(self.style.ERROR('=' * 70))
            self.stdout.write(self.style.ERROR(f'错误信息：{str(e)}'))
            import traceback
            self.stdout.write(self.style.ERROR(traceback.format_exc()))
            raise

