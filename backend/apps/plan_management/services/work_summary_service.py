"""
工作总结服务

提供周报和月报的生成功能
"""
from django.utils import timezone
from django.contrib.auth import get_user_model
from datetime import date, datetime, timedelta
from typing import Dict, Any, Optional
import logging

from ..models import StrategicGoal, Plan, GoalProgressRecord, PlanProgressRecord, WorkSummary
from ..notifications import safe_approval_notification

User = get_user_model()
logger = logging.getLogger(__name__)


def generate_weekly_summary(user, week_start: date, week_end: date) -> Optional[WorkSummary]:
    """
    生成周报
    
    Args:
        user: 用户对象
        week_start: 周期开始日期（周一）
        week_end: 周期结束日期（周日）
    
    Returns:
        WorkSummary实例或None
    """
    try:
        week_start_dt = timezone.make_aware(datetime.combine(week_start, datetime.min.time()))
        week_end_dt = timezone.make_aware(datetime.combine(week_end, datetime.max.time()))
        
        # 汇总上周目标进度更新记录
        goal_progress_records = GoalProgressRecord.objects.filter(
            goal__owner=user,
            recorded_time__gte=week_start_dt,
            recorded_time__lte=week_end_dt
        ).select_related('goal')
        
        goal_progress_summary = {
            'total_updates': goal_progress_records.count(),
            'goals': []
        }
        
        for record in goal_progress_records:
            goal_progress_summary['goals'].append({
                'goal_name': record.goal.name,
                'completion_rate': float(record.completion_rate),
                'current_value': float(record.current_value),
                'updated_at': record.recorded_time.isoformat()
            })
        
        # 汇总上周周计划任务完成情况
        weekly_plans = Plan.objects.filter(
            owner=user,
            plan_period='weekly',
            status__in=['completed', 'in_progress'],
            start_time__lte=week_end_dt,
            end_time__gte=week_start_dt
        )
        
        plan_completion_summary = {
            'total_plans': weekly_plans.count(),
            'completed': weekly_plans.filter(status='completed').count(),
            'in_progress': weekly_plans.filter(status='in_progress').count(),
            'plans': []
        }
        
        for plan in weekly_plans:
            plan_completion_summary['plans'].append({
                'plan_name': plan.name,
                'status': plan.status,
                'progress': float(plan.progress),
                'completed_at': plan.completed_at.isoformat() if plan.completed_at else None
            })
        
        # 识别成就亮点（提前完成的任务）
        achievements = []
        completed_plans = weekly_plans.filter(status='completed', completed_at__isnull=False)
        for plan in completed_plans:
            if plan.end_time and plan.completed_at:
                days_ahead = (plan.end_time.date() - plan.completed_at.date()).days
                if days_ahead > 0:
                    achievements.append({
                        'type': 'early_completion',
                        'plan_name': plan.name,
                        'days_ahead': days_ahead
                    })
        
        # 识别风险项（逾期任务）
        risk_items = []
        overdue_plans = Plan.objects.filter(
            owner=user,
            plan_period='weekly',
            status__in=['draft', 'published', 'accepted', 'in_progress'],
            end_time__lt=week_end_dt
        )
        
        for plan in overdue_plans:
            days_overdue = (week_end - plan.end_time.date()).days
            risk_items.append({
                'type': 'overdue_plan',
                'plan_name': plan.name,
                'days_overdue': days_overdue
            })
        
        # 创建工作总结
        summary = WorkSummary.objects.create(
            summary_type='weekly',
            user=user,
            period_start=week_start,
            period_end=week_end,
            goal_progress_summary=goal_progress_summary,
            plan_completion_summary=plan_completion_summary,
            achievements=achievements,
            risk_items=risk_items,
            sent_to_supervisor=False
        )
        
        logger.info(f"成功生成周报（用户：{user.username}, 周期：{week_start} ~ {week_end}）")
        return summary
        
    except Exception as e:
        logger.error(f"生成周报失败（用户：{user.username}）: {str(e)}", exc_info=True)
        return None


