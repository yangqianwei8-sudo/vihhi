# 商机管理模块的Django Admin配置
from django.contrib import admin
from backend.core.admin_base import BaseModelAdmin
from .models import (
    BusinessOpportunity,
    OpportunityFollowUp,
    OpportunityQuotation,
    OpportunityApproval,
    OpportunityStatusLog,
    QuotationRule,
    BusinessNegotiation,
    OpportunityFiling,
    BiddingQuotation,
    CustomerRequirementCommunication,
)

# 注意：业务模块数据应在前端管理，不再在Django Admin中显示
# 这些数据应通过API接口在前端管理
# 如果需要，可以在这里注册模型用于后台管理
