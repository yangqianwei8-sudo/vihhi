"""
诉讼管理模块信号处理器
监听审批流程状态变化，自动更新案件和费用状态
"""
import logging
from django.db.models.signals import post_save
from django.dispatch import receiver
from django.contrib.contenttypes.models import ContentType
from django.utils import timezone

from backend.apps.workflow_engine.models import ApprovalInstance
from backend.apps.litigation_management.models import LitigationCase, LitigationExpense

logger = logging.getLogger(__name__)


@receiver(post_save, sender=ApprovalInstance)
def handle_approval_status_change(sender, instance, created, **kwargs):
    """
    监听审批实例状态变化，自动更新关联的案件或费用状态
    """
    # 只处理状态为"已通过"或"已驳回"的情况
    if instance.status not in ['approved', 'rejected']:
        return
    
    # 获取关联的业务对象
    content_type = instance.content_type
    object_id = instance.object_id
    
    try:
        # 判断对象类型并更新状态
        if content_type.model == 'litigationcase':
            # 案件审批
            case = LitigationCase.objects.get(id=object_id)
            
            if instance.workflow.code == 'litigation_case_registration':
                # 案件登记审批
                if instance.status == 'approved':
                    logger.info(f'案件登记审批通过：{case.case_number}')
                    # 案件可以正常使用，状态保持不变
                elif instance.status == 'rejected':
                    logger.info(f'案件登记审批驳回：{case.case_number}')
                    # 可以提示用户修改后重新提交
            
            elif instance.workflow.code == 'litigation_case_filing':
                # 立案申请审批
                if instance.status == 'approved':
                    logger.info(f'立案申请审批通过：{case.case_number}')
                    # 更新案件状态为"已立案"
                    if case.status == 'pending_filing':
                        case.status = 'filed'
                        if not case.filing_date:
                            case.filing_date = timezone.now().date()
                        case.save(update_fields=['status', 'filing_date'])
                        logger.info(f'案件状态已更新为"已立案"：{case.case_number}')
                elif instance.status == 'rejected':
                    logger.info(f'立案申请审批驳回：{case.case_number}')
                    # 状态保持"待立案"
        
        elif content_type.model == 'litigationexpense':
            # 费用报销审批
            expense = LitigationExpense.objects.get(id=object_id)
            
            if instance.workflow.code == 'litigation_expense_reimbursement':
                if instance.status == 'approved':
                    logger.info(f'费用报销审批通过：{expense.expense_name}')
                    # 更新费用报销状态为"已通过"
                    expense.reimbursement_status = 'approved'
                    expense.reimbursement_applied = True
                    expense.save(update_fields=['reimbursement_status', 'reimbursement_applied'])
                    logger.info(f'费用报销状态已更新为"已通过"：{expense.expense_name}')
                elif instance.status == 'rejected':
                    logger.info(f'费用报销审批驳回：{expense.expense_name}')
                    # 更新费用报销状态为"已驳回"
                    expense.reimbursement_status = 'rejected'
                    expense.save(update_fields=['reimbursement_status'])
                    logger.info(f'费用报销状态已更新为"已驳回"：{expense.expense_name}')
    
    except Exception as e:
        logger.error(f'处理审批状态变化失败: {str(e)}', exc_info=True)

