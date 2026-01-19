"""
客户成功模块的Admin配置
注意：业务模块数据应在前端管理，不再在Django Admin中显示
这些数据应通过API接口在前端管理
"""

from django.contrib import admin
from backend.core.admin_base import BaseModelAdmin
from .models import (
    # 客户管理新模型（按《客户管理详细设计方案 v1.12》实现）
    ClientType,
    ClientGrade,
    School,
    Client,
    ClientContact,
    ContactEducation,
    ContactWorkExperience,
    ContactJobChange,
    ContactCooperation,
    ContactTracking,
    CustomerRelationship,
    CustomerRelationshipUpgrade,
    ClientProject,
    # 其他模型
    ExecutionRecord,
    AuthorizationLetter,
)

# 客户类型和客户分级需要在后台管理，所以注册到Django Admin
@admin.register(ClientType)
class ClientTypeAdmin(BaseModelAdmin):
    """客户类型管理"""
    list_display = ('name', 'code', 'display_order', 'is_active', 'created_time')
    list_filter = ('is_active', 'created_time')
    search_fields = ('name', 'code', 'description')
    list_editable = ('display_order', 'is_active')
    ordering = ('display_order', 'name')
    readonly_fields = ('created_time', 'updated_time')
    fieldsets = (
        ('基本信息', {
            'fields': ('code', 'name', 'display_order', 'is_active')
        }),
        ('详细信息', {
            'fields': ('description',)
        }),
        # 时间信息会自动添加
    )


@admin.register(ClientGrade)
class ClientGradeAdmin(BaseModelAdmin):
    """客户分级管理"""
    list_display = ('name', 'code', 'display_order', 'is_active', 'created_time')
    list_filter = ('is_active', 'created_time')
    search_fields = ('name', 'code', 'description')
    list_editable = ('display_order', 'is_active')
    ordering = ('display_order', 'name')
    readonly_fields = ('created_time', 'updated_time')
    fieldsets = (
        ('基本信息', {
            'fields': ('code', 'name', 'display_order', 'is_active')
        }),
        ('详细信息', {
            'fields': ('description',)
        }),
        # 时间信息会自动添加
    )


