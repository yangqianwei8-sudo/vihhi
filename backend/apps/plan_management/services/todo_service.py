"""
P2-4: 待办中心服务

待办来源：
- 待接收目标/计划（published，owner=user）
- 待执行目标/计划（accepted，owner=user）
- 今日应执行计划（in_progress，today在[start_time, end_time]）
- 风险计划（逾期）
- 系统生成的待办事项（TodoTask模型）

原则：
- 查询待办和存储待办相结合
- 所有待办必须能点进去处理
"""
from django.utils import timezone
from django.urls import reverse
from datetime import date, datetime, timedelta
from typing import List, Dict, Any, Optional
from ..models import StrategicGoal, Plan, TodoTask


def get_user_todos(user) -> List[Dict[str, Any]]:
    """
    获取用户的待办列表（包含查询生成的待办和数据库中的待办）
    
    Args:
        user: User 对象
    
    Returns:
        List[Dict]: 待办列表，每个待办包含：
            - type: 待办类型（'goal_accept', 'plan_accept', 'goal_execute', 'plan_execute', 'plan_today', 'plan_risk', 或数据库待办类型）
            - title: 待办标题
            - description: 待办描述
            - priority: 优先级（'high', 'medium', 'low'）
            - url: 跳转链接
            - object: 关联的对象（StrategicGoal 或 Plan 或 TodoTask）
            - created_at: 创建时间（用于排序）
            - deadline: 截止时间（数据库待办）
            - is_overdue: 是否逾期（数据库待办）
    """
    todos = []
    now = timezone.now()
    today = now.date()
    
    # ========== 0. 从数据库获取系统生成的待办事项 ==========
    db_todos = TodoTask.objects.filter(
        user=user,
        status__in=['pending', 'overdue']
    ).select_related('user').order_by('deadline')
    
    for todo in db_todos:
        # 检查是否逾期（如果模型有 check_overdue 方法则调用，否则使用 save 方法自动检查）
        if hasattr(todo, 'check_overdue'):
            todo.check_overdue()
        elif todo.deadline and todo.status == 'pending' and todo.deadline < now:
            # 如果没有 check_overdue 方法，手动检查
            todo.is_overdue = True
            todo.overdue_days = (now.date() - todo.deadline.date()).days
            todo.status = 'overdue'
            todo.save(update_fields=['status', 'is_overdue', 'overdue_days'])
        
        # 构建跳转链接
        url = '#'
        
        # 根据待办类型设置跳转URL
        if todo.task_type == 'plan_decomposition_weekly':
            # 周计划分解待办：跳转到计划创建页面，筛选周计划
            try:
                url = reverse('plan_pages:plan_create') + '?plan_period=weekly'
            except:
                url = '/plan/plans/create/?plan_period=weekly'
        elif todo.task_type == 'plan_decomposition_daily':
            # 日计划分解待办：跳转到计划创建页面，筛选日计划
            try:
                url = reverse('plan_pages:plan_create') + '?plan_period=daily'
            except:
                url = '/plan/plans/create/?plan_period=daily'
        elif todo.task_type == 'plan_creation':
            # 计划创建待办：跳转到计划创建页面
            try:
                url = reverse('plan_pages:plan_create')
            except:
                url = '/plan/plans/create/'
        elif todo.task_type == 'goal_creation':
            # 目标创建待办：跳转到目标创建页面
            try:
                url = reverse('plan_pages:strategic_goal_create')
            except:
                url = '/plan/strategic-goals/create/'
        elif todo.task_type == 'goal_decomposition':
            # 目标分解待办：跳转到目标列表页面
            try:
                url = reverse('plan_pages:strategic_goal_list')
            except:
                url = '/plan/strategic-goals/'
        elif todo.task_type in ['goal_progress_update', 'plan_progress_update']:
            # 进度更新待办：根据关联对象跳转
            if todo.related_object_type == 'goal' and todo.related_object_id:
                try:
                    url = reverse('plan_pages:strategic_goal_track', args=[todo.related_object_id])
                except:
                    pass
            elif todo.related_object_type == 'plan' and todo.related_object_id:
                try:
                    url = reverse('plan_pages:plan_execution_track', args=[todo.related_object_id])
                except:
                    pass
            else:
                # 如果没有关联对象，跳转到对应的列表页面
                if todo.task_type == 'goal_progress_update':
                    try:
                        url = reverse('plan_pages:strategic_goal_list')
                    except:
                        url = '/plan/strategic-goals/'
                elif todo.task_type == 'plan_progress_update':
                    try:
                        url = reverse('plan_pages:plan_list')
                    except:
                        url = '/plan/plans/'
        elif todo.related_object_type == 'goal' and todo.related_object_id:
            # 其他目标相关待办
            try:
                url = reverse('plan_pages:strategic_goal_detail', args=[todo.related_object_id])
            except:
                pass
        elif todo.related_object_type == 'plan' and todo.related_object_id:
            # 其他计划相关待办
            try:
                url = reverse('plan_pages:plan_detail', args=[todo.related_object_id])
            except:
                pass
        
        priority = 'high' if todo.is_overdue else ('high' if (todo.deadline - now).total_seconds() < 86400 else 'medium')
        
        todos.append({
            'type': todo.task_type,
            'title': todo.title,
            'description': todo.description or f'截止时间：{todo.deadline.strftime("%Y-%m-%d %H:%M")}',
            'priority': priority,
            'url': url,
            'object': todo,
            'created_at': todo.created_at,
            'deadline': todo.deadline,
            'is_overdue': todo.is_overdue,
            'overdue_days': todo.overdue_days,
            'is_db_todo': True,  # 标记为数据库待办
        })
    
    # ========== 1. 待接收目标（published，owner=user）==========
    pending_goals = StrategicGoal.objects.filter(
        level='personal',
        status='published',
        owner=user
    ).select_related('parent_goal', 'responsible_person')
    
    for goal in pending_goals:
        todos.append({
            'type': 'goal_accept',
            'title': f'待接收目标：{goal.name}',
            'description': f'您有一个待接收的目标，请及时接收',
            'priority': 'high',
            'url': reverse('plan_pages:strategic_goal_detail', args=[goal.id]),
            'object': goal,
            'created_at': goal.published_at or goal.created_time,
        })
    
    # ========== 2. 待接收计划（published，owner=user）==========
    pending_plans = Plan.objects.filter(
        level='personal',
        status='published',
        owner=user
    ).select_related('parent_plan', 'responsible_person')
    
    for plan in pending_plans:
        todos.append({
            'type': 'plan_accept',
            'title': f'待接收计划：{plan.name}',
            'description': f'您有一个待接收的计划，请及时接收',
            'priority': 'high',
            'url': reverse('plan_pages:plan_detail', args=[plan.id]),
            'object': plan,
            'created_at': plan.published_at or plan.created_time,
        })
    
    # ========== 3. 待执行目标（accepted，owner=user）==========
    accepted_goals = StrategicGoal.objects.filter(
        level='personal',
        status='accepted',
        owner=user
    ).select_related('parent_goal', 'responsible_person')
    
    for goal in accepted_goals:
        todos.append({
            'type': 'goal_execute',
            'title': f'待执行目标：{goal.name}',
            'description': f'目标已接收，请开始执行',
            'priority': 'medium',
            'url': reverse('plan_pages:strategic_goal_detail', args=[goal.id]),
            'object': goal,
            'created_at': goal.accepted_at or goal.created_time,
        })
    
    # ========== 4. 待执行计划（accepted，owner=user）==========
    accepted_plans = Plan.objects.filter(
        level='personal',
        status='accepted',
        owner=user
    ).select_related('parent_plan', 'responsible_person')
    
    for plan in accepted_plans:
        todos.append({
            'type': 'plan_execute',
            'title': f'待执行计划：{plan.name}',
            'description': f'计划已接收，请开始执行',
            'priority': 'medium',
            'url': reverse('plan_pages:plan_detail', args=[plan.id]),
            'object': plan,
            'created_at': plan.accepted_at or plan.created_time,
        })
    
    # ========== 5. 今日应执行计划（in_progress，today在[start_time, end_time]）==========
    today_start = timezone.make_aware(datetime.combine(today, datetime.min.time()))
    today_end = timezone.make_aware(datetime.combine(today, datetime.max.time()))
    
    today_plans = Plan.objects.filter(
        level='personal',
        status='in_progress',
        owner=user,
        start_time__lte=today_end,
        end_time__gte=today_start
    ).select_related('responsible_person')
    
    for plan in today_plans:
        todos.append({
            'type': 'plan_today',
            'title': f'今日应执行：{plan.name}',
            'description': f'计划应在今天执行，请及时更新进度',
            'priority': 'high',
            'url': reverse('plan_pages:plan_execution_track', args=[plan.id]),
            'object': plan,
            'created_at': plan.start_time or plan.created_time,
        })
    
    # ========== 6. 风险计划（逾期）==========
    overdue_plans = Plan.objects.filter(
        level='personal',
        status__in=['draft', 'published', 'accepted', 'in_progress'],
        owner=user,
        end_time__lt=now
    ).select_related('responsible_person')
    
    for plan in overdue_plans:
        days_overdue = (now.date() - plan.end_time.date()).days
        todos.append({
            'type': 'plan_risk',
            'title': f'⚠️ 逾期计划：{plan.name}',
            'description': f'计划已逾期 {days_overdue} 天，请尽快处理',
            'priority': 'high',
            'url': reverse('plan_pages:plan_detail', args=[plan.id]),
            'object': plan,
            'created_at': plan.end_time,
        })
    
    # ========== 7. 风险目标（逾期）==========
    overdue_goals = StrategicGoal.objects.filter(
        level='personal',
        status__in=['published', 'accepted', 'in_progress'],
        owner=user,
        end_date__lt=today
    ).select_related('parent_goal', 'responsible_person')
    
    for goal in overdue_goals:
        days_overdue = (today - goal.end_date).days
        todos.append({
            'type': 'goal_risk',
            'title': f'⚠️ 逾期目标：{goal.name}',
            'description': f'目标已逾期 {days_overdue} 天，请尽快处理',
            'priority': 'high',
            'url': reverse('plan_pages:strategic_goal_detail', args=[goal.id]),
            'object': goal,
            'created_at': goal.end_date,
        })
    
    # ========== 排序：优先级 > 创建时间 ==========
    priority_order = {'high': 0, 'medium': 1, 'low': 2}
    todos.sort(key=lambda x: (priority_order.get(x['priority'], 2), x['created_at'] or timezone.now()))
    
    return todos


