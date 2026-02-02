# 计划管理 - 辅助计算与校验函数
from decimal import Decimal
from django.db.models import Sum, Avg


def calculate_child_goals_summary(parent_goal):
    """计算子目标汇总信息（根据指标类型）"""
    child_goals = parent_goal.child_goals.all()
    if not child_goals.exists():
        return {
            'total_target_value': None,
            'total_current_value': None,
            'avg_completion_rate': None,
            'display_mode': 'none',
        }
    indicator_type = parent_goal.indicator_type
    if indicator_type == 'numeric':
        total_weight = child_goals.aggregate(Sum('weight'))['weight__sum'] or Decimal('0')
        if total_weight > 0:
            weighted_target_sum = sum(float(g.target_value or 0) * float(g.weight or 0) / 100.0 for g in child_goals)
            weighted_current_sum = sum(float(g.current_value or 0) * float(g.weight or 0) / 100.0 for g in child_goals)
            if abs(float(total_weight) - 100.0) > 0.01:
                weight_ratio = float(total_weight) / 100.0
                total_target = weighted_target_sum / weight_ratio if weight_ratio > 0 else 0
                total_current = weighted_current_sum / weight_ratio if weight_ratio > 0 else 0
                weighted_completion_sum = sum(float(g.completion_rate or 0) * float(g.weight or 0) / 100.0 for g in child_goals)
                avg_completion = weighted_completion_sum / weight_ratio if weight_ratio > 0 else 0
            else:
                total_target = weighted_target_sum
                total_current = weighted_current_sum
                avg_completion = sum(float(g.completion_rate or 0) * float(g.weight or 0) / 100.0 for g in child_goals)
        else:
            total_target = child_goals.aggregate(Sum('target_value'))['target_value__sum'] or Decimal('0')
            total_current = child_goals.aggregate(Sum('current_value'))['current_value__sum'] or Decimal('0')
            avg_completion = child_goals.aggregate(Avg('completion_rate'))['completion_rate__avg'] or Decimal('0')
        return {
            'total_target_value': Decimal(str(total_target)),
            'total_current_value': Decimal(str(total_current)),
            'avg_completion_rate': Decimal(str(avg_completion)),
            'display_mode': 'sum',
        }
    elif indicator_type == 'percentage':
        total_weight = child_goals.aggregate(Sum('weight'))['weight__sum'] or Decimal('0')
        if total_weight > 0:
            weighted_sum = sum(float(g.current_value or 0) * float(g.weight or 0) / 100.0 for g in child_goals)
            if abs(float(total_weight) - 100.0) > 0.01:
                weight_ratio = float(total_weight) / 100.0
                avg_current = weighted_sum / weight_ratio if weight_ratio > 0 else 0
            else:
                avg_current = weighted_sum
        else:
            avg_current = child_goals.aggregate(Avg('current_value'))['current_value__avg'] or Decimal('0')
        avg_completion = child_goals.aggregate(Avg('completion_rate'))['completion_rate__avg'] or Decimal('0')
        return {
            'total_target_value': None,
            'total_current_value': Decimal(str(avg_current)),
            'avg_completion_rate': avg_completion,
            'display_mode': 'average',
        }
    else:
        total_weight = child_goals.aggregate(Sum('weight'))['weight__sum'] or Decimal('0')
        if total_weight > 0:
            weighted_completion_sum = sum(float(g.completion_rate or 0) * float(g.weight or 0) / 100.0 for g in child_goals)
            if abs(float(total_weight) - 100.0) > 0.01:
                weight_ratio = float(total_weight) / 100.0
                avg_completion = weighted_completion_sum / weight_ratio if weight_ratio > 0 else 0
            else:
                avg_completion = weighted_completion_sum
        else:
            avg_completion = child_goals.aggregate(Avg('completion_rate'))['completion_rate__avg'] or Decimal('0')
        return {
            'total_target_value': None,
            'total_current_value': None,
            'avg_completion_rate': Decimal(str(avg_completion)),
            'display_mode': 'text',
        }


def calculate_child_plans_summary(parent_plan):
    """计算子计划汇总信息（计划通常使用百分比进度）"""
    child_plans = parent_plan.child_plans.all()
    if not child_plans.exists():
        return {'total_progress': None, 'avg_progress': None, 'display_mode': 'none'}
    avg_progress = child_plans.aggregate(Avg('progress'))['progress__avg'] or Decimal('0')
    return {'total_progress': None, 'avg_progress': avg_progress, 'display_mode': 'average'}


