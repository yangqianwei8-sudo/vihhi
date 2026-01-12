from django.apps import AppConfig


class DetailConfigConfig(AppConfig):
    """详情页配置系统应用配置"""
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'backend.apps.detail_config'
    verbose_name = '详情页配置系统'

