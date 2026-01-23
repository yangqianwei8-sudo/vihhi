"""
计划管理模块后台管理配置
优化后的后台管理，提供数据维护、调试和日志查看功能
"""
from django.contrib import admin
from django.utils.html import format_html
from django.urls import reverse
from django.utils import timezone
from django.db.models import Count, Q
from django.contrib import messages
from datetime import date, timedelta

from backend.core.admin_base import (
    BaseModelAdmin, 
    AuditAdminMixin, 
    ReadOnlyAdminMixin,
    StatusBadgeMixin,
    ExportMixin
)
from .models import (
    StrategicGoal,
    GoalStatusLog,
    GoalProgressRecord,
    GoalAdjustment,
    GoalAlignmentRecord,
    Plan,
    PlanStatusLog,
    PlanProgressRecord,
    PlanIssue,
    PlanDecision,
    PlanAdjustment,
    PlanInactivityLog,
    TodoTask,
    WorkSummary,
    ApprovalNotification,
)


# ==================== 战略目标管理 ====================

@admin.register(StrategicGoal)
class StrategicGoalAdmin(StatusBadgeMixin, AuditAdminMixin, BaseModelAdmin):
    """战略目标管理"""
    
    # 列表显示
    list_display = (
        'goal_number', 
        'name', 
        'level_badge',
        'status_badge',
        'owner_link',
        'parent_goal_link',
        'completion_rate_display',
        'start_date',
        'end_date',
        'overdue_indicator',
        'created_time'
    )
    
    # 列表筛选
    list_filter = (
        'level',
        'status',
        'goal_type',
        'goal_period',
        ('start_date', admin.DateFieldListFilter),
        ('end_date', admin.DateFieldListFilter),
        ('created_time', admin.DateFieldListFilter),
    )
    
    # 搜索字段
    search_fields = (
        'goal_number',
        'name',
        'indicator_name',
        'owner__username',
        'owner__full_name',
        'responsible_person__username',
        'responsible_person__full_name',
    )
    
    # 查询优化
    select_related_fields = [
        'owner',
        'parent_goal',
        'responsible_person',
        'responsible_department',
        'created_by',
    ]
    prefetch_related_fields = [
        'participants',
        'child_goals',
    ]
    
    # 只读字段
    readonly_fields = (
        'goal_number',
        'created_time',
        'updated_time',
        'published_at',
        'accepted_at',
        'completed_at',
        'duration_days',
        'completion_rate',
    )
    
    # 字段分组
    fieldsets = (
        ('基本信息', {
            'fields': (
                'goal_number',
                'name',
                'level',
                'goal_type',
                'goal_period',
                'status',
            )
        }),
        ('目标指标', {
            'fields': (
                'indicator_name',
                'indicator_type',
                'indicator_unit',
                'target_value',
                'current_value',
                'completion_rate',
            )
        }),
        ('责任人信息', {
            'fields': (
                'owner',
                'responsible_person',
                'responsible_department',
            )
        }),
        ('时间信息', {
            'fields': (
                'start_date',
                'end_date',
                'duration_days',
            )
        }),
        ('状态时间戳（P2-1）', {
            'fields': (
                'published_at',
                'accepted_at',
                'completed_at',
            ),
            'classes': ('collapse',),
        }),
        ('关联信息', {
            'fields': (
                'parent_goal',
                'participants',
            ),
            'classes': ('collapse',),
        }),
        ('其他信息', {
            'fields': (
                'background',
                'significance',
                'weight',
                'weight_description',
                'notes',
            ),
            'classes': ('collapse',),
        }),
        ('系统信息', {
            'fields': (
                'created_by',
                'created_time',
                'updated_time',
            ),
            'classes': ('collapse',),
        }),
    )
    
    # 批量操作
    actions = ['mark_as_published', 'mark_as_completed', 'mark_as_cancelled']
    
    def level_badge(self, obj):
        """层级标签"""
        colors = {
            'company': '#007bff',
            'personal': '#28a745',
        }
        color = colors.get(obj.level, '#6c757d')
        return format_html(
            '<span style="background-color: {}; color: white; padding: 2px 8px; border-radius: 3px; font-size: 11px;">{}</span>',
            color,
            obj.get_level_display()
        )
    level_badge.short_description = '层级'
    
    def status_badge(self, obj):
        """状态标签"""
        color_map = {
            'draft': '#6c757d',
            'published': '#17a2b8',
            'accepted': '#ffc107',
            'in_progress': '#007bff',
            'completed': '#28a745',
            'cancelled': '#dc3545',
        }
        return self.format_status_badge(
            obj.status,
            obj.get_status_display(),
            color_map
        )
    status_badge.short_description = '状态'
    
    def owner_link(self, obj):
        """所有者链接"""
        if obj.owner:
            url = reverse('admin:system_management_user_change', args=[obj.owner.id])
            return format_html('<a href="{}">{}</a>', url, obj.owner.get_full_name() or obj.owner.username)
        return '-'
    owner_link.short_description = '所有者'
    
    def parent_goal_link(self, obj):
        """父目标链接"""
        if obj.parent_goal:
            url = reverse('admin:plan_management_strategicgoal_change', args=[obj.parent_goal.id])
            return format_html('<a href="{}">{}</a>', url, obj.parent_goal.name)
        return '-'
    parent_goal_link.short_description = '父目标'
    
    def completion_rate_display(self, obj):
        """完成率显示（带颜色）"""
        try:
            rate = float(obj.completion_rate) if obj.completion_rate is not None else 0.0
        except (ValueError, TypeError):
            rate = 0.0
        
        if rate >= 100:
            color = '#28a745'
        elif rate >= 80:
            color = '#007bff'
        elif rate >= 50:
            color = '#ffc107'
        else:
            color = '#dc3545'
        # 先格式化数值，再传递给 format_html，避免 SafeString 格式化问题
        rate_str = f'{rate:.1f}%'
        return format_html(
            '<span style="color: {}; font-weight: bold;">{}</span>',
            color,
            rate_str
        )
    completion_rate_display.short_description = '完成率'
    
    def overdue_indicator(self, obj):
        """逾期指示器"""
        if obj.status in ['published', 'accepted', 'in_progress']:
            if obj.end_date and obj.end_date < date.today():
                days = (date.today() - obj.end_date).days
                return format_html(
                    '<span style="color: red; font-weight: bold;">⚠️ 逾期 {} 天</span>',
                    days
                )
        return '-'
    overdue_indicator.short_description = '逾期状态'
    
    # 批量操作
    def mark_as_published(self, request, queryset):
        """批量标记为已发布"""
        from .notifications import notify_company_goal_published, notify_personal_goal_published
        
        count = 0
        for goal in queryset.filter(status='draft'):
            try:
                goal.transition_to('published', user=request.user)
                # P2-2: 发送发布通知
                if goal.level == 'company':
                    notify_company_goal_published(goal)
                elif goal.level == 'personal':
                    notify_personal_goal_published(goal)
                count += 1
            except ValueError as e:
                pass
        self.message_user(request, f'成功发布 {count} 个目标', messages.SUCCESS)
    mark_as_published.short_description = '批量发布（draft → published）'
    
    def mark_as_completed(self, request, queryset):
        """批量标记为已完成"""
        count = 0
        for goal in queryset.filter(status='in_progress'):
            try:
                goal.transition_to('completed', user=request.user)
                count += 1
            except ValueError:
                pass
        self.message_user(request, f'成功完成 {count} 个目标', messages.SUCCESS)
    mark_as_completed.short_description = '批量完成（in_progress → completed）'
    
    def mark_as_cancelled(self, request, queryset):
        """批量标记为已取消"""
        count = 0
        for goal in queryset.filter(status__in=['draft', 'published', 'accepted', 'in_progress']):
            try:
                goal.transition_to('cancelled', user=request.user)
                count += 1
            except ValueError:
                pass
        self.message_user(request, f'成功取消 {count} 个目标', messages.SUCCESS)
    mark_as_cancelled.short_description = '批量取消'
    
    def has_change_permission(self, request, obj=None):
        """控制修改权限"""
        if request.user.is_superuser:
            return True
        
        # 已发布/已接收的目标，不允许在后台直接修改（应通过前端流程）
        if obj and obj.status in ['published', 'accepted', 'in_progress', 'completed']:
            return False
        
        return super().has_change_permission(request, obj)


