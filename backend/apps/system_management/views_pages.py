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

from backend.apps.system_management.models import Department, Role, User, SystemFeedback
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
    return render(request, "shared/center_dashboard.html", context)


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
        },
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
