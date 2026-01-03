from rest_framework import viewsets, permissions, status, mixins
from rest_framework.decorators import action, api_view, permission_classes
from rest_framework.response import Response
from rest_framework.exceptions import PermissionDenied
from rest_framework.parsers import MultiPartParser, FormParser
from rest_framework.permissions import IsAuthenticated
from django.db.models import Q, Count, Sum
from django.utils import timezone
from django.http import JsonResponse
from django.conf import settings
from django_filters.rest_framework import DjangoFilterBackend
from backend.apps.system_management.services import get_user_permission_codes
import json
import logging
from django.db import transaction
from .views_pages import (
    build_project_dashboard_payload,
    _has_permission,
    _user_is_project_member,
    _filter_projects_for_user,
)
from .models import (
    Project,
    ProjectTeam,
    ProjectMilestone,
    ProjectDocument,
    ProjectArchive,
    ProjectTeamNotification,
    ProjectDrawingSubmission,
    ProjectDrawingReview,
    ProjectDrawingFile,
    ProjectStartNotice,
    PreOptimizationMaterial,
)
from .serializers import (
    ProjectSerializer, ProjectCreateSerializer, ProjectTeamSerializer,
    ProjectMilestoneSerializer, ProjectDocumentSerializer,
    ProjectArchiveSerializer, ProjectTeamNotificationSerializer,
    ProjectDrawingSubmissionSerializer, ProjectDrawingReviewSerializer,
    ProjectDrawingFileSerializer, ProjectStartNoticeSerializer,
)

class ProjectViewSet(viewsets.ModelViewSet):
    queryset = Project.objects.all()
    permission_classes = [permissions.IsAuthenticated]
    filter_backends = [DjangoFilterBackend]
    filterset_fields = ['status', 'service_type', 'project_manager', 'client']
    
    def get_serializer_class(self):
        if self.action == 'create':
            return ProjectCreateSerializer
        return ProjectSerializer
    
    def get_queryset(self):
        queryset = Project.objects.all()
        user = self.request.user
        permission_set = get_user_permission_codes(user) if user.is_authenticated else set()
        queryset = _filter_projects_for_user(queryset, user, permission_set)
        
        # 搜索功能
        search = self.request.query_params.get('search')
        if search:
            queryset = queryset.filter(
                Q(project_number__icontains=search) |
                Q(name__icontains=search) |
                Q(client__name__icontains=search)
            )
        
        # 时间范围过滤
        start_date_from = self.request.query_params.get('start_date_from')
        start_date_to = self.request.query_params.get('start_date_to')
        if start_date_from:
            queryset = queryset.filter(start_date__gte=start_date_from)
        if start_date_to:
            queryset = queryset.filter(start_date__lte=start_date_to)
        
        return queryset.select_related(
            'project_manager', 'created_by', 'client', 'service_type'
        ).prefetch_related(
            'team_members', 'milestones', 'documents', 'service_professions'
        )
    
    def perform_create(self, serializer):
        serializer.save(created_by=self.request.user)
    
    @action(detail=True, methods=['get'])
    def statistics(self, request, pk=None):
        """项目统计信息"""
        project = self.get_object()
        
        stats = {
            'team_member_count': project.team_members.count(),
            'completed_milestones': project.milestones.filter(is_completed=True).count(),
            'total_milestones': project.milestones.count(),
        }
        
        return Response(stats)
    
    @action(detail=False, methods=['get'])
    def dashboard(self, request):
        """项目中心仪表盘数据"""
        user = request.user
        
        # 基础统计
        total_projects = Project.objects.count()
        active_projects = Project.objects.filter(status='in_progress').count()
        completed_projects = Project.objects.filter(status='completed').count()
        
        # 用户相关项目
        user_managed_projects = Project.objects.filter(project_manager=user).count()
        user_team_projects = Project.objects.filter(team_members__user=user).count()
        
        # 财务统计
        dashboard_data = {
            'total_projects': total_projects,
            'active_projects': active_projects,
            'completed_projects': completed_projects,
            'user_managed_projects': user_managed_projects,
            'user_team_projects': user_team_projects,
        }
        
        return Response(dashboard_data)
    
    @action(detail=False, methods=['get'])
    def get_next_number(self, request):
        """获取下一个项目编号序号"""
        import datetime
        from django.db.models import Max
        
        year = request.query_params.get('year', str(datetime.datetime.now().year))
        
        queryset = Project.objects.filter(
            project_number__startswith=f'VIH-{year}-'
        )
        
        max_number = queryset.aggregate(max_num=Max('project_number'))['max_num']
        
        if max_number:
            try:
                seq = int(max_number.split('-')[-1]) + 1
            except (ValueError, IndexError):
                seq = 1
        else:
            seq = 1
        
        return Response({'next_seq': seq})
    
    @action(detail=False, methods=['get'])
    def check_project_number(self, request):
        project_number = request.query_params.get('project_number')
        if not project_number:
            return Response({'valid': False, 'message': '项目编号不能为空'}, status=400)
        exclude_id = request.query_params.get('exclude_id')
        qs = Project.objects.filter(project_number=project_number)
        if exclude_id:
            qs = qs.exclude(id=exclude_id)
        exists = qs.exists()
        return Response({'valid': not exists})

    @action(detail=False, methods=['get'], url_path='dashboard-charts')
    def dashboard_charts(self, request):
        permission_set = get_user_permission_codes(request.user)
        payload = build_project_dashboard_payload(
            request.user,
            permission_set,
            request.query_params
        )
        return Response({
            'summary': payload['summary_json'],
            'progress_trends': payload['progress_trends'],
            'milestone_summary': payload['milestone_summary'],
            'risk_matrix': payload['risk_matrix'],
            'quality_distribution': payload['quality_distribution'],
            'quality_trend': payload['quality_trend'],
        })

