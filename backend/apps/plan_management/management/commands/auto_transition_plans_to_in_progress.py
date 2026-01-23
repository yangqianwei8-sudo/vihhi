"""
计划自动变更为执行中定时任务

执行时间：每天上午9点

使用方法：
    python manage.py auto_transition_plans_to_in_progress
    
建议配置为定时任务（crontab）：
    # 每天上午9点执行
    0 9 * * * cd /path/to/project && /path/to/venv/bin/python manage.py auto_transition_plans_to_in_progress
"""
from django.core.management.base import BaseCommand
from django.utils import timezone
from datetime import datetime, timedelta
import logging

from backend.apps.plan_management.models import Plan

logger = logging.getLogger(__name__)


class Command(BaseCommand):
    help = '自动将计划状态从已确认变更为执行中（当计划开始时间到达时）'

    def add_arguments(self, parser):
        parser.add_argument(
            '--dry-run',
            action='store_true',
            help='试运行模式：不实际更新，只显示将要更新的计划',
        )

    def handle(self, *args, **options):
        dry_run = options.get('dry_run', False)
        
        self.stdout.write(f'开始检查计划自动状态流转（时间：{timezone.now()}）...')
        
        if dry_run:
            self.stdout.write(self.style.WARNING('【DRY RUN 模式】仅检查，不更新'))
        
        try:
            # 查找所有状态为 accepted 的计划
            accepted_plans = Plan.objects.filter(status='accepted')
            
            self.stdout.write(f'找到 {accepted_plans.count()} 个已确认的计划')
            
            now = timezone.now()
            today_start = now.replace(hour=0, minute=0, second=0, microsecond=0)
            
            updated_count = 0
            
            for plan in accepted_plans:
                # 检查计划的 start_time 是否已到达（当天或之前）
                if plan.start_time and plan.start_time <= today_start:
                    if dry_run:
                        self.stdout.write(
                            self.style.WARNING(
                                f'  [DRY RUN] 计划 {plan.plan_number} - {plan.name} '
                                f'(开始时间: {plan.start_time.strftime("%Y-%m-%d %H:%M")}) 将变更为执行中'
                            )
                        )
                        updated_count += 1
                    else:
                        try:
                            # 自动变更为执行中
                            plan.transition_to('in_progress', user=None)
                            self.stdout.write(
                                self.style.SUCCESS(
                                    f'  ✓ 计划 {plan.plan_number} - {plan.name} 已自动变更为执行中'
                                )
                            )
                            updated_count += 1
                        except Exception as e:
                            logger.error(f"计划 {plan.id} 状态变更失败: {str(e)}", exc_info=True)
                            self.stdout.write(
                                self.style.ERROR(f'  ✗ 计划 {plan.plan_number} - {plan.name}: {str(e)}')
                            )
            
            self.stdout.write('')
            self.stdout.write(self.style.SUCCESS(f'检查完成：总计={accepted_plans.count()}, 更新={updated_count}'))
            
            if dry_run:
                self.stdout.write(self.style.WARNING('\n这是试运行模式，未实际更新数据'))
            
        except Exception as e:
            logger.error(f"自动状态流转失败: {str(e)}", exc_info=True)
            self.stdout.write(self.style.ERROR(f'检查失败：{str(e)}'))
