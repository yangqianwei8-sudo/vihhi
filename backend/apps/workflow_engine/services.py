"""
审批流程引擎服务
"""
import logging
from typing import Optional, List, Dict
from django.utils import timezone
from django.contrib.contenttypes.models import ContentType
from django.db import transaction
from backend.apps.workflow_engine.models import WorkflowTemplate, ApprovalNode, ApprovalInstance, ApprovalRecord
from backend.apps.system_management.models import User

logger = logging.getLogger(__name__)


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
            
            # 获取第一个节点（优先获取第一个审批节点，如果没有则获取开始节点）
            first_approval_node = workflow.nodes.filter(node_type='approval').order_by('sequence').first()
            if first_approval_node:
                # 如果有审批节点，设置为当前节点
                instance.current_node = first_approval_node
                instance.save()
                
                # 创建审批记录（待审批状态）
                # 如果找不到审批人，自动退回
                has_records = ApprovalEngine._create_pending_records(instance, first_approval_node)
                
                if not has_records:
                    # 找不到审批人，自动退回
                    instance.status = 'rejected'
                    instance.completed_time = timezone.now()
                    instance.final_comment = f'节点 {first_approval_node.name} 找不到审批人，自动退回。请检查审批流程配置。'
                    instance.current_node = None
                    instance.save()
                    
                    # 创建退回记录
                    from backend.apps.workflow_engine.models import ApprovalRecord
                    ApprovalRecord.objects.create(
                        instance=instance,
                        node=first_approval_node,
                        approver=instance.applicant,  # 使用申请人作为退回记录的操作人
                        result='rejected',
                        comment=instance.final_comment,
                        approval_time=timezone.now()
                    )
                    
                    # 同步更新关联业务对象的状态
                    ApprovalEngine._sync_content_object_status(instance, 'rejected')
                    
                    logger.warning(
                        f'审批流程 {instance.instance_number} 启动失败：'
                        f'第一个节点 {first_approval_node.name} 没有找到审批人，已自动退回。'
                    )
            else:
                # 如果没有审批节点，至少设置开始节点
                first_node = workflow.nodes.filter(node_type='start').first()
                if not first_node:
                    first_node = workflow.nodes.order_by('sequence').first()
                
                if first_node:
                    instance.current_node = first_node
                    instance.save()
                    logger.warning(f'审批流程 {workflow.name} 没有找到审批节点，只设置了开始节点')
            
            logger.info(f'启动审批流程: {instance.instance_number}, 申请人: {applicant.username}')
            return instance
    
    @staticmethod
    def _create_pending_records(instance: ApprovalInstance, node: ApprovalNode) -> bool:
        """
        为节点创建待审批记录
        
        Returns:
            bool: 是否成功创建了审批记录（True=成功，False=找不到审批人）
        """
        approvers = ApprovalEngine._get_approvers(node, instance)
        
        if not approvers:
            # 记录详细的警告信息，便于排查问题
            applicant_info = f"申请人: {instance.applicant.username}"
            if instance.applicant.department:
                applicant_info += f", 部门: {instance.applicant.department.name}"
            logger.warning(
                f'节点 {node.name} 没有找到审批人。'
                f'节点类型: {node.get_approver_type_display()}, '
                f'{applicant_info}'
            )
            return False
        
        # 如果是单人审批模式，只创建第一个审批人的记录
        if node.approval_mode == 'single':
            approver = approvers[0]
            # 检查是否已经存在该审批人的pending记录，避免重复创建
            # 使用 select_for_update 防止并发情况下的重复创建
            with transaction.atomic():
                existing_record = ApprovalRecord.objects.select_for_update().filter(
                    instance=instance,
                    node=node,
                    approver=approver,
                    result='pending'
                ).first()
                if not existing_record:
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
            with transaction.atomic():
                for approver in approvers:
                    # 检查是否已经存在该审批人的pending记录，避免重复创建
                    # 使用 select_for_update 防止并发情况下的重复创建
                    existing_record = ApprovalRecord.objects.select_for_update().filter(
                        instance=instance,
                        node=node,
                        approver=approver,
                        result='pending'
                    ).first()
                    if not existing_record:
                        ApprovalRecord.objects.create(
                            instance=instance,
                            node=node,
                            approver=approver,
                            result='pending'
                        )
                        # 发送审批通知
                        ApprovalEngine._send_approval_notification(instance, approver, node)
        
        return True
    
    @staticmethod
    def _get_approvers(node: ApprovalNode, instance: ApprovalInstance) -> List[User]:
        """获取节点的审批人列表"""
        approvers = []
        
        if node.approver_type == 'user':
            # 允许系统管理员参与审批（系统管理员可能同时也是业务人员）
            approvers = list(node.approver_users.all())
        elif node.approver_type == 'role':
            from backend.apps.system_management.models import Role
            role_ids = node.approver_roles.values_list('id', flat=True)
            # 允许系统管理员参与审批（系统管理员可能同时也是业务人员）
            approvers = list(User.objects.filter(
                roles__id__in=role_ids
            ).distinct())
        elif node.approver_type == 'department':
            dept_ids = node.approver_departments.values_list('id', flat=True)
            # 允许系统管理员参与审批（系统管理员可能同时也是业务人员）
            approvers = list(User.objects.filter(
                department_id__in=dept_ids
            ).distinct())
        elif node.approver_type == 'creator':
            approvers = [instance.applicant]
        elif node.approver_type == 'department_manager':
            if instance.applicant.department:
                # 查找部门经理
                # 方法1：优先查找部门中具有 department_manager 角色的用户
                approvers = list(User.objects.filter(
                    department=instance.applicant.department,
                    roles__code='department_manager',
                    is_active=True
                ).exclude(id=instance.applicant.id).distinct())
                
                # 方法2：如果没有找到角色，查找部门负责人
                if not approvers and instance.applicant.department.leader:
                    leader = instance.applicant.department.leader
                    # 确保不是申请人自己
                    if leader != instance.applicant:
                        approvers = [leader]
                
                # 方法3：如果还是没有找到，查找部门中的高级角色（按优先级）
                if not approvers:
                    priority_role_codes = [
                        'general_manager',      # 总经理
                        'business_director',     # 商务总监
                        'business_manager',     # 商务部经理
                        'technical_manager',     # 技术部经理
                        'admin_office',          # 行政主管
                    ]
                    
                    for role_code in priority_role_codes:
                        managers = User.objects.filter(
                            department=instance.applicant.department,
                            roles__code=role_code,
                            is_active=True
                        ).exclude(id=instance.applicant.id).distinct()
                        if managers.exists():
                            approvers = [managers.first()]
                            break
                
                # 方法4：如果同部门没找到，尝试查找其他部门中具有总经理角色的用户
                if not approvers:
                    general_managers = User.objects.filter(
                        roles__code='general_manager',
                        is_active=True
                    ).exclude(id=instance.applicant.id).distinct()
                    if general_managers.exists():
                        # 优先找同部门的总经理；否则找第一个
                        if instance.applicant.department:
                            same_dept_manager = general_managers.filter(
                                department=instance.applicant.department
                            ).first()
                            if same_dept_manager:
                                approvers = [same_dept_manager]
                            else:
                                approvers = [general_managers.first()]
                        else:
                            approvers = [general_managers.first()]
        elif node.approver_type == 'creator_manager':
            # 创建人的上级审批
            # 优先查找部门负责人，如果没有则查找部门经理角色或高级角色
            applicant = instance.applicant
            manager = None
            
            # 方法1：查找部门负责人
            if applicant.department and applicant.department.leader:
                leader = applicant.department.leader
                # 确保不是申请人自己
                if leader != applicant:
                    manager = leader
            
            # 方法2：如果部门负责人是自己或不存在，查找部门中的高级角色
            if not manager and applicant.department:
                # 优先查找的上级角色（按优先级排序）
                priority_role_codes = [
                    'general_manager',  # 总经理
                    'business_director',  # 商务总监
                    'department_manager',  # 部门经理
                    'business_manager',  # 商务部经理
                    'technical_manager',  # 技术部经理
                    'admin_office',  # 行政主管
                ]
                
                # 按优先级依次查找，必须排除申请人自己
                for role_code in priority_role_codes:
                    managers = User.objects.filter(
                        department=applicant.department,
                        roles__code=role_code,
                        is_active=True  # 确保用户是激活状态
                    ).exclude(id=applicant.id).distinct()  # 必须排除申请人自己
                    if managers.exists():
                        found_manager = managers.first()
                        # 双重检查：确保不是申请人自己（防止数据异常）
                        if found_manager != applicant:
                            manager = found_manager
                            break
            
            # 方法3：如果同部门没找到，尝试查找其他部门中具有高级角色的用户
            # 例如：总经理通常不在具体部门，可能在不同部门
            if not manager:
                # 查找总经理角色（通常是最高级别）
                general_managers = User.objects.filter(
                    roles__code='general_manager',
                    is_active=True
                ).exclude(id=applicant.id).distinct()  # 必须排除申请人自己
                if general_managers.exists():
                    # 如果申请人有部门，优先找同部门的总经理；否则找第一个
                    if applicant.department:
                        same_dept_manager = general_managers.filter(
                            department=applicant.department
                        ).exclude(id=applicant.id).first()  # 双重排除
                        if same_dept_manager and same_dept_manager != applicant:
                            manager = same_dept_manager
                        else:
                            # 找其他部门的总经理，但必须不是申请人自己
                            other_manager = general_managers.exclude(id=applicant.id).first()
                            if other_manager and other_manager != applicant:
                                manager = other_manager
                    else:
                        # 申请人没有部门，找第一个总经理，但必须不是申请人自己
                        other_manager = general_managers.exclude(id=applicant.id).first()
                        if other_manager and other_manager != applicant:
                            manager = other_manager
            
            # 最终检查：确保找到的审批人不是申请人自己
            if manager and manager == applicant:
                logger.warning(
                    f'creator_manager 类型节点找到的审批人是申请人自己，已排除。'
                    f'申请人: {applicant.username}, 节点: {node.name}'
                )
                manager = None
            
            if manager:
                approvers = [manager]
            else:
                # 记录详细的警告信息，便于排查问题
                applicant_info = f"申请人: {applicant.username}"
                if applicant.department:
                    applicant_info += f", 部门: {applicant.department.name}"
                    if applicant.department.leader:
                        applicant_info += f", 部门负责人: {applicant.department.leader.username}"
                        if applicant.department.leader == applicant:
                            applicant_info += " (是申请人自己)"
                logger.warning(
                    f'creator_manager 类型节点 {node.name} 没有找到审批人。'
                    f'{applicant_info}'
                )
        # 如果 approver_type 为空或未匹配任何类型，记录警告
        if not approvers:
            if not node.approver_type:
                logger.warning(
                    f'节点 {node.name} (ID: {node.id}) 的 approver_type 为空，无法确定审批人'
                )
            else:
                logger.warning(
                    f'节点 {node.name} (ID: {node.id}, 类型: {node.approver_type}) 未找到审批人。'
                    f'申请人: {instance.applicant.username if instance.applicant else "未知"}'
                )
        
        # 其他类型可以根据需要扩展
        
        # 去重审批人列表（避免同一审批人多次出现）
        # 同时确保不包含申请人自己（防止数据异常导致的问题）
        unique_approvers = []
        seen_approver_ids = set()
        applicant_id = instance.applicant.id if instance.applicant else None
        
        for approver in approvers:
            # 排除申请人自己（防止数据异常或逻辑错误）
            if applicant_id and approver.id == applicant_id:
                logger.warning(
                    f'审批人列表中包含申请人自己，已排除。'
                    f'申请人: {instance.applicant.username}, '
                    f'节点: {node.name if hasattr(node, "name") else "未知"}'
                )
                continue
            
            # 去重
            if approver.id not in seen_approver_ids:
                unique_approvers.append(approver)
                seen_approver_ids.add(approver.id)
        
        return unique_approvers if unique_approvers else []
    
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
            # 查找现有的pending审批记录（审批时应该更新pending记录，而不是创建新记录）
            existing_record = ApprovalRecord.objects.filter(
                instance=instance,
                node=instance.current_node,
                approver=approver,
                result='pending'
            ).first()
            
            if existing_record:
                # 更新现有的pending记录
                existing_record.result = result
                existing_record.comment = comment
                existing_record.transferred_to = transferred_to
                existing_record.approval_time = timezone.now()
                existing_record.save()
                record = existing_record
            else:
                # 如果没有pending记录，检查是否已有approved/rejected记录
                existing_approved = ApprovalRecord.objects.filter(
                    instance=instance,
                    node=instance.current_node,
                    approver=approver,
                    result__in=['approved', 'rejected']
                ).first()
                
                if existing_approved:
                    # 如果已经有approved/rejected记录，不允许重复审批
                    logger.warning(
                        f'审批人 {approver.username} 已对节点 {instance.current_node.name} 进行过审批操作'
                        f'（记录ID: {existing_approved.id}, 结果: {existing_approved.result}），不允许重复审批'
                    )
                    return False
                
                # 只有在完全没有记录的情况下才创建新记录（这种情况理论上不应该发生，因为审批前应该先创建pending记录）
                record = ApprovalRecord.objects.create(
                    instance=instance,
                    node=instance.current_node,
                    approver=approver,
                    result=result,
                    comment=comment,
                    transferred_to=transferred_to,
                    approval_time=timezone.now()
                )
                logger.warning(
                    f'为审批人 {approver.username} 创建了新的审批记录（节点: {instance.current_node.name}），'
                    f'这通常不应该发生，应该在审批前先创建pending记录'
                )
            
            # 处理审批结果
            if result == 'rejected':
                # 驳回，流程结束
                instance.status = 'rejected'
                instance.completed_time = timezone.now()
                instance.final_comment = comment
                instance.current_node = None
                instance.save()
                
                # 同步更新关联业务对象的状态（如果是发文）
                ApprovalEngine._sync_content_object_status(instance, 'rejected')
                
                logger.info(f'审批被驳回: {instance.instance_number}')
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
                # 如果当前节点是结束节点，直接完成流程
                if instance.current_node.node_type == 'end':
                    instance.status = 'approved'
                    instance.completed_time = timezone.now()
                    instance.final_comment = comment
                    instance.current_node = None
                    instance.save()
                    
                    # 同步更新关联业务对象的状态（如果是发文）
                    ApprovalEngine._sync_content_object_status(instance, 'approved')
                    
                    logger.info(f'审批流程完成（结束节点）: {instance.instance_number}')
                    return True
                
                # 检查是否所有审批人都已审批
                if ApprovalEngine._check_node_completed(instance, instance.current_node):
                    # 节点完成，进入下一个节点
                    next_node = ApprovalEngine._get_next_node(instance.current_node)
                    if next_node:
                        # 如果下一个节点是结束节点，直接完成流程
                        if next_node.node_type == 'end':
                            instance.status = 'approved'
                            instance.completed_time = timezone.now()
                            instance.final_comment = comment
                            instance.current_node = None
                            instance.save()
                            
                            # 同步更新关联业务对象的状态（如果是发文）
                            ApprovalEngine._sync_content_object_status(instance, 'approved')
                            
                            logger.info(f'审批流程完成（进入结束节点）: {instance.instance_number}')
                        else:
                            instance.current_node = next_node
                            instance.save()
                            # 创建下一个节点的审批记录，如果找不到审批人则自动退回
                            has_records = ApprovalEngine._create_pending_records(instance, next_node)
                            
                            if not has_records:
                                # 找不到审批人，自动退回
                                instance.status = 'rejected'
                                instance.completed_time = timezone.now()
                                instance.final_comment = f'节点 {next_node.name} 找不到审批人，自动退回。请检查审批流程配置。'
                                instance.current_node = None
                                instance.save()
                                
                                # 创建退回记录
                                ApprovalRecord.objects.create(
                                    instance=instance,
                                    node=next_node,
                                    approver=instance.applicant,  # 使用申请人作为退回记录的操作人
                                    result='rejected',
                                    comment=instance.final_comment,
                                    approval_time=timezone.now()
                                )
                                
                                # 同步更新关联业务对象的状态
                                ApprovalEngine._sync_content_object_status(instance, 'rejected')
                                
                                logger.warning(
                                    f'审批流程 {instance.instance_number} 进入节点 {next_node.name} 失败：'
                                    f'没有找到审批人，已自动退回。'
                                )
                            else:
                                logger.info(f'进入下一个节点: {instance.instance_number}, 节点: {next_node.name}')
                    else:
                        # 流程完成
                        instance.status = 'approved'
                        instance.completed_time = timezone.now()
                        instance.final_comment = comment
                        instance.current_node = None
                        instance.save()
                        
                        # 同步更新关联业务对象的状态（如果是发文）
                        ApprovalEngine._sync_content_object_status(instance, 'approved')
                        
                        logger.info(f'审批流程完成（无下一个节点）: {instance.instance_number}')
                    return True
            
            return False
    
    @staticmethod
    def _check_node_completed(instance: ApprovalInstance, node: ApprovalNode) -> bool:
        """检查节点是否已完成"""
        # 首先检查是否有待审批记录，如果没有，说明节点还没有开始审批，不能算完成
        pending_records = ApprovalRecord.objects.filter(
            instance=instance,
            node=node,
            result='pending'
        )
        
        # 如果节点没有审批记录（既没有pending也没有approved），说明还没有开始审批，不能算完成
        has_any_records = ApprovalRecord.objects.filter(
            instance=instance,
            node=node
        ).exists()
        
        if not has_any_records:
            # 节点还没有任何审批记录，不能算完成
            return False
        
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
            # 如果没有审批人，不能算完成
            if len(approvers) == 0:
                return False
            approved_count = ApprovalRecord.objects.filter(
                instance=instance,
                node=node,
                result='approved'
            ).count()
            return approved_count >= len(approvers)
        elif node.approval_mode == 'majority':
            # 多数通过
            approvers = ApprovalEngine._get_approvers(node, instance)
            # 如果没有审批人，不能算完成
            if len(approvers) == 0:
                return False
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
        """
        撤回审批
        
        条件：
        1. 审批实例状态必须是 pending（审批中）
        2. 必须是申请人本人才能撤回
        3. 必须还没有任何人审批（所有审批记录都必须是 pending 状态）
        4. 流程模板必须允许撤回（allow_withdraw=True）
        """
        if instance.status != 'pending':
            logger.warning(f'审批实例状态不正确，无法撤回: {instance.instance_number}, 状态: {instance.status}')
            return False
        
        if instance.applicant != user:
            logger.warning(f'只有申请人才能撤回: {instance.instance_number}, 申请人: {instance.applicant.username}, 当前用户: {user.username}')
            return False
        
        # 检查流程模板是否允许撤回
        if not instance.workflow.allow_withdraw:
            logger.warning(f'流程模板不允许撤回: {instance.instance_number}, 流程: {instance.workflow.name}')
            return False
        
        # 检查是否已经有审批记录（如果有人已经审批了，不允许撤回）
        has_approved_or_rejected = ApprovalRecord.objects.filter(
            instance=instance,
            result__in=['approved', 'rejected']
        ).exists()
        
        if has_approved_or_rejected:
            logger.warning(f'已有审批记录，无法撤回: {instance.instance_number}')
            return False
        
        with transaction.atomic():
            # 将所有 pending 的审批记录标记为 withdrawn
            ApprovalRecord.objects.filter(
                instance=instance,
                result='pending'
            ).update(
                result='withdrawn',
                comment='申请人撤回',
                approval_time=timezone.now()
            )
            
            # 更新审批实例状态
            instance.status = 'withdrawn'
            instance.completed_time = timezone.now()
            instance.final_comment = '申请人撤回'
            instance.save()
            
            # 同步更新关联业务对象的状态（如果是发文，恢复为草稿状态）
            try:
                if instance.content_type and instance.object_id:
                    content_object = instance.content_type.get_object_for_this_type(id=instance.object_id)
                    # 如果是发文，恢复为草稿状态
                    if hasattr(content_object, 'status') and hasattr(content_object, 'transition_to'):
                        from backend.apps.delivery_customer.models import OutgoingDocument
                        if isinstance(content_object, OutgoingDocument):
                            if content_object.status == 'reviewing':
                                content_object.transition_to('draft', actor=user, comment='审批流程已撤回')
                                logger.info(f'发文状态已恢复为草稿: {content_object.document_number}')
            except Exception as e:
                logger.error(f'同步业务对象状态失败: {str(e)}', exc_info=True)
            
            logger.info(f'审批已撤回: {instance.instance_number}, 申请人: {user.username}')
            return True
    
    @staticmethod
    def get_pending_approvals(user: User) -> List[ApprovalInstance]:
        """获取用户的待审批列表"""
        return ApprovalInstance.objects.filter(
            status='pending',
            records__approver=user,
            records__result='pending'
        ).distinct()
    
    @staticmethod
    def get_my_applications(user: User) -> List[ApprovalInstance]:
        """获取用户的申请列表"""
        return ApprovalInstance.objects.filter(applicant=user).order_by('-created_time')
    
    @staticmethod
    def _sync_content_object_status(instance: ApprovalInstance, approval_status: str):
        """
        同步更新关联业务对象的状态
        
        Args:
            instance: 审批实例
            approval_status: 审批状态 ('approved' 或 'rejected')
        """
        try:
            # 使用 ContentType 框架获取关联对象
            if not instance.content_type or not instance.object_id:
                logger.warning(f'审批实例 {instance.instance_number} 没有关联的业务对象')
                return
            
            content_object = instance.content_type.get_object_for_this_type(id=instance.object_id)
            
            # 如果是发文，更新发文状态
            if hasattr(content_object, 'transition_to') and hasattr(content_object, 'status'):
                from backend.apps.delivery_customer.models import OutgoingDocument
                if isinstance(content_object, OutgoingDocument):
                    if approval_status == 'approved' and content_object.status == 'reviewing':
                        content_object.transition_to('approved', actor=None, comment='审批流程已完成')
                        logger.info(f'发文状态已同步更新: {content_object.document_number}, 状态: {content_object.status}')
                    elif approval_status == 'rejected' and content_object.status == 'reviewing':
                        content_object.transition_to('rejected', actor=None, comment='审批流程已驳回')
                        logger.info(f'发文状态已同步更新: {content_object.document_number}, 状态: {content_object.status}')
        except Exception as e:
            logger.error(f'同步业务对象状态失败: {str(e)}', exc_info=True)
    
    @staticmethod
    def _send_approval_notification(instance: ApprovalInstance, approver: User, node: ApprovalNode):
        """发送审批通知"""
        try:
            from django.urls import reverse
            from backend.apps.production_management.models import ProjectTeamNotification
            
            # 获取关联对象信息
            content_obj = instance.content_type.get_object_for_this_type(id=instance.object_id)
            obj_name = str(content_obj)[:50]
            
            # 生成通知标题和内容
            title = f"待审批：{instance.workflow.name}"
            message = f"您有一个待审批事项：{obj_name}\n审批节点：{node.name}\n申请人：{instance.applicant.username}\n申请时间：{instance.apply_time.strftime('%Y-%m-%d %H:%M') if instance.apply_time else ''}"
            
            # 生成跳转链接（跳转到前端审批详情页，而不是后台管理系统）
            try:
                action_url = reverse('workflow_engine:approval_detail', args=[instance.id])
            except:
                # 如果前端页面不存在，使用后台管理系统
                action_url = reverse('admin:workflow_engine_approvalinstance_change', args=[instance.id])
            
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

