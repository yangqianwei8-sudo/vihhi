"""
商机审批服务
使用通用审批流程服务
"""
from typing import Optional
from backend.apps.workflow_engine.services.universal_approval import UniversalApprovalService
from backend.apps.workflow_engine.models import WorkflowTemplate
from backend.apps.opportunity_management.models import BusinessOpportunity


class OpportunityApprovalService(UniversalApprovalService):
    """
    商机审批服务
    
    支持流程模板绑定配置（WorkflowBinding）：
    - 无绑定配置时，使用默认模板 'opportunity_approval'
    - 有绑定配置时，优先使用配置的模板
    - 历史审批实例不受影响，仍使用原模板
    - 审批通过后会更新商机状态（approval_status='approved'），此逻辑不受模板切换影响
    """
    WORKFLOW_CODE = 'opportunity_approval'  # 兜底模板代码
    CONTENT_MODEL = BusinessOpportunity
    
    def validate_before_submit(self, obj: BusinessOpportunity, applicant):
        """
        提交审批前的验证
        
        Args:
            obj: 商机对象
            applicant: 申请人
            
        Raises:
            ValueError: 如果验证失败
        """
        # 检查商机是否已删除
        if not obj.is_active:
            raise ValueError('该商机已删除，无法提交审批')
    
    def get_workflow(self, obj=None, action='submit', use_binding=True) -> Optional[WorkflowTemplate]:
        """
        获取审批流程模板（配置优先、兜底原逻辑）
        
        优先级顺序：
        1. WorkflowBinding 配置（如果启用且存在）
        2. 主流程代码 'opportunity_approval'
        3. 通过 applicable_models 查找（回退逻辑）
        
        Args:
            obj: 业务对象（可选，如果提供则尝试从绑定配置获取）
            action: 操作类型，默认为 'submit'
            use_binding: 是否使用绑定配置，默认为 True
        
        Returns:
            WorkflowTemplate: 审批流程模板，如果未配置则返回 None
        """
        # 如果启用绑定配置且提供了业务对象，先尝试从绑定配置获取
        if use_binding and obj is not None:
            workflow = self.get_workflow_from_binding(obj, action)
            if workflow:
                return workflow
        
        # 兜底：优先使用主流程代码
        try:
            return WorkflowTemplate.objects.get(code=self.WORKFLOW_CODE, status='active')
        except WorkflowTemplate.DoesNotExist:
            # 回退：通过 applicable_models 查找
            workflow = WorkflowTemplate.objects.filter(
                status='active',
                applicable_models__contains=['businessopportunity']
            ).first()
            
            return workflow
    
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
            
            if not hasattr(content_obj, 'approval_status'):
                logger.warning(f'商机对象无 approval_status 字段: #{instance.object_id}')
                return
            
            if approval_status == 'approved':
                # 更新审批人信息
                last_record = instance.records.filter(result='approved').order_by('-approval_time').first()
                if last_record and hasattr(content_obj, 'approver'):
                    content_obj.approver = last_record.approver
                if hasattr(content_obj, 'approved_time'):
                    content_obj.approved_time = timezone.now()
                
                content_obj.approval_status = 'approved'
                content_obj.save()
                logger.info(f'商机审批通过: #{instance.object_id}')
            elif approval_status == 'rejected':
                content_obj.approval_status = 'rejected'
                content_obj.save()
                logger.info(f'商机审批驳回: #{instance.object_id}')
        except Exception as e:
            logger.error(f'处理商机审批结果异常: {str(e)}', exc_info=True)
