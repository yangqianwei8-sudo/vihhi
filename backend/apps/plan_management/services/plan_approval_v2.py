"""
计划管理审批流程服务 V2
基于通用审批流程服务 UniversalApprovalService
"""
import logging
from typing import Optional
from backend.apps.workflow_engine.services.universal_approval import UniversalApprovalService
from backend.apps.plan_management.models import Plan
from backend.apps.system_management.models import User

logger = logging.getLogger(__name__)


class PlanStartApprovalService(UniversalApprovalService):
    """计划启动审批服务"""
    
    WORKFLOW_CODE = 'plan_start_approval'
    CONTENT_MODEL = Plan
    
    def validate_before_submit(self, obj: Plan, applicant: User) -> None:
        """
        提交审批前的验证
        
        Args:
            obj: 计划对象
            applicant: 申请人
            
        Raises:
            ValueError: 如果验证失败
        """
        # 检查计划状态：只有草稿或已取消状态的计划可以提交审批
        if obj.status not in ['draft', 'cancelled']:
            raise ValueError(
                f'只有草稿或已取消状态的计划可以提交审批，当前状态：{obj.get_status_display()}'
            )
        
        # 检查验收标准（必填）
        if not obj.acceptance_criteria or not obj.acceptance_criteria.strip():
            raise ValueError(
                '提交审批前必须填写验收标准，明确说明如何判定计划完成。请在计划详情页编辑验收标准后再提交审批。'
            )
        
        # 检查计划基本信息
        if not obj.name or not obj.name.strip():
            raise ValueError('计划名称不能为空')
        
        if not obj.content or not obj.content.strip():
            raise ValueError('计划内容不能为空')
        
        if not obj.start_time or not obj.end_time:
            raise ValueError('计划开始时间和结束时间不能为空')
        
        if obj.start_time >= obj.end_time:
            raise ValueError('计划开始时间必须早于结束时间')
        
        # 检查负责人
        if not obj.responsible_person:
            raise ValueError('计划负责人不能为空')


class PlanCancelApprovalService(UniversalApprovalService):
    """计划取消审批服务"""
    
    WORKFLOW_CODE = 'plan_cancel_approval'
    CONTENT_MODEL = Plan
    
    def validate_before_submit(self, obj: Plan, applicant: User) -> None:
        """
        提交审批前的验证
        
        Args:
            obj: 计划对象
            applicant: 申请人
            
        Raises:
            ValueError: 如果验证失败
        """
        # 检查计划状态：只有执行中状态的计划可以提交取消审批
        if obj.status != 'in_progress':
            raise ValueError(
                f'只有执行中状态的计划可以提交取消审批，当前状态：{obj.get_status_display()}'
            )

