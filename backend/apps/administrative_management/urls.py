from django.urls import path
from . import views_pages

app_name = "admin_pages"

urlpatterns = [
    # 行政管理主页
    path("", views_pages.administrative_home, name="administrative_home"),
    
    # 办公用品
    path("supplies/", views_pages.supplies_management, name="supplies_management"),
    path("supplies/create/", views_pages.supply_create, name="supply_create"),
    path("supplies/<int:supply_id>/", views_pages.supply_detail, name="supply_detail"),
    path("supplies/<int:supply_id>/edit/", views_pages.supply_update, name="supply_update"),
    
    # 会议室
    path("meeting-rooms/", views_pages.meeting_room_management, name="meeting_room_management"),
    path("meeting-rooms/create/", views_pages.meeting_room_create, name="meeting_room_create"),
    path("meeting-rooms/<int:room_id>/", views_pages.meeting_room_detail, name="meeting_room_detail"),
    path("meeting-rooms/<int:room_id>/edit/", views_pages.meeting_room_update, name="meeting_room_update"),
    
    # 用车管理
    path("vehicles/", views_pages.vehicle_management, name="vehicle_management"),
    path("vehicles/create/", views_pages.vehicle_create, name="vehicle_create"),
    path("vehicles/<int:vehicle_id>/", views_pages.vehicle_detail, name="vehicle_detail"),
    path("vehicles/<int:vehicle_id>/edit/", views_pages.vehicle_update, name="vehicle_update"),
    
    # 接待管理
    path("receptions/", views_pages.reception_management, name="reception_management"),
    path("receptions/create/", views_pages.reception_create, name="reception_create"),
    path("receptions/<int:reception_id>/", views_pages.reception_detail, name="reception_detail"),
    path("receptions/<int:reception_id>/edit/", views_pages.reception_update, name="reception_update"),
    
    # 公告通知
    path("announcements/", views_pages.announcement_management, name="announcement_management"),
    path("announcements/create/", views_pages.announcement_create, name="announcement_create"),
    path("announcements/<int:announcement_id>/", views_pages.announcement_detail, name="announcement_detail"),
    path("announcements/<int:announcement_id>/edit/", views_pages.announcement_update, name="announcement_update"),
    
    # 印章管理
    path("seals/", views_pages.seal_management, name="seal_management"),
    path("seals/create/", views_pages.seal_create, name="seal_create"),
    path("seals/<int:seal_id>/", views_pages.seal_detail, name="seal_detail"),
    path("seals/<int:seal_id>/edit/", views_pages.seal_update, name="seal_update"),
    
    # 固定资产
    path("assets/", views_pages.asset_management, name="asset_management"),
    path("assets/create/", views_pages.asset_create, name="asset_create"),
    path("assets/<int:asset_id>/", views_pages.asset_detail, name="asset_detail"),
    path("assets/<int:asset_id>/edit/", views_pages.asset_update, name="asset_update"),
    
    # 报销管理
    path("expenses/", views_pages.expense_management, name="expense_management"),
    path("expenses/create/", views_pages.expense_create, name="expense_create"),
    path("expenses/<int:expense_id>/", views_pages.expense_detail, name="expense_detail"),
    path("expenses/<int:expense_id>/edit/", views_pages.expense_update, name="expense_update"),
]

