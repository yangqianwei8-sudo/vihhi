"""
管理命令：批量添加文件模板
用法：
    python manage.py seed_file_templates --stage conversion --names "评估报告,服务建议书,报价函"
"""
from django.core.management.base import BaseCommand
from backend.apps.delivery_customer.models import FileTemplate


class Command(BaseCommand):
    help = '批量添加文件模板'

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
            help='模板名称列表，用逗号分隔'
        )

    def handle(self, *args, **options):
        stage_code = options['stage']
        names_str = options['names']
        
        # 验证阶段代码
        valid_stages = [choice[0] for choice in FileTemplate.STAGE_CHOICES]
        if stage_code not in valid_stages:
            self.stdout.write(self.style.ERROR(f'无效的阶段代码: {stage_code}'))
            self.stdout.write(self.style.ERROR(f'有效的阶段代码: {", ".join(valid_stages)}'))
            return
        
        # 解析模板名称
        template_names = [name.strip() for name in names_str.split(',') if name.strip()]
        
        if not template_names:
            self.stdout.write(self.style.ERROR('未提供有效的模板名称'))
            return
        
        stage_name = dict(FileTemplate.STAGE_CHOICES)[stage_code]
        self.stdout.write(f'开始为"{stage_name}"添加文件模板...')
        
        created_count = 0
        skipped_count = 0
        
        # 获取该阶段已有的模板数量（用于生成代码）
        existing_count = FileTemplate.objects.filter(stage=stage_code).count()
        stage_prefix = stage_code.upper()
        
        for idx, name in enumerate(template_names):
            # 检查是否已存在同名模板
            if FileTemplate.objects.filter(stage=stage_code, name=name).exists():
                self.stdout.write(self.style.WARNING(f'  ⚠️  跳过: "{name}" 已存在'))
                skipped_count += 1
                continue
            
            # 生成模板代码
            template_code = f"{stage_prefix}_TEMPLATE_{existing_count + idx + 1:03d}"
            
            # 确保代码唯一
            while FileTemplate.objects.filter(code=template_code).exists():
                existing_count += 1
                template_code = f"{stage_prefix}_TEMPLATE_{existing_count + idx + 1:03d}"
            
            # 创建模板
            template = FileTemplate(
                name=name,
                code=template_code,
                stage=stage_code,
                sort_order=existing_count + idx + 1,
                is_active=True,
            )
            template.save()
            
            self.stdout.write(self.style.SUCCESS(f'  ✅ 创建: "{name}" (代码: {template_code})'))
            created_count += 1
        
        self.stdout.write('')
        self.stdout.write(self.style.SUCCESS(f'完成！创建 {created_count} 个模板，跳过 {skipped_count} 个已存在的模板'))

