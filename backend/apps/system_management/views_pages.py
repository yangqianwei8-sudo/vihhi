from django.contrib import messages
from django.contrib.auth import logout
from django.contrib.auth.decorators import login_required
from django.core.exceptions import PermissionDenied
from django.shortcuts import render, redirect, get_object_or_404
from django.urls import reverse, NoReverseMatch
from django.http import JsonResponse
from django.utils import timezone
from django.core.paginator import Paginator

from collections import defaultdict, OrderedDict

from backend.apps.system_management.models import Department, Role, User, SystemFeedback, DataDictionary
from backend.apps.permission_management.models import PermissionItem
from backend.apps.system_management.serializers import (
    AccountProfileSerializer,
    AccountNotificationSerializer,
    AccountPasswordChangeSerializer,
)
from backend.apps.system_management.services import get_user_permission_codes
from backend.apps.system_management.forms import POSITION_CHOICES, SystemFeedbackForm
from backend.core.views import _build_full_top_nav, _permission_granted


def _is_admin(user):
    """与 config.admin 一致：仅 username=admin 或 is_superuser 视为 admin"""
    if not user or not user.is_authenticated:
        return False
    return user.username == 'admin' or user.is_superuser


def _context(page_title, page_icon, description, summary_cards=None, sections=None, request=None):
    return {
        "page_title": page_title,
        "page_icon": page_icon,
        "description": description,
        "summary_cards": summary_cards or [],
        "sections": sections or [],
    }


@login_required
def account_settings(request):
    user = request.user
    tab = request.GET.get("tab", "profile")
    if tab not in {"profile", "notifications", "security"}:
        tab = "profile"

    profile_errors = {}
    notification_errors = {}
    password_errors = {}

    profile_data = AccountProfileSerializer(instance=user, context={"request": request}).data
    notification_values = user.get_notification_preferences()
    position_choices = POSITION_CHOICES.get(user.user_type, POSITION_CHOICES.get('internal', []))

    if request.method == "POST":
        form_type = request.POST.get("form_type")
        if form_type == "profile":
            payload = {
                "first_name": request.POST.get("first_name", "").strip(),
                "last_name": request.POST.get("last_name", "").strip(),
                "email": request.POST.get("email", "").strip(),
                "position": request.POST.get("position", "").strip(),
            }
            avatar_file = request.FILES.get("avatar")
            if avatar_file:
                payload["avatar"] = avatar_file

            serializer = AccountProfileSerializer(
                instance=user,
                data=payload,
                partial=True,
                context={"request": request},
            )
            if serializer.is_valid():
                serializer.save()
                messages.success(request, "账号资料已更新。")
                return redirect("system_pages:account_settings")
            profile_errors = serializer.errors
            display_payload = payload.copy()
            display_payload.pop("avatar", None)
            profile_data = {**profile_data, **display_payload}
            tab = "profile"
            messages.error(request, "资料保存失败，请检查填写内容。")

        elif form_type == "notifications":
            payload = {
                "inbox": request.POST.get("inbox") == "on",
                "email": request.POST.get("email") == "on",
                "wecom": request.POST.get("wecom") == "on",
            }
            serializer = AccountNotificationSerializer(data=payload)
            if serializer.is_valid():
                preferences = user.get_notification_preferences()
                preferences.update(serializer.validated_data)
                user.notification_preferences = preferences
                user.save(update_fields=["notification_preferences"])
                messages.success(request, "通知偏好已保存。")
                return redirect(f"{reverse('system_pages:account_settings')}?tab=notifications")
            notification_errors = serializer.errors
            notification_values = payload
            tab = "notifications"
            messages.error(request, "通知偏好保存失败，请至少开启一种通知方式。")

        elif form_type == "password":
            serializer = AccountPasswordChangeSerializer(
                data={
                    "old_password": request.POST.get("old_password", ""),
                    "new_password": request.POST.get("new_password", ""),
                    "confirm_password": request.POST.get("confirm_password", ""),
                },
                context={"request": request},
            )
            if serializer.is_valid():
                user.set_password(serializer.validated_data["new_password"])
                user.save(update_fields=["password"])
                logout(request)
                messages.success(request, "密码已更新，请重新登录。")
                return redirect("login")
            password_errors = serializer.errors
            tab = "security"
            messages.error(request, "密码修改失败，请检查输入内容。")

    roles = user.roles.all().order_by("name")
    permission_codes = sorted(get_user_permission_codes(user))

    context = {
        "user_obj": user,
        "active_tab": tab,
        "profile_data": profile_data,
        "notification_values": notification_values,
        "profile_errors": profile_errors,
        "notification_errors": notification_errors,
        "password_errors": password_errors,
        "roles": roles,
        "permission_codes": permission_codes,
        "position_choices": position_choices,
    }
    return render(request, "system_management/account_settings.html", context)


@login_required
def system_management_home(request):
    """系统管理首页"""
    from django.urls import reverse
    permission_set = get_user_permission_codes(request.user)
    
    # 统计卡片
    summary_cards = []
    try:
        users_count = User.objects.count()
        departments_count = Department.objects.count()
        roles_count = Role.objects.count()
        
        summary_cards = [
            {"label": "用户总数", "value": users_count, "hint": "系统注册用户数"},
            {"label": "部门数量", "value": departments_count, "hint": "组织架构部门数"},
            {"label": "角色数量", "value": roles_count, "hint": "系统角色数"},
        ]
    except Exception:
        pass
    
    # 功能模块
    sections = [
        {
            "title": "用户与权限管理",
            "description": "管理用户账号、角色和权限配置。",
            "items": [
                {"label": "系统设置", "description": "系统配置与参数管理。", "url": reverse("system_pages:system_settings"), "icon": "⚙️"},
                {"label": "权限矩阵", "description": "查看角色与权限的对应关系。", "url": reverse("system_pages:permission_matrix"), "icon": "📊"},
                {"label": "数据字典", "description": "维护系统数据字典与基础数据。", "url": reverse("system_pages:data_dictionary"), "icon": "📚"},
                {"label": "操作日志", "description": "查看系统操作日志记录。", "url": reverse("system_pages:operation_logs"), "icon": "📋"},
            ],
        },
        {
            "title": "个人设置",
            "description": "管理个人账号和偏好设置。",
            "items": [
                {"label": "账号设置", "description": "管理个人资料、密码和通知设置。", "url": reverse("system_pages:account_settings"), "icon": "👤"},
            ],
        },
    ]
    
    context = _context(
        "系统管理",
        "⚙️",
        "系统配置、用户权限与数据管理，保障系统稳定运行。",
        summary_cards=summary_cards,
        sections=sections,
        request=request
    )
    
    # 添加顶部导航菜单
    context['full_top_nav'] = _build_full_top_nav(permission_set, user=request.user)
    
    # 添加侧边栏导航
    context['sidebar_nav'] = _build_system_management_sidebar_nav(
        permission_set, 
        request_path=request.path,
        active_id='system_management_home',
        user=request.user,
    )
    
    return render(request, "shared/center_dashboard.html", context)


