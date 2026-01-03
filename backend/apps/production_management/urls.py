from django.urls import path, include
from django.shortcuts import redirect
from rest_framework.routers import DefaultRouter
from . import views
from . import views_pages

app_name = 'production'

router = DefaultRouter()
router.register('projects', views.ProjectViewSet, basename='project')
router.register('project-teams', views.ProjectTeamViewSet, basename='project-team')
router.register('milestones', views.ProjectMilestoneViewSet, basename='milestone')
router.register('documents', views.ProjectDocumentViewSet, basename='document')
router.register('archives', views.ProjectArchiveViewSet, basename='archive')
router.register('notifications', views.ProjectTeamNotificationViewSet, basename='notification')
router.register('drawing-submissions', views.ProjectDrawingSubmissionViewSet, basename='drawing-submission')
router.register('drawing-reviews', views.ProjectDrawingReviewViewSet, basename='drawing-review')
router.register('drawing-files', views.ProjectDrawingFileViewSet, basename='drawing-file')
router.register('start-notices', views.ProjectStartNoticeViewSet, basename='start-notice')

urlpatterns = [
    # API 路由
    path('api/', include(router.urls)),
    
    # 页面路由
    # 首页
    path('', views_pages.production_management_home, name='production_management_home'),
    path('home/', views_pages.production_management_home, name='production_management_home'),
    
    path('create/', views_pages.project_create, name='project_create'),
    path('<int:project_id>/edit/', views_pages.project_edit, name='project_edit'),
    path('<int:project_id>/complete/', views_pages.project_complete, name='project_complete'),
    path('<int:project_id>/team/', views_pages.project_team, name='project_team'),
    path('<int:project_id>/receive/', views_pages.project_receive, name='project_receive'),
    path('admin/import/', views_pages.project_import_admin, name='project_import_admin'),
    path('<int:project_id>/drawings/submit/', views_pages.project_drawing_submit, name='project_drawing_submit'),
    path('<int:project_id>/drawings/<int:submission_id>/action/', views_pages.project_drawing_action, name='project_drawing_action'),
    path('<int:project_id>/drawings/<int:submission_id>/review/', views_pages.project_drawing_review, name='project_drawing_review'),
    path('<int:project_id>/flow/action/', views_pages.project_flow_action, name='project_flow_action'),
    path('<int:project_id>/tasks/<int:task_id>/action/', views_pages.project_task_action, name='project_task_action'),
    path('<int:project_id>/start-notices/create/', views_pages.project_start_notice_create, name='project_start_notice_create'),
    path('<int:project_id>/start-notices/<int:notice_id>/action/', views_pages.project_start_notice_action, name='project_start_notice_action'),
    # 项目列表路由
    path('list/', views_pages.project_list, name='project_list'),
    path('list/export/', views_pages.project_list_export, name='project_list_export'),
    # 兼容旧的项目查询URL，重定向到项目总览
    path('query/', lambda request: redirect('production_pages:project_list', permanent=False)),
    path('<int:project_id>/detail/', views_pages.project_detail, name='project_detail'),
    path('tasks/dashboard/', views_pages.project_task_dashboard, name='project_task_dashboard'),
    path('<int:project_id>/client-pre-docs/', views_pages.project_client_pre_docs, name='project_client_pre_docs'),
    path('<int:project_id>/design-reply/', views_pages.project_design_reply, name='project_design_reply'),
    path('<int:project_id>/meeting-log/', views_pages.project_meeting_log, name='project_meeting_log'),
    path('<int:project_id>/design-upload/', views_pages.project_design_upload, name='project_design_upload'),
    path('<int:project_id>/internal-verify/', views_pages.project_internal_verify, name='project_internal_verify'),
    path('<int:project_id>/client-confirm/', views_pages.project_client_confirm_outcome, name='project_client_confirm_outcome'),
    path('<int:project_id>/archive/', views_pages.project_archive, name='project_archive'),
    
    # AI顾问系统
    path('ai-advisor/', views_pages.ai_advisor, name='ai_advisor'),
    path('api/ai-advisor/analyze/', views.ai_advisor_analyze, name='ai_advisor_api_analyze'),
    path('api/ai-advisor/cases/search/', views.ai_advisor_cases_search, name='ai_advisor_api_cases_search'),
    path('api/ai-advisor/solutions/save/', views.ai_advisor_save_solution, name='ai_advisor_api_save_solution'),
    path('api/ai-advisor/solutions/list/', views.ai_advisor_list_solutions, name='ai_advisor_api_list_solutions'),
    
    # 优化前资料
    path('pre-optimization-materials/', views_pages.pre_optimization_materials_list, name='pre_optimization_materials'),
    path('pre-optimization-materials/create/', views_pages.pre_optimization_materials_create, name='pre_optimization_materials_create'),
    path('pre-optimization-materials/<int:material_id>/', views_pages.pre_optimization_materials_detail, name='pre_optimization_materials_detail'),
    path('pre-optimization-materials/<int:material_id>/reparse/', views_pages.pre_optimization_materials_reparse, name='pre_optimization_materials_reparse'),
    path('pre-optimization-materials/<int:material_id>/progress/', views_pages.pre_optimization_materials_progress, name='pre_optimization_materials_progress'),
    path('api/pre-optimization-materials/<int:material_id>/parse-status/', views.pre_optimization_materials_parse_status, name='pre_optimization_materials_parse_status'),
    
]
