"""
Django Admin 优化功能使用示例

本文件展示了如何使用新增的优化功能来提升后台管理的性能和用户体验。
"""

from django.contrib import admin
from backend.core.admin_base import (
    BaseModelAdmin,
    AuditAdminMixin,
    ExportMixin,
    StatusBadgeMixin,
    QueryOptimizationMixin,
    LinkAdminMixin,
)


# ==================== 示例1: 基础优化 ====================

@admin.register(ExampleModel1)
class ExampleModel1Admin(QueryOptimizationMixin, BaseModelAdmin):
    """
    示例1: 使用查询优化
    
    特性：
    - 自动优化关联查询，减少数据库查询次数
    - 提升列表页面加载速度
    """
    # 指定需要优化的ForeignKey和OneToOneField关联
    select_related_fields = ['department', 'created_by', 'updated_by']
    
    # 指定需要优化的ManyToManyField和反向ForeignKey关联
    prefetch_related_fields = ['roles', 'permissions']
    
    list_display = ['name', 'department', 'created_by', 'created_time']
    list_filter = ['department', 'created_time']
    search_fields = ['name', 'code']


# ==================== 示例2: 导出功能 ====================

@admin.register(ExampleModel2)
class ExampleModel2Admin(ExportMixin, BaseModelAdmin):
    """
    示例2: 使用数据导出功能
    
    特性：
    - 批量操作中自动添加"导出选中项为CSV"选项
    - 支持中文文件名
    - 自动处理HTML内容
    """
    list_display = ['name', 'code', 'status', 'created_time']
    
    # 可选：指定导出字段（默认使用list_display）
    export_fields = ['name', 'code', 'status', 'created_time']
    
    # 可选：指定导出文件名前缀（默认使用模型verbose_name）
    export_filename_prefix = '示例模型'


# ==================== 示例3: 状态标签 ====================

@admin.register(ExampleModel3)
class ExampleModel3Admin(StatusBadgeMixin, BaseModelAdmin):
    """
    示例3: 使用状态标签格式化
    
    特性：
    - 统一的状态显示格式
    - 带颜色的标签，提升视觉效果
    """
    list_display = ['name', 'status_badge', 'is_active_badge', 'created_time']
    
    def status_badge(self, obj):
        """状态标签"""
        return self.format_status_badge(
            obj.status,
            obj.get_status_display(),
            color_map={
                'active': '#28a745',
                'inactive': '#dc3545',
                'pending': '#ffc107',
            }
        )
    status_badge.short_description = '状态'
    status_badge.admin_order_field = 'status'
    
    def is_active_badge(self, obj):
        """激活状态标签"""
        return self.format_boolean_badge(obj.is_active, '启用', '禁用')
    is_active_badge.short_description = '状态'
    is_active_badge.admin_order_field = 'is_active'


# ==================== 示例4: 组合使用 ====================

@admin.register(ExampleModel4)
class ExampleModel4Admin(
    QueryOptimizationMixin,
    ExportMixin,
    StatusBadgeMixin,
    AuditAdminMixin,
    LinkAdminMixin,
    BaseModelAdmin
):
    """
    示例4: 组合使用多个优化功能
    
    特性：
    - 查询优化：减少数据库查询次数
    - 数据导出：支持CSV导出
    - 状态标签：统一的状态显示
    - 审计记录：自动记录操作人
    - 链接生成：便捷的关联对象链接
    """
    # 查询优化配置
    select_related_fields = ['client', 'department', 'created_by', 'updated_by']
    prefetch_related_fields = ['team_members', 'documents', 'tags']
    
    # 导出配置
    export_fields = ['name', 'code', 'client', 'status', 'created_time']
    export_filename_prefix = '项目列表'
    
    list_display = [
        'name', 
        'code', 
        'client_link', 
        'status_badge', 
        'is_active_badge',
        'created_by',
        'created_time'
    ]
    list_filter = ['status', 'is_active', 'created_time']
    search_fields = ['name', 'code', 'client__name']
    
    def client_link(self, obj):
        """客户端链接"""
        if obj.client:
            return self._link_to_related_object(obj, 'client', display_field='name')
        return '-'
    client_link.short_description = '客户'
    
    def status_badge(self, obj):
        """状态标签"""
        return self.format_status_badge(
            obj.status,
            obj.get_status_display()
        )
    status_badge.short_description = '状态'
    status_badge.admin_order_field = 'status'
    
    def is_active_badge(self, obj):
        """激活状态标签"""
        return self.format_boolean_badge(obj.is_active)
    is_active_badge.short_description = '状态'
    is_active_badge.admin_order_field = 'is_active'


