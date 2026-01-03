"""
人事管理模块的Admin配置
注意：业务模块数据应在前端管理，不再在Django Admin中显示
这些数据应通过API接口在前端管理
"""

from django.contrib import admin
from django.utils.html import format_html
from django.urls import reverse
from django.db.models import Count, Sum
from backend.apps.personnel_management.models import (
    Employee, Attendance, Leave, Training, TrainingParticipant,
    Performance, Salary, LaborContract,
)


# 所有业务模型的Admin注册已注释，改为在前端管理
# 如需查看数据，请使用API接口或前端管理页面

# ==================== 员工档案管理 ====================
# @admin.register(Employee)
# class EmployeeAdmin(admin.ModelAdmin):
#     """员工档案管理"""
#     ...


# ==================== 考勤管理 ====================
# @admin.register(Attendance)
# class AttendanceAdmin(admin.ModelAdmin):
#     """考勤记录管理"""
#     ...


# ==================== 请假管理 ====================
# @admin.register(Leave)
# class LeaveAdmin(admin.ModelAdmin):
#     """请假申请管理"""
#     ...


# ==================== 培训管理 ====================
# @admin.register(Training)
# class TrainingAdmin(admin.ModelAdmin):
#     """培训记录管理"""
#     ...

# @admin.register(TrainingParticipant)
# class TrainingParticipantAdmin(admin.ModelAdmin):
#     """培训参与人员管理"""
#     ...


# ==================== 绩效考核 ====================
# @admin.register(Performance)
# class PerformanceAdmin(admin.ModelAdmin):
#     """绩效考核管理"""
#     ...


# ==================== 薪资管理 ====================
# @admin.register(Salary)
# class SalaryAdmin(admin.ModelAdmin):
#     """薪资记录管理"""
#     ...


# ==================== 劳动合同 ====================
# @admin.register(LaborContract)
# class LaborContractAdmin(admin.ModelAdmin):
#     """劳动合同管理"""
#     ...
