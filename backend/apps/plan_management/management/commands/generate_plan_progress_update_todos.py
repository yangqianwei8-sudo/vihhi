"""
计划进度更新待办生成定时任务

执行时间：
    - 日计划：每天下午5点
    - 周计划：每周五下午5点
    - 月计划：每月28日下午5点

使用方法：
    python manage.py generate_plan_progress_update_todos --plan-type daily|weekly|monthly
    
建议配置为定时任务（crontab）：
    # 日计划：每天下午5点执行
    0 17 * * * cd /path/to/project && /path/to/venv/bin/python manage.py generate_plan_progress_update_todos --plan-type daily
    
    # 周计划：每周五下午5点执行
    0 17 * * 5 cd /path/to/project && /path/to/venv/bin/python manage.py generate_plan_progress_update_todos --plan-type weekly
    
    # 月计划：每月28日下午5点执行
    0 17 28 * * cd /path/to/project && /path/to/venv/bin/python manage.py generate_plan_progress_update_todos --plan-type monthly
"""
from django.core.management.base import BaseCommand
from django.utils import timezone
from datetime import datetime, timedelta
import logging

from backend.apps.plan_management.models import Plan
from backend.apps.plan_management.services.todo_generator import generate_plan_progress_update_todo

logger = logging.getLogger(__name__)


class Command(BaseCommand):
    help = '生成计划进度更新待办事项（支持按计划类型：daily/weekly/monthly）'

    def add_arguments(self, parser):
        parser.add_argument(
            '--plan-type',
            type=str,
            choices=['daily', 'weekly', 'monthly'],
            help='计划类型：daily=日计划, weekly=周计划, monthly=月计划',
        )
        parser.add_argument(
            '--dry-run',
            action='store_true',
            help='试运行模式：不实际创建，只显示将要创建的内容',
        )

    def handle(self, *args, **options):
        dry_run = options.get('dry_run', False)
        plan_type = options.get('plan_type')
        
        self.stdout.write(f'开始生成计划进度更新待办（时间：{timezone.now()}）...')
        
        if plan_type:
            self.stdout.write(f'计划类型：{plan_type}')
        else:
            self.stdout.write(self.style.WARNING('未指定计划类型，将处理所有类型的计划'))
        
        if dry_run:
            self.stdout.write(self.style.WARNING('【DRY RUN 模式】仅显示，不创建'))
        
        try:
            # 查找执行中的计划
            query = Plan.objects.filter(status='in_progress').select_related('responsible_person')
            
            # 如果指定了计划类型，只处理该类型的计划
            if plan_type:
                query = query.filter(plan_period=plan_type)
            
            in_progress_plans = query
            
            plan_type_display = {
                'daily': '日计划',
                'weekly': '周计划',
                'monthly': '月计划',
            }.get(plan_type, '计划')
            
            self.stdout.write(f'找到 {in_progress_plans.count()} 个执行中的{plan_type_display}')
            
            success_count = 0
            fail_count = 0
            
            for plan in in_progress_plans:
                if not plan.responsible_person:
                    continue
                
                if dry_run:
                    self.stdout.write(f'  [DRY RUN] 将为{plan_type_display} {plan.name} (负责人: {plan.responsible_person.username}) 生成进度更新待办')
                    success_count += 1
                else:
                    try:
                        # deadline=None 时，函数会根据计划类型自动计算截止时间
                        todo = generate_plan_progress_update_todo(plan, deadline=None)
                        if todo:
                            success_count += 1
                            self.stdout.write(self.style.SUCCESS(f'  ✓ {plan_type_display} {plan.name}: 已生成待办（截止时间：{todo.deadline.strftime("%Y-%m-%d %H:%M")}）'))
                        else:
                            fail_count += 1
                    except Exception as e:
                        logger.error(f"为计划 {plan.id} 生成进度更新待办失败: {str(e)}", exc_info=True)
                        fail_count += 1
                        self.stdout.write(self.style.ERROR(f'  ✗ {plan_type_display} {plan.name}: {str(e)}'))
            
            self.stdout.write('')
            self.stdout.write(self.style.SUCCESS(
                f'生成完成：总计={in_progress_plans.count()}, 成功={success_count}, 失败={fail_count}'
            ))
            
        except Exception as e:
            logger.error(f"生成计划进度更新待办失败: {str(e)}", exc_info=True)
            self.stdout.write(self.style.ERROR(f'生成失败：{str(e)}'))
