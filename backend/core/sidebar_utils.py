"""
统一导航栏工具函数
用于标准化各模块的导航栏数据结构
"""
from django.urls import reverse, NoReverseMatch


def normalize_sidebar_menu(menu_data):
    """
    标准化导航栏数据结构
    
    将不同格式的菜单数据统一为标准格式：
    [
        {
            'label': '分组名称',  # 可选，如果有children则作为分组标题
            'icon': '📊',         # 可选
            'expanded': True,     # 是否展开（可选）
            'children': [         # 子菜单项列表
                {
                    'label': '菜单项',
                    'icon': '📝',
                    'url': '/path/',
                    'active': True,
                    'children': [...]  # 可选，支持三级菜单
                }
            ]
        }
    ]
    
    支持的输入格式：
    1. 分组格式：{'label': '...', 'children': [...]}
    2. 扁平格式：{'label': '...', 'url': '...', 'children': [...]}
    3. 兼容格式：{'label': '...', 'items': [...]} -> 转换为 children
    4. 兼容格式：{'collapsed': True} -> 转换为 expanded=False
    """
    if not menu_data:
        return []
    
    normalized = []
    
    for item in menu_data:
        # 处理兼容格式：items -> children
        if 'items' in item and 'children' not in item:
            item['children'] = item.pop('items')
        
        # 处理兼容格式：collapsed -> expanded
        if 'collapsed' in item:
            item['expanded'] = not item.get('collapsed', False)
            item.pop('collapsed', None)
        
        # 确保所有子菜单项都有必要的字段
        if 'children' in item and item['children']:
            normalized_children = []
            for child in item['children']:
                normalized_child = {
                    'label': child.get('label', ''),
                    'icon': child.get('icon', ''),
                    'url': child.get('url', '#'),
                    'active': child.get('active', False),
                }
                
                # 如果有子菜单，递归处理
                if 'children' in child:
                    normalized_child['children'] = normalize_sidebar_menu([child])[0].get('children', [])
                
                normalized_children.append(normalized_child)
            
            item['children'] = normalized_children
        
        # 确保expanded字段存在
        if 'children' in item and item['children']:
            if 'expanded' not in item:
                # 默认展开包含激活项的分组
                item['expanded'] = any(child.get('active') for child in item['children'])
        
        normalized.append(item)
    
    return normalized


def build_sidebar_menu_item(label, url_name=None, url=None, icon='', active=False, 
                           permission=None, permission_set=None, children=None, 
                           path_keywords=None, request_path=None):
    """
    构建标准化的导航栏菜单项
    
    Args:
        label: 菜单项标签
        url_name: URL名称（用于reverse）
        url: 直接URL（如果提供url_name则忽略）
        icon: 图标
        active: 是否激活
        permission: 所需权限
        permission_set: 用户权限集合
        children: 子菜单项列表
        path_keywords: 路径关键词列表（用于自动判断激活状态）
        request_path: 当前请求路径（用于自动判断激活状态）
    
    Returns:
        dict: 标准化的菜单项字典，如果权限不足则返回None
    """
    from backend.core.views import _permission_granted
    
    # 权限检查
    if permission and permission_set and not _permission_granted(permission, permission_set):
        return None
    
    # 获取URL
    final_url = url
    if url_name and not final_url:
        try:
            final_url = reverse(url_name)
        except NoReverseMatch:
            final_url = '#'
    
    if not final_url:
        final_url = '#'
    
    # 自动判断激活状态
    if request_path and path_keywords:
        for keyword in path_keywords:
            if keyword in request_path:
                active = True
                break
    
    menu_item = {
        'label': label,
        'icon': icon,
        'url': final_url,
        'active': active,
    }
    
    # 处理子菜单
    if children:
        normalized_children = []
        for child in children:
            if isinstance(child, dict):
                normalized_child = build_sidebar_menu_item(
                    label=child.get('label', ''),
                    url_name=child.get('url_name'),
                    url=child.get('url'),
                    icon=child.get('icon', ''),
                    active=child.get('active', False),
                    permission=child.get('permission'),
                    permission_set=permission_set,
                    children=child.get('children'),
                    path_keywords=child.get('path_keywords'),
                    request_path=request_path,
                )
                if normalized_child:
                    normalized_children.append(normalized_child)
        menu_item['children'] = normalized_children
    
    return menu_item


def build_sidebar_menu_group(label, icon='', children=None, permission=None, 
                            permission_set=None, request_path=None, expanded=None):
    """
    构建标准化的导航栏菜单分组
    
    Args:
        label: 分组标题
        icon: 分组图标（可选）
        children: 子菜单项列表
        permission: 分组所需权限
        permission_set: 用户权限集合
        request_path: 当前请求路径（用于自动判断展开状态）
        expanded: 是否展开（如果为None，则根据是否有激活项自动判断）
    
    Returns:
        dict: 标准化的菜单分组字典，如果没有可见的子项则返回None
    """
    from backend.core.views import _permission_granted
    
    # 权限检查
    if permission and permission_set and not _permission_granted(permission, permission_set):
        return None
    
    # 处理子菜单
    normalized_children = []
    if children:
        for child in children:
            if isinstance(child, dict):
                normalized_child = build_sidebar_menu_item(
                    label=child.get('label', ''),
                    url_name=child.get('url_name'),
                    url=child.get('url'),
                    icon=child.get('icon', ''),
                    active=child.get('active', False),
                    permission=child.get('permission'),
                    permission_set=permission_set,
                    children=child.get('children'),
                    path_keywords=child.get('path_keywords'),
                    request_path=request_path,
                )
                if normalized_child:
                    normalized_children.append(normalized_child)
    
    # 如果没有可见的子项，返回None
    if not normalized_children:
        return None
    
    # 自动判断展开状态
    if expanded is None:
        expanded = any(child.get('active') for child in normalized_children)
    
    return {
        'label': label,
        'icon': icon,
        'expanded': expanded,
        'children': normalized_children,
    }

