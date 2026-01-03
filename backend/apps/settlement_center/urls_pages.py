from django.urls import path
from django.shortcuts import redirect
from . import views_pages
from . import views_settlement_items

app_name = "settlement_pages"


def settlement_center_redirect(request):
    """结算中心首页重定向到产值管理首页"""
    return redirect('settlement_pages:output_value_home')


urlpatterns = [
    # 旧链接重定向：结算中心首页重定向到产值管理首页
    path("", settlement_center_redirect, name="settlement_center_home"),
    path("home/", settlement_center_redirect, name="settlement_center_home_redirect"),
    
    # 产值管理
    path("output-value/", views_pages.output_value_home, name="output_value_home"),
    path("output-value/home/", views_pages.output_value_home, name="output_value_home"),
    path("output-value/template/", views_pages.output_value_template_manage, name="output_value_template_manage"),
    path("output-value/records/", views_pages.output_value_record_list, name="output_value_record_list"),
    path("output-value/records/<int:record_id>/confirm/", views_pages.output_value_record_confirm, name="output_value_record_confirm"),
    path("output-value/records/batch-confirm/", views_pages.output_value_record_batch_confirm, name="output_value_record_batch_confirm"),
    path("output-value/records/export/", views_pages.output_value_record_export, name="output_value_record_export"),
    path("output-value/project/<int:project_id>/", views_pages.project_output_value_detail, name="project_output_value_detail"),
    path("output-value/statistics/", views_pages.output_value_statistics, name="output_value_statistics"),
    
    # 产值阶段管理
    path("output-value/stages/", views_pages.output_value_stage_list, name="output_value_stage_list"),
    path("output-value/stages/create/", views_pages.output_value_stage_create, name="output_value_stage_create"),
    path("output-value/stages/<int:stage_id>/edit/", views_pages.output_value_stage_edit, name="output_value_stage_edit"),
    path("output-value/stages/<int:stage_id>/delete/", views_pages.output_value_stage_delete, name="output_value_stage_delete"),
    
    # 产值里程碑管理
    path("output-value/milestones/", views_pages.output_value_milestone_list, name="output_value_milestone_list"),
    path("output-value/milestones/create/", views_pages.output_value_milestone_create, name="output_value_milestone_create"),
    path("output-value/milestones/<int:milestone_id>/edit/", views_pages.output_value_milestone_edit, name="output_value_milestone_edit"),
    path("output-value/milestones/<int:milestone_id>/delete/", views_pages.output_value_milestone_delete, name="output_value_milestone_delete"),
    
    # 产值事件管理
    path("output-value/events/", views_pages.output_value_event_list, name="output_value_event_list"),
    path("output-value/events/create/", views_pages.output_value_event_create, name="output_value_event_create"),
    path("output-value/events/<int:event_id>/edit/", views_pages.output_value_event_edit, name="output_value_event_edit"),
    path("output-value/events/<int:event_id>/delete/", views_pages.output_value_event_delete, name="output_value_event_delete"),
    
    # 项目结算管理
    path("project-settlement/", views_pages.project_settlement_home, name="project_settlement_home"),
    path("project-settlement/home/", views_pages.project_settlement_home, name="project_settlement_home"),
    path("project-settlement/list/", views_pages.project_settlement_list, name="project_settlement_list"),
    path("project-settlement/create/", views_pages.project_settlement_create, name="project_settlement_create"),
    path("project-settlement/<int:settlement_id>/", views_pages.project_settlement_detail, name="project_settlement_detail"),
    path("project-settlement/<int:settlement_id>/edit/", views_pages.project_settlement_update, name="project_settlement_update"),
    path("project-settlement/<int:settlement_id>/submit/", views_pages.project_settlement_submit, name="project_settlement_submit"),
    
    # 结算明细项管理
    path("settlement-item/<int:item_id>/review/", views_settlement_items.settlement_item_review, name="settlement_item_review"),
    path("settlement/<int:settlement_id>/generate-items/", views_settlement_items.generate_items_from_opinions, name="generate_items_from_opinions"),
    
    # 回款管理
    path("payment/", views_pages.payment_management_home, name="payment_management_home"),
    path("payment/home/", views_pages.payment_management_home, name="payment_management_home"),
    path("payment-plans/", views_pages.payment_plan_list, name="payment_plan_list"),
    path("payment-plans/create/", views_pages.payment_plan_create, name="payment_plan_create"),
    path("payment-plans/<str:plan_type>/<int:plan_id>/", views_pages.payment_plan_detail, name="payment_plan_detail"),
    path("payment-plans/<str:plan_type>/<int:plan_id>/edit/", views_pages.payment_plan_edit, name="payment_plan_edit"),
    path("payment-plans/<str:plan_type>/<int:plan_id>/delete/", views_pages.payment_plan_delete, name="payment_plan_delete"),
    path("payment-records/", views_pages.payment_record_list, name="payment_record_list"),
    path("payment-records/<int:record_id>/", views_pages.payment_record_detail, name="payment_record_detail"),
    path("payment-records/<int:record_id>/edit/", views_pages.payment_record_edit, name="payment_record_edit"),
    path("payment-records/<int:record_id>/delete/", views_pages.payment_record_delete, name="payment_record_delete"),
    path("payment-records/<int:record_id>/confirm/", views_pages.payment_record_confirm, name="payment_record_confirm"),
    path("payment-records/create/", views_pages.payment_record_create_standalone, name="payment_record_create_standalone"),
    path("payment-records/create/<str:plan_type>/<int:plan_id>/", views_pages.payment_record_create, name="payment_record_create"),
    path("payment-records/export/", views_pages.payment_record_export, name="payment_record_export"),
    # 回款申请
    path("payment-applications/", views_pages.payment_application_list, name="payment_application_list"),
    path("payment-applications/create/", views_pages.payment_application_create, name="payment_application_create"),
    path("payment-applications/<int:application_id>/", views_pages.payment_application_detail, name="payment_application_detail"),
    path("payment-applications/<int:application_id>/review/", views_pages.payment_application_review, name="payment_application_review"),
    path("payment-applications/<int:application_id>/submit/", views_pages.payment_application_submit, name="payment_application_submit"),
]
