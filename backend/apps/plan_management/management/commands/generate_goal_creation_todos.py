"""
目标创建待办生成定时任务

执行时间：每个自然季度起始月1日9点（1月、4月、7月、10月）

使用方法：
    python manage.py generate_goal_creation_todos
    
建议配置为定时任务（crontab）：
    # 每个自然季度起始月1日9点执行
    0 9 1 1,4,7,10 * cd /path/to/project && /path/to/venv/bin/python manage.py generate_goal_creation_todos
"""
from django.core.management.base import BaseCommand
from django.utils import timezone
from datetime import datetime
import logging

from backend.apps.plan_management.services.todo_generator import generate_goal_creation_todo

logger = logging.getLogger(__name__)


class Command(BaseCommand):
    help = '生成目标创建待办事项（给总经理）'

    def add_arguments(self, parser):
        parser.add_argument(
            '--dry-run',
            action='store_true',
            help='试运行模式：不实际创建，只显示将要创建的内容',
        )

    def handle(self, *args, **options):
        dry_run = options.get('dry_run', False)
        
        self.stdout.write(f'开始生成目标创建待办（时间：{timezone.now()}）...')
        
        if dry_run:
            self.stdout.write(self.style.WARNING('【DRY RUN 模式】仅显示，不创建'))
        
        try:
            if not dry_run:
                todos = generate_goal_creation_todo()
                self.stdout.write(self.style.SUCCESS(f'成功生成 {len(todos)} 个目标创建待办'))
            else:
                self.stdout.write(self.style.WARNING('试运行模式：将生成目标创建待办给所有总经理'))
            
        except Exception as e:
            logger.error(f"生成目标创建待办失败: {str(e)}", exc_info=True)
            self.stdout.write(self.style.ERROR(f'生成失败：{str(e)}'))
