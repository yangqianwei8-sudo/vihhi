from rest_framework import viewsets, permissions, status, mixins
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.exceptions import PermissionDenied
from rest_framework.parsers import MultiPartParser, FormParser
from django.db.models import Q, Count, Sum
from django.utils import timezone
from django_filters.rest_framework import DjangoFilterBackend
from backend.apps.system_management.services import get_user_permission_codes
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
        if not (_has_permission(permission_set, 'project_center.view_all', 'project_center.configure_team')
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
        if not (_has_permission(permission_set, 'project_center.view_all', 'project_center.configure_team')
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
        if not (_has_permission(permission_set, 'project_center.view_all', 'project_center.configure_team')
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
        if not (_has_permission(permission_set, 'project_center.view_all', 'project_center.configure_team')
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
        if not (_has_permission(permission_set, 'project_center.view_all', 'project_center.configure_team')
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
        if not (_has_permission(permission_set, 'project_center.view_all', 'project_center.configure_team')
                or _user_is_project_member(user, project)):
            raise PermissionDenied('您无权创建该项目的开工通知。')
        serializer.save(created_by=user)

    @action(detail=True, methods=['post'], url_path='send')
    def send_notice(self, request, pk=None):
        notice = self.get_object()
        permission_set = get_user_permission_codes(request.user)
        if not (_has_permission(permission_set, 'project_center.view_all', 'project_center.configure_team')
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
        if not (_has_permission(permission_set, 'project_center.view_all', 'project_center.configure_team')
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
        if not (_has_permission(permission_set, 'project_center.view_all', 'project_center.configure_team')
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
