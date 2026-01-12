"""
初始化任务自动转交配置

将现有的硬编码配置迁移到数据库中。
运行方式：python manage.py init_task_transfer_configs
"""
from django.core.management.base import BaseCommand
from django.contrib.auth import get_user_model
from backend.apps.production_management.models import TaskAutoTransferConfig

User = get_user_model()


class Command(BaseCommand):
    help = '初始化任务自动转交配置，将硬编码配置迁移到数据库'

    def add_arguments(self, parser):
        parser.add_argument(
            '--dry-run',
            action='store_true',
            help='仅显示将要创建的配置，不实际创建',
        )
        parser.add_argument(
            '--overwrite',
            action='store_true',
            help='如果配置已存在，则覆盖更新',
        )

    def handle(self, *args, **options):
        dry_run = options['dry_run']
        overwrite = options['overwrite']
        
        # 从views_pages.py中读取硬编码配置
        # 注意：这里需要与views_pages.py中的TASK_COMPLETION_FOLLOWUPS保持一致
        hardcoded_configs = {
            'design_reply_opinions': ['organize_tripartite_meeting'],
            'client_confirm_meeting': [],
            'organize_tripartite_meeting': ['design_upload_revisions'],
            'design_upload_revisions': ['internal_verify_revisions'],
            'internal_verify_revisions': ['client_confirm_outcome'],
        }
        
        # 获取系统用户（用于创建人）
        system_user = User.objects.filter(is_superuser=True).first()
        if not system_user:
            system_user = User.objects.filter(is_staff=True).first()
        if not system_user:
            self.stdout.write(self.style.ERROR('未找到系统用户，无法创建配置'))
            return
        
        created_count = 0
        updated_count = 0
        skipped_count = 0
        
        self.stdout.write(self.style.SUCCESS('开始初始化任务自动转交配置...\n'))
        
        for source_task_type, target_task_types in hardcoded_configs.items():
            if not target_task_types:
                continue
            
            for order, target_task_type in enumerate(target_task_types):
                # 检查是否已存在
                existing = TaskAutoTransferConfig.objects.filter(
                    source_task_type=source_task_type,
                    target_task_type=target_task_type,
                    condition_type='always'
                ).first()
                
                if existing:
                    if overwrite:
                        if not dry_run:
                            existing.is_active = True
                            existing.order = order
                            existing.save()
                        dry_run_prefix = '[DRY RUN] ' if dry_run else ''
                        self.stdout.write(
                            f'  {dry_run_prefix}更新: '
                            f'{source_task_type} → {target_task_type}'
                        )
                        updated_count += 1
                    else:
                        self.stdout.write(
                            self.style.WARNING(
                                f'  跳过（已存在）: {source_task_type} → {target_task_type}'
                            )
                        )
                        skipped_count += 1
                else:
                    if not dry_run:
                        TaskAutoTransferConfig.objects.create(
                            source_task_type=source_task_type,
                            target_task_type=target_task_type,
                            condition_type='always',
                            is_active=True,
                            order=order,
                            description=f'从硬编码配置迁移：{source_task_type} → {target_task_type}',
                            created_by=system_user
                        )
                    dry_run_prefix = '[DRY RUN] ' if dry_run else ''
                    self.stdout.write(
                        f'  {dry_run_prefix}创建: '
                        f'{source_task_type} → {target_task_type}'
                    )
                    created_count += 1
        
        self.stdout.write('\n' + '='*60)
        self.stdout.write(self.style.SUCCESS(f'初始化完成！'))
        self.stdout.write(f'  创建: {created_count} 条')
        self.stdout.write(f'  更新: {updated_count} 条')
        self.stdout.write(f'  跳过: {skipped_count} 条')
        
        if dry_run:
            self.stdout.write(self.style.WARNING('\n这是预览模式，未实际创建配置。'))
            self.stdout.write('运行时不加 --dry-run 参数即可实际创建。')

