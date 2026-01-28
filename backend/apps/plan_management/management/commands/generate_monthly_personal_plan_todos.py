"""
为所有员工生成月度个人计划创建待办事项

使用方法：
    python manage.py generate_monthly_personal_plan_todos --year 2026 --month 2 --deadline "2026-01-31 23:59:59"
    
参数说明：
    --year: 目标月份（计划所属月份）
    --month: 目标月份（计划所属月份）
    --deadline: 截止日期时间（格式：YYYY-MM-DD HH:MM:SS）
"""
from django.core.management.base import BaseCommand
from django.utils import timezone
from django.contrib.auth import get_user_model
from datetime import datetime
import logging

from backend.apps.plan_management.services.todo_service import create_todo_task
from backend.apps.plan_management.notifications import safe_approval_notification

User = get_user_model()
logger = logging.getLogger(__name__)


class Command(BaseCommand):
    help = '为所有员工生成月度个人计划创建待办事项'

    def add_arguments(self, parser):
        parser.add_argument(
            '--year',
            type=int,
            help='目标月份（计划所属年份，如：2026）',
        )
        parser.add_argument(
            '--month',
            type=int,
            help='目标月份（计划所属月份，如：2）',
        )
        parser.add_argument(
            '--deadline',
            type=str,
            help='截止日期时间（格式：YYYY-MM-DD HH:MM:SS，如：2026-01-31 23:59:59）',
        )
        parser.add_argument(
            '--dry-run',
            action='store_true',
            help='试运行模式：不实际创建，只显示将要创建的内容',
        )

    def handle(self, *args, **options):
        dry_run = options.get('dry_run', False)
        year = options.get('year')
        month = options.get('month')
        deadline_str = options.get('deadline')
        
        # 解析截止时间
        if deadline_str:
            try:
                deadline = datetime.strptime(deadline_str, '%Y-%m-%d %H:%M:%S')
                deadline = timezone.make_aware(deadline)
            except ValueError:
                self.stdout.write(self.style.ERROR(f'截止时间格式错误，请使用格式：YYYY-MM-DD HH:MM:SS'))
                return
        else:
            # 如果没有指定截止时间，使用2026年1月31日23:59:59
            deadline = timezone.make_aware(datetime(2026, 1, 31, 23, 59, 59))
        
        # 如果没有指定年份和月份，使用2026年2月
        if not year:
            year = 2026
        if not month:
            month = 2
        
        self.stdout.write(f'开始生成{year}年{month}月月度个人计划创建待办（时间：{timezone.now()}）...')
        self.stdout.write(f'截止时间：{deadline.strftime("%Y-%m-%d %H:%M:%S")}')
        
        if dry_run:
            self.stdout.write(self.style.WARNING('【DRY RUN 模式】仅显示，不创建'))
        
        try:
            # 获取所有活跃用户
            users = User.objects.filter(is_active=True)
            user_count = users.count()
            
            self.stdout.write(f'找到 {user_count} 个活跃用户')
            
            if dry_run:
                self.stdout.write(self.style.WARNING(f'试运行模式：将为 {user_count} 个用户创建待办事项'))
                for user in users[:5]:  # 只显示前5个作为示例
                    self.stdout.write(f'  - {user.username} ({user.get_full_name() or user.username})')
                if user_count > 5:
                    self.stdout.write(f'  ... 还有 {user_count - 5} 个用户')
                return
            
            # 创建待办事项和通知
            success_count = 0
            error_count = 0
            
            for user in users:
                try:
                    # 创建待办事项
                    todo = create_todo_task(
                        task_type='plan_creation',
                        user=user,
                        title=f'【计划创建】请创建{year}年{month}月月度个人计划',
                        description=f'请在{deadline.strftime("%Y年%m月%d日 %H:%M:%S")}前完成{year}年{month}月月度个人计划的创建。',
                        deadline=deadline,
                        auto_generated=True
                    )
                    
                    # 发送系统通知
                    safe_approval_notification(
                        user=user,
                        title=f'【待办提醒】{year}年{month}月月度个人计划创建待办事项',
                        content=f'系统已为您生成{year}年{month}月月度个人计划创建待办事项，请在{deadline.strftime("%Y年%m月%d日 %H:%M:%S")}前完成。',
                        object_type='todo',
                        object_id=str(todo.id),
                        event='plan_creation',
                        is_read=False
                    )
                    
                    success_count += 1
                    
                except Exception as e:
                    logger.error(f"为用户 {user.username} 创建月度个人计划创建待办失败: {str(e)}", exc_info=True)
                    error_count += 1
                    self.stdout.write(self.style.ERROR(f'  ❌ {user.username}: {str(e)}'))
            
            self.stdout.write(self.style.SUCCESS(f'成功生成 {success_count} 个待办事项和通知'))
            if error_count > 0:
                self.stdout.write(self.style.WARNING(f'失败 {error_count} 个'))
            
        except Exception as e:
            logger.error(f"生成月度个人计划创建待办失败: {str(e)}", exc_info=True)
            self.stdout.write(self.style.ERROR(f'生成失败：{str(e)}'))
