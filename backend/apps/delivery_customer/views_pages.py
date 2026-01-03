"""
视图模块 - 重构后的入口文件
为了保持向后兼容，此文件从拆分后的模块导入所有视图函数

注意：由于 views_pages.py 和 views_pages/ 目录同名，Python 会优先导入文件。
这里使用相对导入来导入 views_pages 包（目录）中的模块。
"""
# 使用相对导入从 views_pages 包导入所有视图函数
# 注意：由于命名冲突，这里使用 .views_pages 来明确指向目录包
from .views_pages.delivery_views import *
from .views_pages.incoming_document_views import *
from .views_pages.outgoing_document_views import *
from .views_pages.express_views import *
from .views_pages.file_views import *
from .views_pages.email_sms_views import *
from .views_pages.other_views import *

# 导出公共函数和配置
from .views_pages.common import (
    DELIVERY_MANAGEMENT_MENU,
    _get_active_id_from_path,
    _build_delivery_sidebar_nav,
    _context,
    check_permission_or_redirect,
)
