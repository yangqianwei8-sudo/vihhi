from django import template

register = template.Library()

@register.filter
def get_item(dictionary, key):
    """从字典中获取值"""
    if dictionary is None:
        return None
    return dictionary.get(key)


@register.filter(name='tracking_status_display')
def tracking_status_display(status):
    """
    统一的状态显示过滤器
    将状态码转换为中文显示
    支持目标和计划的状态显示
    """
    # 统一的状态映射
    # 注意：draft 在目标中显示为'制定中'，在计划中显示为'草稿'
    # 这里统一使用'制定中'，计划模板中可以覆盖显示
    status_map = {
        'draft': '制定中',
        'published': '已发布',
        'in_progress': '执行中',
        'completed': '已完成',
        'cancelled': '已取消',
        'paused': '已暂停',
        'delayed': '已延期',
    }
    return status_map.get(status, status)


@register.filter(name='extract_notes')
def extract_notes(notes_text):
    """
    从文本型目标的 notes 字段中提取备注部分
    notes 格式: "[文本进度] 文本内容\n备注内容"
    返回备注部分，如果没有备注则返回空字符串
    """
    if not notes_text:
        return ''
    
    # 检查是否是文本型格式
    if notes_text.startswith('[文本进度]'):
        # 去掉前缀 "[文本进度] "
        content_after_prefix = notes_text[8:].strip()
        # 查找第一个换行符
        if '\n' in content_after_prefix:
            # 提取换行符后的内容作为备注
            parts = content_after_prefix.split('\n', 1)
            if len(parts) > 1:
                return parts[1].strip()
    
    # 非文本型或没有备注，返回原内容
    return notes_text
