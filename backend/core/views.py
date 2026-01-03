from datetime import timedelta

from django.shortcuts import render, redirect
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from django.contrib.auth import login, logout, authenticate
from django.contrib import messages
from django.db.models import Sum, Q
from django.utils import timezone
from django.urls import reverse, NoReverseMatch

# 注意：Project, ProjectTask 等模型改为延迟导入，避免在数据库表不存在时导致模块加载失败
# from backend.apps.project_center.models import Project, ProjectMilestone, ProjectTeamNotification, ProjectTask
from backend.apps.system_management.services import get_user_permission_codes


def _permission_granted(required_code, user_permissions: set) -> bool:
    if not required_code:
        return True
    # 检查是否有所有权限
    if '__all__' in user_permissions:
        return True
    if required_code in user_permissions:
        return True
    if isinstance(required_code, str) and required_code.endswith('.view_assigned'):
        return required_code.replace('view_assigned', 'view_all') in user_permissions
    return False


def _build_unified_sidebar_nav(menu_structure, permission_set, active_id=None, permission_check_func=None):
    """
    统一的左侧栏菜单构建函数
    
    标准格式：
    menu_structure = [
        {
            'id': 'module_home',
            'label': '模块首页',
            'icon': '🏠',
            'url_name': 'module:home',
            'permission': 'module.view',
        },
        {
            'id': 'group_id',
            'label': '分组标题',
            'icon': '📊',
            'permission': 'module.view',
            'children': [
                {
                    'id': 'child_id',
                    'label': '子菜单项',
                    'icon': '📋',
                    'url_name': 'module:child',
                    'permission': 'module.view',
                },
            ]
        },
    ]
    
    Args:
        menu_structure: 菜单结构定义（列表）
        permission_set: 用户权限集合
        active_id: 当前激活的菜单项ID
        permission_check_func: 可选的权限检查函数，如果提供则使用它，否则使用默认的 _permission_granted
    
    Returns:
        list: 菜单项列表，格式统一为：
            {
                'id': str,
                'label': str,
                'icon': str,
                'url': str,
                'active': bool,
                'expanded': bool,  # 仅分组菜单有
                'children': list,   # 仅分组菜单有
            }
    """
    from django.urls import reverse, NoReverseMatch
    import logging
    logger = logging.getLogger(__name__)
    
    # 使用提供的权限检查函数，或默认使用 _permission_granted
    check_permission = permission_check_func if permission_check_func else _permission_granted
    
    menu = []
    
    for menu_item in menu_structure:
        # 检查父菜单权限
        permission = menu_item.get('permission')
        if permission and not check_permission(permission, permission_set):
            continue
        
        # 如果是独立菜单项（有url_name但没有children）
        if menu_item.get('url_name') and not menu_item.get('children'):
            try:
                url = reverse(menu_item['url_name'])
                is_active = menu_item.get('id') == active_id
                menu.append({
                    'id': menu_item.get('id'),
                    'label': menu_item.get('label'),
                    'icon': menu_item.get('icon', ''),
                    'url': url,
                    'active': is_active,
                })
            except NoReverseMatch:
                logger.warning(f"URL pattern '{menu_item['url_name']}' not found for sidebar menu.")
                continue
        
        # 如果是分组菜单（有children）
        elif menu_item.get('children'):
            children = []
            for child in menu_item.get('children', []):
                # 检查子菜单权限
                child_permission = child.get('permission')
                if child_permission and not check_permission(child_permission, permission_set):
                    continue
                
                # 获取URL
                url_name = child.get('url_name')
                url = '#'
                if url_name:
                    try:
                        url = reverse(url_name)
                        # 如果提供了 url_params，追加到URL
                        url_params = child.get('url_params', '')
                        if url_params:
                            url = url + url_params
                    except NoReverseMatch:
                        logger.warning(f"URL pattern '{url_name}' not found for sidebar menu.")
                        url = '#'
                
                # 判断是否激活
                is_active = child.get('id') == active_id
                
                children.append({
                    'id': child.get('id'),
                    'label': child.get('label'),
                    'icon': child.get('icon', ''),
                    'url': url,
                    'active': is_active,
                })
            
            # 如果父菜单没有可见的子菜单，跳过
            if not children:
                continue
            
            # 判断父菜单是否激活（任意子菜单激活则父菜单激活，或父菜单ID匹配active_id）
            parent_id = menu_item.get('id')
            group_active = (parent_id == active_id) or any(child.get('id') == active_id for child in menu_item.get('children', []))
            
            # 判断是否有激活的子菜单
            has_active_child = any(child.get('id') == active_id for child in children)
            
            # 获取父菜单的URL（如果有）
            parent_url = '#'
            parent_url_name = menu_item.get('url_name')
            if parent_url_name:
                try:
                    parent_url = reverse(parent_url_name)
                    # 如果提供了 url_params，追加到URL
                    parent_url_params = menu_item.get('url_params', '')
                    if parent_url_params:
                        parent_url = parent_url + parent_url_params
                except NoReverseMatch:
                    logger.warning(f"URL pattern '{parent_url_name}' not found for parent menu item.")
                    parent_url = '#'
            
            menu.append({
                'id': parent_id,
                'label': menu_item.get('label'),
                'icon': menu_item.get('icon', ''),
                'url': parent_url,
                'active': group_active,
                'expanded': has_active_child or group_active,  # 有激活的子菜单或父菜单激活时展开
                'children': children,
            })
    
    return menu

