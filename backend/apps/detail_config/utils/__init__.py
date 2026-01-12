"""
工具模块
提供详情页相关的工具函数
"""

from .formatters import format_value
from .field_renderers import render_field, get_field_value
from .auto_discover import auto_discover_fields, build_auto_config

__all__ = [
    'format_value',
    'render_field',
    'get_field_value',
    'auto_discover_fields',
    'build_auto_config',
]

