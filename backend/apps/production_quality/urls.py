from django.urls import path
from rest_framework.routers import DefaultRouter

from . import views_pages, views_startup
from .views import (
    OpinionReviewViewSet,
    OpinionViewSet,
    ProductionReportViewSet,
    ProductionStatisticViewSet,
)

app_name = "production_quality"

router = DefaultRouter()
router.register(r"opinions", OpinionViewSet, basename="opinion")
router.register(r"opinions/(?P<opinion_pk>[^/.]+)/reviews", OpinionReviewViewSet, basename="opinion-review")
router.register(r"reports", ProductionReportViewSet, basename="production-report")
router.register(r"statistics", ProductionStatisticViewSet, basename="production-statistic")

urlpatterns = [
    path("opinions/new/", views_pages.opinion_create, name="opinion_create"),
    path("opinions/drafts/", views_pages.opinion_drafts, name="opinion_drafts"),
    path("opinions/review/", views_pages.opinion_review_dashboard, name="opinion_review"),
    path("opinions/review/list/", views_pages.opinion_review_list, name="opinion_review_list"),
    path("opinions/<int:opinion_id>/review/", views_pages.opinion_review_detail, name="opinion_review_detail"),
    path("opinions/import/", views_pages.opinion_import, name="opinion_import"),
    path(
        "opinions/import/template/",
        views_pages.opinion_import_template,
        name="opinion_import_template",
    ),
    path("reports/generate/", views_pages.report_generate, name="report_generate"),
    path("statistics/overview/", views_pages.production_stats, name="production_stats"),
    # 生产启动相关路由
    path("startup/", views_startup.production_startup_list, name="production_startup_list"),
    path("startup/<int:startup_id>/", views_startup.production_startup_detail, name="production_startup_detail"),
    path("startup/<int:project_id>/receive/", views_startup.production_startup_receive, name="production_startup_receive"),
    path("startup/<int:startup_id>/upload-drawings/", views_startup.production_startup_upload_drawings, name="production_startup_upload_drawings"),
    path("startup/<int:startup_id>/configure-team/", views_startup.production_startup_configure_team, name="production_startup_configure_team"),
    path("startup/<int:startup_id>/create-tasks/", views_startup.production_startup_create_tasks, name="production_startup_create_tasks"),
    path("startup/<int:startup_id>/submit/", views_startup.production_startup_submit, name="production_startup_submit"),
    path("startup/<int:startup_id>/approve/", views_startup.production_startup_approve, name="production_startup_approve"),
] + router.urls

