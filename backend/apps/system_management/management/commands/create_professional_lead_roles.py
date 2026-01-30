from django.core.management.base import BaseCommand
from django.utils.text import slugify
from backend.apps.system_management.models import Role


class Command(BaseCommand):
    help = '创建专业负责人角色（结构、建筑、电气、给排、暖通）'

    def handle(self, *args, **options):
        # 定义要创建的角色
        roles_to_create = [
            {
                'name': '结构专业负责人',
                'code': 'structural-professional-lead',
                'description': '结构专业负责人角色，负责结构专业相关工作'
            },
            {
                'name': '建筑专业负责人',
                'code': 'architectural-professional-lead',
                'description': '建筑专业负责人角色，负责建筑专业相关工作'
            },
            {
                'name': '电气专业负责人',
                'code': 'electrical-professional-lead',
                'description': '电气专业负责人角色，负责电气专业相关工作'
            },
            {
                'name': '给排专业负责人',
                'code': 'plumbing-professional-lead',
                'description': '给排专业负责人角色，负责给排水专业相关工作'
            },
            {
                'name': '暖通专业负责人',
                'code': 'hvac-professional-lead',
                'description': '暖通专业负责人角色，负责暖通空调专业相关工作'
            },
        ]
        
        created_count = 0
        existing_count = 0
        
        for role_data in roles_to_create:
            # 检查角色是否已存在（按编码）
            role = Role.objects.filter(code=role_data['code']).first()
            
            if role:
                self.stdout.write(
                    self.style.WARNING(
                        f'角色已存在: {role.name} (编码: {role.code})'
                    )
                )
                existing_count += 1
            else:
                # 检查是否已存在同名角色
                existing_by_name = Role.objects.filter(name=role_data['name']).first()
                if existing_by_name:
                    self.stdout.write(
                        self.style.WARNING(
                            f'同名角色已存在: {existing_by_name.name} (编码: {existing_by_name.code})'
                        )
                    )
                    existing_count += 1
                else:
                    # 创建新角色
                    role = Role.objects.create(
                        name=role_data['name'],
                        code=role_data['code'],
                        description=role_data['description'],
                        is_active=True
                    )
                    self.stdout.write(
                        self.style.SUCCESS(
                            f'成功创建角色: {role.name} (编码: {role.code})'
                        )
                    )
                    created_count += 1
        
        self.stdout.write(
            self.style.SUCCESS(
                f'\n完成！创建了 {created_count} 个新角色，{existing_count} 个角色已存在。'
            )
        )