# ==================== 目标日志（只读）====================

@admin.register(GoalStatusLog)
class GoalStatusLogAdmin(ReadOnlyAdminMixin, BaseModelAdmin):
    """目标状态日志管理（只读）"""
    
    list_display = (
        'goal_link',
        'status_transition',
        'changed_by',
        'changed_time',
        'change_reason',
    )
    
    list_filter = (
        'old_status',
        'new_status',
        ('changed_time', admin.DateFieldListFilter),
    )
    
    search_fields = (
        'goal__goal_number',
        'goal__name',
        'changed_by__username',
        'change_reason',
    )
    
    select_related_fields = ['goal', 'changed_by']
    
    readonly_fields = ('goal', 'old_status', 'new_status', 'changed_by', 'changed_time', 'change_reason', 'notes')
    
    def goal_link(self, obj):
        """目标链接"""
        url = reverse('admin:plan_management_strategicgoal_change', args=[obj.goal.id])
        return format_html('<a href="{}">{}</a>', url, obj.goal.name)
    goal_link.short_description = '目标'
    
    def status_transition(self, obj):
        """状态转换显示"""
        return format_html(
            '<span style="color: gray;">{}</span> → <span style="color: green; font-weight: bold;">{}</span>',
            obj.get_old_status_display() if hasattr(obj, 'get_old_status_display') else obj.old_status,
            obj.get_new_status_display() if hasattr(obj, 'get_new_status_display') else obj.new_status
        )
    status_transition.short_description = '状态转换'


