"""
合同管理模块权限定义
"""

# 权限定义模块
# 注意：实际的权限检查使用系统统一的权限管理机制

# 权限代码常量
PERMISSION_VIEW = 'contract_management.contract.view'
PERMISSION_CREATE = 'contract_management.contract.create'
PERMISSION_EDIT = 'contract_management.contract.edit'
PERMISSION_DELETE = 'contract_management.contract.delete'
PERMISSION_APPROVE = 'contract_management.contract.approve'
PERMISSION_SIGN = 'contract_management.contract.sign'
PERMISSION_CHANGE = 'contract_management.contract.change'
PERMISSION_FILE_MANAGE = 'contract_management.contract.file.manage'


def get_contract_permissions():
    """
    获取合同管理相关的所有权限
    """
    return {
        'view': 'contract_management.contract.view',
        'create': 'contract_management.contract.create',
        'edit': 'contract_management.contract.edit',
        'delete': 'contract_management.contract.delete',
        'approve': 'contract_management.contract.approve',
        'sign': 'contract_management.contract.sign',
        'change': 'contract_management.contract.change',
        'file_manage': 'contract_management.contract.file.manage',
    }


def check_contract_permission(user, permission_code):
    """
    检查用户是否具有指定的合同管理权限
    
    Args:
        user: 用户对象
        permission_code: 权限代码
        
    Returns:
        bool: 是否有权限
    """
    if not user or not user.is_authenticated:
        return False
    
    # 超级用户拥有所有权限
    if user.is_superuser:
        return True
    
    # 检查用户权限
    try:
        from backend.apps.system_management.services import get_user_permission_codes
        from backend.core.views import _permission_granted
        permission_set = get_user_permission_codes(user)
        return _permission_granted(permission_code, permission_set)
    except ImportError:
        # 如果导入失败，返回False
        return False

