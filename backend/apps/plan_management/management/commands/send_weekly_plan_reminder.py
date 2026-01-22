"""
周工作计划提醒管理命令

使用方法：
    python manage.py send_weekly_plan_reminder
    
建议配置为定时任务（crontab）：
    # 每周五9点执行
    0 9 * * 5 cd /path/to/project && /path/to/venv/bin/python manage.py send_weekly_plan_reminder
    
    # 或使用Celery Beat
    @periodic_task(run_every=crontab(hour=9, minute=0, day_of_week=5))
    def send_weekly_plan_reminder_task():
        call_command('send_weekly_plan_reminder')
"""
from django.core.management.base import BaseCommand
from django.utils import timezone
from django.contrib.auth import get_user_model
from django.urls import reverse
import logging
from datetime import datetime, timedelta

from backend.apps.plan_management.notifications import safe_approval_notification

User = get_user_model()
logger = logging.getLogger(__name__)


class Command(BaseCommand):
    help = '发送周工作计划编制提醒给所有员工'

    def add_arguments(self, parser):
        parser.add_argument(
            '--test',
            action='store_true',
            help='测试模式：只发送给前5个用户',
        )
        parser.add_argument(
            '--dry-run',
            action='store_true',
            help='试运行模式：不实际发送，只显示将要发送的内容',
        )

    def handle(self, *args, **options):
        test_mode = options.get('test', False)
        dry_run = options.get('dry_run', False)
        
        self.stdout.write(f'开始发送周工作计划提醒（时间：{timezone.now()}）...')
        
        # 获取所有激活的员工
        users = User.objects.filter(is_active=True)
        
        if test_mode:
            users = users[:5]
            self.stdout.write(self.style.WARNING(f'测试模式：只发送给前{users.count()}个用户'))
        
        if not users.exists():
            self.stdout.write(self.style.ERROR('没有找到激活的用户'))
            return
        
        self.stdout.write(f'找到 {users.count()} 个激活用户')
        
        # 获取当前周和下周信息
        now = timezone.now()
        today = now.date()
        
        # 计算本周五和下周一
        # 获取本周五（如果今天是周五，就是今天；否则是下一个周五）
        days_until_friday = (4 - today.weekday()) % 7
        if days_until_friday == 0 and now.hour < 9:
            # 如果今天是周五但还没到9点，提醒的是本周
            this_friday = today
        elif days_until_friday == 0:
            # 如果今天是周五且已过9点，提醒的是下周
            this_friday = today + timedelta(days=7)
        else:
            this_friday = today + timedelta(days=days_until_friday)
        
        # 计算下周一的日期（下周一是一周的开始）
        next_monday = this_friday + timedelta(days=3)  # 周五+3天=下周一
        next_sunday = next_monday + timedelta(days=6)  # 下周一+6天=下周日
        
        # 格式化日期
        week_str = f"{next_monday.strftime('%Y年%m月%d日')} - {next_sunday.strftime('%m月%d日')}"
        
        # 构建通知内容
        title = f'【周工作计划提醒】请及时编制下周工作计划（{week_str}）'
        
        # 获取计划创建页面的URL
        try:
            plan_create_url = reverse('plan_pages:plan_create')
        except Exception as e:
            logger.warning(f"无法构建计划创建URL: {str(e)}")
            plan_create_url = '/plan/plans/create/'
        
        content = f"""根据工作计划管理制度，请在每周五18:00前完成下周工作计划的编制工作。

本周提醒：请及时编制下周（{week_str}）的工作计划。

⚠️ 重要提示：周计划提交截止时间为每周五18:00，逾期提交的将进入风险预警栏。

请及时登录系统，进入"计划管理"模块，点击"新建工作计划"进行编制，计划周期请选择"周计划"。

计划创建地址：{plan_create_url}

如有疑问，请联系系统管理员。"""
        
        # 统计信息
        success_count = 0
        fail_count = 0
        
        # 发送系统通知给每个用户
        for user in users:
            user_display = user.get_full_name() or user.username
            
            if dry_run:
                self.stdout.write(f'[试运行] 将发送系统通知给: {user_display}')
                success_count += 1
                continue
            
            try:
                # 创建系统通知
                notification = safe_approval_notification(
                    user=user,
                    title=title,
                    content=content,
                    object_type='plan',  # 关联到计划类型
                    object_id='weekly_reminder',  # 使用特殊ID标识这是提醒通知
                    event='weekly_plan_reminder',
                    is_read=False
                )
                
                if notification:
                    success_count += 1
                    self.stdout.write(self.style.SUCCESS(f'  ✓ {user_display}: 系统通知已创建'))
                else:
                    fail_count += 1
                    self.stdout.write(self.style.ERROR(f'  ✗ {user_display}: 系统通知创建失败'))
                    
            except Exception as e:
                logger.error(f"创建系统通知给 {user_display} 失败: {str(e)}", exc_info=True)
                fail_count += 1
                self.stdout.write(self.style.ERROR(f'  ✗ {user_display}: {str(e)}'))
        
        # 输出统计结果
        self.stdout.write('')
        self.stdout.write(self.style.SUCCESS(
            f'\n提醒发送完成：'
            f'总计={users.count()}, '
            f'成功={success_count}, '
            f'失败={fail_count}'
        ))
        
        if dry_run:
            self.stdout.write(self.style.WARNING('\n这是试运行模式，未实际发送通知'))

