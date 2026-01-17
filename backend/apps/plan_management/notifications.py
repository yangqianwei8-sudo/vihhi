"""
C3-2: 审批通知服务（最小闭环版）

统一处理审批流程中的通知，包括：
- 提交审批 → 通知审批人
- 审批通过/驳回 → 通知提交人

原则：
- 通知是"附加能力"，失败不影响审批成功
- 所有通知逻辑 try/except 包裹
- 出异常只 logger.warning，不抛错
"""
import logging
from django.contrib.auth.models import User, Permission
from django.db.models import Q
from .models import Plan, StrategicGoal
from .compat import safe_approval_notification, has_approval_notification, get_approval_notification_model

logger = logging.getLogger(__name__)


def notify_approvers(obj, event, actor, comment=None):
    """
    C3-2: 通知审批人（用于 submit_approval）
    
    Args:
        obj: Plan 或 StrategicGoal 对象
        event: 事件类型，'submit'
        actor: 操作人（User 对象）
        comment: 可选，申请说明
    
    Returns:
        int: 成功创建的通知数量
    """
    try:
        # 确定对象类型和权限代码
        if isinstance(obj, Plan):
            object_type = 'plan'
            perm_code = 'plan_management.approve_plan'
            obj_name = obj.name
        elif isinstance(obj, StrategicGoal):
            object_type = 'goal'
            perm_code = 'plan_management.approve_strategicgoal'
            obj_name = obj.indicator_name
        else:
            logger.warning(f"未知对象类型：{type(obj)}")
            return 0
        
        # 找审批人：拥有 approve_plan / approve_strategicgoal 权限的人
        # 最小方案：通过 Permission 查找
        try:
            perm = Permission.objects.get(
                codename=perm_code.split('.')[-1],  # 'approve_plan' 或 'approve_strategicgoal'
                content_type__app_label='plan_management'
            )
            
            # 获取所有拥有该权限的用户（包括通过组获得的）
            approvers = User.objects.filter(
                Q(user_permissions=perm) | Q(groups__permissions=perm)
            ).distinct()
            
            # 公司隔离：只筛选同公司
            if hasattr(obj, 'company') and obj.company:
                # 通过 profile 过滤同公司用户
                approvers = approvers.filter(profile__company=obj.company)
            
            # 排除操作人自己（如果操作人也是审批人，不需要通知自己）
            approvers = approvers.exclude(id=actor.id)
            
        except Permission.DoesNotExist:
            logger.warning(f"权限不存在：{perm_code}")
            return 0
        
        # 构建通知内容
        if event == 'submit':
            title = f"[审批] 有新的{'计划' if object_type == 'plan' else '目标'}需要审批"
            content = f"{actor.get_full_name() or actor.username} 提交了{'计划' if object_type == 'plan' else '目标'}《{obj_name}》，请审批"
            if comment:
                content += f"。说明：{comment}"
        else:
            logger.warning(f"未知事件类型：{event}")
            return 0
        
        # 为每个审批人创建通知
        count = 0
        for approver in approvers:
            try:
                safe_approval_notification(
                    user=approver,
                    title=title,
                    content=content,
                    object_type=object_type,
                    object_id=str(obj.id),
                    event=event,
                    is_read=False
                )
                count += 1
            except Exception as e:
                logger.warning(f"创建通知失败（用户：{approver.username}）：{str(e)}")
        
        logger.info(f"成功创建 {count} 条审批通知（{object_type} #{obj.id}）")
        return count
        
    except Exception as e:
        logger.warning(f"通知审批人失败（不影响业务）：{str(e)}")
        return 0


def notify_submitter(obj, event, actor, comment=None):
    """
    C3-2: 通知提交人（用于 approve / reject）
    
    Args:
        obj: Plan 或 StrategicGoal 对象
        event: 事件类型，'approve' 或 'reject'
        actor: 操作人（User 对象）
        comment: 可选，审批意见/驳回原因
    
    Returns:
        bool: 是否成功创建通知
    """
    try:
        # 确定对象类型
        if isinstance(obj, Plan):
            object_type = 'plan'
            obj_name = obj.name
        elif isinstance(obj, StrategicGoal):
            object_type = 'goal'
            obj_name = obj.indicator_name
        else:
            logger.warning(f"未知对象类型：{type(obj)}")
            return False
        
        # 接收人：obj.created_by
        submitter = obj.created_by
        if not submitter:
            logger.warning(f"对象 {object_type} #{obj.id} 没有创建人，无法发送通知")
            return False
        
        # 构建通知内容
        if event == 'approve':
            title = f"[审批结果] {'计划' if object_type == 'plan' else '目标'}已审批通过"
            content = f"你的{'计划' if object_type == 'plan' else '目标'}《{obj_name}》已审批通过"
            if comment:
                content += f"。意见：{comment}"
        elif event == 'reject':
            title = f"[审批结果] {'计划' if object_type == 'plan' else '目标'}已被驳回"
            content = f"你的{'计划' if object_type == 'plan' else '目标'}《{obj_name}》已被驳回"
            if comment:
                content += f"。原因：{comment}"
        else:
            logger.warning(f"未知事件类型：{event}")
            return False
        
        # 创建通知
        safe_approval_notification(
            user=submitter,
            title=title,
            content=content,
            object_type=object_type,
            object_id=str(obj.id),
            event=event,
            is_read=False
        )
        
        logger.info(f"成功创建审批结果通知（{object_type} #{obj.id} → {submitter.username}）")
        return True
        
    except Exception as e:
        logger.warning(f"通知提交人失败（不影响业务）：{str(e)}")
        return False