HOME_ACTION_DEFINITIONS = [
    {
        "id": "project_create",
        "label": "新建生产启动",
        "icon": "➕",
        "url_name": "production_pages:project_create",
        "permission": "production_management.create",
    },
]

# 菜单结构：直接对应home页左侧菜单，取消所有"中心"概念
# 注意：所有模块现在都有独立的首页（Dashboard），列表页已移至侧边栏菜单中
HOME_NAV_STRUCTURE = [
    # 按数据库模块定义顺序排列，确保与数据库一致
    {'label': '客户管理', 'icon': '👥', 'url_name': 'business_pages:customer_management_home', 'permission': 'customer_management.client.view'},  # 指向 /business/home/
    {'label': '商机管理', 'icon': '💼', 'url_name': 'business_pages:opportunity_management_home', 'permission': 'customer_success.opportunity.view'},  # 改为首页
    {'label': '合同管理', 'icon': '📄', 'url_name': 'business_pages:contract_management_home', 'permission': 'customer_management.contract.view'},  # 改为首页
    {'label': '产值管理', 'icon': '📊', 'url_name': 'settlement_pages:output_value_home', 'permission': 'settlement_center.view_output_value'},
    {'label': '项目结算', 'icon': '💳', 'url_name': 'settlement_pages:project_settlement_home', 'permission': 'settlement_center.view_project_settlement'},
    {'label': '回款管理', 'icon': '💵', 'url_name': 'settlement_pages:payment_management_home', 'permission': 'settlement_center.view_payment'},
    {'label': '生产管理', 'icon': '🏗️', 'url_name': 'production_pages:production_management_home', 'permission': 'production_management.view_assigned'},  # 改为首页
    {'label': '资源管理', 'icon': '🗂️', 'url_name': 'resource_standard_pages:resource_standard_home', 'permission': 'resource_center.view'},  # 改为首页
    {'label': '档案管理', 'icon': '📁', 'url_name': 'archive_management:archive_management_home', 'permission': 'archive_management.view'},  # 首页会跳转到项目归档列表
    {'label': '收文管理', 'icon': '📥', 'url_name': 'delivery_pages:incoming_document_home', 'permission': 'delivery_center.view'},  # 收文管理首页
    {'label': '发文管理', 'icon': '📤', 'url_name': 'delivery_pages:outgoing_document_home', 'permission': 'delivery_center.view'},  # 发文管理
    {'label': '计划管理', 'icon': '📅', 'url_name': 'plan_pages:plan_management_home', 'permission': 'plan_management.view'},  # 改为首页
    {'label': '诉讼管理', 'icon': '⚖️', 'url_name': 'litigation_pages:litigation_home', 'permission': 'litigation_management.view'},
    {'label': '风险管理', 'icon': '⚠️', 'url_name': 'risk_management:risk_management_home', 'permission': 'risk_management.view'},  # 改为首页
    {'label': '财务管理', 'icon': '💵', 'url_name': 'finance_pages:financial_home', 'permission': 'financial_management.view'},
    {'label': '人事管理', 'icon': '👤', 'url_name': 'personnel_pages:personnel_home', 'permission': 'personnel_management.view'},
    {'label': '行政管理', 'icon': '🏢', 'url_name': 'admin_pages:administrative_home', 'permission': 'administrative_management.view'},
    {'label': '系统管理', 'icon': '⚙️', 'url_name': 'system_pages:system_management_home', 'permission': 'system_management.view'},  # 改为首页
    {'label': '流程引擎', 'icon': '🔄', 'url_name': 'workflow_engine:workflow_engine_home', 'permission': 'workflow_engine.view'},  # 流程引擎首页
    # 注意：权限管理仅保留在Django Admin后台管理中，不添加到前端导航栏
]


