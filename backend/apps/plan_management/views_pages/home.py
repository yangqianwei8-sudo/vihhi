# 计划管理首页 - 依赖
from datetime import datetime, timedelta, date
from django.shortcuts import render, redirect
from django.utils import timezone

from .common import (
    login_required,
    get_user_permission_codes,
    _permission_granted,
    messages,
    Department,
    User,
    Plan,
    StrategicGoal,
)
from .helpers import calculate_goal_progress_status, calculate_plan_progress_status
from .menu import _build_plan_management_sidebar_nav, _context
from django.urls import reverse

@login_required
def plan_management_home(request):
    """
    P2-5: 计划管理首页 - 数据展示中心（定版）
    
    首页结构（强制）：
    1. 第一行：目标中心（个人优先）
    2. 第二行：我的计划执行
    3. 第三行：待办 & 风险
    4. 第四行：管理视角（仅有权限者可见）
    
    原则：
    - 首页不做编辑，只做"看"
    - 首页不堆数据，只给"结论 + 入口"
    - 目标优先于计划
    - 风险高于统计
    - 所有数据来自 service，禁止直接 ORM
    """
    permission_codes = get_user_permission_codes(request.user)
    # 待办“取消”加强：只有具备管理权限者，才允许取消系统自动生成的待办
    context_can_manage_todo_cancel = (
        _permission_granted('plan_management.plan.manage', permission_codes)
        or _permission_granted('plan_management.manage_goal', permission_codes)
        or request.user.is_superuser
    )
    
    # 权限检查
    if not _permission_granted('plan_management.view', permission_codes):
        messages.error(request, '您没有权限访问计划管理')
        return redirect('admin:index')
    
    context = {}
    context['can_manage_todo_cancel'] = context_can_manage_todo_cancel
    
    # ========== 获取筛选参数 ==========
    filter_department_id = request.GET.get('filter_department', '').strip()
    filter_responsible_person_id = request.GET.get('filter_responsible_person', '').strip()
    filter_start_date = request.GET.get('filter_start_date', '').strip()
    filter_end_date = request.GET.get('filter_end_date', '').strip()
    active_tab = request.GET.get('active_tab', 'all').strip()  # 当前选中的标签页
    
    # 将筛选参数传递到context
    context['filter_department_id'] = filter_department_id
    context['filter_responsible_person_id'] = filter_responsible_person_id
    context['filter_start_date'] = filter_start_date
    context['filter_end_date'] = filter_end_date
    context['active_tab'] = active_tab
    
    # 获取所有部门和用户（用于筛选下拉框）
    from backend.apps.plan_management.models import Plan, StrategicGoal
    all_departments = Department.objects.filter(is_active=True).order_by('order', 'name')
    context['all_departments'] = all_departments
    
    # 根据部门筛选用户
    filter_users = User.objects.filter(is_active=True)
    if filter_department_id:
        try:
            filter_users = filter_users.filter(department_id=filter_department_id)
        except ValueError:
            pass
    context['filter_users'] = filter_users.order_by('first_name', 'last_name', 'username')
    
    # 辅助函数：应用筛选条件到查询集（不包含负责人筛选，因为负责人筛选已在查询时应用）
    def apply_filters_to_queryset(qs, model_type='plan'):
        """应用筛选条件到查询集（不包含负责人筛选，因为负责人筛选已在查询时应用）"""
        if model_type == 'plan':
            if filter_department_id:
                try:
                    qs = qs.filter(responsible_department_id=filter_department_id)
                except ValueError:
                    pass
            # 注意：不在这里应用 filter_responsible_person_id，因为已经在查询时应用了
            if filter_start_date:
                try:
                    start_date = datetime.strptime(filter_start_date, '%Y-%m-%d').date()
                    start_datetime = timezone.make_aware(datetime.combine(start_date, datetime.min.time()))
                    # 筛选：结束时间 >= 筛选开始日期（计划在执行时间范围内）
                    qs = qs.filter(end_time__gte=start_datetime)
                except ValueError:
                    pass
            if filter_end_date:
                try:
                    end_date = datetime.strptime(filter_end_date, '%Y-%m-%d').date()
                    # 包含结束日期当天
                    end_datetime = timezone.make_aware(datetime.combine(end_date, datetime.max.time()))
                    # 筛选：开始时间 <= 筛选结束日期（计划在执行时间范围内）
                    qs = qs.filter(start_time__lte=end_datetime)
                except ValueError:
                    pass
        elif model_type == 'goal':
            if filter_department_id:
                try:
                    qs = qs.filter(responsible_department_id=filter_department_id)
                except ValueError:
                    pass
            # 注意：不在这里应用 filter_responsible_person_id，因为已经在查询时应用了
            if filter_start_date:
                try:
                    start_date = datetime.strptime(filter_start_date, '%Y-%m-%d').date()
                    # 筛选：结束日期 >= 筛选开始日期（目标在执行时间范围内）
                    qs = qs.filter(end_date__gte=start_date)
                except ValueError:
                    pass
            if filter_end_date:
                try:
                    end_date = datetime.strptime(filter_end_date, '%Y-%m-%d').date()
                    # 筛选：开始日期 <= 筛选结束日期（目标在执行时间范围内）
                    qs = qs.filter(start_date__lte=end_date)
                except ValueError:
                    pass
        return qs
    
    # 辅助函数：从计划对象构建计划字典（包含plan_period）
    def build_plan_dict(plan):
        """从计划对象构建包含plan_period的字典（支持 Plan 实例或已有字典）"""
        from .helpers import calculate_plan_progress_status as _calc_plan_status
        if isinstance(plan, dict):
            # 已是字典时确保包含 plan_period，避免重复构建
            return dict(plan, plan_period=plan.get('plan_period', ''))
        return {
            'title': plan.name,
            'progress': float(getattr(plan, 'progress', 0) or 0),
            'progress_status': _calc_plan_status(plan),
            'url': reverse('plan_pages:plan_detail', args=[plan.id]),
            'plan_period': getattr(plan, 'plan_period', '') or '',
        }
    
    # 辅助函数：按计划周期分类计划（支持字典或 Plan 实例列表）
    def categorize_plans_by_period(plans_list):
        """将计划列表按周期分类为月计划、周计划、日计划"""
        monthly_plans = []
        weekly_plans = []
        daily_plans = []
        
        for plan in plans_list or []:
            if isinstance(plan, dict):
                plan_period = (plan.get('plan_period') or '').strip()
                item = plan
            else:
                plan_period = (getattr(plan, 'plan_period', None) or '').strip()
                item = build_plan_dict(plan)
            if plan_period == 'monthly':
                monthly_plans.append(item)
            elif plan_period == 'weekly':
                weekly_plans.append(item)
            elif plan_period == 'daily':
                daily_plans.append(item)
        
        return {
            'monthly': monthly_plans,
            'weekly': weekly_plans,
            'daily': daily_plans,
            'monthly_count': len(monthly_plans),
            'weekly_count': len(weekly_plans),
            'daily_count': len(daily_plans),
        }
    
    try:
        # ========== P2-5: 导入所有 service ==========
        from backend.apps.plan_management.services.goal_stats_service import get_user_goal_stats, get_company_goal_stats, get_user_collaboration_goal_stats
        from backend.apps.plan_management.services.plan_stats_service import get_user_plan_stats, get_company_plan_stats, get_user_collaboration_plan_stats
        from backend.apps.plan_management.services.todo_service import get_user_todos, get_responsible_todos
        from backend.apps.plan_management.services.risk_query_service import get_user_risk_items, get_responsible_risk_items, get_subordinates_risk_items
        
        # ========== 第一行：目标中心（个人优先）==========
        goal_stats = get_user_goal_stats(
            request.user,
            filter_department_id=filter_department_id,
            filter_responsible_person_id=filter_responsible_person_id,
            filter_start_date=filter_start_date,
            filter_end_date=filter_end_date
        )
        
        goal_cards = [{
            'label': '我的目标',
            'icon': '🎯',
            'value': str(goal_stats['total']),
            'subvalue': f'执行中 {goal_stats["in_progress"]} | 逾期 {goal_stats["overdue"]} | 本月需完成 {goal_stats["this_month"]}',
            'url': reverse('plan_pages:strategic_goal_list') + '?level=personal',
            'variant': 'primary' if goal_stats['total'] > 0 else 'secondary'
        }]
        
        context['goal_cards'] = goal_cards
        context['goal_stats'] = goal_stats
        
        # ========== 第二行：我的计划执行 ==========
        plan_stats = get_user_plan_stats(
            request.user,
            filter_department_id=filter_department_id,
            filter_responsible_person_id=filter_responsible_person_id,
            filter_start_date=filter_start_date,
            filter_end_date=filter_end_date
        )
        
        plan_cards = [{
            'label': '我的计划',
            'icon': '📋',
            'value': str(plan_stats['total']),
            'subvalue': f'执行中 {plan_stats["in_progress"]} | 今日应执行 {plan_stats["today"]} | 逾期 {plan_stats["overdue"]}',
            'url': reverse('plan_pages:plan_list') + '?level=personal',
            'variant': 'primary' if plan_stats['total'] > 0 else 'secondary'
        }]
        
        context['plan_cards'] = plan_cards
        context['plan_stats'] = plan_stats
        
        # ========== 我协作的统计 ==========
        collaboration_plan_stats = get_user_collaboration_plan_stats(
            request.user,
            filter_department_id=filter_department_id,
            filter_responsible_person_id=filter_responsible_person_id,
            filter_start_date=filter_start_date,
            filter_end_date=filter_end_date
        )
        collaboration_goal_stats = get_user_collaboration_goal_stats(
            request.user,
            filter_department_id=filter_department_id,
            filter_responsible_person_id=filter_responsible_person_id,
            filter_start_date=filter_start_date,
            filter_end_date=filter_end_date
        )
        
        collaboration_plan_cards = [{
            'label': '我协作的计划',
            'icon': '🤝',
            'value': str(collaboration_plan_stats['total']),
            'subvalue': f'执行中 {collaboration_plan_stats["in_progress"]} | 今日应执行 {collaboration_plan_stats["today"]} | 逾期 {collaboration_plan_stats["overdue"]}',
            'url': reverse('plan_pages:plan_list') + '?participating=1',
            'variant': 'info' if collaboration_plan_stats['total'] > 0 else 'secondary'
        }]
        
        collaboration_goal_cards = [{
            'label': '我协作的目标',
            'icon': '🤝',
            'value': str(collaboration_goal_stats['total']),
            'subvalue': f'执行中 {collaboration_goal_stats["in_progress"]} | 逾期 {collaboration_goal_stats["overdue"]} | 本月需完成 {collaboration_goal_stats["this_month"]}',
            'url': reverse('plan_pages:strategic_goal_list') + '?participating=1',
            'variant': 'info' if collaboration_goal_stats['total'] > 0 else 'secondary'
        }]
        
        context['collaboration_plan_stats'] = collaboration_plan_stats
        context['collaboration_goal_stats'] = collaboration_goal_stats
        context['collaboration_plan_cards'] = collaboration_plan_cards
        context['collaboration_goal_cards'] = collaboration_goal_cards
        
        # ========== 第三行：待办 & 风险 ==========
        # 我的待办（左）
        user_todos = get_user_todos(
            request.user,
            filter_department_id=filter_department_id,
            filter_responsible_person_id=filter_responsible_person_id,
            filter_start_date=filter_start_date,
            filter_end_date=filter_end_date
        )
        
        # 按类型分类待办事项（本周待办、本月待办、今日待办）
        from django.utils import timezone
        from datetime import datetime, timedelta
        
        now = timezone.now()
        today = now.date()
        week_start = today - timedelta(days=today.weekday())  # 本周一
        week_end = week_start + timedelta(days=6)  # 本周日
        month_start = today.replace(day=1)  # 本月1日
        next_month = month_start + timedelta(days=32)
        month_end = (next_month.replace(day=1) - timedelta(days=1))  # 本月最后一天
        
        todo_items = []
        weekly_todos = []
        monthly_todos = []
        daily_todos = []
        
        for todo in user_todos:
            todo_item = {
                'title': todo.get('title', ''),
                'description': todo.get('description', ''),
                'url': todo.get('url', '#'),
                'type': todo.get('type', ''),
                'priority': todo.get('priority', 'medium'),
                'deadline': todo.get('deadline'),
                'is_overdue': todo.get('is_overdue', False),
                'overdue_days': todo.get('overdue_days', 0),
            }
            
            # 根据待办类型设置显示信息
            if todo.get('is_db_todo'):
                # 数据库待办事项
                todo_item['type'] = 'db_todo'
                # 严格闭环：提供前台手动闭环所需标识
                try:
                    todo_obj = todo.get('object')
                    if todo_obj and hasattr(todo_obj, 'id'):
                        todo_item['db_todo_id'] = todo_obj.id
                        todo_item['db_todo_owner_id'] = getattr(todo_obj, 'user_id', None)
                        todo_item['db_todo_auto_generated'] = bool(getattr(todo_obj, 'auto_generated', True))
                except Exception:
                    pass
                deadline = todo.get('deadline')
                if deadline:
                    if isinstance(deadline, str):
                        try:
                            from django.utils.dateparse import parse_datetime
                            deadline = parse_datetime(deadline)
                        except:
                            try:
                                from datetime import datetime
                                deadline = datetime.fromisoformat(deadline.replace('Z', '+00:00'))
                            except:
                                deadline = None
                    
                    if deadline and hasattr(deadline, 'date'):
                        deadline_date = deadline.date() if hasattr(deadline, 'date') else deadline
                        days_left = (deadline_date - today).days
                        
                        if todo.get('is_overdue'):
                            todo_item['meta'] = f'已逾期 {todo.get("overdue_days", 0)} 天'
                        elif days_left >= 0:
                            todo_item['meta'] = f'剩余 {days_left} 天'
                        else:
                            todo_item['meta'] = f'已逾期 {abs(days_left)} 天'
                        
                        # 分类到对应的卡片
                        if deadline_date == today:
                            daily_todos.append(todo_item)
                        elif week_start <= deadline_date <= week_end:
                            weekly_todos.append(todo_item)
                        elif month_start <= deadline_date <= month_end:
                            monthly_todos.append(todo_item)
                        else:
                            todo_items.append(todo_item)  # 其他待办
                    else:
                        todo_items.append(todo_item)
                else:
                    todo_items.append(todo_item)
            else:
                # 查询生成的待办事项
                if todo.get('object'):
                    obj = todo['object']
                    if hasattr(obj, 'get_full_name'):
                        todo_item['responsible'] = obj.get_full_name() or obj.username
                    elif hasattr(obj, 'username'):
                        todo_item['responsible'] = obj.username
                    else:
                        todo_item['responsible'] = '系统'
                
                # 根据待办类型分类
                todo_type = todo.get('type', '')
                if todo_type in ['plan_decomposition_daily', 'plan_today']:
                    daily_todos.append(todo_item)
                elif todo_type in ['plan_decomposition_weekly', 'plan_creation']:
                    weekly_todos.append(todo_item)
                elif todo_type in ['plan_creation', 'goal_creation']:
                    monthly_todos.append(todo_item)
                else:
                    todo_items.append(todo_item)
        
        # 合并所有待办，优先显示今日、本周、本月
        all_todo_items = daily_todos + weekly_todos + monthly_todos + todo_items  # 显示全部，不限制数量
        
        context['todo_items'] = all_todo_items  # 显示全部，不限制数量
        context['daily_todos_count'] = len(daily_todos)
        context['weekly_todos_count'] = len(weekly_todos)
        context['monthly_todos_count'] = len(monthly_todos)
        context['user_todos'] = user_todos  # 显示全部，不限制数量
        context['user_todos_count'] = len(user_todos)
        
        # 风险提醒（右）
        # 修复：合并owner和responsible_person的风险，确保显示完整
        owner_risk_items = get_user_risk_items(
            request.user,
            limit=1000,  # 获取全部风险项，不限制数量
            filter_department_id=filter_department_id,
            filter_responsible_person_id=filter_responsible_person_id,
            filter_start_date=filter_start_date,
            filter_end_date=filter_end_date
        )
        
        responsible_risk_items = get_responsible_risk_items(
            request.user,
            limit=1000,  # 获取全部风险项，不限制数量
            filter_department_id=filter_department_id,
            filter_responsible_person_id=filter_responsible_person_id,
            filter_start_date=filter_start_date,
            filter_end_date=filter_end_date
        )
        
        # 合并并去重
        all_risk_items = owner_risk_items + responsible_risk_items
        seen_objects = set()
        unique_risk_items = []
        for item in all_risk_items:
            obj = item.get('object')
            if obj:
                obj_key = (item['type'], obj.id)
                if obj_key not in seen_objects:
                    seen_objects.add(obj_key)
                    unique_risk_items.append(item)
        
        # 按逾期天数排序
        unique_risk_items.sort(key=lambda x: x.get('days_overdue', 0), reverse=True)
        risk_items = unique_risk_items  # 显示全部，不限制数量
        
        context['risk_items'] = risk_items
        context['risk_items_count'] = len(risk_items)
        
        # ========== 第四行：管理视角（仅有权限者可见）==========
        can_view_management = _permission_granted('plan_management.manage_goal', permission_codes) or _permission_granted('plan_management.plan.manage', permission_codes)
        
        if can_view_management:
            # 公司目标统计
            company_goal_stats = get_company_goal_stats(request.user)
            context['company_goal_stats'] = company_goal_stats
            
            # 公司计划统计
            company_plan_stats = get_company_plan_stats(request.user)
            context['company_plan_stats'] = company_plan_stats
            
            # 审批统计（仅管理视角）
            # 待审批判定：decided_at is null（根据模型定义和注释）
            pending_decisions = PlanDecision.objects.filter(decided_at__isnull=True)
            pending_total = pending_decisions.count()
            pending_start = pending_decisions.filter(request_type='start').count()
            pending_cancel = pending_decisions.filter(request_type='cancel').count()
            
            context['management_view'] = {
                'pending_total': pending_total,
                'pending_start': pending_start,
                'pending_cancel': pending_cancel,
            }
        
        context['can_view_management'] = can_view_management
        
        # ========== 第五行：下属工作情况（仅部门负责人可见）==========
        from backend.apps.system_management.services import get_subordinate_users, is_department_manager
        from django.db.models import Q, Count
        from django.utils import timezone
        from datetime import datetime, timedelta
        
        is_manager = is_department_manager(request.user)
        context['is_department_manager'] = is_manager
        
        # 初始化subordinates变量
        subordinates = get_subordinate_users(request.user) if is_manager else User.objects.none()
        
        if is_manager:
            context['subordinates_count'] = subordinates.count()
            
            # 获取下属的计划统计
            subordinate_plan_stats = []
            now = timezone.now()
            
            for subordinate in subordinates[:10]:  # 最多显示10个下属
                # 获取下属的计划
                subordinate_plans = Plan.objects.filter(
                    Q(owner=subordinate) | Q(responsible_person=subordinate) | Q(created_by=subordinate)
                ).distinct()
                
                # 统计
                total = subordinate_plans.count()
                in_progress = subordinate_plans.filter(status='in_progress').count()
                overdue = subordinate_plans.filter(
                    status__in=['draft', 'published', 'in_progress'],
                    end_time__lt=now
                ).count()
                
                # 今日应执行
                today = now.date()
                today_plans = subordinate_plans.filter(
                    status__in=['draft', 'published', 'in_progress'],
                    start_time__lte=now,
                    end_time__gte=now
                )
                
                subordinate_plan_stats.append({
                    'user': subordinate,
                    'user_name': subordinate.get_full_name() or subordinate.username,
                    'total': total,
                    'in_progress': in_progress,
                    'overdue': overdue,
                    'today': today_plans.count(),
                })
            
            context['subordinate_plan_stats'] = subordinate_plan_stats
            
            # 获取下属的目标统计
            subordinate_goal_stats = []
            for subordinate in subordinates[:10]:
                subordinate_goals = StrategicGoal.objects.filter(
                    Q(owner=subordinate) | Q(responsible_person=subordinate) | Q(created_by=subordinate)
                ).distinct()
                
                total = subordinate_goals.count()
                in_progress = subordinate_goals.filter(status='in_progress').count()
                overdue = subordinate_goals.filter(
                    status__in=['draft', 'published', 'in_progress'],
                    end_date__lt=today
                ).count()
                
                # 本月需完成
                month_start = today.replace(day=1)
                month_end = (month_start + timedelta(days=32)).replace(day=1) - timedelta(days=1)
                this_month = subordinate_goals.filter(
                    status__in=['draft', 'published', 'in_progress'],
                    end_date__gte=month_start,
                    end_date__lte=month_end
                ).count()
                
                subordinate_goal_stats.append({
                    'user': subordinate,
                    'user_name': subordinate.get_full_name() or subordinate.username,
                    'total': total,
                    'in_progress': in_progress,
                    'overdue': overdue,
                    'this_month': this_month,
                })
            
            context['subordinate_goal_stats'] = subordinate_goal_stats
            
            # 计算"全部"分类的汇总数据（我的 + 下属的）
            # 汇总下属的计划统计
            subordinate_plan_summary = {
                'total': sum(stat['total'] for stat in subordinate_plan_stats),
                'in_progress': sum(stat['in_progress'] for stat in subordinate_plan_stats),
                'today': sum(stat['today'] for stat in subordinate_plan_stats),
                'overdue': sum(stat['overdue'] for stat in subordinate_plan_stats),
            }
            
            # 汇总下属的目标统计
            subordinate_goal_summary = {
                'total': sum(stat['total'] for stat in subordinate_goal_stats),
                'in_progress': sum(stat['in_progress'] for stat in subordinate_goal_stats),
                'overdue': sum(stat['overdue'] for stat in subordinate_goal_stats),
                'this_month': sum(stat['this_month'] for stat in subordinate_goal_stats),
            }
            
            # 获取下属协作的统计
            subordinate_collaboration_plan_stats = []
            subordinate_collaboration_goal_stats = []
            subordinate_collaboration_plan_summary = {'total': 0, 'in_progress': 0, 'today': 0, 'overdue': 0}
            subordinate_collaboration_goal_summary = {'total': 0, 'in_progress': 0, 'overdue': 0, 'this_month': 0}
            
            for subordinate in subordinates[:10]:
                # 下属协作的计划（作为参与者，排除自己负责的）
                sub_collab_plans = Plan.objects.filter(participants=subordinate).exclude(responsible_person=subordinate)
                sub_collab_plan_total = sub_collab_plans.count()
                sub_collab_plan_in_progress = sub_collab_plans.filter(status='in_progress').count()
                sub_collab_plan_overdue = sub_collab_plans.filter(
                    status__in=['draft', 'published', 'in_progress'],
                    end_time__lt=now
                ).count()
                today_start = timezone.make_aware(datetime.combine(today, datetime.min.time()))
                today_end = timezone.make_aware(datetime.combine(today, datetime.max.time()))
                sub_collab_plan_today = sub_collab_plans.filter(
                    status='in_progress',
                    start_time__lte=today_end,
                    end_time__gte=today_start
                ).count()
                
                subordinate_collaboration_plan_summary['total'] += sub_collab_plan_total
                subordinate_collaboration_plan_summary['in_progress'] += sub_collab_plan_in_progress
                subordinate_collaboration_plan_summary['today'] += sub_collab_plan_today
                subordinate_collaboration_plan_summary['overdue'] += sub_collab_plan_overdue
                
                # 下属协作的目标（作为参与者，排除自己负责的）
                sub_collab_goals = StrategicGoal.objects.filter(participants=subordinate).exclude(responsible_person=subordinate)
                sub_collab_goal_total = sub_collab_goals.count()
                sub_collab_goal_in_progress = sub_collab_goals.filter(status='in_progress').count()
                sub_collab_goal_overdue = sub_collab_goals.filter(
                    status__in=['published', 'in_progress'],
                    end_date__lt=today
                ).count()
                month_start = today.replace(day=1)
                month_end = (month_start + timedelta(days=32)).replace(day=1) - timedelta(days=1)
                sub_collab_goal_this_month = sub_collab_goals.filter(
                    end_date__year=today.year,
                    end_date__month=today.month,
                    status__in=['published', 'accepted', 'in_progress']
                ).count()
                
                subordinate_collaboration_goal_summary['total'] += sub_collab_goal_total
                subordinate_collaboration_goal_summary['in_progress'] += sub_collab_goal_in_progress
                subordinate_collaboration_goal_summary['overdue'] += sub_collab_goal_overdue
                subordinate_collaboration_goal_summary['this_month'] += sub_collab_goal_this_month
            
            context['subordinate_collaboration_plan_summary'] = subordinate_collaboration_plan_summary
            context['subordinate_collaboration_goal_summary'] = subordinate_collaboration_goal_summary
            
            # "全部" = 我负责的 + 下属负责的 + 我协作的 + 下属协作的
            # 但如果筛选了负责人或部门，只显示筛选后的数据（不合并下属和协作数据）
            if filter_responsible_person_id or filter_department_id:
                # 有筛选条件时，"全部"只显示筛选后的数据
                all_plan_stats = {
                    'total': plan_stats['total'] + collaboration_plan_stats['total'],
                    'in_progress': plan_stats['in_progress'] + collaboration_plan_stats['in_progress'],
                    'today': plan_stats['today'] + collaboration_plan_stats['today'],
                    'overdue': plan_stats['overdue'] + collaboration_plan_stats['overdue'],
                }
                
                all_goal_stats = {
                    'total': goal_stats['total'] + collaboration_goal_stats['total'],
                    'in_progress': goal_stats['in_progress'] + collaboration_goal_stats['in_progress'],
                    'overdue': goal_stats['overdue'] + collaboration_goal_stats['overdue'],
                    'this_month': goal_stats['this_month'] + collaboration_goal_stats['this_month'],
                }
            else:
                # 没有筛选条件时，合并所有数据
                all_plan_stats = {
                    'total': plan_stats['total'] + subordinate_plan_summary['total'] + collaboration_plan_stats['total'] + subordinate_collaboration_plan_summary['total'],
                    'in_progress': plan_stats['in_progress'] + subordinate_plan_summary['in_progress'] + collaboration_plan_stats['in_progress'] + subordinate_collaboration_plan_summary['in_progress'],
                    'today': plan_stats['today'] + subordinate_plan_summary['today'] + collaboration_plan_stats['today'] + subordinate_collaboration_plan_summary['today'],
                    'overdue': plan_stats['overdue'] + subordinate_plan_summary['overdue'] + collaboration_plan_stats['overdue'] + subordinate_collaboration_plan_summary['overdue'],
                }
                
                all_goal_stats = {
                    'total': goal_stats['total'] + subordinate_goal_summary['total'] + collaboration_goal_stats['total'] + subordinate_collaboration_goal_summary['total'],
                    'in_progress': goal_stats['in_progress'] + subordinate_goal_summary['in_progress'] + collaboration_goal_stats['in_progress'] + subordinate_collaboration_goal_summary['in_progress'],
                    'overdue': goal_stats['overdue'] + subordinate_goal_summary['overdue'] + collaboration_goal_stats['overdue'] + subordinate_collaboration_goal_summary['overdue'],
                    'this_month': goal_stats['this_month'] + subordinate_goal_summary['this_month'] + collaboration_goal_stats['this_month'] + subordinate_collaboration_goal_summary['this_month'],
                }
            
            context['all_plan_stats'] = all_plan_stats
            context['all_goal_stats'] = all_goal_stats
            context['subordinate_plan_summary'] = subordinate_plan_summary
            context['subordinate_goal_summary'] = subordinate_goal_summary
            
            # 为手风琴分类准备卡片数据
            # 全部分类的卡片
            all_goal_cards = [{
                'label': '全部目标',
                'icon': '🎯',
                'value': str(all_goal_stats['total']),
                'subvalue': f'执行中 {all_goal_stats["in_progress"]} | 逾期 {all_goal_stats["overdue"]} | 本月需完成 {all_goal_stats["this_month"]}',
                'url': reverse('plan_pages:strategic_goal_list'),
                'variant': 'primary' if all_goal_stats['total'] > 0 else 'secondary'
            }]
            
            all_plan_cards = [{
                'label': '全部计划',
                'icon': '📋',
                'value': str(all_plan_stats['total']),
                'subvalue': f'执行中 {all_plan_stats["in_progress"]} | 今日应执行 {all_plan_stats["today"]} | 逾期 {all_plan_stats["overdue"]}',
                'url': reverse('plan_pages:plan_list'),
                'variant': 'primary' if all_plan_stats['total'] > 0 else 'secondary'
            }]
            
            # 我负责的分类的卡片（使用现有的）
            my_goal_cards = goal_cards
            my_plan_cards = plan_cards
            
            # 我下属的分类的卡片
            subordinate_goal_cards = [{
                'label': '下属目标',
                'icon': '🎯',
                'value': str(subordinate_goal_summary['total']),
                'subvalue': f'执行中 {subordinate_goal_summary["in_progress"]} | 逾期 {subordinate_goal_summary["overdue"]} | 本月需完成 {subordinate_goal_summary["this_month"]}',
                'url': reverse('plan_pages:strategic_goal_list'),
                'variant': 'success' if subordinate_goal_summary['total'] > 0 else 'secondary'
            }]
            
            subordinate_plan_cards = [{
                'label': '下属计划',
                'icon': '📋',
                'value': str(subordinate_plan_summary['total']),
                'subvalue': f'执行中 {subordinate_plan_summary["in_progress"]} | 今日应执行 {subordinate_plan_summary["today"]} | 逾期 {subordinate_plan_summary["overdue"]}',
                'url': reverse('plan_pages:plan_list'),
                'variant': 'success' if subordinate_plan_summary['total'] > 0 else 'secondary'
            }]
            
            # 下属协作的卡片
            subordinate_collaboration_goal_cards = [{
                'label': '下属协作目标',
                'icon': '🤝',
                'value': str(subordinate_collaboration_goal_summary['total']),
                'subvalue': f'执行中 {subordinate_collaboration_goal_summary["in_progress"]} | 逾期 {subordinate_collaboration_goal_summary["overdue"]} | 本月需完成 {subordinate_collaboration_goal_summary["this_month"]}',
                'url': reverse('plan_pages:strategic_goal_list'),
                'variant': 'warning' if subordinate_collaboration_goal_summary['total'] > 0 else 'secondary'
            }]
            
            subordinate_collaboration_plan_cards = [{
                'label': '下属协作计划',
                'icon': '🤝',
                'value': str(subordinate_collaboration_plan_summary['total']),
                'subvalue': f'执行中 {subordinate_collaboration_plan_summary["in_progress"]} | 今日应执行 {subordinate_collaboration_plan_summary["today"]} | 逾期 {subordinate_collaboration_plan_summary["overdue"]}',
                'url': reverse('plan_pages:plan_list'),
                'variant': 'warning' if subordinate_collaboration_plan_summary['total'] > 0 else 'secondary'
            }]
            
            context['all_goal_cards'] = all_goal_cards
            context['all_plan_cards'] = all_plan_cards
            context['my_goal_cards'] = my_goal_cards
            context['my_plan_cards'] = my_plan_cards
            context['subordinate_goal_cards'] = subordinate_goal_cards
            context['subordinate_plan_cards'] = subordinate_plan_cards
            context['subordinate_collaboration_goal_cards'] = subordinate_collaboration_goal_cards
            context['subordinate_collaboration_plan_cards'] = subordinate_collaboration_plan_cards
        else:
            context['subordinates_count'] = 0
            context['subordinate_plan_stats'] = []
            context['subordinate_goal_stats'] = []
            # 非部门负责人，全部 = 我负责的 + 我协作的
            context['subordinate_plan_summary'] = {'total': 0, 'in_progress': 0, 'today': 0, 'overdue': 0}
            context['subordinate_goal_summary'] = {'total': 0, 'in_progress': 0, 'overdue': 0, 'this_month': 0}
            context['subordinate_plan_summary'] = {'total': 0, 'in_progress': 0, 'today': 0, 'overdue': 0}
            context['subordinate_goal_summary'] = {'total': 0, 'in_progress': 0, 'overdue': 0, 'this_month': 0}
            context['subordinate_collaboration_plan_summary'] = {'total': 0, 'in_progress': 0, 'today': 0, 'overdue': 0}
            context['subordinate_collaboration_goal_summary'] = {'total': 0, 'in_progress': 0, 'overdue': 0, 'this_month': 0}
            
            # 全部 = 我负责的 + 我协作的
            all_plan_stats = {
                'total': plan_stats['total'] + collaboration_plan_stats['total'],
                'in_progress': plan_stats['in_progress'] + collaboration_plan_stats['in_progress'],
                'today': plan_stats['today'] + collaboration_plan_stats['today'],
                'overdue': plan_stats['overdue'] + collaboration_plan_stats['overdue'],
            }
            
            all_goal_stats = {
                'total': goal_stats['total'] + collaboration_goal_stats['total'],
                'in_progress': goal_stats['in_progress'] + collaboration_goal_stats['in_progress'],
                'overdue': goal_stats['overdue'] + collaboration_goal_stats['overdue'],
                'this_month': goal_stats['this_month'] + collaboration_goal_stats['this_month'],
            }
            
            context['all_plan_stats'] = all_plan_stats
            context['all_goal_stats'] = all_goal_stats
            
            # 非部门负责人，只显示"全部"、"我负责的"和"我协作的"
            all_goal_cards = [{
                'label': '全部目标',
                'icon': '🎯',
                'value': str(all_goal_stats['total']),
                'subvalue': f'执行中 {all_goal_stats["in_progress"]} | 逾期 {all_goal_stats["overdue"]} | 本月需完成 {all_goal_stats["this_month"]}',
                'url': reverse('plan_pages:strategic_goal_list'),
                'variant': 'primary' if all_goal_stats['total'] > 0 else 'secondary'
            }]
            
            all_plan_cards = [{
                'label': '全部计划',
                'icon': '📋',
                'value': str(all_plan_stats['total']),
                'subvalue': f'执行中 {all_plan_stats["in_progress"]} | 今日应执行 {all_plan_stats["today"]} | 逾期 {all_plan_stats["overdue"]}',
                'url': reverse('plan_pages:plan_list'),
                'variant': 'primary' if all_plan_stats['total'] > 0 else 'secondary'
            }]
            
            context['all_goal_cards'] = all_goal_cards
            context['all_plan_cards'] = all_plan_cards
            context['my_goal_cards'] = goal_cards
            context['my_plan_cards'] = plan_cards
            context['subordinate_goal_cards'] = []
            context['subordinate_plan_cards'] = []
            context['subordinate_collaboration_goal_cards'] = []
            context['subordinate_collaboration_plan_cards'] = []
        
    except Exception as e:
        import logging
        logger = logging.getLogger(__name__)
        logger.exception('获取统计数据失败: %s', str(e))
        # P2-5: 设置默认值避免模板错误
        context.setdefault('goal_cards', [])
        context.setdefault('plan_cards', [])
        context.setdefault('user_todos', [])
        context.setdefault('risk_items', [])
        context.setdefault('goal_stats', {'total': 0, 'in_progress': 0, 'overdue': 0, 'this_month': 0})
        context.setdefault('plan_stats', {'total': 0, 'in_progress': 0, 'today': 0, 'overdue': 0})
        context.setdefault('can_view_management', False)
        context.setdefault('is_department_manager', False)
        context.setdefault('subordinates_count', 0)
        # 确保 is_manager 变量被定义
        is_manager = False
        # 确保 subordinates 变量被定义
        subordinates = User.objects.none()
        # 确保 risk_items 变量被定义
        risk_items = []
        # 确保 all_todo_items 变量被定义
        all_todo_items = []
        # 确保导入的函数被定义（如果导入失败）
        try:
            from backend.apps.plan_management.services.risk_query_service import get_user_risk_items, get_responsible_risk_items, get_subordinates_risk_items
            from backend.apps.plan_management.services.todo_service import get_user_todos, get_responsible_todos
        except ImportError:
            # 如果导入失败，定义默认的空函数
            def get_user_risk_items(*args, **kwargs):
                return []
            def get_responsible_risk_items(*args, **kwargs):
                return []
            def get_subordinates_risk_items(*args, **kwargs):
                return []
            def get_user_todos(*args, **kwargs):
                return []
            def get_responsible_todos(*args, **kwargs):
                return []
        context.setdefault('subordinate_plan_stats', [])
        context.setdefault('subordinate_goal_stats', [])
        context.setdefault('all_plan_stats', {'total': 0, 'in_progress': 0, 'today': 0, 'overdue': 0})
        context.setdefault('all_goal_stats', {'total': 0, 'in_progress': 0, 'overdue': 0, 'this_month': 0})
        context.setdefault('subordinate_plan_summary', {'total': 0, 'in_progress': 0, 'today': 0, 'overdue': 0})
        context.setdefault('subordinate_goal_summary', {'total': 0, 'in_progress': 0, 'overdue': 0, 'this_month': 0})
        context.setdefault('all_goal_cards', [])
        context.setdefault('all_plan_cards', [])
        context.setdefault('my_goal_cards', [])
        context.setdefault('my_plan_cards', [])
        context.setdefault('subordinate_goal_cards', [])
        context.setdefault('subordinate_plan_cards', [])
        context.setdefault('collaboration_goal_cards', [])
        context.setdefault('collaboration_plan_cards', [])
        context.setdefault('subordinate_collaboration_goal_cards', [])
        context.setdefault('subordinate_collaboration_plan_cards', [])
        context.setdefault('collaboration_plan_stats', {'total': 0, 'in_progress': 0, 'today': 0, 'overdue': 0})
        context.setdefault('collaboration_goal_stats', {'total': 0, 'in_progress': 0, 'overdue': 0, 'this_month': 0})
        context.setdefault('subordinate_collaboration_plan_summary', {'total': 0, 'in_progress': 0, 'today': 0, 'overdue': 0})
        context.setdefault('subordinate_collaboration_goal_summary', {'total': 0, 'in_progress': 0, 'overdue': 0, 'this_month': 0})
        # 空计划按周期结构，供模板安全访问月/周/日计划卡片
        _empty_plans_by_period = {
            'monthly': [], 'weekly': [], 'daily': [],
            'monthly_count': 0, 'weekly_count': 0, 'daily_count': 0,
        }
        _empty_my_work = {
            'my_plans': [], 'my_plans_count': 0,
            'my_goals': [], 'my_goals_count': 0,
            'participating_plans': [], 'participating_plans_count': 0,
            'plans_by_period': _empty_plans_by_period,
        }
        context.setdefault('category_data', {
            'all': {'plan_status_dist': None, 'goal_status_dist': None, 'risk_items': [], 'todo_items': [], 'my_work': _empty_my_work},
            'mine': {'plan_status_dist': None, 'goal_status_dist': None, 'risk_items': [], 'todo_items': [], 'my_work': _empty_my_work},
            'collaboration': {'plan_status_dist': None, 'goal_status_dist': None, 'risk_items': [], 'todo_items': [], 'my_work': _empty_my_work},
        })
    
    # ========== 安全字段检查（统一获取，避免重复）==========
    plan_fields = {f.name for f in Plan._meta.get_fields()}
    goal_fields = {f.name for f in StrategicGoal._meta.get_fields()}
    
    # ========== 计划状态分布（已清除）==========
    context['plan_status_dist'] = None
    
    # ========== 目标状态分布（已清除）==========
    context['goal_status_dist'] = None
    
    # 保留状态标签映射用于其他用途（如果需要）
    from django.db.models import Q
    plan_status_label_map = {}
    try:
        for code, label in getattr(Plan, 'STATUS_CHOICES', Plan._meta.get_field('status').choices):
            plan_status_label_map[code] = label
    except Exception:
        plan_status_label_map = {}
    
    goal_status_label_map = {}
    try:
        for code, label in getattr(StrategicGoal, 'STATUS_CHOICES', StrategicGoal._meta.get_field('status').choices):
            goal_status_label_map[code] = label
    except Exception:
        goal_status_label_map = {}
    
    # ========== 我的工作 ==========
    my_work = {}
    
    # 我负责的计划（安全字段检查）
    plan_related_fields = []
    if 'responsible_person' in plan_fields:
        plan_related_fields.append('responsible_person')
    if 'related_goal' in plan_fields:
        plan_related_fields.append('related_goal')
    
    # 根据筛选条件决定查询逻辑
    # 如果筛选了负责人，查询该负责人负责的计划（所有级别）；否则查询当前用户负责的所有计划（个人+公司）
    if 'responsible_person' in plan_fields:
        if filter_responsible_person_id:
            # 筛选了负责人，查询该负责人负责的计划（所有级别）
            my_plans_qs = Plan.objects.filter(responsible_person_id=filter_responsible_person_id).order_by('-updated_time')
        else:
            # 没有筛选负责人，查询当前用户负责的所有计划（个人计划+公司计划，月/周/日卡片一致展示）
            my_plans_qs = Plan.objects.filter(responsible_person=request.user).order_by('-updated_time')
    else:
        my_plans_qs = Plan.objects.none()
    
    # 应用其他筛选条件（部门、日期）
    my_plans_qs = apply_filters_to_queryset(my_plans_qs, 'plan')
    my_plans = list(my_plans_qs.select_related(*plan_related_fields)) if plan_related_fields and my_plans_qs else []  # 显示全部，不限制数量
    my_work['my_plans'] = [build_plan_dict(p) for p in my_plans]
    my_work['my_plans_count'] = my_plans_qs.count()
    # 按周期分类我负责的计划
    my_work['plans_by_period'] = categorize_plans_by_period(my_work['my_plans'])
    
    # 我负责的目标（安全字段检查）
    goal_related_fields = []
    if 'responsible_person' in goal_fields:
        goal_related_fields.append('responsible_person')
    if 'parent_goal' in goal_fields:
        goal_related_fields.append('parent_goal')
    
    # 根据筛选条件决定查询逻辑
    # 如果筛选了负责人，查询该负责人负责的目标（所有级别）；否则查询当前用户负责的所有目标（个人+公司）
    if 'responsible_person' in goal_fields:
        if filter_responsible_person_id:
            # 筛选了负责人，查询该负责人负责的目标（所有级别）
            my_goals_qs = StrategicGoal.objects.filter(responsible_person_id=filter_responsible_person_id).order_by('-updated_time')
        else:
            # 没有筛选负责人，查询当前用户负责的所有目标（个人目标+公司目标）
            my_goals_qs = StrategicGoal.objects.filter(responsible_person=request.user).order_by('-updated_time')
    else:
        my_goals_qs = StrategicGoal.objects.none()
    
    # 应用其他筛选条件（部门、日期）
    my_goals_qs = apply_filters_to_queryset(my_goals_qs, 'goal')
    my_goals = list(my_goals_qs.select_related(*goal_related_fields)) if goal_related_fields and my_goals_qs else []  # 显示全部，不限制数量
    
    my_work['my_goals'] = [{
        'title': g.name,
        'target_value': float(g.target_value) if g.target_value else 0,
        'current_value': float(g.current_value) if g.current_value else 0,
        'indicator_unit': g.indicator_unit or '',
        'completion_rate': float(getattr(g, 'completion_rate', 0) or 0),
        'progress_status': calculate_goal_progress_status(g),
        'url': reverse('plan_pages:strategic_goal_detail', args=[g.id])
    } for g in my_goals]
    my_work['my_goals_count'] = my_goals_qs.count()
    
    # 我参与的计划（仅当 participants 字段存在才统计，避免 FieldError）
    # 注意：根据权限要求，员工只能看到本人的和公司级的工作计划
    # 所以这里只显示用户作为负责人或所有者的计划，不显示仅作为参与者的计划
    participating_plans = []
    participating_plans_count = 0
    # 移除"我参与的计划"功能，因为员工只能看到本人的和公司级的计划
    # 如果用户只是参与者但不是负责人或所有者，则不应该看到该计划
    
    my_work['participating_plans'] = participating_plans
    my_work['participating_plans_count'] = participating_plans_count
    
    context['my_work'] = my_work
    
    # ========== 最近活动 ==========
    # ========== 为每个分类准备完整数据 ==========
    # 由于代码量很大，我们为每个分类准备数据字典
    # 每个分类需要：plan_status_dist, goal_status_dist, risk_items, todo_items, my_work
    
    # 确保is_manager已定义（必须在subordinates之前）
    # 优先从 context 获取，如果没有则重新计算
    if 'is_manager' not in locals() and 'is_department_manager' in context:
        is_manager = context['is_department_manager']
    elif 'is_manager' not in locals():
        from backend.apps.system_management.services import is_department_manager
        is_manager = is_department_manager(request.user)
    
    # 确保subordinates变量已定义（如果还没有）
    if 'subordinates' not in locals():
        from backend.apps.system_management.services import get_subordinate_users
        subordinates = get_subordinate_users(request.user) if is_manager else User.objects.none()
    
    # 确保subordinates_count已定义
    if 'subordinates_count' not in context:
        context['subordinates_count'] = subordinates.count() if is_manager else 0
    
    # 分类数据字典
    category_data = {}
    
    # 预先定义所有需要的查询集（用于"全部"分类）
    # 下属负责的查询集（与统计卡片保持一致：owner、responsible_person、created_by）
    subordinate_responsible_plans_qs = Plan.objects.none()
    subordinate_responsible_goals_qs = StrategicGoal.objects.none()
    if is_manager and subordinates.exists():
        from django.db.models import Q
        # 根据筛选条件决定查询逻辑
        if filter_responsible_person_id:
            # 筛选了负责人，如果该负责人是下属，查询该负责人负责的计划/目标
            if User.objects.filter(id=filter_responsible_person_id, id__in=subordinates).exists():
                subordinate_responsible_plans_qs = Plan.objects.filter(responsible_person_id=filter_responsible_person_id)
                subordinate_responsible_goals_qs = StrategicGoal.objects.filter(responsible_person_id=filter_responsible_person_id)
            else:
                # 筛选的负责人不是下属，返回空查询集
                subordinate_responsible_plans_qs = Plan.objects.none()
                subordinate_responsible_goals_qs = StrategicGoal.objects.none()
        else:
            # 没有筛选负责人，查询所有下属的计划/目标（包含 owner、responsible_person、created_by）
            subordinate_responsible_plans_qs = Plan.objects.filter(
                Q(owner__in=subordinates) | Q(responsible_person__in=subordinates) | Q(created_by__in=subordinates)
            ).distinct()
            subordinate_responsible_goals_qs = StrategicGoal.objects.filter(
                Q(owner__in=subordinates) | Q(responsible_person__in=subordinates) | Q(created_by__in=subordinates)
            ).distinct()
        # 应用其他筛选条件（部门、日期）
        subordinate_responsible_plans_qs = apply_filters_to_queryset(subordinate_responsible_plans_qs, 'plan')
        subordinate_responsible_goals_qs = apply_filters_to_queryset(subordinate_responsible_goals_qs, 'goal')
    
    # 我协作的查询集
    # 根据筛选条件决定查询逻辑
    if filter_responsible_person_id:
        # 筛选了负责人，查询该负责人负责的计划/目标（不限制参与者）
        my_collaboration_plans_qs = Plan.objects.filter(responsible_person_id=filter_responsible_person_id)
        my_collaboration_goals_qs = StrategicGoal.objects.filter(responsible_person_id=filter_responsible_person_id)
    else:
        # 没有筛选负责人，查询当前用户作为参与者的计划/目标（排除自己负责的）
        my_collaboration_plans_qs = Plan.objects.filter(participants=request.user).exclude(responsible_person=request.user)
        my_collaboration_goals_qs = StrategicGoal.objects.filter(participants=request.user).exclude(responsible_person=request.user)
    # 应用其他筛选条件（部门、日期）
    my_collaboration_plans_qs = apply_filters_to_queryset(my_collaboration_plans_qs, 'plan')
    my_collaboration_goals_qs = apply_filters_to_queryset(my_collaboration_goals_qs, 'goal')
    
    # 下属协作的查询集
    subordinate_collaboration_plans_qs = Plan.objects.none()
    subordinate_collaboration_goals_qs = StrategicGoal.objects.none()
    if is_manager and subordinates.exists():
        # 根据筛选条件决定查询逻辑
        if filter_responsible_person_id:
            # 筛选了负责人，如果该负责人是下属，查询该负责人负责的计划/目标
            if filter_responsible_person_id and User.objects.filter(id=filter_responsible_person_id, id__in=subordinates).exists():
                subordinate_collaboration_plans_qs = Plan.objects.filter(responsible_person_id=filter_responsible_person_id)
                subordinate_collaboration_goals_qs = StrategicGoal.objects.filter(responsible_person_id=filter_responsible_person_id)
            else:
                # 筛选的负责人不是下属，返回空查询集
                subordinate_collaboration_plans_qs = Plan.objects.none()
                subordinate_collaboration_goals_qs = StrategicGoal.objects.none()
        else:
            # 没有筛选负责人，查询下属作为参与者的计划/目标（排除下属负责的）
            subordinate_collaboration_plans_qs = Plan.objects.filter(participants__in=subordinates).exclude(responsible_person__in=subordinates)
            subordinate_collaboration_goals_qs = StrategicGoal.objects.filter(participants__in=subordinates).exclude(responsible_person__in=subordinates)
        # 应用其他筛选条件（部门、日期）
        subordinate_collaboration_plans_qs = apply_filters_to_queryset(subordinate_collaboration_plans_qs, 'plan')
        subordinate_collaboration_goals_qs = apply_filters_to_queryset(subordinate_collaboration_goals_qs, 'goal')
    
    # 1. 全部分类的数据（合并所有：我负责的+我协作的+下属负责的+下属协作的）
    # 计划状态分布和目标状态分布已清除
    
    # 全部分类的风险项：合并所有相关风险
    # 修复：包含owner + responsible_person + 下属负责的风险
    # 确保 risk_items 已定义
    if 'risk_items' not in locals():
        risk_items = context.get('risk_items', [])
    
    # 从context获取风险（已在首页计算，包含owner和responsible的风险）
    # 但为了确保完整性，我们重新获取所有相关风险
    owner_risk_items = get_user_risk_items(
        request.user,
        limit=10,
        filter_department_id=filter_department_id,
        filter_responsible_person_id=filter_responsible_person_id,
        filter_start_date=filter_start_date,
        filter_end_date=filter_end_date
    )
    
    responsible_risk_items = get_responsible_risk_items(
        request.user,
        limit=10,
        filter_department_id=filter_department_id,
        filter_responsible_person_id=filter_responsible_person_id,
        filter_start_date=filter_start_date,
        filter_end_date=filter_end_date
    )
    
    # 合并owner和responsible的风险
    all_risk_items = owner_risk_items + responsible_risk_items
    
    # 如果筛选了负责人，只显示该负责人的风险，不再添加下属的风险
    # 如果筛选了部门，只显示该部门的风险
    # 如果没有筛选，才添加下属的风险
    if not filter_responsible_person_id and not filter_department_id:
        if is_manager and subordinates.exists():
            all_risk_items.extend(get_subordinates_risk_items(
                subordinates,
                limit=10,
                filter_department_id=filter_department_id,
                filter_responsible_person_id=filter_responsible_person_id,
                filter_start_date=filter_start_date,
                filter_end_date=filter_end_date
            ))
    
    # 排序并去重（基于对象ID）
    seen_objects = set()
    unique_risk_items = []
    for item in all_risk_items:
        obj = item.get('object')
        if obj:
            obj_key = (item['type'], obj.id)
            if obj_key not in seen_objects:
                seen_objects.add(obj_key)
                unique_risk_items.append(item)
    
    # 重新排序
    unique_risk_items.sort(key=lambda x: x.get('days_overdue', 0), reverse=True)
    
    # 全部分类的待办项：合并所有相关待办
    # 使用完整的 user_todos 变量（包含我负责的 + 我协作的），而不是从 context 中获取（只包含5条）
    if 'user_todos' not in locals():
        user_todos = context.get('user_todos', [])
    # 将 user_todos 转换为统一的格式
    all_category_todos = []
    for todo in user_todos:
        todo_item = {
            'title': todo.get('title', ''),
            'description': todo.get('description', ''),
            'url': todo.get('url', '#'),
            'type': todo.get('type', ''),
            'priority': todo.get('priority', 'medium'),
            'deadline': todo.get('deadline'),
            'is_overdue': todo.get('is_overdue', False),
            'overdue_days': todo.get('overdue_days', 0),
            'meta': todo.get('meta', todo.get('description', '')),
        }
        if todo.get('is_db_todo'):
            todo_item['type'] = 'db_todo'
            try:
                todo_obj = todo.get('object')
                if todo_obj and hasattr(todo_obj, 'id'):
                    todo_item['db_todo_id'] = todo_obj.id
                    todo_item['db_todo_owner_id'] = getattr(todo_obj, 'user_id', None)
                    todo_item['db_todo_auto_generated'] = bool(getattr(todo_obj, 'auto_generated', True))
            except Exception:
                pass
        all_category_todos.append(todo_item)
    
    # 如果筛选了负责人，只显示该负责人的待办，不再添加下属的待办
    # 如果筛选了部门，只显示该部门的待办
    # 如果没有筛选，才添加下属负责的待办和下属协作的待办
    if not filter_responsible_person_id and not filter_department_id:
        if is_manager and subordinates.exists():
            # 添加下属负责的待办
            for subordinate in subordinates[:10]:
                sub_todos = get_responsible_todos(
                    subordinate,
                    filter_department_id=filter_department_id,
                    filter_responsible_person_id=filter_responsible_person_id,
                    filter_start_date=filter_start_date,
                    filter_end_date=filter_end_date
                )
                for todo in sub_todos:
                    todo_item = {
                        'title': todo.get('title', ''),
                        'description': todo.get('description', ''),
                        'url': todo.get('url', '#'),
                        'type': todo.get('type', ''),
                        'priority': todo.get('priority', 'medium'),
                        'deadline': todo.get('deadline'),
                        'is_overdue': todo.get('is_overdue', False),
                        'overdue_days': todo.get('overdue_days', 0),
                        'meta': f'负责人：{subordinate.get_full_name() or subordinate.username}',
                    }
                    if todo.get('is_db_todo'):
                        todo_item['type'] = 'db_todo'
                        try:
                            todo_obj = todo.get('object')
                            if todo_obj and hasattr(todo_obj, 'id'):
                                todo_item['db_todo_id'] = todo_obj.id
                                todo_item['db_todo_owner_id'] = getattr(todo_obj, 'user_id', None)
                                todo_item['db_todo_auto_generated'] = bool(getattr(todo_obj, 'auto_generated', True))
                        except Exception:
                            pass
                    all_category_todos.append(todo_item)
            
            # 添加下属协作的待办
            for subordinate in subordinates[:10]:
                sub_collab_todos = get_user_todos(
                    subordinate,
                    filter_department_id=filter_department_id,
                    filter_responsible_person_id=filter_responsible_person_id,
                    filter_start_date=filter_start_date,
                    filter_end_date=filter_end_date
                )
                # 从下属的待办中筛选出协作的（参与者但不是负责人）
                for todo in sub_collab_todos:
                    obj = todo.get('object')
                    if obj:
                        # 如果是计划或目标，检查是否是协作的（参与者但不是负责人）
                        if hasattr(obj, 'participants') and subordinate in obj.participants.all():
                            if hasattr(obj, 'responsible_person') and obj.responsible_person != subordinate:
                                todo_item = {
                                    'title': todo.get('title', ''),
                                    'description': todo.get('description', ''),
                                    'url': todo.get('url', '#'),
                                    'type': todo.get('type', ''),
                                    'priority': todo.get('priority', 'medium'),
                                    'deadline': todo.get('deadline'),
                                    'is_overdue': todo.get('is_overdue', False),
                                    'overdue_days': todo.get('overdue_days', 0),
                                    'meta': f'下属协作：{subordinate.get_full_name() or subordinate.username}',
                                }
                                all_category_todos.append(todo_item)
    # 排序
    priority_order = {'high': 0, 'medium': 1, 'low': 2}
    all_category_todos.sort(key=lambda x: (priority_order.get(x.get('priority', 'low'), 2), x.get('deadline') or timezone.now()))
    
    # 全部分类的我的工作：合并所有相关计划和目标
    all_work_plans = list(my_work.get('my_plans', []))
    all_work_goals = list(my_work.get('my_goals', []))
    all_work_plans_count = my_work.get('my_plans_count', 0)
    all_work_goals_count = my_work.get('my_goals_count', 0)
    
    # 如果筛选了负责人，只显示该负责人的工作，不再添加下属的工作
    # 如果筛选了部门，只显示该部门的工作
    # 如果没有筛选，才添加下属负责的工作
    if not filter_responsible_person_id and not filter_department_id:
        if is_manager and subordinates.exists():
            # 添加下属负责的计划和目标
            for plan in subordinate_responsible_plans_qs.select_related('responsible_person', 'related_goal').order_by('-updated_time'):  # 显示全部，不限制数量
                all_work_plans.append(build_plan_dict(plan))
            for goal in subordinate_responsible_goals_qs.select_related('responsible_person', 'parent_goal').order_by('-updated_time'):  # 显示全部，不限制数量
                all_work_goals.append({
                    'title': goal.name,
                    'status': goal.get_status_display() if hasattr(goal, 'get_status_display') else str(getattr(goal, 'status', '')),
                    'completion_rate': float(getattr(goal, 'completion_rate', 0) or 0),
                    'url': reverse('plan_pages:strategic_goal_detail', args=[goal.id])
                })
            all_work_plans_count += subordinate_responsible_plans_qs.count()
            all_work_goals_count += subordinate_responsible_goals_qs.count()
    
    # 添加我协作的计划和目标
    for plan in my_collaboration_plans_qs.select_related('responsible_person', 'related_goal').order_by('-updated_time'):  # 显示全部，不限制数量
        plan_dict = build_plan_dict(plan)
        plan_dict['status'] = plan.get_status_display() if hasattr(plan, 'get_status_display') else str(getattr(plan, 'status', ''))
        all_work_plans.append(plan_dict)
    for goal in my_collaboration_goals_qs.select_related('responsible_person', 'parent_goal').order_by('-updated_time'):  # 显示全部，不限制数量
        all_work_goals.append({
            'title': goal.name,
            'status': goal.get_status_display() if hasattr(goal, 'get_status_display') else str(getattr(goal, 'status', '')),
            'completion_rate': float(getattr(goal, 'completion_rate', 0) or 0),
            'url': reverse('plan_pages:strategic_goal_detail', args=[goal.id])
        })
    all_work_plans_count += my_collaboration_plans_qs.count()
    all_work_goals_count += my_collaboration_goals_qs.count()
    
    # 如果筛选了负责人，只显示该负责人的工作，不再添加下属的工作
    # 如果筛选了部门，只显示该部门的工作
    # 如果没有筛选，才添加下属协作的工作
    if not filter_responsible_person_id and not filter_department_id:
        if is_manager and subordinates.exists():
            # 添加下属协作的计划和目标
            for plan in subordinate_collaboration_plans_qs.select_related('responsible_person', 'related_goal').order_by('-updated_time'):  # 显示全部，不限制数量
                all_work_plans.append(build_plan_dict(plan))
            for goal in subordinate_collaboration_goals_qs.select_related('responsible_person', 'parent_goal').order_by('-updated_time'):  # 显示全部，不限制数量
                all_work_goals.append({
                    'title': goal.name,
                    'status': goal.get_status_display() if hasattr(goal, 'get_status_display') else str(getattr(goal, 'status', '')),
                    'completion_rate': float(getattr(goal, 'completion_rate', 0) or 0),
                    'url': reverse('plan_pages:strategic_goal_detail', args=[goal.id])
                })
            all_work_plans_count += subordinate_collaboration_plans_qs.count()
            all_work_goals_count += subordinate_collaboration_goals_qs.count()
    
    # 按周期分类计划
    all_plans_by_period = categorize_plans_by_period(all_work_plans)
    
    all_work = {
        'my_plans': all_work_plans[:5],
        'my_plans_count': all_work_plans_count,
        'my_goals': all_work_goals[:5],
        'my_goals_count': all_work_goals_count,
        'participating_plans': [],
        'participating_plans_count': 0,
        'plans_by_period': all_plans_by_period,  # 按周期分类的计划
    }
    
    category_data['all'] = {
        'plan_status_dist': None,
        'goal_status_dist': None,
        'risk_items': unique_risk_items,  # 显示全部，不限制数量
        'todo_items': all_category_todos,  # 显示全部，不限制数量
        'my_work': all_work,
        'goal_cards': context.get('all_goal_cards', []),
        'plan_cards': context.get('all_plan_cards', []),
    }
    
    # 2. 我负责的分类的数据
    # 计划状态分布和目标状态分布已清除
    # 我负责的风险项和待办项（只包含我负责的）
    my_responsible_risk_items = get_responsible_risk_items(
        request.user,
        limit=1000,  # 获取全部风险项，不限制数量
        filter_department_id=filter_department_id,
        filter_responsible_person_id=filter_responsible_person_id,
        filter_start_date=filter_start_date,
        filter_end_date=filter_end_date
    )
    my_responsible_todos_raw = get_responsible_todos(
        request.user,
        filter_department_id=filter_department_id,
        filter_responsible_person_id=filter_responsible_person_id,
        filter_start_date=filter_start_date,
        filter_end_date=filter_end_date
    )
    
    # 处理待办项，添加responsible字段用于显示
    my_responsible_todos = []
    for todo in my_responsible_todos_raw:
        todo_item = {
            'title': todo.get('title', ''),
            'description': todo.get('description', ''),
            'url': todo.get('url', '#'),
            'type': todo.get('type', ''),
            'priority': todo.get('priority', 'medium'),
            'deadline': todo.get('deadline'),
            'is_overdue': todo.get('is_overdue', False),
            'overdue_days': todo.get('overdue_days', 0),
            'meta': todo.get('description', ''),
        }
        if todo.get('object'):
            obj = todo['object']
            if hasattr(obj, 'get_full_name'):
                todo_item['responsible'] = obj.get_full_name() or obj.username
            elif hasattr(obj, 'username'):
                todo_item['responsible'] = obj.username
        my_responsible_todos.append(todo_item)
    
    # 确保my_work包含plans_by_period（如果还没有）
    if 'plans_by_period' not in my_work:
        my_work['plans_by_period'] = categorize_plans_by_period(my_work.get('my_plans', []))
    
    category_data['mine'] = {
        'plan_status_dist': None,
        'goal_status_dist': None,
        'risk_items': my_responsible_risk_items,  # 显示全部，不限制数量
        'todo_items': my_responsible_todos,  # 显示全部，不限制数量
        'my_work': my_work,  # 使用现有的我的工作
        'goal_cards': context.get('my_goal_cards', []),
        'plan_cards': context.get('my_plan_cards', []),
    }
    
    # 3. 下属负责的分类的数据（仅部门负责人）
    if is_manager and subordinates.exists():
        # subordinate_responsible_plans_qs 和 subordinate_responsible_goals_qs 已在上面定义
        
        # 计划状态分布和目标状态分布已清除
        # 下属负责的风险项和待办项
        subordinate_responsible_risk_items = get_subordinates_risk_items(
            subordinates,
            limit=1000,  # 获取全部风险项，不限制数量
            filter_department_id=filter_department_id,
            filter_responsible_person_id=filter_responsible_person_id,
            filter_start_date=filter_start_date,
            filter_end_date=filter_end_date
        )
        
        # 下属负责的待办项（汇总所有下属的待办）
        subordinate_responsible_todos = []
        for subordinate in subordinates:  # 查询所有下属，不限制数量
            sub_todos = get_responsible_todos(
                subordinate,
                filter_department_id=filter_department_id,
                filter_responsible_person_id=filter_responsible_person_id,
                filter_start_date=filter_start_date,
                filter_end_date=filter_end_date
            )
            for todo in sub_todos:
                todo_item = {
                    'title': todo.get('title', ''),
                    'description': todo.get('description', ''),
                    'url': todo.get('url', '#'),
                    'type': todo.get('type', ''),
                    'priority': todo.get('priority', 'medium'),
                    'deadline': todo.get('deadline'),
                    'is_overdue': todo.get('is_overdue', False),
                    'overdue_days': todo.get('overdue_days', 0),
                    'meta': f'负责人：{subordinate.get_full_name() or subordinate.username}',
                }
                subordinate_responsible_todos.append(todo_item)
        
        # 按优先级和时间排序
        priority_order = {'high': 0, 'medium': 1, 'low': 2}
        subordinate_responsible_todos.sort(key=lambda x: (priority_order.get(x['priority'], 2), x.get('deadline') or timezone.now()))
        
        # 下属负责的工作
        subordinate_plans = list(subordinate_responsible_plans_qs.select_related('responsible_person', 'related_goal').order_by('-updated_time'))  # 显示全部，不限制数量
        subordinate_goals = list(subordinate_responsible_goals_qs.select_related('responsible_person', 'parent_goal').order_by('-updated_time'))  # 显示全部，不限制数量
        
        subordinate_plans_list = [build_plan_dict(p) for p in subordinate_plans]
        subordinate_work = {
            'my_plans': subordinate_plans_list,
            'my_plans_count': subordinate_responsible_plans_qs.count(),
            'my_goals': [{
                'title': g.name,
                'target_value': float(g.target_value) if g.target_value else 0,
                'current_value': float(g.current_value) if g.current_value else 0,
                'indicator_unit': g.indicator_unit or '',
                'completion_rate': float(getattr(g, 'completion_rate', 0) or 0),
                'progress_status': calculate_goal_progress_status(g),
                'url': reverse('plan_pages:strategic_goal_detail', args=[g.id])
            } for g in subordinate_goals],
            'my_goals_count': subordinate_responsible_goals_qs.count(),
            'participating_plans': [],
            'participating_plans_count': 0,
            'plans_by_period': categorize_plans_by_period(subordinate_plans_list),
        }
        
        category_data['subordinate'] = {
            'plan_status_dist': None,
            'goal_status_dist': None,
            'risk_items': subordinate_responsible_risk_items,  # 显示全部，不限制数量
            'todo_items': subordinate_responsible_todos,  # 显示全部，不限制数量
            'my_work': subordinate_work,
            'goal_cards': context.get('subordinate_goal_cards', []),
            'plan_cards': context.get('subordinate_plan_cards', []),
        }
    
    # 4. 我协作的分类的数据
    # my_collaboration_plans_qs 和 my_collaboration_goals_qs 已在上面定义
    
    # 计划状态分布和目标状态分布已清除
    # 我协作的风险项和待办项
    # 修复：计算用户参与但非负责人的进度落后计划和目标
    from backend.apps.plan_management.services.risk_query_service import (
        _build_risk_item, _is_progress_behind_goal, _is_progress_behind_plan,
        _get_goal_actual_progress, _get_plan_actual_progress,
        _calculate_time_progress_goal, _calculate_time_progress_plan
    )
    from django.utils import timezone
    now = timezone.now()
    today = now.date()
    
    my_collaboration_risk_items = []
    
    # 查询用户参与但非负责人的未完成计划
    collaboration_plans = Plan.objects.filter(
        participants=request.user,
        level='personal',
        status__in=['draft', 'published', 'accepted', 'in_progress']
    ).exclude(responsible_person=request.user).distinct().select_related('responsible_person').prefetch_related('progress_records')
    
    # 过滤出进度落后的计划
    for plan in collaboration_plans:
        if _is_progress_behind_plan(plan, now):
            actual_progress = _get_plan_actual_progress(plan)
            time_progress = _calculate_time_progress_plan(plan, now)
            my_collaboration_risk_items.append(_build_risk_item('plan_risk', plan, actual_progress, time_progress, plan.status))
    
    # 查询用户参与但非负责人的未完成目标
    collaboration_goals = StrategicGoal.objects.filter(
        participants=request.user,
        level='personal',
        status__in=['published', 'accepted', 'in_progress']
    ).exclude(responsible_person=request.user).distinct().select_related('responsible_person').prefetch_related('progress_records')
    
    # 过滤出进度落后的目标
    for goal in collaboration_goals:
        if _is_progress_behind_goal(goal, today):
            actual_progress = _get_goal_actual_progress(goal)
            time_progress = _calculate_time_progress_goal(goal, today)
            my_collaboration_risk_items.append(_build_risk_item('goal_risk', goal, actual_progress, time_progress, goal.status))
    
    # 排序（按优先级分数降序）
    my_collaboration_risk_items.sort(key=lambda x: x.get('_priority_score', 0), reverse=True)
    
    my_collaboration_todos = []
    
    # 我协作的工作
    my_collaboration_plans = my_collaboration_plans_qs.select_related('responsible_person', 'related_goal').order_by('-updated_time')[:5]
    my_collaboration_goals = my_collaboration_goals_qs.select_related('responsible_person', 'parent_goal').order_by('-updated_time')[:5]
    
    my_collaboration_plans_list = [build_plan_dict(p) for p in my_collaboration_plans]
    my_collaboration_work = {
        'my_plans': my_collaboration_plans_list,
        'my_plans_count': my_collaboration_plans_qs.count(),
        'my_goals': [{
            'title': g.name,
            'target_value': float(g.target_value) if g.target_value else 0,
            'current_value': float(g.current_value) if g.current_value else 0,
            'indicator_unit': g.indicator_unit or '',
            'completion_rate': float(getattr(g, 'completion_rate', 0) or 0),
            'progress_status': calculate_goal_progress_status(g),
            'url': reverse('plan_pages:strategic_goal_detail', args=[g.id])
        } for g in my_collaboration_goals],
        'my_goals_count': my_collaboration_goals_qs.count(),
        'participating_plans': [],
        'participating_plans_count': 0,
        'plans_by_period': categorize_plans_by_period(my_collaboration_plans_list),
    }
    
    category_data['collaboration'] = {
        'plan_status_dist': None,
        'goal_status_dist': None,
        'risk_items': my_collaboration_risk_items,  # 显示全部，不限制数量
        'todo_items': my_collaboration_todos,  # 显示全部，不限制数量
        'my_work': my_collaboration_work,
        'goal_cards': context.get('collaboration_goal_cards', []),
        'plan_cards': context.get('collaboration_plan_cards', []),
    }
    
    # 5. 下属协作的分类的数据（仅部门负责人）
    if is_manager and subordinates.exists():
        # subordinate_collaboration_plans_qs 和 subordinate_collaboration_goals_qs 已在上面定义
        
        # 计划状态分布和目标状态分布已清除
        # 下属协作的风险项和待办项
        # 修复：计算下属参与但非负责人的进度落后计划和目标
        subordinate_collaboration_risk_items = []
        
        # 使用已定义的查询集，筛选进度落后的项
        if subordinate_collaboration_plans_qs.exists():
            collaboration_plans = subordinate_collaboration_plans_qs.filter(
                level='personal',
                status__in=['draft', 'published', 'accepted', 'in_progress']
            ).distinct().select_related('responsible_person').prefetch_related('progress_records')
            
            for plan in collaboration_plans:
                if _is_progress_behind_plan(plan, now):
                    actual_progress = _get_plan_actual_progress(plan)
                    time_progress = _calculate_time_progress_plan(plan, now)
                    subordinate_collaboration_risk_items.append(_build_risk_item('plan_risk', plan, actual_progress, time_progress, plan.status))
        
        if subordinate_collaboration_goals_qs.exists():
            collaboration_goals = subordinate_collaboration_goals_qs.filter(
                level='personal',
                status__in=['published', 'accepted', 'in_progress']
            ).distinct().select_related('responsible_person').prefetch_related('progress_records')
            
            for goal in collaboration_goals:
                if _is_progress_behind_goal(goal, today):
                    actual_progress = _get_goal_actual_progress(goal)
                    time_progress = _calculate_time_progress_goal(goal, today)
                    subordinate_collaboration_risk_items.append(_build_risk_item('goal_risk', goal, actual_progress, time_progress, goal.status))
        
        # 排序（按优先级分数降序）
        subordinate_collaboration_risk_items.sort(key=lambda x: x.get('_priority_score', 0), reverse=True)
        
        subordinate_collaboration_todos = []
        
        # 下属协作的工作
        sub_collab_plans = list(subordinate_collaboration_plans_qs.select_related('responsible_person', 'related_goal').order_by('-updated_time'))  # 显示全部，不限制数量
        sub_collab_goals = list(subordinate_collaboration_goals_qs.select_related('responsible_person', 'parent_goal').order_by('-updated_time'))  # 显示全部，不限制数量
        
        sub_collab_plans_list = [build_plan_dict(p) for p in sub_collab_plans]
        subordinate_collaboration_work = {
            'my_plans': sub_collab_plans_list,
            'my_plans_count': subordinate_collaboration_plans_qs.count(),
            'my_goals': [{
                'title': g.name,
                'target_value': float(g.target_value) if g.target_value else 0,
                'current_value': float(g.current_value) if g.current_value else 0,
                'indicator_unit': g.indicator_unit or '',
                'completion_rate': float(getattr(g, 'completion_rate', 0) or 0),
                'progress_status': calculate_goal_progress_status(g),
                'url': reverse('plan_pages:strategic_goal_detail', args=[g.id])
            } for g in sub_collab_goals],
            'my_goals_count': subordinate_collaboration_goals_qs.count(),
            'participating_plans': [],
            'participating_plans_count': 0,
            'plans_by_period': categorize_plans_by_period(sub_collab_plans_list),
        }
        
        category_data['subordinate_collaboration'] = {
            'plan_status_dist': None,
            'goal_status_dist': None,
            'risk_items': subordinate_collaboration_risk_items,  # 显示全部，不限制数量
            'todo_items': subordinate_collaboration_todos,  # 显示全部，不限制数量
            'my_work': subordinate_collaboration_work,
            'goal_cards': context.get('subordinate_collaboration_goal_cards', []),
            'plan_cards': context.get('subordinate_collaboration_plan_cards', []),
        }
    
    context['category_data'] = category_data
    
    # 构建上下文
    page_context = _context(
        page_title="计划管理",
        page_icon="📅",
        description="数据展示中心 - 集中展示计划与目标的关键指标、趋势和风险",
        summary_cards=[],  # 不再使用旧的summary_cards
        sections=[],  # 不再使用旧的sections
        request=request,
    )
    
    # 合并所有数据
    page_context.update(context)
    
    # 添加 sidebar_nav（与左侧栏同源，确保对齐）
    page_context['sidebar_nav'] = _build_plan_management_sidebar_nav(permission_codes, request_path=request.path, active_id='plan_home')
    page_context['sidebar_title'] = '计划管理'
    page_context['sidebar_subtitle'] = 'Plan Management'
    
    return render(request, "plan_management/plan_management_home.html", page_context)

