"""
借款审批服务
使用通用审批流程服务
"""
import logging
from backend.apps.workflow_engine.services.universal_approval import UniversalApprovalService
from backend.apps.administrative_management.models import LoanApplication

logger = logging.getLogger(__name__)


class LoanApprovalService(UniversalApprovalService):
    """借款审批服务"""
    
    WORKFLOW_CODE = 'loan_approval'
    CONTENT_MODEL = LoanApplication
    
    def validate_before_submit(self, obj: LoanApplication, applicant):
        """
        提交审批前的验证
        
        Args:
            obj: 借款申请对象
            applicant: 申请人
            
        Raises:
            ValueError: 如果验证失败
        """
        # 检查借款申请状态
        if obj.status != 'draft' and obj.status != 'pending_approval':
            raise ValueError('只有草稿或待审批状态的借款申请可以提交审批')
        
        # 检查必填字段
        if not obj.loan_amount or obj.loan_amount <= 0:
            raise ValueError('借款金额必须大于0')
        
        if not obj.loan_date:
            raise ValueError('借款日期不能为空')
        
        if not obj.loan_reason:
            raise ValueError('借款事由不能为空')
        
        # 检查申请人是否有部门（部门经理审批需要）
        if not hasattr(applicant, 'department') or not applicant.department:
            raise ValueError('申请人必须属于某个部门才能提交审批')
    
    def handle_approval_result(self, instance, approval_status: str):
        """
        处理审批结果
        
        Args:
            instance: 审批实例
            approval_status: 审批状态 ('approved' 或 'rejected')
        """
        from backend.apps.workflow_engine.models import ApprovalInstance
        from django.utils import timezone
        
        try:
            content_obj = instance.content_type.get_object_for_this_type(id=instance.object_id)
            
            if approval_status == 'approved':
                # 更新审批人信息
                last_record = instance.records.filter(result='approved').order_by('-approval_time').first()
                if last_record and hasattr(content_obj, 'approver'):
                    content_obj.approver = last_record.approver
                if hasattr(content_obj, 'approved_time'):
                    content_obj.approved_time = timezone.now()
                
                # 更新状态
                status_choices = dict(getattr(content_obj, 'STATUS_CHOICES', []))
                if 'approved' in status_choices:
                    content_obj.status = 'approved'
                
                content_obj.save()
                logger.info(f'借款申请审批通过: #{instance.object_id}')
            elif approval_status == 'rejected':
                status_choices = dict(getattr(content_obj, 'STATUS_CHOICES', []))
                if 'rejected' in status_choices:
                    content_obj.status = 'rejected'
                elif 'pending_approval' in status_choices:
                    content_obj.status = 'pending_approval'
                
                content_obj.save()
                logger.info(f'借款申请审批驳回: #{instance.object_id}')
        except Exception as e:
            logger.error(f'处理借款审批结果异常: {str(e)}', exc_info=True)