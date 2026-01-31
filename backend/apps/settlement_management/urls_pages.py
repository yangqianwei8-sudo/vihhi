"""
结算管理页面路由（由原 settlement_center 迁入，统一入口为 settlement_management）
"""
from django.urls import path
from . import views_pages
from . import views_settlement_items

app_name = "settlement_pages"

urlpatterns = [
    path("home/", views_pages.settlement_management_home, name="settlement_management_home"),
    path("project-settlement/", views_pages.project_settlement_list, name="project_settlement_list"),
    path("project-settlement/create/", views_pages.project_settlement_create, name="project_settlement_create"),
    path("project-settlement/<int:settlement_id>/", views_pages.project_settlement_detail, name="project_settlement_detail"),
    path("project-settlement/<int:settlement_id>/edit/", views_pages.project_settlement_update, name="project_settlement_update"),
    path("project-settlement/<int:settlement_id>/submit/", views_pages.project_settlement_submit, name="project_settlement_submit"),
    path("settlement-item/<int:item_id>/review/", views_settlement_items.settlement_item_review, name="settlement_item_review"),
    path("settlement/<int:settlement_id>/generate-items/", views_settlement_items.generate_items_from_opinions, name="generate_items_from_opinions"),
    # 回款管理
    path("payment-plans/", views_pages.payment_plan_list, name="payment_plan_list"),
    path("payment-plans/<str:plan_type>/<int:plan_id>/", views_pages.payment_plan_detail, name="payment_plan_detail"),
    path("payment-records/", views_pages.payment_record_list, name="payment_record_list"),
    path("payment-records/create/<str:plan_type>/<int:plan_id>/", views_pages.payment_record_create, name="payment_record_create"),
]
