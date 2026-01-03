"""
权限代码映射工具
用于向后兼容旧的权限代码
"""

# 客户管理权限代码映射（旧 -> 新）
CUSTOMER_PERMISSION_MAPPING = {
    # 客户信息管理
    'customer_success.view': 'customer_management.client.view',  # 自动根据角色选择级别
    'customer_success.manage': 'customer_management.client.edit',
    # 客户人员管理
    'customer_success.contact.view': 'customer_management.contact.view',
    'customer_success.contact.manage': 'customer_management.contact.edit',
    # 客户关系管理
    'customer_success.relationship.view': 'customer_management.relationship.view',
    'customer_success.relationship.manage': 'customer_management.relationship.edit',
    # 客户公海
    'customer_success.public_sea.view': 'customer_management.public_sea.view',
    'customer_success.public_sea.claim': 'customer_management.public_sea.claim',
    # 客户分析
    'customer_success.analyze': 'customer_management.analysis.view',
    # 合同管理（向后兼容，customer_success.manage 也可以访问合同管理）
    'customer_success.contract.view': 'customer_management.contract.view',
    'customer_success.contract.manage': 'customer_management.contract.manage',
    # 商机管理（向后兼容）
    'customer_success.opportunity.view': 'customer_management.opportunity.view',
    'customer_success.opportunity.manage': 'customer_management.opportunity.manage',
    # 合同管理权限代码统一映射（contract_management -> customer_management）
    'contract_management.contract.view': 'customer_management.contract.view',
    'contract_management.contract.create': 'customer_management.contract.create',
    'contract_management.contract.edit': 'customer_management.contract.manage',
    'contract_management.contract.delete': 'customer_management.contract.manage',
    'contract_management.contract.approve': 'customer_management.contract.manage',
    'contract_management.contract.sign': 'customer_management.contract.manage',
    'contract_management.contract.change': 'customer_management.contract.manage',
    'contract_management.contract.file.manage': 'customer_management.contract.manage',
}


def normalize_permission_code(permission_code: str) -> str:
    """
    规范化权限代码，将旧代码映射到新代码
    
    Args:
        permission_code: 权限代码（可能是旧代码或新代码）
    
    Returns:
        规范化后的权限代码
    """
    return CUSTOMER_PERMISSION_MAPPING.get(permission_code, permission_code)


def normalize_permission_codes(*permission_codes: str) -> tuple:
    """
    规范化多个权限代码
    
    Args:
        *permission_codes: 权限代码列表
    
    Returns:
        规范化后的权限代码元组
    """
    return tuple(normalize_permission_code(code) for code in permission_codes)


def has_customer_permission(user, *permission_codes: str) -> bool:
    """
    检查用户是否拥有客户管理权限（支持新旧权限代码）
    
    Args:
        user: 用户对象
        *permission_codes: 权限代码列表（支持旧代码）
    
    Returns:
        是否拥有权限
    """
    from backend.apps.system_management.services import get_user_permission_codes, user_has_permission
    
    # 规范化权限代码
    normalized_codes = normalize_permission_codes(*permission_codes)
    
    # 检查权限
    return user_has_permission(user, *normalized_codes)

