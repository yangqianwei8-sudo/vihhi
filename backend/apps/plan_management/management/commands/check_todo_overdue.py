"""
待办事项逾期检查定时任务

执行时间：每天凌晨1点

使用方法：
    python manage.py check_todo_overdue
    
建议配置为定时任务（crontab）：
    # 每天凌晨1点执行
    0 1 * * * cd /path/to/project && /path/to/venv/bin/python manage.py check_todo_overdue
"""
from django.core.management.base import BaseCommand
from django.utils import timezone
import logging

from backend.apps.plan_management.models import TodoTask
from backend.apps.plan_management.services.todo_service import check_todo_overdue
from backend.apps.plan_management.notifications import safe_approval_notification

logger = logging.getLogger(__name__)


class Command(BaseCommand):
    help = '检查并标记逾期待办事项，发送逾期通知'

    def add_arguments(self, parser):
        parser.add_argument(
            '--dry-run',
            action='store_true',
            help='试运行模式：不实际更新，只显示将要更新的待办',
        )

    def handle(self, *args, **options):
        dry_run = options.get('dry_run', False)
        
        self.stdout.write(f'开始检查待办事项逾期状态（时间：{timezone.now()}）...')
        
        if dry_run:
            self.stdout.write(self.style.WARNING('【DRY RUN 模式】仅检查，不更新'))
        
        try:
            # 查找所有状态为 pending 的待办
            pending_todos = TodoTask.objects.filter(status='pending')
            
            self.stdout.write(f'找到 {pending_todos.count()} 个待处理的待办事项')
            
            updated_count = 0
            notified_count = 0
            
            for todo in pending_todos:
                old_status = todo.status
                old_is_overdue = todo.is_overdue
                
                # 检查是否逾期
                if todo.check_overdue():
                    if dry_run:
                        self.stdout.write(
                            self.style.WARNING(
                                f'  [DRY RUN] 待办 {todo.title} (负责人: {todo.user.username}, '
                                f'截止时间: {todo.deadline.strftime("%Y-%m-%d %H:%M")}, '
                                f'逾期{todo.overdue_days}天) 将标记为逾期'
                            )
                        )
                        updated_count += 1
                    else:
                        todo.save()
                        updated_count += 1
                        
                        # 发送逾期通知
                        try:
                            safe_approval_notification(
                                user=todo.user,
                                title=f'【逾期提醒】待办事项已逾期：{todo.title}',
                                content=f'您的待办事项《{todo.title}》已逾期 {todo.overdue_days} 天，请尽快处理。\n截止时间：{todo.deadline.strftime("%Y年%m月%d日 %H:%M")}',
                                object_type='todo',
                                object_id=str(todo.id),
                                event='todo_overdue',
                                is_read=False
                            )
                            notified_count += 1
                            self.stdout.write(
                                self.style.SUCCESS(
                                    f'  ✓ 待办 {todo.title}: 已标记为逾期并发送通知'
                                )
                            )
                        except Exception as e:
                            logger.error(f"发送逾期通知失败（待办 {todo.id}）: {str(e)}", exc_info=True)
                            self.stdout.write(
                                self.style.ERROR(f'  ✗ 待办 {todo.title}: 标记逾期成功，但通知发送失败')
                            )
            
            self.stdout.write('')
            self.stdout.write(self.style.SUCCESS(
                f'检查完成：总计={pending_todos.count()}, 标记逾期={updated_count}, 发送通知={notified_count}'
            ))
            
            if dry_run:
                self.stdout.write(self.style.WARNING('\n这是试运行模式，未实际更新数据'))
            
        except Exception as e:
            logger.error(f"检查待办逾期失败: {str(e)}", exc_info=True)
            self.stdout.write(self.style.ERROR(f'检查失败：{str(e)}'))
