from django.urls import path
from . import views_pages, views_export, views_notification, views_approval

app_name = "litigation_pages"

urlpatterns = [
    # 诉讼管理首页
    path("", views_pages.litigation_home, name="litigation_home"),
    path("home/", views_pages.litigation_home, name="litigation_management_home"),
    
    # 案件管理
    path("cases/", views_pages.case_list, name="case_list"),
    path("cases/export/", views_export.case_list_export, name="case_list_export"),
    path("cases/create/", views_pages.case_create, name="case_create"),
    path("cases/<int:case_id>/", views_pages.case_detail, name="case_detail"),
    path("cases/<int:case_id>/edit/", views_pages.case_edit, name="case_edit"),
    path("cases/<int:case_id>/delete/", views_pages.case_delete, name="case_delete"),
    path("cases/<int:case_id>/submit-approval/", views_approval.case_submit_approval, name="case_submit_approval"),
    path("cases/<int:case_id>/submit-filing/", views_approval.case_submit_filing, name="case_submit_filing"),
    
    # 诉讼流程管理
    path("cases/<int:case_id>/processes/", views_pages.process_list, name="process_list"),
    path("cases/<int:case_id>/processes/create/", views_pages.process_create, name="process_create"),
    path("processes/<int:process_id>/", views_pages.process_detail, name="process_detail"),
    path("processes/<int:process_id>/edit/", views_pages.process_edit, name="process_edit"),
    
    # 保全续封管理
    path("cases/<int:case_id>/preservation/", views_pages.preservation_list, name="preservation_list"),
    path("cases/<int:case_id>/preservation/create/", views_pages.preservation_create, name="preservation_create"),
    path("preservation/<int:seal_id>/", views_pages.preservation_detail, name="preservation_detail"),
    path("preservation/<int:seal_id>/edit/", views_pages.preservation_edit, name="preservation_edit"),
    path("preservation/<int:seal_id>/renew/", views_pages.preservation_renew, name="preservation_renew"),
    
    # 诉讼文档管理
    path("cases/<int:case_id>/documents/", views_pages.document_list, name="document_list"),
    path("cases/<int:case_id>/documents/upload/", views_pages.document_upload, name="document_upload"),
    path("documents/<int:document_id>/", views_pages.document_detail, name="document_detail"),
    path("documents/<int:document_id>/delete/", views_pages.document_delete, name="document_delete"),
    
    # 费用管理
    path("cases/<int:case_id>/expenses/", views_pages.expense_list, name="expense_list"),
    path("cases/<int:case_id>/expenses/export/", views_export.expense_list_export, name="expense_list_export"),
    path("expenses/export/", views_export.expense_list_export, name="expense_list_export_all"),
    path("cases/<int:case_id>/expenses/create/", views_pages.expense_create, name="expense_create"),
    path("expenses/<int:expense_id>/", views_pages.expense_detail, name="expense_detail"),
    path("expenses/<int:expense_id>/edit/", views_pages.expense_edit, name="expense_edit"),
    path("expenses/<int:expense_id>/reimburse/", views_pages.expense_reimburse, name="expense_reimburse"),
    path("expenses/<int:expense_id>/submit-reimbursement/", views_approval.expense_submit_reimbursement, name="expense_submit_reimbursement"),
    
    # 人员管理
    path("cases/<int:case_id>/persons/", views_pages.person_list, name="person_list"),
    path("cases/<int:case_id>/persons/create/", views_pages.person_create, name="person_create"),
    path("persons/<int:person_id>/", views_pages.person_detail, name="person_detail"),
    path("persons/<int:person_id>/edit/", views_pages.person_edit, name="person_edit"),
    
    # 时间管理
    path("cases/<int:case_id>/timelines/", views_pages.timeline_list, name="timeline_list"),
    path("cases/<int:case_id>/timelines/create/", views_pages.timeline_create, name="timeline_create"),
    path("timelines/<int:timeline_id>/", views_pages.timeline_detail, name="timeline_detail"),
    path("timelines/<int:timeline_id>/edit/", views_pages.timeline_edit, name="timeline_edit"),
    path("timelines/<int:timeline_id>/confirm/", views_pages.timeline_confirm, name="timeline_confirm"),
    path("timelines/calendar/", views_pages.timeline_calendar, name="timeline_calendar"),
    
    # 案件统计
    path("statistics/", views_pages.case_statistics, name="case_statistics"),
    path("statistics/export/", views_export.statistics_export, name="statistics_export"),
    path("statistics/expenses/", views_pages.expense_statistics, name="expense_statistics"),
    path("statistics/results/", views_pages.result_statistics, name="result_statistics"),
    
    # 通知确认
    path("notifications/", views_notification.notification_list, name="notification_list"),
    path("notifications/<int:notification_id>/", views_notification.notification_detail, name="notification_detail"),
    path("notifications/<int:notification_id>/confirm/", views_notification.notification_confirm, name="notification_confirm"),
    
    # 全局列表页面（不需要case_id）
    path("preservation/", views_pages.preservation_list_all, name="preservation_list_all"),
    path("documents/", views_pages.document_list_all, name="document_list_all"),
    path("expenses/", views_pages.expense_list_all, name="expense_list_all"),
    path("expenses/reimburse/", views_pages.expense_reimburse_list, name="expense_reimburse_list"),
    path("persons/", views_pages.person_list_all, name="person_list_all"),
    path("timelines/", views_pages.timeline_list_all, name="timeline_list_all"),
]