@login_required
def system_settings(request):
    # 仅系统管理员可以访问系统设置
    is_system_admin = request.user.is_superuser or request.user.roles.filter(code='system_admin').exists()
    if not is_system_admin:
        from django.core.exceptions import PermissionDenied
        raise PermissionDenied("仅系统管理员可以访问系统设置。")
    departments = Department.objects.count()
    users = User.objects.count()
    roles_count = Role.objects.count()
    summary_cards = []
    from django.urls import reverse
    permission_set = get_user_permission_codes(request.user)
    
    context = _context(
        "系统设置",
        "⚙️",
        "配置组织结构、账号策略及平台参数，保障系统稳定运行。",
        summary_cards=summary_cards,
        sections=[
            {
                "title": "用户与权限管理",
                "description": "管理用户账号、角色和权限配置。",
                "items": [
                    {"label": "用户管理", "description": "查看和管理系统用户账号。", "url": "/api/system/users/", "icon": "👥", "note": "通过API接口管理"},
                    {"label": "角色管理", "description": "配置系统角色和权限模板。", "url": "/api/system/roles/", "icon": "🎭", "note": "通过API接口管理"},
                    {"label": "部门管理", "description": "维护组织架构和部门层级。", "url": "/api/system/departments/", "icon": "🏢", "note": "通过API接口管理"},
                    {"label": "权限矩阵", "description": "查看角色与权限的对应关系。", "url": reverse("system_pages:permission_matrix"), "icon": "📊"},
                ],
            },
            {
                "title": "系统配置",
                "description": "常用的系统配置入口。",
                "items": [
                    {"label": "数据字典", "description": "维护系统数据字典与基础数据。", "url": reverse("system_pages:data_dictionary"), "icon": "📚"},
                    {"label": "系统配置", "description": "配置系统参数与开关。", "url": "/admin/system_management/systemconfig/", "icon": "⚙️"},
                    {"label": "注册申请", "description": "审核用户注册申请。", "url": "/admin/registrations/", "icon": "📝"},
                    {"label": "权限管理", "description": "管理业务权限点。", "url": "/admin/system_management/permissionitem/", "icon": "🔑"},
                ],
            }
        ],
        request=request
    )
    
    # 添加侧边栏导航
    context['sidebar_nav'] = _build_system_management_sidebar_nav(
        permission_set, 
        request_path=request.path,
        active_id='system_settings',
        user=request.user,
    )
    
    return render(request, "shared/center_dashboard.html", context)


@login_required
def operation_logs(request):
    # 仅系统管理员可以访问操作日志
    is_system_admin = request.user.is_superuser or request.user.roles.filter(code='system_admin').exists()
    if not is_system_admin:
        from django.core.exceptions import PermissionDenied
        raise PermissionDenied("仅系统管理员可以访问操作日志。")
    summary_cards = []
    context = _context(
        "操作日志",
        "🧾",
        "记录系统操作行为与异常告警，为审计与问题排查提供依据。",
        summary_cards=summary_cards,
        sections=[
            {
                "title": "日志视图",
                "description": "查看不同维度的日志信息。",
                "items": [
                    {"label": "用户操作", "description": "审计用户关键操作记录。", "url": "#", "icon": "🧑‍💼"},
                    {"label": "系统运行", "description": "监控系统服务运行情况。", "url": "#", "icon": "🖥"},
                    {"label": "异常告警", "description": "处理系统异常与安全告警。", "url": "#", "icon": "🚨"},
                ],
            }
        ],
    )
    return render(request, "shared/center_dashboard.html", context)


@login_required
def data_dictionary(request):
    # 仅系统管理员可以访问数据字典
    is_system_admin = request.user.is_superuser or request.user.roles.filter(code='system_admin').exists()
    if not is_system_admin:
        from django.core.exceptions import PermissionDenied
        raise PermissionDenied("仅系统管理员可以访问数据字典。")
    
    permission_set = get_user_permission_codes(request.user)
    
    # 获取选中的字典类型
    selected_type = request.GET.get('type', 'project')
    if selected_type not in dict(DataDictionary.DICT_TYPE_CHOICES):
        selected_type = 'project'
    
    # 构建字典类型导航数据（用于主内容区域的类型选择器）
    dict_type_nav = []
    for type_code, type_name in DataDictionary.DICT_TYPE_CHOICES:
        count = DataDictionary.objects.filter(dict_type=type_code, is_active=True).count()
        dict_type_nav.append({
            'label': type_name,
            'url': f'?type={type_code}',
            'active': type_code == selected_type,
            'badge': str(count) if count > 0 else None,
            'icon': '📚'
        })
    
    # 获取选中类型的字典列表（按父级分组）
    dictionaries = DataDictionary.objects.filter(
        dict_type=selected_type,
        is_active=True
    ).select_related('parent').order_by('order', 'id')
    
    # 按父级分组
    root_items = []
    child_map = defaultdict(list)
    
    for item in dictionaries:
        if item.parent is None:
            root_items.append(item)
        else:
            child_map[item.parent.id].append(item)
    
    # 构建树形结构
    dict_tree = []
    for root in root_items:
        dict_tree.append({
            'item': root,
            'children': sorted(child_map.get(root.id, []), key=lambda x: (x.order, x.id))
        })
    
    # 统计信息
    total_count = DataDictionary.objects.filter(is_active=True).count()
    active_count = DataDictionary.objects.filter(is_active=True).count()
    type_count = len([item for item in dict_type_nav if item.get('badge') and int(item['badge']) > 0])
    
    context = {
        'page_title': '数据字典',
        'dict_type_nav': dict_type_nav,  # 字典类型导航（用于主内容区域）
        'selected_type': selected_type,
        'selected_type_name': dict(DataDictionary.DICT_TYPE_CHOICES).get(selected_type, ''),
        'dict_tree': dict_tree,
        'total_count': total_count,
        'active_count': active_count,
        'type_count': type_count,
    }
    
    # 添加系统管理的侧边栏导航
    context['sidebar_nav'] = _build_system_management_sidebar_nav(
        permission_set, 
        request_path=request.path,
        active_id='data_dictionary',
        user=request.user,
    )
    
    return render(request, "system_management/data_dictionary.html", context)


