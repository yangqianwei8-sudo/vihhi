"""
P2-4: 每日待办提醒定时任务

每天 9:00 执行，为每个用户生成待办汇总通知

使用方式：
1. Celery beat（推荐）：
   - 在 celery.py 中添加：
     app.conf.beat_schedule = {
         'daily-todo-reminder': {
             'task': 'plan_management.tasks.daily_todo_reminder',
             'schedule': crontab(hour=9, minute=0),
         },
     }

2. Django-crontab：
   - 在 settings.py 中添加：
     CRONJOBS = [
         ('0 9 * * *', 'plan_management.management.commands.daily_todo_reminder'),
     ]
   - 运行：python manage.py crontab add

3. 手动执行（测试）：
   - python manage.py daily_todo_reminder
"""
from django.core.management.base import BaseCommand
from django.contrib.auth.models import User
from django.utils import timezone
from backend.apps.plan_management.services.todo_service import get_user_todos, get_user_todo_summary
from backend.apps.plan_management.notifications import safe_approval_notification
import logging

logger = logging.getLogger(__name__)


class Command(BaseCommand):
    help = 'P2-4: 每日待办提醒 - 每天 9:00 为每个用户生成待办汇总通知'

    def add_arguments(self, parser):
        parser.add_argument(
            '--dry-run',
            action='store_true',
            help='仅显示待办统计，不发送通知',
        )

    def handle(self, *args, **options):
        dry_run = options.get('dry_run', False)
        
        self.stdout.write(self.style.SUCCESS('=' * 60))
        self.stdout.write(self.style.SUCCESS('P2-4: 每日待办提醒任务'))
        self.stdout.write(self.style.SUCCESS('=' * 60))
        
        if dry_run:
            self.stdout.write(self.style.WARNING('【DRY RUN 模式】仅统计，不发送通知'))
        
        # 获取所有活跃用户
        users = User.objects.filter(is_active=True)
        total_users = users.count()
        
        self.stdout.write(f'\n处理用户数：{total_users}')
        
        success_count = 0
        error_count = 0
        
        for user in users:
            try:
                # 获取用户待办汇总
                summary = get_user_todo_summary(user)
                
                # 如果没有待办，跳过
                if summary['total'] == 0:
                    continue
                
                # 构建通知内容
                title = "[每日提醒] 您有新的待办事项"
                
                content_parts = []
                
                # 今日待办
                if summary['pending_accept'] > 0 or summary['pending_execute'] > 0 or summary['today_plans'] > 0:
                    content_parts.append("📋 今日待办：")
                    if summary['pending_accept'] > 0:
                        content_parts.append(f"  • 待接收：{summary['pending_accept']} 项（目标/计划）")
                    if summary['pending_execute'] > 0:
                        content_parts.append(f"  • 待执行：{summary['pending_execute']} 项（目标/计划）")
                    if summary['today_plans'] > 0:
                        content_parts.append(f"  • 今日需执行计划：{summary['today_plans']} 项")
                
                # 风险提示
                if summary['risk_items'] > 0:
                    content_parts.append("")
                    content_parts.append("⚠️ 风险提示：")
                    content_parts.append(f"  • 逾期/高风险项：{summary['risk_items']} 项，请尽快处理")
                
                content = "\n".join(content_parts)
                
                if not dry_run:
                    # 发送通知
                    safe_approval_notification(
                        user=user,
                        title=title,
                        content=content,
                        object_type='todo',
                        object_id='daily_summary',
                        event='daily_todo_reminder',
                        is_read=False
                    )
                    
                    self.stdout.write(self.style.SUCCESS(f'  ✓ {user.username}: {summary["total"]} 项待办'))
                else:
                    self.stdout.write(self.style.WARNING(f'  [DRY RUN] {user.username}: {summary["total"]} 项待办'))
                
                success_count += 1
                
            except Exception as e:
                logger.error(f"处理用户 {user.username} 的待办提醒失败：{str(e)}", exc_info=True)
                self.stdout.write(self.style.ERROR(f'  ✗ {user.username}: {str(e)}'))
                error_count += 1
        
        # 汇总
        self.stdout.write(self.style.SUCCESS('\n' + '=' * 60))
        self.stdout.write(self.style.SUCCESS('任务完成'))
        self.stdout.write(self.style.SUCCESS('=' * 60))
        self.stdout.write(f'成功：{success_count} 个用户')
        if error_count > 0:
            self.stdout.write(self.style.ERROR(f'失败：{error_count} 个用户'))
        
        if dry_run:
            self.stdout.write(self.style.WARNING('\n提示：使用 --dry-run 仅统计，实际发送请去掉该参数'))