@admin.register(GoalProgressRecord)
class GoalProgressRecordAdmin(ReadOnlyAdminMixin, BaseModelAdmin):
    """目标进度记录管理（只读）"""
    
    list_display = (
        'goal_link',
        'current_value',
        'completion_rate',
        'recorded_by',
        'recorded_time',
    )
    
    list_filter = (
        ('recorded_time', admin.DateFieldListFilter),
    )
    
    search_fields = (
        'goal__goal_number',
        'goal__name',
        'recorded_by__username',
    )
    
    select_related_fields = ['goal', 'recorded_by']
    
    readonly_fields = ('goal', 'current_value', 'completion_rate', 'progress_description', 'recorded_by', 'recorded_time', 'notes')
    
    def goal_link(self, obj):
        """目标链接"""
        url = reverse('admin:plan_management_strategicgoal_change', args=[obj.goal.id])
        return format_html('<a href="{}">{}</a>', url, obj.goal.name)
    goal_link.short_description = '目标'


# ==================== 目标调整申请 ====================

@admin.register(GoalAdjustment)
class GoalAdjustmentAdmin(StatusBadgeMixin, AuditAdminMixin, BaseModelAdmin):
    """目标调整申请管理"""
    
    list_display = (
        'goal_link',
        'status_badge',
        'created_by',
        'created_time',
        'approved_by',
        'approved_time',
    )
    
    list_filter = (
        'status',
        ('created_time', admin.DateFieldListFilter),
        ('approved_time', admin.DateFieldListFilter),
    )
    
    search_fields = (
        'goal__goal_number',
        'goal__name',
        'adjustment_reason',
        'created_by__username',
    )
    
    select_related_fields = ['goal', 'created_by', 'approved_by']
    
    readonly_fields = (
        'goal',
        'created_time',
        'updated_time',
        'approved_time',
    )
    
    fieldsets = (
        ('基本信息', {
            'fields': (
                'goal',
                'status',
            )
        }),
        ('调整内容', {
            'fields': (
                'adjustment_reason',
                'adjustment_content',
                'new_target_value',
                'new_end_date',
            )
        }),
        ('审批信息', {
            'fields': (
                'approved_by',
                'approved_time',
                'approval_notes',
            )
        }),
        ('系统信息', {
            'fields': (
                'created_by',
                'created_time',
                'updated_time',
            ),
            'classes': ('collapse',),
        }),
    )
    
    def goal_link(self, obj):
        """目标链接"""
        url = reverse('admin:plan_management_strategicgoal_change', args=[obj.goal.id])
        return format_html('<a href="{}">{}</a>', url, obj.goal.name)
    goal_link.short_description = '目标'
    
    def status_badge(self, obj):
        """状态标签"""
        color_map = {
            'pending': '#ffc107',
            'approved': '#28a745',
            'rejected': '#dc3545',
        }
        return self.format_status_badge(
            obj.status,
            obj.get_status_display(),
            color_map
        )
    status_badge.short_description = '审批状态'


# ==================== 目标对齐度记录（只读）====================

@admin.register(GoalAlignmentRecord)
class GoalAlignmentRecordAdmin(ReadOnlyAdminMixin, BaseModelAdmin):
    """目标对齐度记录管理（只读）"""
    
    list_display = (
        'parent_goal_link',
        'child_goal_link',
        'alignment_score',
        'recorded_time',
    )
    
    list_filter = (
        ('recorded_time', admin.DateFieldListFilter),
    )
    
    search_fields = (
        'parent_goal__goal_number',
        'parent_goal__name',
        'child_goal__goal_number',
        'child_goal__name',
    )
    
    select_related_fields = ['parent_goal', 'child_goal']
    
    readonly_fields = ('parent_goal', 'child_goal', 'alignment_score', 'alignment_analysis', 'suggestions', 'recorded_time')
    
    def parent_goal_link(self, obj):
        """父目标链接"""
        url = reverse('admin:plan_management_strategicgoal_change', args=[obj.parent_goal.id])
        return format_html('<a href="{}">{}</a>', url, obj.parent_goal.name)
    parent_goal_link.short_description = '上级目标'
    
    def child_goal_link(self, obj):
        """子目标链接"""
        url = reverse('admin:plan_management_strategicgoal_change', args=[obj.child_goal.id])
        return format_html('<a href="{}">{}</a>', url, obj.child_goal.name)
    child_goal_link.short_description = '下级目标'


# ==================== 计划管理 ====================

