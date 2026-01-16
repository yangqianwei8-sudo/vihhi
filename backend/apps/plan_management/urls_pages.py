"""
计划管理模块页面路由配置
"""
from django.urls import path
from . import views_pages

app_name = "plan_pages"

urlpatterns = [
    # 首页
    path("", views_pages.plan_management_home, name="plan_management_home"),
    path("home/", views_pages.plan_management_home, name="plan_management_home"),
    
    # 计划列表
    path("plans/", views_pages.plan_list, name="plan_list"),
    
    # 计划管理
    path("plans/create/", views_pages.plan_create, name="plan_create"),
    path("plans/<int:plan_id>/", views_pages.plan_detail, name="plan_detail"),
    path("plans/<int:plan_id>/edit/", views_pages.plan_edit, name="plan_edit"),
    path("plans/<int:plan_id>/delete/", views_pages.plan_delete, name="plan_delete"),
    path("plans/decompose/", views_pages.plan_decompose_entry, name="plan_decompose_entry"),
    path("plans/<int:plan_id>/decompose/", views_pages.plan_decompose, name="plan_decompose"),
    path("plans/<int:plan_id>/goal-alignment/", views_pages.plan_goal_alignment, name="plan_goal_alignment"),
    path("plans/approval/", views_pages.plan_approval_list, name="plan_approval_list"),
    
    # 计划执行
    path("plans/<int:plan_id>/execution/", views_pages.plan_execution_track, name="plan_execution_track"),
    path("plans/<int:plan_id>/progress/update/", views_pages.plan_progress_update, name="plan_progress_update"),
    path("plans/<int:plan_id>/issues/", views_pages.plan_issue_list, name="plan_issue_list"),
    path("plans/<int:plan_id>/complete/", views_pages.plan_complete, name="plan_complete"),
    
    # P1 决策接口（围绕 decision 的裁决）
    path("plans/<int:plan_id>/requests/start/", views_pages.plan_request_start, name="plan_request_start"),
    path("plans/<int:plan_id>/requests/cancel/", views_pages.plan_request_cancel, name="plan_request_cancel"),
    path("decisions/<int:decision_id>/approve/", views_pages.decision_approve, name="decision_approve"),
    path("decisions/<int:decision_id>/reject/", views_pages.decision_reject, name="decision_reject"),
    
    # 计划调整申请
    path("plans/<int:plan_id>/adjustment/create/", views_pages.plan_adjustment_create, name="plan_adjustment_create"),
    path("adjustments/", views_pages.plan_adjustment_list, name="plan_adjustment_list"),
    path("adjustments/<int:adjustment_id>/approve/", views_pages.plan_adjustment_approve, name="plan_adjustment_approve"),
    path("adjustments/<int:adjustment_id>/reject/", views_pages.plan_adjustment_reject, name="plan_adjustment_reject"),
    
    # 战略目标
    path("strategic-goals/", views_pages.strategic_goal_list, name="strategic_goal_list"),
    path("strategic-goals/create/", views_pages.strategic_goal_create, name="strategic_goal_create"),
    path("strategic-goals/decompose/", views_pages.strategic_goal_decompose_entry, name="strategic_goal_decompose_entry"),
    path("strategic-goals/track/", views_pages.strategic_goal_track_entry, name="strategic_goal_track_entry"),
    path("strategic-goals/<int:goal_id>/", views_pages.strategic_goal_detail, name="strategic_goal_detail"),
    path("strategic-goals/<int:goal_id>/edit/", views_pages.strategic_goal_edit, name="strategic_goal_edit"),
    path("strategic-goals/<int:goal_id>/delete/", views_pages.strategic_goal_delete, name="strategic_goal_delete"),
    path("strategic-goals/<int:goal_id>/decompose/", views_pages.strategic_goal_decompose, name="strategic_goal_decompose"),
    path("strategic-goals/<int:goal_id>/track/", views_pages.strategic_goal_track, name="strategic_goal_track"),
    path("strategic-goals/<int:parent_goal_id>/create-child/", views_pages.create_child_goal, name="create_child_goal"),
    
    # 计划分析
    path("analysis/completion/", views_pages.plan_completion_analysis, name="plan_completion_analysis"),
    path("analysis/goal-achievement/", views_pages.plan_goal_achievement, name="plan_goal_achievement"),
    path("analysis/statistics/", views_pages.plan_statistics, name="plan_statistics"),
]

