from rest_framework import viewsets, status
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from django_filters.rest_framework import DjangoFilterBackend
from rest_framework.filters import SearchFilter, OrderingFilter
from django.utils import timezone

from .models import DeliveryRecord, DeliveryFile, DeliveryFeedback, DeliveryTracking
from .serializers import (
    DeliveryRecordListSerializer,
    DeliveryRecordDetailSerializer,
    DeliveryRecordCreateSerializer,
    DeliveryFileSerializer,
    DeliveryFeedbackSerializer,
    DeliveryTrackingSerializer
)
from .services import (
    DeliveryEmailService,
    DeliveryTrackingService,
    DeliveryWarningService,
    DeliveryArchiveService
)


class DeliveryRecordViewSet(viewsets.ModelViewSet):
    """交付记录视图集"""
    permission_classes = [IsAuthenticated]
    filter_backends = [DjangoFilterBackend, SearchFilter, OrderingFilter]
    filterset_fields = ['delivery_method', 'status', 'priority', 'project', 'client', 'is_overdue', 'risk_level']
    search_fields = ['delivery_number', 'title', 'recipient_name', 'recipient_email']
    ordering_fields = ['created_at', 'deadline', 'sent_at', 'delivered_at']
    ordering = ['-created_at']
    
    def get_queryset(self):
        from backend.apps.system_management.services import get_user_permission_codes
        from backend.core.views import _permission_granted
        from django.db.models import Q
        
        queryset = DeliveryRecord.objects.all()
        
        # 根据权限过滤
        user = self.request.user
        permission_set = get_user_permission_codes(user)
        
        # 如果没有查看全部权限，只能查看自己创建的或负责项目的
        if not _permission_granted('delivery_center.view_all', permission_set):
            queryset = queryset.filter(
                Q(created_by=user) | 
                Q(project__team_members__user=user)
            ).distinct()
        
        # 使用 defer 排除不存在的 total_execution_amount 字段
        return queryset.select_related('project', 'client', 'created_by', 'sent_by', 'delivery_person').defer('client__total_execution_amount').prefetch_related('files', 'tracking_records', 'feedbacks')
    
    def get_serializer_class(self):
        if self.action == 'list':
            return DeliveryRecordListSerializer
        elif self.action == 'create':
            return DeliveryRecordCreateSerializer
        return DeliveryRecordDetailSerializer
    
    def create(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        instance = serializer.save()
        
        # 记录跟踪
        DeliveryTracking.objects.create(
            delivery_record=instance,
            event_type='submitted',
            event_description='交付记录已创建',
            operator=request.user
        )
        
        return Response(DeliveryRecordDetailSerializer(instance).data, status=status.HTTP_201_CREATED)
    
    @action(detail=True, methods=['post'])
    def submit(self, request, pk=None):
        """提交报送"""
        delivery = self.get_object()
        if delivery.status != 'draft':
            return Response({'error': '只能提交草稿状态的交付记录'}, status=status.HTTP_400_BAD_REQUEST)
        
        delivery.status = 'submitted'
        delivery.submitted_at = timezone.now()
        delivery.save()
        
        # 记录跟踪
        DeliveryTracking.objects.create(
            delivery_record=delivery,
            event_type='submitted',
            event_description='交付记录已报送',
            operator=request.user
        )
        
        return Response({'status': 'submitted', 'message': '交付记录已报送'})
    
    @action(detail=True, methods=['post'])
    def send(self, request, pk=None):
        """发送/寄出/送达"""
        delivery = self.get_object()
        
        if delivery.delivery_method == 'email':
            # 邮件发送
            success = DeliveryEmailService.send_delivery_email(delivery, user=request.user)
            if success:
                return Response({'status': 'sent', 'message': '邮件发送成功'})
            else:
                return Response({'status': 'failed', 'message': delivery.error_message}, status=status.HTTP_400_BAD_REQUEST)
        
        elif delivery.delivery_method == 'express':
            # 快递寄出
            express_company = request.data.get('express_company', '')
            express_number = request.data.get('express_number', '')
            express_fee = request.data.get('express_fee')
            
            if not express_number:
                return Response({'error': '请输入快递单号'}, status=status.HTTP_400_BAD_REQUEST)
            
            delivery.express_company = express_company
            delivery.express_number = express_number
            if express_fee:
                delivery.express_fee = express_fee
            delivery.status = 'in_transit'
            delivery.sent_at = timezone.now()
            delivery.sent_by = request.user
            delivery.save()
            
            # 记录跟踪
            DeliveryTracking.objects.create(
                delivery_record=delivery,
                event_type='sent',
                event_description=f'快递已寄出，单号：{express_number}',
                operator=request.user
            )
            
            return Response({'status': 'in_transit', 'message': '快递已寄出'})
        
        elif delivery.delivery_method == 'hand_delivery':
            # 送达
            delivery_person_id = request.data.get('delivery_person_id')
            delivery_notes = request.data.get('delivery_notes', '')
            
            if delivery_person_id:
                from django.contrib.auth import get_user_model
                User = get_user_model()
                try:
                    delivery.delivery_person = User.objects.get(id=delivery_person_id)
                except User.DoesNotExist:
                    pass
            
            delivery.delivery_notes = delivery_notes
            delivery.status = 'delivered'
            delivery.delivered_at = timezone.now()
            delivery.sent_by = request.user
            delivery.save()
            
            # 记录跟踪
            DeliveryTracking.objects.create(
                delivery_record=delivery,
                event_type='delivered',
                event_description='已送达',
                operator=request.user,
                notes=delivery_notes
            )
            
            return Response({'status': 'delivered', 'message': '已送达'})
        
        return Response({'error': '未知的交付方式'}, status=status.HTTP_400_BAD_REQUEST)
    
    @action(detail=True, methods=['post'])
    def tracking(self, request, pk=None):
        """更新跟踪状态"""
        delivery = self.get_object()
        event_type = request.data.get('event_type')
        event_description = request.data.get('event_description', '')
        location = request.data.get('location', '')
        
        if not event_type:
            return Response({'error': '请提供事件类型'}, status=status.HTTP_400_BAD_REQUEST)
        
        tracking = DeliveryTrackingService.update_tracking(
            delivery, event_type, event_description, location, request.user
        )
        
        return Response(DeliveryTrackingSerializer(tracking).data)
    
    @action(detail=True, methods=['post'])
    def feedback(self, request, pk=None):
        """提交客户反馈"""
        delivery = self.get_object()
        
        feedback = DeliveryFeedback.objects.create(
            delivery_record=delivery,
            feedback_type=request.data.get('feedback_type', 'received'),
            content=request.data.get('content', ''),
            feedback_by=request.data.get('feedback_by', ''),
            feedback_email=request.data.get('feedback_email', ''),
            feedback_phone=request.data.get('feedback_phone', '')
        )
        
        # 更新交付记录
        delivery.feedback_received = True
        delivery.feedback_content = feedback.content
        delivery.feedback_time = timezone.now()
        delivery.feedback_by = feedback.feedback_by
        
        # 如果反馈类型是确认，更新状态
        if feedback.feedback_type == 'confirmed':
            delivery.status = 'confirmed'
            delivery.confirmed_at = timezone.now()
        
        delivery.save()
        
        # 记录跟踪
        DeliveryTracking.objects.create(
            delivery_record=delivery,
            event_type='feedback',
            event_description=f'收到反馈：{feedback.get_feedback_type_display()}',
            operator=None
        )
        
        return Response(DeliveryFeedbackSerializer(feedback).data)
    
    @action(detail=True, methods=['post'])
    def archive(self, request, pk=None):
        """归档交付记录"""
        delivery = self.get_object()
        DeliveryArchiveService.archive_record(delivery)
        return Response({'status': 'archived', 'message': '交付记录已归档'})
    
    @action(detail=True, methods=['post'])
    def send_warning(self, request, pk=None):
        """发送预警通知"""
        delivery = self.get_object()
        DeliveryWarningService.send_warning_notification(delivery)
        return Response({'warning_sent': True, 'warning_times': delivery.warning_times})
    
    @action(detail=False, methods=['get'])
    def warnings(self, request):
        """获取风险预警列表"""
        queryset = self.filter_queryset(self.get_queryset().filter(is_overdue=True))
        
        risk_level = request.query_params.get('risk_level')
        if risk_level:
            queryset = queryset.filter(risk_level=risk_level)
        
        page = self.paginate_queryset(queryset)
        if page is not None:
            serializer = self.get_serializer(page, many=True)
            return self.get_paginated_response(serializer.data)
        
        serializer = self.get_serializer(queryset, many=True)
        return Response(serializer.data)
    
    @action(detail=False, methods=['get'])
    def statistics(self, request):
        """交付统计"""
        queryset = self.get_queryset()
        
        # 基本统计
        total_count = queryset.count()
        status_distribution = {}
        for status_code, status_label in DeliveryRecord.STATUS_CHOICES:
            status_distribution[status_code] = queryset.filter(status=status_code).count()
        
        # 文件统计
        total_files = DeliveryFile.objects.filter(delivery_record__in=queryset).count()
        total_size = sum(d.total_file_size for d in queryset)
        
        # 时间统计
        today = timezone.now().date()
        today_count = queryset.filter(created_at__date=today).count()
        
        return Response({
            'total_count': total_count,
            'status_distribution': status_distribution,
            'file_statistics': {
                'total_files': total_files,
                'total_size': total_size,
            },
            'time_statistics': {
                'today_count': today_count,
            }
        })

    @action(detail=False, methods=['get'])
    def project_recipients(self, request):
        """获取项目团队成员收件人信息"""
        project_id = request.query_params.get('project_id')
        if not project_id:
            return Response({'error': '请提供项目ID'}, status=status.HTTP_400_BAD_REQUEST)
        
        try:
            from backend.apps.production_management.models import Project
            project = Project.objects.get(id=project_id)
            
            recipients = []
            
            # 获取项目团队成员
            team_members = project.team_members.filter(is_active=True)
            for member in team_members:
                if member.user:
                    role_name = member.role.name if member.role else ''
                    if '甲方' in role_name or '项目负责人' in role_name:
                        recipients.append({
                            'type': 'client_project_manager',
                            'name': member.user.get_full_name() or member.user.username,
                            'email': getattr(member.user, 'email', ''),
                            'phone': getattr(member.user, 'phone', ''),
                            'role': role_name
                        })
                    elif '设计方' in role_name and '项目负责人' in role_name:
                        recipients.append({
                            'type': 'design_project_manager',
                            'name': member.user.get_full_name() or member.user.username,
                            'email': getattr(member.user, 'email', ''),
                            'phone': getattr(member.user, 'phone', ''),
                            'role': role_name
                        })
                    elif '设计方' in role_name and '专业负责人' in role_name:
                        recipients.append({
                            'type': 'design_professional_manager',
                            'name': member.user.get_full_name() or member.user.username,
                            'email': getattr(member.user, 'email', ''),
                            'phone': getattr(member.user, 'phone', ''),
                            'role': role_name
                        })
            
            return Response({'recipients': recipients})
            
        except Project.DoesNotExist:
            return Response({'error': '项目不存在'}, status=status.HTTP_404_NOT_FOUND)
        except Exception as e:
            return Response({'error': str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


class DeliveryFileViewSet(viewsets.ModelViewSet):
    """交付文件视图集"""
    permission_classes = [IsAuthenticated]
    serializer_class = DeliveryFileSerializer
    
    def get_queryset(self):
        delivery_id = self.request.query_params.get('delivery_id')
        if delivery_id:
            return DeliveryFile.objects.filter(delivery_record_id=delivery_id, is_deleted=False)
        return DeliveryFile.objects.filter(is_deleted=False)
    
    def perform_create(self, serializer):
        delivery_id = self.request.data.get('delivery_record')
        if delivery_id:
            try:
                delivery = DeliveryRecord.objects.get(id=delivery_id)
                instance = serializer.save(
                    delivery_record=delivery,
                    uploaded_by=self.request.user
                )
                # 更新交付记录的文件统计
                delivery.file_count = delivery.files.filter(is_deleted=False).count()
                delivery.total_file_size = sum(f.file_size for f in delivery.files.filter(is_deleted=False))
                delivery.save()
            except DeliveryRecord.DoesNotExist:
                pass
        else:
            serializer.save(uploaded_by=self.request.user)
