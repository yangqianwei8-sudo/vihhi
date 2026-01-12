"""
详情页助手函数
提供详情页相关的辅助功能
"""


def check_permission(user, permission: str) -> bool:
    """
    检查用户权限
    
    Args:
        user: 用户对象
        permission: 权限字符串（格式：app.permission）
    
    Returns:
        是否有权限
    """
    if not permission:
        return True
    
    if not user or not user.is_authenticated:
        return False
    
    # 简单的权限检查，可以根据实际权限系统扩展
    # 这里假设使用Django的权限系统
    app_label, perm = permission.split('.', 1)
    return user.has_perm(f"{app_label}.{perm}")


def check_conditions(data: dict, conditions: dict) -> bool:
    """
    检查显示条件
    
    Args:
        data: 数据对象
        conditions: 条件字典
    
    Returns:
        是否满足条件
    """
    if not conditions:
        return True
    
    # 简单的条件检查实现
    # 可以根据需要扩展更复杂的条件逻辑
    for key, expected_value in conditions.items():
        actual_value = getattr(data, key, None)
        if actual_value != expected_value:
            return False
    
    return True

