"""
权限映射表：业务权限 -> Django codename
用于统一权限判定和同步
"""

# 计划管理模块权限映射
PLAN_MANAGEMENT_PERMISSION_MAPPING = {
    # 业务权限 -> Django codename
    'plan_management.view': 'plan_management.view_plan',
    'plan_management.plan.view': 'plan_management.view_plan',
    'plan_management.goal.view': 'plan_management.view_strategicgoal',
    'plan_management.view_plan': 'plan_management.view_plan',  # 已统一
    'plan_management.view_strategicgoal': 'plan_management.view_strategicgoal',  # 已统一
    
    # 创建权限
    'plan_management.create': 'plan_management.add_plan',
    'plan_management.plan.create': 'plan_management.add_plan',
    'plan_management.goal.create': 'plan_management.add_strategicgoal',
    
    # 管理权限（通常包含多个操作）
    'plan_management.manage_goal': [
        'plan_management.add_strategicgoal',
        'plan_management.change_strategicgoal',
        'plan_management.delete_strategicgoal',
    ],
    'plan_management.plan.manage': [
        'plan_management.change_plan',
        'plan_management.delete_plan',
    ],
    
    # 审批权限
    'plan_management.approve': [
        'plan_management.approve_plan',
        'plan_management.approve_strategicgoal',
    ],
}

# 反向映射：Django codename -> 业务权限（用于同步）
DJANGO_TO_BUSINESS_MAPPING = {
    'plan_management.view_plan': ['plan_management.view', 'plan_management.plan.view', 'plan_management.view_plan'],
    'plan_management.view_strategicgoal': ['plan_management.goal.view', 'plan_management.view_strategicgoal'],
    'plan_management.add_plan': ['plan_management.create', 'plan_management.plan.create'],
    'plan_management.add_strategicgoal': ['plan_management.goal.create'],
    'plan_management.change_plan': ['plan_management.plan.manage'],
    'plan_management.change_strategicgoal': ['plan_management.manage_goal'],
    'plan_management.delete_plan': ['plan_management.plan.manage'],
    'plan_management.delete_strategicgoal': ['plan_management.manage_goal'],
    'plan_management.approve_plan': ['plan_management.approve'],
    'plan_management.approve_strategicgoal': ['plan_management.approve'],
}


def map_business_to_django(business_perm: str) -> list:
    """
    将业务权限映射到 Django codename(s)
    返回列表，因为一个业务权限可能对应多个 Django 权限
    
    Args:
        business_perm: 业务权限代码，如 'plan_management.view'
    
    Returns:
        list: Django codename 列表，如 ['plan_management.view_plan']
    """
    mapped = PLAN_MANAGEMENT_PERMISSION_MAPPING.get(business_perm)
    if mapped is None:
        return []
    if isinstance(mapped, str):
        return [mapped]
    if isinstance(mapped, list):
        return mapped
    return []


def get_all_django_perms_for_module(module: str = 'plan_management') -> list:
    """
    获取模块的所有 Django 权限 codename
    
    Args:
        module: 模块名，默认 'plan_management'
    
    Returns:
        list: Django codename 列表
    """
    if module == 'plan_management':
        return [
            'plan_management.view_plan',
            'plan_management.view_strategicgoal',
            'plan_management.add_plan',
            'plan_management.add_strategicgoal',
            'plan_management.change_plan',
            'plan_management.change_strategicgoal',
            'plan_management.delete_plan',
            'plan_management.delete_strategicgoal',
            'plan_management.approve_plan',
            'plan_management.approve_strategicgoal',
        ]
    return []

