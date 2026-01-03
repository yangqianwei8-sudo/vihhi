"""
诉讼管理通知确认视图
"""
import logging
from django.contrib.auth.decorators import login_required
from django.shortcuts import render, get_object_or_404, redirect
from django.contrib import messages
from django.utils import timezone
from django.db.models import Q

from backend.apps.system_management.services import get_user_permission_codes
from backend.core.views import _permission_granted
from backend.apps.litigation_management.models import LitigationNotificationConfirmation
from .views_pages import _context

logger = logging.getLogger(__name__)


@login_required
def notification_list(request):
    """通知列表"""
    permission_codes = get_user_permission_codes(request.user)
    
    if not _permission_granted('litigation_management.view', permission_codes):
        messages.error(request, '您没有权限查看通知')
        return redirect('litigation_pages:case_list')
    
    # 获取当前用户的通知
    notifications = LitigationNotificationConfirmation.objects.filter(
        recipient=request.user
    ).select_related('case', 'timeline', 'seal').order_by('-sent_at')
    
    # 筛选
    status_filter = request.GET.get('status', '')
    if status_filter:
        notifications = notifications.filter(status=status_filter)
    
    notification_type = request.GET.get('type', '')
    if notification_type:
        notifications = notifications.filter(notification_type=notification_type)
    
    # 统计
    total_count = notifications.count()
    pending_count = notifications.filter(status='pending').count()
    confirmed_count = notifications.filter(status='confirmed').count()
    escalated_count = notifications.filter(status='escalated').count()
    
    summary_cards = []
    
    context = _context(
        "通知列表",
        "📬",
        "诉讼管理通知确认",
        summary_cards=summary_cards,
        request=request
    )
    
    context.update({
        'notifications': notifications[:50],  # 限制显示数量
        'status_filter': status_filter,
        'notification_type': notification_type,
        'total_count': total_count,
        'pending_count': pending_count,
    })
    
    return render(request, 'litigation_management/notification_list.html', context)


@login_required
def notification_confirm(request, notification_id):
    """确认通知"""
    notification = get_object_or_404(
        LitigationNotificationConfirmation.objects.select_related('case', 'timeline', 'seal'),
        id=notification_id
    )
    
    # 检查权限：只能确认自己的通知
    if notification.recipient != request.user:
        messages.error(request, '您只能确认自己的通知')
        return redirect('litigation_pages:notification_list')
    
    if request.method == 'POST':
        try:
            notification.confirm(request.user)
            logger.info(f'用户 {request.user.username} 确认了通知 {notification.notification_title}')
            messages.success(request, '通知已确认')
            return redirect('litigation_pages:notification_list')
        except Exception as e:
            logger.error(f'确认通知失败: {str(e)}', exc_info=True)
            messages.error(request, f'确认失败：{str(e)}')
    
    context = _context(
        "确认通知",
        "✅",
        notification.notification_title,
        request=request
    )
    
    context.update({
        'notification': notification,
        'case': notification.case,
    })
    
    return render(request, 'litigation_management/notification_confirm.html', context)


@login_required
def notification_detail(request, notification_id):
    """通知详情"""
    notification = get_object_or_404(
        LitigationNotificationConfirmation.objects.select_related('case', 'timeline', 'seal'),
        id=notification_id
    )
    
    # 检查权限：只能查看自己的通知
    if notification.recipient != request.user:
        messages.error(request, '您只能查看自己的通知')
        return redirect('litigation_pages:notification_list')
    
    # 标记为已读（如果还未确认）
    if notification.status == 'pending':
        notification.mark_as_read()
    
    context = _context(
        "通知详情",
        "📬",
        notification.notification_title,
        request=request
    )
    
    context.update({
        'notification': notification,
        'case': notification.case,
    })
    
    return render(request, 'litigation_management/notification_detail.html', context)

