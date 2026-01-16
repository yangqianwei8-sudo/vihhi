from django.urls import path

from . import views_pages

app_name = "delivery_pages"

urlpatterns = [
    # 收发管理首页
    path("", views_pages.report_delivery, name="report_delivery"),
    
    # 交付记录管理页面（收发管理模块）
    path("list/", views_pages.delivery_list, name="delivery_list"),
    path("create/", views_pages.delivery_create, name="delivery_create"),
    path("<int:delivery_id>/", views_pages.delivery_detail, name="delivery_detail"),
    path("<int:delivery_id>/edit/", views_pages.delivery_edit, name="delivery_edit"),
    path("<int:delivery_id>/delete/", views_pages.delivery_delete, name="delivery_delete"),
    path("<int:delivery_id>/submit/", views_pages.delivery_submit, name="delivery_submit"),
    path("statistics/", views_pages.delivery_statistics, name="delivery_statistics"),
    path("warnings/", views_pages.delivery_warnings, name="delivery_warnings"),
    
    # 交付审核页面（收发管理模块）
    path("approval/", views_pages.delivery_approval_list, name="delivery_approval_list"),
    path("approval/<int:delivery_id>/", views_pages.delivery_approval_detail, name="delivery_approval_detail"),
    path("approval/<int:delivery_id>/action/", views_pages.delivery_approval_action, name="delivery_approval_action"),
    
    # 邮件发送页面
    path("email/", views_pages.delivery_email_list, name="delivery_email_list"),
    path("email/<int:delivery_id>/send/", views_pages.delivery_email_send, name="delivery_email_send"),
    
    # 快递寄送页面
    path("express/", views_pages.delivery_express_list, name="delivery_express_list"),
    path("express/<int:delivery_id>/send/", views_pages.delivery_express_send, name="delivery_express_send"),
    
    # 签收确认页面
    path("receipt/", views_pages.delivery_receipt_list, name="delivery_receipt_list"),
    path("receipt/<int:delivery_id>/confirm/", views_pages.delivery_receipt_confirm, name="delivery_receipt_confirm"),
    
    # 现场送达页面
    path("hand-delivery/", views_pages.delivery_hand_delivery_list, name="delivery_hand_delivery_list"),
    path("hand-delivery/<int:delivery_id>/confirm/", views_pages.delivery_hand_delivery_confirm, name="delivery_hand_delivery_confirm"),
    
    # 收件确认页面
    path("receive/", views_pages.delivery_receive_list, name="delivery_receive_list"),
    path("receive/<int:delivery_id>/confirm/", views_pages.delivery_receive_confirm, name="delivery_receive_confirm"),
    
    # 客户反馈页面
    path("feedback/", views_pages.delivery_feedback_list, name="delivery_feedback_list"),
    path("feedback/<int:delivery_id>/create/", views_pages.delivery_feedback_create, name="delivery_feedback_create"),
    
    # 成果确认页面
    path("achievement/", views_pages.delivery_achievement_list, name="delivery_achievement_list"),
    path("achievement/<int:delivery_id>/confirm/", views_pages.delivery_achievement_confirm, name="delivery_achievement_confirm"),
    
    # 满意度评价页面
    path("satisfaction/", views_pages.delivery_satisfaction_list, name="delivery_satisfaction_list"),
    path("satisfaction/<int:delivery_id>/create/", views_pages.delivery_satisfaction_create, name="delivery_satisfaction_create"),
    path("satisfaction/statistics/", views_pages.delivery_satisfaction_statistics, name="delivery_satisfaction_statistics"),
    
    # 物流跟踪页面
    path("logistics/", views_pages.delivery_logistics_list, name="delivery_logistics_list"),
    path("logistics/<int:delivery_id>/", views_pages.delivery_logistics_detail, name="delivery_logistics_detail"),
    
    # 每周快报页面
    path("weekly-report/", views_pages.delivery_weekly_report_list, name="delivery_weekly_report_list"),
    path("weekly-report/create/", views_pages.delivery_weekly_report_create, name="delivery_weekly_report_create"),
    
    # 文件准备页面
    path("file-prep/", views_pages.delivery_file_prep_list, name="delivery_file_prep_list"),
    path("file-prep/upload/", views_pages.delivery_file_prep_upload, name="delivery_file_prep_upload"),
    
    # 收文管理
    path("incoming-document/", views_pages.incoming_document_list, name="incoming_document_list"),
    path("incoming-document/create/", views_pages.incoming_document_create, name="incoming_document_create"),
    path("incoming-document/<int:document_id>/", views_pages.incoming_document_detail, name="incoming_document_detail"),
    path("incoming-document/<int:document_id>/edit/", views_pages.incoming_document_edit, name="incoming_document_edit"),
    
    # 发文管理
    path("outgoing-document/", views_pages.outgoing_document_list, name="outgoing_document_list"),
    path("outgoing-document/create/", views_pages.outgoing_document_create, name="outgoing_document_create"),
    path("outgoing-document/<int:document_id>/", views_pages.outgoing_document_detail, name="outgoing_document_detail"),
    path("outgoing-document/<int:document_id>/edit/", views_pages.outgoing_document_edit, name="outgoing_document_edit"),
    
    # 快递公司管理
    path("express-company/", views_pages.express_company_list, name="express_company_list"),
    path("express-company/create/", views_pages.express_company_create, name="express_company_create"),
    path("express-company/<int:company_id>/", views_pages.express_company_detail, name="express_company_detail"),
    path("express-company/<int:company_id>/edit/", views_pages.express_company_edit, name="express_company_edit"),
    path("express-company/<int:company_id>/delete/", views_pages.express_company_delete, name="express_company_delete"),
    
    # 文件分类维护（统一管理页面）
    path("file-category/manage/", views_pages.file_category_manage, name="file_category_manage"),
    # 保留旧路由以兼容（可选）
    path("file-category/<str:stage_code>/", views_pages.file_category_list, name="file_category_list"),
    path("file-category/<str:stage_code>/create/", views_pages.file_category_create, name="file_category_create"),
    
    # 文件模板维护
    path("file-template/manage/", views_pages.file_template_manage, name="file_template_manage"),
    
    # ==================== 老版本路由（已注释，待实现）====================
    # 以下功能使用老版本的center_dashboard.html模板，已注释掉
    # 待后续实现新版本时再启用
    # path("collaboration/", views_pages.customer_collaboration, name="customer_collaboration"),
    # path("portal/", views_pages.customer_portal, name="customer_portal"),
    # path("signature/", views_pages.electronic_signature, name="electronic_signature"),
    # ==================== 老版本路由结束 ====================
]

