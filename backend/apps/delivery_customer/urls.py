from django.urls import path

from . import views_pages

app_name = "delivery"

urlpatterns = [
    path("report/", views_pages.report_delivery, name="report_delivery"),
    path("collaboration/", views_pages.customer_collaboration, name="customer_collaboration"),
    path("portal/", views_pages.customer_portal, name="customer_portal"),
    path("signature/", views_pages.electronic_signature, name="electronic_signature"),
]

