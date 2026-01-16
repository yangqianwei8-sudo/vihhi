"""
项目中心信号处理器
"""
import logging
from django.db.models.signals import post_save
from django.dispatch import receiver
from django.db import transaction
from django.db.models import Max
from django.utils import timezone
from backend.apps.workflow_engine.models import ApprovalInstance
from backend.apps.project_center.models import Project

logger = logging.getLogger(__name__)



