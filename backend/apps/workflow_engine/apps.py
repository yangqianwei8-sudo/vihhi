from django.apps import AppConfig


class WorkflowEngineConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'backend.apps.workflow_engine'
    verbose_name = '审批流程引擎'