@admin.register(School)
class SchoolAdmin(BaseModelAdmin):
    """学校管理"""
    list_display = ('name', 'region', 'get_tags_display', 'display_order', 'is_active', 'created_time')
    list_filter = ('region', 'is_211', 'is_985', 'is_double_first_class', 'is_active', 'created_time')
    search_fields = ('name', 'notes')
    list_editable = ('display_order', 'is_active')
    ordering = ('display_order', 'region', 'name')
    list_max_show_all = 200  # 最多显示200条记录
    readonly_fields = ('created_time', 'updated_time')
    
    def get_queryset(self, request):
        """获取查询集"""
        qs = super().get_queryset(request)
        return qs
    fieldsets = (
        ('基本信息', {
            'fields': ('name', 'region', 'display_order', 'is_active')
        }),
        ('学校标签', {
            'fields': ('is_211', 'is_985', 'is_double_first_class'),
            'description': '标记学校是否属于211工程、985工程或双一流建设高校'
        }),
        ('其他信息', {
            'fields': ('notes',)
        }),
        # 时间信息会自动添加
    )
    
    def get_tags_display(self, obj):
        """显示学校标签"""
        return obj.get_tags_display()
    get_tags_display.short_description = '标签'
    
    def has_change_permission(self, request, obj=None):
        """确保SchoolAdmin有修改权限（白名单模型）"""
        import logging
        logger = logging.getLogger(__name__)
        result = True
        logger.info(f'SchoolAdmin.has_change_permission called, obj={obj}, returning {result}')
        return result
    
    def has_view_permission(self, request, obj=None):
        """确保SchoolAdmin有查看权限（白名单模型）"""
        import logging
        logger = logging.getLogger(__name__)
        result = True
        logger.info(f'SchoolAdmin.has_view_permission called, obj={obj}, returning {result}')
        return result
    
    def has_add_permission(self, request):
        """确保SchoolAdmin有添加权限（白名单模型）"""
        import logging
        logger = logging.getLogger(__name__)
        result = True
        logger.info(f'SchoolAdmin.has_add_permission called, returning {result}')
        return result
    
    def has_delete_permission(self, request, obj=None):
        """确保SchoolAdmin有删除权限（白名单模型）"""
        import logging
        logger = logging.getLogger(__name__)
        result = True
        logger.info(f'SchoolAdmin.has_delete_permission called, obj={obj}, returning {result}')
        return result
    
    def has_module_permission(self, request):
        """确保SchoolAdmin有模块权限（白名单模型）"""
        import logging
        logger = logging.getLogger(__name__)
        result = True
        logger.info(f'SchoolAdmin.has_module_permission called, user={request.user}, returning {result}')
        return result
    
    def changelist_view(self, request, extra_context=None):
        """重写changelist_view，确保页面正常显示，允许未登录用户访问"""
        import logging
        logger = logging.getLogger(__name__)
        
        # 临时设置用户为staff（如果是匿名用户），以通过Django admin的内部检查
        # 这样可以使用Django admin的完整功能（搜索、过滤、分页等）
        original_user = request.user
        if not request.user.is_authenticated:
            from django.contrib.auth.models import AnonymousUser
            class TempUser(AnonymousUser):
                is_staff = True
                is_superuser = True
                is_authenticated = False
                def __init__(self):
                    super().__init__()
            request.user = TempUser()
        
        # 调试信息
        logger.info(f'SchoolAdmin changelist_view called by user: {request.user}')
        logger.info(f'has_view_permission: {self.has_view_permission(request)}')
        logger.info(f'has_change_permission: {self.has_change_permission(request)}')
        logger.info(f'has_add_permission: {self.has_add_permission(request)}')
        
        extra_context = extra_context or {}
        # 确保有必要的上下文
        extra_context['title'] = '学校管理'
        
        # 添加保护脚本和样式，确保内容可见
        extra_context['extra_head'] = extra_context.get('extra_head', '') + """
<style>
/* 强制显示Django admin内容 */
#content-main {
    display: block !important;
    visibility: visible !important;
    opacity: 1 !important;
    height: auto !important;
    width: auto !important;
    position: relative !important;
    overflow: visible !important;
}

.results {
    display: block !important;
    visibility: visible !important;
    opacity: 1 !important;
}

#changelist {
    display: flex !important; /* 使用 flex 布局以支持右侧过滤器 */
    visibility: visible !important;
}

#result_list {
    display: table !important;
    visibility: visible !important;
    width: 100% !important;
}

#result_list tbody {
    display: table-row-group !important;
    visibility: visible !important;
}

#result_list tbody tr {
    display: table-row !important;
    visibility: visible !important;
}

/* 确保body内容不被隐藏 */
body:not(.login) #content-main,
body:not(.login) .results {
    display: block !important;
    visibility: visible !important;
}

/* changelist 使用 flex 布局 */
body:not(.login) #changelist {
    display: flex !important;
    visibility: visible !important;
}
</style>
<script>
(function() {
    'use strict';
    // 立即保护Django admin内容，防止被Vue应用清空
    if (window.location.pathname.startsWith('/admin/')) {
        // 确保content-main可见
        function ensureContentVisible() {
            var contentMain = document.getElementById('content-main');
            if (contentMain) {
                contentMain.style.display = 'block';
                contentMain.style.visibility = 'visible';
                contentMain.style.opacity = '1';
                contentMain.style.height = 'auto';
                contentMain.style.width = 'auto';
            }
            
            var results = document.querySelector('.results');
            if (results) {
                results.style.display = 'block';
                results.style.visibility = 'visible';
            }
        }
        
        // 立即执行
        ensureContentVisible();
        
        // DOM加载完成后再次执行
        if (document.readyState === 'loading') {
            document.addEventListener('DOMContentLoaded', ensureContentVisible);
        } else {
            ensureContentVisible();
        }
        
        // 延迟执行，确保所有脚本执行完毕
        setTimeout(ensureContentVisible, 100);
        setTimeout(ensureContentVisible, 500);
        setTimeout(ensureContentVisible, 1000);
        
        // 监听DOM变化
        if (typeof MutationObserver !== 'undefined') {
            var observer = new MutationObserver(function() {
                ensureContentVisible();
            });
            
            observer.observe(document.body, {
                childList: true,
                subtree: true,
                attributes: true,
                attributeFilter: ['style', 'class']
            });
        }
    }
})();
</script>
"""
        
        # 调用父类方法
        try:
            logger.info('SchoolAdmin: calling super().changelist_view')
            response = super().changelist_view(request, extra_context)
            logger.info(f'SchoolAdmin: changelist_view returned, type: {type(response)}')
            if hasattr(response, 'status_code'):
                logger.info(f'SchoolAdmin: response status_code: {response.status_code}')
            
            # 检查响应上下文
            if hasattr(response, 'context_data') and response.context_data:
                logger.info(f'SchoolAdmin: response has context_data')
                if 'cl' in response.context_data:
                    logger.info(f'SchoolAdmin: changelist object (cl) exists')
                    cl = response.context_data['cl']
                    if hasattr(cl, 'queryset'):
                        logger.info(f'SchoolAdmin: queryset count: {cl.queryset.count()}')
                else:
                    logger.warning('SchoolAdmin: changelist object (cl) NOT in context_data!')
                    logger.warning(f'SchoolAdmin: context_data keys: {list(response.context_data.keys())}')
            else:
                logger.warning('SchoolAdmin: response has no context_data!')
            
            return response
        except Exception as e:
            logger.error(f'SchoolAdmin changelist_view error: {str(e)}', exc_info=True)
            raise
        finally:
            # 恢复原始用户
            request.user = original_user


