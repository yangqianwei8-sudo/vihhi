from django.urls import path
from . import views_pages
from . import views_settlement_items

app_name = "settlement"

urlpatterns = [
    # 产值管理
    path("output-value/template/", views_pages.output_value_template_manage, name="output_value_template_manage"),
    path("output-value/records/", views_pages.output_value_record_list, name="output_value_record_list"),
    path("output-value/records/<int:record_id>/confirm/", views_pages.output_value_record_confirm, name="output_value_record_confirm"),
    path("output-value/project/<int:project_id>/", views_pages.project_output_value_detail, name="project_output_value_detail"),
    path("output-value/statistics/", views_pages.output_value_statistics, name="output_value_statistics"),

    # 项目结算管理
    path("project-settlement/", views_pages.project_settlement_list, name="project_settlement_list"),
    path("project-settlement/create/", views_pages.project_settlement_create, name="project_settlement_create"),
    path("project-settlement/<int:settlement_id>/", views_pages.project_settlement_detail, name="project_settlement_detail"),
    path("project-settlement/<int:settlement_id>/edit/", views_pages.project_settlement_update, name="project_settlement_update"),
    path("project-settlement/<int:settlement_id>/submit/", views_pages.project_settlement_submit, name="project_settlement_submit"),

    # 结算明细项管理
    path("settlement-item/<int:item_id>/review/", views_settlement_items.settlement_item_review, name="settlement_item_review"),
    path("settlement/<int:settlement_id>/generate-items/", views_settlement_items.generate_items_from_opinions, name="generate_items_from_opinions"),

    # 回款管理
    path("payment-plans/", views_pages.payment_plan_list, name="payment_plan_list"),
    path("payment-plans/<str:plan_type>/<int:plan_id>/", views_pages.payment_plan_detail, name="payment_plan_detail"),
    path("payment-records/", views_pages.payment_record_list, name="payment_record_list"),
    path("payment-records/create/<str:plan_type>/<int:plan_id>/", views_pages.payment_record_create, name="payment_record_create"),
]

