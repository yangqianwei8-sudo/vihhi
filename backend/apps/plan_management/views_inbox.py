"""
审批待办箱 API 视图
C2-1-3: 提供待我审批和我提交的两个只读 API
"""
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from rest_framework import status
from .models import Plan, StrategicGoal
from .serializers_inbox import PlanInboxItemSerializer, GoalInboxItemSerializer
from .utils import apply_company_scope


class InboxAPI(APIView):
    """
    待我审批 API
    
    GET /api/plan/inbox/
    
    返回待审批的 Plan 和 Goal（需要用户有对应的 approve 权限）
    """
    permission_classes = [IsAuthenticated]
    
    def get(self, request):
        """
        获取待我审批的列表
        
        逻辑：
        - 先走公司隔离
        - 只有有 approve_plan 权限的用户才能看到 Plan
        - 只有有 approve_strategicgoal 权限的用户才能看到 Goal
        - 只返回状态为 pending_approval 的记录
        """
        user = request.user
        
        # 初始化结果
        plans_data = {"count": 0, "results": []}
        goals_data = {"count": 0, "results": []}
        
        # 检查 Plan 审批权限
        can_approve_plan = user.is_superuser or user.has_perm("plan_management.approve_plan")
        if can_approve_plan:
            # P1: 不认 pending_approval 状态，改为空查询或 draft
            plans_qs = Plan.objects.none()  # 或改为 filter(status='draft')，根据业务需求
            # 应用公司隔离
            plans_qs = apply_company_scope(plans_qs, user)
            # 序列化
            plans_data = {
                "count": plans_qs.count(),
                "results": PlanInboxItemSerializer(plans_qs.order_by('-created_time'), many=True).data
            }
        
        # 检查 Goal 审批权限
        can_approve_goal = user.is_superuser or user.has_perm("plan_management.approve_strategicgoal")
        if can_approve_goal:
            goals_qs = StrategicGoal.objects.filter(status='pending_approval')
            # 应用公司隔离
            goals_qs = apply_company_scope(goals_qs, user)
            # 序列化
            goals_data = {
                "count": goals_qs.count(),
                "results": GoalInboxItemSerializer(goals_qs.order_by('-created_time'), many=True).data
            }
        
        return Response({
            "plans": plans_data,
            "goals": goals_data,
        }, status=status.HTTP_200_OK)


class MySubmissionsAPI(APIView):
    """
    我提交的 API
    
    GET /api/plan/my-submissions/
    
    返回我创建/提交的 Plan 和 Goal
    """
    permission_classes = [IsAuthenticated]
    
    def get(self, request):
        """
        获取我提交的列表
        
        逻辑：
        - 公司隔离：普通用户按公司过滤，超管不过滤
        - 口径：created_by=request.user
        """
        user = request.user
        
        # 查询我创建的 Plan
        plans_qs = Plan.objects.filter(created_by=user)
        # 应用公司隔离
        plans_qs = apply_company_scope(plans_qs, user)
        plans_data = {
            "count": plans_qs.count(),
            "results": PlanInboxItemSerializer(plans_qs.order_by('-created_time'), many=True).data
        }
        
        # 查询我创建的 Goal
        goals_qs = StrategicGoal.objects.filter(created_by=user)
        # 应用公司隔离
        goals_qs = apply_company_scope(goals_qs, user)
        goals_data = {
            "count": goals_qs.count(),
            "results": GoalInboxItemSerializer(goals_qs.order_by('-created_time'), many=True).data
        }
        
        return Response({
            "plans": plans_data,
            "goals": goals_data,
        }, status=status.HTTP_200_OK)

