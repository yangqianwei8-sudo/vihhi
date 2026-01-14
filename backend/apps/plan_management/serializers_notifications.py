from rest_framework import serializers
from .compat import get_approval_notification_model

ApprovalNotification = get_approval_notification_model()


class ApprovalNotificationSerializer(serializers.ModelSerializer):
    url = serializers.SerializerMethodField()
    
    class Meta:
        model = ApprovalNotification if ApprovalNotification else None
        fields = [
            "id",
            "title",
            "content",
            "object_type",
            "object_id",
            "event",
            "is_read",
            "created_at",
            "url",
        ]
        read_only_fields = fields
    
    def get_url(self, obj):
        """
        C3-3-3: 返回通知对应的详情页 URL
        - object_type == "plan" → /plan/plans/<object_id>/?next=/plan/notifications/
        - object_type == "goal" → /plan/strategic-goals/<object_id>/?next=/plan/notifications/
        """
        if obj.object_type == "plan":
            return f"/plan/plans/{obj.object_id}/?next=/plan/notifications/"
        elif obj.object_type == "goal":
            return f"/plan/strategic-goals/{obj.object_id}/?next=/plan/notifications/"
        else:
            return ""

