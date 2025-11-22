"""
生产质量模块的Admin配置
注意：业务模块数据应在前端管理，不再在Django Admin中显示
这些数据应通过API接口在前端管理
"""

from django.contrib import admin

from .models import (
    Opinion,
    OpinionAttachment,
    OpinionReview,
    ProductionReport,
    ProductionReportSection,
    ProductionStatistic,
)


# 所有业务模型的Admin注册已注释，改为在前端管理
# 如需查看数据，请使用API接口或前端管理页面

# @admin.register(Opinion)
# class OpinionAdmin(admin.ModelAdmin):
#     ...

# @admin.register(ProductionReport)
# class ProductionReportAdmin(admin.ModelAdmin):
#     ...

# @admin.register(ProductionReportSection)
# class ProductionReportSectionAdmin(admin.ModelAdmin):
#     ...

# @admin.register(ProductionStatistic)
# class ProductionStatisticAdmin(admin.ModelAdmin):
#     ...

# @admin.register(OpinionAttachment)
# class OpinionAttachmentAdmin(admin.ModelAdmin):
#     ...

# @admin.register(OpinionReview)
# class OpinionReviewAdmin(admin.ModelAdmin):
#     ...