def get_user_todo_summary(user) -> Dict[str, int]:
    """
    获取用户待办汇总统计
    
    Args:
        user: User 对象
    
    Returns:
        Dict: 待办统计
            - total: 总待办数
            - pending_accept: 待接收数（目标+计划）
            - pending_execute: 待执行数（目标+计划）
            - today_plans: 今日应执行计划数
            - risk_items: 风险项数（逾期目标+计划）
    """
    todos = get_user_todos(user)
    
    summary = {
        'total': len(todos),
        'pending_accept': len([t for t in todos if t['type'] in ['goal_accept', 'plan_accept']]),
        'pending_execute': len([t for t in todos if t['type'] in ['goal_execute', 'plan_execute']]),
        'today_plans': len([t for t in todos if t['type'] == 'plan_today']),
        'risk_items': len([t for t in todos if t['type'] in ['plan_risk', 'goal_risk']]),
    }
    
    return summary


def create_todo_task(
    task_type: str,
    user,
    title: str,
    description: str = '',
    related_object_type: Optional[str] = None,
    related_object_id: Optional[str] = None,
    deadline: datetime = None,
    auto_generated: bool = True
) -> TodoTask:
    """
    创建待办事项
    
    Args:
        task_type: 待办类型
        user: 负责人
        title: 待办标题
        description: 待办描述
        related_object_type: 关联对象类型
        related_object_id: 关联对象ID
        deadline: 截止时间
        auto_generated: 是否系统自动生成
    
    Returns:
        TodoTask实例
    """
    if deadline is None:
        deadline = timezone.now() + timedelta(days=1)
    
    todo = TodoTask.objects.create(
        task_type=task_type,
        user=user,
        title=title,
        description=description,
        related_object_type=related_object_type,
        related_object_id=related_object_id,
        deadline=deadline,
        auto_generated=auto_generated,
        status='pending'
    )
    
    # 检查是否已逾期
    todo.check_overdue()
    if todo.is_overdue:
        todo.save()
    
    return todo


