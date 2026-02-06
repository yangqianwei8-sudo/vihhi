"""
印章借用审批服务
使用通用审批流程服务
"""
from backend.apps.workflow_engine.services.universal_approval import UniversalApprovalService
from backend.apps.administrative_management.models import SealBorrowing


class SealBorrowingApprovalService(UniversalApprovalService):
    """
    印章借用审批服务
    
    支持流程模板绑定配置（WorkflowBinding）：
    - 无绑定配置时，使用默认模板 'seal_borrowing_approval'
    - 有绑定配置时，优先使用配置的模板
    - 历史审批实例不受影响，仍使用原模板
    - 审批通过后会更新印章状态（seal.status='borrowed'），此逻辑不受模板切换影响
    """
    WORKFLOW_CODE = 'seal_borrowing_approval'  # 兜底模板代码
    CONTENT_MODEL = SealBorrowing
    
    def validate_before_submit(self, obj: SealBorrowing, applicant):
        """
        提交审批前的验证
        
        Args:
            obj: 印章借用对象
            applicant: 申请人
            
        Raises:
            ValueError: 如果验证失败
        """
        # 检查印章借用状态
        if obj.status != 'pending':
            raise ValueError('只有待审批状态的印章借用申请可以提交审批')
        
        # 检查必填字段
        if not obj.seal:
            raise ValueError('必须选择要借用的印章')
        
        if not obj.borrowing_reason:
            raise ValueError('借用事由不能为空')
        
        if not obj.expected_return_date:
            raise ValueError('预计归还日期不能为空')
        
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
        import logging
        
        logger = logging.getLogger(__name__)
        
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
                content_obj.status = 'approved'
                
                # 更新印章状态
                if hasattr(content_obj, 'seal') and content_obj.seal:
                    if hasattr(content_obj.seal, 'status'):
                        content_obj.seal.status = 'borrowed'
                        content_obj.seal.save(update_fields=['status'])
                
                content_obj.save()
                logger.info(f'印章借用审批通过: #{instance.object_id}')
            elif approval_status == 'rejected':
                content_obj.status = 'rejected'
                content_obj.save()
                logger.info(f'印章借用审批驳回: #{instance.object_id}')
        except Exception as e:
            logger.error(f'处理印章借用审批结果异常: {str(e)}', exc_info=True)
