"""
创建部门经理角色并分配给指定用户
运行方式：python manage.py create_department_manager_role --username 杨乾维
"""
import logging
from django.core.management.base import BaseCommand
from backend.apps.system_management.models import Role, User

logger = logging.getLogger(__name__)


class Command(BaseCommand):
    help = '创建部门经理角色（department_manager）并分配给指定用户'

    def add_arguments(self, parser):
        parser.add_argument(
            '--username',
            type=str,
            help='要分配角色的用户名（可选，如果不指定则只创建角色）',
        )
        parser.add_argument(
            '--role-code',
            type=str,
            default='department_manager',
            help='角色代码（默认：department_manager）',
        )
        parser.add_argument(
            '--role-name',
            type=str,
            default='部门经理',
            help='角色名称（默认：部门经理）',
        )

    def handle(self, *args, **options):
        username = options.get('username')
        role_code = options['role_code']
        role_name = options['role_name']
        
        self.stdout.write(self.style.SUCCESS(f'开始创建角色: {role_name} ({role_code})'))
        
        # 创建或获取角色
        role, created = Role.objects.get_or_create(
            code=role_code,
            defaults={
                'name': role_name,
                'description': f'{role_name}角色，用于审批流程中的部门经理审批节点',
                'is_active': True,
            }
        )
        
        if created:
            self.stdout.write(self.style.SUCCESS(f'✓ 创建角色: {role.name} (代码: {role.code})'))
        else:
            self.stdout.write(self.style.WARNING(f'角色已存在: {role.name} (代码: {role.code})'))
            # 确保角色是激活状态
            if not role.is_active:
                role.is_active = True
                role.save()
                self.stdout.write(self.style.SUCCESS(f'✓ 已激活角色: {role.name}'))
        
        # 如果指定了用户名，则分配角色
        if username:
            try:
                user = User.objects.get(username=username)
                self.stdout.write(f'\n处理用户: {user.username} ({user.get_full_name() or user.username})')
                
                # 检查用户是否已有该角色
                if user.roles.filter(code=role_code).exists():
                    self.stdout.write(self.style.WARNING(f'用户 {user.username} 已有角色 {role.name}'))
                else:
                    user.roles.add(role)
                    self.stdout.write(self.style.SUCCESS(f'✓ 已将角色 {role.name} 分配给用户 {user.username}'))
                
                # 显示用户当前的所有角色
                user_roles = user.roles.filter(is_active=True)
                if user_roles.exists():
                    self.stdout.write(f'\n用户 {user.username} 当前的角色:')
                    for r in user_roles:
                        self.stdout.write(f'  - {r.name} (代码: {r.code})')
                
            except User.DoesNotExist:
                self.stdout.write(self.style.ERROR(f'用户不存在: {username}'))
                self.stdout.write(self.style.WARNING('角色已创建，但未分配给用户'))
        else:
            self.stdout.write(self.style.WARNING('\n未指定用户名，仅创建了角色'))
            self.stdout.write(self.style.WARNING('要分配角色给用户，请使用: --username <用户名>'))
        
        self.stdout.write(self.style.SUCCESS(f'\n完成！'))
        self.stdout.write(self.style.WARNING('\n注意：'))
        self.stdout.write(self.style.WARNING('1. 角色代码必须是: department_manager'))
        self.stdout.write(self.style.WARNING('2. 用户必须在该部门中，审批流程才会自动分配给他'))
        self.stdout.write(self.style.WARNING('3. 或者可以在审批节点中直接指定用户作为审批人'))
