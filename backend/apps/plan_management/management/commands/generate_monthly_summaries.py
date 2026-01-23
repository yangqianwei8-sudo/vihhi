"""
月报生成定时任务

执行时间：每月1日上午9点

使用方法：
    python manage.py generate_monthly_summaries
    
建议配置为定时任务（crontab）：
    # 每月1日上午9点执行
    0 9 1 * * cd /path/to/project && /path/to/venv/bin/python manage.py generate_monthly_summaries
"""
from django.core.management.base import BaseCommand
from django.utils import timezone
from django.contrib.auth import get_user_model
from datetime import date, datetime, timedelta
import logging

from backend.apps.plan_management.services.work_summary_service import (
    generate_monthly_summary,
    send_summary_to_user_and_supervisor
)

User = get_user_model()
logger = logging.getLogger(__name__)


class Command(BaseCommand):
    help = '生成月报并发送给员工及其上级'

    def add_arguments(self, parser):
        parser.add_argument(
            '--dry-run',
            action='store_true',
            help='试运行模式：不实际生成，只显示将要生成的内容',
        )

    def handle(self, *args, **options):
        dry_run = options.get('dry_run', False)
        
        self.stdout.write(f'开始生成月报（时间：{timezone.now()}）...')
        
        if dry_run:
            self.stdout.write(self.style.WARNING('【DRY RUN 模式】仅显示，不生成'))
        
        try:
            # 计算上月日期范围
            now = timezone.now()
            today = now.date()
            
            # 上月第一天和最后一天
            if today.month == 1:
                last_month_start = date(today.year - 1, 12, 1)
                last_month_end = date(today.year - 1, 12, 31)
            else:
                last_month_start = date(today.year, today.month - 1, 1)
                # 计算上月最后一天
                if today.month == 2:
                    last_month_end = date(today.year, 1, 31)
                else:
                    last_month_end = (last_month_start + timedelta(days=32)).replace(day=1) - timedelta(days=1)
            
            self.stdout.write(f'上月日期范围：{last_month_start} ~ {last_month_end}')
            
            # 获取所有活跃员工
            users = User.objects.filter(is_active=True)
            
            self.stdout.write(f'找到 {users.count()} 个活跃用户')
            
            success_count = 0
            fail_count = 0
            
            for user in users:
                if dry_run:
                    self.stdout.write(f'  [DRY RUN] 将为用户 {user.username} 生成月报')
                    success_count += 1
                else:
                    try:
                        summary = generate_monthly_summary(user, last_month_start, last_month_end)
                        if summary:
                            # 发送给员工和上级
                            send_summary_to_user_and_supervisor(summary)
                            success_count += 1
                            self.stdout.write(self.style.SUCCESS(f'  ✓ {user.username}: 月报已生成并发送'))
                        else:
                            fail_count += 1
                            self.stdout.write(self.style.WARNING(f'  - {user.username}: 无数据，跳过'))
                    except Exception as e:
                        logger.error(f"为用户 {user.username} 生成月报失败: {str(e)}", exc_info=True)
                        fail_count += 1
                        self.stdout.write(self.style.ERROR(f'  ✗ {user.username}: {str(e)}'))
            
            self.stdout.write('')
            self.stdout.write(self.style.SUCCESS(
                f'生成完成：总计={users.count()}, 成功={success_count}, 失败={fail_count}'
            ))
            
            if dry_run:
                self.stdout.write(self.style.WARNING('\n这是试运行模式，未实际生成月报'))
            
        except Exception as e:
            logger.error(f"生成月报失败: {str(e)}", exc_info=True)
            self.stdout.write(self.style.ERROR(f'生成失败：{str(e)}'))
