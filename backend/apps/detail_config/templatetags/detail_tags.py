"""
详情页模板标签
提供详情页渲染相关的模板标签和过滤器
"""
from django import template
from django.template.loader import render_to_string
from backend.apps.detail_config.utils.field_renderers import render_field, get_field_value
from backend.apps.detail_config.utils.formatters import format_value

register = template.Library()


@register.simple_tag(takes_context=True)
def render_detail_field(context, field_config, data):
    """
    渲染详情字段
    
    用法：
        {% render_detail_field field_config data %}
    """
    return render_field(field_config, data, context)


@register.simple_tag(takes_context=True)
def render_detail_section(context, section_config, data):
    """
    渲染详情区块
    
    用法：
        {% render_detail_section section_config data %}
    """
    # 传递所有上下文变量，特别是自定义组件需要的变量
    render_context = {
        'section': section_config,
        'data': data,
    }
    
    # 获取 request 对象
    try:
        request_val = context.get('request') if hasattr(context, 'get') else (context['request'] if hasattr(context, '__getitem__') else None)
        render_context['request'] = request_val
    except Exception:
        pass
    
    # 传递额外的上下文变量（如contacts, execution_records等）
    # RequestContext 对象不能直接用 dict() 转换，直接访问需要的变量
    known_keys = [
        'contacts', 'execution_records', 'execution_count', 'client', 
        'approval_instance', 'approval_records', 'approval_path_nodes', 
        'can_submit_approval', 'can_approve_workflow', 'config', 'data'
    ]
    
    for key in known_keys:
        try:
            # 尝试使用 get() 方法
            if hasattr(context, 'get'):
                try:
                    value = context.get(key)
                    if value is not None:
                        render_context[key] = value
                        continue
                except Exception:
                    pass
            
            # 如果 get() 方法不可用，尝试直接访问
            if hasattr(context, '__getitem__'):
                try:
                    render_context[key] = context[key]
                except (TypeError, KeyError):
                    pass
        except Exception:
            pass
    
    # 确保 render_context 是一个干净的字典
    # 创建一个新的字典，避免直接修改原字典
    clean_context = {}
    request_obj = None
    
    for key, value in render_context.items():
        if key == 'request':
            request_obj = value
        else:
            clean_context[key] = value
    
    return render_to_string(
        'shared/details/components/sections/_detail_section.html',
        clean_context,
        request=request_obj
    )


@register.simple_tag
def get_field_value_tag(data, field_id):
    """
    获取字段值（支持嵌套路径）
    
    用法：
        {% get_field_value_tag data 'field_id' %}
    """
    return get_field_value(data, field_id)


@register.filter
def detail_format(value, format_type):
    """
    格式化值
    
    用法：
        {{ value|detail_format:'currency' }}
    """
    return format_value(value, format_type)

