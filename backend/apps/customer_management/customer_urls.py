from django.urls import path
from django.views.generic import RedirectView

from . import views_pages

app_name = "customer_pages"

urlpatterns = [
    # ==================== 客户管理首页 ====================
    path("", views_pages.customer_management_home, name="customer_management_home"),
    path("home/", views_pages.customer_management_home, name="customer_management_home_alt"),
    
    # ==================== 客户管理路由（按《客户管理详细设计方案 v1.12》实现）====================
    # 客户信息管理
    path("customers/", views_pages.customer_list, name="customer_list"),
    path("customers/create/", views_pages.customer_create, name="customer_create"),
    path("customers/<int:client_id>/", views_pages.customer_detail, name="customer_detail"),
    path("customers/<int:client_id>/edit/", views_pages.customer_edit, name="customer_edit"),
    path("customers/<int:client_id>/delete/", views_pages.customer_delete, name="customer_delete"),
    path("customers/<int:client_id>/submit-approval/", views_pages.customer_submit_approval, name="customer_submit_approval"),
    path("customers/<int:client_id>/execution-records/export/", views_pages.execution_records_export, name="execution_records_export"),
    path("customers/batch-delete/", views_pages.customer_batch_delete, name="customer_batch_delete"),
    path("customers/export/", views_pages.customer_export, name="customer_export"),
    path("customers/public-sea/", views_pages.customer_public_sea, name="customer_public_sea"),
    path("customers/public-sea/<int:client_id>/claim/", views_pages.customer_public_sea_claim, name="customer_public_sea_claim"),
    
    # 人员关系管理
    path("contacts/", views_pages.contact_list, name="contact_list"),
    path("contacts/create/", views_pages.contact_create, name="contact_create"),
    path("contacts/<int:contact_id>/", views_pages.contact_detail, name="contact_detail"),
    path("contacts/<int:contact_id>/edit/", views_pages.contact_edit, name="contact_edit"),
    path("contacts/<int:contact_id>/delete/", views_pages.contact_delete, name="contact_delete"),
    path("contacts/relationship-mining/", views_pages.contact_relationship_mining, name="contact_relationship_mining"),
    path("contacts/tracking-reminders/", views_pages.contact_tracking_reminders, name="contact_tracking_reminders"),
    path("contacts/info-change/create/", views_pages.contact_info_change_create, name="contact_info_change_create"),
    
    # 跟进与拜访管理（放在客户管理模块下）
    path("customers/visits/", views_pages.customer_visit, name="customer_visit"),
    # 旧路径重定向（保持向后兼容）
    path("customer-visit/", RedirectView.as_view(pattern_name='customer_pages:customer_visit', permanent=True), name="customer_visit_old"),
    path("customer-visit/create/", RedirectView.as_view(pattern_name='customer_pages:visit_plan_flow', permanent=True), name="customer_visit_create_old"),
    
    # 拜访四步流程
    path("visit-plan/flow/", views_pages.visit_plan_flow, name="visit_plan_flow"),
    path("visit-plan/flow/<int:plan_id>/", views_pages.visit_plan_flow, name="visit_plan_flow_edit"),
    path("visit-plan/create/", views_pages.visit_plan_create, name="visit_plan_create"),
    path("visit-plan/<int:plan_id>/", views_pages.visit_plan_detail, name="visit_plan_detail"),
    path("visit-plan/<int:plan_id>/checklist/", views_pages.visit_plan_checklist, name="visit_plan_checklist"),
    path("visit-plan/<int:plan_id>/checkin/", views_pages.visit_plan_checkin, name="visit_plan_checkin"),
    path("visit-plan/<int:plan_id>/review/", views_pages.visit_plan_review, name="visit_plan_review"),
    
    # 关系升级管理
    path("customer-relationship-upgrade/", views_pages.customer_relationship_upgrade, name="customer_relationship_upgrade"),
    path("customer-relationship-upgrade/create/", views_pages.customer_relationship_upgrade_create, name="customer_relationship_upgrade_create"),
    path("business-expense-application/", views_pages.business_expense_application_list, name="business_expense_application_list"),
    path("business-expense-application/create/", views_pages.business_expense_application_create, name="business_expense_application_create"),
    path("customer-relationship-collaboration/", views_pages.customer_relationship_collaboration, name="customer_relationship_collaboration"),
    path("customer-relationship-collaboration/create/", views_pages.customer_relationship_collaboration_create, name="customer_relationship_collaboration_create"),
    path("customer-relationship-collaboration/<int:collaboration_id>/", views_pages.customer_relationship_collaboration_detail, name="customer_relationship_collaboration_detail"),
    
    # 其他功能
    path("settlements/", views_pages.project_settlement, name="project_settlement"),
    path("analysis/", views_pages.output_analysis, name="output_analysis"),
    path("payments/", views_pages.payment_tracking, name="payment_tracking"),
]