@admin.register(Plan)
class PlanAdmin(StatusBadgeMixin, AuditAdminMixin, BaseModelAdmin):
    """计划管理"""
    
    list_display = (
        'plan_number',
        'name',
        'level_badge',
        'status_badge',
        'owner_link',
        'parent_plan_link',
        'progress_display',
        'start_time',
        'end_time',
        'overdue_indicator',
        'created_time',
    )
    
    list_filter = (
        'level',
        'status',
        'plan_period',
        ('start_time', admin.DateFieldListFilter),
        ('end_time', admin.DateFieldListFilter),
        ('created_time', admin.DateFieldListFilter),
    )
    
    search_fields = (
        'plan_number',
        'name',
        'owner__username',
        'owner__full_name',
        'responsible_person__username',
        'responsible_person__full_name',
    )
    
    select_related_fields = [
        'owner',
        'parent_plan',
        'responsible_person',
        'responsible_department',
        'related_goal',
        'created_by',
    ]
    prefetch_related_fields = ['participants']
    
    readonly_fields = (
        'plan_number',
        'created_time',
        'updated_time',
        'published_at',
        'accepted_at',
        'completed_at',
        'duration_days',
        'progress',
    )
    
    fieldsets = (
        ('基本信息', {
            'fields': (
                'plan_number',
                'name',
                'level',
                'plan_period',
                'status',
            )
        }),
        ('计划内容', {
            'fields': (
                'content',
                'plan_objective',
            )
        }),
        ('责任人信息', {
            'fields': (
                'owner',
                'responsible_person',
                'responsible_department',
                'participants',
                'collaboration_plan',
            )
        }),
        ('时间信息', {
            'fields': (
                'start_time',
                'end_time',
                'duration_days',
            )
        }),
        ('进度信息', {
            'fields': (
                'progress',
            )
        }),
        ('状态时间戳（P2-1）', {
            'fields': (
                'published_at',
                'accepted_at',
                'completed_at',
            ),
            'classes': ('collapse',),
        }),
        ('关联信息', {
            'fields': (
                'parent_plan',
                'related_goal',
                'related_project',
            ),
            'classes': ('collapse',),
        }),
        ('其他信息', {
            'fields': (
                'notes',
            ),
            'classes': ('collapse',),
        }),
        ('系统信息', {
            'fields': (
                'created_by',
                'created_time',
                'updated_time',
            ),
            'classes': ('collapse',),
        }),
    )
    
    actions = ['mark_as_published', 'mark_as_completed', 'mark_as_cancelled']
    
    def level_badge(self, obj):
        """层级标签"""
        colors = {
            'company': '#007bff',
            'personal': '#28a745',
        }
        color = colors.get(obj.level, '#6c757d')
        return format_html(
            '<span style="background-color: {}; color: white; padding: 2px 8px; border-radius: 3px; font-size: 11px;">{}</span>',
            color,
            obj.get_level_display()
        )
    level_badge.short_description = '层级'
    
    def status_badge(self, obj):
        """状态标签"""
        color_map = {
            'draft': '#6c757d',
            'published': '#17a2b8',
            'accepted': '#ffc107',
            'in_progress': '#007bff',
            'completed': '#28a745',
            'cancelled': '#dc3545',
        }
        return self.format_status_badge(
            obj.status,
            obj.get_status_display(),
            color_map
        )
    status_badge.short_description = '状态'
    
    def owner_link(self, obj):
        """所有者链接"""
        if obj.owner:
            url = reverse('admin:system_management_user_change', args=[obj.owner.id])
            return format_html('<a href="{}">{}</a>', url, obj.owner.get_full_name() or obj.owner.username)
        return '-'
    owner_link.short_description = '所有者'
    
    def parent_plan_link(self, obj):
        """父计划链接"""
        if obj.parent_plan:
            url = reverse('admin:plan_management_plan_change', args=[obj.parent_plan.id])
            return format_html('<a href="{}">{}</a>', url, obj.parent_plan.name)
        return '-'
    parent_plan_link.short_description = '父计划'
    
    def progress_display(self, obj):
        """进度显示（带颜色）"""
        try:
            # 确保 progress 是数值类型，不是 SafeString
            if obj.progress is None:
                progress = 0.0
            else:
                # 如果是字符串类型，先尝试转换
                if isinstance(obj.progress, str):
                    progress = float(obj.progress)
                else:
                    progress = float(obj.progress)
        except (ValueError, TypeError):
            progress = 0.0
        
        if progress >= 100:
            color = '#28a745'
        elif progress >= 80:
            color = '#007bff'
        elif progress >= 50:
            color = '#ffc107'
        else:
            color = '#dc3545'
        # 先格式化数值，再传递给 format_html，避免 SafeString 格式化问题
        progress_str = f'{progress:.1f}%'
        return format_html(
            '<span style="color: {}; font-weight: bold;">{}</span>',
            color,
            progress_str
        )
    progress_display.short_description = '进度'
    
    def overdue_indicator(self, obj):
        """逾期指示器"""
        if obj.status in ['draft', 'published', 'accepted', 'in_progress']:
            if obj.end_time and obj.end_time < timezone.now():
                days = (timezone.now().date() - obj.end_time.date()).days
                return format_html(
                    '<span style="color: red; font-weight: bold;">⚠️ 逾期 {} 天</span>',
                    days
                )
        return '-'
    overdue_indicator.short_description = '逾期状态'
    
    def mark_as_published(self, request, queryset):
        """批量发布"""
        count = 0
        for plan in queryset.filter(status='draft'):
            try:
                plan.transition_to('published', user=request.user)
                count += 1
            except ValueError:
                pass
        self.message_user(request, f'成功发布 {count} 个计划', messages.SUCCESS)
    mark_as_published.short_description = '批量发布（draft → published）'
    
    def mark_as_completed(self, request, queryset):
        """批量完成"""
        count = 0
        for plan in queryset.filter(status='in_progress'):
            try:
                plan.transition_to('completed', user=request.user)
                count += 1
            except ValueError:
                pass
        self.message_user(request, f'成功完成 {count} 个计划', messages.SUCCESS)
    mark_as_completed.short_description = '批量完成（in_progress → completed）'
    
    def mark_as_cancelled(self, request, queryset):
        """批量取消"""
        count = 0
        for plan in queryset.filter(status__in=['draft', 'published', 'accepted', 'in_progress']):
            try:
                plan.transition_to('cancelled', user=request.user)
                count += 1
            except ValueError:
                pass
        self.message_user(request, f'成功取消 {count} 个计划', messages.SUCCESS)
    mark_as_cancelled.short_description = '批量取消'
    
    def has_change_permission(self, request, obj=None):
        """控制修改权限"""
        if request.user.is_superuser:
            return True
        
        # 已发布/已接收的计划，不允许在后台直接修改（应通过前端流程）
        if obj and obj.status in ['published', 'accepted', 'in_progress', 'completed']:
            return False
        
        return super().has_change_permission(request, obj)