def _build_full_top_nav(permission_set, user=None):
    """构建完整的顶部导航菜单
    
    Args:
        permission_set: 用户权限集合
        user: 当前用户对象（可选）
    
    Returns:
        list: 导航菜单项列表
    """
    nav = []
    for item in HOME_NAV_STRUCTURE:
        # 检查权限
        if item.get('permission'):
            if not _permission_granted(item['permission'], permission_set):
                continue
        
        # 构建URL
        url = '#'
        if item.get('url_name'):
            try:
                url = reverse(item['url_name'])
            except NoReverseMatch as e:
                # 如果URL反向解析失败，记录警告但继续处理
                import logging
                logger = logging.getLogger(__name__)
                logger.warning(f'URL反向解析失败: {item["url_name"]} - {e}')
                url = item.get('url', '#')
        else:
            url = item.get('url', '#')
        
        nav.append({
            'label': item['label'],
            'icon': item.get('icon', ''),
            'url': url,
        })
    
    return nav


def _serialize_task_for_home(task):
    """序列化任务对象为首页显示格式"""
    try:
        project = getattr(task, 'project', None)
        project_number = getattr(project, 'project_number', '') if project else ''
        project_name = getattr(project, 'name', '关联项目') if project else '关联项目'
        
        # 根据任务类型设置跳转URL
        url = '#'
        if project:
            try:
                task_type = getattr(task, 'task_type', None)
                if task_type == 'project_complete_info':
                    # 完善项目信息 -> 跳转到项目信息完善页面
                    url = reverse('production_pages:project_complete', args=[project.id])
                elif task_type == 'configure_team':
                    # 配置项目团队 -> 跳转到团队配置页面
                    url = reverse('production_pages:project_team', args=[project.id])
                else:
                    # 其他任务 -> 跳转到项目详情页面
                    url = reverse('production_pages:project_detail', args=[project.id])
            except (NoReverseMatch, AttributeError):
                url = '#'
        
        return {
            'id': getattr(task, 'id', None),
            'title': getattr(task, 'title', ''),
            'project_name': project_name,
            'project_number': project_number,
            'status': getattr(task, 'status', 'pending'),
            'status_label': getattr(task, 'get_status_display', lambda: '')() if hasattr(task, 'get_status_display') else '',
            'due_time': getattr(task, 'due_time', None),
            'completed_time': getattr(task, 'completed_time', None),
            'description': getattr(task, 'description', ''),
            'url': url,
        }
    except Exception as e:
        import logging
        logger = logging.getLogger(__name__)
        logger.warning(f'序列化任务失败: {e}', exc_info=True)
        # 返回一个基本的任务信息
        return {
            'id': getattr(task, 'id', None),
            'title': getattr(task, 'title', '未知任务'),
            'project_name': '未知项目',
            'project_number': '',
            'status': 'pending',
            'status_label': '',
            'due_time': None,
            'completed_time': None,
            'description': '',
            'url': '#',
        }


# ============================================
# home 视图函数 - 系统总工作台首页
# ============================================
from django.contrib.auth.decorators import login_required

