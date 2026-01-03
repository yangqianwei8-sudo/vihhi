from django.apps import AppConfig


class LitigationManagementConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'backend.apps.litigation_management'
    
    def ready(self):
        """应用启动时注册信号处理器"""
        import backend.apps.litigation_management.signals  # noqa
    verbose_name = '诉讼管理'

