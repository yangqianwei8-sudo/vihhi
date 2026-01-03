from django.core.management.base import BaseCommand
from django.db import transaction
from backend.apps.customer_management.models import BusinessOpportunity


class Command(BaseCommand):
    help = '删除所有商机数据（用于上传正式数据前清理）'
    
    def add_arguments(self, parser):
        parser.add_argument(
            '--dry-run',
            action='store_true',
            help='仅显示将要删除的商机数量，不实际删除',
        )
        parser.add_argument(
            '--confirm',
            action='store_true',
            help='确认删除，无需交互确认',
        )
    
    def handle(self, *args, **options):
        dry_run = options['dry_run']
        confirm = options['confirm']
        
        # 统计所有商机
        total_count = BusinessOpportunity.objects.count()
        
        if total_count == 0:
            self.stdout.write(self.style.SUCCESS('✓ 数据库中没有商机数据'))
            return
        
        self.stdout.write(self.style.WARNING(f'\n找到 {total_count} 个商机记录'))
        
        # 统计关联数据（会级联删除）
        from backend.apps.customer_management.models import (
            OpportunityFollowUp,
            BusinessOpportunityAttachment,
            OpportunityStatusLog
        )
        
        followup_count = OpportunityFollowUp.objects.count()
        attachment_count = BusinessOpportunityAttachment.objects.count()
        
        # 尝试统计状态日志（如果模型存在）
        try:
            status_log_count = OpportunityStatusLog.objects.count()
        except:
            status_log_count = 0
        
        self.stdout.write(f'\n关联数据统计：')
        self.stdout.write(f'  - 商机跟进记录: {followup_count} 条')
        self.stdout.write(f'  - 商机附件: {attachment_count} 条')
        if status_log_count > 0:
            self.stdout.write(f'  - 状态流转日志: {status_log_count} 条')
        self.stdout.write(f'\n注意：删除商机时会自动级联删除所有关联数据')
        
        if dry_run:
            self.stdout.write(self.style.WARNING('\n[DRY RUN模式] 以上数据将被删除'))
            return
        
        # 确认删除
        if not confirm:
            self.stdout.write(self.style.ERROR('\n⚠️  警告：此操作将永久删除所有商机数据，无法恢复！'))
            confirm_input = input('请输入 "YES" 确认删除: ')
            if confirm_input != 'YES':
                self.stdout.write(self.style.ERROR('操作已取消'))
                return
        
        # 执行删除
        try:
            with transaction.atomic():
                deleted_count = BusinessOpportunity.objects.all().delete()[0]
                self.stdout.write(self.style.SUCCESS(f'\n✓ 成功删除 {deleted_count} 个商机记录（包括所有关联数据）'))
                
                # 验证删除结果
                remaining_count = BusinessOpportunity.objects.count()
                if remaining_count == 0:
                    self.stdout.write(self.style.SUCCESS('✓ 所有商机数据已清理完毕'))
                else:
                    self.stdout.write(self.style.WARNING(f'⚠️  仍有 {remaining_count} 个商机记录未删除'))
                    
        except Exception as e:
            self.stdout.write(self.style.ERROR(f'\n✗ 删除失败: {str(e)}'))
            raise