def notify_draft_timeout(plan, days_overdue=7):
    """
    工作流强制推进：通知草稿超时
    
    Args:
        plan: Plan 对象（状态为 draft，创建时间超过指定天数）
        days_overdue: 超时天数，默认7天
    
    Returns:
        bool: 是否成功创建通知
    """
    try:
        # 接收人：计划负责人
        recipient = plan.responsible_person
        if not recipient:
            logger.warning(f"计划 #{plan.id} 没有负责人，无法发送草稿超时通知")
            return False
        
        # 检查是否已经发送过通知（避免重复发送）
        # 检查最近7天内是否已有相同类型的通知
        from datetime import timedelta
        from django.utils import timezone
        recent_notification = False
        if has_approval_notification():
            ApprovalNotification = get_approval_notification_model()
            if ApprovalNotification:
                recent_notification = ApprovalNotification.objects.filter(
                    user=recipient,
                    object_type='plan',
                    object_id=str(plan.id),
                    event='draft_timeout',
                    created_at__gte=timezone.now() - timedelta(days=1)  # 1天内不重复发送
                ).exists()
        
        if recent_notification:
            logger.debug(f"计划 #{plan.id} 的草稿超时通知已在1天内发送过，跳过")
            return False
        
        # 构建通知内容
        title = "[提醒] 计划草稿超时，请尽快提交审批"
        content = f"您的计划《{plan.name}》已创建超过{days_overdue}天，仍处于草稿状态。请尽快提交审批，以便开始执行。"
        
        # 创建通知
        safe_approval_notification(
            user=recipient,
            title=title,
            content=content,
            object_type='plan',
            object_id=str(plan.id),
            event='draft_timeout',  # 新增事件类型
            is_read=False
        )
        
        logger.info(f"成功创建草稿超时通知（计划 #{plan.id} → {recipient.username}）")
        return True
        
    except Exception as e:
        logger.warning(f"通知草稿超时失败（不影响业务）：{str(e)}")
        return False


def notify_company_goal_published(goal):
    """
    P2-2: 通知员工创建个人目标（公司目标发布后）
    
    Args:
        goal: StrategicGoal 对象（level='company', status='published'）
    
    Returns:
        int: 成功创建的通知数量
    """
    try:
        if goal.level != 'company' or goal.status != 'published':
            logger.warning(f"目标 #{goal.id} 不是已发布的公司目标，跳过通知")
            return 0
        
        # 通知对象：公司内所有活跃员工（或根据业务规则筛选）
        # P2-2 简化版：通知所有活跃用户（后续可优化为按部门/角色筛选）
        from django.contrib.auth.models import User
        
        # 公司隔离
        recipients = User.objects.filter(is_active=True)
        if hasattr(goal, 'company') and goal.company:
            recipients = recipients.filter(profile__company=goal.company)
        
        # 排除创建人（创建人不需要通知自己）
        recipients = recipients.exclude(id=goal.created_by_id)
        
        # 构建通知内容
        title = "[目标发布] 请创建个人目标进行对齐"
        content = f"公司目标《{goal.name}》已发布，请创建个人目标进行对齐。"
        
        # 为每个员工创建通知
        count = 0
        for recipient in recipients:
            try:
                safe_approval_notification(
                    user=recipient,
                    title=title,
                    content=content,
                    object_type='goal',
                    object_id=str(goal.id),
                    event='company_goal_published',
                    is_read=False
                )
                count += 1
            except Exception as e:
                logger.warning(f"创建通知失败（用户：{recipient.username}）：{str(e)}")
        
        logger.info(f"成功创建 {count} 条公司目标发布通知（目标 #{goal.id}）")
        return count
        
    except Exception as e:
        logger.warning(f"通知公司目标发布失败（不影响业务）：{str(e)}")
        return 0


