"""
视图模块 - 按业务模块拆分
导出所有视图函数以保持向后兼容
"""
from .delivery_views import *
from .incoming_document_views import *
from .outgoing_document_views import *
from .express_views import *
from .file_views import *
from .email_sms_views import *
from .other_views import *

# 导出公共函数和配置
from .common import (
    DELIVERY_MANAGEMENT_MENU,
    _get_active_id_from_path,
    _build_delivery_sidebar_nav,
    _context,
    check_permission_or_redirect,
)

