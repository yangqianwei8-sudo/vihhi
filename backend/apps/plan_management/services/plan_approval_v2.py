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
        提交审批前的验证（仅检查状态，字段验证在创建/编辑时完成）
        
        Args:
            obj: 计划对象
            applicant: 申请人
            
        Raises:
            ValueError: 如果验证失败
        """
        logger.info(f'开始验证计划提交审批: plan_id={obj.id}, status={obj.status}, name={obj.name}')
        
        # 检查计划状态：只有草稿或已取消状态的计划可以提交审批
        if obj.status not in ['draft', 'cancelled']:
            error_msg = f'只有草稿或已取消状态的计划可以提交审批，当前状态：{obj.get_status_display()}'
            logger.warning(f'验证失败（状态）: {error_msg}, plan_id={obj.id}')
            raise ValueError(error_msg)
        
        logger.info(f'计划验证通过: plan_id={obj.id}')


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

