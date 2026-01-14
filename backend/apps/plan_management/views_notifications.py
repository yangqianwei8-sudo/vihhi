from rest_framework import generics, permissions, status
from rest_framework.response import Response
from rest_framework.views import APIView

from .compat import get_approval_notification_model, has_approval_notification
from .serializers_notifications import ApprovalNotificationSerializer

ApprovalNotification = get_approval_notification_model()


class NotificationListAPI(generics.ListAPIView):
    """
    GET /api/plan/notifications/?is_read=0|1&page=1
    只返回当前用户的通知。
    """
    permission_classes = [permissions.IsAuthenticated]
    serializer_class = ApprovalNotificationSerializer

    def get_queryset(self):
        if not has_approval_notification():
            from django.db import models
            return models.QuerySet.none()
        qs = ApprovalNotification.objects.filter(user=self.request.user).order_by("-created_at")

        is_read = self.request.query_params.get("is_read")
        if is_read in ("0", "1"):
            qs = qs.filter(is_read=(is_read == "1"))

        return qs


class NotificationUnreadCountAPI(APIView):
    """
    GET /api/plan/notifications/unread-count/
    -> {"unread": 3}
    """
    permission_classes = [permissions.IsAuthenticated]

    def get(self, request):
        unread = ApprovalNotification.objects.filter(user=request.user, is_read=False).count() if ApprovalNotification else 0
        return Response({"unread": unread})


class NotificationMarkReadAPI(APIView):
    """
    POST /api/plan/notifications/{id}/mark-read/
    只允许操作自己的通知；否则 404。
    """
    permission_classes = [permissions.IsAuthenticated]

    def post(self, request, pk: int):
        if not ApprovalNotification:
            return Response({"detail": "Not found."}, status=status.HTTP_404_NOT_FOUND)
        qs = ApprovalNotification.objects.filter(user=request.user, pk=pk)
        obj = qs.first()
        if not obj:
            return Response({"detail": "Not found."}, status=status.HTTP_404_NOT_FOUND)

        if not obj.is_read:
            obj.is_read = True
            obj.save(update_fields=["is_read"])

        return Response({"ok": True, "id": obj.pk, "is_read": True})


class NotificationMarkAllReadAPI(APIView):
    """
    POST /api/plan/notifications/mark-all-read/
    一键已读（可选但强烈建议做，成本低收益高）。
    """
    permission_classes = [permissions.IsAuthenticated]

    def post(self, request):
        updated = ApprovalNotification.objects.filter(user=request.user, is_read=False).update(is_read=True) if ApprovalNotification else 0
        return Response({"ok": True, "updated": updated})

