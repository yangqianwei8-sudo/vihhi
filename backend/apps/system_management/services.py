
from typing import Set

from django.db.models import Prefetch

from backend.apps.permission_management.models import PermissionItem


def get_user_permission_codes(user) -> Set[str]:
    """Return a set of business permission codes granted to the user."""
    if user is None or not getattr(user, 'is_authenticated', False):
        return set()

    if getattr(user, 'is_superuser', False):
        return {'__all__'}

    cache_attr = '_permission_codes_cache'
    if hasattr(user, cache_attr):
        return getattr(user, cache_attr)

    roles_qs = user.roles.filter(is_active=True).prefetch_related(
        Prefetch('custom_permissions', queryset=PermissionItem.objects.only('code'))
    )

    # 检查是否有 system_admin 或 general_manager 角色（这些角色拥有全部权限）
    role_codes = {role.code for role in roles_qs}
    if 'system_admin' in role_codes or 'general_manager' in role_codes:
        permission_codes = {'__all__'}
    else:
        permission_codes = {perm.code for role in roles_qs for perm in role.custom_permissions.all()}
    
    setattr(user, cache_attr, permission_codes)
    return permission_codes


def user_has_permission(user, *permission_codes: str) -> bool:
    """Check whether the user has any of the specified permission codes."""
    codes = get_user_permission_codes(user)
    if '__all__' in codes:
        return True
    return any(code in codes for code in permission_codes)
