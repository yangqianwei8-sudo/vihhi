"""
用印申请审批服务
使用通用审批流程服务
"""
from backend.apps.workflow_engine.services.universal_approval import UniversalApprovalService
from backend.apps.administrative_management.models import SealUsage


class SealUsageApprovalService(UniversalApprovalService):
    """
    用印申请审批服务
    
    支持流程模板绑定配置（WorkflowBinding）：
    - 无绑定配置时，使用默认模板 'seal_usage_approval'
    - 有绑定配置时，优先使用配置的模板
    - 历史审批实例不受影响，仍使用原模板
    """
    WORKFLOW_CODE = 'seal_usage_approval'  # 兜底模板代码
    CONTENT_MODEL = SealUsage
    
    def validate_before_submit(self, obj: SealUsage, applicant):
        """
        提交审批前的验证
        
        Args:
            obj: 用印申请对象
            applicant: 申请人
            
        Raises:
            ValueError: 如果验证失败
        """
        # 检查用印申请状态
        if obj.status != 'pending':
            raise ValueError('只有待审批状态的用印申请可以提交审批')
        
        # 检查必填字段
        if not obj.seal:
            raise ValueError('必须选择要使用的印章')
        
        if not obj.usage_reason:
            raise ValueError('用印事由不能为空')
        
        # 检查申请人是否有部门（部门经理审批需要）
        if not hasattr(applicant, 'department') or not applicant.department:
            raise ValueError('申请人必须属于某个部门才能提交审批')
    
    def handle_approval_result(self, instance, approval_status: str):
        """
        处理审批结果（用印申请审批通过/驳回仅记录日志，不更新状态）
        
        Args:
            instance: 审批实例
            approval_status: 审批状态 ('approved' 或 'rejected')
        """
        import logging
        
        logger = logging.getLogger(__name__)
        
        try:
            content_obj = instance.content_type.get_object_for_this_type(id=instance.object_id)
            
            if approval_status == 'approved':
                logger.info(f'用印申请 {content_obj.usage_number} 审批通过')
            elif approval_status == 'rejected':
                logger.info(f'用印申请 {content_obj.usage_number} 审批驳回')
        except Exception as e:
            logger.error(f'处理用印申请审批结果异常: {str(e)}', exc_info=True)
