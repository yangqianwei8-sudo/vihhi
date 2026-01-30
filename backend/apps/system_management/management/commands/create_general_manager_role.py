from django.core.management.base import BaseCommand
from backend.apps.system_management.models import Role


class Command(BaseCommand):
    help = '创建总经理角色'

    def handle(self, *args, **options):
        code = 'general_manager'
        name = '总经理'
        
        # 检查是否已存在
        role = Role.objects.filter(code=code).first()
        if role:
            self.stdout.write(
                self.style.WARNING(
                    f'角色已存在: {role.name} (编码: {role.code})\n'
                    f'  描述: {role.description or "无"}\n'
                    f'  状态: {"启用" if role.is_active else "停用"}'
                )
            )
        else:
            # 创建新角色
            role = Role.objects.create(
                name=name,
                code=code,
                description='总经理角色，拥有系统最高管理权限',
                is_active=True
            )
            self.stdout.write(
                self.style.SUCCESS(
                    f'成功创建角色: {role.name} (编码: {role.code})\n'
                    f'  描述: {role.description}\n'
                    f'  状态: {"启用" if role.is_active else "停用"}'
                )
            )
