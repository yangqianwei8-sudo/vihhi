"""
修复审批流程中的时区问题
将非时区感知的时间转换为时区感知的时间（UTC）
"""
from django.core.management.base import BaseCommand
from django.utils import timezone
from backend.apps.workflow_engine.models import ApprovalInstance


class Command(BaseCommand):
    help = '修复审批流程中的时区问题，将非时区感知的时间转换为时区感知的时间'

    def add_arguments(self, parser):
        parser.add_argument(
            '--dry-run',
            action='store_true',
            help='仅检查不修改，显示需要修复的记录'
        )

    def handle(self, *args, **options):
        dry_run = options.get('dry_run', False)
        
        if dry_run:
            self.stdout.write(self.style.WARNING('🔍 仅检查模式，不会修改任何数据\n'))
        
        # 查找所有非时区感知的时间记录
        instances = ApprovalInstance.objects.all()
        
        apply_time_fixes = 0
        completed_time_fixes = 0
        
        for instance in instances:
            needs_save = False
            
            # 修复 apply_time
            if instance.apply_time and not timezone.is_aware(instance.apply_time):
                if dry_run:
                    self.stdout.write(
                        f'实例 {instance.instance_number}: apply_time 需要修复 '
                        f'({instance.apply_time} -> UTC时区感知)'
                    )
                else:
                    # 假设旧数据是 UTC 时间，转换为时区感知
                    instance.apply_time = timezone.make_aware(instance.apply_time, timezone.utc)
                    needs_save = True
                    apply_time_fixes += 1
            
            # 修复 completed_time
            if instance.completed_time and not timezone.is_aware(instance.completed_time):
                if dry_run:
                    self.stdout.write(
                        f'实例 {instance.instance_number}: completed_time 需要修复 '
                        f'({instance.completed_time} -> UTC时区感知)'
                    )
                else:
                    # 假设旧数据是 UTC 时间，转换为时区感知
                    instance.completed_time = timezone.make_aware(instance.completed_time, timezone.utc)
                    needs_save = True
                    completed_time_fixes += 1
            
            if needs_save and not dry_run:
                instance.save(update_fields=['apply_time', 'completed_time'])
        
        self.stdout.write('\n' + '='*60)
        if dry_run:
            self.stdout.write(f'检查完成！发现 {apply_time_fixes} 个 apply_time 需要修复')
            self.stdout.write(f'发现 {completed_time_fixes} 个 completed_time 需要修复')
            self.stdout.write('运行时不加 --dry-run 参数即可应用修复')
        else:
            self.stdout.write(self.style.SUCCESS(f'修复完成！'))
            self.stdout.write(f'已修复 {apply_time_fixes} 个 apply_time')
            self.stdout.write(f'已修复 {completed_time_fixes} 个 completed_time')
        self.stdout.write('='*60)

