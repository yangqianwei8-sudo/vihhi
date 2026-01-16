from django.urls import path
from . import views_pages, views_api

app_name = "finance_pages"

urlpatterns = [
    # 财务管理主页
    path("", views_pages.financial_home, name="financial_home"),
    path("statistics/", views_pages.financial_statistics, name="financial_statistics"),
    
    # 会计科目
    path("accounts/", views_pages.account_subject_management, name="account_subject_management"),
    path("accounts/tree-export/", views_pages.account_subject_tree_export, name="account_subject_tree_export"),
    path("accounts/import-template/", views_pages.account_subject_import_template, name="account_subject_import_template"),
    path("accounts/import/", views_pages.account_subject_import, name="account_subject_import"),
    path("accounts/create/", views_pages.account_subject_create, name="account_subject_create"),
    path("accounts/<int:account_subject_id>/", views_pages.account_subject_detail, name="account_subject_detail"),
    path("accounts/<int:account_subject_id>/edit/", views_pages.account_subject_update, name="account_subject_update"),
    path("accounts/<int:account_subject_id>/delete/", views_pages.account_subject_delete, name="account_subject_delete"),
    
    # 凭证管理
    path("vouchers/", views_pages.voucher_management, name="voucher_management"),
    path("vouchers/export/", views_pages.voucher_export, name="voucher_export"),
    path("vouchers/batch-approve/", views_pages.voucher_batch_approve, name="voucher_batch_approve"),
    path("vouchers/batch-post/", views_pages.voucher_batch_post, name="voucher_batch_post"),
    path("vouchers/create/", views_pages.voucher_create, name="voucher_create"),
    path("vouchers/<int:voucher_id>/", views_pages.voucher_detail, name="voucher_detail"),
    path("vouchers/<int:voucher_id>/edit/", views_pages.voucher_update, name="voucher_update"),
    path("vouchers/<int:voucher_id>/submit/", views_pages.voucher_submit, name="voucher_submit"),
    path("vouchers/<int:voucher_id>/withdraw/", views_pages.voucher_withdraw, name="voucher_withdraw"),
    path("vouchers/<int:voucher_id>/approve/", views_pages.voucher_approve, name="voucher_approve"),
    path("vouchers/<int:voucher_id>/post/", views_pages.voucher_post, name="voucher_post"),
    path("vouchers/<int:voucher_id>/unpost/", views_pages.voucher_unpost, name="voucher_unpost"),
    path("vouchers/<int:voucher_id>/delete/", views_pages.voucher_delete, name="voucher_delete"),
    path("vouchers/<int:voucher_id>/print/", views_pages.voucher_print, name="voucher_print"),
    path("vouchers/<int:voucher_id>/copy/", views_pages.voucher_copy, name="voucher_copy"),
    path("vouchers/<int:voucher_id>/validate/", views_pages.voucher_validate, name="voucher_validate"),
    path("vouchers/<int:voucher_id>/entries/add/", views_pages.voucher_entry_add, name="voucher_entry_add"),
    path("vouchers/<int:voucher_id>/entries/<int:entry_id>/edit/", views_pages.voucher_entry_update, name="voucher_entry_update"),
    path("vouchers/<int:voucher_id>/entries/<int:entry_id>/delete/", views_pages.voucher_entry_delete, name="voucher_entry_delete"),
    
    # 账簿管理
    path("ledgers/", views_pages.ledger_management, name="ledger_management"),
    path("ledgers/<int:ledger_id>/", views_pages.ledger_detail, name="ledger_detail"),
    path("ledgers/opening-balance-setup/", views_pages.ledger_opening_balance_setup, name="ledger_opening_balance_setup"),
    path("ledgers/period-closing/", views_pages.ledger_period_closing, name="ledger_period_closing"),
    path("ledgers/subsidiary/", views_pages.subsidiary_ledger, name="subsidiary_ledger"),
    path("ledgers/balance-sheet/", views_pages.account_balance_sheet, name="account_balance_sheet"),
    path("ledgers/trial-balance/", views_pages.trial_balance, name="trial_balance"),
    
    # 预算管理
    path("budgets/", views_pages.budget_management, name="budget_management"),
    path("budgets/export/", views_pages.budget_export, name="budget_export"),
    path("budgets/execution-analysis/", views_pages.budget_execution_analysis, name="budget_execution_analysis"),
    path("budgets/create/", views_pages.budget_create, name="budget_create"),
    path("budgets/<int:budget_id>/", views_pages.budget_detail, name="budget_detail"),
    path("budgets/<int:budget_id>/edit/", views_pages.budget_update, name="budget_update"),
    path("budgets/<int:budget_id>/approve/", views_pages.budget_approve, name="budget_approve"),
    path("budgets/<int:budget_id>/delete/", views_pages.budget_delete, name="budget_delete"),
    
    # 发票管理
    path("invoices/", views_pages.invoice_management, name="invoice_management"),
    path("invoices/export/", views_pages.invoice_export, name="invoice_export"),
    path("invoices/create/", views_pages.invoice_create, name="invoice_create"),
    path("invoices/<int:invoice_id>/", views_pages.invoice_detail, name="invoice_detail"),
    path("invoices/<int:invoice_id>/edit/", views_pages.invoice_update, name="invoice_update"),
    path("invoices/<int:invoice_id>/verify/", views_pages.invoice_verify, name="invoice_verify"),
    path("invoices/<int:invoice_id>/cancel/", views_pages.invoice_cancel, name="invoice_cancel"),
    path("invoices/<int:invoice_id>/delete/", views_pages.invoice_delete, name="invoice_delete"),
    
    # API接口
    path("api/invoice/recognize/", views_api.recognize_invoice, name="invoice_recognize_api"),
    
    # 资金流水
    path("fund-flows/", views_pages.fund_flow_management, name="fund_flow_management"),
    path("fund-flows/export/", views_pages.fund_flow_export, name="fund_flow_export"),
    path("fund-flows/import-template/", views_pages.fund_flow_import_template, name="fund_flow_import_template"),
    path("fund-flows/import/", views_pages.fund_flow_import, name="fund_flow_import"),
    path("fund-flows/create/", views_pages.fund_flow_create, name="fund_flow_create"),
    path("fund-flows/<int:fund_flow_id>/", views_pages.fund_flow_detail, name="fund_flow_detail"),
    path("fund-flows/<int:fund_flow_id>/edit/", views_pages.fund_flow_update, name="fund_flow_update"),
    path("fund-flows/<int:fund_flow_id>/delete/", views_pages.fund_flow_delete, name="fund_flow_delete"),
    
    # 财务报表
    path("reports/", views_pages.report_management, name="report_management"),
    path("reports/balance-sheet/", views_pages.balance_sheet_report, name="balance_sheet_report"),
    path("reports/income-statement/", views_pages.income_statement_report, name="income_statement_report"),
    path("reports/cash-flow/", views_pages.cash_flow_report, name="cash_flow_report"),
    path("reports/<int:report_id>/", views_pages.report_detail, name="report_detail"),
    path("reports/<int:report_id>/export/", views_pages.report_export, name="report_export"),
    
    # 往来账款
    path("receivables/", views_pages.receivable_management, name="receivable_management"),
    path("receivables/export/", views_pages.receivable_export, name="receivable_export"),
    path("receivables/create/", views_pages.receivable_create, name="receivable_create"),
    path("receivables/<int:receivable_id>/", views_pages.receivable_detail, name="receivable_detail"),
    path("receivables/<int:receivable_id>/edit/", views_pages.receivable_update, name="receivable_update"),
    path("receivables/<int:receivable_id>/payment/", views_pages.receivable_payment, name="receivable_payment"),
    path("receivables/<int:receivable_id>/cancel/", views_pages.receivable_cancel, name="receivable_cancel"),
    path("receivables/<int:receivable_id>/delete/", views_pages.receivable_delete, name="receivable_delete"),
    
    path("payables/", views_pages.payable_management, name="payable_management"),
    path("payables/export/", views_pages.payable_export, name="payable_export"),
    path("payables/create/", views_pages.payable_create, name="payable_create"),
    path("payables/<int:payable_id>/", views_pages.payable_detail, name="payable_detail"),
    path("payables/<int:payable_id>/edit/", views_pages.payable_update, name="payable_update"),
    path("payables/<int:payable_id>/payment/", views_pages.payable_payment, name="payable_payment"),
    path("payables/<int:payable_id>/cancel/", views_pages.payable_cancel, name="payable_cancel"),
    path("payables/<int:payable_id>/delete/", views_pages.payable_delete, name="payable_delete"),
]

