from django.urls import path

from . import views_pages

app_name = "opportunity_pages"

urlpatterns = [
    # ==================== 商机管理路由 ====================
    # 商机管理首页
    path("", views_pages.opportunity_management_home, name="opportunity_management_home"),
    path("home/", views_pages.opportunity_management_home, name="opportunity_management_home_alt"),
    path("list/", views_pages.opportunity_management, name="opportunity_management"),
    path("import/", views_pages.opportunity_import, name="opportunity_import"),
    path("create/", views_pages.opportunity_create, name="opportunity_create"),
    path("<int:opportunity_id>/", views_pages.opportunity_detail, name="opportunity_detail"),
    path("<int:opportunity_id>/edit/", views_pages.opportunity_edit, name="opportunity_edit"),
    path("<int:opportunity_id>/delete/", views_pages.opportunity_delete, name="opportunity_delete"),
    path("<int:opportunity_id>/transition/", views_pages.opportunity_status_transition, name="opportunity_status_transition"),
    path("<int:opportunity_id>/followup/create/", views_pages.opportunity_followup_create, name="opportunity_followup_create"),
    path("<int:opportunity_id>/followup/<int:followup_id>/edit/", views_pages.opportunity_followup_edit, name="opportunity_followup_edit"),
    path("<int:opportunity_id>/followup/<int:followup_id>/delete/", views_pages.opportunity_followup_delete, name="opportunity_followup_delete"),
    
    # 商机管理子功能（根据总体设计方案）
    path("evaluation-application/", views_pages.opportunity_evaluation_application, name="opportunity_evaluation_application"),
    path("drawing-evaluation/", views_pages.opportunity_drawing_evaluation, name="opportunity_drawing_evaluation"),
    path("warehouse-application/", views_pages.opportunity_warehouse_application, name="opportunity_warehouse_application"),
    path("warehouse-list/", views_pages.opportunity_warehouse_list, name="opportunity_warehouse_list"),
    path("bid-bond-payment/", views_pages.opportunity_bid_bond_payment, name="opportunity_bid_bond_payment"),
    path("tender-fee-payment/", views_pages.opportunity_tender_fee_payment, name="opportunity_tender_fee_payment"),
    path("agency-fee-payment/", views_pages.opportunity_agency_fee_payment, name="opportunity_agency_fee_payment"),
    path("bidding-quotation-application/", views_pages.opportunity_bidding_quotation_application, name="opportunity_bidding_quotation_application"),
    path("bidding-document-preparation/", views_pages.opportunity_bidding_document_preparation, name="opportunity_bidding_document_preparation"),
    path("bidding-document-submission/", views_pages.opportunity_bidding_document_submission, name="opportunity_bidding_document_submission"),
    
    # 投标报价管理
    path("bidding-quotation/", views_pages.opportunity_bidding_quotation, name="opportunity_bidding_quotation"),
    path("bidding-quotation/create/", views_pages.bidding_quotation_create, name="bidding_quotation_create"),
    path("bidding-quotation/<int:bidding_id>/", views_pages.bidding_quotation_detail, name="bidding_quotation_detail"),
    path("bidding-quotation/<int:bidding_id>/edit/", views_pages.bidding_quotation_edit, name="bidding_quotation_edit"),
    
    path("tech-meeting/", views_pages.opportunity_tech_meeting, name="opportunity_tech_meeting"),
    path("followup/", views_pages.opportunity_followup_list, name="opportunity_followup_list"),
    path("forecast/", views_pages.opportunity_sales_forecast, name="opportunity_sales_forecast"),
    path("win-loss/", views_pages.opportunity_win_loss, name="opportunity_win_loss"),
    path("win-loss/select/", views_pages.opportunity_win_loss_select, name="opportunity_win_loss_select"),
    path("<int:opportunity_id>/win-loss/mark/", views_pages.opportunity_mark_win_loss, name="opportunity_mark_win_loss"),
    
    # 商务洽谈与表单
    path("business-negotiation/", views_pages.opportunity_business_negotiation, name="opportunity_business_negotiation"),
    path("business-negotiation/form/", views_pages.opportunity_business_negotiation_form, name="opportunity_business_negotiation_form"),
    path("<int:opportunity_id>/business-negotiation/form/", views_pages.opportunity_business_negotiation_form, name="opportunity_business_negotiation_form_edit"),
]
