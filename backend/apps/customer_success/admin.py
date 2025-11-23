"""
客户成功模块的Admin配置
注意：业务模块数据应在前端管理，不再在Django Admin中显示
这些数据应通过API接口在前端管理
"""

from django.contrib import admin
from .models import (
    Client,
    ClientContact,
    BusinessContract,
    BusinessPaymentPlan,
    ContractFile,
    ContractApproval,
    ContractChange,
    ContractStatusLog,
)


# 所有业务模型的Admin注册已注释，改为在前端管理
# 如需查看数据，请使用API接口或前端管理页面

# @admin.register(Client)
# class ClientAdmin(admin.ModelAdmin):
#     ...

# @admin.register(ClientContact)
# class ClientContactAdmin(admin.ModelAdmin):
#     ...

# @admin.register(BusinessContract)
# class BusinessContractAdmin(admin.ModelAdmin):
#     ...

# @admin.register(BusinessPaymentPlan)
# class BusinessPaymentPlanAdmin(admin.ModelAdmin):
#     ...

# @admin.register(ContractFile)
# class ContractFileAdmin(admin.ModelAdmin):
#     ...

# @admin.register(ContractApproval)
# class ContractApprovalAdmin(admin.ModelAdmin):
#     ...

# @admin.register(ContractChange)
# class ContractChangeAdmin(admin.ModelAdmin):
#     ...

# @admin.register(ContractStatusLog)
# class ContractStatusLogAdmin(admin.ModelAdmin):
#     ...
