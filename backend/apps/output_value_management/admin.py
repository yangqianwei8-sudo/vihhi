from django.contrib import admin
from django.utils.html import format_html
from backend.core.admin_base import BaseModelAdmin
from backend.apps.output_value_management.models import OutputValuePolicy


@admin.register(OutputValuePolicy)
class OutputValuePolicyAdmin(BaseModelAdmin):
    """
    产值口径配置 — 唯一权威配置入口。
    修改后立即生效，计算内核（calculator_v1）从本表读取所有可变口径。
    """
    list_display = ('name', 'enabled', 'stage_weight', 'event_modifier_min', 'event_modifier_max',
                    'confidence_high_threshold', 'updated_at')
    list_filter = ('enabled',)
    search_fields = ('name',)
    ordering = ('-updated_at',)
    readonly_fields = ('updated_at', 'created_at')

    fieldsets = (
        ('说明', {
            'fields': (),
            'description': format_html(
                '<p style="font-weight:bold;color:#c00;">这是<strong>唯一权威产值口径</strong>。'
                '修改后立即生效；全系统仅允许一条「是否生效」= 是。'
                '服务类型权重为 JSON：{{"转化阶段":"0.02","conversion":"0.02", ...}}，支持中文名与 code。</p>'
            ),
        }),
        ('口径参数', {
            'fields': (
                'name', 'enabled', 'effective_from',
                'service_type_weights',
                'stage_weight',
                'event_modifier_min', 'event_modifier_max',
                'confidence_high_threshold',
            ),
        }),
        ('审计', {
            'fields': ('updated_by', 'updated_at', 'created_at'),
            'classes': ('collapse',),
        }),
    )

    def save_model(self, request, obj, form, change):
        if not change:
            obj.updated_by = request.user
        else:
            obj.updated_by = request.user
        super().save_model(request, obj, form, change)
