# -*- coding: utf-8 -*-
"""
Django Admin 菜单映射配置
将模型映射到对应的导航菜单项

配置规范：
1. 菜单路径格式：主菜单 > 子菜单（可选）
2. 使用通配符 '*' 表示应用下所有未明确指定的模型
3. 主菜单必须在 MAIN_MENU_ITEMS 中定义
4. 菜单URL映射在 MENU_URL_MAPPING 中定义
"""

# ==================== 菜单URL映射 ====================
# 主菜单到URL的映射，用于前端导航
# 格式：{菜单路径: URL}
MENU_URL_MAPPING = {
    '首页': '/admin/',
    '客户管理': '/admin/customer_management/',
    '合同管理': '/admin/production_management/businesscontract/',
    '商机管理': '/admin/customer_success/',
    '生产管理': '/admin/production_management/',
    '结算管理': '/admin/settlement_center/',
    '收发管理': '/admin/delivery_customer/',
    '档案管理': '/admin/archive_management/',
    '财务管理': '/admin/financial_management/',
    '人事管理': '/admin/personnel_management/',
    '行政管理': '/admin/administrative_management/',
    '计划管理': '/admin/plan_management/',
    '诉讼管理': '/admin/litigation_management/',
    '风险管理': '/admin/risk_management/',
    '资源管理': '/admin/resource_standard/',
    '报表管理': '/admin/report_management/',
    '系统设置': '/admin/system_management/',
    '权限设置': '/admin/permission_management/',
    '流程设置': '/admin/workflow_engine/',
    'API管理': '/admin/api_management/',
    '团队管理': '/admin/auth/',
}


# ==================== 菜单映射配置 ====================
# 菜单映射：{应用名: {模型名: 菜单路径}}
# 菜单路径格式：主菜单 > 子菜单（可选）
MENU_MAPPING = {
    'administrative_management': {
        'AdministrativeAffair': '行政管理 > 行政事务',
        'AffairProgressRecord': '行政管理 > 行政事务',
        'AffairStatusHistory': '行政管理 > 行政事务',
        'Announcement': '行政管理',
        'AnnouncementRead': '行政管理',
        'AssetMaintenance': '行政管理 > 固定资产管理',
        'AssetTransfer': '行政管理 > 固定资产管理',
        'ExpenseItem': '行政管理 > 差旅管理',
        'ExpenseReimbursement': '行政管理 > 差旅管理',
        'FixedAsset': '行政管理 > 固定资产管理',
        'InventoryAdjust': '行政管理 > 办公用品管理',
        'InventoryCheck': '行政管理 > 办公用品管理',
        'Meeting': '行政管理 > 会议管理',
        'MeetingRecord': '行政管理 > 会议管理',
        'MeetingResolution': '行政管理 > 会议管理',
        'MeetingRoom': '行政管理 > 会议管理',
        'MeetingRoomBooking': '行政管理 > 会议管理',
        'OfficeSupply': '行政管理 > 办公用品管理',
        'PurchaseContract': '行政管理',
        'PurchasePayment': '行政管理',
        'ReceptionExpense': '行政管理 > 接待管理',
        'ReceptionRecord': '行政管理 > 接待管理',
        'Seal': '行政管理 > 印章管理',
        'SealBorrowing': '行政管理 > 印章管理',
        'SealUsage': '行政管理 > 印章管理',
        'Supplier': '行政管理',
        'SupplyCategory': '行政管理 > 办公用品管理',
        'SupplyPurchase': '行政管理 > 办公用品管理',
        'SupplyRequest': '行政管理 > 办公用品管理',
        'TravelApplication': '行政管理 > 差旅管理',
        'Vehicle': '行政管理 > 车辆管理',
        'VehicleBooking': '行政管理 > 车辆管理',
        'VehicleMaintenance': '行政管理 > 车辆管理',
    },
    'archive_management': {
        '*': '档案管理',  # 所有模型都放在档案管理下
    },
    'customer_management': {
        'ContractFile': '合同管理',
        'ContractChange': '合同管理',
        'ContractApproval': '合同管理',
        'ContractStatusLog': '合同管理',
        '*': '客户管理',
    },
    'delivery_customer': {
        'IncomingDocument': '收发管理 > 收文管理',
        'OutgoingDocument': '收发管理 > 发文管理',
        '*': '收发管理',  # 其他模型放在收发管理下
    },
    'financial_management': {
        '*': '财务管理',
    },
    'litigation_management': {
        '*': '诉讼管理',
    },
    'permission_management': {
        '*': '权限设置',
    },
    'personnel_management': {
        '*': '人事管理',
    },
    'plan_management': {
        '*': '计划管理',
    },
    'production_management': {
        'BusinessContract': '合同管理',  # 商务合同
        'BusinessPaymentPlan': '合同管理',  # 回款计划
        'ComprehensiveAdjustmentCoefficient': '合同管理 > 综合调整系数',  # 综合调整系数
        'ServiceType': '合同管理',  # 服务类型
        'ServiceProfession': '合同管理',  # 服务专业
        'BusinessType': '合同管理',  # 项目业态
        'StructureType': '合同管理',  # 结构形式
        'DesignUnitCategory': '合同管理',  # 设计单位分类
        '*': '生产管理',
    },
    'settlement_center': {
        'SettlementMethod': '结算管理 > 结算方式',
        # 注释掉：只保留结算方式二级菜单
        # 'ServiceFeeSettlementScheme': '结算管理 > 结算方式',
        # 'ServiceFeeSegmentedRate': '结算管理 > 结算方式',
        # 'ServiceFeeJumpPointRate': '结算管理 > 结算方式',
        # 'ServiceFeeUnitCapDetail': '结算管理 > 结算方式',
        # '*': '结算管理',  # 注释掉：只保留结算方式二级菜单
    },
    'system_management': {
        '*': '系统设置',
    },
    'workflow_engine': {
        '*': '流程设置',
    },
    'api_management': {
        '*': 'API管理',
    },
    'risk_management': {
        '*': '风险管理',
    },
    'resource_standard': {
        '*': '资源管理',
    },
    'auth': {
        'User': '团队管理',
        'Group': '团队管理',
    },
}

