"""
合同审批服务
使用通用审批流程服务
"""
from typing import Optional
from backend.apps.workflow_engine.services.universal_approval import UniversalApprovalService
from backend.apps.workflow_engine.models import WorkflowTemplate
from backend.apps.contract_management.models import BusinessContract


class ContractApprovalService(UniversalApprovalService):
    """合同审批服务"""
    
    WORKFLOW_CODE = 'contract_approval'  # 主流程代码
    CONTENT_MODEL = BusinessContract
    
    def validate_before_submit(self, obj: BusinessContract, applicant):
        """
        提交审批前的验证
        
        Args:
            obj: 合同对象
            applicant: 申请人
            
        Raises:
            ValueError: 如果验证失败
        """
        # 检查合同状态：只有草稿或待审核状态的合同才能提交审批
        if obj.status not in ['draft', 'pending_review']:
            raise ValueError(f'合同状态为{obj.get_status_display()}，无法提交审批')
    
    def get_workflow(self, obj=None, action='submit', use_binding=True) -> Optional[WorkflowTemplate]:
        """
        获取审批流程模板（配置优先、兜底原逻辑）
        
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
            # 回退到客户管理审批流程
            try:
                return WorkflowTemplate.objects.get(code='customer_management_approval', status='active')
            except WorkflowTemplate.DoesNotExist:
                return None