@login_required
def permission_matrix(request):
    """权限矩阵页面"""
    # 检查业务权限：系统管理权限
    from backend.apps.system_management.services import user_has_permission
    if not (request.user.is_superuser or request.user.is_staff or 
            user_has_permission(request.user, 'system_management.user.manage', 'system_management.manage')):
        from django.core.exceptions import PermissionDenied
        raise PermissionDenied('您没有权限访问此页面。')
    
    roles = (
        Role.objects.prefetch_related("custom_permissions")
        .filter(is_active=True)
        .order_by("name")
    )
    permission_items = PermissionItem.objects.filter(is_active=True).order_by(
        "module", "action"
    )

    role_entries = []
    for role in roles:
        perms = sorted(role.custom_permissions.filter(is_active=True), key=lambda item: (item.module, item.action))
        module_summary = OrderedDict()
        for perm in perms:
            module_summary.setdefault(perm.module, []).append(perm)
        role_entries.append(
            {
                "id": role.id,
                "code": role.code,
                "name": role.name,
                "description": role.description,
                "permission_count": len(perms),
                "module_summary": module_summary,
            }
        )

    module_catalog = defaultdict(list)
    for item in permission_items:
        module_catalog[item.module].append(item)

    context = {
        "role_entries": role_entries,
        "module_catalog": sorted(
            ((module, perms) for module, perms in module_catalog.items()),
            key=lambda entry: entry[0],
        ),
        "permission_total": permission_items.count(),
        "role_total": roles.count(),
    }
    return render(request, "system_management/permission_matrix.html", context)


@login_required
def feedback_submit(request):
    """提交反馈（弹窗表单提交）"""
    if request.method == 'POST':
        form = SystemFeedbackForm(request.POST, request.FILES)
        if form.is_valid():
            feedback = form.save(commit=False)
            feedback.submitted_by = request.user
            # 自动获取当前页面信息
            referer = request.META.get('HTTP_REFERER', '')
            if referer:
                feedback.related_url = referer
            feedback.save()
            
            # 返回JSON响应（用于AJAX提交）
            if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
                return JsonResponse({
                    'success': True,
                    'message': '反馈已提交，我们会尽快处理！',
                    'feedback_id': feedback.id
                })
            else:
                messages.success(request, '反馈已提交，我们会尽快处理！')
                return redirect(request.META.get('HTTP_REFERER', '/'))
        else:
            if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
                return JsonResponse({
                    'success': False,
                    'errors': form.errors
                }, status=400)
    
    # GET请求返回表单（用于弹窗）
    form = SystemFeedbackForm()
    permission_set = get_user_permission_codes(request.user)
    
    return render(request, 'system_management/feedback_form_modal.html', {
        'form': form,
        'full_top_nav': _build_full_top_nav(permission_set, request.user),
    })


@login_required
def feedback_list(request):
    """反馈列表（管理员查看）"""
    permission_set = get_user_permission_codes(request.user)
    
    # 查询参数
    status_filter = request.GET.get('status', 'all')
    type_filter = request.GET.get('type', 'all')
    page_num = request.GET.get('page', 1)
    
    # 构建查询
    queryset = SystemFeedback.objects.select_related('submitted_by', 'processed_by')
    
    # 权限过滤：普通用户只能看自己的反馈
    if not _permission_granted('system_management.view_all_feedback', permission_set):
        queryset = queryset.filter(submitted_by=request.user)
    
    # 状态筛选
    if status_filter != 'all':
        queryset = queryset.filter(status=status_filter)
    
    # 类型筛选
    if type_filter != 'all':
        queryset = queryset.filter(feedback_type=type_filter)
    
    # 排序和分页
    queryset = queryset.order_by('-submitted_at')
    paginator = Paginator(queryset, 20)
    page = paginator.get_page(page_num)
    
    # 统计信息
    base_queryset = SystemFeedback.objects.all()
    if not _permission_granted('system_management.view_all_feedback', permission_set):
        base_queryset = base_queryset.filter(submitted_by=request.user)
    
    stats = {
        'total': base_queryset.count(),
        'pending': base_queryset.filter(status='pending').count(),
        'processing': base_queryset.filter(status='processing').count(),
        'resolved': base_queryset.filter(status='resolved').count(),
    }
    
    return render(request, 'system_management/feedback_list.html', {
        'page_title': '系统反馈',
        'page_icon': '💬',
        'feedbacks': page,
        'status_filter': status_filter,
        'type_filter': type_filter,
        'stats': stats,
        'full_top_nav': _build_full_top_nav(permission_set, request.user),
    })


@login_required
def feedback_process(request, feedback_id):
    """处理反馈"""
    feedback = get_object_or_404(SystemFeedback, id=feedback_id)
    permission_set = get_user_permission_codes(request.user)
    
    # 权限检查：只有管理员可以处理，或者用户只能处理自己的反馈
    can_process = _permission_granted('system_management.process_feedback', permission_set)
    if not can_process and feedback.submitted_by != request.user:
        from django.core.exceptions import PermissionDenied
        raise PermissionDenied("您没有权限处理此反馈。")
    
    if request.method == 'POST':
        status = request.POST.get('status')
        comment = request.POST.get('comment', '').strip()
        
        if status in dict(SystemFeedback.STATUS_CHOICES):
            feedback.status = status
            feedback.process_comment = comment
            feedback.processed_by = request.user
            feedback.processed_at = timezone.now()
            feedback.save()
            
            messages.success(request, '反馈处理完成')
            return redirect('system_pages:feedback_list')
    
    return render(request, 'system_management/feedback_process.html', {
        'feedback': feedback,
        'full_top_nav': _build_full_top_nav(permission_set, request.user),
    })


# ==================== 侧边栏导航 ====================

