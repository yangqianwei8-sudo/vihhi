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
        - 审批通知（event 为 submit/approve/reject）：跳转到审批详情页
        """
        from django.urls import reverse
        
        # 检查是否是审批通知（通过 event 类型判断）
        if obj.event in ['submit', 'approve', 'reject']:
            # 解析 object_id：格式可能是 "approval_<instance_id>:<business_object_id>" 或直接是业务对象ID
            object_id_str = str(obj.object_id)
            if object_id_str.startswith('approval_'):
                # 提取审批实例ID
                parts = object_id_str.split(':')
                if len(parts) >= 1:
                    approval_instance_id = parts[0].replace('approval_', '')
                    try:
                        return reverse('workflow_engine:approval_detail', args=[approval_instance_id])
                    except:
                        return f"/workflow/approvals/{approval_instance_id}/"
            # 如果没有找到审批实例ID，尝试根据业务对象类型跳转
            # 这里 object_id 可能是业务对象ID
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
            else:
                # 默认跳转到审批列表页
                try:
                    return reverse('workflow_engine:approval_list')
                except:
                    return "/workflow/approvals/"
        
        # 非审批通知，按原来的逻辑处理
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

