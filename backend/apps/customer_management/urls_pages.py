from django.urls import path, include
from django.views.generic import RedirectView

from . import views_pages

app_name = "business"

urlpatterns = [
    # ==================== 客户管理首页 ====================
    path("", views_pages.customer_management_home, name="customer_management_home"),
    
    # ==================== 客户管理路由（按《客户管理详细设计方案 v1.12》实现）====================
    # 客户信息管理
    path("customers/", views_pages.customer_list, name="customer_list"),
    path("customers/create/", views_pages.customer_create, name="customer_create"),
    path("customers/<int:client_id>/", views_pages.customer_detail, name="customer_detail"),
    path("customers/<int:client_id>/edit/", views_pages.customer_edit, name="customer_edit"),
    path("customers/<int:client_id>/delete/", views_pages.customer_delete, name="customer_delete"),
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
    path("contacts/info-change/create/", views_pages.contact_info_change_create, name="contact_info_change_create"),
    
    # 跟进与拜访管理（放在客户管理模块下）
    path("customers/visits/", views_pages.customer_visit, name="customer_visit"),
    # 旧路径重定向（保持向后兼容）
    path("customer-visit/", RedirectView.as_view(pattern_name='business_pages:customer_visit', permanent=True), name="customer_visit_old"),
    path("customer-visit/create/", RedirectView.as_view(pattern_name='business_pages:visit_plan_flow', permanent=True), name="customer_visit_create_old"),
    
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
    # 以下路由暂时注释，视图函数尚未实现
    # path("customer-relationship-collaboration/<int:collaboration_id>/edit/", views_pages.customer_relationship_collaboration_edit, name="customer_relationship_collaboration_edit"),
    # path("customer-relationship-collaboration/<int:collaboration_id>/delete/", views_pages.customer_relationship_collaboration_delete, name="customer_relationship_collaboration_delete"),
    # 客户联系人管理（暂时注释，视图函数尚未实现）
    # path("contacts/", views_pages.contact_management, name="contact_management"),
    # path("contacts/create/", views_pages.contact_create, name="contact_create"),
    # path("contacts/change/", views_pages.contact_change, name="contact_change"),
    # path("contacts/<int:contact_id>/edit/", views_pages.contact_edit, name="contact_edit"),
    # path("contacts/<int:contact_id>/delete/", views_pages.contact_delete, name="contact_delete"),
    # path("contacts/<int:contact_id>/set-primary/", views_pages.contact_set_primary, name="contact_set_primary"),
    # 客户管理子功能（暂时注释，视图函数尚未实现）
    # path("customer-leads/", views_pages.customer_lead_list, name="customer_lead_list"),
    # path("customer-leads/create/", views_pages.customer_lead_create, name="customer_lead_create"),
    # path("customer-leads/<int:lead_id>/", views_pages.customer_lead_detail, name="customer_lead_detail"),
    # path("customer-leads/<int:lead_id>/edit/", views_pages.customer_lead_edit, name="customer_lead_edit"),
    # path("customer-leads/<int:lead_id>/delete/", views_pages.customer_lead_delete, name="customer_lead_delete"),
    # path("customer-leads/<int:lead_id>/claim/", views_pages.customer_lead_claim, name="customer_lead_claim"),
    # path("customer-leads/<int:lead_id>/followup/create/", views_pages.customer_lead_followup_create, name="customer_lead_followup_create"),
    # path("customer-leads/<int:lead_id>/followup/<int:followup_id>/edit/", views_pages.customer_lead_followup_edit, name="customer_lead_followup_edit"),
    # path("customer-leads/<int:lead_id>/followup/<int:followup_id>/delete/", views_pages.customer_lead_followup_delete, name="customer_lead_followup_delete"),
    # path("customer-leads/bulk-action/", views_pages.customer_lead_bulk_action, name="customer_lead_bulk_action"),
    # path("customer-lead-pool/", views_pages.customer_lead_pool, name="customer_lead_pool"),
    # path("customer-relationship/", views_pages.customer_relationship, name="customer_relationship"),
    # path("customer-relationship/create/", views_pages.customer_relationship_create, name="customer_relationship_create"),
    # path("customer-relationship/<int:relationship_id>/", views_pages.customer_relationship_detail, name="customer_relationship_detail"),
    # path("customer-relationship/<int:relationship_id>/edit/", views_pages.customer_relationship_edit, name="customer_relationship_edit"),
    # path("customer-public-sea/", views_pages.customer_public_sea, name="customer_public_sea"),
    # path("customer-public-sea/<int:client_id>/claim/", views_pages.customer_public_sea_claim, name="customer_public_sea_claim"),
    # path("visit-checkin/", views_pages.visit_checkin, name="visit_checkin"),
    # path("visit-checkin/create/", views_pages.visit_checkin_create, name="visit_checkin_create"),
    # path("visit-checkin/<int:checkin_id>/", views_pages.visit_checkin_detail, name="visit_checkin_detail"),
    # path("visit-plan/", views_pages.visit_plan, name="visit_plan"),
    # path("visit-plan/create/", views_pages.visit_plan_create, name="visit_plan_create"),
    # path("visit-plan/<int:plan_id>/", views_pages.visit_plan_detail, name="visit_plan_detail"),
    # path("visit-plan/<int:plan_id>/edit/", views_pages.visit_plan_edit, name="visit_plan_edit"),
    # path("visit-plan/<int:plan_id>/complete/", views_pages.visit_plan_complete, name="visit_plan_complete"),
    # path("followup-record/", views_pages.followup_record, name="followup_record"),
    # 合同相关路由已迁移至独立应用 contract_management，统一入口为 /contracts/（namespace: contract_pages）
    path("settlements/", views_pages.project_settlement, name="project_settlement"),
    path("analysis/", views_pages.output_analysis, name="output_analysis"),
    path("payments/", views_pages.payment_tracking, name="payment_tracking"),
    # 商机管理已迁移至独立应用 opportunity_management，统一入口为 /opportunities/（namespace: opportunity_pages）

    # ==================== 业务委托书管理路由（已迁移至 contract_management，此处重定向以兼容 /business/ 旧路径）====================
    path("authorization-letters/", views_pages.authorization_letter_list_redirect, name="authorization_letter_list"),
    path("authorization-letters/create/", views_pages.authorization_letter_create_redirect, name="authorization_letter_create"),
    path("authorization-letters/<int:letter_id>/", views_pages.authorization_letter_detail_redirect, name="authorization_letter_detail"),
    path("authorization-letters/<int:letter_id>/edit/", views_pages.authorization_letter_edit_redirect, name="authorization_letter_edit"),
    path("authorization-letters/<int:letter_id>/delete/", views_pages.authorization_letter_delete_redirect, name="authorization_letter_delete"),
    path("authorization-letters/<int:letter_id>/status-transition/", views_pages.authorization_letter_status_transition_redirect, name="authorization_letter_status_transition"),
    
    # 业务委托书模板管理（重定向到 contract_pages）
    path("authorization-letter-templates/", views_pages.authorization_letter_template_list_redirect, name="authorization_letter_template_list"),
    path("authorization-letter-templates/create/", views_pages.authorization_letter_template_create_redirect, name="authorization_letter_template_create"),
    path("authorization-letter-templates/<int:template_id>/edit/", views_pages.authorization_letter_template_edit_redirect, name="authorization_letter_template_edit"),
    path("authorization-letter-templates/<int:template_id>/delete/", views_pages.authorization_letter_template_delete_redirect, name="authorization_letter_template_delete"),
    path("authorization-letter-templates/<int:template_id>/create-letter/", views_pages.authorization_letter_create_from_template_redirect, name="authorization_letter_create_from_template"),
    path("authorization-letter-templates/<int:template_id>/file/preview/", views_pages.authorization_letter_template_file_preview_redirect, name="authorization_letter_template_file_preview"),
    path("authorization-letter-templates/<int:template_id>/file/download/", views_pages.authorization_letter_template_file_download_redirect, name="authorization_letter_template_file_download"),
    
]

