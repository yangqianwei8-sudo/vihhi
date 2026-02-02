# 客户管理页面视图包：从子模块聚合导出，供 customer_urls / urls_pages 使用
from . import _legacy

# 先从 _legacy 导出所有公开名称
for _name in dir(_legacy):
    if not _name.startswith('_'):
        globals()[_name] = getattr(_legacy, _name)

# 导出菜单/权限辅助函数（供 contract_management 等应用引用）
from .menu import (
    _filter_clients_by_permission,
    _check_customer_permission,
    _build_customer_management_sidebar_nav,
    _build_opportunity_management_sidebar_nav,
    _context,
)

# 用已拆出的模块覆盖
from .redirects import (
    authorization_letter_list_redirect,
    authorization_letter_create_redirect,
    authorization_letter_detail_redirect,
    authorization_letter_edit_redirect,
    authorization_letter_delete_redirect,
    authorization_letter_status_transition_redirect,
    authorization_letter_template_list_redirect,
    authorization_letter_template_create_redirect,
    authorization_letter_template_edit_redirect,
    authorization_letter_template_delete_redirect,
    authorization_letter_create_from_template_redirect,
    authorization_letter_template_file_preview_redirect,
    authorization_letter_template_file_download_redirect,
)
from .home import customer_management_home