# ==================== 计划日志（只读）====================

@admin.register(PlanStatusLog)
class PlanStatusLogAdmin(ReadOnlyAdminMixin, BaseModelAdmin):
    """计划状态日志管理（只读）"""
    
    list_display = (
        'plan_link',
        'status_transition',
        'changed_by',
        'changed_time',
        'change_reason',
    )
    
    list_filter = (
        'old_status',
        'new_status',
        ('changed_time', admin.DateFieldListFilter),
    )
    
    search_fields = (
        'plan__plan_number',
        'plan__name',
        'changed_by__username',
        'change_reason',
    )
    
    select_related_fields = ['plan', 'changed_by']
    
    readonly_fields = ('plan', 'old_status', 'new_status', 'changed_by', 'changed_time', 'change_reason', 'notes')
    
    def plan_link(self, obj):
        """计划链接"""
        url = reverse('admin:plan_management_plan_change', args=[obj.plan.id])
        return format_html('<a href="{}">{}</a>', url, obj.plan.name)
    plan_link.short_description = '计划'
    
    def status_transition(self, obj):
        """状态转换显示"""
        return format_html(
            '<span style="color: gray;">{}</span> → <span style="color: green; font-weight: bold;">{}</span>',
            obj.get_old_status_display() if hasattr(obj, 'get_old_status_display') else obj.old_status,
            obj.get_new_status_display() if hasattr(obj, 'get_new_status_display') else obj.new_status
        )
    status_transition.short_description = '状态转换'


@admin.register(PlanProgressRecord)
class PlanProgressRecordAdmin(ReadOnlyAdminMixin, BaseModelAdmin):
    """计划进度记录管理（只读）"""
    
    list_display = (
        'plan_link',
        'progress',
        'recorded_by',
        'recorded_time',
    )
    
    list_filter = (
        ('recorded_time', admin.DateFieldListFilter),
    )
    
    search_fields = (
        'plan__plan_number',
        'plan__name',
        'recorded_by__username',
    )
    
    select_related_fields = ['plan', 'recorded_by']
    
    readonly_fields = ('plan', 'progress', 'progress_description', 'recorded_by', 'recorded_time', 'notes')
    
    def plan_link(self, obj):
        """计划链接"""
        url = reverse('admin:plan_management_plan_change', args=[obj.plan.id])
        return format_html('<a href="{}">{}</a>', url, obj.plan.name)
    plan_link.short_description = '计划'


# ==================== 计划决策（只读）====================

@admin.register(PlanDecision)
class PlanDecisionAdmin(ReadOnlyAdminMixin, BaseModelAdmin):
    """计划决策管理（只读）"""
    
    list_display = (
        'plan_link',
        'request_type',
        'decision_badge',
        'requested_by',
        'requested_at',
        'decided_by',
        'decided_at',
    )
    
    list_filter = (
        'request_type',
        'decision',
        ('requested_at', admin.DateFieldListFilter),
        ('decided_at', admin.DateFieldListFilter),
    )
    
    search_fields = (
        'plan__plan_number',
        'plan__name',
        'requested_by__username',
        'decided_by__username',
        'reason',
    )
    
    select_related_fields = ['plan', 'requested_by', 'decided_by']
    
    readonly_fields = (
        'plan',
        'request_type',
        'decision',
        'requested_by',
        'requested_at',
        'decided_by',
        'decided_at',
        'reason',
    )
    
    def plan_link(self, obj):
        """计划链接"""
        url = reverse('admin:plan_management_plan_change', args=[obj.plan.id])
        return format_html('<a href="{}">{}</a>', url, obj.plan.name)
    plan_link.short_description = '计划'
    
    def decision_badge(self, obj):
        """决策标签"""
        if obj.decision == 'approve':
            return format_html('<span style="background-color: #28a745; color: white; padding: 2px 8px; border-radius: 3px; font-size: 11px;">✓ 通过</span>')
        elif obj.decision == 'reject':
            return format_html('<span style="background-color: #dc3545; color: white; padding: 2px 8px; border-radius: 3px; font-size: 11px;">✗ 驳回</span>')
        else:
            return format_html('<span style="background-color: #ffc107; color: white; padding: 2px 8px; border-radius: 3px; font-size: 11px;">⏳ 待处理</span>')
    decision_badge.short_description = '决策结果'


