from django.urls import path
from . import views_pages

app_name = "payment_pages"

urlpatterns = [
    # 回款管理首页
    path("home/", views_pages.payment_home, name="payment_home"),
    
    # 回款管理
    path("payment-plans/", views_pages.payment_plan_list, name="payment_plan_list"),
    path("payment-plans/<str:plan_type>/<int:plan_id>/", views_pages.payment_plan_detail, name="payment_plan_detail"),
    path("payment-records/", views_pages.payment_record_list, name="payment_record_list"),
    path("payment-records/create/<str:plan_type>/<int:plan_id>/", views_pages.payment_record_create, name="payment_record_create"),
]
