"""
字段渲染器
提供字段值的获取和渲染功能
"""
from typing import Any, Optional
from django.template.loader import render_to_string
from django.template import Context
from .formatters import format_value


def get_field_value(data: Any, field_id: str) -> Any:
    """
    获取字段值（支持嵌套路径）
    
    Args:
        data: 数据对象（模型实例或字典）
        field_id: 字段ID，支持嵌套路径（如 'user.profile.name'）
    
    Returns:
        字段值，如果不存在返回None
    """
    if not field_id:
        return None
    
    keys = field_id.split('.')
    value = data
    current_obj = data
    
    for i, key in enumerate(keys):
        if value is None:
            return None
        
        # 检查是否是方法调用（如 get_status_display）
        if hasattr(current_obj, key):
            try:
                attr = getattr(current_obj, key)
                # 如果是方法且可调用
                if callable(attr) and not key.startswith('_'):
                    try:
                        value = attr()
                        # 如果值为None且还有后续键，直接返回None
                        if value is None and i < len(keys) - 1:
                            return None
                        # 如果还有后续键，继续处理
                        if i < len(keys) - 1:
                            current_obj = value
                            continue
                        else:
                            return value
                    except Exception:
                        # 如果方法调用失败，尝试作为属性处理
                        pass
                
                # 如果是属性
                value = attr
                # 如果值为None，直接返回
                if value is None:
                    return None
                current_obj = value
                
                # 处理 choices 字段的显示方法（如果当前对象是模型实例）
                if hasattr(current_obj, '_meta'):
                    try:
                        model_field = current_obj._meta.get_field(key)
                        if hasattr(model_field, 'choices') and model_field.choices:
                            display_method = getattr(current_obj, f'get_{key}_display', None)
                            if display_method:
                                return display_method()
                    except Exception:
                        pass
            except AttributeError:
                return None
        # 如果是字典
        elif isinstance(current_obj, dict) and key in current_obj:
            value = current_obj[key]
            if value is None:
                return None
            current_obj = value
        else:
            return None
    
    return value


def render_field(field_config: Any, data: Any, context: Optional[dict] = None) -> str:
    """
    渲染字段
    
    Args:
        field_config: 字段配置对象（FieldConfig）
        data: 数据对象
        context: 模板上下文
    
    Returns:
        渲染后的HTML字符串
    """
    # 获取字段值
    value = get_field_value(data, field_config.id)
    
    # 格式化
    if field_config.format:
        value = format_value(value, field_config.format)
    
    # 选择模板
    template_map = {
        'text': 'shared/details/components/fields/_text_field.html',
        'date': 'shared/details/components/fields/_date_field.html',
        'datetime': 'shared/details/components/fields/_date_field.html',
        'status': 'shared/details/components/fields/_status_field.html',
        'link': 'shared/details/components/fields/_link_field.html',
        'tag': 'shared/details/components/fields/_tag_field.html',
        'phone': 'shared/details/components/fields/_phone_field.html',
        'email': 'shared/details/components/fields/_email_field.html',
        'address': 'shared/details/components/fields/_text_field.html',
        'currency': 'shared/details/components/fields/_text_field.html',
        'percent': 'shared/details/components/fields/_text_field.html',
    }
    
    template_name = template_map.get(field_config.type, template_map['text'])
    
    # 准备上下文
    render_context = {
        'field': field_config,
        'value': value,
        'data': data,
    }
    
    # 处理 context 参数（可能是 RequestContext 或字典）
    # 对于字段渲染，我们只需要 request 对象，不需要其他上下文变量
    request_obj = None
    if context:
        try:
            # 尝试获取 request 对象
            if isinstance(context, dict):
                # 普通字典
                request_obj = context.get('request')
                # 可以安全地更新其他变量（如果有的话）
                # 但通常字段渲染不需要额外的上下文变量
            elif hasattr(context, 'get'):
                # RequestContext 对象，使用 get() 方法
                request_obj = context.get('request')
            elif hasattr(context, '__getitem__'):
                # 其他类型的上下文对象
                try:
                    request_obj = context['request']
                except (KeyError, TypeError):
                    pass
        except Exception:
            # 如果获取 request 失败，继续使用 None
            pass
    
    return render_to_string(
        template_name,
        render_context,
        request=request_obj
    )