# ==================== 计划问题 ====================

@admin.register(PlanIssue)
class PlanIssueAdmin(StatusBadgeMixin, AuditAdminMixin, BaseModelAdmin):
    """计划问题管理"""
    
    list_display = (
        'plan_link',
        'title',
        'status_badge',
        'severity_badge',
        'assigned_to',
        'created_by',
        'created_time',
    )
    
    list_filter = (
        'status',
        'severity',
        ('created_time', admin.DateFieldListFilter),
    )
    
    search_fields = (
        'plan__plan_number',
        'plan__name',
        'title',
        'description',
    )
    
    select_related_fields = ['plan', 'assigned_to', 'created_by']
    
    readonly_fields = (
        'created_time',
        'updated_time',
        'discovered_time',
        'resolved_time',
    )
    
    fieldsets = (
        ('基本信息', {
            'fields': (
                'plan',
                'title',
                'description',
            )
        }),
        ('问题状态', {
            'fields': (
                'status',
                'severity',
                'assigned_to',
            )
        }),
        ('解决方案', {
            'fields': (
                'solution',
            )
        }),
        ('时间信息', {
            'fields': (
                'discovered_time',
                'resolved_time',
            ),
            'classes': ('collapse',),
        }),
        ('系统信息', {
            'fields': (
                'created_by',
                'created_time',
                'updated_time',
            ),
            'classes': ('collapse',),
        }),
    )
    
    def plan_link(self, obj):
        """计划链接"""
        url = reverse('admin:plan_management_plan_change', args=[obj.plan.id])
        return format_html('<a href="{}">{}</a>', url, obj.plan.name)
    plan_link.short_description = '计划'
    
    def status_badge(self, obj):
        """状态标签"""
        color_map = {
            'open': '#ffc107',
            'in_progress': '#007bff',
            'resolved': '#28a745',
            'closed': '#6c757d',
        }
        return self.format_status_badge(
            obj.status,
            obj.get_status_display(),
            color_map
        )
    status_badge.short_description = '问题状态'
    
    def severity_badge(self, obj):
        """严重程度标签"""
        color_map = {
            'critical': '#dc3545',
            'high': '#fd7e14',
            'medium': '#ffc107',
            'low': '#28a745',
        }
        return self.format_status_badge(
            obj.severity,
            obj.get_severity_display(),
            color_map
        )
    severity_badge.short_description = '严重程度'


# ==================== 计划调整申请 ====================

@admin.register(PlanAdjustment)
class PlanAdjustmentAdmin(StatusBadgeMixin, AuditAdminMixin, BaseModelAdmin):
    """计划调整申请管理"""
    
    list_display = (
        'plan_link',
        'status_badge',
        'created_by',
        'created_time',
        'approved_by',
        'approved_time',
    )
    
    list_filter = (
        'status',
        ('created_time', admin.DateFieldListFilter),
        ('approved_time', admin.DateFieldListFilter),
    )
    
    search_fields = (
        'plan__plan_number',
        'plan__name',
        'adjustment_reason',
        'created_by__username',
    )
    
    select_related_fields = ['plan', 'created_by', 'approved_by']
    
    readonly_fields = (
        'plan',
        'created_time',
        'updated_time',
        'approved_time',
    )
    
    fieldsets = (
        ('基本信息', {
            'fields': (
                'plan',
                'status',
            )
        }),
        ('调整内容', {
            'fields': (
                'adjustment_reason',
                'adjustment_content',
                'original_end_time',
                'new_end_time',
            )
        }),
        ('审批信息', {
            'fields': (
                'approved_by',
                'approved_time',
                'approval_notes',
            )
        }),
        ('系统信息', {
            'fields': (
                'created_by',
                'created_time',
                'updated_time',
            ),
            'classes': ('collapse',),
        }),
    )
    
    def plan_link(self, obj):
        """计划链接"""
        url = reverse('admin:plan_management_plan_change', args=[obj.plan.id])
        return format_html('<a href="{}">{}</a>', url, obj.plan.name)
    plan_link.short_description = '计划'
    
    def status_badge(self, obj):
        """状态标签"""
        color_map = {
            'pending': '#ffc107',
            'approved': '#28a745',
            'rejected': '#dc3545',
        }
        return self.format_status_badge(
            obj.status,
            obj.get_status_display(),
            color_map
        )
    status_badge.short_description = '审批状态'


