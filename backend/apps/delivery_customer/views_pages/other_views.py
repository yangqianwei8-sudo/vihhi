from django.contrib.auth.decorators import login_required
from django.shortcuts import render, redirect
from django.urls import reverse, NoReverseMatch
from django.views.decorators.csrf import csrf_exempt
from django.http import JsonResponse
from django.utils import timezone
from django.contrib import messages
import logging

from backend.apps.system_management.services import get_user_permission_codes
from backend.core.views import HOME_NAV_STRUCTURE, _permission_granted, _build_full_top_nav, _build_unified_sidebar_nav
from .common import _context, _build_delivery_sidebar_nav

logger = logging.getLogger(__name__)


@login_required
def report_delivery(request):
    """收发管理首页 - 新版本：直接跳转到交付记录列表页（保留用于向后兼容）"""
    from django.shortcuts import redirect
    
    permission_set = get_user_permission_codes(request.user)
    
    # 权限检查
    if not _permission_granted('delivery_center.view', permission_set):
        from django.http import HttpResponseForbidden
        return HttpResponseForbidden("无权限访问收发管理")
    
    # 新版本：直接跳转到交付记录列表页（首页=交付记录列表）
    return redirect('delivery_pages:delivery_list')


@login_required
def customer_collaboration(request):
    """客户协同工作台 - 老版本（已注释，待实现）"""
    # ==================== 老版本代码（已注释）====================
    # 客户协同工作台功能待实现，暂时注释掉老版本代码
    # context = _context(
    #     "客户协同工作台",
    #     "🤝",
    #     "与客户及设计方协同处理意见、确认事项与信息同步。",
    #     request=request,
    #     summary_cards=[
    #         {"label": "活跃协同", "value": "0", "hint": "当前有互动的客户协同专题"},
    #         {"label": "待回复事项", "value": "0", "hint": "等待客户或设计方反馈的事项"},
    #         {"label": "协同会议", "value": "0", "hint": "排期中的客户会议数量"},
    #         {"label": "满意度评分", "value": "--", "hint": "客户反馈满意度"},
    #     ],
    #     sections=[
    #         {
    #             "title": "协同功能",
    #             "description": "围绕客户沟通的关键环节进行管理。",
    #             "items": [
    #                 {"label": "协同专题", "description": "为项目创建协同沟通空间。", "url": "#", "icon": "🗂"},
    #                 {"label": "互动记录", "description": "跟踪客户沟通日志。", "url": "#", "icon": "📝"},
    #                 {"label": "待办提醒", "description": "及时处理客户反馈与任务。", "url": "#", "icon": "⏰"},
    #             ],
    #         }
    #     ],
    # )
    # return render(request, "shared/center_dashboard.html", context)
    # ==================== 老版本代码结束 ====================
    
    # 新版本：暂时返回404或跳转到交付记录列表
    from django.http import Http404
    raise Http404("客户协同工作台功能待实现")


@login_required
def customer_portal(request):
    """客户门户管理 - 老版本（已注释，待实现）"""
    # ==================== 老版本代码（已注释）====================
    # 客户门户管理功能待实现，暂时注释掉老版本代码
    # context = _context(
    #     "客户门户管理",
    #     "🌐",
    #     "配置客户门户账号、权限与界面展示，实现成果在线交付与客户自助服务。",
    #     request=request,
    #     summary_cards=[
    #         {"label": "门户用户", "value": "0", "hint": "已开通的客户门户账号数"},
    #         {"label": "活跃用户", "value": "0", "hint": "近 30 天登录的客户数"},
    #         {"label": "权限模板", "value": "0", "hint": "已配置的门户权限组"},
    #         {"label": "界面主题", "value": "0", "hint": "可选门户主题数量"},
    #     ],
    #     sections=[
    #         {
    #             "title": "门户配置",
    #             "description": "在线配置客户门户资源。",
    #             "items": [
    #                 {"label": "账号管理", "description": "新增或停用客户账号。", "url": "#", "icon": "👤"},
    #                 {"label": "权限设置", "description": "维护门户访问权限。", "url": "#", "icon": "🔐"},
    #                 {"label": "界面定制", "description": "调整门户视觉与栏目。", "url": "#", "icon": "🎨"},
    #             ],
    #         }
    #     ],
    # )
    # return render(request, "shared/center_dashboard.html", context)
    # ==================== 老版本代码结束 ====================
    
    # 新版本：暂时返回404或跳转到交付记录列表
    from django.http import Http404
    raise Http404("客户门户管理功能待实现")


@login_required
def electronic_signature(request):
    """电子签章中心 - 老版本（已注释，待实现）"""
    # ==================== 老版本代码（已注释）====================
    # 电子签章中心功能待实现，暂时注释掉老版本代码
    # context = _context(
    #     "电子签章中心",
    #     "🖋",
    #     "统一管理成果确认函、结算确认单等电子签署流程，确保轨迹可追溯。",
    #     request=request,
    #     summary_cards=[
    #         {"label": "待签文件", "value": "0", "hint": "等待签署的电子文档数量"},
    #         {"label": "已完成签章", "value": "0", "hint": "已完成签署并归档的文件"},
    #         {"label": "签署耗时", "value": "--", "hint": "平均签署完成耗时"},
    #         {"label": "异常记录", "value": "0", "hint": "签署失败或撤回的记录"},
    #     ],
    #     sections=[
    #         {
    #             "title": "签章流程",
    #             "description": "发起、追踪并归档电子签章。",
    #             "items": [
    #                 {"label": "发起签署", "description": "上传文档并选择签署方。", "url": "#", "icon": "📨"},
    #                 {"label": "签署进度", "description": "实时查看签章状态。", "url": "#", "icon": "⏳"},
    #                 {"label": "签署归档", "description": "管理签署完成后的文件。", "url": "#", "icon": "🗄"},
    #             ],
    #         }
    #     ],
    # )
    # return render(request, "shared/center_dashboard.html", context)
    # ==================== 老版本代码结束 ====================
    
    # 新版本：暂时返回404或跳转到交付记录列表
    from django.http import Http404
    raise Http404("电子签章中心功能待实现")


