"""
审批流程引擎服务
"""
import logging
from typing import Optional, List, Dict
from django.utils import timezone
from django.contrib.contenttypes.models import ContentType
from django.db import transaction
from django.core.exceptions import ValidationError
from backend.apps.workflow_engine.models import WorkflowTemplate, ApprovalNode, ApprovalInstance, ApprovalRecord
from backend.apps.system_management.models import User

logger = logging.getLogger(__name__)


class CompanyScopeNotResolved(ValidationError):
    """
    公司范围未解析异常
    
    当审批流程无法确定公司归属时抛出，用于阻止跨公司审批。
    """
    def __init__(self, instance, message=None):
        self.instance = instance
        if message is None:
            message = (
                f"未配置公司归属/无法确定company范围，已阻止审批以避免跨公司串人。"
                f"审批实例：{instance.instance_number if hasattr(instance, 'instance_number') else instance.id}，"
                f"关联对象：{instance.content_type.model}#{instance.object_id}。"
                f"请确保业务对象已配置company字段，或联系管理员配置用户所属公司。"
            )
        super().__init__(message)


class ApprovalEngine:
    """审批流程引擎"""
    
    @staticmethod
    def generate_instance_number(workflow: WorkflowTemplate) -> str:
        """生成审批实例编号"""
        from django.db.models import Count
        count = ApprovalInstance.objects.filter(workflow=workflow).count()
        return f"{workflow.code}-{timezone.now().strftime('%Y%m%d')}-{count + 1:04d}"
    
    @staticmethod
    def start_approval(
        workflow: WorkflowTemplate,
        content_object,
        applicant: User,
        comment: str = ''
    ) -> ApprovalInstance:
        """
        启动审批流程
        
        Args:
            workflow: 审批流程模板
            content_object: 关联的业务对象
            applicant: 申请人
            comment: 申请说明
        
        Returns:
            ApprovalInstance: 审批实例
        """
        with transaction.atomic():
            # 创建审批实例
            instance = ApprovalInstance.objects.create(
                workflow=workflow,
                instance_number=ApprovalEngine.generate_instance_number(workflow),
                content_type=ContentType.objects.get_for_model(content_object),
                object_id=content_object.pk,
                applicant=applicant,
                apply_time=timezone.now(),
                apply_comment=comment,
                status='pending'
            )
            
            # 获取第一个节点（跳过开始节点，直接进入第一个审批节点）
            start_node = workflow.nodes.filter(node_type='start').first()
            if start_node:
                # 获取开始节点的下一个节点（第一个审批节点）
                first_approval_node = ApprovalEngine._get_next_node(start_node)
                if first_approval_node:
                    instance.current_node = first_approval_node
                    instance.save()
                    # 创建审批记录（待审批状态）
                    ApprovalEngine._create_pending_records(instance, first_approval_node)
                else:
                    # 如果没有下一个节点，使用开始节点
                    instance.current_node = start_node
                    instance.save()
            else:
                # 如果没有开始节点，使用第一个节点
                first_node = workflow.nodes.order_by('sequence').first()
                if first_node:
                    instance.current_node = first_node
                    instance.save()
                    # 如果是审批节点，创建审批记录
                    if first_node.node_type == 'approval':
                        ApprovalEngine._create_pending_records(instance, first_node)
            
            logger.info(f'启动审批流程: {instance.instance_number}, 申请人: {applicant.username}')
            return instance
    
    @staticmethod
    def _create_pending_records(instance: ApprovalInstance, node: ApprovalNode):
        """为节点创建待审批记录"""
        # 如果是结束节点，直接完成流程
        if node.node_type == 'end':
            instance.status = 'approved'
            instance.completed_time = timezone.now()
            instance.current_node = None
            instance.save()
            logger.info(f'到达结束节点，审批流程完成: {instance.instance_number}')
            ApprovalEngine._update_business_object_status(instance, 'approved')
            # 抄送出纳员（如果是借款审批流程）
            ApprovalEngine._notify_cashier_on_loan_approval(instance)
            return
        
        approvers = ApprovalEngine._get_approvers(node, instance)
        
        if not approvers:
            # 记录详细的调试信息
            debug_info = f'节点 {node.name} (ID: {node.id}) 没有找到审批人。'
            debug_info += f' 审批人类型: {node.approver_type}'
            if node.approver_type == 'department_manager':
                if instance.applicant.department:
                    debug_info += f', 申请人部门: {instance.applicant.department.name}'
                    if instance.applicant.department.leader:
                        debug_info += f', 部门负责人: {instance.applicant.department.leader.username}'
                    else:
                        debug_info += ', 部门负责人: 未设置'
                else:
                    debug_info += ', 申请人没有部门'
            logger.warning(debug_info)
            # 如果是非必审节点，没有审批人也可以继续（抄送节点）
            if not node.is_required:
                logger.info(f'节点 {node.name} 是非必审节点，即使没有审批人也可以继续流程')
                return
            return
        
        # 如果是非必审节点（抄送节点），创建审批记录但标记为已通过，流程自动继续
        if not node.is_required:
            # 非必审节点：创建审批记录并自动通过，仅发送通知
            for approver in approvers:
                ApprovalRecord.objects.create(
                    instance=instance,
                    node=node,
                    approver=approver,
                    result='approved',  # 自动通过
                    comment='抄送通知，自动通过',
                    approval_time=timezone.now()
                )
                # 发送通知
                ApprovalEngine._send_approval_notification(instance, approver, node)
            # 非必审节点创建完记录后，立即进入下一个节点
            next_node = ApprovalEngine._get_next_node(node)
            if next_node:
                instance.current_node = next_node
                instance.save()
                ApprovalEngine._create_pending_records(instance, next_node)
                logger.info(f'非必审节点 {node.name} 自动通过，进入下一个节点: {next_node.name}')
            else:
                # 流程完成
                instance.status = 'approved'
                instance.completed_time = timezone.now()
                instance.current_node = None
                instance.save()
                logger.info(f'非必审节点 {node.name} 自动通过，审批流程完成')
                ApprovalEngine._update_business_object_status(instance, 'approved')
                # 抄送出纳员（如果是借款审批流程）
                ApprovalEngine._notify_cashier_on_loan_approval(instance)
            return
        
        # 如果是单人审批模式，只创建第一个审批人的记录
        if node.approval_mode == 'single':
            approver = approvers[0]
            ApprovalRecord.objects.create(
                instance=instance,
                node=node,
                approver=approver,
                result='pending'
            )
            # 发送审批通知
            ApprovalEngine._send_approval_notification(instance, approver, node)
        else:
            # 其他模式（any, all, majority），为所有审批人创建记录
            for approver in approvers:
                ApprovalRecord.objects.create(
                    instance=instance,
                    node=node,
                    approver=approver,
                    result='pending'
                )
                
                # 发送审批通知
                ApprovalEngine._send_approval_notification(instance, approver, node)
    
    @staticmethod
    def _get_approvers(node: ApprovalNode, instance: ApprovalInstance) -> List[User]:
        """
        获取节点的审批人列表（完全配置化，无硬编码）
        
        ⚠️ P0-1: 公司隔离安全阀
        - 优先从 instance 关联的业务对象获取 company
        - 如果无法确定 company，直接拒绝流转/发起审批（抛出 CompanyScopeNotResolved）
        - 所有选人分支强制加 company 过滤
        
        支持的审批人类型（全部可配置，无需修改代码）：
        - role: 指定角色（动态查询拥有该角色的所有用户）
        - department: 指定部门（动态查询部门内所有用户）
        - department_manager: 部门经理（动态获取申请人部门的负责人）
        - creator: 创建人（动态获取申请人）
        - creator_manager: 创建人直属上级（动态获取申请人的manager）
        - creator_manager_chain: 创建人多级上级（通过approver_config.levels控制级数）
        """
        # ========== P0-1: 获取业务对象的 company ==========
        company = None
        company_id = None
        try:
            # 尝试从关联的业务对象获取 company
            content_obj = instance.content_type.get_object_for_this_type(id=instance.object_id)
            if hasattr(content_obj, 'company') and content_obj.company:
                company = content_obj.company
                company_id = company.id
                logger.info(f"从业务对象获取 company: {company.company_name} (ID: {company.id})")
            elif hasattr(content_obj, 'company_id') and content_obj.company_id:
                # 如果只有 company_id，尝试获取对象
                from backend.apps.system_management.models import OurCompany
                company = OurCompany.objects.filter(id=content_obj.company_id).first()
                if company:
                    company_id = company.id
                    logger.info(f"从业务对象 company_id 获取 company: {company.company_name} (ID: {company.id})")
        except Exception as e:
            logger.warning(f"获取业务对象 company 失败: {str(e)}")
        
        # 如果无法确定 company，直接拒绝审批
        if not company_id:
            raise CompanyScopeNotResolved(instance)
        # ========== P0-1 结束 ==========
        
        approvers = []
        
        if node.approver_type == 'role':
            # 指定角色：动态查询拥有该角色的所有用户（组织变化自动适配）
            from backend.apps.system_management.models import Role
            role_ids = node.approver_roles.values_list('id', flat=True)
            # P0-1: 强制加 company 过滤
            approvers = list(User.objects.filter(
                roles__id__in=role_ids,
                company_id=company_id,
                is_active=True
            ).distinct())
        elif node.approver_type == 'department':
            # 指定部门：动态查询部门内所有用户（组织变化自动适配）
            dept_ids = node.approver_departments.values_list('id', flat=True)
            # P0-1: 强制加 company 过滤
            approvers = list(User.objects.filter(
                department_id__in=dept_ids,
                company_id=company_id,
                is_active=True
            ).distinct())
        elif node.approver_type == 'creator':
            # 创建人：动态获取申请人
            if instance.applicant:
                # P0-1: 校验申请人 company
                if instance.applicant.company_id != company_id:
                    logger.error(
                        f"⚠️ P0 风险：申请人跨公司 - "
                        f"applicant.company_id={instance.applicant.company_id}, "
                        f"instance.company_id={company_id}"
                    )
                    raise CompanyScopeNotResolved(instance)
                approvers = [instance.applicant]
        elif node.approver_type == 'department_manager':
            # 部门经理：动态获取申请人所在部门的负责人（组织变化自动适配）
            if instance.applicant and instance.applicant.department:
                # P0-1: 校验部门 company
                if hasattr(instance.applicant.department, 'company_id'):
                    if instance.applicant.department.company_id != company_id:
                        logger.error(
                            f"⚠️ P0 风险：申请人部门跨公司 - "
                            f"department.company_id={instance.applicant.department.company_id}, "
                            f"instance.company_id={company_id}"
                        )
                        raise CompanyScopeNotResolved(instance)
                
                # 优先使用部门的 leader（部门负责人）
                if instance.applicant.department.leader:
                    leader = instance.applicant.department.leader
                    # P0-1: 校验部门负责人 company
                    if leader.company_id != company_id:
                        logger.error(
                            f"⚠️ P0 风险：部门负责人跨公司 - "
                            f"leader.company_id={leader.company_id}, "
                            f"instance.company_id={company_id}"
                        )
                        raise CompanyScopeNotResolved(instance)
                    approvers = [leader]
                else:
                    # 如果没有设置部门负责人，则查找角色代码为 department_manager 的用户
                    approvers = list(User.objects.filter(
                        department=instance.applicant.department,
                        roles__code='department_manager',
                        company_id=company_id,
                        is_active=True
                    ).distinct())
        elif node.approver_type == 'creator_manager':
            # 创建人直属上级：动态获取申请人的manager（组织变化自动适配）
            if not instance.applicant:
                raise ValueError(
                    f'审批实例 {instance.instance_number} 的申请人不存在，无法获取 creator_manager 审批人。'
                    f'节点：{node.name} (ID: {node.id})'
                )
            
            if not instance.applicant.manager:
                raise ValueError(
                    f'申请人 {instance.applicant.username} ({instance.applicant.get_full_name() or "无姓名"}) '
                    f'没有设置直属上级（manager），无法获取审批人。'
                    f'请在用户管理中为 {instance.applicant.username} 设置 manager 字段。'
                    f'节点：{node.name} (ID: {node.id})，流程：{instance.workflow.name}'
                )
            
            manager = instance.applicant.manager
            # P0-1: 只允许 manager.company_id == applicant.company_id
            if manager.company_id != instance.applicant.company_id:
                logger.error(
                    f"⚠️ P0 风险：创建人上级跨公司 - "
                    f"applicant.company_id={instance.applicant.company_id}, "
                    f"manager.company_id={manager.company_id}"
                )
                raise CompanyScopeNotResolved(instance)
            
            approvers = [manager]
        elif node.approver_type == 'creator_manager_chain':
            # 创建人多级上级：通过approver_config.levels控制级数（组织变化自动适配）
            if not instance.applicant:
                logger.warning('申请人不存在，无法获取多级上级')
                return []
            
            levels = node.approver_config.get('levels')
            if levels is None:
                raise ValueError(
                    f'节点 {node.name} (ID: {node.id}) 使用 creator_manager_chain 类型，'
                    f'但 approver_config 中未配置 levels 参数。请在 Admin 中配置 approver_config，例如：{{"levels": 2}}'
                )
            
            if not isinstance(levels, int) or levels < 1:
                raise ValueError(
                    f'节点 {node.name} (ID: {node.id}) 的 approver_config.levels 无效：{levels}。'
                    f'levels 必须为正整数（1-10）。'
                )
            
            if levels > 10:
                raise ValueError(
                    f'节点 {node.name} (ID: {node.id}) 的 approver_config.levels 超过上限：{levels}。'
                    f'levels 不能超过 10 级，建议值：2-4 级。'
                )
            
            if not instance.applicant:
                raise ValueError(
                    f'审批实例 {instance.instance_number} 的申请人不存在，无法获取 creator_manager_chain 审批人。'
                    f'节点：{node.name} (ID: {node.id})'
                )
            
            current_user = instance.applicant
            manager_chain = []
            missing_level = None
            
            for level in range(levels):
                if not current_user or not current_user.manager:
                    # 上级链中断
                    missing_level = level + 1
                    break
                
                current_user = current_user.manager
                
                # P0-1: 只允许 manager.company_id == applicant.company_id（链路上每一跳都校验）
                if current_user.company_id != instance.applicant.company_id:
                    logger.error(
                        f"⚠️ P0 风险：上级链第 {level+1} 级跨公司 - "
                        f"applicant.company_id={instance.applicant.company_id}, "
                        f"manager_{level+1}.company_id={current_user.company_id}"
                    )
                    raise CompanyScopeNotResolved(instance)
                
                manager_chain.append(current_user)
            
            if missing_level is not None:
                if missing_level == 1:
                    raise ValueError(
                        f'申请人 {instance.applicant.username} ({instance.applicant.get_full_name() or "无姓名"}) '
                        f'没有设置直属上级（manager），无法获取多级上级审批人。'
                        f'请在用户管理中为 {instance.applicant.username} 设置 manager 字段。'
                        f'节点：{node.name} (ID: {node.id})，流程：{instance.workflow.name}，需要 {levels} 级上级'
                    )
                else:
                    raise ValueError(
                        f'申请人 {instance.applicant.username} 的上级链在第 {missing_level} 级中断（需要 {levels} 级）。'
                        f'已找到 {len(manager_chain)} 级上级：{" -> ".join([u.username for u in manager_chain])}。'
                        f'请在用户管理中为上级链中的用户补齐 manager 字段。'
                        f'节点：{node.name} (ID: {node.id})，流程：{instance.workflow.name}'
                    )
            
            approvers = manager_chain
        elif node.approver_type in ['user', 'custom']:
            # 已废弃的类型：直接报错，不允许使用
            raise ValueError(
                f'审批人类型 "{node.approver_type}" 已废弃，禁止使用。'
                f'请使用配置化的审批人类型（role/department/department_manager/creator/creator_manager/creator_manager_chain）。'
                f'节点ID: {node.id}, 节点名称: {node.name}'
            )
        else:
            logger.warning(f'未知的审批人类型: {node.approver_type}, 节点ID: {node.id}')
        
        return approvers if approvers else []
    
    @staticmethod
    def approve(
        instance: ApprovalInstance,
        approver: User,
        result: str,
        comment: str = '',
        transferred_to: Optional[User] = None
    ) -> bool:
        """
        执行审批操作
        
        Args:
            instance: 审批实例
            approver: 审批人
            result: 审批结果 ('approved', 'rejected', 'transferred')
            comment: 审批意见
            transferred_to: 转交给（转交时使用）
        
        Returns:
            bool: 是否成功
        """
        if instance.status != 'pending':
            logger.warning(f'审批实例状态不正确: {instance.instance_number}, 状态: {instance.status}')
            return False
        
        if not instance.current_node:
            logger.warning(f'审批实例没有当前节点: {instance.instance_number}')
            return False
        
        with transaction.atomic():
            # 创建审批记录
            record = ApprovalRecord.objects.create(
                instance=instance,
                node=instance.current_node,
                approver=approver,
                result=result,
                comment=comment,
                transferred_to=transferred_to,
                approval_time=timezone.now()
            )
            
            # 处理审批结果
            if result == 'rejected':
                # 驳回，流程结束
                instance.status = 'rejected'
                instance.completed_time = timezone.now()
                instance.final_comment = comment
                instance.current_node = None
                instance.save()
                logger.info(f'审批被驳回: {instance.instance_number}')
                # 调用业务对象状态更新回调
                ApprovalEngine._update_business_object_status(instance, 'rejected')
                # 发送审批结果通知给提交人
                ApprovalEngine._send_approval_result_notification(instance, 'rejected', approver)
                return True
            
            elif result == 'transferred' and transferred_to:
                # 转交
                # 创建新的审批记录给转交人
                ApprovalRecord.objects.create(
                    instance=instance,
                    node=instance.current_node,
                    approver=transferred_to,
                    result='pending',
                    comment=f'由 {approver.username} 转交',
                    approval_time=timezone.now()
                )
                logger.info(f'审批已转交: {instance.instance_number}, 转交给: {transferred_to.username}')
                return True
            
            elif result == 'approved':
                # 检查是否所有审批人都已审批
                if ApprovalEngine._check_node_completed(instance, instance.current_node):
                    # 节点完成，进入下一个节点
                    next_node = ApprovalEngine._get_next_node(instance.current_node)
                    if next_node:
                        instance.current_node = next_node
                        instance.save()
                        ApprovalEngine._create_pending_records(instance, next_node)
                        logger.info(f'进入下一个节点: {instance.instance_number}, 节点: {next_node.name}')
                    else:
                        # 流程完成
                        instance.status = 'approved'
                        instance.completed_time = timezone.now()
                        instance.final_comment = comment
                        instance.current_node = None
                        instance.save()
                        logger.info(f'审批流程完成: {instance.instance_number}')
                        # 调用业务对象状态更新回调
                        ApprovalEngine._update_business_object_status(instance, 'approved')
                        # 发送审批结果通知给提交人
                        ApprovalEngine._send_approval_result_notification(instance, 'approved', approver)
                        # 抄送出纳员（如果是借款审批流程）
                        ApprovalEngine._notify_cashier_on_loan_approval(instance)
                    return True
            
            return False
    
    @staticmethod
    def _check_node_completed(instance: ApprovalInstance, node: ApprovalNode) -> bool:
        """检查节点是否已完成"""
        pending_records = ApprovalRecord.objects.filter(
            instance=instance,
            node=node,
            result='pending'
        )
        
        if node.approval_mode == 'single':
            # 单人审批，只要有一个通过即可
            return ApprovalRecord.objects.filter(
                instance=instance,
                node=node,
                result='approved'
            ).exists()
        elif node.approval_mode == 'any':
            # 任意一人通过
            return ApprovalRecord.objects.filter(
                instance=instance,
                node=node,
                result='approved'
            ).exists()
        elif node.approval_mode == 'all':
            # 全部通过
            approvers = ApprovalEngine._get_approvers(node, instance)
            approved_count = ApprovalRecord.objects.filter(
                instance=instance,
                node=node,
                result='approved'
            ).count()
            return approved_count >= len(approvers)
        elif node.approval_mode == 'majority':
            # 多数通过
            approvers = ApprovalEngine._get_approvers(node, instance)
            approved_count = ApprovalRecord.objects.filter(
                instance=instance,
                node=node,
                result='approved'
            ).count()
            return approved_count > len(approvers) / 2
        
        return False
    
    @staticmethod
    def _get_next_node(current_node: ApprovalNode) -> Optional[ApprovalNode]:
        """获取下一个节点"""
        # 简单实现：按顺序获取下一个节点
        next_node = ApprovalNode.objects.filter(
            workflow=current_node.workflow,
            sequence__gt=current_node.sequence
        ).order_by('sequence').first()
        
        return next_node
    
    @staticmethod
    def withdraw(instance: ApprovalInstance, user: User) -> bool:
        """撤回审批"""
        if instance.status != 'pending':
            return False
        
        if instance.applicant != user:
            return False
        
        with transaction.atomic():
            instance.status = 'withdrawn'
            instance.completed_time = timezone.now()
            instance.save()
            
            # 创建撤回记录
            ApprovalRecord.objects.create(
                instance=instance,
                node=instance.current_node,
                approver=user,
                result='withdrawn',
                comment='申请人撤回',
                approval_time=timezone.now()
            )
            
            logger.info(f'审批已撤回: {instance.instance_number}')
            return True
    
    @staticmethod
    def get_pending_approvals(user: User):
        """获取用户的待审批列表（返回QuerySet，支持分页）"""
        return ApprovalInstance.objects.filter(
            status='pending',
            records__approver=user,
            records__result='pending'
        ).distinct().select_related(
            'workflow', 'applicant', 'current_node', 'content_type'
        ).prefetch_related('records').order_by('-created_time')
    
    @staticmethod
    def get_my_applications(user: User):
        """获取用户的申请列表（返回QuerySet，支持分页）"""
        return ApprovalInstance.objects.filter(
            applicant=user
        ).select_related(
            'workflow', 'applicant', 'current_node', 'content_type'
        ).prefetch_related('records').order_by('-created_time')
    
    @staticmethod
    def get_my_historical_approvals(user: User):
        """获取用户作为审批人审批过的历史记录（返回QuerySet，支持分页）"""
        # 获取用户审批过的所有审批实例（通过审批记录关联）
        # 只包含已完成的审批（status不是pending）
        return ApprovalInstance.objects.filter(
            records__approver=user,
            status__in=['approved', 'rejected', 'withdrawn', 'cancelled']
        ).distinct().select_related(
            'workflow', 'applicant', 'current_node', 'content_type'
        ).prefetch_related('records').order_by('-created_time')
    
    @staticmethod
    def _send_approval_notification(instance: ApprovalInstance, approver: User, node: ApprovalNode):
        """发送审批通知（给审批人）"""
        try:
            from django.urls import reverse
            from backend.apps.production_management.models import ProjectTeamNotification
            
            # 获取关联对象信息
            try:
                content_obj = instance.content_type.get_object_for_this_type(id=instance.object_id)
                obj_name = str(content_obj)[:50]
            except Exception as e:
                logger.warning(f'获取审批对象失败: {instance.content_type.model}#{instance.object_id}, 错误: {str(e)}')
                obj_name = f"{instance.content_type.model}#{instance.object_id}"
                content_obj = None
            
            # 生成通知标题和内容
            title = f"待审批：{instance.workflow.name}"
            message = f"您有一个待审批事项：{obj_name}\n审批节点：{node.name}\n申请人：{instance.applicant.username}\n申请时间：{instance.apply_time.strftime('%Y-%m-%d %H:%M') if instance.apply_time else ''}"
            
            # 生成跳转链接（跳转到前端审批详情页，而不是后台管理系统）
            try:
                action_url = reverse('workflow_engine:approval_detail', args=[instance.id])
            except:
                # 如果前端页面不存在，使用后台管理系统
                action_url = reverse('admin:workflow_engine_approvalinstance_change', args=[instance.id])
            
            # 创建 ApprovalNotification 类型的通知（通知中心使用）
            try:
                from backend.apps.plan_management.compat import safe_approval_notification
                
                # 根据业务对象类型确定 object_type（必须是 OBJECT_TYPE_CHOICES 中的值）
                object_type_map = {
                    'plan': 'plan',
                    'strategicgoal': 'goal',
                    'sealborrowing': 'notification',  # 使用 notification 类型
                    'sealusage': 'notification',  # 使用 notification 类型
                }
                object_type = object_type_map.get(instance.content_type.model, 'plan')
                
                # 对于审批通知，将审批实例ID存储在 object_id 中，以便序列化器能正确生成跳转链接
                # 格式：approval_instance_id:business_object_id
                approval_object_id = f"approval_{instance.id}:{instance.object_id}"
                
                # 创建审批通知（注意：模型没有 url 字段，url 由序列化器动态生成）
                notification = safe_approval_notification(
                    user=approver,
                    event='submit',  # 提交审批事件
                    title=title,
                    content=message,
                    object_type=object_type,
                    object_id=approval_object_id,  # 存储审批实例ID和业务对象ID
                    is_read=False,
                )
                if notification:
                    logger.info(f'已创建审批通知（ApprovalNotification）: {instance.instance_number}, 审批人: {approver.username}, 通知ID: {notification.id}')
                else:
                    logger.warning(f'创建ApprovalNotification通知返回None: {instance.instance_number}, 审批人: {approver.username}')
            except Exception as e:
                logger.error(f'创建ApprovalNotification通知失败: {str(e)}', exc_info=True)
            
            # 尝试获取关联的项目（如果关联对象是项目）
            project = None
            if hasattr(content_obj, 'project'):
                project = content_obj.project
            elif instance.content_type.model == 'project':
                from backend.apps.production_management.models import Project
                try:
                    project = Project.objects.get(id=instance.object_id)
                except:
                    pass
            
            # 创建通知（如果有项目，使用项目通知；否则创建一个通用的通知）
            if project:
                # 使用项目通知
                ProjectTeamNotification.objects.create(
                    project=project,
                    recipient=approver,
                    operator=instance.applicant,
                    title=title,
                    message=message,
                    category='team_change',  # 可以扩展为 'approval' 类别
                    action_url=action_url,
                    is_read=False,
                    context={
                        'approval_instance_id': instance.id,
                        'approval_instance_number': instance.instance_number,
                        'node_id': node.id,
                        'node_name': node.name,
                    }
                )
                logger.info(f'已发送审批通知（项目）: {instance.instance_number}, 审批人: {approver.username}')
            else:
                # 对于非项目相关的审批，创建通知（project 可以为 null）
                ProjectTeamNotification.objects.create(
                    project=None,
                    recipient=approver,
                    operator=instance.applicant,
                    title=title,
                    message=message,
                    category='approval',  # 使用审批通知类别
                    action_url=action_url,
                    is_read=False,
                    context={
                        'approval_instance_id': instance.id,
                        'approval_instance_number': instance.instance_number,
                        'node_id': node.id,
                        'node_name': node.name,
                        'content_type': instance.content_type.model,
                        'object_id': instance.object_id,
                    }
                )
                logger.info(f'已发送审批通知（非项目）: {instance.instance_number}, 审批人: {approver.username}')
                
        except Exception as e:
            # 通知发送失败不应影响审批流程
            logger.error(f'发送审批通知异常: {str(e)}', exc_info=True)
    
    @staticmethod
    def _send_approval_result_notification(instance: ApprovalInstance, approval_status: str, approver: User):
        """
        发送审批结果通知（给提交人）
        
        Args:
            instance: 审批实例
            approval_status: 审批状态 ('approved' 或 'rejected')
            approver: 审批人
        """
        try:
            from django.urls import reverse
            from backend.apps.production_management.models import ProjectTeamNotification
            
            # 获取关联对象信息
            try:
                content_obj = instance.content_type.get_object_for_this_type(id=instance.object_id)
                obj_name = str(content_obj)[:50]
            except Exception as e:
                logger.warning(f'获取审批对象失败: {instance.content_type.model}#{instance.object_id}, 错误: {str(e)}')
                obj_name = f"{instance.content_type.model}#{instance.object_id}"
                content_obj = None
            
            # 生成通知标题和内容
            if approval_status == 'approved':
                title = f"[审批结果] {instance.workflow.name}已审批通过"
                message = f"您的申请《{obj_name}》已审批通过"
                if instance.final_comment:
                    message += f"\n审批意见：{instance.final_comment}"
                message += f"\n审批人：{approver.get_full_name() or approver.username}"
                message += f"\n审批时间：{instance.completed_time.strftime('%Y-%m-%d %H:%M') if instance.completed_time else ''}"
                event_type = 'approve'  # 审批通过事件
            elif approval_status == 'rejected':
                title = f"[审批结果] {instance.workflow.name}已被驳回"
                message = f"您的申请《{obj_name}》已被驳回"
                if instance.final_comment:
                    message += f"\n驳回原因：{instance.final_comment}"
                message += f"\n审批人：{approver.get_full_name() or approver.username}"
                message += f"\n审批时间：{instance.completed_time.strftime('%Y-%m-%d %H:%M') if instance.completed_time else ''}"
                event_type = 'reject'  # 审批驳回事件
            else:
                logger.warning(f'未知的审批状态: {approval_status}')
                return
            
            # 生成跳转链接（跳转到业务对象详情页或审批详情页）
            action_url = ''
            try:
                # 尝试根据业务对象类型生成详情页链接
                if instance.content_type.model == 'plan':
                    action_url = reverse('plan_pages:plan_detail', args=[instance.object_id])
                elif instance.content_type.model == 'strategicgoal':
                    action_url = reverse('plan_pages:goal_detail', args=[instance.object_id])
                else:
                    # 默认跳转到审批详情页
                    action_url = reverse('workflow_engine:approval_detail', args=[instance.id])
            except:
                try:
                    action_url = reverse('workflow_engine:approval_detail', args=[instance.id])
                except:
                    pass
            
            # 创建 ApprovalNotification 类型的通知（通知中心使用）
            try:
                from backend.apps.plan_management.compat import safe_approval_notification
                
                # 根据业务对象类型确定 object_type（必须是 OBJECT_TYPE_CHOICES 中的值）
                object_type_map = {
                    'plan': 'plan',
                    'strategicgoal': 'goal',
                    'sealborrowing': 'notification',  # 使用 notification 类型
                    'sealusage': 'notification',  # 使用 notification 类型
                }
                object_type = object_type_map.get(instance.content_type.model, 'plan')
                
                # 对于审批通知，将审批实例ID存储在 object_id 中，以便序列化器能正确生成跳转链接
                # 格式：approval_instance_id:business_object_id
                approval_object_id = f"approval_{instance.id}:{instance.object_id}"
                
                # 创建审批结果通知（注意：模型没有 url 字段，url 由序列化器动态生成）
                notification = safe_approval_notification(
                    user=instance.applicant,  # 发送给提交人
                    event=event_type,  # 'approve' 或 'reject'
                    title=title,
                    content=message,
                    object_type=object_type,
                    object_id=approval_object_id,  # 存储审批实例ID和业务对象ID
                    is_read=False,
                )
                if notification:
                    logger.info(f'已创建审批结果通知（ApprovalNotification）: {instance.instance_number}, 提交人: {instance.applicant.username}, 状态: {approval_status}, 通知ID: {notification.id}')
                else:
                    logger.warning(f'创建ApprovalNotification审批结果通知返回None: {instance.instance_number}, 提交人: {instance.applicant.username}, 状态: {approval_status}')
            except Exception as e:
                logger.error(f'创建ApprovalNotification审批结果通知失败: {str(e)}', exc_info=True)
            
            # 尝试获取关联的项目（如果关联对象是项目）
            project = None
            if hasattr(content_obj, 'project'):
                project = content_obj.project
            elif instance.content_type.model == 'project':
                from backend.apps.production_management.models import Project
                try:
                    project = Project.objects.get(id=instance.object_id)
                except:
                    pass
            
            # 创建通知（发送给提交人）
            if project:
                # 使用项目通知
                ProjectTeamNotification.objects.create(
                    project=project,
                    recipient=instance.applicant,
                    operator=approver,
                    title=title,
                    message=message,
                    category='approval',  # 审批结果通知
                    action_url=action_url,
                    is_read=False,
                    context={
                        'approval_instance_id': instance.id,
                        'approval_instance_number': instance.instance_number,
                        'approval_status': approval_status,
                        'content_type': instance.content_type.model,
                        'object_id': instance.object_id,
                    }
                )
                logger.info(f'已发送审批结果通知（项目）: {instance.instance_number}, 提交人: {instance.applicant.username}, 状态: {approval_status}')
            else:
                # 对于非项目相关的审批，创建通知（project 可以为 null）
                ProjectTeamNotification.objects.create(
                    project=None,
                    recipient=instance.applicant,
                    operator=approver,
                    title=title,
                    message=message,
                    category='approval',  # 审批结果通知
                    action_url=action_url,
                    is_read=False,
                    context={
                        'approval_instance_id': instance.id,
                        'approval_instance_number': instance.instance_number,
                        'approval_status': approval_status,
                        'content_type': instance.content_type.model,
                        'object_id': instance.object_id,
                    }
                )
                logger.info(f'已发送审批结果通知（非项目）: {instance.instance_number}, 提交人: {instance.applicant.username}, 状态: {approval_status}')
                
        except Exception as e:
            # 通知发送失败不应影响审批流程
            logger.error(f'发送审批结果通知异常: {str(e)}', exc_info=True)
    
    @staticmethod
    def _update_business_object_status(instance: ApprovalInstance, approval_status: str):
        """
        更新业务对象的状态（根据审批结果）
        
        治理后：仅保留通用、最小状态记录能力，具体业务逻辑由各 Service 的 handle_approval_result 方法处理
        
        Args:
            instance: 审批实例
            approval_status: 审批状态 ('approved' 或 'rejected')
        """
        try:
            # 获取关联的业务对象
            content_obj = instance.content_type.get_object_for_this_type(id=instance.object_id)
            
            # 尝试通过 Service 处理审批结果
            # 根据 content_type 查找对应的 Service
            service_map = {
                'loanapplication': 'LoanApprovalService',
                'sealborrowing': 'SealBorrowingApprovalService',
                'sealusage': 'SealUsageApprovalService',
                'businessopportunity': 'OpportunityApprovalService',
            }
            
            service_class_name = service_map.get(instance.content_type.model)
            if service_class_name:
                try:
                    if service_class_name == 'LoanApprovalService':
                        from backend.apps.administrative_management.services.loan_approval import LoanApprovalService
                        service = LoanApprovalService()
                    elif service_class_name == 'SealBorrowingApprovalService':
                        from backend.apps.administrative_management.services.seal_borrowing_approval import SealBorrowingApprovalService
                        service = SealBorrowingApprovalService()
                    elif service_class_name == 'SealUsageApprovalService':
                        from backend.apps.administrative_management.services.seal_usage_approval import SealUsageApprovalService
                        service = SealUsageApprovalService()
                    elif service_class_name == 'OpportunityApprovalService':
                        from backend.apps.opportunity_management.services.opportunity_approval import OpportunityApprovalService
                        service = OpportunityApprovalService()
                    else:
                        service = None
                    
                    if service:
                        service.handle_approval_result(instance, approval_status)
                        return
                except Exception as e:
                    logger.warning(f'通过 Service 处理审批结果失败，回退到通用逻辑: {str(e)}')
            
            # 回退：通用逻辑（仅更新审批人信息和时间，不更新状态）
            # 注意：Plan 审批由 signal 处理，不在此处处理
            if instance.content_type.model == 'plan':
                logger.debug(f'计划审批由 signal 处理，跳过通用逻辑: #{instance.object_id}')
                return
            
            # 通用逻辑：仅更新审批人信息和时间
            if approval_status == 'approved':
                last_record = instance.records.filter(result='approved').order_by('-approval_time').first()
                if last_record and hasattr(content_obj, 'approver'):
                    content_obj.approver = last_record.approver
                if hasattr(content_obj, 'approved_time'):
                    content_obj.approved_time = timezone.now()
                content_obj.save(update_fields=['approver', 'approved_time'] if hasattr(content_obj, 'approver') or hasattr(content_obj, 'approved_time') else [])
                logger.info(f'业务对象审批信息已更新（通用逻辑）: {instance.content_type.model}#{instance.object_id}')
                        
        except Exception as e:
            # 状态更新失败不应影响审批流程
            logger.error(f'更新业务对象状态异常: {str(e)}', exc_info=True)
    
    @staticmethod
    def _notify_cashier_on_loan_approval(instance: ApprovalInstance):
        """
        借款审批完成后，抄送出纳员
        
        Args:
            instance: 审批实例
        """
        try:
            # 只处理借款审批流程
            if instance.workflow.code != 'loan_approval':
                return
            
            # 只处理审批通过的情况
            if instance.status != 'approved':
                return
            
            # 获取出纳员角色
            from backend.apps.system_management.models import Role
            from backend.apps.production_management.models import ProjectTeamNotification
            from django.urls import reverse
            
            cashier_role = Role.objects.filter(code='cashier', is_active=True).first()
            if not cashier_role:
                logger.warning('未找到出纳员角色（code: cashier），无法抄送出纳员')
                return
            
            # 获取所有出纳员用户
            cashier_users = cashier_role.users.filter(is_active=True)
            if not cashier_users.exists():
                logger.warning('没有激活的出纳员用户，无法抄送出纳员')
                return
            
            # 获取业务对象信息
            try:
                content_obj = instance.content_type.get_object_for_this_type(id=instance.object_id)
                obj_name = str(content_obj)[:50]
            except Exception as e:
                logger.warning(f'获取审批对象失败: {instance.content_type.model}#{instance.object_id}, 错误: {str(e)}')
                obj_name = f"{instance.content_type.model}#{instance.object_id}"
                content_obj = None
            
            # 生成通知标题和内容
            title = f"[借款审批] {obj_name} 已审批通过"
            message = f"借款申请《{obj_name}》已审批通过，请及时处理。\n"
            message += f"审批单号：{instance.instance_number}\n"
            message += f"申请人：{instance.applicant.get_full_name() or instance.applicant.username}\n"
            if content_obj and hasattr(content_obj, 'loan_amount'):
                message += f"借款金额：¥{content_obj.loan_amount}\n"
            message += f"审批完成时间：{instance.completed_time.strftime('%Y-%m-%d %H:%M') if instance.completed_time else ''}"
            
            # 生成跳转链接
            try:
                # 尝试生成借款申请详情页链接
                if instance.content_type.model == 'loanapplication':
                    action_url = reverse('admin_pages:loan_detail', args=[instance.object_id])
                else:
                    action_url = reverse('workflow_engine:approval_detail', args=[instance.id])
            except:
                try:
                    action_url = reverse('workflow_engine:approval_detail', args=[instance.id])
                except:
                    action_url = ''
            
            # 为每个出纳员发送通知
            notified_count = 0
            for cashier_user in cashier_users:
                try:
                    ProjectTeamNotification.objects.create(
                        project=None,
                        recipient=cashier_user,
                        operator=instance.applicant,
                        title=title,
                        message=message,
                        category='approval',  # 审批通知
                        action_url=action_url,
                        is_read=False,
                        context={
                            'approval_instance_id': instance.id,
                            'approval_instance_number': instance.instance_number,
                            'approval_status': 'approved',
                            'content_type': instance.content_type.model,
                            'object_id': instance.object_id,
                            'is_copy': True,  # 标记为抄送
                        }
                    )
                    notified_count += 1
                except Exception as e:
                    logger.error(f'发送出纳员通知失败: {cashier_user.username}, 错误: {str(e)}')
            
            if notified_count > 0:
                logger.info(f'已抄送出纳员: {instance.instance_number}, 抄送人数: {notified_count}')
            else:
                logger.warning(f'抄送出纳员失败: {instance.instance_number}, 所有出纳员通知发送失败')
                
        except Exception as e:
            # 抄送失败不应影响审批流程
            logger.error(f'抄送出纳员异常: {str(e)}', exc_info=True)