@login_required
def home(request):
    """系统总工作台首页"""
    # 如果未登录，重定向到登录页
    if not request.user.is_authenticated:
        return redirect('login')
    
    user = request.user
    
    # 构建上下文，传递用户信息给模板
    context = {
        'user': user,
        'username': user.get_full_name() or user.username,
        'user_role': '超级管理员' if user.is_superuser else '普通用户',
    }
    
    # 渲染新的总工作台首页模板
    return render(request, 'home.html', context)


def login_view(request):
    """登录页面 - 返回前端Vue登录页面，统一使用Vue登录"""
    # 统一使用Vue登录页面，Django模板登录已暂时注释
    # 无论是否登录，都返回前端页面，由前端路由处理登录逻辑
    import os
    from django.conf import settings
    from django.http import HttpResponse

    # 前端构建文件路径
    frontend_dist_path = os.path.join(settings.BASE_DIR.parent, 'frontend', 'dist', 'index.html')

    if os.path.exists(frontend_dist_path):
        # 如果前端构建文件存在，返回前端页面
        with open(frontend_dist_path, 'r', encoding='utf-8') as f:
            return HttpResponse(f.read(), content_type='text/html')
    else:
        # 如果前端构建文件不存在，返回一个简单的提示页面
        return HttpResponse('''
        <!DOCTYPE html>
        <html>
        <head>
            <title>维海科技信息化管理平台 - 登录</title>
            <meta charset="UTF-8">
        </head>
        <body>
            <h1>维海科技信息化管理平台</h1>
            <p>前端页面未找到，请先构建前端应用。</p>
            <p><a href="/admin/login/">访问后台管理登录</a></p>
        </body>
        </html>
        ''', content_type='text/html')

    # ========== Django模板登录（已暂时注释）==========
    # if request.user.is_authenticated:
    #     # 已登录用户，根据next参数决定重定向目标
    #     next_url = request.GET.get('next', '')
    #     if next_url and ('admin' in next_url or next_url.startswith('/admin')):
    #         return redirect('admin:index')
    #     else:
    #         return redirect('home')  # 重定向到前端首页
    #
    # if request.method == 'POST':
    #     username = request.POST.get('username')
    #     password = request.POST.get('password')
    #
    #     if username and password:
    #         user = authenticate(request, username=username, password=password)
    #         if user:
    #             if user.is_active:
    #                 login(request, user)
    #                 if not user.profile_completed:
    #                     return redirect('complete_profile')
    #                 
    #                 # 根据next参数决定重定向目标
    #                 next_url = request.GET.get('next', 'home')
    #                 if next_url and ('admin' in next_url or next_url.startswith('/admin')):
    #                     # 如果next包含admin，重定向到后台管理
    #                     return redirect('admin:index')
    #                 else:
    #                     # 否则重定向到前端首页
    #                     return redirect('home')
    #             else:
    #                 messages.error(request, '用户账户已被禁用')
    #         else:
    #             messages.error(request, '用户名或密码错误')
    #     else:
    #         messages.error(request, '请输入用户名和密码')
    #
    # return render(request, 'login.html')


def logout_view(request):
    """登出页面"""
    logout(request)
    messages.success(request, '您已成功退出登录')
    return redirect('login')


@csrf_exempt
def health_check(request):
    """健康检查端点"""
    return JsonResponse({
        'status': 'healthy',
        'service': '维海科技信息化管理平台',
        'version': '1.0.0',
        'timestamp': '2025-11-06T14:01:28Z'
    })


