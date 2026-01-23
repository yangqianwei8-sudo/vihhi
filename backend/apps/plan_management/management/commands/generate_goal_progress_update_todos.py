"""
目标进度更新待办生成定时任务

执行时间：每周一上午10点

使用方法：
    python manage.py generate_goal_progress_update_todos
    
建议配置为定时任务（crontab）：
    # 每周一上午10点执行
    0 10 * * 1 cd /path/to/project && /path/to/venv/bin/python manage.py generate_goal_progress_update_todos
"""
from django.core.management.base import BaseCommand
from django.utils import timezone
from datetime import datetime, timedelta
import logging

from backend.apps.plan_management.models import StrategicGoal
from backend.apps.plan_management.services.todo_generator import generate_goal_progress_update_todo

logger = logging.getLogger(__name__)


class Command(BaseCommand):
    help = '生成目标进度更新待办事项'

    def add_arguments(self, parser):
        parser.add_argument(
            '--dry-run',
            action='store_true',
            help='试运行模式：不实际创建，只显示将要创建的内容',
        )

    def handle(self, *args, **options):
        dry_run = options.get('dry_run', False)
        
        self.stdout.write(f'开始生成目标进度更新待办（时间：{timezone.now()}）...')
        
        if dry_run:
            self.stdout.write(self.style.WARNING('【DRY RUN 模式】仅显示，不创建'))
        
        try:
            # 查找所有执行中的个人目标
            in_progress_goals = StrategicGoal.objects.filter(
                status='in_progress',
                level='personal'
            ).select_related('owner', 'responsible_person')
            
            self.stdout.write(f'找到 {in_progress_goals.count()} 个执行中的个人目标')
            
            # 计算截止时间：当天下午5点
            now = timezone.now()
            deadline = now.replace(hour=17, minute=0, second=0, microsecond=0)
            # 如果已经过了5点，使用明天下午5点
            if now.hour >= 17:
                deadline = deadline + timedelta(days=1)
            
            success_count = 0
            fail_count = 0
            
            for goal in in_progress_goals:
                if not goal.owner:
                    continue
                
                if dry_run:
                    self.stdout.write(f'  [DRY RUN] 将为目标 {goal.name} (负责人: {goal.owner.username}) 生成进度更新待办')
                    success_count += 1
                else:
                    try:
                        todo = generate_goal_progress_update_todo(goal, deadline)
                        if todo:
                            success_count += 1
                            self.stdout.write(self.style.SUCCESS(f'  ✓ 目标 {goal.name}: 已生成待办'))
                        else:
                            fail_count += 1
                    except Exception as e:
                        logger.error(f"为目标 {goal.id} 生成进度更新待办失败: {str(e)}", exc_info=True)
                        fail_count += 1
                        self.stdout.write(self.style.ERROR(f'  ✗ 目标 {goal.name}: {str(e)}'))
            
            self.stdout.write('')
            self.stdout.write(self.style.SUCCESS(
                f'生成完成：总计={in_progress_goals.count()}, 成功={success_count}, 失败={fail_count}'
            ))
            
        except Exception as e:
            logger.error(f"生成目标进度更新待办失败: {str(e)}", exc_info=True)
            self.stdout.write(self.style.ERROR(f'生成失败：{str(e)}'))
