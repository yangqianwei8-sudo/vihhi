"""
P1 兼容层：
历史代码引用 plan_management.filters.*，但原实现缺失。
此处仅提供最小实现，禁止在 P1 扩展复杂过滤逻辑。
"""
from dataclasses import dataclass
from django.db.models import Q
from django.utils import timezone
from datetime import timedelta


@dataclass
class ListFilterSpec:
    """列表筛选规格"""
    range: str = None
    mine: bool = False
    participating: bool = False
    overdue: bool = False

    @classmethod
    def from_params(cls, params, allow_overdue=False):
        """从查询参数构建"""
        return cls(
            range=params.get('range'),
            mine=params.get('mine') == '1',
            participating=params.get('participating') == '1',
            overdue=params.get('overdue') == '1' if allow_overdue else False,
        )


def apply_range(qs, field_name, range_value):
    """应用时间范围筛选"""
    if not range_value:
        return qs
    
    now = timezone.now()
    if range_value == 'week':
        start = (now - timedelta(days=now.weekday())).replace(hour=0, minute=0, second=0, microsecond=0)
        return qs.filter(**{f"{field_name}__gte": start})
    elif range_value == 'month':
        start = now.replace(day=1, hour=0, minute=0, second=0, microsecond=0)
        return qs.filter(**{f"{field_name}__gte": start})
    return qs


def apply_mine_participating(qs, user, mine, participating):
    """应用"我负责/我参与"筛选"""
    if mine:
        qs = qs.filter(responsible_person=user)
    if participating:
        qs = qs.filter(participants=user)
    return qs


def apply_overdue(qs, overdue):
    """应用逾期筛选"""
    if not overdue:
        return qs
    now = timezone.now()
    return qs.filter(end_time__lt=now, status__in=['draft', 'in_progress'])

