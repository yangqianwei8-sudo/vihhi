from django.urls import path, include
from rest_framework.routers import DefaultRouter
from . import views
from . import views_pages

app_name = 'project'

router = DefaultRouter()
router.register('projects', views.ProjectViewSet, basename='project')
router.register('project-teams', views.ProjectTeamViewSet, basename='project-team')
router.register('payment-plans', views.PaymentPlanViewSet, basename='payment-plan')
router.register('milestones', views.ProjectMilestoneViewSet, basename='milestone')
router.register('documents', views.ProjectDocumentViewSet, basename='document')
router.register('archives', views.ProjectArchiveViewSet, basename='archive')

urlpatterns = [
    # API 路由
    path('api/', include(router.urls)),
    
    # 页面路由
    path('create/', views_pages.project_create, name='project_create'),
    path('<int:project_id>/complete/', views_pages.project_complete, name='project_complete'),
    path('<int:project_id>/team/', views_pages.project_team, name='project_team'),
    path('list/', views_pages.project_list, name='project_list'),
    path('<int:project_id>/detail/', views_pages.project_detail, name='project_detail'),
    path('query/', views_pages.project_query, name='project_query'),
    path('<int:project_id>/archive/', views_pages.project_archive, name='project_archive'),
]
