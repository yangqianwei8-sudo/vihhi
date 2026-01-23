"""
计划进度更新待办生成定时任务

执行时间：每天下午5点

使用方法：
    python manage.py generate_plan_progress_update_todos
    
建议配置为定时任务（crontab）：
    # 每天下午5点执行
    0 17 * * * cd /path/to/project && /path/to/venv/bin/python manage.py generate_plan_progress_update_todos
"""
from django.core.management.base import BaseCommand
from django.utils import timezone
from datetime import datetime, timedelta
import logging

from backend.apps.plan_management.models import Plan
from backend.apps.plan_management.services.todo_generator import generate_plan_progress_update_todo

logger = logging.getLogger(__name__)


class Command(BaseCommand):
    help = '生成计划进度更新待办事项'

    def add_arguments(self, parser):
        parser.add_argument(
            '--dry-run',
            action='store_true',
            help='试运行模式：不实际创建，只显示将要创建的内容',
        )

    def handle(self, *args, **options):
        dry_run = options.get('dry_run', False)
        
        self.stdout.write(f'开始生成计划进度更新待办（时间：{timezone.now()}）...')
        
        if dry_run:
            self.stdout.write(self.style.WARNING('【DRY RUN 模式】仅显示，不创建'))
        
        try:
            # 查找所有执行中的计划
            in_progress_plans = Plan.objects.filter(
                status='in_progress'
            ).select_related('responsible_person')
            
            self.stdout.write(f'找到 {in_progress_plans.count()} 个执行中的计划')
            
            # 计算截止时间：当天下午6点
            now = timezone.now()
            deadline = now.replace(hour=18, minute=0, second=0, microsecond=0)
            # 如果已经过了6点，使用明天下午6点
            if now.hour >= 18:
                deadline = deadline + timedelta(days=1)
            
            success_count = 0
            fail_count = 0
            
            for plan in in_progress_plans:
                if not plan.responsible_person:
                    continue
                
                if dry_run:
                    self.stdout.write(f'  [DRY RUN] 将为计划 {plan.name} (负责人: {plan.responsible_person.username}) 生成进度更新待办')
                    success_count += 1
                else:
                    try:
                        todo = generate_plan_progress_update_todo(plan, deadline)
                        if todo:
                            success_count += 1
                            self.stdout.write(self.style.SUCCESS(f'  ✓ 计划 {plan.name}: 已生成待办'))
                        else:
                            fail_count += 1
                    except Exception as e:
                        logger.error(f"为计划 {plan.id} 生成进度更新待办失败: {str(e)}", exc_info=True)
                        fail_count += 1
                        self.stdout.write(self.style.ERROR(f'  ✗ 计划 {plan.name}: {str(e)}'))
            
            self.stdout.write('')
            self.stdout.write(self.style.SUCCESS(
                f'生成完成：总计={in_progress_plans.count()}, 成功={success_count}, 失败={fail_count}'
            ))
            
        except Exception as e:
            logger.error(f"生成计划进度更新待办失败: {str(e)}", exc_info=True)
            self.stdout.write(self.style.ERROR(f'生成失败：{str(e)}'))
