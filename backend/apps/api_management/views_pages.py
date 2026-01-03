"""
API管理模块页面视图
"""
from django.contrib.auth.decorators import login_required
from django.shortcuts import render, redirect
from django.contrib import messages
from django.urls import reverse
from django.utils import timezone

from backend.apps.system_management.services import get_user_permission_codes
from backend.core.views import _permission_granted, _build_full_top_nav
from .models import ExternalSystem, ApiInterface, ApiCallLog


def _context(page_title, page_icon, description, summary_cards=None, sections=None, request=None):
    """构建页面上下文"""
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
    else:
        context['full_top_nav'] = []
    
    return context


@login_required
def api_management_home(request):
    """API管理首页"""
    permission_codes = get_user_permission_codes(request.user)
    today = timezone.now().date()
    this_month_start = today.replace(day=1)
    
    # 权限检查
    if not _permission_granted('api_management.view', permission_codes):
        messages.error(request, '您没有权限访问API管理')
        return redirect('admin:index')
    
    # 收集统计数据
    summary_cards = []
    
    try:
        # 外部系统统计
        if _permission_granted('api_management.view', permission_codes):
            try:
                total_systems = ExternalSystem.objects.count()
                active_systems = ExternalSystem.objects.filter(status='active', is_active=True).count()
                
                summary_cards.append({
                    'label': '外部系统',
                    'icon': '🔌',
                    'value': str(total_systems),
                    'subvalue': f'启用 {active_systems} 个',
                    'url': '/admin/api_management/externalsystem/',
                    'variant': 'info'
                })
            except Exception:
                pass
        
        # API接口统计
        if _permission_granted('api_management.view', permission_codes):
            try:
                total_apis = ApiInterface.objects.count()
                active_apis = ApiInterface.objects.filter(status='active', is_active=True).count()
                
                summary_cards.append({
                    'label': 'API接口',
                    'icon': '🌐',
                    'value': str(total_apis),
                    'subvalue': f'启用 {active_apis} 个',
                    'url': '/admin/api_management/apiinterface/',
                    'variant': 'info'
                })
            except Exception:
                pass
        
        # API调用统计
        if _permission_granted('api_management.view', permission_codes):
            try:
                this_month_calls = ApiCallLog.objects.filter(called_time__gte=this_month_start).count()
                success_calls = ApiCallLog.objects.filter(
                    called_time__gte=this_month_start,
                    status='success'
                ).count()
                
                summary_cards.append({
                    'label': '本月调用',
                    'icon': '📊',
                    'value': str(this_month_calls),
                    'subvalue': f'成功 {success_calls} 次',
                    'url': '/admin/api_management/apicalllog/',
                    'variant': 'success' if success_calls == this_month_calls else 'warning'
                })
            except Exception:
                pass
    except Exception as e:
        import logging
        logger = logging.getLogger(__name__)
        logger.exception('获取统计数据失败: %s', str(e))
    
    # 功能模块入口
    module_entries = []
    
    if _permission_granted('api_management.view', permission_codes):
        module_entries.append({
            'label': '外部系统',
            'icon': '🔌',
            'description': '管理外部系统配置',
            'url': '/admin/api_management/externalsystem/',
            'link_label': '进入模块 →'
        })
        
        module_entries.append({
            'label': 'API接口',
            'icon': '🌐',
            'description': '管理API接口配置',
            'url': '/admin/api_management/apiinterface/',
            'link_label': '进入模块 →'
        })
        
        module_entries.append({
            'label': '调用日志',
            'icon': '📋',
            'description': '查看API调用日志',
            'url': '/admin/api_management/apicalllog/',
            'link_label': '进入模块 →'
        })
    
    # 构建区域
    sections = []
    
    if module_entries:
        sections.append({
            'title': '功能模块',
            'description': 'API管理的各个功能模块入口',
            'items': module_entries,
            'layout': 'grid'
        })
    
    # 构建上下文
    context = _context(
        page_title="API管理",
        page_icon="🔌",
        description="管理系统API接口和外部系统集成",
        summary_cards=summary_cards,
        sections=sections,
        request=request,
    )
    
    return render(request, "api_management/home.html", context)