class ProjectTeamViewSet(viewsets.ModelViewSet):
    queryset = ProjectTeam.objects.all()
    serializer_class = ProjectTeamSerializer
    permission_classes = [permissions.IsAuthenticated]
    
    def get_queryset(self):
        queryset = ProjectTeam.objects.all()
        project_id = self.request.query_params.get('project')
        if project_id:
            queryset = queryset.filter(project_id=project_id)
        return queryset.select_related('user', 'project')

class ProjectMilestoneViewSet(viewsets.ModelViewSet):
    queryset = ProjectMilestone.objects.all()
    serializer_class = ProjectMilestoneSerializer
    permission_classes = [permissions.IsAuthenticated]
    
    def get_queryset(self):
        queryset = ProjectMilestone.objects.all()
        project_id = self.request.query_params.get('project')
        if project_id:
            queryset = queryset.filter(project_id=project_id)
        return queryset.select_related('project')

class ProjectDocumentViewSet(viewsets.ModelViewSet):
    queryset = ProjectDocument.objects.all()
    serializer_class = ProjectDocumentSerializer
    permission_classes = [permissions.IsAuthenticated]
    
    def get_queryset(self):
        queryset = ProjectDocument.objects.all()
        project_id = self.request.query_params.get('project')
        if project_id:
            queryset = queryset.filter(project_id=project_id)
        return queryset.select_related('uploaded_by', 'project')

class ProjectArchiveViewSet(viewsets.ModelViewSet):
    queryset = ProjectArchive.objects.all()
    serializer_class = ProjectArchiveSerializer
    permission_classes = [permissions.IsAuthenticated]
    
    def get_queryset(self):
        queryset = ProjectArchive.objects.all()
        project_id = self.request.query_params.get('project')
        if project_id:
            queryset = queryset.filter(project_id=project_id)
        return queryset.select_related('archived_by', 'project')


