"""
管理命令：强制删除所有战略目标数据

用法：
    python manage.py delete_all_goals
    
警告：此操作将删除所有战略目标及其关联数据，不可恢复！
"""
from django.core.management.base import BaseCommand
from django.db import transaction
from backend.apps.plan_management.models import (
    StrategicGoal,
    GoalProgressRecord,
    GoalStatusLog,
    GoalAdjustment,
    GoalAlignmentRecord
)


class Command(BaseCommand):
    help = '强制删除所有战略目标数据（包括关联数据）'

    def add_arguments(self, parser):
        parser.add_argument(
            '--force',
            action='store_true',
            help='跳过确认提示，直接删除',
        )

    def handle(self, *args, **options):
        force = options.get('force', False)
        
        # 统计要删除的数据
        goal_count = StrategicGoal.objects.count()
        progress_count = GoalProgressRecord.objects.count()
        status_log_count = GoalStatusLog.objects.count()
        adjustment_count = GoalAdjustment.objects.count()
        alignment_count = GoalAlignmentRecord.objects.count()
        
        self.stdout.write(self.style.WARNING('=' * 60))
        self.stdout.write(self.style.WARNING('警告：此操作将删除所有战略目标数据！'))
        self.stdout.write(self.style.WARNING('=' * 60))
        self.stdout.write('')
        self.stdout.write(f'将删除的数据统计：')
        self.stdout.write(f'  - 战略目标：{goal_count} 条')
        self.stdout.write(f'  - 进度记录：{progress_count} 条')
        self.stdout.write(f'  - 状态日志：{status_log_count} 条')
        self.stdout.write(f'  - 调整记录：{adjustment_count} 条')
        self.stdout.write(f'  - 对齐记录：{alignment_count} 条')
        self.stdout.write('')
        
        if not force:
            confirm = input('确认删除所有数据？输入 "YES" 继续：')
            if confirm != 'YES':
                self.stdout.write(self.style.ERROR('操作已取消'))
                return
        
        try:
            with transaction.atomic():
                # 1. 清除多对多关系（必须先清除，避免外键约束问题）
                self.stdout.write('正在清除多对多关系...')
                for goal in StrategicGoal.objects.all():
                    goal.participants.clear()
                self.stdout.write(self.style.SUCCESS('  ✓ 已清除所有多对多关系'))
                
                # 2. 删除对齐记录（独立的外键关系）
                self.stdout.write('正在删除对齐记录...')
                alignment_deleted = GoalAlignmentRecord.objects.all().delete()[0]
                self.stdout.write(self.style.SUCCESS(f'  ✓ 已删除 {alignment_deleted} 条对齐记录'))
                
                # 3. 删除调整记录（独立的外键关系）
                self.stdout.write('正在删除调整记录...')
                adjustment_deleted = GoalAdjustment.objects.all().delete()[0]
                self.stdout.write(self.style.SUCCESS(f'  ✓ 已删除 {adjustment_deleted} 条调整记录'))
                
                # 4. 删除所有战略目标（CASCADE会自动删除GoalProgressRecord和GoalStatusLog）
                # 由于parent_goal是SET_NULL，可以安全删除所有目标
                self.stdout.write('正在删除战略目标（将自动删除关联的进度记录和状态日志）...')
                deleted_count = StrategicGoal.objects.all().delete()[0]
                self.stdout.write(self.style.SUCCESS(f'  ✓ 已删除 {deleted_count} 条战略目标'))
                
            self.stdout.write('')
            self.stdout.write(self.style.SUCCESS('=' * 60))
            self.stdout.write(self.style.SUCCESS('所有数据已成功删除！'))
            self.stdout.write(self.style.SUCCESS('=' * 60))
            
        except Exception as e:
            self.stdout.write(self.style.ERROR(f'删除失败：{str(e)}'))
            import traceback
            self.stdout.write(self.style.ERROR(traceback.format_exc()))
            raise

