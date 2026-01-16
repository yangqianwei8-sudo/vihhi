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
    path("contracts/management/", views_pages.contract_management_list, name="contract_management_list"),  # 合同管理列表（显示所有状态的合同）
    path("contracts/<int:contract_id>/", views_pages.contract_detail, name="contract_detail"),
    path("contracts/create/", views_pages.contract_create, name="contract_create"),
    path("contracts/<int:contract_id>/edit/", views_pages.contract_edit, name="contract_edit"),
    # 合同删除
    path("contracts/<int:contract_id>/delete/", views_pages.contract_delete, name="contract_delete"),
    # 合同审批
    path("contracts/<int:contract_id>/submit-approval/", views_pages.contract_submit_approval, name="contract_submit_approval"),
    # 合同争议
    path("contracts/dispute/", views_pages.contract_dispute_list, name="contract_dispute_list"),
    # 合同定稿
    path("contracts/finalize/", views_pages.contract_finalize_list, name="contract_finalize_list"),
    path("contracts/finalize/create/", views_pages.contract_finalize_create, name="contract_finalize_create"),  # 创建合同定稿
    # 合同洽谈记录
    path("contracts/negotiation/", views_pages.contract_negotiation_list, name="contract_negotiation_list"),  # 合同洽谈记录列表
    path("contracts/negotiation/create/", views_pages.contract_negotiation_create, name="contract_negotiation_create"),  # 创建合同洽谈记录
    path("contracts/negotiation/<int:negotiation_id>/", views_pages.contract_negotiation_detail, name="contract_negotiation_detail"),  # 合同洽谈记录详情
    # 履约跟踪
    path("contracts/performance/", views_pages.contract_performance_track, name="contract_performance_track"),
    # 到期提醒
    path("contracts/expiry-reminder/", views_pages.contract_expiry_reminder, name="contract_expiry_reminder"),
    # 付款提醒
    path("contracts/payment-reminder/", views_pages.contract_payment_reminder, name="contract_payment_reminder"),
    # 风险预警
    path("contracts/risk-warning/", views_pages.contract_risk_warning, name="contract_risk_warning"),
    path("settlements/", views_pages.project_settlement, name="project_settlement"),
    path("analysis/", views_pages.output_analysis, name="output_analysis"),
    path("payments/", views_pages.payment_tracking, name="payment_tracking"),
    
    # 商机管理（根据总体设计方案）
    path("opportunities/", views_pages.opportunity_management_home, name="opportunity_management_home"),
    path("opportunities/home/", views_pages.opportunity_management_home, name="opportunity_management_home"),
    path("opportunities/list/", views_pages.opportunity_management, name="opportunity_management"),
    path("opportunities/import/", views_pages.opportunity_import, name="opportunity_import"),
    path("opportunities/create/", views_pages.opportunity_create, name="opportunity_create"),
    path("opportunities/<int:opportunity_id>/", views_pages.opportunity_detail, name="opportunity_detail"),
    path("opportunities/<int:opportunity_id>/edit/", views_pages.opportunity_edit, name="opportunity_edit"),
    path("opportunities/<int:opportunity_id>/delete/", views_pages.opportunity_delete, name="opportunity_delete"),
    path("opportunities/<int:opportunity_id>/transition/", views_pages.opportunity_status_transition, name="opportunity_status_transition"),
    path("opportunities/<int:opportunity_id>/followup/create/", views_pages.opportunity_followup_create, name="opportunity_followup_create"),
    path("opportunities/<int:opportunity_id>/followup/<int:followup_id>/edit/", views_pages.opportunity_followup_edit, name="opportunity_followup_edit"),
    path("opportunities/<int:opportunity_id>/followup/<int:followup_id>/delete/", views_pages.opportunity_followup_delete, name="opportunity_followup_delete"),
    
    # 商机管理子功能（根据总体设计方案）
    path("opportunities/evaluation-application/", views_pages.opportunity_evaluation_application, name="opportunity_evaluation_application"),
    path("opportunities/drawing-evaluation/", views_pages.opportunity_drawing_evaluation, name="opportunity_drawing_evaluation"),
    path("opportunities/warehouse-application/", views_pages.opportunity_warehouse_application, name="opportunity_warehouse_application"),
    path("opportunities/warehouse-list/", views_pages.opportunity_warehouse_list, name="opportunity_warehouse_list"),
    path("opportunities/bid-bond-payment/", views_pages.opportunity_bid_bond_payment, name="opportunity_bid_bond_payment"),
    path("opportunities/tender-fee-payment/", views_pages.opportunity_tender_fee_payment, name="opportunity_tender_fee_payment"),
    path("opportunities/agency-fee-payment/", views_pages.opportunity_agency_fee_payment, name="opportunity_agency_fee_payment"),
    path("opportunities/bidding-quotation-application/", views_pages.opportunity_bidding_quotation_application, name="opportunity_bidding_quotation_application"),
    path("opportunities/bidding-document-preparation/", views_pages.opportunity_bidding_document_preparation, name="opportunity_bidding_document_preparation"),
    path("opportunities/bidding-document-submission/", views_pages.opportunity_bidding_document_submission, name="opportunity_bidding_document_submission"),
    # 投标报价管理
    path("opportunities/bidding-quotation/", views_pages.opportunity_bidding_quotation, name="opportunity_bidding_quotation"),
    path("opportunities/bidding-quotation/create/", views_pages.bidding_quotation_create, name="bidding_quotation_create"),
    path("opportunities/bidding-quotation/<int:bidding_id>/", views_pages.bidding_quotation_detail, name="bidding_quotation_detail"),
    path("opportunities/bidding-quotation/<int:bidding_id>/edit/", views_pages.bidding_quotation_edit, name="bidding_quotation_edit"),
    path("opportunities/tech-meeting/", views_pages.opportunity_tech_meeting, name="opportunity_tech_meeting"),
    path("opportunities/followup/", views_pages.opportunity_followup_list, name="opportunity_followup_list"),
    path("opportunities/forecast/", views_pages.opportunity_sales_forecast, name="opportunity_sales_forecast"),
    path("opportunities/win-loss/", views_pages.opportunity_win_loss, name="opportunity_win_loss"),
    path("opportunities/win-loss/select/", views_pages.opportunity_win_loss_select, name="opportunity_win_loss_select"),
    path("opportunities/<int:opportunity_id>/win-loss/mark/", views_pages.opportunity_mark_win_loss, name="opportunity_mark_win_loss"),
    
    # 商务洽谈与表单
    path("opportunities/business-negotiation/", views_pages.opportunity_business_negotiation, name="opportunity_business_negotiation"),
    path("opportunities/business-negotiation/form/", views_pages.opportunity_business_negotiation_form, name="opportunity_business_negotiation_form"),
    path("opportunities/<int:opportunity_id>/business-negotiation/form/", views_pages.opportunity_business_negotiation_form, name="opportunity_business_negotiation_form_edit"),
    
    # ==================== 业务委托书管理路由 ====================
    path("authorization-letters/", views_pages.authorization_letter_list, name="authorization_letter_list"),
    path("authorization-letters/create/", views_pages.authorization_letter_create, name="authorization_letter_create"),
    path("authorization-letters/<int:letter_id>/", views_pages.authorization_letter_detail, name="authorization_letter_detail"),
    path("authorization-letters/<int:letter_id>/edit/", views_pages.authorization_letter_edit, name="authorization_letter_edit"),
    path("authorization-letters/<int:letter_id>/delete/", views_pages.authorization_letter_delete, name="authorization_letter_delete"),
    path("authorization-letters/<int:letter_id>/status-transition/", views_pages.authorization_letter_status_transition, name="authorization_letter_status_transition"),
    
    # 业务委托书模板管理
    path("authorization-letter-templates/", views_pages.authorization_letter_template_list, name="authorization_letter_template_list"),
    path("authorization-letter-templates/create/", views_pages.authorization_letter_template_create, name="authorization_letter_template_create"),
    path("authorization-letter-templates/<int:template_id>/edit/", views_pages.authorization_letter_template_edit, name="authorization_letter_template_edit"),
    path("authorization-letter-templates/<int:template_id>/delete/", views_pages.authorization_letter_template_delete, name="authorization_letter_template_delete"),
    path("authorization-letter-templates/<int:template_id>/create-letter/", views_pages.authorization_letter_create_from_template, name="authorization_letter_create_from_template"),
    path("authorization-letter-templates/<int:template_id>/file/preview/", views_pages.authorization_letter_template_file_preview, name="authorization_letter_template_file_preview"),
    path("authorization-letter-templates/<int:template_id>/file/download/", views_pages.authorization_letter_template_file_download, name="authorization_letter_template_file_download"),
    
]

