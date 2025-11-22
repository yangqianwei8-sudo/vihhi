from rest_framework import serializers
from django.contrib.auth import authenticate, password_validation
from .models import User, Department, Role, DataDictionary, SystemConfig

class UserSerializer(serializers.ModelSerializer):
    department_name = serializers.CharField(source='department.name', read_only=True)
    
    class Meta:
        model = User
        fields = [
            'id', 'username', 'email', 'first_name', 'last_name', 
            'phone', 'department', 'department_name', 'position',
            'user_type', 'avatar', 'is_active', 'date_joined',
            'created_time', 'updated_time', 'notification_preferences'
        ]
        read_only_fields = ['date_joined', 'created_time', 'updated_time']
        extra_kwargs = {
            'password': {'write_only': True}
        }
    
    def create(self, validated_data):
        password = validated_data.pop('password', None)
        user = User.objects.create(**validated_data)
        if password:
            user.set_password(password)
            user.save()
        return user
    
    def update(self, instance, validated_data):
        password = validated_data.pop('password', None)
        for attr, value in validated_data.items():
            setattr(instance, attr, value)
        if password:
            instance.set_password(password)
        instance.save()
        return instance


class AccountProfileSerializer(serializers.ModelSerializer):
    phone = serializers.CharField(read_only=True)

    class Meta:
        model = User
        fields = [
            'first_name',
            'last_name',
            'email',
            'phone',
            'position',
            'avatar',
        ]

    def update(self, instance, validated_data):
        for attr, value in validated_data.items():
            setattr(instance, attr, value)
        # profile_completed 依据必填字段
        required_fields = [
            instance.first_name,
            instance.email,
            instance.position,
        ]
        instance.profile_completed = all(bool(field) for field in required_fields)
        save_fields = list(validated_data.keys()) + ['profile_completed']
        instance.save(update_fields=save_fields)
        return instance


class AccountNotificationSerializer(serializers.Serializer):
    inbox = serializers.BooleanField(required=False, default=True)
    email = serializers.BooleanField(required=False, default=False)
    wecom = serializers.BooleanField(required=False, default=False)

    def validate(self, attrs):
        if not any(attrs.get(key, False) for key in ['inbox', 'email', 'wecom']):
            raise serializers.ValidationError('至少需开启一种通知方式。')
        return attrs


class AccountPasswordChangeSerializer(serializers.Serializer):
    old_password = serializers.CharField(write_only=True)
    new_password = serializers.CharField(write_only=True)
    confirm_password = serializers.CharField(write_only=True)

    def validate_old_password(self, value):
        user = self.context['request'].user
        if not user.check_password(value):
            raise serializers.ValidationError('原密码不正确。')
        return value

    def validate(self, attrs):
        new_password = attrs.get('new_password')
        confirm_password = attrs.get('confirm_password')
        if new_password != confirm_password:
            raise serializers.ValidationError('两次输入的密码不一致。')
        password_validation.validate_password(new_password, self.context['request'].user)
        return attrs

class UserLoginSerializer(serializers.Serializer):
    username = serializers.CharField()
    password = serializers.CharField()
    
    def validate(self, data):
        username = data.get('username')
        password = data.get('password')
        
        if username and password:
            user = authenticate(username=username, password=password)
            if user:
                if user.is_active:
                    data['user'] = user
                else:
                    raise serializers.ValidationError('用户账户已被禁用')
            else:
                raise serializers.ValidationError('用户名或密码错误')
        else:
            raise serializers.ValidationError('必须提供用户名和密码')
        
        return data

class DepartmentSerializer(serializers.ModelSerializer):
    parent_name = serializers.CharField(source='parent.name', read_only=True)
    leader_name = serializers.CharField(source='leader.get_full_name', read_only=True)
    
    class Meta:
        model = Department
        fields = [
            'id', 'name', 'code', 'parent', 'parent_name', 
            'leader', 'leader_name', 'description', 'order',
            'is_active', 'created_time'
        ]

class RoleSerializer(serializers.ModelSerializer):
    class Meta:
        model = Role
        fields = '__all__'

class DataDictionarySerializer(serializers.ModelSerializer):
    parent_name = serializers.CharField(source='parent.name', read_only=True)
    
    class Meta:
        model = DataDictionary
        fields = '__all__'

class SystemConfigSerializer(serializers.ModelSerializer):
    class Meta:
        model = SystemConfig
        fields = '__all__'
