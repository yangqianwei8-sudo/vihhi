from django.contrib.auth.decorators import login_required
from django.shortcuts import render


def _context(page_title, page_icon, description, summary_cards=None, sections=None):
    return {
        "page_title": page_title,
        "page_icon": page_icon,
        "description": description,
        "summary_cards": summary_cards or [],
        "sections": sections or [],
    }


@login_required
def report_delivery(request):
    """交付管理首页"""
    from .models import DeliveryRecord
    
    # 从数据库获取统计数据
    try:
        total_count = DeliveryRecord.objects.count()
        pending_count = DeliveryRecord.objects.filter(status__in=['draft', 'submitted']).count()
        confirmed_count = DeliveryRecord.objects.filter(status='confirmed').count()
        overdue_count = DeliveryRecord.objects.filter(is_overdue=True).count()
    except Exception:
        # 如果表不存在，使用默认值
        total_count = 0
        pending_count = 0
        confirmed_count = 0
        overdue_count = 0
    
    context = _context(
        "交付管理",
        "📦",
        "管理成果交付、上传确认材料，并追踪客户下载与回执情况。支持邮件、快递、送达三种交付方式。",
        summary_cards=[
            {"label": "待交付成果", "value": str(pending_count), "hint": "等待上传或发送的成果文件"},
            {"label": "客户回执", "value": str(confirmed_count), "hint": "客户已确认的交付项目"},
            {"label": "逾期待发", "value": str(overdue_count), "hint": "超过交付期限仍未完成的任务"},
            {"label": "交付总数", "value": str(total_count), "hint": "所有交付记录总数"},
        ],
        sections=[
            {
                "title": "交付操作",
                "description": "对交付成果进行上传、推送与确认。",
                "items": [
                    {"label": "创建交付单", "description": "发起新的交付任务。", "url": "/delivery/create/", "icon": "🧾"},
                    {"label": "交付记录", "description": "查看历次交付与客户回执。", "url": "/delivery/list/", "icon": "📚"},
                    {"label": "交付统计", "description": "交付效率与及时率分析。", "url": "/delivery/statistics/", "icon": "📈"},
                    {"label": "风险预警", "description": "查看逾期交付预警。", "url": "/delivery/warnings/", "icon": "⚠️"},
                ],
            }
        ],
    )
    return render(request, "shared/center_dashboard.html", context)


@login_required
def delivery_list(request):
    """交付记录列表页"""
    return render(request, "delivery_customer/delivery_list.html", {
        "page_title": "交付记录",
        "page_icon": "📚",
    })


@login_required
def delivery_create(request):
    """创建交付记录页"""
    return render(request, "delivery_customer/delivery_create.html", {
        "page_title": "创建交付单",
        "page_icon": "🧾",
    })


@login_required
def delivery_detail(request, delivery_id):
    """交付记录详情页"""
    from .models import DeliveryRecord
    try:
        delivery = DeliveryRecord.objects.select_related('project', 'client', 'created_by', 'sent_by', 'delivery_person').prefetch_related('files', 'tracking_records', 'feedbacks').get(id=delivery_id)
    except DeliveryRecord.DoesNotExist:
        from django.http import Http404
        raise Http404("交付记录不存在")
    
    return render(request, "delivery_customer/delivery_detail.html", {
        "page_title": "交付详情",
        "page_icon": "📋",
        "delivery": delivery,
    })


@login_required
def delivery_statistics(request):
    """交付统计页"""
    return render(request, "delivery_customer/delivery_statistics.html", {
        "page_title": "交付统计",
        "page_icon": "📈",
    })


@login_required
def delivery_warnings(request):
    """风险预警页"""
    return render(request, "delivery_customer/delivery_warnings.html", {
        "page_title": "风险预警",
        "page_icon": "⚠️",
    })


@login_required
def customer_collaboration(request):
    context = _context(
        "客户协同工作台",
        "🤝",
        "与客户及设计方协同处理意见、确认事项与信息同步。",
        summary_cards=[
            {"label": "活跃协同", "value": "0", "hint": "当前有互动的客户协同专题"},
            {"label": "待回复事项", "value": "0", "hint": "等待客户或设计方反馈的事项"},
            {"label": "协同会议", "value": "0", "hint": "排期中的客户会议数量"},
            {"label": "满意度评分", "value": "--", "hint": "客户反馈满意度"},
        ],
        sections=[
            {
                "title": "协同功能",
                "description": "围绕客户沟通的关键环节进行管理。",
                "items": [
                    {"label": "协同专题", "description": "为项目创建协同沟通空间。", "url": "#", "icon": "🗂"},
                    {"label": "互动记录", "description": "跟踪客户沟通日志。", "url": "#", "icon": "📝"},
                    {"label": "待办提醒", "description": "及时处理客户反馈与任务。", "url": "#", "icon": "⏰"},
                ],
            }
        ],
    )
    return render(request, "shared/center_dashboard.html", context)


@login_required
def customer_portal(request):
    context = _context(
        "客户门户管理",
        "🌐",
        "配置客户门户账号、权限与界面展示，实现成果在线交付与客户自助服务。",
        summary_cards=[
            {"label": "门户用户", "value": "0", "hint": "已开通的客户门户账号数"},
            {"label": "活跃用户", "value": "0", "hint": "近 30 天登录的客户数"},
            {"label": "权限模板", "value": "0", "hint": "已配置的门户权限组"},
            {"label": "界面主题", "value": "0", "hint": "可选门户主题数量"},
        ],
        sections=[
            {
                "title": "门户配置",
                "description": "在线配置客户门户资源。",
                "items": [
                    {"label": "账号管理", "description": "新增或停用客户账号。", "url": "#", "icon": "👤"},
                    {"label": "权限设置", "description": "维护门户访问权限。", "url": "#", "icon": "🔐"},
                    {"label": "界面定制", "description": "调整门户视觉与栏目。", "url": "#", "icon": "🎨"},
                ],
            }
        ],
    )
    return render(request, "shared/center_dashboard.html", context)


@login_required
def electronic_signature(request):
    context = _context(
        "电子签章中心",
        "🖋",
        "统一管理成果确认函、结算确认单等电子签署流程，确保轨迹可追溯。",
        summary_cards=[
            {"label": "待签文件", "value": "0", "hint": "等待签署的电子文档数量"},
            {"label": "已完成签章", "value": "0", "hint": "已完成签署并归档的文件"},
            {"label": "签署耗时", "value": "--", "hint": "平均签署完成耗时"},
            {"label": "异常记录", "value": "0", "hint": "签署失败或撤回的记录"},
        ],
        sections=[
            {
                "title": "签章流程",
                "description": "发起、追踪并归档电子签章。",
                "items": [
                    {"label": "发起签署", "description": "上传文档并选择签署方。", "url": "#", "icon": "📨"},
                    {"label": "签署进度", "description": "实时查看签章状态。", "url": "#", "icon": "⏳"},
                    {"label": "签署归档", "description": "管理签署完成后的文件。", "url": "#", "icon": "🗄"},
                ],
            }
        ],
    )
    return render(request, "shared/center_dashboard.html", context)

