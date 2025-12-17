from django.apps import AppConfig


class ProductionManagementConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'backend.apps.production_management'
    verbose_name = '合同管理'
    
    def ready(self):
        """应用启动时注册信号处理器"""
        import backend.apps.production_management.signals  # noqa

