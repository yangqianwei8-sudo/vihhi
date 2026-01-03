from django.apps import AppConfig


class SettlementCenterConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'backend.apps.settlement_center'
    verbose_name = '结算中心'
    
    def ready(self):
        """应用就绪时导入信号处理器"""
        import backend.apps.settlement_center.signals  # noqa