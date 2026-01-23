"""
日计划分解待办生成定时任务

执行时间：每天下午5点

使用方法：
    python manage.py generate_daily_plan_todos
    
建议配置为定时任务（crontab）：
    # 每天下午5点执行
    0 17 * * * cd /path/to/project && /path/to/venv/bin/python manage.py generate_daily_plan_todos
"""
from django.core.management.base import BaseCommand
from django.utils import timezone
from datetime import datetime, timedelta
import logging

from backend.apps.plan_management.services.todo_generator import generate_plan_decomposition_todo

logger = logging.getLogger(__name__)


class Command(BaseCommand):
    help = '生成日计划分解待办事项（明日计划）'

    def add_arguments(self, parser):
        parser.add_argument(
            '--dry-run',
            action='store_true',
            help='试运行模式：不实际创建，只显示将要创建的内容',
        )

    def handle(self, *args, **options):
        dry_run = options.get('dry_run', False)
        
        self.stdout.write(f'开始生成日计划分解待办（时间：{timezone.now()}）...')
        
        if dry_run:
            self.stdout.write(self.style.WARNING('【DRY RUN 模式】仅显示，不创建'))
        
        try:
            # 计算截止时间：明天上午9点
            now = timezone.now()
            tomorrow = now + timedelta(days=1)
            deadline = tomorrow.replace(hour=9, minute=0, second=0, microsecond=0)
            
            if not dry_run:
                todos = generate_plan_decomposition_todo(plan_type='daily', deadline=deadline)
                self.stdout.write(self.style.SUCCESS(f'成功生成 {len(todos)} 个日计划分解待办'))
            else:
                self.stdout.write(self.style.WARNING(f'试运行模式：将为所有活跃员工生成日计划分解待办（截止时间：{deadline.strftime("%Y-%m-%d %H:%M")}）'))
            
        except Exception as e:
            logger.error(f"生成日计划分解待办失败: {str(e)}", exc_info=True)
            self.stdout.write(self.style.ERROR(f'生成失败：{str(e)}'))
