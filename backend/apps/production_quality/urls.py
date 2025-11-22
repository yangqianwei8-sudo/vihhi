from django.urls import path
from rest_framework.routers import DefaultRouter

from . import views_pages
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
] + router.urls