# ==================== 示例5: 实际应用场景 ====================

# 场景：项目管理Admin，需要优化查询、导出数据、显示状态

@admin.register(Project)
class ProjectAdmin(
    QueryOptimizationMixin,
    ExportMixin,
    StatusBadgeMixin,
    AuditAdminMixin,
    BaseModelAdmin
):
    """项目管理 - 完整优化示例"""
    
    # 1. 查询优化：优化关联查询
    select_related_fields = [
        'client',           # 客户信息
        'department',       # 部门信息
        'created_by',       # 创建人
        'updated_by',       # 更新人
        'responsible_person',  # 负责人
    ]
    prefetch_related_fields = [
        'team_members',     # 团队成员（ManyToMany）
        'documents',        # 项目文档（反向ForeignKey）
        'tasks',            # 项目任务（反向ForeignKey）
    ]
    
    # 2. 导出配置
    export_fields = [
        'name',
        'code',
        'client__name',     # 关联字段
        'status',
        'created_time',
        'created_by__username',
    ]
    export_filename_prefix = '项目列表'
    
    # 3. 列表显示配置
    list_display = [
        'name',
        'code',
        'client',
        'status_badge',
        'progress_badge',
        'responsible_person',
        'created_time',
    ]
    list_filter = ['status', 'department', 'created_time']
    search_fields = ['name', 'code', 'client__name']
    date_hierarchy = 'created_time'
    
    # 4. 自定义显示方法
    def status_badge(self, obj):
        """状态标签"""
        color_map = {
            'planning': '#17a2b8',      # 计划中 - 蓝色
            'in_progress': '#007bff',   # 进行中 - 深蓝色
            'completed': '#28a745',      # 已完成 - 绿色
            'cancelled': '#dc3545',     # 已取消 - 红色
            'on_hold': '#ffc107',       # 暂停 - 黄色
        }
        return self.format_status_badge(
            obj.status,
            obj.get_status_display(),
            color_map=color_map
        )
    status_badge.short_description = '状态'
    status_badge.admin_order_field = 'status'
    
    def progress_badge(self, obj):
        """进度标签（百分比显示）"""
        progress = getattr(obj, 'progress', 0) or 0
        if progress >= 100:
            color = '#28a745'  # 绿色
        elif progress >= 50:
            color = '#007bff'  # 蓝色
        else:
            color = '#ffc107'  # 黄色
        
        return format_html(
            '<span style="background: {}; color: white; padding: 3px 8px; '
            'border-radius: 3px; font-size: 11px;">{}%</span>',
            color,
            progress
        )
    progress_badge.short_description = '进度'
    progress_badge.admin_order_field = 'progress'


# ==================== 使用建议 ====================

"""
1. 查询优化（QueryOptimizationMixin）
   - 对于ForeignKey字段，添加到select_related_fields
   - 对于ManyToManyField字段，添加到prefetch_related_fields
   - 使用Django Debug Toolbar检查查询次数，确保优化有效

2. 数据导出（ExportMixin）
   - 导出大量数据时，考虑添加分页或限制
   - 导出字段不要包含大量文本内容
   - 对于敏感数据，考虑添加权限检查

3. 状态标签（StatusBadgeMixin）
   - 统一使用format_status_badge确保样式一致
   - 自定义颜色映射以符合业务需求
   - 布尔值使用format_boolean_badge

4. 组合使用
   - 混入类的顺序：功能混入类在前，BaseModelAdmin在后
   - 所有混入类都兼容，可以自由组合
   - 注意方法名冲突，避免覆盖重要方法
"""

