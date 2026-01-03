"""
诉讼管理模块工具函数
"""
from django.utils import timezone
from django.db.models import Sum, Count
from datetime import timedelta
from typing import List, Dict, Optional
from decimal import Decimal

from backend.apps.litigation_management.models import LitigationCase, LitigationTimeline, PreservationSeal, LitigationExpense


def get_case_statistics(cases_queryset) -> Dict:
    """
    获取案件统计信息
    
    Args:
        cases_queryset: 案件查询集
        
    Returns:
        包含统计信息的字典
    """
    total = cases_queryset.count()
    
    return {
        'total': total,
        'pending_filing': cases_queryset.filter(status='pending_filing').count(),
        'filed': cases_queryset.filter(status='filed').count(),
        'trial': cases_queryset.filter(status='trial').count(),
        'judged': cases_queryset.filter(status='judged').count(),
        'executing': cases_queryset.filter(status='executing').count(),
        'closed': cases_queryset.filter(status='closed').count(),
        'withdrawn': cases_queryset.filter(status='withdrawn').count(),
        'settled': cases_queryset.filter(status='settled').count(),
        'urgent': cases_queryset.filter(priority='urgent').count(),
        'high': cases_queryset.filter(priority='high').count(),
        'medium': cases_queryset.filter(priority='medium').count(),
        'low': cases_queryset.filter(priority='low').count(),
    }


def get_expense_statistics(cases_queryset) -> Dict:
    """
    获取费用统计信息
    
    Args:
        cases_queryset: 案件查询集
        
    Returns:
        包含费用统计信息的字典
    """
    expenses = LitigationExpense.objects.filter(case__in=cases_queryset)
    
    total_amount = expenses.aggregate(total=Sum('amount'))['total'] or Decimal('0')
    
    return {
        'total_amount': total_amount,
        'total_count': expenses.count(),
        'by_type': expenses.values('expense_type').annotate(
            total=Sum('amount'),
            count=Count('id')
        ),
        'by_status': expenses.values('payment_status').annotate(
            total=Sum('amount'),
            count=Count('id')
        ),
    }


def get_upcoming_timelines(cases_queryset, days: int = 7) -> List[LitigationTimeline]:
    """
    获取即将到期的时间节点
    
    Args:
        cases_queryset: 案件查询集
        days: 提前天数，默认7天
        
    Returns:
        即将到期的时间节点列表
    """
    today = timezone.now().date()
    end_date = today + timedelta(days=days)
    
    return LitigationTimeline.objects.filter(
        case__in=cases_queryset,
        reminder_enabled=True,
        timeline_date__gte=timezone.now(),
        timeline_date__lte=timezone.now() + timedelta(days=days),
        status__in=['pending', 'in_progress']
    ).order_by('timeline_date')


def get_expiring_preservation_seals(cases_queryset, days: int = 7) -> List[PreservationSeal]:
    """
    获取即将到期的保全续封
    
    Args:
        cases_queryset: 案件查询集
        days: 提前天数，默认7天
        
    Returns:
        即将到期的保全续封列表
    """
    today = timezone.now().date()
    end_date = today + timedelta(days=days)
    
    return PreservationSeal.objects.filter(
        case__in=cases_queryset,
        status='active',
        end_date__gte=today,
        end_date__lte=end_date
    ).order_by('end_date')


def calculate_case_duration(case: LitigationCase) -> Optional[int]:
    """
    计算案件持续时间（天数）
    
    Args:
        case: 案件对象
        
    Returns:
        持续时间（天数），如果无法计算则返回None
    """
    if not case.registration_date:
        return None
    
    end_date = case.closing_date or timezone.now().date()
    duration = (end_date - case.registration_date).days
    return duration if duration >= 0 else None


def get_case_progress(case: LitigationCase) -> Dict:
    """
    获取案件进度信息
    
    Args:
        case: 案件对象
        
    Returns:
        包含进度信息的字典
    """
    progress_steps = {
        'pending_filing': 0,
        'filed': 1,
        'trial': 2,
        'judged': 3,
        'executing': 4,
        'closed': 5,
        'withdrawn': 5,
        'settled': 5,
    }
    
    current_step = progress_steps.get(case.status, 0)
    total_steps = 5
    
    return {
        'current_step': current_step,
        'total_steps': total_steps,
        'progress_percentage': int((current_step / total_steps) * 100) if total_steps > 0 else 0,
        'status_label': case.get_status_display(),
    }


def format_case_number(case_number: str) -> str:
    """
    格式化案件编号显示
    
    Args:
        case_number: 案件编号
        
    Returns:
        格式化后的案件编号
    """
    if not case_number:
        return ''
    
    # LAW-20240101-0001 -> LAW-2024-01-01-0001
    parts = case_number.split('-')
    if len(parts) == 3 and len(parts[1]) == 8:
        date_part = parts[1]
        formatted_date = f"{date_part[:4]}-{date_part[4:6]}-{date_part[6:8]}"
        return f"{parts[0]}-{formatted_date}-{parts[2]}"
    
    return case_number

