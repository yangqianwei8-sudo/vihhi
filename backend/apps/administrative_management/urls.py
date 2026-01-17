from django.urls import path
from . import views_pages

app_name = "admin_pages"

urlpatterns = [
    # 行政管理主页（行政事务列表）
    path("", views_pages.administrative_home, name="administrative_home"),
    path("home/", views_pages.administrative_home, name="administrative_management_home"),
    
    # 行政事务管理
    path("affairs/", views_pages.affair_list, name="affair_list"),
    path("affairs/create/", views_pages.affair_create, name="affair_create"),
    path("affairs/<int:affair_id>/", views_pages.affair_detail, name="affair_detail"),
    path("affairs/<int:affair_id>/edit/", views_pages.affair_update, name="affair_update"),
    path("affairs/<int:affair_id>/start/", views_pages.affair_start, name="affair_start"),
    path("affairs/<int:affair_id>/complete/", views_pages.affair_complete, name="affair_complete"),
    path("affairs/<int:affair_id>/cancel/", views_pages.affair_cancel, name="affair_cancel"),
    path("affairs/<int:affair_id>/progress/", views_pages.affair_add_progress, name="affair_add_progress"),
    
    # 用品分类管理
    path("supplies/categories/", views_pages.supply_category_list, name="supply_category_list"),
    path("supplies/categories/create/", views_pages.supply_category_create, name="supply_category_create"),
    path("supplies/categories/<int:category_id>/edit/", views_pages.supply_category_update, name="supply_category_update"),
    path("supplies/categories/<int:category_id>/delete/", views_pages.supply_category_delete, name="supply_category_delete"),
    
    # 办公用品
    path("supplies/", views_pages.supplies_management, name="supplies_management"),
    path("supplies/create/", views_pages.supply_create, name="supply_create"),
    path("supplies/<int:supply_id>/", views_pages.supply_detail, name="supply_detail"),
    path("supplies/<int:supply_id>/edit/", views_pages.supply_update, name="supply_update"),
    
    # 采购管理
    path("supplies/purchases/", views_pages.supply_purchase_list, name="supply_purchase_list"),
    path("supplies/purchases/create/", views_pages.supply_purchase_create, name="supply_purchase_create"),
    path("supplies/purchases/<int:purchase_id>/", views_pages.supply_purchase_detail, name="supply_purchase_detail"),
    path("supplies/purchases/<int:purchase_id>/edit/", views_pages.supply_purchase_update, name="supply_purchase_update"),
    path("supplies/purchases/<int:purchase_id>/approve/", views_pages.supply_purchase_approve, name="supply_purchase_approve"),
    path("supplies/purchases/<int:purchase_id>/receive/", views_pages.supply_purchase_receive, name="supply_purchase_receive"),
    
    # 领用管理
    path("supplies/requests/", views_pages.supply_request_list, name="supply_request_list"),
    path("supplies/requests/create/", views_pages.supply_request_create, name="supply_request_create"),
    path("supplies/requests/<int:request_id>/", views_pages.supply_request_detail, name="supply_request_detail"),
    path("supplies/requests/<int:request_id>/edit/", views_pages.supply_request_update, name="supply_request_update"),
    path("supplies/requests/<int:request_id>/approve/", views_pages.supply_request_approve, name="supply_request_approve"),
    path("supplies/requests/<int:request_id>/issue/", views_pages.supply_request_issue, name="supply_request_issue"),
    
    # 会议室管理
    path("meeting-rooms/", views_pages.meeting_room_management, name="meeting_room_management"),
    path("meeting-rooms/create/", views_pages.meeting_room_create, name="meeting_room_create"),
    path("meeting-rooms/<int:room_id>/", views_pages.meeting_room_detail, name="meeting_room_detail"),
    path("meeting-rooms/<int:room_id>/edit/", views_pages.meeting_room_update, name="meeting_room_update"),
    
    # 会议室预订管理
    path("meeting-rooms/bookings/", views_pages.meeting_room_booking_list, name="meeting_room_booking_list"),
    path("meeting-rooms/bookings/create/", views_pages.meeting_room_booking_create, name="meeting_room_booking_create"),
    path("meeting-rooms/bookings/<int:booking_id>/", views_pages.meeting_room_booking_detail, name="meeting_room_booking_detail"),
    path("meeting-rooms/bookings/<int:booking_id>/edit/", views_pages.meeting_room_booking_update, name="meeting_room_booking_update"),
    path("meeting-rooms/bookings/<int:booking_id>/confirm/", views_pages.meeting_room_booking_confirm, name="meeting_room_booking_confirm"),
    path("meeting-rooms/bookings/<int:booking_id>/cancel/", views_pages.meeting_room_booking_cancel, name="meeting_room_booking_cancel"),
    
    # 会议安排
    path("meetings/", views_pages.meeting_list, name="meeting_list"),
    path("meetings/create/", views_pages.meeting_create, name="meeting_create"),
    path("meetings/<int:meeting_id>/", views_pages.meeting_detail, name="meeting_detail"),
    path("meetings/<int:meeting_id>/edit/", views_pages.meeting_update, name="meeting_update"),
    path("meetings/<int:meeting_id>/cancel/", views_pages.meeting_cancel, name="meeting_cancel"),
    path("meetings/<int:meeting_id>/record/", views_pages.meeting_record_create, name="meeting_record_create"),
    path("meetings/<int:meeting_id>/record/edit/", views_pages.meeting_record_update, name="meeting_record_update"),
    
    # 用车管理
    path("vehicles/", views_pages.vehicle_management, name="vehicle_management"),
    path("vehicles/create/", views_pages.vehicle_create, name="vehicle_create"),
    path("vehicles/<int:vehicle_id>/", views_pages.vehicle_detail, name="vehicle_detail"),
    path("vehicles/<int:vehicle_id>/edit/", views_pages.vehicle_update, name="vehicle_update"),
    
    # 用车申请管理
    path("vehicles/bookings/", views_pages.vehicle_booking_list, name="vehicle_booking_list"),
    path("vehicles/bookings/create/", views_pages.vehicle_booking_create, name="vehicle_booking_create"),
    path("vehicles/bookings/<int:booking_id>/", views_pages.vehicle_booking_detail, name="vehicle_booking_detail"),
    path("vehicles/bookings/<int:booking_id>/edit/", views_pages.vehicle_booking_update, name="vehicle_booking_update"),
    path("vehicles/bookings/<int:booking_id>/approve/", views_pages.vehicle_booking_approve, name="vehicle_booking_approve"),
    path("vehicles/bookings/<int:booking_id>/reject/", views_pages.vehicle_booking_reject, name="vehicle_booking_reject"),
    path("vehicles/bookings/<int:booking_id>/dispatch/", views_pages.vehicle_booking_dispatch, name="vehicle_booking_dispatch"),
    path("vehicles/bookings/<int:booking_id>/return/", views_pages.vehicle_booking_return, name="vehicle_booking_return"),
    
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
    
    # 资产转移
    path("assets/transfers/", views_pages.asset_transfer_list, name="asset_transfer_list"),
    path("assets/<int:asset_id>/transfer/", views_pages.asset_transfer_create, name="asset_transfer_create"),
    path("assets/transfers/<int:transfer_id>/", views_pages.asset_transfer_detail, name="asset_transfer_detail"),
    path("assets/transfers/<int:transfer_id>/approve/", views_pages.asset_transfer_approve, name="asset_transfer_approve"),
    path("assets/transfers/<int:transfer_id>/complete/", views_pages.asset_transfer_complete, name="asset_transfer_complete"),
    
    # 资产维护
    path("assets/<int:asset_id>/maintenance/", views_pages.asset_maintenance_create, name="asset_maintenance_create"),
    path("assets/maintenances/<int:maintenance_id>/", views_pages.asset_maintenance_detail, name="asset_maintenance_detail"),
    path("assets/maintenances/<int:maintenance_id>/edit/", views_pages.asset_maintenance_update, name="asset_maintenance_update"),
    
    # 差旅管理
    path("travels/", views_pages.travel_list, name="travel_list"),
    path("travels/create/", views_pages.travel_create, name="travel_create"),
    path("travels/<int:travel_id>/", views_pages.travel_detail, name="travel_detail"),
    path("travels/<int:travel_id>/edit/", views_pages.travel_update, name="travel_update"),
    path("travels/<int:travel_id>/approve/", views_pages.travel_approve, name="travel_approve"),
    path("travels/<int:travel_id>/reject/", views_pages.travel_reject, name="travel_reject"),
    
    # 报销管理
    path("expenses/", views_pages.expense_management, name="expense_management"),
    path("expenses/create/", views_pages.expense_create, name="expense_create"),
    path("expenses/<int:expense_id>/", views_pages.expense_detail, name="expense_detail"),
    path("expenses/<int:expense_id>/edit/", views_pages.expense_update, name="expense_update"),
    
    # 供应商管理
    path("suppliers/", views_pages.supplier_list, name="supplier_list"),
    path("suppliers/create/", views_pages.supplier_create, name="supplier_create"),
    path("suppliers/<int:supplier_id>/", views_pages.supplier_detail, name="supplier_detail"),
    path("suppliers/<int:supplier_id>/edit/", views_pages.supplier_update, name="supplier_update"),
    
    # 采购合同管理
    path("purchases/contracts/", views_pages.purchase_contract_list, name="purchase_contract_list"),
    path("purchases/contracts/create/", views_pages.purchase_contract_create, name="purchase_contract_create"),
    path("purchases/contracts/<int:contract_id>/", views_pages.purchase_contract_detail, name="purchase_contract_detail"),
    path("purchases/contracts/<int:contract_id>/edit/", views_pages.purchase_contract_update, name="purchase_contract_update"),
    
    # 采购付款管理
    path("purchases/payments/", views_pages.purchase_payment_list, name="purchase_payment_list"),
    path("purchases/payments/create/", views_pages.purchase_payment_create, name="purchase_payment_create"),
    path("purchases/payments/create/<int:contract_id>/", views_pages.purchase_payment_create, name="purchase_payment_create_for_contract"),
    path("purchases/payments/<int:payment_id>/", views_pages.purchase_payment_detail, name="purchase_payment_detail"),
    path("purchases/payments/<int:payment_id>/confirm/", views_pages.purchase_payment_confirm, name="purchase_payment_confirm"),
    
    # 库存盘点管理
    path("supplies/inventory/checks/", views_pages.inventory_check_list, name="inventory_check_list"),
    path("supplies/inventory/checks/create/", views_pages.inventory_check_create, name="inventory_check_create"),
    path("supplies/inventory/checks/<int:check_id>/", views_pages.inventory_check_detail, name="inventory_check_detail"),
    path("supplies/inventory/checks/<int:check_id>/edit/", views_pages.inventory_check_update, name="inventory_check_update"),
    path("supplies/inventory/checks/<int:check_id>/approve/", views_pages.inventory_check_approve, name="inventory_check_approve"),
    
    # 库存调整管理
    path("supplies/inventory/adjusts/", views_pages.inventory_adjust_list, name="inventory_adjust_list"),
    path("supplies/inventory/adjusts/create/", views_pages.inventory_adjust_create, name="inventory_adjust_create"),
    path("supplies/inventory/adjusts/<int:adjust_id>/", views_pages.inventory_adjust_detail, name="inventory_adjust_detail"),
    path("supplies/inventory/adjusts/<int:adjust_id>/edit/", views_pages.inventory_adjust_update, name="inventory_adjust_update"),
    path("supplies/inventory/adjusts/<int:adjust_id>/approve/", views_pages.inventory_adjust_approve, name="inventory_adjust_approve"),
    path("supplies/inventory/adjusts/<int:adjust_id>/execute/", views_pages.inventory_adjust_execute, name="inventory_adjust_execute"),
]

