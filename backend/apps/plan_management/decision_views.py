"""
计划决策 API 视图（P1 裁决模型 v2）
"""
from rest_framework import viewsets, status
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from django.shortcuts import get_object_or_404
from django.core.exceptions import PermissionDenied
from django_filters.rest_framework import DjangoFilterBackend

from backend.apps.plan_management.models import PlanDecision
from backend.apps.plan_management.services.plan_decisions import decide, PlanDecisionError
from backend.apps.plan_management.serializers import PlanDecisionSerializer


class PlanDecisionViewSet(viewsets.ReadOnlyModelViewSet):
    """计划决策列表视图（只读）"""
    permission_classes = [IsAuthenticated]
    serializer_class = PlanDecisionSerializer
    filter_backends = [DjangoFilterBackend]
    filterset_fields = ['plan', 'request_type', 'decision']
    
    def get_queryset(self):
        """获取查询集"""
        qs = PlanDecision.objects.select_related('plan', 'requested_by', 'decided_by').order_by('-requested_at')
        
        # 支持 pending=1 过滤（等价于 decided_at__isnull=True）
        pending = self.request.query_params.get('pending')
        if pending == '1':
            qs = qs.filter(decided_at__isnull=True)
        
        return qs


class PlanDecisionDecideAPIView(APIView):
    """计划决策裁决 API"""
    permission_classes = [IsAuthenticated]

    def post(self, request, decision_id: int):
        """
        裁决决策
        
        POST /api/plan/plan-decisions/{decision_id}/decide/
        Body: {
            "approve": true/false,
            "reason": "裁决原因（可选）"
        }
        """
        decision_obj = get_object_or_404(PlanDecision, id=decision_id)

        approve = request.data.get("approve")
        if approve not in [True, False, "true", "false", 1, 0, "1", "0"]:
            return Response({"success": False, "message": "approve 必须为 true/false"}, status=status.HTTP_400_BAD_REQUEST)
        approve_bool = approve in [True, "true", 1, "1"]

        try:
            decision_obj = decide(decision_id, request.user, approve=approve_bool, reason=request.data.get("reason"))
        except PermissionDenied as e:
            return Response({"success": False, "message": str(e)}, status=status.HTTP_403_FORBIDDEN)
        except PlanDecisionError as e:
            # P1 v2: 使用 409 Conflict 更语义化（重复请求/状态冲突）
            error_status = getattr(e, 'status_code', status.HTTP_409_CONFLICT)
            return Response({"success": False, "message": str(e)}, status=error_status)

        plan = decision_obj.plan
        return Response({
            "success": True,
            "plan_id": plan.id,
            "plan_status": plan.status,
            "decision": {
                "id": decision_obj.id,
                "request_type": decision_obj.request_type,
                "decision": decision_obj.decision,
                "decided_at": decision_obj.decided_at,
            }
        }, status=status.HTTP_200_OK)
