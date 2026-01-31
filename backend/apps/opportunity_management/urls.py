from django.urls import path, include
from rest_framework.routers import DefaultRouter
from . import views

app_name = 'opportunity'

router = DefaultRouter()

urlpatterns = [
    path('', include(router.urls)),
    # 商机分析API
    path('opportunities/funnel-analysis/', views.opportunity_funnel_analysis_api, name='opportunity_funnel_analysis'),
    path('opportunities/sales-forecast/', views.opportunity_sales_forecast_api, name='opportunity_sales_forecast'),
    path('opportunities/<int:opportunity_id>/health-score/', views.opportunity_health_score_api, name='opportunity_health_score'),
    path('opportunities/<int:opportunity_id>/quality-score/', views.opportunity_quality_score_api, name='opportunity_quality_score'),
    path('opportunities/<int:opportunity_id>/action-suggestions/', views.opportunity_action_suggestions_api, name='opportunity_action_suggestions'),
]