def generate_monthly_summary(user, month_start: date, month_end: date) -> Optional[WorkSummary]:
    """
    生成月报
    
    Args:
        user: 用户对象
        month_start: 周期开始日期（月初）
        month_end: 周期结束日期（月末）
    
    Returns:
        WorkSummary实例或None
    """
    try:
        month_start_dt = timezone.make_aware(datetime.combine(month_start, datetime.min.time()))
        month_end_dt = timezone.make_aware(datetime.combine(month_end, datetime.max.time()))
        
        # 汇总上月目标进度更新记录
        goal_progress_records = GoalProgressRecord.objects.filter(
            goal__owner=user,
            recorded_time__gte=month_start_dt,
            recorded_time__lte=month_end_dt
        ).select_related('goal')
        
        goal_progress_summary = {
            'total_updates': goal_progress_records.count(),
            'goals': []
        }
        
        for record in goal_progress_records:
            goal_progress_summary['goals'].append({
                'goal_name': record.goal.name,
                'completion_rate': float(record.completion_rate),
                'current_value': float(record.current_value),
                'updated_at': record.recorded_time.isoformat()
            })
        
        # 汇总上月月度计划完成情况
        monthly_plans = Plan.objects.filter(
            owner=user,
            plan_period='monthly',
            status__in=['completed', 'in_progress'],
            start_time__lte=month_end_dt,
            end_time__gte=month_start_dt
        )
        
        plan_completion_summary = {
            'total_plans': monthly_plans.count(),
            'completed': monthly_plans.filter(status='completed').count(),
            'in_progress': monthly_plans.filter(status='in_progress').count(),
            'plans': []
        }
        
        for plan in monthly_plans:
            plan_completion_summary['plans'].append({
                'plan_name': plan.name,
                'status': plan.status,
                'progress': float(plan.progress),
                'completed_at': plan.completed_at.isoformat() if plan.completed_at else None
            })
        
        # 识别成就亮点（提前完成的任务）
        achievements = []
        completed_plans = monthly_plans.filter(status='completed', completed_at__isnull=False)
        for plan in completed_plans:
            if plan.end_time and plan.completed_at:
                days_ahead = (plan.end_time.date() - plan.completed_at.date()).days
                if days_ahead > 0:
                    achievements.append({
                        'type': 'early_completion',
                        'plan_name': plan.name,
                        'days_ahead': days_ahead
                    })
        
        # 识别风险项（逾期任务）
        risk_items = []
        overdue_plans = Plan.objects.filter(
            owner=user,
            plan_period='monthly',
            status__in=['draft', 'published', 'accepted', 'in_progress'],
            end_time__lt=month_end_dt
        )
        
        for plan in overdue_plans:
            days_overdue = (month_end - plan.end_time.date()).days
            risk_items.append({
                'type': 'overdue_plan',
                'plan_name': plan.name,
                'days_overdue': days_overdue
            })
        
        # 创建工作总结
        summary = WorkSummary.objects.create(
            summary_type='monthly',
            user=user,
            period_start=month_start,
            period_end=month_end,
            goal_progress_summary=goal_progress_summary,
            plan_completion_summary=plan_completion_summary,
            achievements=achievements,
            risk_items=risk_items,
            sent_to_supervisor=False
        )
        
        logger.info(f"成功生成月报（用户：{user.username}, 周期：{month_start} ~ {month_end}）")
        return summary
        
    except Exception as e:
        logger.error(f"生成月报失败（用户：{user.username}）: {str(e)}", exc_info=True)
        return None


def send_summary_to_user_and_supervisor(summary: WorkSummary) -> bool:
    """
    发送总结给员工和上级
    
    Args:
        summary: WorkSummary实例
    
    Returns:
        bool: 是否成功发送
    """
    try:
        user = summary.user
        summary_type_display = summary.get_summary_type_display()
        period_str = f"{summary.period_start.strftime('%Y-%m-%d')} ~ {summary.period_end.strftime('%Y-%m-%d')}"
        
        # 构建总结内容
        content_parts = [
            f"【{summary_type_display}】工作周期：{period_str}",
            "",
            "📊 目标进度汇总：",
            f"  • 进度更新次数：{summary.goal_progress_summary.get('total_updates', 0)} 次",
            "",
            "📋 计划完成汇总：",
            f"  • 总计划数：{summary.plan_completion_summary.get('total_plans', 0)} 个",
            f"  • 已完成：{summary.plan_completion_summary.get('completed', 0)} 个",
            f"  • 进行中：{summary.plan_completion_summary.get('in_progress', 0)} 个",
        ]
        
        # 成就亮点
        if summary.achievements:
            content_parts.append("")
            content_parts.append("✨ 成就亮点：")
            for achievement in summary.achievements:
                if achievement.get('type') == 'early_completion':
                    content_parts.append(f"  • 计划《{achievement.get('plan_name')}》提前 {achievement.get('days_ahead')} 天完成")
        
        # 风险项
        if summary.risk_items:
            content_parts.append("")
            content_parts.append("⚠️ 风险提示：")
            for risk in summary.risk_items:
                if risk.get('type') == 'overdue_plan':
                    content_parts.append(f"  • 计划《{risk.get('plan_name')}》已逾期 {risk.get('days_overdue')} 天")
        
        content = "\n".join(content_parts)
        
        # 发送给员工
        safe_approval_notification(
            user=user,
            title=f'【{summary_type_display}】您的工作总结已生成',
            content=content,
            object_type='summary',
            object_id=str(summary.id),
            event='work_summary_generated',
            is_read=False
        )
        
        # 发送给上级（部门负责人）
        supervisor = None
        if hasattr(user, 'department') and user.department:
            supervisor = user.department.leader
        
        if supervisor:
            safe_approval_notification(
                user=supervisor,
                title=f'【{summary_type_display}】下属工作总结：{user.get_full_name() or user.username}',
                content=f"{user.get_full_name() or user.username} 的{summary_type_display}已生成。\n\n{content}",
                object_type='summary',
                object_id=str(summary.id),
                event='work_summary_supervisor',
                is_read=False
            )
            summary.sent_to_supervisor = True
            summary.save(update_fields=['sent_to_supervisor'])
        
        logger.info(f"成功发送{summary_type_display}给用户和上级（用户：{user.username}）")
        return True
        
    except Exception as e:
        logger.error(f"发送工作总结失败（总结 #{summary.id}）: {str(e)}", exc_info=True)
        return False
