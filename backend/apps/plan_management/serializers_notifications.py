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
        - object_type == "plan" → /plan/plans/<object_id>/
        - object_type == "goal" → /plan/strategic-goals/<object_id>/
        - object_type == "todo" → /plan/todos/ (待办中心)
        """
        from django.urls import reverse
        
        if obj.object_type == "plan":
            try:
                return reverse('plan_pages:plan_detail', args=[obj.object_id])
            except:
                return f"/plan/plans/{obj.object_id}/"
        elif obj.object_type == "goal":
            try:
                return reverse('plan_pages:strategic_goal_detail', args=[obj.object_id])
            except:
                return f"/plan/strategic-goals/{obj.object_id}/"
        elif obj.object_type == "todo":
            try:
                return reverse('plan_pages:plan_management_home')
            except:
                return "/plan/"
        else:
            return ""

