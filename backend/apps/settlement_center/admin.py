"""
结算中心模块的Admin配置
注意：业务模块数据应在前端管理，不再在Django Admin中显示
这些数据应通过API接口在前端管理
"""

from django.contrib import admin
from django.db.models import Sum
from .models import (
    OutputValueStage, OutputValueMilestone, OutputValueEvent, OutputValueRecord,
    ProjectSettlement, SettlementItem, ServiceFeeRate, ContractSettlement
)


# 所有业务模型的Admin注册已注释，改为在前端管理
# 如需查看数据，请使用API接口或前端管理页面

# @admin.register(OutputValueStage)
# class OutputValueStageAdmin(admin.ModelAdmin):
#     ...

# @admin.register(OutputValueMilestone)
# class OutputValueMilestoneAdmin(admin.ModelAdmin):
#     ...

# @admin.register(OutputValueEvent)
# class OutputValueEventAdmin(admin.ModelAdmin):
#     ...

# @admin.register(OutputValueRecord)
# class OutputValueRecordAdmin(admin.ModelAdmin):
#     ...

# @admin.register(ProjectSettlement)
# class ProjectSettlementAdmin(admin.ModelAdmin):
#     ...

# @admin.register(ServiceFeeRate)
# class ServiceFeeRateAdmin(admin.ModelAdmin):
#     ...

# @admin.register(SettlementItem)
# class SettlementItemAdmin(admin.ModelAdmin):
#     ...

# @admin.register(ContractSettlement)
# class ContractSettlementAdmin(admin.ModelAdmin):
#     ...