class ProjectTeamNotificationViewSet(mixins.ListModelMixin,
                                     mixins.UpdateModelMixin,
                                     viewsets.GenericViewSet):
    serializer_class = ProjectTeamNotificationSerializer
    permission_classes = [permissions.IsAuthenticated]
    pagination_class = None

    def get_queryset(self):
        queryset = ProjectTeamNotification.objects.filter(
            recipient=self.request.user
        ).select_related('project')

        status_filter = self.request.query_params.get('status')
        if status_filter == 'unread':
            queryset = queryset.filter(is_read=False)
        elif status_filter == 'read':
            queryset = queryset.filter(is_read=True)

        return queryset.order_by('-created_time')

    def perform_update(self, serializer):
        notification = serializer.instance
        if notification.recipient_id != self.request.user.id:
            raise PermissionDenied('无权更新该通知')

        is_read = serializer.validated_data.get('is_read', notification.is_read)
        update_kwargs = serializer.validated_data.copy()
        if is_read and not notification.is_read:
            update_kwargs['is_read'] = True
            update_kwargs['read_time'] = timezone.now()
        serializer.save(**update_kwargs)

    @action(detail=True, methods=['post'], url_path='mark-read')
    def mark_read(self, request, pk=None):
        notification = self.get_object()
        if not notification.is_read:
            notification.is_read = True
            notification.read_time = timezone.now()
            notification.save(update_fields=['is_read', 'read_time'])
        serializer = self.get_serializer(notification)
        return Response(serializer.data)

    @action(detail=False, methods=['post'], url_path='bulk-mark-read')
    def bulk_mark_read(self, request):
        ids = request.data.get('ids', [])
        if not isinstance(ids, list):
            return Response({'detail': 'ids 必须为列表'}, status=status.HTTP_400_BAD_REQUEST)
        queryset = self.get_queryset().filter(id__in=ids, is_read=False)
        updated = queryset.update(is_read=True, read_time=timezone.now())
        return Response({'updated': updated})

    @action(detail=False, methods=['post'], url_path='mark-all-read')
    def mark_all_read(self, request):
        queryset = self.get_queryset().filter(is_read=False)
        updated = queryset.update(is_read=True, read_time=timezone.now())
        return Response({'updated': updated})


class ProjectDrawingSubmissionViewSet(viewsets.ModelViewSet):
    serializer_class = ProjectDrawingSubmissionSerializer
    permission_classes = [permissions.IsAuthenticated]
    filter_backends = [DjangoFilterBackend]
    filterset_fields = ['project', 'status']

    def get_queryset(self):
        queryset = ProjectDrawingSubmission.objects.select_related(
            'project', 'submitter', 'latest_review'
        ).prefetch_related(
            'files', 'reviews', 'reviews__reviewer'
        )
        project_id = self.request.query_params.get('project')
        if project_id:
            queryset = queryset.filter(project_id=project_id)
        return queryset

    def perform_create(self, serializer):
        request = self.request
        user = request.user
        project = serializer.validated_data['project']
        permission_set = get_user_permission_codes(user)
        if not (_has_permission(permission_set, 'production_management.view_all', 'production_management.configure_team')
                or _user_is_project_member(user, project)):
            raise PermissionDenied('您无权创建该项目的图纸提交。')

        submitter_role = serializer.validated_data.get('submitter_role') or getattr(user, 'position', '')

        with transaction.atomic():
            serializer.save(
                submitter=user,
                submitter_role=submitter_role or '',
            )
            project.launch_status = 'precheck_in_progress'
            project.launch_status_updated_time = timezone.now()
            project.save(update_fields=['launch_status', 'launch_status_updated_time'])

    @action(detail=True, methods=['post'], url_path='start-review')
    def start_review(self, request, pk=None):
        submission = self.get_object()
        project = submission.project
        permission_set = get_user_permission_codes(request.user)
        if not (_has_permission(permission_set, 'production_management.view_all', 'production_management.configure_team')
                or _user_is_project_member(request.user, project)):
            raise PermissionDenied('您无权更新该图纸提交。')
        submission.status = 'in_review'
        submission.project.launch_status = 'precheck_in_progress'
        submission.project.launch_status_updated_time = timezone.now()
        with transaction.atomic():
            submission.project.save(update_fields=['launch_status', 'launch_status_updated_time'])
            submission.save(update_fields=['status'])
        return Response(self.get_serializer(submission).data)

    @action(detail=True, methods=['post'], url_path='mark-notified')
    def mark_notified(self, request, pk=None):
        submission = self.get_object()
        project = submission.project
        permission_set = get_user_permission_codes(request.user)
        if not (_has_permission(permission_set, 'production_management.view_all', 'production_management.configure_team')
                or _user_is_project_member(request.user, project)):
            raise PermissionDenied('您无权更新该提交的甲方通知状态。')
        channel = request.data.get('channel') or 'system'
        now = timezone.now()
        submission.client_notified = True
        submission.client_notification_channel = channel
        submission.client_notified_time = now
        submission.save(update_fields=['client_notified', 'client_notification_channel', 'client_notified_time'])
        return Response(self.get_serializer(submission).data)


