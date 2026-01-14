"""
计划管理模块API路由配置
"""
from django.urls import path
from rest_framework.routers import DefaultRouter
from . import views
from .views_stats import PlanStatsAPI, GoalStatsAPI
from .views_inbox import InboxAPI, MySubmissionsAPI
from .views_notifications import (
    NotificationListAPI,
    NotificationUnreadCountAPI,
    NotificationMarkReadAPI,
    NotificationMarkAllReadAPI,
)
from .decision_views import PlanDecisionDecideAPIView, PlanDecisionViewSet

app_name = 'plan'

router = DefaultRouter()
router.register(r'strategic-goals', views.StrategicGoalViewSet, basename='strategic-goals')
router.register(r'plans', views.PlanViewSet, basename='plans')
router.register(r'plan-decisions', PlanDecisionViewSet, basename='plan-decisions')

urlpatterns = router.urls + [
    path('stats/plans/', PlanStatsAPI.as_view(), name='plan_stats'),
    path('stats/goals/', GoalStatsAPI.as_view(), name='goal_stats'),
    path('inbox/', InboxAPI.as_view(), name='inbox'),
    path('my-submissions/', MySubmissionsAPI.as_view(), name='my_submissions'),
    # C3-3-1: 通知相关 API
    path('notifications/', NotificationListAPI.as_view(), name='plan_notifications'),
    path('notifications/unread-count/', NotificationUnreadCountAPI.as_view(), name='plan_notifications_unread_count'),
    path('notifications/<int:pk>/mark-read/', NotificationMarkReadAPI.as_view(), name='plan_notifications_mark_read'),
    path('notifications/mark-all-read/', NotificationMarkAllReadAPI.as_view(), name='plan_notifications_mark_all_read'),
    # P1: 计划决策裁决 API（注意：plan-decisions 列表已通过 router 注册）
    path('plan-decisions/<int:decision_id>/decide/', PlanDecisionDecideAPIView.as_view(), name='plan_decision_decide'),
]

