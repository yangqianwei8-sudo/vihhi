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
        """获取节点的审批人列表"""
        approvers = []
        
        if node.approver_type == 'user':
            approvers = list(node.approver_users.all())
        elif node.approver_type == 'role':
            from backend.apps.system_management.models import Role
            role_ids = node.approver_roles.values_list('id', flat=True)
            approvers = list(User.objects.filter(roles__id__in=role_ids).distinct())
        elif node.approver_type == 'department':
            dept_ids = node.approver_departments.values_list('id', flat=True)
            approvers = list(User.objects.filter(department_id__in=dept_ids).distinct())
        elif node.approver_type == 'creator':
            approvers = [instance.applicant]
        elif node.approver_type == 'department_manager':
            if instance.applicant.department:
                # 优先使用部门的 leader（部门负责人）
                if instance.applicant.department.leader:
                    approvers = [instance.applicant.department.leader]
                else:
                    # 如果没有设置部门负责人，则查找角色代码为 department_manager 的用户
                    approvers = list(User.objects.filter(
                        department=instance.applicant.department,
                        roles__code='department_manager'
                    ).distinct())
        # 其他类型可以根据需要扩展
        
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
    def _send_approval_notification(instance: ApprovalInstance, approver: User, node: ApprovalNode):
        """发送审批通知（给审批人）"""
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
            content_obj = instance.content_type.get_object_for_this_type(id=instance.object_id)
            obj_name = str(content_obj)[:50]
            
            # 生成通知标题和内容
            if approval_status == 'approved':
                title = f"[审批结果] {instance.workflow.name}已审批通过"
                message = f"您的申请《{obj_name}》已审批通过"
                if instance.final_comment:
                    message += f"\n审批意见：{instance.final_comment}"
                message += f"\n审批人：{approver.get_full_name() or approver.username}"
                message += f"\n审批时间：{instance.completed_time.strftime('%Y-%m-%d %H:%M') if instance.completed_time else ''}"
            elif approval_status == 'rejected':
                title = f"[审批结果] {instance.workflow.name}已被驳回"
                message = f"您的申请《{obj_name}》已被驳回"
                if instance.final_comment:
                    message += f"\n驳回原因：{instance.final_comment}"
                message += f"\n审批人：{approver.get_full_name() or approver.username}"
                message += f"\n审批时间：{instance.completed_time.strftime('%Y-%m-%d %H:%M') if instance.completed_time else ''}"
            else:
                logger.warning(f'未知的审批状态: {approval_status}')
                return
            
            # 生成跳转链接（跳转到业务对象详情页或审批详情页）
            action_url = ''
            try:
                # 尝试根据业务对象类型生成详情页链接
                if instance.content_type.model == 'plan':
                    action_url = reverse('plan_management:plan_detail', args=[instance.object_id])
                elif instance.content_type.model == 'strategicgoal':
                    action_url = reverse('plan_management:strategic_goal_detail', args=[instance.object_id])
                else:
                    # 默认跳转到审批详情页
                    action_url = reverse('workflow_engine:approval_detail', args=[instance.id])
            except:
                try:
                    action_url = reverse('workflow_engine:approval_detail', args=[instance.id])
                except:
                    pass
            
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
        
        Args:
            instance: 审批实例
            approval_status: 审批状态 ('approved' 或 'rejected')
        """
        try:
            # 获取关联的业务对象
            content_obj = instance.content_type.get_object_for_this_type(id=instance.object_id)
            
            # 根据业务对象类型更新状态
            if hasattr(content_obj, 'status'):
                if approval_status == 'approved':
                    # 审批通过
                    # 更新审批人信息
                    last_record = instance.records.filter(result='approved').order_by('-approval_time').first()
                    if last_record and hasattr(content_obj, 'approver'):
                        content_obj.approver = last_record.approver
                    if hasattr(content_obj, 'approved_time'):
                        content_obj.approved_time = timezone.now()
                    
                    # 根据业务对象类型设置状态
                    # 印章借用：审批通过后状态变为 'approved'，印章状态变为 'borrowed'
                    if instance.content_type.model == 'sealborrowing':
                        content_obj.status = 'approved'
                        # 更新印章状态
                        if hasattr(content_obj, 'seal') and content_obj.seal:
                            if hasattr(content_obj.seal, 'status'):
                                content_obj.seal.status = 'borrowed'
                                content_obj.seal.save(update_fields=['status'])
                    elif instance.content_type.model == 'sealusage':
                        # 用印申请审批通过，不需要更新状态（用印记录通常不需要状态字段）
                        # 如果需要，可以在这里添加状态更新逻辑
                        logger.info(f'用印申请 {content_obj.usage_number} 审批通过')
                    else:
                        # 其他业务对象：检查是否有 'approved' 状态
                        status_choices = dict(getattr(content_obj, 'STATUS_CHOICES', []))
                        if 'approved' in status_choices:
                            content_obj.status = 'approved'
                    
                    content_obj.save()
                    logger.info(f'业务对象状态已更新: {instance.content_type.model}#{instance.object_id} -> approved')
                    
                elif approval_status == 'rejected':
                    # 审批驳回
                    if instance.content_type.model == 'sealborrowing':
                        content_obj.status = 'rejected'
                    elif instance.content_type.model == 'sealusage':
                        # 用印申请审批驳回，不需要更新状态（用印记录通常不需要状态字段）
                        # 如果需要，可以在这里添加状态更新逻辑
                        logger.info(f'用印申请 {content_obj.usage_number} 审批驳回')
                    else:
                        status_choices = dict(getattr(content_obj, 'STATUS_CHOICES', []))
                        if 'rejected' in status_choices:
                            content_obj.status = 'rejected'
                        elif 'pending_approval' in status_choices:
                            content_obj.status = 'pending_approval'
                    
                    content_obj.save()
                    logger.info(f'业务对象状态已更新: {instance.content_type.model}#{instance.object_id} -> rejected')
                        
        except Exception as e:
            # 状态更新失败不应影响审批流程
            logger.error(f'更新业务对象状态异常: {str(e)}', exc_info=True)

