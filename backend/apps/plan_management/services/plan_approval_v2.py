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
        logger.info(f'开始验证计划提交审批: plan_id={obj.id}, status={obj.status}, name={obj.name}')
        
        # 检查计划状态：只有草稿或已取消状态的计划可以提交审批
        if obj.status not in ['draft', 'cancelled']:
            error_msg = f'只有草稿或已取消状态的计划可以提交审批，当前状态：{obj.get_status_display()}'
            logger.warning(f'验证失败（状态）: {error_msg}, plan_id={obj.id}')
            raise ValueError(error_msg)
        
        # 检查计划基本信息
        if not obj.name or not obj.name.strip():
            error_msg = '计划名称不能为空'
            logger.warning(f'验证失败（名称）: {error_msg}, plan_id={obj.id}')
            raise ValueError(error_msg)
        
        if not obj.content or not obj.content.strip():
            error_msg = '计划内容不能为空'
            logger.warning(f'验证失败（内容）: {error_msg}, plan_id={obj.id}')
            raise ValueError(error_msg)
        
        if not obj.start_time:
            error_msg = '计划开始时间不能为空'
            logger.warning(f'验证失败（开始时间）: {error_msg}, plan_id={obj.id}')
            raise ValueError(error_msg)
        
        if not obj.end_time:
            error_msg = '计划结束时间不能为空'
            logger.warning(f'验证失败（结束时间）: {error_msg}, plan_id={obj.id}')
            raise ValueError(error_msg)
        
        if obj.start_time >= obj.end_time:
            error_msg = '计划开始时间必须早于结束时间'
            logger.warning(f'验证失败（时间逻辑）: {error_msg}, plan_id={obj.id}, start_time={obj.start_time}, end_time={obj.end_time}')
            raise ValueError(error_msg)
        
        # 检查负责人
        if not obj.responsible_person:
            error_msg = '计划负责人不能为空'
            logger.warning(f'验证失败（负责人）: {error_msg}, plan_id={obj.id}')
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

