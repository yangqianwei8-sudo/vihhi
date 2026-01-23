"""
审批流程引擎服务模块
"""
# 从父级 services.py 模块导入 ApprovalEngine（避免循环导入）
# 使用 importlib 来导入同级的 services.py 文件
import importlib.util
import sys
from pathlib import Path

# 获取父级目录的 services.py 文件路径
_parent_dir = Path(__file__).parent.parent
_services_py_path = _parent_dir / 'services.py'

if _services_py_path.exists():
    # 动态导入 services.py 模块
    spec = importlib.util.spec_from_file_location(
        "backend.apps.workflow_engine.services_py",
        _services_py_path
    )
    _services_py_module = importlib.util.module_from_spec(spec)
    sys.modules['backend.apps.workflow_engine.services_py'] = _services_py_module
    spec.loader.exec_module(_services_py_module)
    ApprovalEngine = _services_py_module.ApprovalEngine
else:
    # 如果 services.py 不存在，尝试标准导入
    from ..services import ApprovalEngine

# 延迟导入 UniversalApprovalService（避免循环导入）
# UniversalApprovalService 会在需要时从 universal_approval 模块导入
__all__ = ['ApprovalEngine']

def __getattr__(name):
    """延迟导入 UniversalApprovalService"""
    if name == 'UniversalApprovalService':
        from .universal_approval import UniversalApprovalService
        return UniversalApprovalService
    raise AttributeError(f"module '{__name__}' has no attribute '{name}'")

