from django.apps import AppConfig


class ProductionQualityConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'backend.apps.production_quality'
    verbose_name = '生产质量'

