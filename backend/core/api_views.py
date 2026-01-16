from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.reverse import reverse
from django.shortcuts import render
from django.utils import timezone
from django.db.models import Q
from django.http import JsonResponse
from django.views.decorators.http import require_http_methods
import json

@api_view(['GET'])
def api_root(request, format=None):
    """API 根目录，显示所有可用的 API 端点"""
    return Response({
        'system': reverse('system:user-list', request=request, format=format),
        'projects': reverse('project:project-list', request=request, format=format),
        'customers': reverse('customer:client-list', request=request, format=format),
        'message': '维海科技信息化管理平台 API',
        'version': '1.0.0'
    })

def api_docs(request):
    """API 文档页面"""
    return render(request, 'api/docs.html')


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def notification_list(request):
    """获取当前用户的通知列表"""
    from backend.apps.administrative_management.models import Announcement, AnnouncementRead
    from backend.apps.production_management.models import ProjectTeamNotification
    from backend.apps.litigation_management.models import LitigationNotificationConfirmation
    
    user = request.user
    notifications = []
    
    # 1. 获取公告通知（未读的）
    try:
        # 获取用户应该看到的公告（根据发布范围）
        announcements = Announcement.objects.filter(
            is_active=True,
            publish_date__lte=timezone.now().date()
        ).filter(
            Q(expiry_date__isnull=True) | Q(expiry_date__gte=timezone.now().date())
        )
        
        # 根据发布范围过滤
        user_departments = []
        user_roles = []
        if hasattr(user, 'department') and user.department:
            user_departments.append(user.department)
        if hasattr(user, 'roles'):
            user_roles = list(user.roles.all())
        
        filtered_announcements = []
        for ann in announcements:
            if ann.target_scope == 'all':
                filtered_announcements.append(ann)
            elif ann.target_scope == 'department' and user_departments:
                if any(dept in ann.target_departments.all() for dept in user_departments):
                    filtered_announcements.append(ann)
            elif ann.target_scope == 'specific_roles' and user_roles:
                if any(role in ann.target_roles.all() for role in user_roles):
                    filtered_announcements.append(ann)
            elif ann.target_scope == 'specific_users':
                if user in ann.target_users.all():
                    filtered_announcements.append(ann)
        
        # 检查哪些未读
        read_announcement_ids = set(
            AnnouncementRead.objects.filter(user=user).values_list('announcement_id', flat=True)
        )
        
        for ann in filtered_announcements[:10]:  # 最多10条
            is_read = ann.id in read_announcement_ids
            notifications.append({
                'id': f'announcement_{ann.id}',
                'type': 'announcement',
                'title': ann.title,
                'content': ann.content[:100] + '...' if len(ann.content) > 100 else ann.content,
                'priority': ann.priority,
                'is_read': is_read,
                'created_time': ann.publish_time.isoformat(),
                'url': f'/admin/announcement/{ann.id}/detail/',
                'icon': '📢',
            })
    except Exception as e:
        import logging
        logger = logging.getLogger(__name__)
        logger.warning(f'获取公告通知失败: {e}', exc_info=True)
    
    # 2. 获取项目团队通知（未读的）
    try:
        team_notifications = ProjectTeamNotification.objects.filter(
            recipient=user,
            is_read=False
        ).select_related('project', 'operator').order_by('-created_time')[:10]
        
        for notif in team_notifications:
            notifications.append({
                'id': f'team_{notif.id}',
                'type': 'team_notification',
                'title': notif.title,
                'content': notif.message[:100] + '...' if len(notif.message) > 100 else notif.message,
                'priority': 'normal',
                'is_read': False,
                'created_time': notif.created_time.isoformat(),
                'url': notif.action_url or '#',
                'icon': '👥',
            })
    except Exception as e:
        import logging
        logger = logging.getLogger(__name__)
        logger.warning(f'获取项目团队通知失败: {e}', exc_info=True)
    
    # 3. 获取诉讼通知（未确认的）
    try:
        litigation_notifications = LitigationNotificationConfirmation.objects.filter(
            recipient=user,
            status='pending'
        ).select_related('case').order_by('-sent_at')[:10]
        
        for notif in litigation_notifications:
            notifications.append({
                'id': f'litigation_{notif.id}',
                'type': 'litigation',
                'title': notif.notification_title,
                'content': notif.notification_content[:100] + '...' if len(notif.notification_content) > 100 else notif.notification_content,
                'priority': notif.urgency_level,
                'is_read': False,
                'created_time': notif.sent_at.isoformat(),
                'url': notif.get_absolute_url() if hasattr(notif, 'get_absolute_url') else '#',
                'icon': '⚖️',
            })
    except Exception as e:
        import logging
        logger = logging.getLogger(__name__)
        logger.warning(f'获取诉讼通知失败: {e}', exc_info=True)
    
    # 按时间排序
    notifications.sort(key=lambda x: x['created_time'], reverse=True)
    
    # 统计未读数量
    unread_count = sum(1 for n in notifications if not n['is_read'])
    
    return Response({
        'notifications': notifications[:20],  # 最多返回20条
        'unread_count': unread_count,
        'total_count': len(notifications),
    })


@require_http_methods(["POST"])
def mark_notification_read(request):
    """标记通知为已读"""
    from backend.apps.administrative_management.models import Announcement, AnnouncementRead
    from backend.apps.production_management.models import ProjectTeamNotification
    from backend.apps.litigation_management.models import LitigationNotificationConfirmation
    
    if not request.user.is_authenticated:
        return JsonResponse({'success': False, 'error': '未登录'}, status=401)
    
    # 尝试从POST数据或JSON body中获取notification_id
    notification_id = request.POST.get('notification_id')
    if not notification_id and request.body:
        try:
            body_data = json.loads(request.body)
            notification_id = body_data.get('notification_id')
        except (json.JSONDecodeError, AttributeError):
            pass
    if not notification_id:
        return JsonResponse({'success': False, 'error': '缺少通知ID'}, status=400)
    
    try:
        # 解析通知ID格式：type_id
        if notification_id.startswith('announcement_'):
            ann_id = int(notification_id.replace('announcement_', ''))
            announcement = Announcement.objects.get(id=ann_id)
            AnnouncementRead.objects.get_or_create(
                announcement=announcement,
                user=request.user
            )
        elif notification_id.startswith('team_'):
            notif_id = int(notification_id.replace('team_', ''))
            notif = ProjectTeamNotification.objects.get(id=notif_id, recipient=request.user)
            notif.is_read = True
            notif.read_time = timezone.now()
            notif.save()
        elif notification_id.startswith('litigation_'):
            notif_id = int(notification_id.replace('litigation_', ''))
            notif = LitigationNotificationConfirmation.objects.get(id=notif_id, recipient=request.user)
            notif.status = 'read_unconfirmed'
            notif.save()
        
        return JsonResponse({'success': True})
    except Exception as e:
        import logging
        logger = logging.getLogger(__name__)
        logger.error(f'标记通知已读失败: {e}', exc_info=True)
        return JsonResponse({'success': False, 'error': str(e)}, status=500)