def favicon_view(request):
    """Favicon视图 - 安全处理，避免连接重置"""
    from django.http import HttpResponse, HttpResponseNotFound
    from django.conf import settings
    import os
    import logging
    
    logger = logging.getLogger(__name__)
    
    # 确保返回有效的响应，避免连接重置
    try:
        # 尝试多个可能的favicon路径
        possible_paths = []
        
        # 1. STATIC_ROOT
        try:
            if hasattr(settings, 'STATIC_ROOT') and settings.STATIC_ROOT:
                static_root_path = os.path.join(str(settings.STATIC_ROOT), 'favicon.ico')
                possible_paths.append(static_root_path)
        except Exception as e:
            logger.debug(f'无法获取STATIC_ROOT路径: {e}')
        
        # 2. STATICFILES_DIRS
        try:
            if hasattr(settings, 'STATICFILES_DIRS') and settings.STATICFILES_DIRS:
                for static_dir in settings.STATICFILES_DIRS:
                    try:
                        static_dir_path = os.path.join(str(static_dir), 'favicon.ico')
                        possible_paths.append(static_dir_path)
                    except Exception as e:
                        logger.debug(f'无法构建STATICFILES_DIRS路径: {e}')
                        continue
        except Exception as e:
            logger.debug(f'无法获取STATICFILES_DIRS: {e}')
        
        # 3. 前端构建目录
        try:
            if hasattr(settings, 'BASE_DIR'):
                base_dir = settings.BASE_DIR
                if hasattr(base_dir, 'parent'):
                    frontend_dist = os.path.join(str(base_dir.parent), 'frontend', 'dist', 'favicon.ico')
                    if os.path.exists(frontend_dist):
                        possible_paths.append(frontend_dist)
        except Exception as e:
            logger.debug(f'无法获取前端构建目录: {e}')
        
        # 4. 前端public目录
        try:
            if hasattr(settings, 'BASE_DIR'):
                base_dir = settings.BASE_DIR
                if hasattr(base_dir, 'parent'):
                    frontend_public = os.path.join(str(base_dir.parent), 'frontend', 'public', 'favicon.ico')
                    if os.path.exists(frontend_public):
                        possible_paths.append(frontend_public)
        except Exception as e:
            logger.debug(f'无法获取前端public目录: {e}')
        
        # 尝试每个路径
        for favicon_path in possible_paths:
            try:
                if os.path.exists(favicon_path):
                    # 检查文件大小，如果是空文件则跳过
                    file_size = os.path.getsize(favicon_path)
                    if file_size == 0:
                        logger.debug(f'favicon文件为空，跳过: {favicon_path}')
                        continue
                    
                    with open(favicon_path, 'rb') as f:
                        favicon_data = f.read()
                        # 再次检查读取的数据是否为空
                        if len(favicon_data) > 0:
                            response = HttpResponse(favicon_data, content_type='image/x-icon')
                            response['Cache-Control'] = 'public, max-age=86400'  # 缓存1天
                            return response
                        else:
                            logger.debug(f'读取的favicon数据为空: {favicon_path}')
                            continue
            except Exception as e:
                logger.debug(f'读取favicon文件失败 {favicon_path}: {e}')
                continue
        
        # 如果所有路径都失败，尝试从static目录直接读取
        try:
            from django.contrib.staticfiles import finders
            favicon_path = finders.find('favicon.ico')
            if favicon_path:
                with open(favicon_path, 'rb') as f:
                    favicon_data = f.read()
                    if len(favicon_data) > 0:
                        response = HttpResponse(favicon_data, content_type='image/x-icon')
                        response['Cache-Control'] = 'public, max-age=86400'  # 缓存1天
                        return response
        except Exception as e:
            logger.debug(f'通过staticfiles finders查找favicon失败: {e}')
        
        # 如果所有路径都失败，返回一个简单的1x1透明PNG（避免ERR_EMPTY_RESPONSE）
        # 这是一个最小的透明PNG图片（1x1像素）
        transparent_png = b'\x89PNG\r\n\x1a\n\x00\x00\x00\rIHDR\x00\x00\x00\x01\x00\x00\x00\x01\x08\x06\x00\x00\x00\x1f\x15\xc4\x89\x00\x00\x00\nIDATx\x9cc\x00\x01\x00\x00\x05\x00\x01\r\n-\xdb\x00\x00\x00\x00IEND\xaeB`\x82'
        response = HttpResponse(transparent_png, content_type='image/png')
        response['Cache-Control'] = 'public, max-age=86400'  # 缓存1天
        return response
    except Exception as e:
        logger.warning(f'favicon_view处理异常: {e}', exc_info=True)
        # 返回一个简单的透明PNG而不是空响应，避免连接重置
        transparent_png = b'\x89PNG\r\n\x1a\n\x00\x00\x00\rIHDR\x00\x00\x00\x01\x00\x00\x00\x01\x08\x06\x00\x00\x00\x1f\x15\xc4\x89\x00\x00\x00\nIDATx\x9cc\x00\x01\x00\x00\x05\x00\x01\r\n-\xdb\x00\x00\x00\x00IEND\xaeB`\x82'
        response = HttpResponse(transparent_png, content_type='image/png')
        response['Cache-Control'] = 'public, max-age=86400'  # 缓存1天
        return response


