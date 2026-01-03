import os

# 修复DRF format_suffix_patterns转换器重复注册问题
# 必须在导入Django之前应用补丁
import django.urls.converters

_original_register_converter = django.urls.converters.register_converter

def _patched_register_converter(converter, type_name):
    """补丁版本的register_converter，避免重复注册drf_format_suffix"""
    if type_name == 'drf_format_suffix':
        # 检查是否已注册（使用内部字典检查）
        try:
            # 直接访问内部注册表
            if hasattr(django.urls.converters, '_ converters'):
                if type_name in django.urls.converters._converters:
                    return
            # 或者通过get_converters检查
            converters = django.urls.converters.get_converters()
            if type_name in converters:
                return
        except (AttributeError, Exception):
            # 如果检查失败，尝试注册（可能会失败，但至少不会崩溃）
            pass
    # 调用原始函数
    try:
        return _original_register_converter(converter, type_name)
    except ValueError as e:
        # 如果已经注册，忽略错误
        if 'already registered' in str(e):
            return
        raise

# 应用补丁
django.urls.converters.register_converter = _patched_register_converter

from django.core.wsgi import get_wsgi_application

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'backend.config.settings')

application = get_wsgi_application()
