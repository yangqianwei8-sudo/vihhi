"""
计划管理模块统计 API 视图
"""
from django.core.cache import cache
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated

from backend.apps.plan_management.stats import plan_stats, goal_stats

CACHE_TTL = 60  # 缓存 60 秒


def _cache_key(user, scope: str, params: dict):
    """生成缓存键"""
    # 超管用 "all"，普通用 company_id
    company_id = getattr(getattr(user, "profile", None), "company_id", None)
    scope_key = "all" if getattr(user, "is_superuser", False) else f"c{company_id or 'none'}"
    parts = [
        scope,
        scope_key,
        f"mine={params.get('mine', '')}",
        f"participating={params.get('participating', '')}",
        f"range={params.get('range', '')}",
    ]
    return "plan_mgmt_stats:" + ":".join(parts)


class PlanStatsAPI(APIView):
    """计划统计 API"""
    permission_classes = [IsAuthenticated]

    def get(self, request):
        params = request.query_params
        no_cache = params.get("no_cache") == "1"
        key = _cache_key(request.user, "plans", params)

        if not no_cache:
            cached = cache.get(key)
            if cached is not None:
                return Response({"cached": True, "data": cached})

        data = plan_stats(request.user, params)
        cache.set(key, data, CACHE_TTL)
        return Response({"cached": False, "data": data})


class GoalStatsAPI(APIView):
    """目标统计 API"""
    permission_classes = [IsAuthenticated]

    def get(self, request):
        params = request.query_params
        no_cache = params.get("no_cache") == "1"
        key = _cache_key(request.user, "goals", params)

        if not no_cache:
            cached = cache.get(key)
            if cached is not None:
                return Response({"cached": True, "data": cached})

        data = goal_stats(request.user, params)
        cache.set(key, data, CACHE_TTL)
        return Response({"cached": False, "data": data})