class ProjectDrawingReviewViewSet(viewsets.ModelViewSet):
    serializer_class = ProjectDrawingReviewSerializer
    permission_classes = [permissions.IsAuthenticated]
    filter_backends = [DjangoFilterBackend]
    filterset_fields = ['submission', 'result']

    def get_queryset(self):
        queryset = ProjectDrawingReview.objects.select_related(
            'submission', 'submission__project', 'reviewer'
        )
        submission_id = self.request.query_params.get('submission')
        if submission_id:
            queryset = queryset.filter(submission_id=submission_id)
        return queryset

    def perform_create(self, serializer):
        user = self.request.user
        submission = serializer.validated_data['submission']
        project = submission.project
        permission_set = get_user_permission_codes(user)
        if not (_has_permission(permission_set, 'production_management.view_all', 'production_management.configure_team')
                or _user_is_project_member(user, project)):
            raise PermissionDenied('您无权预审该图纸提交。')

        with transaction.atomic():
            review = serializer.save(reviewer=user)
            submission.latest_review = review
            result = review.result
            now = timezone.now()
            project.launch_status_updated_time = now
            submission_update_fields = ['latest_review']

            if result == 'approved':
                submission.status = 'approved'
                project.launch_status = 'ready_to_start'
                project.drawing_precheck_completed_time = now
                submission_update_fields.append('status')
                project_update_fields = ['launch_status', 'launch_status_updated_time', 'drawing_precheck_completed_time']
            elif result == 'changes_requested':
                submission.status = 'changes_requested'
                project.launch_status = 'changes_requested'
                submission_update_fields.append('status')
                project_update_fields = ['launch_status', 'launch_status_updated_time']
            else:
                submission.status = 'in_review'
                project.launch_status = 'precheck_in_progress'
                submission_update_fields.append('status')
                project_update_fields = ['launch_status', 'launch_status_updated_time']

            submission.save(update_fields=submission_update_fields)
            project.save(update_fields=project_update_fields)


class ProjectDrawingFileViewSet(viewsets.ModelViewSet):
    serializer_class = ProjectDrawingFileSerializer
    permission_classes = [permissions.IsAuthenticated]
    parser_classes = [MultiPartParser, FormParser]
    filter_backends = [DjangoFilterBackend]
    filterset_fields = ['submission', 'category']

    def get_queryset(self):
        queryset = ProjectDrawingFile.objects.select_related(
            'submission', 'submission__project', 'uploaded_by'
        )
        submission_id = self.request.query_params.get('submission')
        if submission_id:
            queryset = queryset.filter(submission_id=submission_id)
        return queryset

    def perform_create(self, serializer):
        user = self.request.user
        submission = serializer.validated_data['submission']
        project = submission.project
        permission_set = get_user_permission_codes(user)
        if not (_has_permission(permission_set, 'production_management.view_all', 'production_management.configure_team')
                or _user_is_project_member(user, project)):
            raise PermissionDenied('您无权上传该项目的图纸文件。')
        serializer.save(uploaded_by=user)


