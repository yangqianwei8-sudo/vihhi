"""
工作流引擎工具函数
"""
from django.urls.resolvers import URLResolver, URLPattern
from django.urls import get_resolver, reverse, NoReverseMatch


def scan_create_urls_for_category(category='计划管理'):
    """
    扫描指定分类下的所有create URL
    
    参数:
        category: 流程分类名称
    
    返回:
        list: [(模型名称, 显示名称, URL路径), ...]
    """
    # URL路径前缀到流程分类的映射
    URL_PREFIX_TO_CATEGORY = {
        '/plan/': '计划管理',
        '/business/': '客户管理',
        '/delivery/': '交付客户',
        '/litigation/': '诉讼管理',
        '/production/': '生产管理',
        '/financial/': '财务管理',
        '/personnel/': '人事管理',
        '/administrative/': '行政管理',
        '/risk/': '风险管理',
        '/archive/': '档案管理',
    }
    
    # 命名空间到流程分类的映射
    NAMESPACE_TO_CATEGORY = {
        'plan_pages': '计划管理',
        'business_pages': '客户管理',
        'delivery_pages': '交付客户',
        'litigation_pages': '诉讼管理',
        'production_pages': '生产管理',
        'finance_pages': '财务管理',
        'personnel_pages': '人事管理',
        'admin_pages': '行政管理',
        'risk_management': '风险管理',
        'archive_management': '档案管理',
    }
    
    create_urls = []
    resolver = get_resolver()
    
    def extract_urls(url_patterns, namespace='', prefix='', current_category=None):
        """递归提取所有URL模式"""
        for pattern in url_patterns:
            if isinstance(pattern, URLResolver):
                # 递归处理嵌套的URL配置
                new_namespace = pattern.namespace or namespace
                new_prefix = prefix + str(pattern.pattern)
                
                # 确定当前分类
                new_category = current_category
                if not new_category:
                    # 根据命名空间判断
                    for ns_key, cat in NAMESPACE_TO_CATEGORY.items():
                        if new_namespace and ns_key in new_namespace:
                            new_category = cat
                            break
                
                # 根据URL前缀判断
                if not new_category:
                    for prefix_key, cat in URL_PREFIX_TO_CATEGORY.items():
                        if new_prefix.startswith(prefix_key) or prefix_key in new_prefix:
                            new_category = cat
                            break
                
                extract_urls(pattern.url_patterns, new_namespace, new_prefix, new_category)
            elif isinstance(pattern, URLPattern):
                # 检查URL路径是否包含'create'
                url_pattern = str(pattern.pattern)
                if 'create' in url_pattern.lower():
                    try:
                        # 尝试获取URL名称
                        url_name = pattern.name
                        if not url_name:
                            continue
                        
                        # 构建完整URL名称
                        if namespace:
                            full_url_name = f'{namespace}:{url_name}'
                        else:
                            full_url_name = url_name
                        
                        # 确定分类
                        pattern_category = current_category
                        
                        # 首先根据命名空间判断
                        if not pattern_category:
                            for ns_key, cat in NAMESPACE_TO_CATEGORY.items():
                                if namespace and ns_key in namespace:
                                    pattern_category = cat
                                    break
                        
                        # 如果命名空间判断失败，根据URL路径前缀判断
                        if not pattern_category:
                            full_path = prefix + url_pattern
                            for prefix_key, cat in URL_PREFIX_TO_CATEGORY.items():
                                if prefix_key in full_path:
                                    pattern_category = cat
                                    break
                        
                        # 如果还是无法确定，根据URL路径中的关键词判断（更严格的匹配）
                        if not pattern_category:
                            full_path = prefix + url_pattern
                            # 使用更严格的路径前缀匹配
                            if '/plan/' in full_path or full_path.startswith('/plan'):
                                pattern_category = '计划管理'
                            elif '/business/' in full_path or full_path.startswith('/business'):
                                pattern_category = '客户管理'
                            elif '/delivery/' in full_path or full_path.startswith('/delivery'):
                                pattern_category = '交付客户'
                            elif '/litigation/' in full_path or full_path.startswith('/litigation'):
                                pattern_category = '诉讼管理'
                            elif '/production/' in full_path or full_path.startswith('/production'):
                                pattern_category = '生产管理'
                            elif '/financial/' in full_path or full_path.startswith('/financial') or '/finance/' in full_path:
                                pattern_category = '财务管理'
                            elif '/personnel/' in full_path or full_path.startswith('/personnel'):
                                pattern_category = '人事管理'
                            elif '/administrative/' in full_path or full_path.startswith('/administrative'):
                                pattern_category = '行政管理'
                            elif '/risk/' in full_path or full_path.startswith('/risk'):
                                pattern_category = '风险管理'
                            elif '/archive/' in full_path or full_path.startswith('/archive'):
                                pattern_category = '档案管理'
                            # 注意：settlement模块不应该被归类到计划管理
                            elif '/settlement/' in full_path or full_path.startswith('/settlement'):
                                # settlement模块应该有自己的分类，这里跳过
                                continue
                        
                        # 只处理指定分类的URL
                        if pattern_category != category:
                            continue
                        
                        # 尝试构建完整URL路径
                        try:
                            # 对于需要参数的URL，尝试使用示例参数
                            if '<int:' in url_pattern or '<path:' in url_pattern or '<slug:' in url_pattern:
                                # 对于需要参数的URL，先尝试不使用参数
                                # 如果失败，则构建基础路径
                                try:
                                    url_path = reverse(full_url_name, args=[1])  # 尝试使用示例参数
                                except:
                                    # 构建基础路径，保留参数占位符但用示例值替换
                                    base_path = prefix + url_pattern
                                    base_path = base_path.replace('<int:parent_goal_id>', '1')
                                    base_path = base_path.replace('<int:', '').replace('<path:', '').replace('<slug:', '').replace('<uuid:', '').replace('<str:', '').replace('>', '')
                                    base_path = base_path.replace('//', '/')
                                    if not base_path.startswith('/'):
                                        base_path = '/' + base_path
                                    url_path = base_path
                            else:
                                url_path = reverse(full_url_name)
                        except NoReverseMatch:
                            # 如果reverse失败，尝试构建URL路径
                            url_path = prefix + url_pattern
                            # 清理URL路径中的参数占位符，但保留有意义的参数名
                            url_path = url_path.replace('<int:parent_goal_id>', '1')  # 特殊处理
                            url_path = url_path.replace('<int:', '').replace('<path:', '').replace('<slug:', '').replace('<uuid:', '').replace('<str:', '').replace('>', '')
                            # 移除重复的斜杠
                            url_path = url_path.replace('//', '/')
                            if not url_path.startswith('/'):
                                url_path = '/' + url_path
                        
                        # 生成模型名称（从URL名称提取）
                        model_name = url_name.replace('_create', '').replace('create', '').replace('_', '')
                        if not model_name:
                            # 从URL路径提取
                            path_parts = url_path.strip('/').split('/')
                            if path_parts:
                                model_name = path_parts[-1] if path_parts[-1] and path_parts[-1] != 'create' else (path_parts[-2] if len(path_parts) > 1 else 'unknown')
                        
                        # 生成显示名称（从URL名称提取，更友好）
                        # 处理特殊命名（中文显示名称映射）- 先检查完整名称
                        display_name_mapping = {
                            'create_child_goal': '创建子目标',
                            'plan_collaboration_create': '协作计划',
                            'plan_adjustment_create': '计划调整',
                            'strategic_goal_create': '战略目标',
                            'plan_create': '工作计划',
                        }
                        
                        if url_name in display_name_mapping:
                            display_name = display_name_mapping[url_name]
                        else:
                            # 移除create相关后缀
                            display_name = url_name.replace('_create', '').replace('create', '')
                            # 将下划线分隔的单词转换为标题格式
                            words = [word.capitalize() for word in display_name.split('_') if word]
                            display_name = ' '.join(words)
                        
                        if not display_name or display_name.strip() == '':
                            display_name = model_name
                        
                        # 避免重复
                        existing_urls = [item[2] for item in create_urls]
                        if url_path not in existing_urls:
                            create_urls.append((model_name, display_name, url_path))
                    except Exception as e:
                        # 忽略无法处理的URL
                        import logging
                        logger = logging.getLogger(__name__)
                        logger.debug(f'处理URL时出错: {pattern.pattern}, 错误: {str(e)}')
                        continue
    
    # 提取所有URL
    extract_urls(resolver.url_patterns)
    
    # 按显示名称排序
    create_urls.sort(key=lambda x: x[1])
    
    return create_urls


def get_all_create_urls():
    """
    动态获取系统中所有包含'create'的URL
    返回格式: {分类: [(模型名称, 显示名称, URL路径), ...]}
    """
    categories = [
        '计划管理', '客户管理', '交付客户', '诉讼管理', '生产管理',
        '财务管理', '人事管理', '行政管理', '风险管理', '档案管理'
    ]
    
    result = {}
    for category in categories:
        result[category] = scan_create_urls_for_category(category)
    
    return result

