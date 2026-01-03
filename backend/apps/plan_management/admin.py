"""
计划管理模块的所有模型已从后台管理中移除，请使用前端管理页面
前端管理页面路径：/plan/
"""

# from django.contrib import admin
# from .models import (
#     StrategicGoal,
#     GoalStatusLog,
#     GoalProgressRecord,
#     GoalAdjustment,
#     GoalAlignmentRecord,
#     Plan,
#     PlanStatusLog,
#     PlanProgressRecord,
#     PlanIssue,
#     PlanApproval,
# )
# from backend.core.admin_base import BaseModelAdmin, AuditAdminMixin, ReadOnlyAdminMixin


# ==================== 战略目标管理 ====================
# 所有模型已从后台管理中移除，请使用前端管理页面

# @admin.register(StrategicGoal)
# class StrategicGoalAdmin(AuditAdminMixin, BaseModelAdmin):
#     """战略目标管理"""
#     pass

# @admin.register(GoalStatusLog)
# class GoalStatusLogAdmin(ReadOnlyAdminMixin, BaseModelAdmin):
#     """目标状态日志管理（只读）"""
#     pass

# @admin.register(GoalProgressRecord)
# class GoalProgressRecordAdmin(ReadOnlyAdminMixin, BaseModelAdmin):
#     """目标进度记录管理（只读）"""
#     pass

# @admin.register(GoalAdjustment)
# class GoalAdjustmentAdmin(AuditAdminMixin, BaseModelAdmin):
#     """目标调整申请管理"""
#     pass

# @admin.register(GoalAlignmentRecord)
# class GoalAlignmentRecordAdmin(ReadOnlyAdminMixin, BaseModelAdmin):
#     """目标对齐度记录管理（只读）"""
#     pass


# ==================== 计划管理 ====================
# 所有模型已从后台管理中移除，请使用前端管理页面

# @admin.register(Plan)
# class PlanAdmin(AuditAdminMixin, BaseModelAdmin):
#     """计划管理"""
#     pass

# @admin.register(PlanStatusLog)
# class PlanStatusLogAdmin(ReadOnlyAdminMixin, BaseModelAdmin):
#     """计划状态日志管理（只读）"""
#     pass

# @admin.register(PlanProgressRecord)
# class PlanProgressRecordAdmin(ReadOnlyAdminMixin, BaseModelAdmin):
#     """计划进度记录管理（只读）"""
#     pass

# @admin.register(PlanIssue)
# class PlanIssueAdmin(AuditAdminMixin, BaseModelAdmin):
#     """计划问题管理"""
#     pass

# @admin.register(PlanApproval)
# class PlanApprovalAdmin(ReadOnlyAdminMixin, BaseModelAdmin):
#     """计划审批记录管理（只读）"""
#     pass
