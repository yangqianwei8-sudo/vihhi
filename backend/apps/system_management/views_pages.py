from django.contrib import messages
from django.contrib.auth import logout
from django.contrib.auth.decorators import login_required, permission_required
from django.shortcuts import render, redirect
from django.urls import reverse

from collections import defaultdict, OrderedDict

from backend.apps.system_management.models import Department, Role, User
from backend.apps.permission_management.models import PermissionItem
from backend.apps.system_management.serializers import (
    AccountProfileSerializer,
    AccountNotificationSerializer,
    AccountPasswordChangeSerializer,
)
from backend.apps.system_management.services import get_user_permission_codes
from backend.apps.system_management.forms import POSITION_CHOICES
from backend.core.views import _permission_granted, _build_full_top_nav, _build_unified_sidebar_nav


# 系统管理菜单结构定义
SYSTEM_MANAGEMENT_MENU_STRUCTURE = [
    {
        'id': 'system_management_home',
        'label': '系统管理首页',
        'icon': '🏠',
        'url_name': 'system_pages:system_management_home',
        'permission': 'system_management.view',
    },
]


def _build_system_management_sidebar_nav(permission_set, request_path=None, active_id=None):
    """生成系统管理左侧菜单（统一格式）"""
    # 使用统一的菜单构建函数
    return _build_unified_sidebar_nav(SYSTEM_MANAGEMENT_MENU_STRUCTURE, permission_set, active_id=active_id)


def _context(page_title, page_icon, description, summary_cards=None, sections=None, request=None):
    context = {
        "page_title": page_title,
        "page_icon": page_icon,
        "description": description,
        "summary_cards": summary_cards or [],
        "sections": sections or [],
    }
    
    if request and request.user.is_authenticated:
        permission_set = get_user_permission_codes(request.user)
        context['full_top_nav'] = _build_full_top_nav(permission_set, request.user)
        context['module_sidebar_nav'] = _build_system_management_sidebar_nav(permission_set, request.path)
    else:
        context['full_top_nav'] = []
        context['module_sidebar_nav'] = []
    
    return context


@login_required
def system_management_home(request):
    """系统管理首页"""
    permission_codes = get_user_permission_codes(request.user)
    
    # 权限检查
    if not _permission_granted('system_management.view', permission_codes):
        messages.error(request, '您没有权限访问系统管理')
        return redirect('admin:index')
    
    # 收集统计数据
    summary_cards = []
    
    try:
        # 用户统计
        if _permission_granted('system_management.user.view', permission_codes):
            try:
                total_users = User.objects.count()
                active_users = User.objects.filter(is_active=True).count()
                
                summary_cards.append({
                    'label': '用户总数',
                    'icon': '👥',
                    'value': str(total_users),
                    'subvalue': f'活跃用户 {active_users} 人',
                    'url': '/admin/system_management/user/',
                    'variant': 'info'
                })
            except Exception:
                pass
        
        # 角色统计
        if _permission_granted('system_management.role.view', permission_codes):
            try:
                total_roles = Role.objects.count()
                
                summary_cards.append({
                    'label': '角色总数',
                    'icon': '🎭',
                    'value': str(total_roles),
                    'subvalue': '系统角色',
                    'url': '/admin/system_management/role/',
                    'variant': 'info'
                })
            except Exception:
                pass
        
        # 部门统计
        if _permission_granted('system_management.department.view', permission_codes):
            try:
                total_departments = Department.objects.count()
                active_departments = Department.objects.filter(is_active=True).count()
                
                summary_cards.append({
                    'label': '部门总数',
                    'icon': '🏢',
                    'value': str(total_departments),
                    'subvalue': f'启用 {active_departments} 个',
                    'url': '/admin/system_management/department/',
                    'variant': 'info'
                })
            except Exception:
                pass
    except Exception as e:
        import logging
        logger = logging.getLogger(__name__)
        logger.exception('获取统计数据失败: %s', str(e))
    
    # 功能模块入口
    module_entries = []
    
    if _permission_granted('system_management.user.view', permission_codes):
        module_entries.append({
            'label': '用户管理',
            'icon': '👥',
            'description': '管理系统用户',
            'url': '/admin/system_management/user/',
            'link_label': '进入模块 →'
        })
    
    if _permission_granted('system_management.role.view', permission_codes):
        module_entries.append({
            'label': '角色管理',
            'icon': '🎭',
            'description': '管理系统角色',
            'url': '/admin/system_management/role/',
            'link_label': '进入模块 →'
        })
    
    if _permission_granted('system_management.department.view', permission_codes):
        module_entries.append({
            'label': '部门管理',
            'icon': '🏢',
            'description': '管理部门组织',
            'url': '/admin/system_management/department/',
            'link_label': '进入模块 →'
        })
    
    # 构建区域
    sections = []
    
    if module_entries:
        sections.append({
            'title': '功能模块',
            'description': '系统管理的各个功能模块入口',
            'items': module_entries,
            'layout': 'grid'
        })
    
    # 构建上下文
    context = _context(
        page_title="系统管理",
        page_icon="⚙️",
        description="管理系统设置、用户和权限",
        summary_cards=summary_cards,
        sections=sections,
        request=request,
    )
    
    return render(request, "system_management/home.html", context)


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
    )
    return render(request, "system_management/home.html", context)


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
    return render(request, "system_management/home.html", context)


@login_required
def data_dictionary(request):
    # 仅系统管理员可以访问数据字典
    is_system_admin = request.user.is_superuser or request.user.roles.filter(code='system_admin').exists()
    if not is_system_admin:
        from django.core.exceptions import PermissionDenied
        raise PermissionDenied("仅系统管理员可以访问数据字典。")
    summary_cards = []
    context = _context(
        "数据字典",
        "📚",
        "维护系统基础数据、编码规则与引用关系，为业务表单提供统一标准。",
        summary_cards=summary_cards,
        sections=[
            {
                "title": "数据维护",
                "description": "按类别维护和发布字典条目。",
                "items": [
                    {"label": "基础资料", "description": "行业、专业、阶段等基础数据。", "url": "#", "icon": "📘"},
                    {"label": "编码规则", "description": "维护编码方案与生成规则。", "url": "#", "icon": "🧮"},
                    {"label": "版本管理", "description": "管理字典版本与发布记录。", "url": "#", "icon": "🗃"},
                ],
            }
        ],
    )
    return render(request, "system_management/home.html", context)


@login_required
@permission_required("system_management.manage_users", raise_exception=True)
def permission_matrix(request):
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