# ==================== 主菜单项配置 ====================
# 主菜单项配置（对应左侧导航栏的一级菜单）
# 格式：{'label': 显示名称, 'icon': 图标类名, 'path': 菜单路径, 'order': 排序（可选）}
MAIN_MENU_ITEMS = [
    {'label': '首页', 'icon': 'bi-house', 'path': '首页', 'order': 0},
    {'label': '客户管理', 'icon': 'bi-people', 'path': '客户管理', 'order': 1},
    {'label': '合同管理', 'icon': 'bi-file-text', 'path': '合同管理', 'order': 2},
    {'label': '商机管理', 'icon': 'bi-briefcase', 'path': '商机管理', 'order': 3},
    {'label': '生产管理', 'icon': 'bi-gear', 'path': '生产管理', 'order': 4},
    {'label': '结算管理', 'icon': 'bi-cash-coin', 'path': '结算管理', 'order': 5},
    {'label': '收发管理', 'icon': 'bi-box-seam', 'path': '收发管理', 'order': 7},
    {'label': '档案管理', 'icon': 'bi-folder', 'path': '档案管理', 'order': 8},
    {'label': '财务管理', 'icon': 'bi-wallet2', 'path': '财务管理', 'order': 9},
    {'label': '人事管理', 'icon': 'bi-person', 'path': '人事管理', 'order': 10},
    {'label': '行政管理', 'icon': 'bi-building', 'path': '行政管理', 'order': 11},
    {'label': '计划管理', 'icon': 'bi-calendar3', 'path': '计划管理', 'order': 12},
    {'label': '诉讼管理', 'icon': 'bi-shield-exclamation', 'path': '诉讼管理', 'order': 13},
    {'label': '风险管理', 'icon': 'bi-exclamation-triangle', 'path': '风险管理', 'order': 14},
    {'label': '资源管理', 'icon': 'bi-folder2', 'path': '资源管理', 'order': 15},
    {'label': '报表管理', 'icon': 'bi-graph-up', 'path': '报表管理', 'order': 16},
    {'label': '系统设置', 'icon': 'bi-gear-fill', 'path': '系统设置', 'order': 17},
    {'label': '权限设置', 'icon': 'bi-shield-lock', 'path': '权限设置', 'order': 18},
    {'label': '流程设置', 'icon': 'bi-diagram-3', 'path': '流程设置', 'order': 19},
    {'label': 'API管理', 'icon': 'bi-code-slash', 'path': 'API管理', 'order': 20},
    {'label': '团队管理', 'icon': 'bi-people-fill', 'path': '团队管理', 'order': 21},
]

