from rest_framework import viewsets, permissions, status
from rest_framework.decorators import action
from rest_framework.response import Response
from django.contrib.auth import login, logout
from django.db.models import Q
from .models import User, Department, Role, DataDictionary, SystemConfig
from .serializers import (
    UserSerializer,
    UserLoginSerializer,
    DepartmentSerializer,
    RoleSerializer,
    DataDictionarySerializer,
    SystemConfigSerializer,
    AccountProfileSerializer,
    AccountNotificationSerializer,
    AccountPasswordChangeSerializer,
)

class UserViewSet(viewsets.ModelViewSet):
    queryset = User.objects.all()
    serializer_class = UserSerializer
    permission_classes = [permissions.IsAuthenticated]
    
    def get_queryset(self):
        queryset = User.objects.all()
        # 添加过滤条件
        department = self.request.query_params.get('department')
        user_type = self.request.query_params.get('user_type')
        search = self.request.query_params.get('search')
        
        if department:
            queryset = queryset.filter(department_id=department)
        if user_type:
            queryset = queryset.filter(user_type=user_type)
        if search:
            queryset = queryset.filter(
                Q(username__icontains=search) |
                Q(first_name__icontains=search) |
                Q(last_name__icontains=search) |
                Q(email__icontains=search)
            )
        return queryset
    
    @action(detail=False, methods=['post'], permission_classes=[permissions.AllowAny])
    def login(self, request):
        serializer = UserLoginSerializer(data=request.data)
        if serializer.is_valid():
            user = serializer.validated_data['user']
            login(request, user)
            return Response({
                'success': True,
                'user': UserSerializer(user).data,
                'message': '登录成功'
            })
        return Response({
            'success': False,
            'message': '登录失败',
            'errors': serializer.errors
        }, status=status.HTTP_400_BAD_REQUEST)
    
    @action(detail=False, methods=['post'])
    def logout(self, request):
        logout(request)
        return Response({'success': True, 'message': '退出成功'})
    
    @action(detail=False, methods=['get'])
    def profile(self, request):
        serializer = UserSerializer(request.user)
        return Response(serializer.data)

    @action(detail=False, methods=['put', 'patch'], url_path='me/profile')
    def update_profile(self, request):
        serializer = AccountProfileSerializer(
            instance=request.user,
            data=request.data,
            partial=True,
            context={'request': request},
        )
        serializer.is_valid(raise_exception=True)
        serializer.save()
        return Response({
            'success': True,
            'message': '账号资料已更新。',
            'data': serializer.data,
        })

    @action(detail=False, methods=['get', 'put'], url_path='me/notifications')
    def notification_preferences(self, request):
        if request.method.upper() == 'GET':
            return Response(request.user.get_notification_preferences())

        serializer = AccountNotificationSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        preferences = request.user.get_notification_preferences()
        preferences.update(serializer.validated_data)
        request.user.notification_preferences = preferences
        request.user.save(update_fields=['notification_preferences'])
        return Response({
            'success': True,
            'message': '通知偏好已保存。',
            'data': request.user.get_notification_preferences(),
        })

    @action(detail=False, methods=['post'], url_path='me/change-password')
    def change_password(self, request):
        serializer = AccountPasswordChangeSerializer(
            data=request.data,
            context={'request': request},
        )
        serializer.is_valid(raise_exception=True)
        new_password = serializer.validated_data['new_password']
        request.user.set_password(new_password)
        request.user.save(update_fields=['password'])
        logout(request)
        return Response({
            'success': True,
            'message': '密码更新成功，请重新登录。',
        })

class DepartmentViewSet(viewsets.ModelViewSet):
    queryset = Department.objects.all()
    serializer_class = DepartmentSerializer
    permission_classes = [permissions.IsAuthenticated]

class RoleViewSet(viewsets.ModelViewSet):
    queryset = Role.objects.all()
    serializer_class = RoleSerializer
    permission_classes = [permissions.IsAuthenticated]

class DataDictionaryViewSet(viewsets.ModelViewSet):
    queryset = DataDictionary.objects.all()
    serializer_class = DataDictionarySerializer
    permission_classes = [permissions.IsAuthenticated]
    
    def get_queryset(self):
        queryset = DataDictionary.objects.all()
        dict_type = self.request.query_params.get('type')
        if dict_type:
            queryset = queryset.filter(dict_type=dict_type)
        return queryset
    
    @action(detail=False, methods=['get'])
    def types(self, request):
        types = DataDictionary.DICT_TYPE_CHOICES
        return Response([{'value': t[0], 'label': t[1]} for t in types])

class SystemConfigViewSet(viewsets.ModelViewSet):
    queryset = SystemConfig.objects.all()
    serializer_class = SystemConfigSerializer
    permission_classes = [permissions.IsAuthenticated]
    
    @action(detail=False, methods=['get'], url_path='by-key/(?P<key>[^/.]+)')
    def by_key(self, request, key=None):
        try:
            config = SystemConfig.objects.get(key=key)
            serializer = self.get_serializer(config)
            return Response(serializer.data)
        except SystemConfig.DoesNotExist:
            return Response(
                {'error': f'配置项 {key} 不存在'},
                status=status.HTTP_404_NOT_FOUND
            )
