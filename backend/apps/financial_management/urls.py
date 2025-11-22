from django.urls import path
from . import views_pages

app_name = "finance_pages"

urlpatterns = [
    # 财务管理主页
    path("", views_pages.financial_home, name="financial_home"),
    
    # 会计科目
    path("accounts/", views_pages.account_subject_management, name="account_subject_management"),
    path("accounts/create/", views_pages.account_subject_create, name="account_subject_create"),
    path("accounts/<int:account_subject_id>/", views_pages.account_subject_detail, name="account_subject_detail"),
    path("accounts/<int:account_subject_id>/edit/", views_pages.account_subject_update, name="account_subject_update"),
    
    # 凭证管理
    path("vouchers/", views_pages.voucher_management, name="voucher_management"),
    path("vouchers/create/", views_pages.voucher_create, name="voucher_create"),
    path("vouchers/<int:voucher_id>/", views_pages.voucher_detail, name="voucher_detail"),
    path("vouchers/<int:voucher_id>/edit/", views_pages.voucher_update, name="voucher_update"),
    
    # 账簿管理
    path("ledgers/", views_pages.ledger_management, name="ledger_management"),
    path("ledgers/<int:ledger_id>/", views_pages.ledger_detail, name="ledger_detail"),
    
    # 预算管理
    path("budgets/", views_pages.budget_management, name="budget_management"),
    path("budgets/create/", views_pages.budget_create, name="budget_create"),
    path("budgets/<int:budget_id>/", views_pages.budget_detail, name="budget_detail"),
    path("budgets/<int:budget_id>/edit/", views_pages.budget_update, name="budget_update"),
    
    # 发票管理
    path("invoices/", views_pages.invoice_management, name="invoice_management"),
    path("invoices/create/", views_pages.invoice_create, name="invoice_create"),
    path("invoices/<int:invoice_id>/", views_pages.invoice_detail, name="invoice_detail"),
    path("invoices/<int:invoice_id>/edit/", views_pages.invoice_update, name="invoice_update"),
    
    # 资金流水
    path("fund-flows/", views_pages.fund_flow_management, name="fund_flow_management"),
    path("fund-flows/create/", views_pages.fund_flow_create, name="fund_flow_create"),
    path("fund-flows/<int:fund_flow_id>/", views_pages.fund_flow_detail, name="fund_flow_detail"),
    path("fund-flows/<int:fund_flow_id>/edit/", views_pages.fund_flow_update, name="fund_flow_update"),
]