def test_admin_page(request):
    """测试admin页面"""
    return redirect('admin:index')


def django_service_control(request):
    """Django服务控制"""
    return JsonResponse({'status': 'ok'})


def _get_current_module_from_path(request_path):
    """
    根据URL路径判断当前模块
    
    Args:
        request_path: 请求路径（如 '/business/opportunities/create/'）
    
    Returns:
        str: 模块名称（如 'opportunity_management', 'contract_management' 等），如果无法判断则返回None
    """
    if not request_path:
        return None
    
    # URL路径到模块的映射
    path_to_module_map = [
        # 商机管理
        ('/business/opportunities', 'opportunity_management'),
        # 合同管理
        ('/business/contracts', 'contract_management'),
        ('/business/authorization-letters', 'contract_management'),
        ('/business/authorization-letter-templates', 'contract_management'),
        # 客户管理
        ('/business/customers', 'customer_management'),
        ('/business/', 'customer_management'),  # 客户管理首页
        # 产值管理
        ('/settlement/output-value', 'output_value_management'),
        # 项目结算
        ('/settlement/project-settlement', 'project_settlement'),
        # 回款管理
        ('/settlement/payment', 'payment_management'),
        # 生产管理
        ('/production/', 'production_management'),
        # 收文管理
        ('/delivery/incoming-document', 'incoming_document'),
        # 发文管理
        ('/delivery/outgoing-document', 'outgoing_document'),
        # 档案管理
        ('/archive/', 'archive_management'),
        # 计划管理
        ('/plan/', 'plan_management'),
        # 诉讼管理
        ('/litigation/', 'litigation_management'),
        # 风险管理
        ('/risk/', 'risk_management'),
        # 财务管理
        ('/finance/', 'financial_management'),
        # 人事管理
        ('/personnel/', 'personnel_management'),
        # 行政管理
        ('/administrative/', 'administrative_management'),
        # 系统管理
        ('/system/', 'system_management'),
        # 资源管理
        ('/resource/', 'resource_standard'),
        ('/resource-standard/', 'resource_standard'),
        # 工作流引擎
        ('/workflow/', 'workflow_engine'),
        # API管理
        ('/api-management/', 'api_management'),
        # 任务协作
        ('/task/', 'task_collaboration'),
    ]
    
    # 按路径长度从长到短排序，优先匹配更具体的路径
    path_to_module_map.sort(key=lambda x: len(x[0]), reverse=True)
    
    for path_pattern, module_name in path_to_module_map:
        if path_pattern in request_path:
            return module_name
    
    return None


