# 计划管理页面视图包：从子模块聚合导出，供 urls_pages 使用
from . import _legacy

# 先从 _legacy 导出所有公开名称
for _name in dir(_legacy):
    if not _name.startswith('_'):
        globals()[_name] = getattr(_legacy, _name)

# 导出菜单/权限辅助函数（供 core/views、plan_management/views 等引用）
from .menu import (
    _build_plan_management_sidebar_nav,
    _filter_plans_by_permission,
    _context,
    get_plan_qs_for_user,
    get_plan_or_404,
    get_pending_decision_or_404,
    get_goal_qs_for_user,
)
from .helpers import (
    calculate_child_goals_summary,
    calculate_child_plans_summary,
    calculate_goal_progress_status,
    calculate_plan_progress_status,
    _form_errors_plain,
    _validate_plan_fields,
)

# 用已拆出的首页覆盖
from .home import plan_management_home

# 向后兼容：部分命令/代码从 views_pages 导入 apply_company_scope（实际在 utils）
try:
    from backend.apps.plan_management.utils import apply_company_scope
except ImportError:
    apply_company_scope = None
