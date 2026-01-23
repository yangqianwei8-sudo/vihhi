from django.apps import AppConfig


class PlanManagementConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'backend.apps.plan_management'
    verbose_name = '计划管理'
    
    def ready(self):
        """应用启动时注册信号处理器"""
        import backend.apps.plan_management.signals  # noqa

