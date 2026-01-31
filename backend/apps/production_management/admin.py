"""
生产管理模块的 Admin 配置
基础数据（ServiceType、DesignStage 等）已迁移至 base_data 应用
"""

from django.contrib import admin
from django.utils.html import format_html
from django.urls import reverse, path
from django import forms
from django.shortcuts import render
from django.contrib.admin.views.decorators import staff_member_required

from backend.apps.production_management.models import Project
from backend.core.admin_base import BaseModelAdmin, AuditAdminMixin, LinkAdminMixin


