"""
计划管理审批流程服务
集成审批流程引擎，实现计划启动审批、取消审批等功能
"""
import logging
from typing import Optional
from django.utils import timezone
from django.contrib.contenttypes.models import ContentType
from django.db import transaction

from backend.apps.workflow_engine.models import WorkflowTemplate, ApprovalInstance
from backend.apps.workflow_engine.services import ApprovalEngine
from backend.apps.plan_management.models import Plan

logger = logging.getLogger(__name__)


class PlanApprovalService:
    """计划管理审批服务"""
    
    # 审批流程代码常量
    PLAN_START_WORKFLOW_CODE = 'plan_start_approval'
    PLAN_CANCEL_WORKFLOW_CODE = 'plan_cancel_approval'
    
    @staticmethod
    def get_workflow_by_code(code: str) -> Optional[WorkflowTemplate]:
        """根据代码获取审批流程模板"""
        try:
            return WorkflowTemplate.objects.get(code=code, status='active')
        except WorkflowTemplate.DoesNotExist:
            logger.warning(f'审批流程模板不存在或未启用: {code}')
            return None
    
    @staticmethod
    @transaction.atomic
    def submit_start_approval(plan: Plan, applicant, comment: str = '') -> Optional[ApprovalInstance]:
        """
        提交计划启动审批
        
        Args:
            plan: 计划对象
            applicant: 申请人
            comment: 申请说明
        
        Returns:
            ApprovalInstance: 审批实例，如果流程未配置则返回None
        """
        # 检查状态：只有草稿状态的计划可以提交启动审批
        if plan.status != 'draft':
            logger.warning(f'计划 {plan.plan_number} 状态为 {plan.status}，不能提交启动审批')
            return None
        
        # 检查是否已有审批实例
        existing_instance = ApprovalInstance.objects.filter(
            content_type=ContentType.objects.get_for_model(plan),
            object_id=plan.id,
            workflow__code=PlanApprovalService.PLAN_START_WORKFLOW_CODE,
            status__in=['pending', 'in_progress']
        ).first()
        
        if existing_instance:
            logger.warning(f'计划 {plan.plan_number} 已有启动审批实例: {existing_instance.instance_number}')
            return existing_instance
        
        # 获取审批流程模板
        workflow = PlanApprovalService.get_workflow_by_code(
            PlanApprovalService.PLAN_START_WORKFLOW_CODE
        )
        
        if not workflow:
            logger.warning(f'计划启动审批流程未配置，跳过审批')
            return None
        
        # 启动审批流程
        try:
            instance = ApprovalEngine.start_approval(
                workflow=workflow,
                content_object=plan,
                applicant=applicant,
                comment=comment or f'申请启动计划：{plan.plan_number} - {plan.name}'
            )
            
            logger.info(f'计划 {plan.plan_number} 已提交启动审批，审批实例: {instance.instance_number}')
            return instance
            
        except Exception as e:
            logger.error(f'提交计划启动审批失败: {str(e)}', exc_info=True)
            raise
    
    @staticmethod
    @transaction.atomic
    def submit_cancel_approval(plan: Plan, applicant, comment: str = '') -> Optional[ApprovalInstance]:
        """
        提交计划取消审批
        
        Args:
            plan: 计划对象
            applicant: 申请人
            comment: 申请说明
        
        Returns:
            ApprovalInstance: 审批实例，如果流程未配置则返回None
        """
        # 检查状态：只有执行中状态的计划可以提交取消审批
        if plan.status != 'in_progress':
            logger.warning(f'计划 {plan.plan_number} 状态为 {plan.status}，不能提交取消审批')
            return None
        
        # 检查是否已有审批实例
        existing_instance = ApprovalInstance.objects.filter(
            content_type=ContentType.objects.get_for_model(plan),
            object_id=plan.id,
            workflow__code=PlanApprovalService.PLAN_CANCEL_WORKFLOW_CODE,
            status__in=['pending', 'in_progress']
        ).first()
        
        if existing_instance:
            logger.warning(f'计划 {plan.plan_number} 已有取消审批实例: {existing_instance.instance_number}')
            return existing_instance
        
        # 获取审批流程模板
        workflow = PlanApprovalService.get_workflow_by_code(
            PlanApprovalService.PLAN_CANCEL_WORKFLOW_CODE
        )
        
        if not workflow:
            logger.warning(f'计划取消审批流程未配置，跳过审批')
            return None
        
        # 启动审批流程
        try:
            instance = ApprovalEngine.start_approval(
                workflow=workflow,
                content_object=plan,
                applicant=applicant,
                comment=comment or f'申请取消计划：{plan.plan_number} - {plan.name}'
            )
            
            logger.info(f'计划 {plan.plan_number} 已提交取消审批，审批实例: {instance.instance_number}')
            return instance
            
        except Exception as e:
            logger.error(f'提交计划取消审批失败: {str(e)}', exc_info=True)
            raise
    
    @staticmethod
    def get_plan_approval_instance(plan: Plan, workflow_code: str = None) -> Optional[ApprovalInstance]:
        """
        获取计划的审批实例
        
        Args:
            plan: 计划对象
            workflow_code: 流程代码（可选，如果不指定则返回最新的）
        
        Returns:
            ApprovalInstance: 审批实例
        """
        try:
            query = ApprovalInstance.objects.filter(
                content_type=ContentType.objects.get_for_model(plan),
                object_id=plan.id
            )
            
            if workflow_code:
                query = query.filter(workflow__code=workflow_code)
            
            return query.order_by('-created_time').first()
        except Exception:
            return None
    
    @staticmethod
    def check_approval_status(instance: ApprovalInstance) -> dict:
        """
        检查审批状态
        
        Returns:
            dict: {
                'status': 'pending'|'approved'|'rejected',
                'can_submit': bool,
                'message': str
            }
        """
        if not instance:
            return {
                'status': None,
                'can_submit': True,
                'message': '未提交审批'
            }
        
        if instance.status == 'approved':
            return {
                'status': 'approved',
                'can_submit': False,
                'message': '审批已通过'
            }
        elif instance.status == 'rejected':
            return {
                'status': 'rejected',
                'can_submit': True,
                'message': '审批已驳回，可以重新提交'
            }
        elif instance.status == 'pending':
            return {
                'status': 'pending',
                'can_submit': False,
                'message': '审批中，请等待审批结果'
            }
        else:
            return {
                'status': instance.status,
                'can_submit': True,
                'message': f'审批状态：{instance.get_status_display()}'
            }
    
    @staticmethod
    def handle_approval_result(instance: ApprovalInstance, plan: Plan):
        """
        处理审批结果，更新计划状态
        
        Args:
            instance: 审批实例
            plan: 计划对象
        """
        if instance.status == 'approved':
            if instance.workflow.code == PlanApprovalService.PLAN_START_WORKFLOW_CODE:
                # 启动审批通过，将计划状态改为 published
                if plan.status == 'draft':
                    plan.transition_to('published', user=instance.applicant)
                    logger.info(f'计划 {plan.plan_number} 启动审批通过，状态已更新为 published')
                    
                    # P2-3: 公司计划发布后，通知员工创建个人计划
                    if plan.level == 'company':
                        from backend.apps.plan_management.notifications import notify_company_plan_published
                        notify_company_plan_published(plan)
            
            elif instance.workflow.code == PlanApprovalService.PLAN_CANCEL_WORKFLOW_CODE:
                # 取消审批通过，将计划状态改为 cancelled
                if plan.status == 'in_progress':
                    old_status = plan.status
                    plan.status = 'cancelled'
                    plan.save(update_fields=['status'])
                    
                    # 创建状态变更日志
                    from backend.apps.plan_management.models import PlanStatusLog
                    PlanStatusLog.objects.create(
                        plan=plan,
                        old_status=old_status,
                        new_status='cancelled',
                        changed_by=instance.applicant,
                        change_reason=f"审批通过取消请求：{instance.final_comment or '无说明'}"
                    )
                    logger.info(f'计划 {plan.plan_number} 取消审批通过，状态已更新为 cancelled')
        
        elif instance.status == 'rejected':
            # 审批驳回，记录日志但不改变计划状态
            logger.info(f'计划 {plan.plan_number} 审批被驳回')
    
    @staticmethod
    def get_plan_approval_info(plan: Plan) -> dict:
        """
        获取计划的审批信息（包括审批引擎和 PlanDecision）
        
        Args:
            plan: 计划对象
        
        Returns:
            dict: {
                'has_pending_start': bool,
                'has_pending_cancel': bool,
                'start_approval_instance': ApprovalInstance | None,
                'cancel_approval_instance': ApprovalInstance | None,
                'pending_decisions': QuerySet,
            }
        """
        from django.contrib.contenttypes.models import ContentType
        from backend.apps.workflow_engine.models import ApprovalInstance
        from backend.apps.plan_management.models import PlanDecision
        
        plan_content_type = ContentType.objects.get_for_model(Plan)
        
        # 获取审批引擎的审批实例
        start_approval_instance = ApprovalInstance.objects.filter(
            content_type=plan_content_type,
            object_id=plan.id,
            workflow__code=PlanApprovalService.PLAN_START_WORKFLOW_CODE,
            status__in=['pending', 'in_progress']
        ).first()
        
        cancel_approval_instance = ApprovalInstance.objects.filter(
            content_type=plan_content_type,
            object_id=plan.id,
            workflow__code=PlanApprovalService.PLAN_CANCEL_WORKFLOW_CODE,
            status__in=['pending', 'in_progress']
        ).first()
        
        # 获取 PlanDecision（向后兼容）
        pending_decisions = PlanDecision.objects.filter(
            plan=plan,
            decided_at__isnull=True
        )
        
        has_pending_start = start_approval_instance is not None or pending_decisions.filter(request_type='start').exists()
        has_pending_cancel = cancel_approval_instance is not None or pending_decisions.filter(request_type='cancel').exists()
        
        return {
            'has_pending_start': has_pending_start,
            'has_pending_cancel': has_pending_cancel,
            'start_approval_instance': start_approval_instance,
            'cancel_approval_instance': cancel_approval_instance,
            'pending_decisions': pending_decisions,
        }

