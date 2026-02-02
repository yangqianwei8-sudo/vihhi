# 商机权限统一检查
# 统一使用 opportunity_management.opportunity.* 作为规范权限码
# 兼容 customer_management.opportunity.*（仅在此模块内做映射）

PREFIX = 'opportunity_management.opportunity'
LEGACY_PREFIX = 'customer_management.opportunity'

# 兼容映射：旧权限码 -> 规范权限码（用于权限检查时同时接受两种）
LEGACY_MAP = {
    f'{LEGACY_PREFIX}.view': f'{PREFIX}.view',
    f'{LEGACY_PREFIX}.view_all': f'{PREFIX}.view_all',
    f'{LEGACY_PREFIX}.create': f'{PREFIX}.create',
    f'{LEGACY_PREFIX}.edit': f'{PREFIX}.edit',
    f'{LEGACY_PREFIX}.delete': f'{PREFIX}.delete',
    f'{LEGACY_PREFIX}.manage': f'{PREFIX}.manage',
}


def _perm(permission_set: set, action: str) -> bool:
    """
    检查商机权限（支持规范码与兼容码）
    permission_set: get_user_permission_codes(user)
    action: view | view_all | create | edit | delete | manage
    """
    if '__all__' in permission_set:
        return True
    canonical = f'{PREFIX}.{action}'
    legacy = f'{LEGACY_PREFIX}.{action}'
    return canonical in permission_set or legacy in permission_set


def opportunity_can_view(permission_set: set) -> bool:
    """是否有基础查看权限"""
    return _perm(permission_set, 'view')


def opportunity_can_view_all(permission_set: set) -> bool:
    """是否可查看全部商机（不限于 business_manager）"""
    return _perm(permission_set, 'view_all')


def opportunity_can_create(permission_set: set) -> bool:
    """是否可创建商机"""
    return _perm(permission_set, 'create')


def opportunity_can_edit(permission_set: set) -> bool:
    """是否可编辑商机（全局权限）"""
    return _perm(permission_set, 'edit')


def opportunity_can_delete(permission_set: set) -> bool:
    """是否可删除商机"""
    return _perm(permission_set, 'delete')


def opportunity_can_manage(permission_set: set) -> bool:
    """是否可管理（高级操作）"""
    return _perm(permission_set, 'manage')


def opportunity_can_access_detail(user, opportunity, permission_set: set) -> bool:
    """
    是否可查看商机详情
    view_all 用户可看全部；普通用户只能看自己 business_manager 的
    """
    if opportunity_can_view_all(permission_set):
        return True
    if not opportunity_can_view(permission_set):
        return False
    return opportunity.business_manager_id == user.id if opportunity.business_manager_id else False


def opportunity_can_access_edit(user, opportunity, permission_set: set) -> bool:
    """
    是否可编辑/流转/删除商机
    有 edit 权限可操作全部；否则仅可操作自己负责的
    """
    if opportunity_can_edit(permission_set):
        return True
    return opportunity.business_manager_id == user.id if opportunity.business_manager_id else False


def opportunity_sidebar_permission(action: str) -> str:
    """
    返回用于侧边栏/菜单的规范权限码（统一为 opportunity_management.*）
    action: view | manage
    """
    return f'{PREFIX}.{action}'


def expand_permission_set_for_nav(permission_set: set) -> set:
    """
    为菜单/侧边栏检查扩展权限集：将 legacy 码视为 canonical
    使得拥有 customer_management.opportunity.* 的用户也能通过 opportunity_management.* 的菜单检查
    """
    if '__all__' in permission_set:
        return permission_set
    expanded = set(permission_set)
    for legacy, canonical in LEGACY_MAP.items():
        if legacy in permission_set:
            expanded.add(canonical)
    return expanded