def notify_goal_accepted(goal, actor):
    """
    P2-4: 通知目标被接收（目标接收后）
    
    Args:
        goal: StrategicGoal 对象（status='accepted'）
        actor: 接收人（User 对象）
    
    Returns:
        bool: 是否成功创建通知
    """
    try:
        if goal.status != 'accepted':
            logger.warning(f"目标 #{goal.id} 不是已接收状态，跳过通知")
            return False
        
        # 通知对象：创建人（可选：管理者）
        recipients = []
        if goal.created_by:
            recipients.append(goal.created_by)
        
        # 构建通知内容
        title = "[目标接收] 目标已被接收"
        content = f"{actor.get_full_name() or actor.username} 已接收目标《{goal.name}》。"
        
        # 创建通知
        count = 0
        for recipient in recipients:
            try:
                safe_approval_notification(
                    user=recipient,
                    title=title,
                    content=content,
                    object_type='goal',
                    object_id=str(goal.id),
                    event='goal_accepted',
                    is_read=False
                )
                count += 1
            except Exception as e:
                logger.warning(f"创建通知失败（用户：{recipient.username}）：{str(e)}")
        
        logger.info(f"成功创建 {count} 条目标接收通知（目标 #{goal.id}）")
        return count > 0
        
    except Exception as e:
        logger.warning(f"通知目标接收失败（不影响业务）：{str(e)}")
        return False


def notify_plan_accepted(plan, actor):
    """
    P2-4: 通知计划被接收（计划接收后）
    
    Args:
        plan: Plan 对象（status='accepted'）
        actor: 接收人（User 对象）
    
    Returns:
        bool: 是否成功创建通知
    """
    try:
        if plan.status != 'accepted':
            logger.warning(f"计划 #{plan.id} 不是已接收状态，跳过通知")
            return False
        
        # 通知对象：创建人（可选：管理者）
        recipients = []
        if plan.created_by:
            recipients.append(plan.created_by)
        
        # 构建通知内容
        title = "[计划接收] 计划已被接收"
        content = f"{actor.get_full_name() or actor.username} 已接收计划《{plan.name}》。"
        
        # 创建通知
        count = 0
        for recipient in recipients:
            try:
                safe_approval_notification(
                    user=recipient,
                    title=title,
                    content=content,
                    object_type='plan',
                    object_id=str(plan.id),
                    event='plan_accepted',
                    is_read=False
                )
                count += 1
            except Exception as e:
                logger.warning(f"创建通知失败（用户：{recipient.username}）：{str(e)}")
        
        logger.info(f"成功创建 {count} 条计划接收通知（计划 #{plan.id}）")
        return count > 0
        
    except Exception as e:
        logger.warning(f"通知计划接收失败（不影响业务）：{str(e)}")
        return False


def notify_personal_goal_published(goal):
    """
    P2-2: 通知员工接收目标（个人目标发布后）
    
    Args:
        goal: StrategicGoal 对象（level='personal', status='published', owner 已设置）
    
    Returns:
        bool: 是否成功创建通知
    """
    try:
        if goal.level != 'personal' or goal.status != 'published':
            logger.warning(f"目标 #{goal.id} 不是已发布的个人目标，跳过通知")
            return False
        
        if not goal.owner:
            logger.warning(f"目标 #{goal.id} 没有 owner，无法发送通知")
            return False
        
        # 构建通知内容
        title = "[目标分配] 您有一个待接收的目标"
        content = f"您有一个待接收的目标《{goal.name}》，请及时接收。"
        
        # 创建通知
        safe_approval_notification(
            user=goal.owner,
            title=title,
            content=content,
            object_type='goal',
            object_id=str(goal.id),
            event='personal_goal_published',
            is_read=False
        )
        
        logger.info(f"成功创建个人目标发布通知（目标 #{goal.id} → {goal.owner.username}）")
        return True
        
    except Exception as e:
        logger.warning(f"通知个人目标发布失败（不影响业务）：{str(e)}")
        return False


