"""
档案管理模块管理后台配置
"""
from django.contrib import admin
from django.utils.html import format_html
from backend.apps.archive_management.models import (
    ArchiveCategory,
    ArchiveProjectArchive,
    ProjectArchiveDocument,
    ArchivePushRecord,
    AdministrativeArchive,
    ArchiveBorrow,
    ArchiveDestroy,
    ArchiveStorageRoom,
    ArchiveLocation,
    ArchiveShelf,
    ArchiveInventory,
)
from backend.core.admin_base import BaseModelAdmin, AuditAdminMixin, ReadOnlyAdminMixin


@admin.register(ArchiveCategory)
class ArchiveCategoryAdmin(BaseModelAdmin):
    """档案分类管理"""
    list_display = ('name', 'code', 'category_type', 'parent', 'order', 'is_active', 'created_time')
    list_filter = ('category_type', 'is_active', 'created_time')
    search_fields = ('name', 'code')
    ordering = ('category_type', 'order', 'id')
    list_editable = ['order', 'is_active']


@admin.register(ArchiveProjectArchive)
class ArchiveProjectArchiveAdmin(AuditAdminMixin, BaseModelAdmin):
    """项目档案管理"""
    list_display = ('archive_number', 'project', 'status', 'applicant', 'applied_time', 'confirmed_time')
    list_filter = ('status', 'applied_time')
    search_fields = ('archive_number', 'project__project_name', 'project__project_number')
    readonly_fields = ('archive_number', 'created_time', 'updated_time')
    date_hierarchy = 'applied_time'


@admin.register(ProjectArchiveDocument)
class ProjectArchiveDocumentAdmin(AuditAdminMixin, BaseModelAdmin):
    """项目档案文档管理"""
    list_display = ('document_number', 'document_name', 'document_type', 'project', 'category', 'status', 'uploaded_by', 'uploaded_time')
    list_filter = ('document_type', 'status', 'category', 'uploaded_time')
    search_fields = ('document_number', 'document_name', 'project__project_name')
    readonly_fields = ('document_number', 'uploaded_time', 'updated_time')
    date_hierarchy = 'uploaded_time'


@admin.register(ArchivePushRecord)
class ArchivePushRecordAdmin(BaseModelAdmin):
    """档案推送记录管理"""
    list_display = ('delivery_record', 'project', 'push_status', 'push_time', 'receive_time', 'retry_count')
    list_filter = ('push_status', 'push_time')
    search_fields = ('delivery_record__delivery_number', 'project__project_name')
    readonly_fields = ('created_time', 'updated_time')


@admin.register(AdministrativeArchive)
class AdministrativeArchiveAdmin(AuditAdminMixin, BaseModelAdmin):
    """行政档案管理"""
    list_display = ('archive_number', 'archive_name', 'category', 'archive_date', 'archivist', 'status', 'storage_room')
    list_filter = ('status', 'category', 'archive_date', 'storage_room')
    search_fields = ('archive_number', 'archive_name')
    readonly_fields = ('archive_number', 'created_time', 'updated_time')
    date_hierarchy = 'archive_date'


@admin.register(ArchiveBorrow)
class ArchiveBorrowAdmin(AuditAdminMixin, BaseModelAdmin):
    """档案借阅管理"""
    list_display = ('borrow_number', 'get_archive_name', 'borrower', 'borrow_date', 'return_date', 'status', 'is_overdue')
    list_filter = ('status', 'borrow_method', 'borrow_date')
    search_fields = ('borrow_number', 'borrower__username')
    readonly_fields = ('borrow_number', 'created_time', 'updated_time')
    date_hierarchy = 'borrow_date'
    
    def get_archive_name(self, obj):
        if obj.project_document:
            return obj.project_document.document_name
        elif obj.administrative_archive:
            return obj.administrative_archive.archive_name
        return '-'
    get_archive_name.short_description = '档案名称'


@admin.register(ArchiveDestroy)
class ArchiveDestroyAdmin(AuditAdminMixin, BaseModelAdmin):
    """档案销毁管理"""
    list_display = ('destroy_number', 'get_archive_name', 'destroyer', 'destroy_date', 'destroy_method', 'status')
    list_filter = ('status', 'destroy_method', 'destroy_date')
    search_fields = ('destroy_number', 'destroyer__username')
    readonly_fields = ('destroy_number', 'created_time', 'updated_time')
    date_hierarchy = 'destroy_date'
    
    def get_archive_name(self, obj):
        if obj.project_document:
            return obj.project_document.document_name
        elif obj.administrative_archive:
            return obj.administrative_archive.archive_name
        return '-'
    get_archive_name.short_description = '档案名称'