# ==================== 计划不作为记录（只读）====================

@admin.register(PlanInactivityLog)
class PlanInactivityLogAdmin(ReadOnlyAdminMixin, BaseModelAdmin):
    """计划不作为记录管理（只读，系统自动生成）"""
    
    list_display = (
        'plan_link',
        'reason_badge',
        'detected_at',
        'period_start',
        'period_end',
    )
    
    list_filter = (
        'reason',
        ('detected_at', admin.DateFieldListFilter),
    )
    
    search_fields = (
        'plan__plan_number',
        'plan__name',
        'reason_detail',
    )
    
    select_related_fields = ['plan']
    
    readonly_fields = ('plan', 'reason', 'detected_at', 'period_start', 'period_end', 'reason_detail', 'snapshot', 'is_confirmed')
    
    fieldsets = (
        ('基本信息', {
            'fields': (
                'plan',
                'reason',
                'is_confirmed',
            )
        }),
        ('检测信息', {
            'fields': (
                'detected_at',
                'period_start',
                'period_end',
            )
        }),
        ('详情', {
            'fields': (
                'reason_detail',
                'snapshot',
            ),
            'classes': ('collapse',),
        }),
    )
    
    def plan_link(self, obj):
        """计划链接"""
        url = reverse('admin:plan_management_plan_change', args=[obj.plan.id])
        return format_html('<a href="{}">{}</a>', url, obj.plan.name)
    plan_link.short_description = '计划'
    
    def reason_badge(self, obj):
        """原因标签"""
        color_map = {
            'overdue_and_silent': '#dc3545',
            'overdue_no_progress': '#fd7e14',
            'overdue_no_feedback': '#ffc107',
        }
        return self.format_status_badge(
            obj.reason,
            obj.get_reason_display() if hasattr(obj, 'get_reason_display') else obj.reason,
            color_map
        )
    reason_badge.short_description = '不作为原因'


# ==================== 待办事项管理 ====================

@admin.register(TodoTask)
class TodoTaskAdmin(BaseModelAdmin):
    """待办事项管理"""
    
    list_display = (
        'title',
        'user_link',
        'task_type_display',
        'status_display',
        'deadline',
        'is_overdue_badge',
        'auto_generated_badge',
        'created_at',
    )
    
    list_filter = (
        'task_type',
        'status',
        'is_overdue',
        'auto_generated',
        'created_at',
    )
    
    search_fields = (
        'title',
        'description',
        'user__username',
        'user__first_name',
        'user__last_name',
    )
    
    readonly_fields = (
        'created_at',
        'updated_at',
    )
    
    fieldsets = (
        ('基本信息', {
            'fields': ('task_type', 'user', 'title', 'description')
        }),
        ('关联信息', {
            'fields': ('related_object_type', 'related_object_id')
        }),
        ('时间信息', {
            'fields': ('deadline', 'completed_at', 'created_at', 'updated_at')
        }),
        ('状态信息', {
            'fields': ('status', 'is_overdue', 'overdue_days', 'auto_generated')
        }),
    )
    
    def user_link(self, obj):
        """用户链接"""
        if obj.user:
            url = reverse('admin:system_management_user_change', args=[obj.user.id])
            return format_html('<a href="{}">{}</a>', url, obj.user.get_full_name() or obj.user.username)
        return '-'
    user_link.short_description = '负责人'
    
    def task_type_display(self, obj):
        """待办类型显示"""
        return obj.get_task_type_display()
    task_type_display.short_description = '待办类型'
    
    def status_display(self, obj):
        """状态显示"""
        color_map = {
            'pending': '#007bff',
            'completed': '#28a745',
            'overdue': '#dc3545',
            'cancelled': '#6c757d',
        }
        color = color_map.get(obj.status, '#6c757d')
        return format_html(
            '<span style="color: {}; font-weight: bold;">{}</span>',
            color,
            obj.get_status_display()
        )
    status_display.short_description = '状态'
    
    def is_overdue_badge(self, obj):
        """逾期标记"""
        if obj.is_overdue:
            return format_html(
                '<span style="color: #dc3545; font-weight: bold;">逾期 {} 天</span>',
                obj.overdue_days
            )
        return format_html('<span style="color: #28a745;">正常</span>')
    is_overdue_badge.short_description = '逾期状态'
    
    def auto_generated_badge(self, obj):
        """自动生成标记"""
        if obj.auto_generated:
            return format_html('<span style="color: #17a2b8;">系统生成</span>')
        return format_html('<span style="color: #6c757d;">手动创建</span>')
    auto_generated_badge.short_description = '生成方式'
    
    actions = ['mark_as_completed', 'mark_as_cancelled']
    
    def mark_as_completed(self, request, queryset):
        """批量标记为已完成"""
        from .services.todo_service import mark_todo_completed
        count = 0
        for todo in queryset:
            if mark_todo_completed(todo, request.user):
                count += 1
        messages.success(request, f'成功标记 {count} 个待办为已完成')
    mark_as_completed.short_description = '标记为已完成'
    
    def mark_as_cancelled(self, request, queryset):
        """批量标记为已取消"""
        updated = queryset.filter(status__in=['pending', 'overdue']).update(
            status='cancelled',
            updated_at=timezone.now()
        )
        messages.success(request, f'成功取消 {updated} 个待办')
    mark_as_cancelled.short_description = '标记为已取消'