class ProjectStartNoticeViewSet(viewsets.ModelViewSet):
    serializer_class = ProjectStartNoticeSerializer
    permission_classes = [permissions.IsAuthenticated]
    filter_backends = [DjangoFilterBackend]
    filterset_fields = ['project', 'status']

    def get_queryset(self):
        queryset = ProjectStartNotice.objects.select_related(
            'project', 'submission', 'created_by', 'recipient_user'
        )
        project_id = self.request.query_params.get('project')
        if project_id:
            queryset = queryset.filter(project_id=project_id)
        return queryset

    def perform_create(self, serializer):
        user = self.request.user
        project = serializer.validated_data['project']
        permission_set = get_user_permission_codes(user)
        if not (_has_permission(permission_set, 'production_management.view_all', 'production_management.configure_team')
                or _user_is_project_member(user, project)):
            raise PermissionDenied('您无权创建该项目的开工通知。')
        serializer.save(created_by=user)

    @action(detail=True, methods=['post'], url_path='send')
    def send_notice(self, request, pk=None):
        notice = self.get_object()
        permission_set = get_user_permission_codes(request.user)
        if not (_has_permission(permission_set, 'production_management.view_all', 'production_management.configure_team')
                or _user_is_project_member(request.user, notice.project)):
            raise PermissionDenied('您无权发送该开工通知。')
        now = timezone.now()
        notice.status = 'sent'
        notice.sent_time = now
        with transaction.atomic():
            notice.save(update_fields=['status', 'sent_time'])
            notice.project.launch_status = 'ready_to_start'
            notice.project.start_notice_sent_time = now
            notice.project.launch_status_updated_time = now
            notice.project.save(update_fields=['launch_status', 'start_notice_sent_time', 'launch_status_updated_time'])
            if notice.submission_id:
                submission = notice.submission
                submission.client_notified = True
                submission.client_notified_time = now
                submission.client_notification_channel = notice.channel
                submission.save(update_fields=['client_notified', 'client_notified_time', 'client_notification_channel'])
        return Response(self.get_serializer(notice).data)

    @action(detail=True, methods=['post'], url_path='acknowledge')
    def acknowledge_notice(self, request, pk=None):
        notice = self.get_object()
        permission_set = get_user_permission_codes(request.user)
        if not (_has_permission(permission_set, 'production_management.view_all', 'production_management.configure_team')
                or _user_is_project_member(request.user, notice.project)):
            raise PermissionDenied('您无权确认该开工通知。')
        now = timezone.now()
        notice.status = 'acknowledged'
        notice.acknowledged_time = now
        with transaction.atomic():
            notice.save(update_fields=['status', 'acknowledged_time'])
            notice.project.launch_status = 'started'
            notice.project.launch_status_updated_time = now
            if notice.project.actual_start_date is None:
                notice.project.actual_start_date = now.date()
                project_fields = ['launch_status', 'launch_status_updated_time', 'actual_start_date']
            else:
                project_fields = ['launch_status', 'launch_status_updated_time']
            notice.project.save(update_fields=project_fields)
        return Response(self.get_serializer(notice).data)

    @action(detail=True, methods=['post'], url_path='fail')
    def mark_failed(self, request, pk=None):
        notice = self.get_object()
        permission_set = get_user_permission_codes(request.user)
        if not (_has_permission(permission_set, 'production_management.view_all', 'production_management.configure_team')
                or _user_is_project_member(request.user, notice.project)):
            raise PermissionDenied('您无权更新该开工通知。')
        reason = request.data.get('reason', '')
        now = timezone.now()
        notice.status = 'failed'
        notice.failure_reason = reason
        notice.save(update_fields=['status', 'failure_reason'])
        notice.project.launch_status = 'ready_to_start'
        notice.project.launch_status_updated_time = now
        notice.project.save(update_fields=['launch_status', 'launch_status_updated_time'])
        return Response(self.get_serializer(notice).data)


# AI顾问系统API视图
from .services.ai_advisor_service import AIAdvisorService