def _build_system_management_sidebar_nav(permission_set, request_path=None, active_id=None, user=None):
    """构建系统管理模块的侧边栏导航。示例表单相关菜单仅对 admin 显示（见 admin_only）。"""
    # 兼容 core get_module_sidebar_nav：第三参为 user 时（无 active_id）
    if active_id is not None and hasattr(active_id, 'is_authenticated'):
        user = active_id
        active_id = None
    menu_structure = [
        {
            'id': 'system_management_home',
            'label': '首页',
            'icon': '🏠',
            'url_name': 'system_pages:system_management_home',
        },
        {
            'id': 'system_settings',
            'label': '系统设置',
            'icon': '⚙️',
            'url_name': 'system_pages:system_settings',
            'permission': 'system_management.view',
        },
        {
            'id': 'account_settings',
            'label': '账号设置',
            'icon': '👤',
            'url_name': 'system_pages:account_settings',
        },
        {
            'id': 'example_form',
            'label': '示例表单',
            'icon': '📝',
            'url_name': 'system_pages:example_form',
            'admin_only': True,
            'expanded': False,
            'children': [
                {
                    'id': 'create_form_example',
                    'label': '创建提交表单示例',
                    'icon': '📋',
                    'url_name': 'system_pages:create_form_example',
                    'admin_only': True,
                },
                {
                    'id': 'detail_page_example',
                    'label': '详情页面示例',
                    'icon': '📄',
                    'url_name': 'system_pages:detail_page_example',
                    'admin_only': True,
                },
                {
                    'id': 'list_page_example',
                    'label': '列表页面示例',
                    'icon': '📊',
                    'url_name': 'system_pages:list_page_example',
                    'admin_only': True,
                },
                {
                    'id': 'three_column_layout_example',
                    'label': '三栏布局模板',
                    'icon': '📐',
                    'url_name': 'system_pages:three_column_layout_example',
                    'admin_only': True,
                },
                {
                    'id': 'tracking_example',
                    'label': '跟踪示例',
                    'icon': '🎯',
                    'url_name': 'system_pages:tracking_example',
                    'admin_only': True,
                },
            ],
        },
        {
            'id': 'permission_matrix',
            'label': '权限矩阵',
            'icon': '📊',
            'url_name': 'system_pages:permission_matrix',
            'permission': 'system_management.view',
        },
        {
            'id': 'data_dictionary',
            'label': '数据字典',
            'icon': '📚',
            'url_name': 'system_pages:data_dictionary',
            'permission': 'system_management.view',
        },
        {
            'id': 'operation_logs',
            'label': '操作日志',
            'icon': '📋',
            'url_name': 'system_pages:operation_logs',
            'permission': 'system_management.view',
        },
    ]
    
    nav = []
    for item in menu_structure:
        # 仅 admin 可访问的菜单项（示例表单模块）
        if item.get('admin_only'):
            if not user or not _is_admin(user):
                continue
        # 权限检查
        if item.get('permission'):
            if not _permission_granted(item['permission'], permission_set):
                continue
        
        # 处理有子菜单的情况
        if 'children' in item and item.get('children'):
            # 构建子菜单
            children = []
            for child in item['children']:
                # 检查子项权限和admin_only
                if child.get('admin_only'):
                    if not user or not _is_admin(user):
                        continue
                if child.get('permission'):
                    if not _permission_granted(child['permission'], permission_set):
                        continue
                
                # 处理子项 URL
                child_url = '#'
                child_url_name = child.get('url_name')
                if child_url_name:
                    try:
                        child_url = reverse(child_url_name)
                    except NoReverseMatch:
                        child_url = child.get('url', '#')
                else:
                    child_url = child.get('url', '#')
                
                # 判断子项是否激活
                child_active = False
                if active_id and child.get('id') == active_id:
                    child_active = True
                elif request_path and child_url != '#' and request_path.startswith(child_url.rstrip('/')):
                    child_active = True
                
                children.append({
                    'id': child.get('id', ''),
                    'label': child.get('label', ''),
                    'icon': child.get('icon', ''),
                    'url': child_url,
                    'active': child_active,
                })
            
            # 只有当有可见的子项时才添加父菜单
            if children:
                # 处理父菜单 URL
                url = '#'
                url_name = item.get('url_name')
                if url_name:
                    try:
                        url = reverse(url_name)
                    except NoReverseMatch:
                        url = item.get('url', '#')
                else:
                    url = item.get('url', '#')
                
                # 判断父菜单是否激活（如果有激活的子项，父菜单也激活）
                is_active = False
                if active_id and item.get('id') == active_id:
                    is_active = True
                elif request_path and url != '#' and request_path.startswith(url.rstrip('/')):
                    is_active = True
                else:
                    # 检查是否有子项激活
                    for child in children:
                        if child.get('active'):
                            is_active = True
                            break
                
                # 判断是否展开（如果有激活的子项，则展开）
                expanded = item.get('expanded', False)
                if not expanded:
                    for child in children:
                        if child.get('active'):
                            expanded = True
                            break
                
                nav.append({
                    'id': item.get('id', ''),
                    'label': item.get('label', ''),
                    'icon': item.get('icon', ''),
                    'url': url,
                    'active': is_active,
                    'expanded': expanded,
                    'children': children,
                })
        else:
            # 处理没有子菜单的菜单项
            # 处理 URL
            url = '#'
            url_name = item.get('url_name')
            if url_name:
                try:
                    url = reverse(url_name)
                except NoReverseMatch:
                    url = item.get('url', '#')
            else:
                url = item.get('url', '#')
            
            # 判断是否激活
            is_active = False
            if active_id and item.get('id') == active_id:
                is_active = True
            elif request_path and url != '#' and request_path.startswith(url.rstrip('/')):
                is_active = True
            
            nav.append({
                'id': item.get('id', ''),
                'label': item.get('label', ''),
                'icon': item.get('icon', ''),
                'url': url,
                'active': is_active,
            })
    
    return nav


# ==================== 示例表单页面 ====================

@login_required
def example_form(request):
    """示例表单页面 - 展示 create_form_base.html 模板的使用方法（仅 admin 可访问）"""
    if not _is_admin(request.user):
        raise PermissionDenied("仅管理员可访问示例表单模块。")
    permission_set = get_user_permission_codes(request.user)
    
    context = _context(
        "示例表单",
        "📝",
        "查看表单模板的使用示例和说明文档",
        request=request
    )
    
    # 添加侧边栏导航
    context['sidebar_nav'] = _build_system_management_sidebar_nav(
        permission_set, 
        request_path=request.path,
        active_id='example_form',
        user=request.user,
    )
    
    # 添加顶部导航
    context['full_top_nav'] = _build_full_top_nav(permission_set, request.user)
    
    return render(request, "system_management/example_form.html", context)


@login_required
def create_form_example(request):
    """创建提交表单示例页面 - 完全按照 create_form_base.html 模板渲染（仅 admin 可访问）"""
    if not _is_admin(request.user):
        raise PermissionDenied("仅管理员可访问示例表单模块。")
    from django import forms

    permission_set = get_user_permission_codes(request.user)
    
    # 创建示例表单，包含基本信息字段
    class ExampleForm(forms.Form):
        """示例表单 - 展示模板使用方法"""
        responsible_department = forms.ModelChoiceField(
            label='所属部门',
            queryset=Department.objects.filter(is_active=True),
            required=True,
            widget=forms.Select(attrs={'class': 'form-select'})
        )
        responsible_person = forms.ModelChoiceField(
            label='负责人',
            queryset=User.objects.filter(is_active=True),
            required=True,
            widget=forms.Select(attrs={'class': 'form-select'})
        )
        form_number = forms.CharField(
            label='表单编号',
            max_length=50,
            required=False,
            widget=forms.TextInput(attrs={'class': 'form-control', 'placeholder': '系统自动生成', 'readonly': True})
        )
        
        def __init__(self, *args, **kwargs):
            user = kwargs.pop('user', None)
            super().__init__(*args, **kwargs)
            
            # 设置负责人字段的显示格式
            def label_from_instance(obj):
                if hasattr(obj, 'get_full_name'):
                    full_name = obj.get_full_name().strip()
                    if full_name:
                        return full_name
                if hasattr(obj, 'first_name') and obj.first_name:
                    return obj.first_name.strip()
                if hasattr(obj, 'username'):
                    return obj.username
                return str(obj)
            self.fields['responsible_person'].label_from_instance = label_from_instance
            
            # 设置默认值
            if user:
                # 设置所属部门默认值
                if hasattr(user, 'department') and user.department:
                    self.fields['responsible_department'].initial = user.department
                # 设置负责人默认值
                self.fields['responsible_person'].initial = user
                # 设置表单编号（示例：自动生成）
                import uuid
                self.fields['form_number'].initial = f'FORM-{uuid.uuid4().hex[:8].upper()}'
    
    if request.method == 'POST':
        form = ExampleForm(request.POST, user=request.user)
        if form.is_valid():
            messages.success(request, '表单提交成功！')
            return redirect('system_pages:create_form_example')
    else:
        form = ExampleForm(user=request.user)
    
    context = {
        'form': form,
        'page_title': '创建提交表单示例',
        'form_title': '创建提交表单示例',
        'form_subtitle': '完全按照 create_form_base.html 模板渲染',
        'cancel_url_name': 'system_pages:example_form',
    }
    
    # 添加侧边栏导航
    context['sidebar_nav'] = _build_system_management_sidebar_nav(
        permission_set, 
        request_path=request.path,
        active_id='create_form_example',
        user=request.user,
    )
    
    # 添加顶部导航
    context['full_top_nav'] = _build_full_top_nav(permission_set, request.user)
    
    return render(request, "system_management/create_form_example.html", context)