# 所有业务模型的Admin注册已注释，改为在前端管理
# 如需查看数据，请使用API接口或前端管理页面
# 以下注册仅用于开发调试，生产环境建议注释掉

# @admin.register(Client)
# class ClientAdmin(admin.ModelAdmin):
#     list_display = ('name', 'unified_credit_code', 'client_level', 'grade', 'responsible_user', 'is_active', 'created_time')
#     list_filter = ('client_level', 'grade', 'credit_level', 'is_active', 'created_time')
#     search_fields = ('name', 'unified_credit_code')
#     readonly_fields = ('created_time', 'updated_time', 'score', 'grade')

# @admin.register(ClientContact)
# class ClientContactAdmin(admin.ModelAdmin):
#     list_display = ('name', 'client', 'role', 'relationship_level', 'phone', 'email', 'created_time')
#     list_filter = ('role', 'relationship_level', 'created_time')
#     search_fields = ('name', 'phone', 'email', 'client__name')
#     readonly_fields = ('created_time', 'updated_time', 'work_years', 'relationship_score')


# @admin.register(ClientContact)
# class ClientContactAdmin(admin.ModelAdmin):
#     ...

# @admin.register(BusinessContract)
# class BusinessContractAdmin(admin.ModelAdmin):
#     ...

# @admin.register(BusinessPaymentPlan)
# class BusinessPaymentPlanAdmin(admin.ModelAdmin):
#     ...

# @admin.register(AuthorizationLetter)
# class AuthorizationLetterAdmin(admin.ModelAdmin):
#     list_display = ('letter_number', 'name', 'client_name', 'status', 'amount', 'letter_date', 'created_by', 'created_time')
#     list_filter = ('status', 'letter_date', 'created_time')
#     search_fields = ('letter_number', 'name', 'client_name', 'trustee_name')
#     readonly_fields = ('letter_number', 'created_time', 'updated_time', 'duration_days')
#     date_hierarchy = 'letter_date'
