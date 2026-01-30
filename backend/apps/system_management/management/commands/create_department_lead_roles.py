from django.core.management.base import BaseCommand
from django.utils.text import slugify
from backend.apps.system_management.models import Role, Department


class Command(BaseCommand):
    help = '为所有部门创建部门负责人角色'

    def handle(self, *args, **options):
        # 获取所有激活的部门
        departments = Department.objects.filter(is_active=True).order_by('name')
        
        if not departments.exists():
            self.stdout.write(self.style.WARNING('没有找到任何激活的部门'))
            return
        
        self.stdout.write(f'找到 {departments.count()} 个部门，开始创建部门负责人角色...\n')
        
        created_count = 0
        existing_count = 0
        skipped_count = 0
        
        for dept in departments:
            # 生成角色名称和编码
            role_name = f'{dept.name}负责人'
            
            # 基于部门编码生成角色编码（优先使用部门编码）
            if dept.code:
                # 使用部门编码，转换为小写并替换下划线为连字符
                base_code = dept.code.lower().replace('_', '-').replace('dept-', '')
                if not base_code.endswith('-lead'):
                    base_code = f'{base_code}-lead'
            else:
                # 如果没有部门编码，尝试从部门名称生成
                base_code = slugify(f'{dept.name}-lead')
                if not base_code:
                    base_code = f'dept-{dept.id}-lead'
            
            # 确保编码唯一
            code = base_code
            counter = 1
            while Role.objects.filter(code=code).exists():
                code = f'{base_code}-{counter}'
                counter += 1
            
            # 检查角色是否已存在（按编码或名称）
            existing_role = Role.objects.filter(code=code).first()
            if not existing_role:
                existing_role = Role.objects.filter(name=role_name).first()
            
            if existing_role:
                self.stdout.write(
                    self.style.WARNING(
                        f'角色已存在: {existing_role.name} (编码: {existing_role.code})'
                    )
                )
                existing_count += 1
            else:
                # 创建新角色
                role = Role.objects.create(
                    name=role_name,
                    code=code,
                    description=f'{dept.name}部门负责人角色，负责该部门的管理工作',
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
