"""
Agent对话API视图
"""
from rest_framework import viewsets, permissions, status
from rest_framework.decorators import action
from rest_framework.response import Response
from django.db.models import Q, Max
from .models import AgentConversation, AgentMessage
from .serializers import (
    AgentConversationSerializer,
    AgentConversationListSerializer,
    AgentConversationCreateSerializer,
    AgentMessageSerializer,
    AgentMessageCreateSerializer,
)


class AgentConversationViewSet(viewsets.ModelViewSet):
    """Agent对话会话视图集"""
    permission_classes = [permissions.IsAuthenticated]
    
    def get_queryset(self):
        """获取当前用户的对话列表"""
        queryset = AgentConversation.objects.filter(user=self.request.user)
        
        # 筛选条件
        is_active = self.request.query_params.get('is_active')
        is_archived = self.request.query_params.get('is_archived')
        search = self.request.query_params.get('search')
        
        if is_active is not None:
            queryset = queryset.filter(is_active=is_active.lower() == 'true')
        
        if is_archived is not None:
            queryset = queryset.filter(is_archived=is_archived.lower() == 'true')
        
        if search:
            queryset = queryset.filter(
                Q(title__icontains=search) |
                Q(description__icontains=search)
            )
        
        return queryset.order_by('-last_message_time', '-created_time')
    
    def get_serializer_class(self):
        """根据操作选择不同的序列化器"""
        if self.action == 'list':
            return AgentConversationListSerializer
        elif self.action == 'create':
            return AgentConversationCreateSerializer
        return AgentConversationSerializer
    
    def perform_create(self, serializer):
        """创建对话时自动设置用户"""
        serializer.save(user=self.request.user)
    
    @action(detail=True, methods=['post'])
    def archive(self, request, pk=None):
        """归档对话"""
        conversation = self.get_object()
        conversation.is_archived = True
        conversation.is_active = False
        conversation.save()
        return Response({
            'success': True,
            'message': '对话已归档'
        })
    
    @action(detail=True, methods=['post'])
    def unarchive(self, request, pk=None):
        """取消归档对话"""
        conversation = self.get_object()
        conversation.is_archived = False
        conversation.is_active = True
        conversation.save()
        return Response({
            'success': True,
            'message': '对话已取消归档'
        })
    
    @action(detail=True, methods=['get'])
    def messages(self, request, pk=None):
        """获取对话的所有消息"""
        conversation = self.get_object()
        messages = conversation.messages.all().order_by('sequence', 'created_time')
        serializer = AgentMessageSerializer(messages, many=True)
        return Response(serializer.data)
    
    @action(detail=True, methods=['post'])
    def add_message(self, request, pk=None):
        """向对话添加消息"""
        conversation = self.get_object()
        serializer = AgentMessageCreateSerializer(
            data={
                **request.data,
                'conversation': conversation.id
            },
            context={'request': request}
        )
        if serializer.is_valid():
            message = serializer.save()
            # 更新对话的最后消息时间
            conversation.update_last_message_time()
            return Response(
                AgentMessageSerializer(message).data,
                status=status.HTTP_201_CREATED
            )
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
    
    @action(detail=False, methods=['get'])
    def recent(self, request):
        """获取最近的对话（不包含消息）"""
        queryset = self.get_queryset().filter(is_archived=False)[:10]
        serializer = AgentConversationListSerializer(queryset, many=True)
        return Response(serializer.data)


class AgentMessageViewSet(viewsets.ModelViewSet):
    """Agent消息视图集"""
    serializer_class = AgentMessageSerializer
    permission_classes = [permissions.IsAuthenticated]
    
    def get_queryset(self):
        """获取当前用户有权限访问的消息"""
        conversation_id = self.request.query_params.get('conversation')
        if conversation_id:
            # 检查用户是否有权限访问该对话
            try:
                conversation = AgentConversation.objects.get(
                    id=conversation_id,
                    user=self.request.user
                )
                return conversation.messages.all().order_by('sequence', 'created_time')
            except AgentConversation.DoesNotExist:
                return AgentMessage.objects.none()
        return AgentMessage.objects.none()
    
    def get_serializer_class(self):
        """根据操作选择不同的序列化器"""
        if self.action == 'create':
            return AgentMessageCreateSerializer
        return AgentMessageSerializer
    
    def perform_create(self, serializer):
        """创建消息时自动设置序列号"""
        conversation = serializer.validated_data['conversation']
        # 检查用户是否有权限
        if conversation.user != self.request.user:
            raise permissions.PermissionDenied('您没有权限向此对话添加消息')
        
        # 获取当前对话的最大序列号
        max_sequence = conversation.messages.aggregate(
            max_seq=Max('sequence')
        ).get('max_seq') or 0
        serializer.save(sequence=max_sequence + 1)
        
        # 更新对话的最后消息时间
        conversation.update_last_message_time()

