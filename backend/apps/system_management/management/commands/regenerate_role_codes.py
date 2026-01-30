from django.core.management.base import BaseCommand
from django.utils.text import slugify
from django.db import transaction
from backend.apps.system_management.models import Role

# 中文角色名称到英文编码的映射表
ROLE_NAME_TO_CODE_MAP = {
    '测试员': 'tester',
    '行政主管': 'admin-supervisor',
    '会计主管': 'accounting-supervisor',
    '专业工程师': 'professional-engineer',
    '商务经理': 'business-manager',
    '部门经理': 'department-manager',
    '总经理': 'general-manager',
}


class Command(BaseCommand):
    help = '重新生成所有角色的编码（基于角色名称使用 slugify）'

    def add_arguments(self, parser):
        parser.add_argument(
            '--dry-run',
            action='store_true',
            help='仅显示将要进行的更改，不实际更新数据库',
        )
        parser.add_argument(
            '--force',
            action='store_true',
            help='强制重新生成所有角色的编码（包括已有标准编码的角色）',
        )

    def handle(self, *args, **options):
        dry_run = options['dry_run']
        force = options['force']
        
        roles = Role.objects.all().order_by('id')
        total = roles.count()
        
        if total == 0:
            self.stdout.write(self.style.WARNING('没有找到任何角色'))
            return
        
        self.stdout.write(f'找到 {total} 个角色，开始重新生成编码...\n')
        
        updated_count = 0
        skipped_count = 0
        errors = []
        
        # 用于跟踪已使用的编码，确保唯一性
        used_codes = set()
        
        with transaction.atomic():
            for role in roles:
                # 判断当前编码是否是拼音缩写（需要重新生成）
                current_code = role.code.lower()
                is_pinyin_abbreviation = (
                    len(current_code) <= 6 and
                    current_code.isalpha() and
                    '_' not in current_code and
                    '-' not in current_code
                )
                
                # 标准格式：有下划线或连字符，或者长度较长
                is_standard_format = (
                    '_' in current_code or 
                    '-' in current_code or
                    len(current_code) > 10
                )
                
                # 生成新的编码
                # 首先检查映射表
                if role.name in ROLE_NAME_TO_CODE_MAP:
                    base_code = ROLE_NAME_TO_CODE_MAP[role.name]
                else:
                    base_code = slugify(role.name)
                    
                    # 如果 slugify 结果为空（通常是纯中文），且原编码是拼音缩写，需要生成新编码
                    if not base_code:
                        if is_pinyin_abbreviation:
                            # 对于拼音缩写，使用角色ID生成临时编码，然后手动处理
                            base_code = f'role-{role.id}'
                        else:
                            # 如果已经是标准格式，保持原编码格式（下划线转连字符）
                            base_code = current_code.replace('_', '-')
                
                # 确保编码唯一
                code = base_code
                counter = 1
                while code in used_codes or (code != role.code and Role.objects.filter(code=code).exclude(pk=role.pk).exists()):
                    code = f'{base_code}-{counter}'
                    counter += 1
                
                used_codes.add(code)
                
                # 判断是否需要更新
                should_update = False
                if force:
                    should_update = True
                elif is_pinyin_abbreviation:
                    # 如果是拼音缩写，强制更新
                    should_update = True
                elif code != role.code and not is_standard_format:
                    # 如果新编码不同且原编码不是标准格式，则更新
                    should_update = True
                
                if should_update:
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
                        f'  [{role.id}] {role.name}: "{role.code}" (跳过，已为标准格式)'
                    )
                    skipped_count += 1
            
            if dry_run:
                self.stdout.write(
                    self.style.WARNING(
                        f'\n这是预览模式，没有实际更新数据库。\n'
                        f'将更新 {updated_count} 个角色，跳过 {skipped_count} 个角色。'
                    )
                )
                # 在 dry-run 模式下，不提交事务
                transaction.set_rollback(True)
            else:
                self.stdout.write(
                    self.style.SUCCESS(
                        f'\n完成！已更新 {updated_count} 个角色，跳过 {skipped_count} 个角色。'
                    )
                )
        
        if errors:
            self.stdout.write(
                self.style.ERROR(f'\n发生 {len(errors)} 个错误：')
            )
            for error in errors:
                self.stdout.write(self.style.ERROR(f'  - {error}'))
