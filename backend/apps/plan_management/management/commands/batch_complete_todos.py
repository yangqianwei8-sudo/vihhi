"""
批量自动完成待办事项

目的：
- 全面检查数据库中所有待处理的待办事项
- 根据业务证据自动完成已完成的待办事项
- 修复历史遗留问题：员工已完成工作但待办仍挂在那里

使用：
  python manage.py batch_complete_todos
  python manage.py batch_complete_todos --dry-run
  python manage.py batch_complete_todos --limit 1000
  python manage.py batch_complete_todos --task-type plan_decomposition_daily
"""
from django.core.management.base import BaseCommand
from django.utils import timezone
from django.db.models import Q
import logging
from datetime import datetime, timedelta

from backend.apps.plan_management.models import TodoTask, Plan, StrategicGoal, PlanProgressRecord, GoalProgressRecord
from backend.apps.plan_management.services.todo_service import check_todo_business_evidence, mark_todo_completed, extract_date_from_text

logger = logging.getLogger(__name__)


class Command(BaseCommand):
    help = '批量检查并自动完成已完成的待办事项，修复历史遗留问题'

    def add_arguments(self, parser):
        parser.add_argument(
            '--dry-run',
            action='store_true',
            help='试运行：仅输出，不更新数据库',
        )
        parser.add_argument(
            '--limit',
            type=int,
            default=None,
            help='最多处理条数（默认不限制）',
        )
        parser.add_argument(
            '--task-type',
            type=str,
            default=None,
            help='仅处理指定类型的待办（如：plan_decomposition_daily）',
        )
        parser.add_argument(
            '--user-id',
            type=int,
            default=None,
            help='仅处理指定用户的待办',
        )

    def handle(self, *args, **options):
        dry_run = options.get('dry_run', False)
        limit = options.get('limit')
        task_type = options.get('task_type')
        user_id = options.get('user_id')

        now = timezone.now()
        self.stdout.write(f'开始批量检查待办事项（时间：{now}）...')
        if dry_run:
            self.stdout.write(self.style.WARNING('【DRY RUN 模式】仅检查，不更新'))

        # 查询待处理的待办事项
        qs = TodoTask.objects.filter(status__in=['pending', 'overdue'])
        
        if task_type:
            qs = qs.filter(task_type=task_type)
        
        if user_id:
            qs = qs.filter(user_id=user_id)
        
        qs = qs.select_related('user').order_by('created_at')
        
        if limit:
            qs = qs[:limit]
        
        total = qs.count()
        self.stdout.write(f'找到 {total} 个待处理的待办事项')
        
        completed_count = 0
        skipped_count = 0
        error_count = 0
        
        stats_by_type = {}
        
        for todo in qs:
            try:
                # 检查业务证据
                evidence_ok, evidence_msg = check_todo_business_evidence(todo)
                
                if evidence_ok:
                    # 业务证据检查通过，自动完成待办
                    if dry_run:
                        self.stdout.write(
                            self.style.SUCCESS(
                                f'[DRY RUN] ✓ 将完成：#{todo.id} [{todo.get_task_type_display()}] '
                                f'{todo.title[:50]}... (用户: {todo.user.username})'
                            )
                        )
                    else:
                        mark_todo_completed(todo, user=todo.user, via='auto')
                        self.stdout.write(
                            self.style.SUCCESS(
                                f'✓ 已完成：#{todo.id} [{todo.get_task_type_display()}] '
                                f'{todo.title[:50]}... (用户: {todo.user.username})'
                            )
                        )
                    
                    completed_count += 1
                    task_type_key = todo.task_type
                    stats_by_type[task_type_key] = stats_by_type.get(task_type_key, 0) + 1
                else:
                    # 业务证据检查未通过，跳过
                    skipped_count += 1
                    if completed_count + skipped_count <= 10:  # 只显示前10个跳过的
                        self.stdout.write(
                            self.style.WARNING(
                                f'⊘ 跳过：#{todo.id} [{todo.get_task_type_display()}] '
                                f'{todo.title[:50]}... (原因: {evidence_msg})'
                            )
                        )
            except Exception as e:
                error_count += 1
                logger.error(f'处理待办事项失败 todo_id={todo.id}: {e}', exc_info=True)
                self.stdout.write(
                    self.style.ERROR(
                        f'✗ 处理失败：#{todo.id} {todo.title[:50]}... (错误: {str(e)[:100]})'
                    )
                )
        
        # 输出统计信息
        self.stdout.write('')
        self.stdout.write(self.style.SUCCESS('=' * 60))
        self.stdout.write(self.style.SUCCESS('处理完成统计'))
        self.stdout.write(self.style.SUCCESS('=' * 60))
        self.stdout.write(f'总计待办事项：{total}')
        self.stdout.write(self.style.SUCCESS(f'自动完成：{completed_count}'))
        self.stdout.write(self.style.WARNING(f'跳过（未完成）：{skipped_count}'))
        self.stdout.write(self.style.ERROR(f'处理失败：{error_count}'))
        
        if stats_by_type:
            self.stdout.write('')
            self.stdout.write('按类型统计（已完成的）：')
            for task_type_key, count in sorted(stats_by_type.items(), key=lambda x: x[1], reverse=True):
                task_type_display = dict(TodoTask.TASK_TYPE_CHOICES).get(task_type_key, task_type_key)
                self.stdout.write(f'  - {task_type_display}: {count}')
        
        if dry_run:
            self.stdout.write('')
            self.stdout.write(self.style.WARNING('【DRY RUN 模式】未实际更新数据库'))
            self.stdout.write('运行时不加 --dry-run 参数来实际更新数据库')