# 按汉语拼音排序（首页固定第一位）
try:
    from pypinyin import lazy_pinyin, Style
    
    def get_pinyin_sort_key(item):
        """获取拼音排序键，首页固定第一位"""
        label = item.get('label', '')
        if label == '首页':
            return ('0', '')  # 首页排在最前面
        # 获取拼音首字母并转换为字符串
        pinyin_list = lazy_pinyin(label, style=Style.FIRST_LETTER)
        pinyin_str = ''.join(pinyin_list).lower()
        return ('1', pinyin_str)  # 其他菜单按拼音排序
    
    MAIN_MENU_ITEMS.sort(key=get_pinyin_sort_key)
except ImportError:
    # 如果没有pypinyin库，使用order排序（首页固定第一位）
    def get_order_sort_key(item):
        """获取order排序键，首页固定第一位"""
        if item.get('label') == '首页':
            return (0, 0)
        return (1, item.get('order', 999))
    
    MAIN_MENU_ITEMS.sort(key=get_order_sort_key)


# ==================== 辅助函数 ====================

def get_menu_url(menu_path):
    """
    获取菜单对应的URL
    
    Args:
        menu_path: 菜单路径（主菜单或主菜单 > 子菜单）
    
    Returns:
        str: URL地址，如果未找到则返回None
    """
    # 提取主菜单名称
    main_menu = menu_path.split(' > ')[0]
    return MENU_URL_MAPPING.get(main_menu)


def get_menu_path_for_model(app_label, model_name):
    """
    获取模型对应的菜单路径
    
    Args:
        app_label: 应用标签
        model_name: 模型名称
    
    Returns:
        str: 菜单路径，格式如 "行政管理 > 办公用品管理"，如果未找到匹配则返回 None
    """
    app_mapping = MENU_MAPPING.get(app_label, {})
    
    # 先查找精确匹配
    if model_name in app_mapping:
        return app_mapping[model_name]
    
    # 查找通配符匹配
    if '*' in app_mapping:
        return app_mapping['*']
    
    # 对于 settlement_center，如果没有明确配置，返回 None（不显示）
    if app_label == 'settlement_center':
        return None
    
    # 默认返回应用标签
    return app_label


def organize_models_by_menu(app_list):
    """
    将app_list中的模型按菜单路径组织
    
    Args:
        app_list: Django Admin的app_list数据结构
    
    Returns:
        dict: {菜单路径: [模型列表]}
    """
    menu_dict = {}
    
    for app in app_list:
        app_label = app.get('app_label', '')
        models = app.get('models', [])
        
        for model in models:
            model_name = model.get('object_name', '')
            menu_path = get_menu_path_for_model(app_label, model_name)
            
            # 如果菜单路径为 None，跳过该模型（不显示）
            if menu_path is None:
                continue
            
            if menu_path not in menu_dict:
                menu_dict[menu_path] = []
            
            menu_dict[menu_path].append({
                'name': model.get('name', model_name),
                'admin_url': model.get('admin_url', '#'),
                'object_name': model_name,
                'app_label': app_label,
            })
    
    return menu_dict


def get_main_menu_for_app(app_label):
    """
    获取应用对应的主菜单名称
    
    Args:
        app_label: 应用标签
    
    Returns:
        str: 主菜单名称，如果找不到则返回None
    """
    app_mapping = MENU_MAPPING.get(app_label, {})
    if '*' in app_mapping:
        # 从通配符匹配中提取主菜单名称
        menu_path = app_mapping['*']
        return menu_path.split(' > ')[0]
    
    # 如果有具体模型映射，从第一个模型映射中提取主菜单名称
    for model_name, menu_path in app_mapping.items():
        if model_name != '*':
            return menu_path.split(' > ')[0]
    
    return None