# ==================== 工作总结管理 ====================

@admin.register(WorkSummary)
class WorkSummaryAdmin(ReadOnlyAdminMixin, BaseModelAdmin):
    """工作总结管理（只读）"""
    
    list_display = (
        'summary_type_display',
        'user_link',
        'period_display',
        'sent_to_supervisor_badge',
        'created_at',
    )
    
    list_filter = (
        'summary_type',
        'sent_to_supervisor',
        'created_at',
    )
    
    search_fields = (
        'user__username',
        'user__first_name',
        'user__last_name',
    )
    
    readonly_fields = (
        'summary_type',
        'user',
        'period_start',
        'period_end',
        'goal_progress_summary',
        'plan_completion_summary',
        'achievements',
        'risk_items',
        'sent_to_supervisor',
        'created_at',
    )
    
    fieldsets = (
        ('基本信息', {
            'fields': ('summary_type', 'user', 'period_start', 'period_end', 'created_at')
        }),
        ('汇总内容', {
            'fields': ('goal_progress_summary', 'plan_completion_summary', 'achievements', 'risk_items')
        }),
        ('发送状态', {
            'fields': ('sent_to_supervisor',)
        }),
    )
    
    def summary_type_display(self, obj):
        """总结类型显示"""
        return obj.get_summary_type_display()
    summary_type_display.short_description = '总结类型'
    
    def user_link(self, obj):
        """用户链接"""
        if obj.user:
            url = reverse('admin:system_management_user_change', args=[obj.user.id])
            return format_html('<a href="{}">{}</a>', url, obj.user.get_full_name() or obj.user.username)
        return '-'
    user_link.short_description = '员工'
    
    def period_display(self, obj):
        """周期显示"""
        return f"{obj.period_start.strftime('%Y-%m-%d')} ~ {obj.period_end.strftime('%Y-%m-%d')}"
    period_display.short_description = '周期'
    
    def sent_to_supervisor_badge(self, obj):
        """发送状态标记"""
        if obj.sent_to_supervisor:
            return format_html('<span style="color: #28a745;">已发送</span>')
        return format_html('<span style="color: #ffc107;">未发送</span>')
    sent_to_supervisor_badge.short_description = '发送状态'


# ==================== 审批通知管理 ====================

@admin.register(ApprovalNotification)
class ApprovalNotificationAdmin(BaseModelAdmin):
    """审批通知管理"""
    
    list_display = (
        'title',
        'user_link',
        'event_display',
        'object_type_display',
        'is_read_badge',
        'created_at',
    )
    
    list_filter = (
        'event',
        'object_type',
        'is_read',
        'created_at',
    )
    
    search_fields = (
        'title',
        'content',
        'user__username',
        'user__first_name',
        'user__last_name',
    )
    
    readonly_fields = (
        'created_at',
    )
    
    fieldsets = (
        ('基本信息', {
            'fields': ('user', 'title', 'content')
        }),
        ('关联信息', {
            'fields': ('object_type', 'object_id', 'event')
        }),
        ('状态信息', {
            'fields': ('is_read', 'created_at')
        }),
    )
    
    def user_link(self, obj):
        """用户链接"""
        if obj.user:
            url = reverse('admin:system_management_user_change', args=[obj.user.id])
            return format_html('<a href="{}">{}</a>', url, obj.user.get_full_name() or obj.user.username)
        return '-'
    user_link.short_description = '接收人'
    
    def event_display(self, obj):
        """事件类型显示"""
        return obj.get_event_display()
    event_display.short_description = '事件类型'
    
    def object_type_display(self, obj):
        """对象类型显示"""
        return obj.get_object_type_display()
    object_type_display.short_description = '对象类型'
    
    def is_read_badge(self, obj):
        """已读状态标记"""
        if obj.is_read:
            return format_html('<span style="color: #6c757d;">已读</span>')
        return format_html('<span style="color: #007bff; font-weight: bold;">未读</span>')
    is_read_badge.short_description = '已读状态'
    
    actions = ['mark_as_read', 'mark_as_unread']
    
    def mark_as_read(self, request, queryset):
        """批量标记为已读"""
        updated = queryset.update(is_read=True)
        messages.success(request, f'成功标记 {updated} 条通知为已读')
    mark_as_read.short_description = '标记为已读'
    
    def mark_as_unread(self, request, queryset):
        """批量标记为未读"""
        updated = queryset.update(is_read=False)
        messages.success(request, f'成功标记 {updated} 条通知为未读')
    mark_as_unread.short_description = '标记为未读'
