from django.urls import path

from . import views_pages

app_name = "delivery_pages"

urlpatterns = [
    # 首页
    path("", views_pages.delivery_customer_home, name="delivery_customer_home"),
    path("home/", views_pages.delivery_customer_home, name="delivery_customer_home"),
    
    # 收发管理首页（保留用于向后兼容）
    path("report/", views_pages.report_delivery, name="report_delivery"),
    
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
    
    # 收文管理首页
    path("incoming-document/home/", views_pages.incoming_document_home, name="incoming_document_home"),
    # 收文管理列表
    path("incoming-document/", views_pages.incoming_document_list, name="incoming_document_list"),
    path("incoming-document/create/", views_pages.incoming_document_create, name="incoming_document_create"),
    path("incoming-document/<int:document_id>/", views_pages.incoming_document_detail, name="incoming_document_detail"),
    path("incoming-document/<int:document_id>/edit/", views_pages.incoming_document_edit, name="incoming_document_edit"),
    path("incoming-document/<int:document_id>/delete/", views_pages.incoming_document_delete, name="incoming_document_delete"),
    
    # 发文管理首页
    path("outgoing-document/home/", views_pages.outgoing_document_home, name="outgoing_document_home"),
    # 发文管理列表
    path("outgoing-document/", views_pages.outgoing_document_list, name="outgoing_document_list"),
    path("outgoing-document/create/", views_pages.outgoing_document_create, name="outgoing_document_create"),
    # 注意：recipient-units 必须在 <int:document_id> 之前，否则会被误匹配
    path("outgoing-document/recipient-units/", views_pages.get_recipient_units, name="get_recipient_units"),
    path("outgoing-document/recipient-contacts/", views_pages.get_recipient_contacts, name="get_recipient_contacts"),
    path("outgoing-document/<int:document_id>/", views_pages.outgoing_document_detail, name="outgoing_document_detail"),
    path("outgoing-document/<int:document_id>/edit/", views_pages.outgoing_document_edit, name="outgoing_document_edit"),
    path("outgoing-document/<int:document_id>/delete/", views_pages.outgoing_document_delete, name="outgoing_document_delete"),
    path("outgoing-document/batch-import/", views_pages.outgoing_document_batch_import, name="outgoing_document_batch_import"),
    path("outgoing-document/import-template/", views_pages.outgoing_document_import_template, name="outgoing_document_import_template"),
    # 发文状态流转操作
    path("outgoing-document/<int:document_id>/submit-review/", views_pages.outgoing_document_submit_review, name="outgoing_document_submit_review"),
    path("outgoing-document/<int:document_id>/approve/", views_pages.outgoing_document_approve, name="outgoing_document_approve"),
    path("outgoing-document/<int:document_id>/reject/", views_pages.outgoing_document_reject, name="outgoing_document_reject"),
    path("outgoing-document/<int:document_id>/send/", views_pages.outgoing_document_send, name="outgoing_document_send"),
    path("outgoing-document/<int:document_id>/complete/", views_pages.outgoing_document_complete, name="outgoing_document_complete"),
    path("outgoing-document/<int:document_id>/archive/", views_pages.outgoing_document_archive, name="outgoing_document_archive"),
    # 邮件相关路由（放在前面，避免被其他路由拦截）
    # 邮件跟踪像素（用于检测邮件是否被打开）
    path("email-tracking/<str:tracking_id>/", views_pages.email_tracking_pixel, name="email_tracking_pixel"),
    # 邮件确认收取（收件人点击确认收取链接后查看完整内容）
    path("email-receipt-confirm/<str:tracking_id>/", views_pages.email_receipt_confirm, name="email_receipt_confirm"),
    # 短信送达状态回调（阿里云短信服务回调接口）
    path("sms-callback/", views_pages.sms_callback, name="sms_callback"),
    # 发文跟踪
    path("outgoing-document/receipt/", views_pages.outgoing_document_receipt_list, name="outgoing_document_receipt_list"),
    path("outgoing-document/tracking/<int:tracking_id>/", views_pages.outgoing_document_tracking_detail, name="outgoing_document_tracking_detail"),
    path("outgoing-document/tracking/<int:tracking_id>/send/", views_pages.outgoing_document_send_from_tracking, name="outgoing_document_send_from_tracking"),
    path("outgoing-document/tracking/<int:tracking_id>/recipients/", views_pages.get_tracking_recipients, name="get_tracking_recipients"),
    path("outgoing-document/tracking/<int:tracking_id>/mark-email-read/", views_pages.mark_tracking_email_read, name="mark_tracking_email_read"),
    path("outgoing-document/tracking/batch-mark-email-read/", views_pages.batch_mark_tracking_email_read, name="batch_mark_tracking_email_read"),
    path("outgoing-document/tracking/<int:tracking_id>/update-express-info/", views_pages.update_tracking_express_info, name="update_tracking_express_info"),
    path("outgoing-document/tracking/<int:tracking_id>/hand-delivery-checkin/", views_pages.hand_delivery_checkin, name="hand_delivery_checkin"),
    path("outgoing-document/tracking/<int:tracking_id>/confirm-email-received/", views_pages.confirm_email_received, name="confirm_email_received"),
    path("outgoing-document/<int:document_id>/receipt-confirm/", views_pages.outgoing_document_receipt_confirm, name="outgoing_document_receipt_confirm"),
    path("outgoing-document/<int:document_id>/record-remedy/", views_pages.outgoing_document_record_remedy, name="outgoing_document_record_remedy"),
    # 发文效能报告
    path("outgoing-document/performance-report/", views_pages.outgoing_document_performance_report, name="outgoing_document_performance_report"),
    # 发文审计追踪
    path("outgoing-document/<int:document_id>/audit-trail/", views_pages.outgoing_document_audit_trail, name="outgoing_document_audit_trail"),
    path("outgoing-document/audit-query/", views_pages.outgoing_document_audit_query, name="outgoing_document_audit_query"),
    # 发文责任人绩效
    path("outgoing-document/performance/", views_pages.outgoing_document_performance_list, name="outgoing_document_performance_list"),
    path("outgoing-document/performance/<int:user_id>/", views_pages.outgoing_document_performance_detail, name="outgoing_document_performance_detail"),
    
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

