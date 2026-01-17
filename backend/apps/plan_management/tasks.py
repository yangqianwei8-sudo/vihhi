"""
P2-4: Celery 任务定义（如果使用 Celery beat）

在 celery.py 中配置：
from celery import Celery
from celery.schedules import crontab

app = Celery('your_project')
app.config_from_object('django.conf:settings', namespace='CELERY')

app.conf.beat_schedule = {
    'daily-todo-reminder': {
        'task': 'plan_management.tasks.daily_todo_reminder',
        'schedule': crontab(hour=9, minute=0),
    },
}
"""
from celery import shared_task
from django.contrib.auth.models import User
from backend.apps.plan_management.services.todo_service import get_user_todo_summary
from backend.apps.plan_management.notifications import safe_approval_notification
import logging

logger = logging.getLogger(__name__)


@shared_task
def daily_todo_reminder():
    """
    P2-4: 每日待办提醒任务（Celery 版本）
    
    每天 9:00 执行，为每个用户生成待办汇总通知
    """
    users = User.objects.filter(is_active=True)
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
            
            success_count += 1
            
        except Exception as e:
            logger.error(f"处理用户 {user.username} 的待办提醒失败：{str(e)}", exc_info=True)
            error_count += 1
    
    logger.info(f"每日待办提醒任务完成：成功 {success_count} 个用户，失败 {error_count} 个用户")
    return {'success': success_count, 'error': error_count}

