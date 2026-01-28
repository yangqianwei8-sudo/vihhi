"""
待办完成巡检（方案B）

目的：
- 对已完成的 TodoTask 做业务证据核验
- 自动把可核验的标记为 verified
- 对无法核验且缺少证据/证据不足的标记为 suspected

使用：
  python manage.py verify_todo_completions
  python manage.py verify_todo_completions --dry-run
  python manage.py verify_todo_completions --only-pending
"""
from django.core.management.base import BaseCommand
from django.utils import timezone
import logging

from backend.apps.plan_management.models import TodoTask
from backend.apps.plan_management.services.todo_service import check_todo_business_evidence

logger = logging.getLogger(__name__)


class Command(BaseCommand):
    help = '巡检已完成的待办事项，核验业务证据并标记疑似虚假完成'

    def add_arguments(self, parser):
        parser.add_argument(
            '--dry-run',
            action='store_true',
            help='试运行：仅输出，不更新数据库',
        )
        parser.add_argument(
            '--only-pending',
            action='store_true',
            help='仅巡检核验状态为 pending 的已完成待办',
        )
        parser.add_argument(
            '--limit',
            type=int,
            default=500,
            help='最多处理条数（默认500）',
        )

    def handle(self, *args, **options):
        dry_run = options.get('dry_run', False)
        only_pending = options.get('only_pending', False)
        limit = options.get('limit', 500)

        now = timezone.now()
        self.stdout.write(f'开始巡检待办完成核验（时间：{now}）...')
        if dry_run:
            self.stdout.write(self.style.WARNING('【DRY RUN 模式】仅检查，不更新'))

        qs = TodoTask.objects.filter(status='completed')
        if only_pending:
            qs = qs.filter(verification_status='pending')
        else:
            qs = qs.filter(verification_status__in=['pending', 'suspected'])

        qs = qs.select_related('user', 'completed_by').order_by('-completed_at')[: max(1, limit)]

        total = qs.count()
        verified = 0
        suspected = 0
        skipped = 0

        for todo in qs:
            try:
                ok, msg = check_todo_business_evidence(todo)
                evidence_text = (getattr(todo, 'completion_evidence', '') or '').strip()

                if ok:
                    if dry_run:
                        self.stdout.write(self.style.SUCCESS(f'[DRY RUN] ✓ 核验通过：{todo.id} {todo.title}'))
                    else:
                        todo.verification_status = 'verified'
                        todo.verification_checked_at = now
                        todo.verification_reason = ''
                        todo.save(update_fields=['verification_status', 'verification_checked_at', 'verification_reason', 'updated_at'])
                    verified += 1
                    continue

                # 不通过：缺少证据或证据不足 → 标记疑似
                reason = msg or '未通过业务证据核验'
                if not evidence_text:
                    reason = f'{reason}；且未提交完成证据'

                if dry_run:
                    self.stdout.write(self.style.WARNING(f'[DRY RUN] ⚠ 疑似虚假完成：{todo.id} {todo.title}（{reason}）'))
                else:
                    todo.verification_status = 'suspected'
                    todo.verification_checked_at = now
                    todo.verification_reason = reason[:1000]
                    todo.save(update_fields=['verification_status', 'verification_checked_at', 'verification_reason', 'updated_at'])
                suspected += 1

            except Exception as e:
                skipped += 1
                logger.error(f'巡检失败 todo_id={todo.id}: {e}', exc_info=True)
                self.stdout.write(self.style.ERROR(f'✗ 巡检失败：{todo.id} {todo.title}（{e}）'))

        self.stdout.write('')
        self.stdout.write(self.style.SUCCESS(
            f'巡检完成：处理={total}，核验通过={verified}，疑似={suspected}，失败/跳过={skipped}'
        ))