def build_menu_structure(app_list, filter_app_label=None):
    """
    构建菜单结构，将模型组织到对应的菜单项下
    
    Args:
        app_list: Django Admin的app_list数据结构
        filter_app_label: 可选，如果提供则只显示该应用的菜单项
    
    Returns:
        dict: 菜单结构 {主菜单: {子菜单: [模型列表]}}
    """
    menu_dict = organize_models_by_menu(app_list)
    
    # 如果指定了过滤应用，只保留该应用的菜单项
    if filter_app_label:
        target_main_menu = get_main_menu_for_app(filter_app_label)
        if target_main_menu:
            # 只保留目标主菜单的菜单项
            filtered_menu_dict = {}
            for menu_path, models in menu_dict.items():
                main_menu = menu_path.split(' > ')[0]
                if main_menu == target_main_menu:
                    filtered_menu_dict[menu_path] = models
            menu_dict = filtered_menu_dict
    
    # 构建菜单结构
    menu_structure = {}
    
    for menu_path, models in menu_dict.items():
        parts = menu_path.split(' > ')
        main_menu = parts[0]
        sub_menu = parts[1] if len(parts) > 1 else None
        
        if main_menu not in menu_structure:
            menu_structure[main_menu] = {}
        
        if sub_menu:
            if sub_menu not in menu_structure[main_menu]:
                menu_structure[main_menu][sub_menu] = []
            menu_structure[main_menu][sub_menu].extend(models)
        else:
            # 如果没有子菜单，使用"默认"作为键
            if '默认' not in menu_structure[main_menu]:
                menu_structure[main_menu]['默认'] = []
            menu_structure[main_menu]['默认'].extend(models)
    
    # 对子菜单和模型按拼音排序
    try:
        from pypinyin import lazy_pinyin, Style
        
        def sort_by_pinyin(items, key_func):
            """按拼音排序"""
            return sorted(items, key=lambda x: ''.join(lazy_pinyin(key_func(x), style=Style.FIRST_LETTER)).lower())
        
        # 对每个主菜单的子菜单按拼音排序
        for main_menu in menu_structure:
            # 对子菜单字典的键按拼音排序
            sub_menus = list(menu_structure[main_menu].keys())
            sorted_sub_menus = sort_by_pinyin(sub_menus, lambda x: x)
            
            # 重新构建排序后的子菜单字典
            sorted_sub_menu_dict = {}
            for sub_menu in sorted_sub_menus:
                sorted_sub_menu_dict[sub_menu] = menu_structure[main_menu][sub_menu]
                # 对每个子菜单下的模型按拼音排序
                sorted_sub_menu_dict[sub_menu] = sort_by_pinyin(
                    sorted_sub_menu_dict[sub_menu],
                    lambda x: x.get('name', '')
                )
            menu_structure[main_menu] = sorted_sub_menu_dict
    except ImportError:
        # 如果没有pypinyin库，保持原有顺序
        pass
    
    # 确保 MAIN_MENU_ITEMS 中定义的所有菜单项都会显示，即使没有模型
    for menu_item in MAIN_MENU_ITEMS:
        menu_path = menu_item.get('path', '')
        if menu_path and menu_path not in menu_structure:
            menu_structure[menu_path] = {'默认': []}
    
    # 按照 MAIN_MENU_ITEMS 的顺序重新构建有序的菜单结构
    # 使用 OrderedDict 或者按照 MAIN_MENU_ITEMS 的顺序返回
    from collections import OrderedDict
    ordered_menu_structure = OrderedDict()
    
    # 按照 MAIN_MENU_ITEMS 的顺序添加菜单项
    for menu_item in MAIN_MENU_ITEMS:
        menu_path = menu_item.get('path', '')
        if menu_path and menu_path in menu_structure:
            ordered_menu_structure[menu_path] = menu_structure[menu_path]
    
    # 添加其他不在 MAIN_MENU_ITEMS 中的菜单项（如果有）
    for menu_path, sub_menus in menu_structure.items():
        if menu_path not in ordered_menu_structure:
            ordered_menu_structure[menu_path] = sub_menus
    
    return ordered_menu_structure


# ==================== 菜单验证函数 ====================

def validate_menu_config():
    """
    验证菜单配置的完整性
    检查：
    1. 所有主菜单项都有对应的URL映射
    2. 菜单路径格式正确
    3. 没有重复的菜单路径
    
    Returns:
        tuple: (is_valid, errors)
    """
    errors = []
    
    # 检查主菜单项是否都有URL映射
    for menu_item in MAIN_MENU_ITEMS:
        menu_path = menu_item.get('path', '')
        if menu_path and menu_path not in MENU_URL_MAPPING:
            errors.append(f'主菜单 "{menu_path}" 没有对应的URL映射')
    
    # 检查URL映射是否都有对应的主菜单项
    for menu_path in MENU_URL_MAPPING.keys():
        if not any(item.get('path') == menu_path for item in MAIN_MENU_ITEMS):
            errors.append(f'URL映射 "{menu_path}" 没有对应的主菜单项')
    
    # 检查菜单路径格式
    for app_label, models in MENU_MAPPING.items():
        for model_name, menu_path in models.items():
            if ' > ' in menu_path:
                parts = menu_path.split(' > ')
                if len(parts) > 2:
                    errors.append(f'菜单路径格式错误（最多只能有一个子菜单）: {app_label}.{model_name} -> {menu_path}')
    
    return len(errors) == 0, errors