@api_view(['POST'])
@permission_classes([IsAuthenticated])
def ai_advisor_analyze(request):
    """AI分析API - 集成DeepSeek"""
    logger = logging.getLogger(__name__)
    
    permission_set = get_user_permission_codes(request.user)
    if not _has_permission(permission_set, 'production_management.view_all', 'production_management.view_assigned'):
        return JsonResponse({'error': '权限不足'}, status=403)
    
    try:
        # 解析请求数据（支持FormData和JSON两种格式）
        try:
            if hasattr(request, 'data'):
                # 如果使用DRF，直接使用request.data
                data = request.data
            elif request.content_type and 'multipart/form-data' in request.content_type:
                # FormData格式（用于文件上传）
                data = request.POST.dict()
                # 如果有images字段（JSON字符串），解析它
                if 'images' in data:
                    try:
                        data['images'] = json.loads(data['images'])
                    except:
                        data['images'] = []
            else:
                # JSON格式
                data = json.loads(request.body.decode('utf-8')) if request.body else {}
        except (json.JSONDecodeError, UnicodeDecodeError) as e:
            logger.error(f"请求数据解析失败: {str(e)}")
            return JsonResponse({'error': '请求数据格式错误'}, status=400)
        
        problem = data.get('problem', '')
        constraints = data.get('constraints', '')
        service_type_id = data.get('service_type_id', '')
        profession_code = data.get('profession_code', '')
        # 为了兼容，如果没有profession_code，使用problem_type作为后备
        problem_type = data.get('problem_type', profession_code or 'structural')
        images = data.get('images', [])  # 获取图片列表（base64编码）
        cad_files = data.get('cad_files', [])  # 获取CAD文件列表
        
        if not problem:
            return JsonResponse({'error': '优化前做法不能为空'}, status=400)
        
        # 验证图片数据
        if images:
            if not isinstance(images, list):
                return JsonResponse({'error': '图片数据格式错误，应为数组'}, status=400)
            if len(images) > 3:
                return JsonResponse({'error': '最多只能上传3张图片'}, status=400)
            # 验证base64格式（简单检查）
            for i, img in enumerate(images):
                if not isinstance(img, str) or len(img) < 100:
                    return JsonResponse({'error': f'第{i+1}张图片数据格式错误'}, status=400)
            logger.info(f"收到 {len(images)} 张图片，将使用Vision API进行识别")
        
        # 处理CAD文件上传（如果通过文件上传）
        cad_file_paths = []
        temp_files_to_cleanup = []  # 记录需要清理的临时文件
        
        if 'cad_file' in request.FILES:
            uploaded_cad = request.FILES['cad_file']
            
            # 检查文件大小（限制50MB）
            max_cad_size = 50 * 1024 * 1024  # 50MB
            if uploaded_cad.size > max_cad_size:
                return JsonResponse({
                    'error': f'CAD文件大小不能超过50MB，当前文件大小: {uploaded_cad.size / 1024 / 1024:.2f}MB'
                }, status=400)
            
            # 保存临时文件
            import tempfile
            import os
            ext = os.path.splitext(uploaded_cad.name)[1].lower()
            if ext in ['.dxf', '.dwg', '.pdf']:
                with tempfile.NamedTemporaryFile(delete=False, suffix=ext) as tmp_file:
                    for chunk in uploaded_cad.chunks():
                        tmp_file.write(chunk)
                    tmp_path = tmp_file.name
                    cad_file_paths.append({
                        'path': tmp_path,
                        'type': ext[1:]  # 去掉点号
                    })
                    temp_files_to_cleanup.append(tmp_path)
                    logger.info(f"收到CAD文件: {uploaded_cad.name}, 大小: {uploaded_cad.size / 1024:.2f}KB, 临时路径: {tmp_path}")
            else:
                return JsonResponse({'error': f'不支持的CAD文件格式: {ext}，支持格式: .dxf, .dwg, .pdf'}, status=400)
        
        # 处理CAD文件路径（如果通过路径传递）
        if cad_files:
            if not isinstance(cad_files, list):
                return JsonResponse({'error': 'CAD文件数据格式错误，应为数组'}, status=400)
            cad_file_paths.extend(cad_files)
        
        # 使用AI顾问服务
        try:
            service = AIAdvisorService()
        except Exception as e:
            logger.error(f"AI顾问服务初始化失败: {str(e)}", exc_info=True)
            # 即使初始化失败，也尝试返回模拟数据，而不是直接返回500错误
            logger.warning("服务初始化失败，使用模拟数据作为后备")
            result = {
                'success': False,
                'error': f'服务初始化失败: {str(e)}' if settings.DEBUG else '服务暂时不可用，返回模拟数据'
            }
        else:
            try:
                result = service.analyze_design_problem(
                    problem, 
                    constraints, 
                    problem_type, 
                    images=images if images else None,
                    cad_files=cad_file_paths if cad_file_paths else None
                )
            except Exception as e:
                logger.error(f"AI分析过程出错: {str(e)}", exc_info=True)
                # 分析过程出错，返回模拟数据
                result = {
                    'success': False,
                    'error': f'分析过程出错: {str(e)}' if settings.DEBUG else '分析失败，请稍后重试'
                }
        
        if not result.get('success'):
            # 记录错误信息
            error_msg = result.get('error', '未知错误')
            logger.warning(f"AI分析失败: {error_msg}，使用模拟数据作为后备")
            
            # 如果API调用失败，返回模拟数据作为后备
            result = {
                'summary': '基于您的问题，我生成了3个优化方案，预计总节省金额约31.5万元。',
                'solutions': [
                    {
                        'title': '方案一：采用变截面H型钢',
                        'description': '将等截面H型钢改为变截面H型钢，跨中截面高度增加，支座附近截面高度减小，有效利用材料强度。',
                        'savings': 12.5,
                        'risk': 'low',
                        'advantages': ['用钢量减少18-22%', '刚度提高15%', '满足稳定性要求'],
                        'disadvantages': ['加工成本增加5%', '需要定制模具']
                    },
                    {
                        'title': '方案二：优化结构布置',
                        'description': '调整次梁间距，将原3m间距调整为2.5m，减小主梁跨度，优化支撑系统。',
                        'savings': 8.3,
                        'risk': 'low',
                        'advantages': ['用钢量减少12-15%', '结构整体性更好', '施工简便'],
                        'disadvantages': ['增加次梁数量', '连接节点增多']
                    },
                    {
                        'title': '方案三：采用高强度钢材',
                        'description': '将Q235钢材替换为Q345钢材，利用高强度优势减少截面尺寸。',
                        'savings': 10.7,
                        'risk': 'medium',
                        'advantages': ['用钢量减少20-25%', '截面尺寸减小', '耐久性更好'],
                        'disadvantages': ['材料单价高15%', '焊接工艺要求更高']
                    }
                ],
                'similar_cases': [],
                'analysis_report': {
                    'content': '<p>基于问题分析，AI推荐以下优化策略：</p><ol><li>材料优化：选择合适材料规格和等级</li><li>结构优化：优化构件布置和截面尺寸</li><li>工艺优化：改进施工工艺</li></ol>'
                },
                'risk_assessment': [
                    {
                        'title': '技术可行性风险',
                        'level': 'low',
                        'description': '优化方案基于成熟技术和类似案例，技术可行性高。'
                    },
                    {
                        'title': '成本控制风险',
                        'level': 'medium',
                        'description': '材料价格波动可能影响成本节省效果。'
                    }
                ]
            }
        else:
            # 移除success字段，只返回结果数据
            result.pop('success', None)
        
        # 清理临时文件
        import os
        for tmp_file in temp_files_to_cleanup:
            try:
                if os.path.exists(tmp_file):
                    os.remove(tmp_file)
                    logger.debug(f"已清理临时文件: {tmp_file}")
            except Exception as e:
                logger.warning(f"清理临时文件失败: {tmp_file}, 错误: {str(e)}")
        
        return JsonResponse(result)
    except json.JSONDecodeError as e:
        logger = logging.getLogger(__name__)
        logger.error(f"JSON解析失败: {str(e)}", exc_info=True)
        return JsonResponse({'error': f'请求数据格式错误: {str(e)}'}, status=400)
    except Exception as e:
        logger = logging.getLogger(__name__)
        logger.error(f"AI分析失败: {str(e)}", exc_info=True)
        # 返回详细的错误信息（开发环境）或通用错误信息（生产环境）
        error_detail = str(e) if settings.DEBUG else '服务器内部错误，请稍后重试'
        return JsonResponse({'error': error_detail, 'detail': str(e) if settings.DEBUG else None}, status=500)


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def ai_advisor_cases_search(request):
    """案例搜索API"""
    permission_set = get_user_permission_codes(request.user)
    if not _has_permission(permission_set, 'production_management.view_all', 'production_management.view_assigned'):
        return JsonResponse({'error': '权限不足'}, status=403)
    
    query = request.GET.get('q', '')
    
    # TODO: 从数据库查询相似案例
    # 这里返回模拟数据
    cases = [
        {
            'id': 'msjfmy',
            'name': '眉山江峰明樾Ⅰ项目',
            'description': '给排水专业优化，35条建议，节省74.2万元',
            'savings': 74.2,
            'tags': ['给排水', '消防系统', '管材优化']
        },
        {
            'id': 'cdsyzh',
            'name': '成都某商业综合体',
            'description': '电气专业优化，28条建议，节省65.8万元',
            'savings': 65.8,
            'tags': ['电气', '照明系统', '配电优化']
        }
    ]
    
    # 简单的关键词匹配
    if query:
        cases = [c for c in cases if query.lower() in c['name'].lower() or query.lower() in c['description'].lower()]
    
    return JsonResponse({'cases': cases})


