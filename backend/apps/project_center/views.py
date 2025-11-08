from rest_framework import viewsets, permissions, status
from rest_framework.decorators import action
from rest_framework.response import Response
from django.db.models import Q, Count, Sum
from django_filters.rest_framework import DjangoFilterBackend
from .models import Project, ProjectTeam, PaymentPlan, ProjectMilestone, ProjectDocument, ProjectArchive
from .serializers import (
    ProjectSerializer, ProjectCreateSerializer, ProjectTeamSerializer,
    PaymentPlanSerializer, ProjectMilestoneSerializer, ProjectDocumentSerializer,
    ProjectArchiveSerializer
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
            'project_manager', 'created_by', 'client'
        ).prefetch_related(
            'team_members', 'payment_plans', 'milestones', 'documents'
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
            'completed_payments': project.payment_plans.filter(status='completed').count(),
            'total_payments': project.payment_plans.count(),
            'total_planned_amount': project.payment_plans.aggregate(
                total=Sum('planned_amount')
            )['total'] or 0,
            'total_actual_amount': project.payment_plans.aggregate(
                total=Sum('actual_amount')
            )['total'] or 0,
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
        total_contract_amount = Project.objects.aggregate(
            total=Sum('contract_amount')
        )['total'] or 0
        
        dashboard_data = {
            'total_projects': total_projects,
            'active_projects': active_projects,
            'completed_projects': completed_projects,
            'user_managed_projects': user_managed_projects,
            'user_team_projects': user_team_projects,
            'total_contract_amount': float(total_contract_amount),
        }
        
        return Response(dashboard_data)
    
    @action(detail=False, methods=['get'])
    def get_next_number(self, request):
        """获取下一个项目编号序号"""
        import datetime
        from django.db.models import Max
        
        year = request.query_params.get('year', str(datetime.datetime.now().year))
        
        max_number = Project.objects.filter(
            project_number__startswith=f'VIH-{year}-'
        ).aggregate(max_num=Max('project_number'))['max_num']
        
        if max_number:
            try:
                seq = int(max_number.split('-')[-1]) + 1
            except (ValueError, IndexError):
                seq = 1
        else:
            seq = 1
        
        return Response({'next_seq': seq})

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

class PaymentPlanViewSet(viewsets.ModelViewSet):
    queryset = PaymentPlan.objects.all()
    serializer_class = PaymentPlanSerializer
    permission_classes = [permissions.IsAuthenticated]
    
    def get_queryset(self):
        queryset = PaymentPlan.objects.all()
        project_id = self.request.query_params.get('project')
        if project_id:
            queryset = queryset.filter(project_id=project_id)
        return queryset.select_related('project')

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