def calculate_goal_progress_status(goal):
    """计算目标进度状态（辅助函数）"""
    from datetime import date
    today = date.today()
    completion_progress = float(goal.completion_rate) if goal.completion_rate else 0
    if goal.end_date and goal.end_date < today:
        if completion_progress >= 100:
            return {'status': 'completed', 'label': '已完成', 'class': 'bg-success'}
        return {'status': 'overdue', 'label': '已逾期', 'class': 'bg-danger'}
    if goal.start_date and goal.start_date > today:
        return {'status': 'not_started', 'label': '未开始', 'class': 'bg-secondary'}
    if goal.start_date and goal.end_date:
        total_days = (goal.end_date - goal.start_date).days + 1
        elapsed_days = max((today - goal.start_date).days + 1, 0) if total_days > 0 else 0
        time_progress = min((elapsed_days / total_days) * 100, 100) if total_days > 0 else 0
    else:
        time_progress = 0
    progress_diff = completion_progress - time_progress
    if completion_progress >= 100:
        return {'status': 'ahead_completed', 'label': '提前完成', 'class': 'bg-success'}
    if progress_diff >= 10:
        return {'status': 'ahead', 'label': '提前', 'class': 'bg-info'}
    if progress_diff >= -10:
        return {'status': 'on_track', 'label': '正常', 'class': 'bg-primary'}
    if progress_diff >= -20:
        return {'status': 'behind', 'label': '滞后', 'class': 'bg-warning'}
    return {'status': 'seriously_behind', 'label': '严重滞后', 'class': 'bg-danger'}


def calculate_plan_progress_status(plan):
    """计算计划进度状态（辅助函数）"""
    from django.utils import timezone
    from datetime import date
    now = timezone.now()
    today = now.date()
    progress = float(getattr(plan, 'progress', 0) or 0)
    if plan.end_time:
        end_date = plan.end_time.date() if hasattr(plan.end_time, 'date') else plan.end_time
        if end_date < today:
            if progress >= 100:
                return {'status': 'completed', 'label': '已完成', 'class': 'bg-success'}
            return {'status': 'overdue', 'label': '已逾期', 'class': 'bg-danger'}
    if plan.start_time:
        start_date = plan.start_time.date() if hasattr(plan.start_time, 'date') else plan.start_time
        if start_date > today:
            return {'status': 'not_started', 'label': '未开始', 'class': 'bg-secondary'}
    if plan.start_time and plan.end_time:
        start_date = plan.start_time.date() if hasattr(plan.start_time, 'date') else plan.start_time
        end_date = plan.end_time.date() if hasattr(plan.end_time, 'date') else plan.end_time
        total_days = (end_date - start_date).days + 1
        elapsed_days = max((today - start_date).days + 1, 0) if total_days > 0 else 0
        time_progress = min((elapsed_days / total_days) * 100, 100) if total_days > 0 else 0
    else:
        time_progress = 0
    progress_diff = progress - time_progress
    if progress >= 100:
        return {'status': 'ahead_completed', 'label': '提前完成', 'class': 'bg-success'}
    if progress_diff >= 10:
        return {'status': 'ahead', 'label': '提前', 'class': 'bg-info'}
    if progress_diff >= -10:
        return {'status': 'on_track', 'label': '正常', 'class': 'bg-primary'}
    if progress_diff >= -20:
        return {'status': 'behind', 'label': '滞后', 'class': 'bg-warning'}
    return {'status': 'seriously_behind', 'label': '严重滞后', 'class': 'bg-danger'}


def _form_errors_plain(form):
    """从表单提取纯文本错误信息，避免 HTML 标签混入 messages。"""
    parts = []
    for field, errs in form.errors.items():
        f = form.fields.get(field)
        label = (f.label if f and hasattr(f, 'label') else None) or field
        for e in (list(errs) if errs else []):
            parts.append(f'{label}: {e}')
    return '; '.join(parts)


def _validate_plan_fields(plan):
    """验证计划的必填字段。返回 (is_valid, errors)。"""
    errors = []
    required_fields = [
        ('name', '计划名称'),
        ('level', '计划层级'),
        ('plan_period', '计划周期'),
        ('responsible_person', '负责人'),
        ('start_time', '开始时间'),
        ('end_time', '结束时间'),
        ('related_goal', '关联战略目标'),
    ]
    for field_name, field_label in required_fields:
        value = getattr(plan, field_name, None)
        if not value:
            errors.append({'field': field_name, 'label': field_label, 'message': f'{field_label}为必填项，请填写'})
    if not plan.content or not plan.content.strip():
        if not plan.child_plans.exists():
            errors.append({'field': 'content', 'label': '计划内容', 'message': '计划内容为必填项，请填写计划内容或添加计划项'})
    if not plan.plan_objective or not plan.plan_objective.strip():
        errors.append({'field': 'plan_objective', 'label': '计划目标', 'message': '计划目标为必填项，请填写'})
    if not plan.acceptance_criteria or not plan.acceptance_criteria.strip():
        errors.append({'field': 'acceptance_criteria', 'label': '验收标准', 'message': '验收标准为必填项，请填写'})
    if plan.participants.exists():
        if not plan.collaboration_plan or not plan.collaboration_plan.strip():
            errors.append({'field': 'collaboration_plan', 'label': '协作计划', 'message': '如果选择了协作人员，必须填写协作计划'})
    if plan.start_time and plan.end_time and plan.end_time < plan.start_time:
        errors.append({'field': 'end_time', 'label': '结束时间', 'message': '结束时间不能早于开始时间'})
    return len(errors) == 0, errors
