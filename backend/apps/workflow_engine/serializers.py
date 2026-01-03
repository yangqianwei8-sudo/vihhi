from rest_framework import serializers
from .models import AgentConversation, AgentMessage


class AgentMessageSerializer(serializers.ModelSerializer):
    """Agent消息序列化器"""
    
    class Meta:
        model = AgentMessage
        fields = [
            'id', 'role', 'content', 'metadata', 
            'sequence', 'created_time'
        ]
        read_only_fields = ['id', 'created_time']


class AgentConversationSerializer(serializers.ModelSerializer):
    """Agent对话会话序列化器"""
    messages = AgentMessageSerializer(many=True, read_only=True)
    message_count = serializers.SerializerMethodField()
    user_name = serializers.CharField(source='user.username', read_only=True)
    
    class Meta:
        model = AgentConversation
        fields = [
            'id', 'title', 'description', 'user', 'user_name',
            'metadata', 'is_active', 'is_archived',
            'created_time', 'updated_time', 'last_message_time',
            'messages', 'message_count'
        ]
        read_only_fields = ['id', 'created_time', 'updated_time', 'last_message_time']
    
    def get_message_count(self, obj):
        """获取消息数量"""
        return obj.messages.count()


class AgentConversationListSerializer(serializers.ModelSerializer):
    """Agent对话列表序列化器（简化版，不包含消息）"""
    message_count = serializers.SerializerMethodField()
    user_name = serializers.CharField(source='user.username', read_only=True)
    last_message_preview = serializers.SerializerMethodField()
    
    class Meta:
        model = AgentConversation
        fields = [
            'id', 'title', 'description', 'user', 'user_name',
            'is_active', 'is_archived',
            'created_time', 'updated_time', 'last_message_time',
            'message_count', 'last_message_preview'
        ]
        read_only_fields = ['id', 'created_time', 'updated_time', 'last_message_time']
    
    def get_message_count(self, obj):
        """获取消息数量"""
        return obj.messages.count()
    
    def get_last_message_preview(self, obj):
        """获取最后一条消息的预览"""
        last_message = obj.messages.order_by('-created_time').first()
        if last_message:
            preview = last_message.content[:100]  # 前100个字符
            if len(last_message.content) > 100:
                preview += '...'
            return preview
        return ''


class AgentConversationCreateSerializer(serializers.ModelSerializer):
    """创建Agent对话序列化器"""
    
    class Meta:
        model = AgentConversation
        fields = ['title', 'description', 'metadata']
    
    def create(self, validated_data):
        """创建对话时自动设置用户"""
        validated_data['user'] = self.context['request'].user
        return super().create(validated_data)


class AgentMessageCreateSerializer(serializers.ModelSerializer):
    """创建Agent消息序列化器"""
    
    class Meta:
        model = AgentMessage
        fields = ['conversation', 'role', 'content', 'metadata']
    
    def create(self, validated_data):
        """创建消息时自动设置序列号"""
        from django.db.models import Max
        conversation = validated_data['conversation']
        # 获取当前对话的最大序列号
        max_sequence = conversation.messages.aggregate(
            max_seq=Max('sequence')
        ).get('max_seq') or 0
        validated_data['sequence'] = max_sequence + 1
        return super().create(validated_data)

