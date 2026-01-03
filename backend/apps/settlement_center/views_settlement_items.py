"""
结算明细项管理视图
处理结算明细项的审核、调整等功能
"""
from django.contrib.auth.decorators import login_required
from django.shortcuts import get_object_or_404, redirect
from django.contrib import messages
from django.http import JsonResponse
from django.views.decorators.http import require_http_methods
from django.utils import timezone
from decimal import Decimal

from backend.apps.settlement_management.models import ProjectSettlement, SettlementItem
from backend.apps.system_management.services import get_user_permission_codes
from backend.core.views import _permission_granted


@login_required
@require_http_methods(["POST"])
def settlement_item_review(request, item_id):
    """审核结算明细项（确认或驳回）"""
    item = get_object_or_404(SettlementItem, id=item_id)
    settlement = item.settlement
    permission_codes = get_user_permission_codes(request.user)
    
    # 检查权限：只有造价工程师或有管理权限的用户可以审核
    # TODO: 添加造价工程师权限检查
    if not (_permission_granted('settlement_center.settlement.manage', permission_codes) or
            request.user.roles.filter(code='cost_engineer').exists()):
        if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
            return JsonResponse({'success': False, 'message': '您没有权限审核此明细项'}, status=403)
        messages.error(request, '您没有权限审核此明细项')
        return redirect('settlement_pages:project_settlement_detail', settlement_id=settlement.id)
    
    # 检查结算单状态
    if settlement.status != 'draft':
        if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
            return JsonResponse({'success': False, 'message': '只有草稿状态的结算单才能审核明细项'}, status=400)
        messages.error(request, '只有草稿状态的结算单才能审核明细项')
        return redirect('settlement_pages:project_settlement_detail', settlement_id=settlement.id)
    
    action = request.POST.get('action')  # 'approve' 或 'reject'
    adjusted_amount = request.POST.get('adjusted_saving_amount')
    adjustment_reason = request.POST.get('adjustment_reason', '')
    review_comment = request.POST.get('review_comment', '')
    rejection_reason = request.POST.get('rejection_reason', '')
    
    if action == 'approve':
        # 确认明细项
        item.review_status = 'approved'
        item.reviewed_by = request.user
        item.reviewed_time = timezone.now()
        item.review_comment = review_comment
        
        # 如果有调整金额，保存调整后的金额
        if adjusted_amount:
            try:
                item.adjusted_saving_amount = Decimal(adjusted_amount)
                item.adjustment_reason = adjustment_reason
            except (ValueError, TypeError):
                item.adjusted_saving_amount = item.original_saving_amount
        
        item.save()
        
        # 重新计算结算单的节省金额汇总
        _recalculate_settlement_savings(settlement)
        
        if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
            return JsonResponse({
                'success': True,
                'message': '明细项已确认',
                'item_id': item.id,
                'review_status': item.review_status
            })
        messages.success(request, '明细项已确认')
        
    elif action == 'reject':
        # 驳回明细项
        item.review_status = 'rejected'
        item.reviewed_by = request.user
        item.reviewed_time = timezone.now()
        item.rejection_reason = rejection_reason
        item.save()
        
        # 重新计算结算单的节省金额汇总
        _recalculate_settlement_savings(settlement)
        
        if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
            return JsonResponse({
                'success': True,
                'message': '明细项已驳回',
                'item_id': item.id,
                'review_status': item.review_status
            })
        messages.success(request, '明细项已驳回')
    else:
        if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
            return JsonResponse({'success': False, 'message': '无效的操作'}, status=400)
        messages.error(request, '无效的操作')
    
    return redirect('settlement_pages:project_settlement_detail', settlement_id=settlement.id)


