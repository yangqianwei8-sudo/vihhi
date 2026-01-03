from django.apps import AppConfig


class ArchiveManagementConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'backend.apps.archive_management'
    verbose_name = '档案管理'
    
    def ready(self):
        """应用启动时注册信号处理器"""
        import backend.apps.archive_management.signals  # noqa

