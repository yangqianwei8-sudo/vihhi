from django.urls import path

from . import views_pages

app_name = "business"

urlpatterns = [
    path("customers/", views_pages.customer_management, name="customer_management"),
    path("contracts/", views_pages.contract_management, name="contract_management"),
    path("contracts/<int:contract_id>/", views_pages.contract_detail, name="contract_detail"),
    path("contracts/<int:contract_id>/transition/", views_pages.contract_status_transition, name="contract_status_transition"),
    path("contracts/create/", views_pages.contract_create, name="contract_create"),
    path("contracts/<int:contract_id>/edit/", views_pages.contract_edit, name="contract_edit"),
    path("settlements/", views_pages.project_settlement, name="project_settlement"),
    path("analysis/", views_pages.output_analysis, name="output_analysis"),
    path("payments/", views_pages.payment_tracking, name="payment_tracking"),
]