def mark_todo_completed(todo: TodoTask, user=None) -> bool:
    """
    标记待办完成
    
    Args:
        todo: TodoTask实例
        user: 完成人（可选）
    
    Returns:
        bool: 是否成功
    """
    if todo.status in ['completed', 'cancelled']:
        return False
    
    todo.status = 'completed'
    todo.completed_at = timezone.now()
    todo.is_overdue = False
    todo.overdue_days = 0
    todo.save()
    
    return True


def check_todo_overdue() -> int:
    """
    检查并标记逾期待办
    
    Returns:
        int: 标记为逾期的待办数量
    """
    now = timezone.now()
    pending_todos = TodoTask.objects.filter(status='pending')
    
    updated_count = 0
    for todo in pending_todos:
        if todo.check_overdue():
            todo.save()
            updated_count += 1
    
    return updated_count


def get_todos_by_type(user, task_type: str) -> List[TodoTask]:
    """
    按类型获取待办
    
    Args:
        user: 用户
        task_type: 待办类型
    
    Returns:
        List[TodoTask]: 待办列表
    """
    return list(TodoTask.objects.filter(
        user=user,
        task_type=task_type,
        status__in=['pending', 'overdue']
    ).order_by('deadline'))


def get_todos_for_period(user, period: str = 'today') -> List[TodoTask]:
    """
    按周期获取待办（今日/本周/本月）
    
    Args:
        user: 用户
        period: 周期（today/week/month）
    
    Returns:
        List[TodoTask]: 待办列表
    """
    now = timezone.now()
    today = now.date()
    
    if period == 'today':
        start = timezone.make_aware(datetime.combine(today, datetime.min.time()))
        end = timezone.make_aware(datetime.combine(today, datetime.max.time()))
        return list(TodoTask.objects.filter(
            user=user,
            deadline__gte=start,
            deadline__lte=end,
            status__in=['pending', 'overdue']
        ).order_by('deadline'))
    
    elif period == 'week':
        # 本周一
        days_since_monday = today.weekday()
        week_start = today - timedelta(days=days_since_monday)
        week_end = week_start + timedelta(days=6)
        start = timezone.make_aware(datetime.combine(week_start, datetime.min.time()))
        end = timezone.make_aware(datetime.combine(week_end, datetime.max.time()))
        return list(TodoTask.objects.filter(
            user=user,
            deadline__gte=start,
            deadline__lte=end,
            status__in=['pending', 'overdue']
        ).order_by('deadline'))
    
    elif period == 'month':
        # 本月第一天和最后一天
        month_start = today.replace(day=1)
        if today.month == 12:
            month_end = today.replace(day=31)
        else:
            month_end = (today.replace(day=1) + timedelta(days=32)).replace(day=1) - timedelta(days=1)
        start = timezone.make_aware(datetime.combine(month_start, datetime.min.time()))
        end = timezone.make_aware(datetime.combine(month_end, datetime.max.time()))
        return list(TodoTask.objects.filter(
            user=user,
            deadline__gte=start,
            deadline__lte=end,
            status__in=['pending', 'overdue']
        ).order_by('deadline'))
    
    return []

