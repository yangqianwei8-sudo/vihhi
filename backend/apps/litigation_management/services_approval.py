"""
诉讼管理审批流程服务
集成审批流程引擎，实现案件审批、费用审批等功能
"""
import logging
from typing import Optional
from django.utils import timezone
from django.contrib.contenttypes.models import ContentType
from django.db import transaction

from backend.apps.workflow_engine.models import WorkflowTemplate, ApprovalInstance
from backend.apps.workflow_engine.services import ApprovalEngine
from backend.apps.litigation_management.models import LitigationCase, LitigationExpense

logger = logging.getLogger(__name__)


class LitigationApprovalService:
    """诉讼管理审批服务"""
    
    # 审批流程代码常量
    CASE_REGISTRATION_WORKFLOW_CODE = 'litigation_case_registration'
    CASE_FILING_WORKFLOW_CODE = 'litigation_case_filing'
    EXPENSE_REIMBURSEMENT_WORKFLOW_CODE = 'litigation_expense_reimbursement'
    SETTLEMENT_AGREEMENT_WORKFLOW_CODE = 'litigation_settlement_agreement'
    WITHDRAWAL_APPLICATION_WORKFLOW_CODE = 'litigation_withdrawal_application'
    EXECUTION_APPLICATION_WORKFLOW_CODE = 'litigation_execution_application'
    
    @staticmethod
    def get_workflow_by_code(code: str) -> Optional[WorkflowTemplate]:
        """根据代码获取审批流程模板"""
        try:
            return WorkflowTemplate.objects.get(code=code, status='active')
        except WorkflowTemplate.DoesNotExist:
            logger.warning(f'审批流程模板不存在或未启用: {code}')
            return None
    
    @staticmethod
    def should_require_case_approval(case: LitigationCase) -> bool:
        """判断案件是否需要审批"""
        # 重大案件需要审批：金额超过50万或特定类型
        if case.litigation_amount and case.litigation_amount >= 500000:
            return True
        
        # 特定类型的案件需要审批
        critical_types = ['ip_dispute', 'tort_dispute']  # 知识产权、侵权纠纷
        if case.case_type in critical_types:
            return True
        
        return False
    
    @staticmethod
    @transaction.atomic
    def submit_case_for_approval(case: LitigationCase, applicant, comment: str = '') -> Optional[ApprovalInstance]:
        """
        提交案件登记审批
        
        Args:
            case: 诉讼案件对象
            applicant: 申请人
            comment: 申请说明
        
        Returns:
            ApprovalInstance: 审批实例，如果不需要审批则返回None
        """
        # 检查是否需要审批
        if not LitigationApprovalService.should_require_case_approval(case):
            logger.info(f'案件 {case.case_number} 不需要审批')
            return None
        
        # 检查是否已有审批实例
        existing_instance = ApprovalInstance.objects.filter(
            content_type=ContentType.objects.get_for_model(case),
            object_id=case.id,
            status__in=['draft', 'pending']
        ).first()
        
        if existing_instance:
            logger.warning(f'案件 {case.case_number} 已有审批实例: {existing_instance.instance_number}')
            return existing_instance
        
        # 获取审批流程模板
        workflow = LitigationApprovalService.get_workflow_by_code(
            LitigationApprovalService.CASE_REGISTRATION_WORKFLOW_CODE
        )
        
        if not workflow:
            logger.warning(f'案件登记审批流程未配置，跳过审批')
            return None
        
        # 启动审批流程
        try:
            instance = ApprovalEngine.start_approval(
                workflow=workflow,
                content_object=case,
                applicant=applicant,
                comment=comment or f'申请审批案件：{case.case_number} - {case.case_name}'
            )
            
            logger.info(f'案件 {case.case_number} 已提交审批，审批实例: {instance.instance_number}')
            return instance
            
        except Exception as e:
            logger.error(f'提交案件审批失败: {str(e)}', exc_info=True)
            raise
    
    @staticmethod
    @transaction.atomic
    def submit_filing_for_approval(case: LitigationCase, applicant, comment: str = '') -> Optional[ApprovalInstance]:
        """
        提交立案申请审批
        
        Args:
            case: 诉讼案件对象
            applicant: 申请人
            comment: 申请说明
        
        Returns:
            ApprovalInstance: 审批实例
        """
        # 检查是否已有审批实例
        existing_instance = ApprovalInstance.objects.filter(
            content_type=ContentType.objects.get_for_model(case),
            object_id=case.id,
            workflow__code=LitigationApprovalService.CASE_FILING_WORKFLOW_CODE,
            status__in=['draft', 'pending']
        ).first()
        
        if existing_instance:
            logger.warning(f'案件 {case.case_number} 立案审批已有审批实例')
            return existing_instance
        
        # 获取审批流程模板
        workflow = LitigationApprovalService.get_workflow_by_code(
            LitigationApprovalService.CASE_FILING_WORKFLOW_CODE
        )
        
        if not workflow:
            logger.warning(f'立案申请审批流程未配置，跳过审批')
            return None
        
        # 启动审批流程
        try:
            instance = ApprovalEngine.start_approval(
                workflow=workflow,
                content_object=case,
                applicant=applicant,
                comment=comment or f'申请立案审批：{case.case_number} - {case.case_name}'
            )
            
            logger.info(f'案件 {case.case_number} 立案申请已提交审批，审批实例: {instance.instance_number}')
            return instance
            
        except Exception as e:
            logger.error(f'提交立案审批失败: {str(e)}', exc_info=True)
            raise
    
    @staticmethod
    @transaction.atomic
    def submit_expense_reimbursement_for_approval(expense: LitigationExpense, applicant, comment: str = '') -> Optional[ApprovalInstance]:
        """
        提交费用报销审批
        
        Args:
            expense: 费用对象
            applicant: 申请人
            comment: 申请说明
        
        Returns:
            ApprovalInstance: 审批实例
        """
        # 检查是否已有审批实例
        existing_instance = ApprovalInstance.objects.filter(
            content_type=ContentType.objects.get_for_model(expense),
            object_id=expense.id,
            workflow__code=LitigationApprovalService.EXPENSE_REIMBURSEMENT_WORKFLOW_CODE,
            status__in=['draft', 'pending']
        ).first()
        
        if existing_instance:
            logger.warning(f'费用 {expense.expense_name} 报销审批已有审批实例')
            return existing_instance
        
        # 获取审批流程模板
        workflow = LitigationApprovalService.get_workflow_by_code(
            LitigationApprovalService.EXPENSE_REIMBURSEMENT_WORKFLOW_CODE
        )
        
        if not workflow:
            logger.warning(f'费用报销审批流程未配置，跳过审批')
            return None
        
        # 启动审批流程
        try:
            instance = ApprovalEngine.start_approval(
                workflow=workflow,
                content_object=expense,
                applicant=applicant,
                comment=comment or f'申请费用报销：{expense.expense_name}，金额：¥{expense.amount}'
            )
            
            # 更新费用状态
            expense.reimbursement_status = 'pending'
            expense.save(update_fields=['reimbursement_status'])
            
            logger.info(f'费用 {expense.expense_name} 报销申请已提交审批，审批实例: {instance.instance_number}')
            return instance
            
        except Exception as e:
            logger.error(f'提交费用报销审批失败: {str(e)}', exc_info=True)
            raise
    
    @staticmethod
    def get_case_approval_instance(case: LitigationCase) -> Optional[ApprovalInstance]:
        """获取案件的审批实例"""
        try:
            return ApprovalInstance.objects.filter(
                content_type=ContentType.objects.get_for_model(case),
                object_id=case.id
            ).order_by('-created_time').first()
        except Exception:
            return None
    
    @staticmethod
    def get_expense_approval_instance(expense: LitigationExpense) -> Optional[ApprovalInstance]:
        """获取费用的审批实例"""
        try:
            return ApprovalInstance.objects.filter(
                content_type=ContentType.objects.get_for_model(expense),
                object_id=expense.id
            ).order_by('-created_time').first()
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

