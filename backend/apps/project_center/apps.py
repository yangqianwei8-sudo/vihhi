from django.apps import AppConfig


class ProjectCenterConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'backend.apps.project_center'
    verbose_name = '项目中心'
    
    def ready(self):
        """应用启动时注册信号处理器"""
        # 信号处理器已迁移到production_management
        # import backend.apps.project_center.signals  # noqa
        pass