@login_required
def detail_page_example(request):
    """详情页面示例 - 展示 detail_base.html 模板的使用方法（仅 admin 可访问）"""
    if not _is_admin(request.user):
        raise PermissionDenied("仅管理员可访问示例表单模块。")
    permission_set = get_user_permission_codes(request.user)
    
    # 创建示例数据对象（模拟一个对象，包含基础模板所需的所有属性）
    class ExampleObject:
        def __init__(self, user):
            self.id = 1
            self.plan_number = 'PLAN-EXAMPLE-001'
            self.name = '示例详情对象'
            self.level = 'level_1'
            self.plan_period = 'annual'
            self.related_goal = None
            self.parent_plan = None
            self.related_project = None
            self.start_time = None
            self.start_date = None
            self.end_time = None
            self.end_date = None
            self.content = '这是一个详情页面示例，展示了如何使用 detail_base.html 模板。\n\n详情页面模板提供了以下功能：\n1. 操作卡片：编辑、删除、提交审批等操作按钮\n2. 基本信息卡片：展示表单的主要字段\n3. 状态信息卡片：展示状态变更历史\n4. 关联信息卡片：展示关联记录和链接\n5. 审计信息卡片：展示审计日志和修改记录\n6. 数据统计卡片：展示进度和统计数据\n7. 附件信息卡片：展示附件和文件\n8. 系统信息卡片：展示创建时间、更新时间等系统字段'
            self.plan_objective = None
            self.collaboration_plan = None
            self.created_time = None
            self.created_at = None
            self.updated_time = None
            self.updated_at = None
            self.created_by = user
            # 模拟 participants.all 方法（返回空列表）
            class Participants:
                def all(self):
                    return []
            self.participants = Participants()
            
        def get_level_display(self):
            level_map = {
                'level_1': '一级',
                'level_2': '二级',
                'level_3': '三级',
            }
            return level_map.get(self.level, self.level)
        
        def get_plan_period_display(self):
            period_map = {
                'annual': '年度',
                'quarterly': '季度',
                'monthly': '月度',
            }
            return period_map.get(self.plan_period, self.plan_period)
    
    example_object = ExampleObject(request.user)
    
    context = {
        'object': example_object,
        'page_title': '详情页面示例',
    }
    
    # 添加侧边栏导航
    context['sidebar_nav'] = _build_system_management_sidebar_nav(
        permission_set, 
        request_path=request.path,
        active_id='detail_page_example',
        user=request.user,
    )
    
    # 添加顶部导航
    context['full_top_nav'] = _build_full_top_nav(permission_set, request.user)
    
    return render(request, "system_management/detail_page_example.html", context)


@login_required
def list_page_example(request):
    """列表页面示例 - 展示 list_page_base.html 模板的使用方法（仅 admin 可访问）"""
    if not _is_admin(request.user):
        raise PermissionDenied("仅管理员可访问示例表单模块。")
    from django.core.paginator import Paginator

    permission_set = get_user_permission_codes(request.user)
    
    # 创建示例数据
    class ExampleItem:
        def __init__(self, id, name, status, created_at, created_by):
            self.id = id
            self.name = name
            self.status = status
            self.created_at = created_at
            self.created_by = created_by
    
    # 模拟数据列表
    example_data = [
        ExampleItem(1, '示例项目1', 'active', '2026-01-20 10:00:00', request.user),
        ExampleItem(2, '示例项目2', 'inactive', '2026-01-21 11:00:00', request.user),
        ExampleItem(3, '示例项目3', 'active', '2026-01-22 12:00:00', request.user),
        ExampleItem(4, '示例项目4', 'pending', '2026-01-23 13:00:00', request.user),
        ExampleItem(5, '示例项目5', 'active', '2026-01-24 14:00:00', request.user),
    ]
    
    # 分页
    paginator = Paginator(example_data, 10)
    page_number = request.GET.get('page', 1)
    page_obj = paginator.get_page(page_number)
    
    context = _context(
        "列表页面示例",
        "📊",
        "完全按照 list_page_base.html 模板渲染",
        request=request,
    )
    
    # 添加侧边栏导航
    context['sidebar_nav'] = _build_system_management_sidebar_nav(
        permission_set, 
        request_path=request.path,
        active_id='list_page_example',
        user=request.user,
    )
    
    # 添加顶部导航
    context['full_top_nav'] = _build_full_top_nav(permission_set, request.user)
    
    # 列表页面需要的上下文
    context['page_obj'] = page_obj
    context['page_title'] = '列表页面示例'
    context['description'] = '完全按照 list_page_base.html 模板渲染'
    
    return render(request, "system_management/list_page_example.html", context)


@login_required
def three_column_layout_example(request):
    """三栏布局模板示例 - 完全按照 three_column_layout_base.html 模板渲染（仅 admin 可访问）"""
    if not _is_admin(request.user):
        raise PermissionDenied("仅管理员可访问示例表单模块。")
    permission_set = get_user_permission_codes(request.user)
    
    context = {
        'page_title': '三栏布局模板示例',
    }
    
    # 添加顶部导航（使用标准的顶部栏模板）
    context['full_top_nav'] = _build_full_top_nav(permission_set, request.user)
    
    # 添加侧边栏导航（使用标准的侧边栏模板）
    context['sidebar_nav'] = _build_system_management_sidebar_nav(
        permission_set, 
        request_path=request.path,
        active_id='three_column_layout_example',
        user=request.user,
    )
    context['sidebar_title'] = '系统管理'
    context['sidebar_subtitle'] = 'System Management'
    
    return render(request, "system_management/three_column_layout_example.html", context)


