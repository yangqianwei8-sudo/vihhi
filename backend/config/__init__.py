"""
Django配置初始化
修复DRF format_suffix_patterns转换器重复注册问题
"""
import django.urls.converters

# 修复DRF format_suffix_patterns转换器重复注册问题
# 在DRF注册转换器之前，先检查是否已注册
_original_register_converter = django.urls.converters.register_converter

def _patched_register_converter(converter, type_name):
    """补丁版本的register_converter，避免重复注册drf_format_suffix"""
    if type_name == 'drf_format_suffix':
        # 检查是否已注册
        if type_name in django.urls.converters.get_converters():
            # 已注册，跳过
            return
    # 调用原始函数
    return _original_register_converter(converter, type_name)

# 应用补丁
django.urls.converters.register_converter = _patched_register_converter