def _get_sidebar_menu_for_module(module_name, permission_set, request_path, user):
    """
    根据模块名称获取对应的左侧菜单
    
    Args:
        module_name: 模块名称（如 'opportunity_management'）
        permission_set: 用户权限集合
        request_path: 请求路径（用于确定激活的菜单项）
        user: 当前用户对象
    
    Returns:
        list: 菜单项列表，格式与 module_sidebar_nav 一致
    """
    if not module_name:
        return []
    
    try:
        # 根据模块名称导入对应的菜单构建函数
        if module_name == 'opportunity_management':
            from backend.apps.customer_management.views_pages import _build_opportunity_management_menu
            # 根据路径确定激活的菜单项
            active_id = None
            if '/opportunities/create' in request_path:
                active_id = 'opportunity_create'
            elif '/opportunities/list' in request_path or '/opportunities/' in request_path and request_path.count('/') >= 3:
                active_id = 'opportunity_list'
            elif '/opportunities' in request_path:
                active_id = 'opportunity_home'
            return _build_opportunity_management_menu(permission_set, active_id=active_id)
        
        elif module_name == 'contract_management':
            from backend.apps.customer_management.views_pages import _build_contract_management_menu
            # 根据路径确定激活的菜单项
            active_id = None
            if '/contracts/create' in request_path:
                active_id = 'contract_management_list'
            elif '/contracts/' in request_path and request_path.count('/') >= 3:
                active_id = 'contract_management_list'
            return _build_contract_management_menu(permission_set, active_id=active_id)
        
        elif module_name == 'customer_management':
            from backend.apps.customer_management.views_pages import _build_customer_management_menu
            return _build_customer_management_menu(permission_set, active_id=None)
        
        elif module_name == 'output_value_management':
            from backend.apps.settlement_center.views_pages import _build_output_value_sidebar_nav
            return _build_output_value_sidebar_nav(permission_set, request_path)
        
        elif module_name == 'project_settlement':
            from backend.apps.settlement_center.views_pages import _build_project_settlement_sidebar_nav
            return _build_project_settlement_sidebar_nav(permission_set, request_path)
        
        elif module_name == 'payment_management':
            from backend.apps.settlement_center.views_pages import _build_payment_sidebar_nav
            return _build_payment_sidebar_nav(permission_set, request_path)
        
        elif module_name == 'production_management':
            from backend.apps.production_management.views_pages import _build_production_management_sidebar_nav
            return _build_production_management_sidebar_nav(permission_set, request_path, user, active_id=None)
        
        elif module_name in ['incoming_document', 'outgoing_document']:
            from backend.apps.delivery_customer.views_pages import _build_delivery_sidebar_nav
            return _build_delivery_sidebar_nav(permission_set, request_path)
        
        elif module_name == 'archive_management':
            from backend.apps.archive_management.views_pages import _build_archive_sidebar_nav
            return _build_archive_sidebar_nav(permission_set, request_path)
        
        elif module_name == 'plan_management':
            from backend.apps.plan_management.views_pages import _build_plan_management_sidebar_nav
            return _build_plan_management_sidebar_nav(permission_set, request_path, active_id=None)
        
        elif module_name == 'litigation_management':
            from backend.apps.litigation_management.views_pages import _build_litigation_sidebar_nav
            return _build_litigation_sidebar_nav(permission_set, request_path)
        
        elif module_name == 'financial_management':
            from backend.apps.financial_management.views_pages import _build_financial_sidebar_nav
            return _build_financial_sidebar_nav(permission_set, request_path)
        
        elif module_name == 'personnel_management':
            from backend.apps.personnel_management.views_pages import _build_personnel_sidebar_nav
            return _build_personnel_sidebar_nav(permission_set, request_path)
        
        elif module_name == 'administrative_management':
            from backend.apps.administrative_management.views_pages import _build_administrative_sidebar_nav
            return _build_administrative_sidebar_nav(permission_set, request_path)
        
        elif module_name == 'system_management':
            from backend.apps.system_management.views_pages import _build_system_management_sidebar_nav
            return _build_system_management_sidebar_nav(permission_set, request_path)
        
        elif module_name == 'resource_standard':
            from backend.apps.resource_standard.views import _build_resource_management_sidebar_nav
            return _build_resource_management_sidebar_nav(permission_set, request_path)
        
        elif module_name == 'risk_management':
            from backend.apps.risk_management.views_pages import _build_risk_management_sidebar_nav
            return _build_risk_management_sidebar_nav(permission_set, request_path)
        
        elif module_name == 'task_collaboration':
            from backend.apps.task_collaboration.views_pages import _build_task_collaboration_sidebar_nav
            return _build_task_collaboration_sidebar_nav(permission_set, request_path, active_id=None)
        
        # 如果模块没有对应的菜单构建函数，返回空列表
        # 注意：workflow_engine, api_management, settlement_management 等模块没有左侧菜单
        return []
    
    except Exception as e:
        import logging
        logger = logging.getLogger(__name__)
        logger.warning(f'获取模块 {module_name} 的左侧菜单失败: {e}', exc_info=True)
        return []