@login_required
def tracking_example(request):
    """跟踪示例页面（目标跟踪/计划跟踪）- 完全按照 tracking_base.html 模板渲染（仅 admin 可访问）
    支持多种跟踪类型：numeric（数字型）、percentage（百分比型）等
    通过 URL 参数：
    - category: goal（目标跟踪）或 plan（计划跟踪），默认为 goal
    - type: numeric, percentage, boolean, choice, text，默认为 numeric
    """
    if not _is_admin(request.user):
        raise PermissionDenied("仅管理员可访问示例表单模块。")
    
    from django import forms
    from datetime import datetime, timedelta
    
    permission_set = get_user_permission_codes(request.user)
    
    # 获取类别和跟踪类型
    category = request.GET.get('category', 'goal')  # goal（目标跟踪）或 plan（计划跟踪）
    tracking_type = request.GET.get('type', 'numeric')  # numeric, percentage, boolean, choice, text
    
    # 创建模拟的跟踪对象（统一类，根据 category 区分目标跟踪和计划跟踪）
    class MockTrackingObject:
        """模拟跟踪对象（统一类，支持目标跟踪和计划跟踪）"""
        def __init__(self, tracking_type='numeric', category='goal'):
            self.tracking_type = tracking_type
            self.status = "in_progress"
            # 为了兼容模板，同时设置 value_type 和 indicator_type
            # indicator_type 是 StrategicGoal 模型使用的属性名
            # value_type 是 tracking_base.html 模板使用的属性名
            
            # 根据 category 设置额外字段
            if category == 'plan':
                self.plan_number = "PLAN-2024-001"
                self.plan_period = "年度计划"
            
            if tracking_type == 'percentage':
                # 百分比型
                if category == 'plan':
                    self.name = "2024年度项目完成度"
                else:
                    self.name = "2024年度销售完成度"
                self.value_type = "percentage"
                self.indicator_type = "percentage"  # 兼容模板中的 indicator_type
                self.target_value = 100
                self.current_value = 65
                self.indicator_unit = "%"
                self.completion_rate = 65.0
            elif tracking_type == 'boolean':
                # 布尔型
                if category == 'plan':
                    self.name = "2024年度项目完成状态"
                else:
                    self.name = "2024年度销售目标完成状态"
                self.value_type = "boolean"
                self.indicator_type = "boolean"  # 兼容模板中的 indicator_type
                self.target_value = 1
                self.current_value = 0  # 0=未完成, 1=已完成
                self.indicator_unit = ""
                self.completion_rate = 0.0
            elif tracking_type == 'choice':
                # 选择型
                if category == 'plan':
                    self.name = "2024年度项目阶段"
                    self.value_choices = [
                        ("stage1", "阶段1：需求分析"),
                        ("stage2", "阶段2：设计开发"),
                        ("stage3", "阶段3：测试验收"),
                    ]
                else:
                    self.name = "2024年度销售阶段"
                    self.value_choices = [
                        ("stage1", "阶段1：市场调研"),
                        ("stage2", "阶段2：销售执行"),
                        ("stage3", "阶段3：完成验收"),
                    ]
                self.value_type = "choice"
                self.indicator_type = "choice"  # 兼容模板中的 indicator_type
                self.target_value = "stage3"
                self.current_value = "stage2"
                self.indicator_unit = ""
                self.completion_rate = 66.7
            elif tracking_type == 'text':
                # 文本型
                if category == 'plan':
                    self.name = "2024年度项目进度描述"
                    self.current_value = "已完成需求分析，正在进行设计开发"
                else:
                    self.name = "2024年度销售进度描述"
                    self.current_value = "已完成市场调研，正在进行销售执行"
                self.value_type = "text"
                self.indicator_type = "text"  # 兼容模板中的 indicator_type
                self.target_value = ""
                self.indicator_unit = ""
                self.completion_rate = 50.0
            else:
                # 默认：数字型
                if category == 'plan':
                    self.name = "2024年度产品研发计划"
                    self.target_value = 500
                    self.current_value = 320
                    self.indicator_unit = "项"
                else:
                    self.name = "2024年度销售目标"
                    self.target_value = 1000
                    self.current_value = 650
                    self.indicator_unit = "万元"
                self.value_type = "numeric"
                self.indicator_type = "numeric"  # 兼容模板中的 indicator_type
                self.completion_rate = (self.current_value / self.target_value) * 100
        
        def get_status_display(self):
            status_map = {
                'draft': '草稿',
                'published': '已发布',
                'in_progress': '执行中',
                'completed': '已完成',
                'cancelled': '已取消',
            }
            return status_map.get(self.status, self.status)
    
    tracking_object = MockTrackingObject(tracking_type=tracking_type, category=category)
    
    # 创建进度更新表单（根据类型动态创建）
    class ProgressUpdateForm(forms.Form):
        """进度更新表单（带业务规则验证）"""
        def __init__(self, *args, tracking_object=None, **kwargs):
            super().__init__(*args, **kwargs)
            self.tracking_object = tracking_object
            
            if not tracking_object:
                # 如果没有 tracking_object，使用默认的数字型字段
                self.fields['current_value'] = forms.DecimalField(
                    label='当前值',
                    required=True,
                    min_value=0,
                    widget=forms.NumberInput(attrs={
                        'class': 'track-form-input',
                        'id': 'id_current_value',
                        'step': '0.01',
                        'min': '0'
                    }),
                    help_text='当前值不能为负数，不能超过目标值的110%'
                )
                return
            
            value_type = tracking_object.value_type
            
            # 根据类型创建不同的字段
            if value_type == 'percentage':
                self.fields['current_value'] = forms.IntegerField(
                    label='完成百分比',
                    required=True,
                    min_value=0,
                    max_value=100,
                    initial=tracking_object.current_value,
                    widget=forms.NumberInput(attrs={
                        'class': 'track-form-input',
                        'id': 'id_current_value',
                        'step': '1',
                        'min': '0',
                        'max': '100',
                        'placeholder': '0-100'
                    }),
                    help_text='请输入0-100之间的百分比值'
                )
            elif value_type == 'boolean':
                self.fields['current_value'] = forms.ChoiceField(
                    label='完成状态',
                    required=True,
                    choices=[('0', '未完成'), ('1', '已完成')],
                    initial=str(tracking_object.current_value),
                    widget=forms.RadioSelect(attrs={
                        'class': 'track-form-radio'
                    }),
                    help_text='请选择完成状态'
                )
            elif value_type == 'choice':
                self.fields['current_value'] = forms.ChoiceField(
                    label='当前阶段',
                    required=True,
                    choices=tracking_object.value_choices,
                    initial=tracking_object.current_value,
                    widget=forms.Select(attrs={
                        'class': 'track-form-input'
                    }),
                    help_text='请选择当前阶段'
                )
            elif value_type == 'text':
                self.fields['current_value'] = forms.CharField(
                    label='当前进度',
                    required=True,
                    max_length=200,
                    initial=tracking_object.current_value,
                    widget=forms.TextInput(attrs={
                        'class': 'track-form-input',
                        'placeholder': '请描述当前进度情况...'
                    }),
                    help_text='请输入当前进度的文字描述'
                )
            else:
                # 默认：数字型
                self.fields['current_value'] = forms.DecimalField(
                    label='当前值',
                    required=True,
                    min_value=0,
                    initial=tracking_object.current_value,
                    widget=forms.NumberInput(attrs={
                        'class': 'track-form-input',
                        'id': 'id_current_value',
                        'step': '0.01',
                        'min': '0'
                    }),
                    help_text='当前值不能为负数，不能超过目标值的110%'
                )
        progress_description = forms.CharField(
            label='进度说明',
            required=True,
            min_length=10,
            max_length=500,
            widget=forms.Textarea(attrs={
                'class': 'track-form-textarea',
                'rows': 3,
                'placeholder': '请详细说明本次进度更新的情况...'
            }),
            help_text='进度说明至少10个字符，最多500个字符'
        )
        remark = forms.CharField(
            label='备注',
            required=False,
            max_length=200,
            widget=forms.Textarea(attrs={
                'class': 'track-form-textarea',
                'rows': 2,
                'placeholder': '可选，添加其他备注信息...'
            })
        )
        
        def clean_current_value(self):
            current_value = self.cleaned_data.get('current_value')
            if not self.tracking_object:
                return current_value
            
            value_type = self.tracking_object.value_type
            
            if value_type == 'percentage':
                # 百分比型验证
                if isinstance(current_value, str):
                    current_value = int(current_value)
                if current_value < 0 or current_value > 100:
                    raise forms.ValidationError('完成百分比必须在0-100之间')
                return current_value
            elif value_type == 'boolean':
                # 布尔型验证
                return int(current_value) if isinstance(current_value, str) else current_value
            elif value_type in ['choice', 'text']:
                # 选择型和文本型直接返回
                return current_value
            else:
                # 数字型验证
                target_value = self.tracking_object.target_value
                if current_value < 0:
                    raise forms.ValidationError('当前值不能为负数')
                if current_value > target_value * 1.1:
                    raise forms.ValidationError(f'当前值不能超过目标值的110%（{target_value * 1.1}）')
                return current_value
        
        def clean_progress_description(self):
            description = self.cleaned_data.get('progress_description')
            if len(description.strip()) < 10:
                raise forms.ValidationError('进度说明至少需要10个字符')
            return description
    
    progress_form = ProgressUpdateForm(tracking_object=tracking_object)
    
    # 处理表单提交
    now = timezone.now()
    current_user = request.user
    
    # 使用 session 存储模拟数据（模拟数据库）
    session_key = f'tracking_mock_records_{category}'  # 根据 category 区分 session key
    if session_key not in request.session:
        # 初始化模拟进度记录（使用可序列化的格式）
        mock_records = [
            {
                'id': 1,
                'recorded_time': (now - timedelta(days=30)).isoformat(),
                'current_value': 100,
                'completion_rate': 20.0,
                'progress_description': '第一阶段研发任务完成，已完成100项研发任务',
                'recorded_by_id': current_user.id,
                'remark': '按计划推进'
            },
            {
                'id': 2,
                'recorded_time': (now - timedelta(days=20)).isoformat(),
                'current_value': 200,
                'completion_rate': 40.0,
                'progress_description': '第二阶段研发任务完成，累计完成200项研发任务',
                'recorded_by_id': current_user.id,
                'remark': '进度良好'
            },
            {
                'id': 3,
                'recorded_time': (now - timedelta(days=10)).isoformat(),
                'current_value': 300,
                'completion_rate': 60.0,
                'progress_description': '第三阶段研发任务完成，累计完成300项研发任务',
                'recorded_by_id': current_user.id,
                'remark': '按计划执行'
            },
        ]
        request.session[session_key] = mock_records
    else:
        mock_records = request.session[session_key]
    
    # 处理进度更新
    if 'update_progress' in request.POST:
        progress_form = ProgressUpdateForm(request.POST, tracking_object=tracking_object)
        if progress_form.is_valid():
            new_current_value = progress_form.cleaned_data['current_value']
            
            # 根据类型计算完成率
            value_type = tracking_object.value_type
            if value_type == 'percentage':
                new_completion_rate = float(new_current_value)
            elif value_type == 'boolean':
                new_completion_rate = 100.0 if new_current_value == 1 or new_current_value == '1' else 0.0
            elif value_type == 'choice':
                # 根据选择的阶段计算完成率
                stage_index = [c[0] for c in tracking_object.value_choices].index(new_current_value)
                total_stages = len(tracking_object.value_choices)
                new_completion_rate = ((stage_index + 1) / total_stages) * 100
            elif value_type == 'text':
                # 文本型不计算完成率，保持原值
                new_completion_rate = tracking_object.completion_rate
            else:
                # 数字型
                new_completion_rate = (float(new_current_value) / tracking_object.target_value) * 100
            
            # 验证不能倒退（仅对数字型和百分比型）
            can_check_backward = value_type in ['numeric', 'percentage']
            if can_check_backward:
                old_value = float(tracking_object.current_value)
                new_value = float(new_current_value)
                if new_value < old_value:
                    messages.error(request, '当前值不能小于之前的进度，不能倒退')
                    progress_form = ProgressUpdateForm(tracking_object=tracking_object)
                else:
                    # 更新对象状态
                    tracking_object.current_value = new_current_value
                    tracking_object.completion_rate = new_completion_rate
                    
                    # 添加新记录（使用可序列化的格式）
                    new_record = {
                        'id': max([r['id'] for r in mock_records], default=0) + 1,
                        'recorded_time': now.isoformat(),
                        'current_value': new_current_value,
                        'completion_rate': new_completion_rate,
                        'progress_description': progress_form.cleaned_data['progress_description'],
                        'recorded_by_id': current_user.id,
                        'remark': progress_form.cleaned_data.get('remark', '')
                    }
                    mock_records.insert(0, new_record)
                    request.session[session_key] = mock_records
                    
                    # 格式化显示消息
                    if value_type == 'percentage':
                        messages.success(request, f'进度已更新：完成百分比 {new_current_value}%，完成率 {new_completion_rate:.1f}%')
                    elif value_type == 'boolean':
                        status_text = '已完成' if new_current_value == 1 or new_current_value == '1' else '未完成'
                        messages.success(request, f'进度已更新：完成状态 {status_text}')
                    elif value_type == 'choice':
                        choice_label = dict(tracking_object.value_choices).get(new_current_value, new_current_value)
                        messages.success(request, f'进度已更新：当前阶段 {choice_label}，完成率 {new_completion_rate:.1f}%')
                    elif value_type == 'text':
                        messages.success(request, f'进度已更新：{new_current_value}')
                    else:
                        messages.success(request, f'进度已更新：当前值 {new_current_value} {tracking_object.indicator_unit}，完成率 {new_completion_rate:.1f}%')
                    
                    progress_form = ProgressUpdateForm(tracking_object=tracking_object)
            else:
                # 对于非数字型，直接更新
                tracking_object.current_value = new_current_value
                tracking_object.completion_rate = new_completion_rate
                
                # 添加新记录
                new_record = {
                    'id': max([r['id'] for r in mock_records], default=0) + 1,
                    'recorded_time': now.isoformat(),
                    'current_value': new_current_value,
                    'completion_rate': new_completion_rate,
                    'progress_description': progress_form.cleaned_data['progress_description'],
                    'recorded_by_id': current_user.id,
                    'remark': progress_form.cleaned_data.get('remark', '')
                }
                mock_records.insert(0, new_record)
                request.session[session_key] = mock_records
                
                # 格式化显示消息
                if value_type == 'boolean':
                    status_text = '已完成' if new_current_value == 1 or new_current_value == '1' else '未完成'
                    messages.success(request, f'进度已更新：完成状态 {status_text}')
                elif value_type == 'choice':
                    choice_label = dict(tracking_object.value_choices).get(new_current_value, new_current_value)
                    messages.success(request, f'进度已更新：当前阶段 {choice_label}，完成率 {new_completion_rate:.1f}%')
                elif value_type == 'text':
                    messages.success(request, f'进度已更新：{new_current_value}')
                
                progress_form = ProgressUpdateForm(tracking_object=tracking_object)
    
    # 处理状态转换
    if 'transition_status' in request.POST:
        new_status = request.POST.get('new_status')
        old_status = tracking_object.status
        status_map = {
            'draft': '草稿',
            'published': '已发布',
            'in_progress': '执行中',
            'completed': '已完成',
            'cancelled': '已取消',
        }
        old_display = status_map.get(old_status, old_status)
        new_display = status_map.get(new_status, new_status)
        tracking_object.status = new_status
        messages.success(request, f'状态已从 {old_display} 转换为 {new_display}')
    elif 'complete_goal' in request.POST:
        tracking_object.status = 'completed'
        tracking_object.completion_rate = 100.0
        if hasattr(tracking_object, 'target_value'):
            tracking_object.current_value = tracking_object.target_value
        messages.success(request, '已完成！')
    
    # 筛选功能（处理序列化后的数据格式）
    recorded_by_filter = request.GET.get('recorded_by', '')
    date_from = request.GET.get('date_from', '')
    date_to = request.GET.get('date_to', '')
    
    filtered_records = mock_records.copy()
    
    if recorded_by_filter:
        filtered_records = [r for r in filtered_records if str(r.get('recorded_by_id', '')) == recorded_by_filter]
    
    if date_from:
        date_from_obj = datetime.strptime(date_from, '%Y-%m-%d').date()
        filtered_records = [
            r for r in filtered_records 
            if datetime.fromisoformat(r['recorded_time']).date() >= date_from_obj
        ]
    
    if date_to:
        date_to_obj = datetime.strptime(date_to, '%Y-%m-%d').date()
        filtered_records = [
            r for r in filtered_records 
            if datetime.fromisoformat(r['recorded_time']).date() <= date_to_obj
        ]
    
    # 将 session 中的记录转换为模板可用的格式
    from django.contrib.auth import get_user_model
    User = get_user_model()
    all_users = User.objects.filter(is_active=True).order_by('username')
    user_map = {user.id: user for user in all_users}
    user_map[current_user.id] = current_user
    
    # 转换记录格式（将 ISO 字符串转换为 datetime，将用户 ID 转换为用户对象）
    class MockProgressRecord:
        """模拟进度记录对象"""
        def __init__(self, record_data):
            self.id = record_data.get('id')
            self.recorded_time = datetime.fromisoformat(record_data['recorded_time'])
            self.current_value = record_data['current_value']
            self.completion_rate = record_data['completion_rate']
            self.progress_description = record_data.get('progress_description', '')
            self.recorded_by = user_map.get(record_data.get('recorded_by_id'), current_user)
            self.remark = record_data.get('remark', '')
    
    # 转换所有记录
    converted_records = []
    for record_data in filtered_records:
        try:
            converted_records.append(MockProgressRecord(record_data))
        except Exception as e:
            # 如果转换失败，跳过该记录
            continue
    
    # 分页
    from django.core.paginator import Paginator
    paginator = Paginator(converted_records, 10)
    page_number = request.GET.get('page', 1)
    page_obj = paginator.get_page(page_number)
    
    # 创建模拟状态日志
    class MockStatusLog:
        """模拟状态日志"""
        def __init__(self, changed_time, old_status, new_status, changed_by, change_reason=None):
            self.changed_time = changed_time
            self.old_status = old_status
            self.new_status = new_status
            self.changed_by = changed_by
            self.change_reason = change_reason
    
    status_logs = [
        MockStatusLog(
            changed_time=now - timedelta(days=60),
            old_status='draft',
            new_status='published',
            changed_by=current_user,
            change_reason='计划审核通过，正式发布'
        ),
        MockStatusLog(
            changed_time=now - timedelta(days=45),
            old_status='published',
            new_status='in_progress',
            changed_by=current_user,
            change_reason='计划启动，开始执行'
        ),
    ]
    
    # 创建模拟调整申请
    class MockAdjustment:
        """模拟调整申请"""
        def __init__(self, applied_time, adjustment_type, old_value, new_value, applied_by, status, reason=None):
            self.applied_time = applied_time
            self.adjustment_type = adjustment_type
            self.old_value = old_value
            self.new_value = new_value
            self.applied_by = applied_by
            self.status = status
            self.reason = reason
        
        def get_status_display(self):
            status_map = {
                'pending': '待审批',
                'approved': '已批准',
                'rejected': '已拒绝',
            }
            return status_map.get(self.status, self.status)
    
    adjustments = [
        MockAdjustment(
            applied_time=now - timedelta(days=25),
            adjustment_type='target_value',
            old_value=450,
            new_value=500,
            applied_by=current_user,
            status='approved',
            reason='根据实际情况调整目标值'
        ),
    ]
    
    # 有效的状态转换
    valid_transitions = ['completed', 'cancelled'] if tracking_object.status == 'in_progress' else []
    
    # 是否可以更新进度和完成
    can_update_progress = tracking_object.status == 'in_progress'
    can_complete = tracking_object.status == 'in_progress'
    
    context = {
        'tracking_object': tracking_object,
        'progress_records': converted_records,  # 使用转换后的记录对象
        'can_update_progress': can_update_progress,
        'valid_transitions': valid_transitions,
        'can_complete': can_complete,
        'all_users': all_users,
        'status_logs': status_logs,
        'adjustments': adjustments,
        'progress_form': progress_form,
        'page_obj': page_obj,
        'recorded_by_filter': recorded_by_filter,
        'date_from': date_from,
        'date_to': date_to,
        'tracking_type': tracking_type,  # 传递跟踪类型到模板
        'category': category,  # 传递类别到模板（goal 或 plan）
    }
    
    # 添加侧边栏导航
    context['sidebar_nav'] = _build_system_management_sidebar_nav(
        permission_set, 
        request_path=request.path,
        active_id='tracking_example',
        user=request.user,
    )
    
    # 添加顶部导航
    context['full_top_nav'] = _build_full_top_nav(permission_set, request.user)
    
    return render(request, "system_management/unified_tracking_example.html", context)
