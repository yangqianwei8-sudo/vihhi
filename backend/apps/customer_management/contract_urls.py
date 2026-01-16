from django.urls import path

from . import views_pages

app_name = "contract_pages"

urlpatterns = [
    # ==================== 合同管理首页 ====================
    path("", views_pages.contract_management_home, name="contract_management_home"),
    path("home/", views_pages.contract_management_home, name="contract_management_home_alt"),
    
    # ==================== 合同管理路由 ====================
    # 合同管理列表（显示所有状态的合同）
    path("management/", views_pages.contract_management_list, name="contract_management_list"),
    path("create/", views_pages.contract_create, name="contract_create"),
    path("<int:contract_id>/", views_pages.contract_detail, name="contract_detail"),
    path("<int:contract_id>/edit/", views_pages.contract_edit, name="contract_edit"),
    # 合同删除
    path("<int:contract_id>/delete/", views_pages.contract_delete, name="contract_delete"),
    # 合同审批
    path("<int:contract_id>/submit-approval/", views_pages.contract_submit_approval, name="contract_submit_approval"),
    # 合同争议
    path("dispute/", views_pages.contract_dispute_list, name="contract_dispute_list"),
    # 合同定稿
    path("finalize/", views_pages.contract_finalize_list, name="contract_finalize_list"),
    path("finalize/create/", views_pages.contract_finalize_create, name="contract_finalize_create"),  # 创建合同定稿
    # 合同洽谈记录
    path("negotiation/", views_pages.contract_negotiation_list, name="contract_negotiation_list"),  # 合同洽谈记录列表
    path("negotiation/create/", views_pages.contract_negotiation_create, name="contract_negotiation_create"),  # 创建合同洽谈记录
    path("negotiation/<int:negotiation_id>/", views_pages.contract_negotiation_detail, name="contract_negotiation_detail"),  # 合同洽谈记录详情
    # 履约跟踪
    path("performance/", views_pages.contract_performance_track, name="contract_performance_track"),
    # 到期提醒
    path("expiry-reminder/", views_pages.contract_expiry_reminder, name="contract_expiry_reminder"),
    # 付款提醒
    path("payment-reminder/", views_pages.contract_payment_reminder, name="contract_payment_reminder"),
    # 风险预警
    path("risk-warning/", views_pages.contract_risk_warning, name="contract_risk_warning"),
    
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