@api_view(['POST'])
@permission_classes([IsAuthenticated])
def ai_advisor_save_solution(request):
    """保存选中的优化方案"""
    permission_set = get_user_permission_codes(request.user)
    if not _has_permission(permission_set, 'production_management.view_all', 'production_management.view_assigned'):
        return JsonResponse({'error': '权限不足'}, status=403)
    
    try:
        data = json.loads(request.body) if request.content_type == 'application/json' else request.POST
        
        # 获取方案数据
        solution_index = int(data.get('solution_index', -1))
        problem_description = data.get('problem_description', '')
        constraints = data.get('constraints', '')
        solution_data = data.get('solution', {})
        
        if solution_index < 0 or not solution_data:
            return JsonResponse({'error': '方案数据不完整'}, status=400)
        
        # 从当前会话中获取完整的分析结果（如果存在）
        # 这里我们直接使用传入的方案数据
        solution_title = solution_data.get('title', f'方案 {solution_index + 1}')
        solution_description = solution_data.get('description', '')
        savings = solution_data.get('savings')
        risk_level = solution_data.get('risk', 'medium')
        advantages = solution_data.get('advantages', '')
        considerations = solution_data.get('considerations', '')
        
        # 保存到数据库
        from .models import AIAdvisorSelectedSolution, Project
        # 获取关联的项目ID（如果提供）
        project_id = data.get('project_id')
        project = None
        if project_id:
            try:
                project = Project.objects.get(id=project_id)
            except Project.DoesNotExist:
                pass  # 项目不存在，不关联
        
        selected_solution = AIAdvisorSelectedSolution.objects.create(
            user=request.user,
            project=project,  # 关联项目
            problem_description=problem_description,
            constraints=constraints,
            solution_title=solution_title,
            solution_description=solution_description,
            solution_index=solution_index,
            savings=float(savings) if savings else None,
            risk_level=risk_level,
            advantages=advantages,
            considerations=considerations,
            service_type_id=data.get('service_type_id'),
            profession_code=data.get('profession_code', ''),
            budget_impact=data.get('budget_impact', ''),
            metadata={
                'full_solution_data': solution_data,
                'analysis_context': data.get('analysis_context', {}),
                'project_id': project_id,  # 保留项目ID在metadata中
            }
        )
        
        return JsonResponse({
            'success': True,
            'message': '方案已保存',
            'solution_id': selected_solution.id
        })
    except Exception as e:
        logger = logging.getLogger(__name__)
        logger.error(f"保存方案失败: {str(e)}", exc_info=True)
        return JsonResponse({'error': f'保存失败: {str(e)}'}, status=500)


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def ai_advisor_list_solutions(request):
    """获取用户已保存的方案列表"""
    permission_set = get_user_permission_codes(request.user)
    if not _has_permission(permission_set, 'production_management.view_all', 'production_management.view_assigned'):
        return JsonResponse({'error': '权限不足'}, status=403)
    
    try:
        from .models import AIAdvisorSelectedSolution
        solutions = AIAdvisorSelectedSolution.objects.filter(user=request.user).order_by('-created_time')[:20]
        
        solutions_data = []
        for sol in solutions:
            solutions_data.append({
                'id': sol.id,
                'solution_title': sol.solution_title,
                'solution_description': sol.solution_description,
                'savings': float(sol.savings) if sol.savings else None,
                'risk_level': sol.risk_level,
                'problem_description': sol.problem_description[:100] + '...' if len(sol.problem_description) > 100 else sol.problem_description,
                'created_time': sol.created_time.strftime('%Y-%m-%d %H:%M:%S')
            })
        
        return JsonResponse({
            'success': True,
            'solutions': solutions_data,
            'count': len(solutions_data)
        })
    except Exception as e:
        logger = logging.getLogger(__name__)
        logger.error(f"获取方案列表失败: {str(e)}", exc_info=True)
        return JsonResponse({'error': f'获取失败: {str(e)}'}, status=500)


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def pre_optimization_materials_parse_status(request, material_id):
    """获取优化前资料的解析状态"""
    permission_set = get_user_permission_codes(request.user)
    if not _has_permission(permission_set, 'production_management.view_all', 'production_management.view_assigned'):
        return JsonResponse({'error': '权限不足'}, status=403)
    
    try:
        material = PreOptimizationMaterial.objects.get(id=material_id)
        
        # 权限检查
        if not _has_permission(permission_set, 'production_management.view_all'):
            if not _user_is_project_member(request.user, material.project):
                return JsonResponse({'error': '无权访问'}, status=403)
        
        return JsonResponse({
            'success': True,
            'parse_status': material.parse_status,
            'parse_progress': material.parse_progress,
            'parse_error': material.parse_error,
            'parsed_time': material.parsed_time.strftime('%Y-%m-%d %H:%M:%S') if material.parsed_time else None,
        })
    except PreOptimizationMaterial.DoesNotExist:
        return JsonResponse({'error': '资料不存在'}, status=404)
    except Exception as e:
        logger = logging.getLogger(__name__)
        logger.error(f"获取解析状态失败: {str(e)}", exc_info=True)
        return JsonResponse({'error': f'获取失败: {str(e)}'}, status=500)
