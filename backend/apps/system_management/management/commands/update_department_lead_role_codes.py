from django.core.management.base import BaseCommand
from django.db import transaction
from backend.apps.system_management.models import Role, Department


class Command(BaseCommand):
    help = '更新部门负责人角色的编码（基于部门编码）'

    def add_arguments(self, parser):
        parser.add_argument(
            '--dry-run',
            action='store_true',
            help='仅显示将要进行的更改，不实际更新数据库',
        )

    def handle(self, *args, **options):
        dry_run = options['dry_run']
        
        # 获取所有激活的部门
        departments = Department.objects.filter(is_active=True).order_by('name')
        
        if not departments.exists():
            self.stdout.write(self.style.WARNING('没有找到任何激活的部门'))
            return
        
        self.stdout.write(f'找到 {departments.count()} 个部门，开始更新部门负责人角色编码...\n')
        
        updated_count = 0
        not_found_count = 0
        
        with transaction.atomic():
            for dept in departments:
                role_name = f'{dept.name}负责人'
                
                # 查找对应的角色
                role = Role.objects.filter(name=role_name).first()
                
                if not role:
                    self.stdout.write(
                        self.style.WARNING(f'未找到角色: {role_name}')
                    )
                    not_found_count += 1
                    continue
                
                # 生成新的编码
                if dept.code:
                    # 使用部门编码，转换为小写并替换下划线为连字符
                    base_code = dept.code.lower().replace('_', '-').replace('dept-', '')
                    if not base_code.endswith('-lead'):
                        new_code = f'{base_code}-lead'
                    else:
                        new_code = base_code
                else:
                    # 如果没有部门编码，使用部门ID
                    new_code = f'dept-{dept.id}-lead'
                
                # 确保编码唯一
                code = new_code
                counter = 1
                while Role.objects.filter(code=code).exclude(pk=role.pk).exists():
                    code = f'{new_code}-{counter}'
                    counter += 1
                
                # 如果编码不同，则更新
                if role.code != code:
                    old_code = role.code
                    if dry_run:
                        self.stdout.write(
                            f'  [{role.id}] {role.name}: "{old_code}" → "{code}"'
                        )
                    else:
                        role.code = code
                        role.save(update_fields=['code'])
                        self.stdout.write(
                            self.style.SUCCESS(
                                f'  [{role.id}] {role.name}: "{old_code}" → "{code}"'
                            )
                        )
                    updated_count += 1
                else:
                    self.stdout.write(
                        f'  [{role.id}] {role.name}: "{role.code}" (无需更新)'
                    )
            
            if dry_run:
                self.stdout.write(
                    self.style.WARNING(
                        f'\n这是预览模式，没有实际更新数据库。\n'
                        f'将更新 {updated_count} 个角色，{not_found_count} 个角色未找到。'
                    )
                )
                transaction.set_rollback(True)
            else:
                self.stdout.write(
                    self.style.SUCCESS(
                        f'\n完成！已更新 {updated_count} 个角色，{not_found_count} 个角色未找到。'
                    )
                )
