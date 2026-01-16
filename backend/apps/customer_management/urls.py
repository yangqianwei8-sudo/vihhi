from django.urls import path, include
from rest_framework.routers import DefaultRouter
from . import views

app_name = 'customer'

router = DefaultRouter()
# 客户管理API路由（按《客户管理详细设计方案 v1.12》实现）
router.register('clients', views.ClientViewSet, basename='client')
router.register('contacts', views.ClientContactViewSet, basename='contact')
router.register('relationships', views.CustomerRelationshipViewSet, basename='relationship')
router.register('relationship-upgrades', views.CustomerRelationshipUpgradeViewSet, basename='relationship-upgrade')

urlpatterns = [
    # 注意：clients/ 和 contacts/ 下的特定路径必须在 router.urls 之前定义，否则会被 ViewSet 路由捕获
    # 获取客户办公地址API
    path('clients/address/', views.get_client_address, name='get_client_address'),
    path('clients/info/', views.get_client_info, name='get_client_info'),
    # 获取联系人信息API（必须在 router.urls 之前）
    path('contacts/<int:contact_id>/info/', views.get_contact_info, name='get_contact_info'),
    
    # ViewSet 路由（必须在特定路径之后）
    path('', include(router.urls)),
    
    path('verify-credit-code/', views.verify_credit_code, name='verify_credit_code'),
    path('search-company/', views.search_company, name='search_company'),
    path('get-company-detail/', views.get_company_detail, name='get_company_detail'),
    path('get-company-info-by-name/', views.get_company_info_by_name, name='get_company_info_by_name'),
    path('get-legal-risk/', views.get_legal_risk, name='get_legal_risk'),
    path('get-execution-records/', views.get_execution_records, name='get_execution_records'),
    path('sync-execution-records/', views.sync_execution_records, name='sync_execution_records'),
    path('check-duplicate/', views.check_duplicate_client, name='check_duplicate_client'),
    # path('find-by-phone/', views.find_client_by_phone, name='find_client_by_phone'),
    # 报价管理 REST API
    path('quotations/modes/', views.get_quotation_modes, name='get_quotation_modes'),
    path('quotations/calculate-by-mode/', views.calculate_quotation_by_mode, name='calculate_quotation_by_mode'),
    # 商机分析 REST API
    path('opportunities/funnel-analysis/', views.opportunity_funnel_analysis_api, name='opportunity_funnel_analysis_api'),
    path('opportunities/sales-forecast/', views.opportunity_sales_forecast_api, name='opportunity_sales_forecast_api'),
    path('opportunities/<int:opportunity_id>/health-score/', views.opportunity_health_score_api, name='opportunity_health_score_api'),
    path('opportunities/<int:opportunity_id>/quality-score/', views.opportunity_quality_score_api, name='opportunity_quality_score_api'),
    path('opportunities/<int:opportunity_id>/action-suggestions/', views.opportunity_action_suggestions_api, name='opportunity_action_suggestions_api'),
    # 销售活动 REST API
    path('activities/', views.sales_activity_rest_api, name='sales_activity_rest_api'),
    path('activities/<int:activity_id>/', views.sales_activity_rest_api, name='sales_activity_rest_api_detail'),
    # 高德地图相关API
    path('regeocode/', views.regeocode_location, name='regeocode_location'),
    path('ip-location/', views.ip_location_api, name='ip_location_api'),
    path('districts/', views.get_districts, name='get_districts'),
    # 业务委托书相关API
    path('authorization-letters/opportunities/', views.get_opportunities_by_client_name, name='get_opportunities_by_client_name'),
    path('authorization-letters/contacts/', views.get_contacts_by_client_id, name='get_contacts_by_client_id'),
    # 我方主体信息API
    path('our-company/info/', views.get_our_company_info, name='get_our_company_info'),
    # 学校搜索API
    path('schools/search/', views.search_schools, name='search_schools'),
    # 合同识别API
    path('contracts/recognize/', views.recognize_contract, name='recognize_contract'),
]
