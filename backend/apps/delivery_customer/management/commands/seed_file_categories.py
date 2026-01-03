"""
管理命令：批量添加文件分类
用法：
    python manage.py seed_file_categories --stage conversion --names "评估图纸,报价文件,投标文件"
"""
from django.core.management.base import BaseCommand
from backend.apps.delivery_customer.models import FileCategory


class Command(BaseCommand):
    help = '批量添加文件分类'

    def add_arguments(self, parser):
        parser.add_argument(
            '--stage',
            type=str,
            required=True,
            help='阶段代码（conversion, contract, production, settlement, payment, after_sales, litigation）'
        )
        parser.add_argument(
            '--names',
            type=str,
            required=True,
            help='分类名称列表，用逗号分隔'
        )

    def handle(self, *args, **options):
        stage_code = options['stage']
        names_str = options['names']
        
        # 验证阶段代码
        valid_stages = [choice[0] for choice in FileCategory.STAGE_CHOICES]
        if stage_code not in valid_stages:
            self.stdout.write(self.style.ERROR(f'无效的阶段代码: {stage_code}'))
            self.stdout.write(self.style.ERROR(f'有效的阶段代码: {", ".join(valid_stages)}'))
            return
        
        # 解析分类名称
        category_names = [name.strip() for name in names_str.split(',') if name.strip()]
        
        if not category_names:
            self.stdout.write(self.style.ERROR('未提供有效的分类名称'))
            return
        
        stage_name = dict(FileCategory.STAGE_CHOICES)[stage_code]
        self.stdout.write(f'开始为"{stage_name}"添加文件分类...')
        
        created_count = 0
        skipped_count = 0
        
        # 获取该阶段已有的分类数量（用于生成代码）
        existing_count = FileCategory.objects.filter(stage=stage_code).count()
        stage_prefix = stage_code.upper()
        
        for idx, name in enumerate(category_names):
            # 检查是否已存在同名分类
            if FileCategory.objects.filter(stage=stage_code, name=name).exists():
                self.stdout.write(self.style.WARNING(f'  ⚠️  跳过: "{name}" 已存在'))
                skipped_count += 1
                continue
            
            # 生成分类代码
            category_code = f"{stage_prefix}_{existing_count + idx + 1:03d}"
            
            # 确保代码唯一
            while FileCategory.objects.filter(code=category_code).exists():
                existing_count += 1
                category_code = f"{stage_prefix}_{existing_count + idx + 1:03d}"
            
            # 创建分类
            category = FileCategory(
                name=name,
                code=category_code,
                stage=stage_code,
                sort_order=existing_count + idx + 1,
                is_active=True,
            )
            category.save()
            
            self.stdout.write(self.style.SUCCESS(f'  ✅ 创建: "{name}" (代码: {category_code})'))
            created_count += 1
        
        self.stdout.write('')
        self.stdout.write(self.style.SUCCESS(f'完成！创建 {created_count} 个分类，跳过 {skipped_count} 个已存在的分类'))