@admin.register(ArchiveStorageRoom)
class ArchiveStorageRoomAdmin(BaseModelAdmin):
    """档案库房管理"""
    list_display = ('room_number', 'room_name', 'location', 'manager', 'status', 'archive_count', 'usage_rate')
    list_filter = ('status',)
    search_fields = ('room_number', 'room_name')
    readonly_fields = ('created_time', 'updated_time')


@admin.register(ArchiveLocation)
class ArchiveLocationAdmin(BaseModelAdmin):
    """档案位置管理"""
    list_display = ('location_number', 'location_name', 'storage_room', 'location_type', 'archive_count', 'usage_rate')
    list_filter = ('location_type', 'storage_room')
    search_fields = ('location_number', 'location_name')
    readonly_fields = ('created_time', 'updated_time')


@admin.register(ArchiveShelf)
class ArchiveShelfAdmin(AuditAdminMixin, BaseModelAdmin):
    """档案上架管理"""
    list_display = ('archive', 'location', 'shelf_time', 'shelf_by')
    list_filter = ('shelf_time', 'location__storage_room')
    search_fields = ('archive__archive_number', 'location__location_number')
    readonly_fields = ('shelf_time',)


@admin.register(ArchiveInventory)
class ArchiveInventoryAdmin(AuditAdminMixin, BaseModelAdmin):
    """档案盘点管理"""
    list_display = ('inventory_number', 'inventory_name', 'inventory_type', 'inventory_date', 'inventory_by', 'total_count', 'actual_count', 'difference_count')
    list_filter = ('inventory_type', 'inventory_date')
    search_fields = ('inventory_number', 'inventory_name')
    readonly_fields = ('inventory_number', 'created_time', 'updated_time')
    date_hierarchy = 'inventory_date'


# ProjectDrawingArchive model not yet implemented
# @admin.register(ProjectDrawingArchive)
# class ProjectDrawingArchiveAdmin(admin.ModelAdmin):
#     list_display = ['archive_number', 'project', 'archive_type', 'status', 'applicant', 'applied_time', 'drawing_count']
#     list_filter = ['status', 'archive_type', 'applied_time']
#     search_fields = ['archive_number', 'project__name', 'project__project_number']
#     readonly_fields = ['archive_number', 'drawing_file_ids', 'drawing_submission_ids', 'created_time', 'updated_time']
#     date_hierarchy = 'applied_time'
#     
#     def drawing_count(self, obj):
#         return obj.drawing_count
#     drawing_count.short_description = '图纸数量'


try:
    from backend.apps.archive_management.models import ProjectDeliveryArchive
    
    @admin.register(ProjectDeliveryArchive)
    class ProjectDeliveryArchiveAdmin(AuditAdminMixin, BaseModelAdmin):
        """项目交付档案管理"""
        list_display = ('archive_number', 'delivery_record', 'project', 'status', 'applicant', 'applied_time')
        list_filter = ('status', 'applied_time')
        search_fields = ('archive_number', 'delivery_record__delivery_number', 'delivery_record__title', 'project__name')
        readonly_fields = ('archive_number', 'created_time', 'updated_time')
        date_hierarchy = 'applied_time'
except ImportError:
    pass

try:
    from backend.apps.archive_management.models import ArchiveCategoryRule
    
    @admin.register(ArchiveCategoryRule)
    class ArchiveCategoryRuleAdmin(AuditAdminMixin, BaseModelAdmin):
        """档案分类规则管理"""
        list_display = ('name', 'rule_type', 'category', 'priority', 'status', 'is_active', 'created_by', 'created_time')
        list_filter = ('rule_type', 'status', 'is_active', 'created_time')
        search_fields = ('name', 'description', 'category__name')
        readonly_fields = ('created_time', 'updated_time')
        date_hierarchy = 'created_time'
except ImportError:
    pass

try:
    from backend.apps.archive_management.models import ArchiveOperationLog
    
    @admin.register(ArchiveOperationLog)
    class ArchiveOperationLogAdmin(ReadOnlyAdminMixin, BaseModelAdmin):
        """档案操作日志管理（只读）"""
        list_display = ('operation_time', 'operation_type', 'operator', 'operation_result', 'project_document', 'administrative_archive')
        list_filter = ('operation_type', 'operation_result', 'operation_time')
        search_fields = ('operation_content', 'operator__username', 'project_document__document_name', 'administrative_archive__archive_name')
        readonly_fields = ('created_time',)
        date_hierarchy = 'operation_time'
        ordering = ('-operation_time',)