@login_required
@require_http_methods(["POST"])
def generate_items_from_opinions(request, settlement_id):
    """从Opinion生成结算明细项"""
    settlement = get_object_or_404(ProjectSettlement, id=settlement_id)
    permission_codes = get_user_permission_codes(request.user)
    
    # 检查权限
    if not _permission_granted('settlement_center.settlement.manage', permission_codes):
        if settlement.created_by != request.user:
            if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
                return JsonResponse({'success': False, 'message': '您没有权限执行此操作'}, status=403)
            messages.error(request, '您没有权限执行此操作')
            return redirect('settlement_pages:project_settlement_detail', settlement_id=settlement.id)
    
    # 检查结算单状态
    if settlement.status != 'draft':
        if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
            return JsonResponse({'success': False, 'message': '只有草稿状态的结算单才能重新生成明细项'}, status=400)
        messages.error(request, '只有草稿状态的结算单才能重新生成明细项')
        return redirect('settlement_pages:project_settlement_detail', settlement_id=settlement.id)
    
    # 获取时间范围（如果提供）
    period_start = request.POST.get('period_start')
    period_end = request.POST.get('period_end')
    
    # from backend.apps.production_quality.models import Opinion  # 已删除生产质量模块
    # from .views_pages import _generate_settlement_items_from_opinions  # 已删除生产质量模块
    
    # 生成明细项（已禁用：生产质量模块已删除）
    count = 0
    # count = _generate_settlement_items_from_opinions(settlement, request.user)
    
    if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
        return JsonResponse({
            'success': True,
            'message': f'成功生成 {count} 条结算明细项',
            'count': count
        })
    
    messages.success(request, f'成功生成 {count} 条结算明细项')
    return redirect('settlement_pages:project_settlement_detail', settlement_id=settlement.id)


def _recalculate_settlement_savings(settlement):
    """重新计算结算单的节省金额汇总"""
    from django.db.models import Sum
    
    # 原始节省总额（所有明细项的原始节省金额）
    original_total = settlement.items.aggregate(
        total=Sum('original_saving_amount')
    )['total'] or Decimal('0')
    settlement.original_total_saving = original_total
    
    # 审核后节省总额（仅计算已确认的明细项的调整后节省金额）
    reviewed_total = settlement.items.filter(review_status='approved').aggregate(
        total=Sum('adjusted_saving_amount')
    )['total']
    if not reviewed_total:
        reviewed_total = settlement.items.filter(review_status='approved').aggregate(
            total=Sum('original_saving_amount')
        )['total'] or Decimal('0')
    settlement.reviewed_total_saving = reviewed_total
    
    # 调整差额
    settlement.saving_adjustment_diff = reviewed_total - original_total
    
    # 服务费计算
    settlement.fee_base_amount = reviewed_total
    
    # 优先使用服务费结算方案，否则使用合同费率表
    if settlement.service_fee_scheme_id and settlement.service_fee_scheme.is_active:
        # 使用新的结算方案计算服务费
        settlement._calculate_service_fee_by_scheme()
    else:
        # 使用旧的费率表方式
        if settlement.contract_id:
            fee_rate = settlement._match_service_fee_rate(reviewed_total)
            if fee_rate:
                settlement.service_fee_rate = fee_rate.service_rate
                if hasattr(settlement.contract, 'base_service_fee'):
                    settlement.base_service_fee = settlement.contract.base_service_fee or Decimal('0')
        
        # 计算服务费金额
        if settlement.service_fee_rate and settlement.fee_base_amount:
            settlement.service_fee_amount = settlement.fee_base_amount * settlement.service_fee_rate
        else:
            settlement.service_fee_amount = Decimal('0')
    
    # 计算结算总金额
    settlement.total_settlement_amount = settlement.base_service_fee + settlement.service_fee_amount
    
    # 计算税额和含税金额
    if settlement.total_settlement_amount:
        settlement.tax_amount = settlement.total_settlement_amount * (settlement.tax_rate / 100)
        settlement.settlement_amount_tax = settlement.total_settlement_amount + settlement.tax_amount
    
    settlement.save(update_fields=[
        'original_total_saving', 'reviewed_total_saving', 'saving_adjustment_diff',
        'fee_base_amount', 'service_fee_rate', 'service_fee_amount',
        'base_service_fee', 'total_settlement_amount', 'tax_amount', 'settlement_amount_tax'
    ])

