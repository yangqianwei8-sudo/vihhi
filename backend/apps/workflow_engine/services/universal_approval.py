"""
通用审批流程服务
提供统一的审批流程接口，方便各业务模块复用
"""
import logging
from typing import Optional, List, Dict, Any, Callable
from django.utils import timezone
from django.contrib.contenttypes.models import ContentType
from django.db import transaction
from backend.apps.workflow_engine.models import WorkflowTemplate, ApprovalInstance, ApprovalRecord
# 延迟导入 ApprovalEngine 以避免循环导入
# from backend.apps.workflow_engine.services import ApprovalEngine
from backend.apps.system_management.models import User

logger = logging.getLogger(__name__)


class UniversalApprovalService:
    """
    通用审批流程服务
    
    使用示例：
    ```python
    # 1. 定义业务审批服务类
    class ContractApprovalService(UniversalApprovalService):
        WORKFLOW_CODE = 'contract_approval'
        CONTENT_MODEL = BusinessContract
        
        # 可选：自定义审批前验证
        def validate_before_submit(self, obj, applicant):
            if obj.amount > 1000000:
                raise ValueError('金额超过100万需要特殊审批')
    
    # 2. 提交审批
    service = ContractApprovalService()
    instance = service.submit_approval(
        contract_obj,
        applicant=request.user,
        comment='申请审批合同'
    )
    
    # 3. 审批操作
    service.approve(instance_id, approver=request.user, comment='同意')
    service.reject(instance_id, approver=request.user, comment='不同意')
    
    # 4. 查询审批状态
    status = service.get_approval_status(contract_obj)
    ```
    """
    
    # 子类需要重写这些属性
    WORKFLOW_CODE: str = None  # 审批流程代码
    CONTENT_MODEL = None  # 关联的业务模型类
    
    def __init__(self, workflow_code: str = None):
        """
        初始化服务
        
        Args:
            workflow_code: 审批流程代码，如果不提供则使用类的 WORKFLOW_CODE
        """
        self.workflow_code = workflow_code or self.WORKFLOW_CODE
        if not self.workflow_code:
            raise ValueError("必须提供 workflow_code 或设置类的 WORKFLOW_CODE 属性")
    
    def get_workflow(self) -> Optional[WorkflowTemplate]:
        """获取审批流程模板"""
        try:
            return WorkflowTemplate.objects.get(
                code=self.workflow_code,
                status='active'
            )
        except WorkflowTemplate.DoesNotExist:
            logger.warning(f'审批流程模板不存在: {self.workflow_code}')
            return None
    
    def validate_before_submit(self, obj: Any, applicant: User) -> None:
        """
        提交审批前的验证（子类可重写）
        
        Args:
            obj: 业务对象
            applicant: 申请人
            
        Raises:
            ValueError: 如果验证失败
        """
        pass
    
    @transaction.atomic
    def submit_approval(
        self,
        obj: Any,
        applicant: User,
        comment: str = '',
        workflow_code: str = None
    ) -> Optional[ApprovalInstance]:
        """
        提交审批
        
        Args:
            obj: 业务对象（需要关联到审批实例的对象）
            applicant: 申请人
            comment: 申请说明
            workflow_code: 可选的流程代码（覆盖默认值）
            
        Returns:
            ApprovalInstance: 审批实例，如果流程未配置则返回 None
            
        Raises:
            ValueError: 如果验证失败
        """
        # 使用提供的 workflow_code 或默认值
        original_code = None
        if workflow_code:
            original_code = self.workflow_code
            self.workflow_code = workflow_code
        
        try:
            # 验证
            self.validate_before_submit(obj, applicant)
            
            # 检查是否已有待审批的实例
            content_type = ContentType.objects.get_for_model(obj)
            existing_instance = ApprovalInstance.objects.filter(
                content_type=content_type,
                object_id=obj.pk,
                workflow__code=self.workflow_code,
                status__in=['pending', 'in_progress']
            ).first()
            
            if existing_instance:
                logger.warning(f'对象 {obj} 已有待审批实例: {existing_instance.instance_number}')
                return existing_instance
            
            # 获取审批流程模板
            workflow = self.get_workflow()
            if not workflow:
                logger.warning(f'审批流程未配置: {self.workflow_code}')
                return None
            
            # 启动审批流程（延迟导入以避免循环导入）
            from backend.apps.workflow_engine.services import ApprovalEngine
            instance = ApprovalEngine.start_approval(
                workflow=workflow,
                content_object=obj,
                applicant=applicant,
                comment=comment or f'申请审批：{str(obj)}'
            )
            
            logger.info(f'已提交审批: {instance.instance_number}, 对象: {obj}')
            return instance
            
        finally:
            # 恢复原始 workflow_code
            if original_code:
                self.workflow_code = original_code
    
    def approve(
        self,
        instance_id: int,
        approver: User,
        comment: str = ''
    ) -> bool:
        """
        审批通过
        
        Args:
            instance_id: 审批实例ID
            approver: 审批人
            comment: 审批意见
            
        Returns:
            bool: 是否成功
        """
        try:
            from backend.apps.workflow_engine.services import ApprovalEngine
            instance = ApprovalInstance.objects.get(id=instance_id)
            return ApprovalEngine.approve(
                instance=instance,
                approver=approver,
                result='approved',
                comment=comment
            )
        except ApprovalInstance.DoesNotExist:
            logger.error(f'审批实例不存在: {instance_id}')
            return False
        except Exception as e:
            logger.error(f'审批失败: {str(e)}', exc_info=True)
            return False
    
    def reject(
        self,
        instance_id: int,
        approver: User,
        comment: str = ''
    ) -> bool:
        """
        审批驳回
        
        Args:
            instance_id: 审批实例ID
            approver: 审批人
            comment: 驳回原因
            
        Returns:
            bool: 是否成功
        """
        try:
            from backend.apps.workflow_engine.services import ApprovalEngine
            instance = ApprovalInstance.objects.get(id=instance_id)
            return ApprovalEngine.approve(
                instance=instance,
                approver=approver,
                result='rejected',
                comment=comment
            )
        except ApprovalInstance.DoesNotExist:
            logger.error(f'审批实例不存在: {instance_id}')
            return False
        except Exception as e:
            logger.error(f'驳回失败: {str(e)}', exc_info=True)
            return False
    
    def transfer(
        self,
        instance_id: int,
        approver: User,
        transferred_to: User,
        comment: str = ''
    ) -> bool:
        """
        转交审批
        
        Args:
            instance_id: 审批实例ID
            approver: 当前审批人
            transferred_to: 转交给
            comment: 转交说明
            
        Returns:
            bool: 是否成功
        """
        try:
            from backend.apps.workflow_engine.services import ApprovalEngine
            instance = ApprovalInstance.objects.get(id=instance_id)
            return ApprovalEngine.approve(
                instance=instance,
                approver=approver,
                result='transferred',
                comment=comment,
                transferred_to=transferred_to
            )
        except ApprovalInstance.DoesNotExist:
            logger.error(f'审批实例不存在: {instance_id}')
            return False
        except Exception as e:
            logger.error(f'转交失败: {str(e)}', exc_info=True)
            return False
    
    def withdraw(
        self,
        instance_id: int,
        applicant: User
    ) -> bool:
        """
        撤回审批
        
        Args:
            instance_id: 审批实例ID
            applicant: 申请人
            
        Returns:
            bool: 是否成功
        """
        try:
            from backend.apps.workflow_engine.services import ApprovalEngine
            instance = ApprovalInstance.objects.get(id=instance_id)
            return ApprovalEngine.withdraw(instance, applicant)
        except ApprovalInstance.DoesNotExist:
            logger.error(f'审批实例不存在: {instance_id}')
            return False
        except Exception as e:
            logger.error(f'撤回失败: {str(e)}', exc_info=True)
            return False
    
    def get_approval_instance(
        self,
        obj: Any,
        workflow_code: str = None
    ) -> Optional[ApprovalInstance]:
        """
        获取对象的审批实例
        
        Args:
            obj: 业务对象
            workflow_code: 可选的流程代码
            
        Returns:
            ApprovalInstance: 审批实例，如果不存在则返回 None
        """
        code = workflow_code or self.workflow_code
        content_type = ContentType.objects.get_for_model(obj)
        
        return ApprovalInstance.objects.filter(
            content_type=content_type,
            object_id=obj.pk,
            workflow__code=code
        ).order_by('-created_time').first()
    
    def get_approval_status(self, obj: Any) -> Dict[str, Any]:
        """
        获取审批状态信息
        
        Args:
            obj: 业务对象
            
        Returns:
            dict: 包含审批状态的字典
            {
                'has_pending': bool,  # 是否有待审批的实例
                'instance': ApprovalInstance | None,  # 审批实例
                'current_node': str | None,  # 当前节点名称
                'approvers': List[User],  # 当前待审批人列表
                'status': str,  # 审批状态
                'can_submit': bool,  # 是否可以提交审批
                'can_approve': bool,  # 当前用户是否可以审批
            }
        """
        instance = self.get_approval_instance(obj)
        
        if not instance:
            return {
                'has_pending': False,
                'instance': None,
                'current_node': None,
                'approvers': [],
                'status': 'none',
                'can_submit': True,
                'can_approve': False,
            }
        
        # 获取当前待审批人
        approvers = []
        if instance.current_node:
            pending_records = ApprovalRecord.objects.filter(
                instance=instance,
                node=instance.current_node,
                result='pending'
            )
            approvers = [record.approver for record in pending_records]
        
        return {
            'has_pending': instance.status in ['pending', 'in_progress'],
            'instance': instance,
            'current_node': instance.current_node.name if instance.current_node else None,
            'approvers': approvers,
            'status': instance.status,
            'can_submit': instance.status not in ['pending', 'in_progress'],
            'can_approve': False,  # 需要根据当前用户判断
        }
    
    def get_pending_approvals(
        self,
        user: User,
        workflow_code: str = None
    ) -> List[ApprovalInstance]:
        """
        获取用户的待审批列表
        
        Args:
            user: 用户
            workflow_code: 可选的流程代码
            
        Returns:
            List[ApprovalInstance]: 待审批实例列表
        """
        from backend.apps.workflow_engine.services import ApprovalEngine
        if workflow_code:
            return ApprovalEngine.get_pending_approvals(user).filter(
                workflow__code=workflow_code
            )
        return ApprovalEngine.get_pending_approvals(user)
    
    def get_my_applications(
        self,
        user: User,
        workflow_code: str = None
    ) -> List[ApprovalInstance]:
        """
        获取用户的申请列表
        
        Args:
            user: 用户
            workflow_code: 可选的流程代码
            
        Returns:
            List[ApprovalInstance]: 申请实例列表
        """
        from backend.apps.workflow_engine.services import ApprovalEngine
        if workflow_code:
            return ApprovalEngine.get_my_applications(user).filter(
                workflow__code=workflow_code
            )
        return ApprovalEngine.get_my_applications(user)
    
    @classmethod
    def create_workflow_from_config(
        cls,
        code: str,
        name: str,
        description: str,
        category: str,
        nodes_config: List[Dict[str, Any]],
        creator: User,
        **kwargs
    ) -> WorkflowTemplate:
        """
        从配置创建审批流程模板（类方法）
        
        Args:
            code: 流程代码
            name: 流程名称
            description: 流程描述
            category: 流程分类
            nodes_config: 节点配置列表，格式：
                [
                    {
                        'name': '部门经理审批',
                        'node_type': 'approval',
                        'sequence': 1,
                        'approver_type': 'department_manager',
                        'approval_mode': 'single',
                        'approver_users': [user1, user2],  # 可选
                        'approver_roles': [role1],  # 可选
                        'timeout_hours': 24,
                        'can_reject': True,
                        'can_transfer': False,
                    },
                    ...
                ]
            creator: 创建人
            **kwargs: 其他流程模板参数
            
        Returns:
            WorkflowTemplate: 创建的流程模板
        """
        from backend.apps.workflow_engine.models import ApprovalNode
        
        # 创建或更新流程模板
        # 确保 applicable_models 有默认值
        defaults = {
            'name': name,
            'description': description,
            'category': category,
            'status': 'active',
            'created_by': creator,
            'applicable_models': kwargs.pop('applicable_models', []),  # 从 kwargs 中提取，如果没有则默认为空列表
            **kwargs
        }
        
        workflow, created = WorkflowTemplate.objects.update_or_create(
            code=code,
            defaults=defaults
        )
        
        if not created:
            # 删除旧节点
            workflow.nodes.all().delete()
        
        # 创建节点
        for node_config in nodes_config:
            node = ApprovalNode.objects.create(
                workflow=workflow,
                name=node_config['name'],
                node_type=node_config.get('node_type', 'approval'),
                sequence=node_config['sequence'],
                approver_type=node_config.get('approver_type', 'user'),
                approval_mode=node_config.get('approval_mode', 'single'),
                is_required=node_config.get('is_required', True),
                can_reject=node_config.get('can_reject', True),
                can_transfer=node_config.get('can_transfer', False),
                timeout_hours=node_config.get('timeout_hours'),
                description=node_config.get('description', ''),
            )
            
            # 关联审批人
            if 'approver_users' in node_config:
                node.approver_users.set(node_config['approver_users'])
            if 'approver_roles' in node_config:
                node.approver_roles.set(node_config['approver_roles'])
            if 'approver_departments' in node_config:
                node.approver_departments.set(node_config['approver_departments'])
        
        logger.info(f'创建审批流程模板: {code}')
        return workflow

