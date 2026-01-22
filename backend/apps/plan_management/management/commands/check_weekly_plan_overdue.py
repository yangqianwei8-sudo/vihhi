"""
检查周计划逾期状态的管理命令

使用方法：
    python manage.py check_weekly_plan_overdue
    
建议配置为定时任务（crontab）：
    # 每天18:30执行，检查当天逾期的周计划
    30 18 * * * cd /path/to/project && /path/to/venv/bin/python manage.py check_weekly_plan_overdue >> /path/to/logs/weekly_plan_overdue.log 2>&1
"""
from django.core.management.base import BaseCommand
from django.utils import timezone
from django.db.models import Q
from backend.apps.plan_management.models import Plan
from backend.apps.plan_management.notifications import safe_approval_notification
import logging

logger = logging.getLogger(__name__)


class Command(BaseCommand):
    help = '检查周计划逾期状态并标记风险预警'

    def add_arguments(self, parser):
        parser.add_argument(
            '--dry-run',
            action='store_true',
            help='试运行模式：不实际更新，只显示将要更新的计划',
        )

    def handle(self, *args, **options):
        dry_run = options.get('dry_run', False)
        
        self.stdout.write(f'开始检查周计划逾期状态（时间：{timezone.now()}）...')
        
        if dry_run:
            self.stdout.write(self.style.WARNING('【DRY RUN 模式】仅检查，不更新'))
        
        # 获取所有周计划
        weekly_plans = Plan.objects.filter(plan_period='weekly')
        
        # 只检查未完成且未取消的计划
        weekly_plans = weekly_plans.exclude(
            status__in=['completed', 'cancelled']
        )
        
        self.stdout.write(f'找到 {weekly_plans.count()} 个周计划需要检查')
        
        updated_count = 0
        new_overdue_count = 0
        notification_count = 0
        
        for plan in weekly_plans:
            # 重新计算截止时间（如果未设置）
            if not plan.submission_deadline and plan.start_time:
                plan.submission_deadline = plan.calculate_weekly_submission_deadline()
            
            # 检查逾期状态
            old_is_overdue = plan.is_overdue
            old_risk_level = plan.risk_level
            
            plan.check_overdue_status()
            
            # 如果状态发生变化，需要保存
            if (plan.is_overdue != old_is_overdue or plan.risk_level != old_risk_level):
                if not dry_run:
                    plan.save(update_fields=['is_overdue', 'overdue_days', 'risk_level', 'submission_deadline'])
                    updated_count += 1
                    
                    # 如果是新逾期的计划，发送通知
                    if plan.is_overdue and not old_is_overdue:
                        new_overdue_count += 1
                        self._send_overdue_notification(plan)
                        notification_count += 1
                
                status_text = '新逾期' if plan.is_overdue and not old_is_overdue else '已逾期'
                self.stdout.write(
                    self.style.WARNING(
                        f'  {status_text}: {plan.plan_number} - {plan.name} '
                        f'(负责人: {plan.responsible_person.get_full_name() or plan.responsible_person.username}, '
                        f'逾期{plan.overdue_days}天, 风险等级: {plan.get_risk_level_display()})'
                    )
                )
        
        # 输出统计结果
        self.stdout.write('')
        self.stdout.write(self.style.SUCCESS(
            f'\n检查完成：'
            f'总计={weekly_plans.count()}, '
            f'更新={updated_count}, '
            f'新逾期={new_overdue_count}, '
            f'发送通知={notification_count}'
        ))
        
        if dry_run:
            self.stdout.write(self.style.WARNING('\n这是试运行模式，未实际更新数据'))
    
    def _send_overdue_notification(self, plan):
        """发送逾期通知给计划负责人"""
        try:
            title = f'【风险预警】周计划提交逾期：{plan.name}'
            content = f"""您的周计划《{plan.name}》已逾期提交。

计划编号：{plan.plan_number}
逾期天数：{plan.overdue_days} 天
风险等级：{plan.get_risk_level_display()}
截止时间：{plan.submission_deadline.strftime('%Y-%m-%d %H:%M') if plan.submission_deadline else '未设置'}

请尽快登录系统提交周计划，避免影响工作进度。

如有疑问，请联系系统管理员。"""
            
            safe_approval_notification(
                user=plan.responsible_person,
                title=title,
                content=content,
                object_type='plan',
                object_id=str(plan.id),
                event='weekly_plan_overdue',
                is_read=False
            )
            
            logger.info(f"已发送逾期通知给 {plan.responsible_person.username} (计划: {plan.plan_number})")
            
        except Exception as e:
            logger.error(f"发送逾期通知失败（计划: {plan.plan_number}）: {str(e)}", exc_info=True)
