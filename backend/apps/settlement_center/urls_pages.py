from django.urls import path
from . import views_pages
from . import views_settlement_items

app_name = "settlement_pages"

urlpatterns = [
    # 结算管理首页
    path("home/", views_pages.settlement_management_home, name="settlement_management_home"),
    
    # 项目结算管理
    path("project-settlement/", views_pages.project_settlement_list, name="project_settlement_list"),
    path("project-settlement/create/", views_pages.project_settlement_create, name="project_settlement_create"),
    path("project-settlement/<int:settlement_id>/", views_pages.project_settlement_detail, name="project_settlement_detail"),
    path("project-settlement/<int:settlement_id>/edit/", views_pages.project_settlement_update, name="project_settlement_update"),
    path("project-settlement/<int:settlement_id>/submit/", views_pages.project_settlement_submit, name="project_settlement_submit"),
    
    # 结算明细项管理
    path("settlement-item/<int:item_id>/review/", views_settlement_items.settlement_item_review, name="settlement_item_review"),
    path("settlement/<int:settlement_id>/generate-items/", views_settlement_items.generate_items_from_opinions, name="generate_items_from_opinions"),
    
    # 合同结算管理（如果存在）
    # path("contract-settlement/", views_pages.contract_settlement_list, name="contract_settlement_list"),
]
