"""
诉讼管理审批视图
"""
import logging
from django.contrib.auth.decorators import login_required
from django.shortcuts import render, get_object_or_404, redirect
from django.contrib import messages
from django.db.models import Q

from backend.apps.system_management.services import get_user_permission_codes
from backend.core.views import _permission_granted
from backend.apps.workflow_engine.models import ApprovalInstance
from backend.apps.workflow_engine.services import ApprovalEngine
from backend.apps.litigation_management.models import LitigationCase, LitigationExpense
from .services_approval import LitigationApprovalService
from .views_pages import _context

logger = logging.getLogger(__name__)


@login_required
def case_submit_approval(request, case_id):
    """提交案件审批"""
    permission_codes = get_user_permission_codes(request.user)
    
    if not _permission_granted('litigation_management.case.create', permission_codes):
        messages.error(request, '您没有权限提交案件审批')
        return redirect('litigation_pages:case_detail', case_id=case_id)
    
    case = get_object_or_404(LitigationCase, id=case_id)
    
    # 检查是否已有审批实例
    existing_instance = LitigationApprovalService.get_case_approval_instance(case)
    approval_status = LitigationApprovalService.check_approval_status(existing_instance)
    
    if request.method == 'POST':
        if not approval_status['can_submit']:
            messages.warning(request, approval_status['message'])
            return redirect('litigation_pages:case_detail', case_id=case_id)
        
        try:
            comment = request.POST.get('comment', '')
            approval_instance = LitigationApprovalService.submit_case_for_approval(
                case=case,
                applicant=request.user,
                comment=comment or f'申请审批案件：{case.case_number} - {case.case_name}'
            )
            
            if approval_instance:
                logger.info(f'用户 {request.user.username} 提交了案件审批 {case.case_number}，审批实例：{approval_instance.instance_number}')
                messages.success(request, f'案件审批已提交！审批实例：{approval_instance.instance_number}')
            else:
                messages.info(request, '该案件不需要审批')
            
            return redirect('litigation_pages:case_detail', case_id=case_id)
            
        except Exception as e:
            logger.error(f'提交案件审批失败: {str(e)}', exc_info=True)
            messages.error(request, f'提交审批失败：{str(e)}')
    
    context = _context(
        "提交案件审批",
        "📝",
        f"案件：{case.case_number} - {case.case_name}",
        request=request
    )
    
    context.update({
        'case': case,
        'approval_status': approval_status,
        'existing_instance': existing_instance,
    })
    
    return render(request, 'litigation_management/case_submit_approval.html', context)


@login_required
def case_submit_filing(request, case_id):
    """提交立案申请审批"""
    permission_codes = get_user_permission_codes(request.user)
    
    if not _permission_granted('litigation_management.process.manage', permission_codes):
        messages.error(request, '您没有权限提交立案申请')
        return redirect('litigation_pages:case_detail', case_id=case_id)
    
    case = get_object_or_404(LitigationCase, id=case_id)
    
    if request.method == 'POST':
        try:
            comment = request.POST.get('comment', '')
            approval_instance = LitigationApprovalService.submit_filing_for_approval(
                case=case,
                applicant=request.user,
                comment=comment or f'申请立案：{case.case_number} - {case.case_name}'
            )
            
            if approval_instance:
                logger.info(f'用户 {request.user.username} 提交了立案申请 {case.case_number}，审批实例：{approval_instance.instance_number}')
                messages.success(request, f'立案申请已提交！审批实例：{approval_instance.instance_number}')
            else:
                messages.info(request, '立案审批流程未配置')
            
            return redirect('litigation_pages:case_detail', case_id=case_id)
            
        except Exception as e:
            logger.error(f'提交立案申请失败: {str(e)}', exc_info=True)
            messages.error(request, f'提交立案申请失败：{str(e)}')
    
    context = _context(
        "提交立案申请",
        "📋",
        f"案件：{case.case_number} - {case.case_name}",
        request=request
    )
    
    context.update({
        'case': case,
    })
    
    return render(request, 'litigation_management/case_submit_filing.html', context)


@login_required
def expense_submit_reimbursement(request, expense_id):
    """提交费用报销审批"""
    permission_codes = get_user_permission_codes(request.user)
    
    if not _permission_granted('litigation_management.expense.manage', permission_codes):
        messages.error(request, '您没有权限提交费用报销')
        return redirect('litigation_pages:expense_detail', expense_id=expense_id)
    
    expense = get_object_or_404(LitigationExpense, id=expense_id)
    
    # 检查是否已有审批实例
    existing_instance = LitigationApprovalService.get_expense_approval_instance(expense)
    approval_status = LitigationApprovalService.check_approval_status(existing_instance)
    
    if request.method == 'POST':
        if not approval_status['can_submit']:
            messages.warning(request, approval_status['message'])
            return redirect('litigation_pages:expense_detail', expense_id=expense_id)
        
        try:
            comment = request.POST.get('comment', '')
            approval_instance = LitigationApprovalService.submit_expense_reimbursement_for_approval(
                expense=expense,
                applicant=request.user,
                comment=comment or f'申请费用报销：{expense.expense_name}，金额：¥{expense.amount}'
            )
            
            if approval_instance:
                logger.info(f'用户 {request.user.username} 提交了费用报销审批 {expense.expense_name}，审批实例：{approval_instance.instance_number}')
                messages.success(request, f'费用报销申请已提交！审批实例：{approval_instance.instance_number}')
            else:
                messages.info(request, '费用报销审批流程未配置')
            
            return redirect('litigation_pages:expense_detail', expense_id=expense_id)
            
        except Exception as e:
            logger.error(f'提交费用报销失败: {str(e)}', exc_info=True)
            messages.error(request, f'提交费用报销失败：{str(e)}')
    
    context = _context(
        "提交费用报销",
        "💳",
        f"费用：{expense.expense_name}",
        request=request
    )
    
    context.update({
        'expense': expense,
        'approval_status': approval_status,
        'existing_instance': existing_instance,
    })
    
    return render(request, 'litigation_management/expense_submit_reimbursement.html', context)

