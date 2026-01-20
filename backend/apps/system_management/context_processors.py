"""
系统管理模块的上下文处理器
用于在所有页面中提供通用的上下文变量
"""
from .forms import SystemFeedbackForm


def feedback_form(request):
    """在所有页面中提供反馈表单对象"""
    if request and hasattr(request, 'user') and request.user.is_authenticated:
        try:
            return {
                'feedback_form': SystemFeedbackForm()
            }
        except Exception:
            # 如果创建表单失败，返回None
            return {
                'feedback_form': None
            }
    return {
        'feedback_form': None
    }
