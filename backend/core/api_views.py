from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.reverse import reverse
from django.shortcuts import render
from django.utils import timezone
from django.db.models import Q
from django.http import JsonResponse
from django.views.decorators.http import require_http_methods
from django.conf import settings
import json
import base64
import requests
import logging

logger = logging.getLogger(__name__)

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


@api_view(['POST'])
@permission_classes([IsAuthenticated])
def deepseek_seal_recognition(request):
    """
    DeepSeek盖章文件识别API
    接收图片文件，使用DeepSeek API进行盖章识别
    
    请求方式: POST
    请求参数:
        - file: 图片文件（multipart/form-data）
        - 或 image_url: 图片URL（可选）
    
    返回格式:
        {
            "success": true,
            "result": "识别结果文本",
            "seal_detected": true/false,
            "details": {...}
        }
    """
    try:
        # 检查API密钥配置
        api_key = getattr(settings, 'DEEPSEEK_API_KEY', '')
        if not api_key:
            return Response({
                'success': False,
                'error': 'DeepSeek API密钥未配置，请联系管理员'
            }, status=500)
        
        api_base_url = getattr(settings, 'DEEPSEEK_API_BASE_URL', 'https://api.deepseek.com')
        model = getattr(settings, 'DEEPSEEK_MODEL', 'deepseek-chat')
        
        # 获取图片数据
        image_data = None
        image_base64 = None
        
        # 方式1: 从文件上传获取
        if 'file' in request.FILES:
            uploaded_file = request.FILES['file']
            # 读取文件内容
            image_data = uploaded_file.read()
            # 转换为base64
            image_base64 = base64.b64encode(image_data).decode('utf-8')
        # 方式2: 从POST数据获取base64编码的图片
        elif 'image_base64' in request.data:
            image_base64 = request.data['image_base64']
        # 方式3: 从URL获取（需要下载）
        elif 'image_url' in request.data:
            image_url = request.data['image_url']
            try:
                response = requests.get(image_url, timeout=10)
                response.raise_for_status()
                image_data = response.content
                image_base64 = base64.b64encode(image_data).decode('utf-8')
            except Exception as e:
                return Response({
                    'success': False,
                    'error': f'无法下载图片: {str(e)}'
                }, status=400)
        else:
            return Response({
                'success': False,
                'error': '请提供图片文件(file)、base64编码图片(image_base64)或图片URL(image_url)'
            }, status=400)
        
        if not image_base64:
            return Response({
                'success': False,
                'error': '无法获取图片数据'
            }, status=400)
        
        # 构建DeepSeek API请求
        # 尝试使用视觉模型进行图像识别
        api_url = f"{api_base_url}/v1/chat/completions"
        
        # 构建提示词，专门用于盖章识别
        prompt = """请仔细分析这张图片，识别其中的盖章信息。请回答以下问题：
1. 图片中是否包含盖章？
2. 如果包含盖章，请描述：
   - 盖章的位置（大致位置，如：左上角、右下角等）
   - 盖章的类型（如：公章、合同章、财务章等）
   - 盖章的文字内容（如果可见）
   - 盖章的清晰度
   - 盖章是否完整
3. 如果图片中没有盖章，请说明。
4. 请提供任何其他相关的识别信息。

请用中文回答，格式清晰。"""
        
        # 构建请求体 - 尝试使用视觉输入格式（兼容OpenAI格式）
        # 注意：如果DeepSeek API不支持视觉输入，可能需要使用OCR预处理
        payload = {
            "model": model,
            "messages": [
                {
                    "role": "user",
                    "content": [
                        {
                            "type": "text",
                            "text": prompt
                        },
                        {
                            "type": "image_url",
                            "image_url": {
                                "url": f"data:image/jpeg;base64,{image_base64}"
                            }
                        }
                    ]
                }
            ],
            "temperature": 0.7,
            "max_tokens": 2000
        }
        
        # 发送请求到DeepSeek API
        headers = {
            "Authorization": f"Bearer {api_key}",
            "Content-Type": "application/json"
        }
        
        logger.info(f"调用DeepSeek API进行盖章识别，模型: {model}, API地址: {api_url}")
        response = requests.post(api_url, json=payload, headers=headers, timeout=30)
        
        # 检查响应状态
        if response.status_code != 200:
            error_detail = response.text
            logger.error(f"DeepSeek API返回错误: {response.status_code}, {error_detail}")
            # 如果是不支持视觉输入的错误，提供更友好的提示
            if response.status_code == 400:
                try:
                    error_json = response.json()
                    error_msg = error_json.get('error', {}).get('message', '')
                    if 'image' in error_msg.lower() or 'vision' in error_msg.lower():
                        return Response({
                            'success': False,
                            'error': '当前DeepSeek模型不支持视觉输入。建议使用OCR预处理图片后，再使用文本分析功能。',
                            'error_code': 'vision_not_supported',
                            'raw_error': error_msg
                        }, status=400)
                except:
                    pass
            
            response.raise_for_status()
        
        result = response.json()
        
        # 解析响应
        if 'choices' in result and len(result['choices']) > 0:
            recognition_text = result['choices'][0]['message']['content']
            
            # 简单判断是否检测到盖章（可以根据实际需求优化）
            seal_detected = any(keyword in recognition_text for keyword in [
                '盖章', '公章', '合同章', '财务章', '印章', '章印', '有章', '包含章'
            ])
            
            return Response({
                'success': True,
                'result': recognition_text,
                'seal_detected': seal_detected,
                'details': {
                    'model': model,
                    'usage': result.get('usage', {}),
                    'raw_response': result
                }
            })
        else:
            return Response({
                'success': False,
                'error': 'DeepSeek API返回格式异常',
                'raw_response': result
            }, status=500)
            
    except requests.exceptions.RequestException as e:
        logger.error(f'DeepSeek API请求失败: {e}', exc_info=True)
        return Response({
            'success': False,
            'error': f'API请求失败: {str(e)}'
        }, status=500)
    except Exception as e:
        logger.error(f'盖章识别处理失败: {e}', exc_info=True)
        return Response({
            'success': False,
            'error': f'处理失败: {str(e)}'
        }, status=500)