except ImportError:
    pass

try:
    from backend.apps.archive_management.models import ArchiveSearchHistory
    
    @admin.register(ArchiveSearchHistory)
    class ArchiveSearchHistoryAdmin(ReadOnlyAdminMixin, BaseModelAdmin):
        """档案搜索历史管理（只读）"""
        list_display = ('search_time', 'searcher', 'search_type', 'search_keyword', 'result_count', 'search_duration')
        list_filter = ('search_type', 'search_time')
        search_fields = ('search_keyword', 'searcher__username')
        readonly_fields = ('created_time',)
        date_hierarchy = 'search_time'
        ordering = ('-search_time',)
except ImportError:
    pass

# ==================== 文件分类管理 ====================
# 使用 proxy model 在档案管理中显示文件分类
# 注意：FileCategory 是在 models.py 中定义的 proxy model
try:
    # 先确保 delivery_customer 的 FileCategory 已导入
    from backend.apps.delivery_customer.models import FileCategory as DeliveryFileCategory
    
    # 然后导入 archive_management 中的 proxy model
    from backend.apps.archive_management.models import FileCategory
    
    # 确保 FileCategory 存在且是 proxy model
    if FileCategory is not None and hasattr(FileCategory._meta, 'proxy') and FileCategory._meta.proxy:
        @admin.register(FileCategory)
        class FileCategoryAdmin(AuditAdminMixin, BaseModelAdmin):
            """文件分类管理（档案管理--档案分类）"""
            list_display = ('name', 'code', 'stage_display', 'sort_order', 'is_active', 'created_by', 'created_at')
            list_filter = ('stage', 'is_active', 'created_at')
            search_fields = ('name', 'code', 'description')
            ordering = ('stage', 'sort_order', 'name')
            list_editable = ['sort_order', 'is_active']
            readonly_fields = ('created_at', 'updated_at')
            raw_id_fields = ('created_by',)
            
            fieldsets = (
                ('基本信息', {
                    'fields': ('name', 'code', 'stage', 'description')
                }),
                ('排序和状态', {
                    'fields': ('sort_order', 'is_active')
                }),
                ('创建信息', {
                    'fields': ('created_by',)
                }),
                ('时间信息', {
                    'fields': ('created_at', 'updated_at'),
                    'classes': ('collapse',)
                }),
            )
            
            def stage_display(self, obj):
                """显示阶段名称"""
                return obj.get_stage_display()
            stage_display.short_description = '所属阶段'
            stage_display.admin_order_field = 'stage'
            
            def save_model(self, request, obj, form, change):
                """保存时自动设置创建人"""
                if not change and not obj.created_by:
                    obj.created_by = request.user
                super().save_model(request, obj, form, change)
    else:
        # 如果 proxy model 不存在，直接使用原始模型注册
        # 但需要先取消 delivery_customer 中的注册（如果存在）
        try:
            admin.site.unregister(DeliveryFileCategory)
        except admin.sites.NotRegistered:
            pass
        
        @admin.register(DeliveryFileCategory)
        class FileCategoryAdmin(AuditAdminMixin, BaseModelAdmin):
            """文件分类管理（档案管理--档案分类）"""
            list_display = ('name', 'code', 'stage_display', 'sort_order', 'is_active', 'created_by', 'created_at')
            list_filter = ('stage', 'is_active', 'created_at')
            search_fields = ('name', 'code', 'description')
            ordering = ('stage', 'sort_order', 'name')
            list_editable = ['sort_order', 'is_active']
            readonly_fields = ('created_at', 'updated_at')
            raw_id_fields = ('created_by',)
            
            fieldsets = (
                ('基本信息', {
                    'fields': ('name', 'code', 'stage', 'description')
                }),
                ('排序和状态', {
                    'fields': ('sort_order', 'is_active')
                }),
                ('创建信息', {
                    'fields': ('created_by',)
                }),
                ('时间信息', {
                    'fields': ('created_at', 'updated_at'),
                    'classes': ('collapse',)
                }),
            )
            
            def stage_display(self, obj):
                """显示阶段名称"""
                return obj.get_stage_display()
            stage_display.short_description = '所属阶段'
            stage_display.admin_order_field = 'stage'
            
            def save_model(self, request, obj, form, change):
                """保存时自动设置创建人"""
                if not change and not obj.created_by:
                    obj.created_by = request.user
                super().save_model(request, obj, form, change)
except (ImportError, AttributeError) as e:
    import logging
    logger = logging.getLogger(__name__)
    logger.warning(f"无法注册 FileCategory admin: {e}")
    pass

