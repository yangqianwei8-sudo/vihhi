from django.apps import AppConfig


class PermissionManagementConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'backend.apps.permission_management'
    label = 'permission_management'  # 明确指定应用标签
    verbose_name = '权限管理'