def notify_company_plan_published(plan):
    """
    P2-3: 通知员工创建个人计划（公司计划发布后）
    
    Args:
        plan: Plan 对象（level='company', status='published'）
    
    Returns:
        int: 成功创建的通知数量
    """
    try:
        if plan.level != 'company' or plan.status != 'published':
            logger.warning(f"计划 #{plan.id} 不是已发布的公司计划，跳过通知")
            return 0
        
        # 通知对象：公司内所有活跃员工（或根据业务规则筛选）
        # P2-3 简化版：通知所有活跃用户（后续可优化为按部门/角色筛选）
        from django.contrib.auth.models import User
        
        # 公司隔离
        recipients = User.objects.filter(is_active=True)
        if hasattr(plan, 'company') and plan.company:
            recipients = recipients.filter(profile__company=plan.company)
        
        # 排除创建人（创建人不需要通知自己）
        recipients = recipients.exclude(id=plan.created_by_id)
        
        # 构建通知内容
        title = "[计划发布] 请创建个人计划进行对齐"
        content = f"公司计划《{plan.name}》已发布，请创建个人计划进行对齐。"
        
        # 为每个员工创建通知
        count = 0
        for recipient in recipients:
            try:
                safe_approval_notification(
                    user=recipient,
                    title=title,
                    content=content,
                    object_type='plan',
                    object_id=str(plan.id),
                    event='company_plan_published',
                    is_read=False
                )
                count += 1
            except Exception as e:
                logger.warning(f"创建通知失败（用户：{recipient.username}）：{str(e)}")
        
        logger.info(f"成功创建 {count} 条公司计划发布通知（计划 #{plan.id}）")
        return count
        
    except Exception as e:
        logger.warning(f"通知公司计划发布失败（不影响业务）：{str(e)}")
        return 0


def notify_personal_plan_published(plan):
    """
    P2-3: 通知员工接收计划（个人计划发布后）
    
    Args:
        plan: Plan 对象（level='personal', status='published', owner 已设置）
    
    Returns:
        bool: 是否成功创建通知
    """
    try:
        if plan.level != 'personal' or plan.status != 'published':
            logger.warning(f"计划 #{plan.id} 不是已发布的个人计划，跳过通知")
            return False
        
        if not plan.owner:
            logger.warning(f"计划 #{plan.id} 没有 owner，无法发送通知")
            return False
        
        # 构建通知内容
        title = "[计划分配] 您有一个待接收的计划"
        content = f"您有一个待接收的计划《{plan.name}》，请及时接收。"
        
        # 创建通知
        safe_approval_notification(
            user=plan.owner,
            title=title,
            content=content,
            object_type='plan',
            object_id=str(plan.id),
            event='personal_plan_published',
            is_read=False
        )
        
        logger.info(f"成功创建个人计划发布通知（计划 #{plan.id} → {plan.owner.username}）")
        return True
        
    except Exception as e:
        logger.warning(f"通知个人计划发布失败（不影响业务）：{str(e)}")
        return False


def notify_approval_timeout(plan, days_overdue=3):
    """
    工作流强制推进：通知审批超时
    
    Args:
        plan: Plan 对象（状态为 pending_approval，审批时间超过指定天数）
        days_overdue: 超时天数，默认3天
    
    Returns:
        bool: 是否成功创建通知
    """
    try:
        # 接收人：审批人（拥有 approve_plan 权限的人）
        try:
            from django.contrib.auth.models import Permission
            perm = Permission.objects.get(
                codename='approve_plan',
                content_type__app_label='plan_management'
            )
            
            approvers = User.objects.filter(
                Q(user_permissions=perm) | Q(groups__permissions=perm)
            ).distinct()
            
            # 公司隔离：只筛选同公司
            if hasattr(plan, 'company') and plan.company:
                approvers = approvers.filter(profile__company=plan.company)
            
        except Permission.DoesNotExist:
            logger.warning("权限不存在：plan_management.approve_plan")
            return False
        
        if not approvers.exists():
            logger.warning(f"计划 #{plan.id} 没有找到审批人")
            return False
        
        # 检查是否已经发送过通知（避免重复发送）
        from datetime import timedelta
        from django.utils import timezone
        count = 0
        for approver in approvers:
            recent_notification = False
            if ApprovalNotification:
                recent_notification = ApprovalNotification.objects.filter(
                    user=approver,
                    object_type='plan',
                    object_id=str(plan.id),
                    event='approval_timeout',
                    created_at__gte=timezone.now() - timedelta(days=1)  # 1天内不重复发送
                ).exists()
            
            if recent_notification:
                logger.debug(f"计划 #{plan.id} 的审批超时通知已在1天内发送给 {approver.username}，跳过")
                continue
            
            # 构建通知内容
            title = "[提醒] 计划审批超时，请尽快处理"
            content = f"计划《{plan.name}》已提交审批超过{days_overdue}天，请尽快处理。"
            
            # 创建通知
            try:
                safe_approval_notification(
                    user=approver,
                    title=title,
                    content=content,
                    object_type='plan',
                    object_id=str(plan.id),
                    event='approval_timeout',  # 新增事件类型
                    is_read=False
                )
                count += 1
            except Exception as e:
                logger.warning(f"创建审批超时通知失败（用户：{approver.username}）：{str(e)}")
        
        logger.info(f"成功创建 {count} 条审批超时通知（计划 #{plan.id}）")
        return count > 0
        
    except Exception as e:
        logger.warning(f"通知审批超时失败（不影响业务）：{str(e)}")
        return False

