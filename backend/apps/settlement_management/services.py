"""
产值计算服务
提供产值自动计算的相关功能
"""
from decimal import Decimal
from django.db import transaction
from django.db.models import Sum, Count
from django.utils import timezone
from backend.apps.settlement_management.models import OutputValueStage, OutputValueMilestone, OutputValueEvent, OutputValueRecord
from backend.apps.production_management.models import Project
from backend.apps.system_management.models import User


def get_base_amount(project, base_amount_type):
    """获取项目的计取基数
    
    Args:
        project: Project 实例
        base_amount_type: 基数类型（registration_amount, intention_amount, contract_amount, settlement_amount, payment_amount）
    
    Returns:
        Decimal: 计取基数金额
    """
    # 获取合同金额作为默认值
    contract_amount = getattr(project, 'contract_amount', None) or Decimal('0')
    
    amount_map = {
        'registration_amount': getattr(project, 'registration_amount', None) or contract_amount or Decimal('0'),
        'intention_amount': getattr(project, 'intention_amount', None) or contract_amount or Decimal('0'),
        'contract_amount': contract_amount,
        'settlement_amount': getattr(project, 'settlement_amount', None) or contract_amount or Decimal('0'),
        'payment_amount': getattr(project, 'total_payment_received', None) or getattr(project, 'payment_received', None) or Decimal('0'),
    }
    return amount_map.get(base_amount_type, Decimal('0'))


def find_responsible_user(project, role_code):
    """根据角色编码找到责任人
    
    Args:
        project: Project 实例
        role_code: 角色编码（如 business_manager, project_manager 等）
    
    Returns:
        User 实例或 None
    """
    if role_code == 'business_manager':
        return project.business_manager
    elif role_code == 'project_manager':
        return project.project_manager
    elif role_code == 'technical_manager':
        # 查找技术部经理
        from backend.apps.system_management.models import User
        return User.objects.filter(roles__code='technical_manager', is_active=True).first()
    elif role_code == 'professional_engineer':
        # 从项目团队中查找专业工程师
        from backend.apps.production_management.models import ProjectTeam
        team_member = ProjectTeam.objects.filter(
            project=project,
            role='professional_engineer',
            is_active=True
        ).select_related('user').first()
        return team_member.user if team_member else None
    elif role_code == 'professional_lead':
        # 从项目团队中查找专业负责人
        from backend.apps.production_management.models import ProjectTeam
        team_member = ProjectTeam.objects.filter(
            project=project,
            role='professional_lead',
            is_active=True
        ).select_related('user').first()
        return team_member.user if team_member else None
    elif role_code == 'cost_manager':
        # 查找造价部经理
        from backend.apps.system_management.models import User
        return User.objects.filter(roles__code='cost_manager', is_active=True).first()
    elif role_code == 'cost_engineer':
        # 查找造价工程师
        from backend.apps.system_management.models import User
        return User.objects.filter(roles__code='cost_engineer', is_active=True).first()
    elif role_code == 'cost_team':
        # 查找造价审核人
        from backend.apps.system_management.models import User
        return User.objects.filter(roles__code='cost_team', is_active=True).first()
    elif role_code == 'admin_office':
        # 查找行政主管
        from backend.apps.system_management.models import User
        return User.objects.filter(roles__code='admin_office', is_active=True).first()
    elif role_code == 'finance_supervisor':
        # 查找财务主管
        from backend.apps.system_management.models import User
        return User.objects.filter(roles__code='finance_supervisor', is_active=True).first()
    
    return None


@transaction.atomic
def calculate_output_value(project, event_code, trigger_condition=None, responsible_user=None):
    """计算并记录产值
    
    Args:
        project: Project 实例
        event_code: 事件编码（如 'create_project', 'configure_team' 等）
        trigger_condition: 触发条件（可选，用于匹配事件）
        responsible_user: 责任人（可选，如果不提供则根据角色自动查找）
    
    Returns:
        OutputValueRecord 实例或 None
    """
    try:
        # 查找对应的事件
        event = OutputValueEvent.objects.filter(
            code=event_code,
            is_active=True
        ).select_related('milestone', 'milestone__stage').first()
        
        if not event:
            # 如果通过 code 找不到，尝试通过 trigger_condition 查找
            if trigger_condition:
                event = OutputValueEvent.objects.filter(
                    trigger_condition=trigger_condition,
                    is_active=True
                ).select_related('milestone', 'milestone__stage').first()
        
        if not event:
            # 事件不存在，跳过计算
            return None
        
        milestone = event.milestone
        stage = milestone.stage
        
        # 获取计取基数
        base_amount = get_base_amount(project, stage.base_amount_type)
        
        if base_amount <= 0:
            # 基数金额为0或未设置，跳过计算
            return None
        
        # 查找责任人
        if not responsible_user:
            responsible_user = find_responsible_user(project, event.responsible_role_code)
        
        if not responsible_user:
            # 找不到责任人，跳过计算
            return None
        
        # 检查是否已经计算过该事件
        existing_record = OutputValueRecord.objects.filter(
            project=project,
            event=event,
            status__in=['calculated', 'confirmed']
        ).first()
        
        if existing_record:
            # 已经计算过，返回现有记录
            return existing_record
        
        # 计算产值
        calculated_value = event.calculate_value(base_amount)
        
        # 创建产值记录
        record = OutputValueRecord.objects.create(
            project=project,
            stage=stage,
            milestone=milestone,
            event=event,
            responsible_user=responsible_user,
            base_amount=base_amount,
            base_amount_type=stage.base_amount_type,
            stage_percentage=stage.stage_percentage,
            milestone_percentage=milestone.milestone_percentage,
            event_percentage=event.event_percentage,
            calculated_value=calculated_value,
            status='calculated',
            calculated_time=timezone.now(),
        )
        
        return record
    
    except Exception as e:
        # 记录错误但不抛出异常，避免影响主流程
        import logging
        logger = logging.getLogger(__name__)
        logger.error(f"计算产值失败: project={project.id}, event_code={event_code}, error={str(e)}")
        return None


def calculate_output_value_by_trigger(project, trigger_condition, responsible_user=None):
    """通过触发条件计算产值（更通用的方法）
    
    Args:
        project: Project 实例
        trigger_condition: 触发条件（项目流程事件的标识）
        responsible_user: 责任人（可选）
    
    Returns:
        OutputValueRecord 实例或 None
    """
    event = OutputValueEvent.objects.filter(
        trigger_condition=trigger_condition,
        is_active=True
    ).select_related('milestone', 'milestone__stage').first()
    
    if not event:
        return None
    
    return calculate_output_value(project, event.code, trigger_condition, responsible_user)


def get_user_output_value_summary(user, start_date=None, end_date=None):
    """获取用户的产值汇总
    
    Args:
        user: User 实例
        start_date: 开始日期（可选）
        end_date: 结束日期（可选）
    
    Returns:
        dict: 包含总产值、已确认产值等统计信息
    """
    records = OutputValueRecord.objects.filter(responsible_user=user)
    
    if start_date:
        records = records.filter(calculated_time__gte=start_date)
    if end_date:
        records = records.filter(calculated_time__lte=end_date)
    
    total_value = records.filter(status__in=['calculated', 'confirmed']).aggregate(
        total=Sum('calculated_value')
    )['total'] or Decimal('0')
    
    confirmed_value = records.filter(status='confirmed').aggregate(
        total=Sum('calculated_value')
    )['total'] or Decimal('0')
    
    return {
        'total_records': records.count(),
        'total_value': total_value,
        'confirmed_value': confirmed_value,
        'pending_value': total_value - confirmed_value,
    }


def get_project_output_value_summary(project):
    """获取项目的产值汇总
    
    Args:
        project: Project 实例或项目ID
    
    Returns:
        dict: 包含总产值、已确认产值、产值记录等统计信息
    """
    if isinstance(project, int):
        from backend.apps.production_management.models import Project
        project = Project.objects.get(id=project)
    
    records = OutputValueRecord.objects.filter(
        project=project,
        status__in=['calculated', 'confirmed']
    ).select_related('stage', 'milestone', 'event', 'responsible_user')
    
    total_value = records.aggregate(
        total=Sum('calculated_value')
    )['total'] or Decimal('0')
    
    confirmed_value = records.filter(status='confirmed').aggregate(
        total=Sum('calculated_value')
    )['total'] or Decimal('0')
    
    calculated_value = records.filter(status='calculated').aggregate(
        total=Sum('calculated_value')
    )['total'] or Decimal('0')
    
    # 按阶段统计
    stage_stats = records.values('stage__name', 'stage__code').annotate(
        total=Sum('calculated_value'),
        count=Count('id')
    ).order_by('stage__order')
    
    # 按责任人统计
    user_stats = records.values(
        'responsible_user__id',
        'responsible_user__username',
        'responsible_user__first_name',
        'responsible_user__last_name'
    ).annotate(
        total=Sum('calculated_value'),
        count=Count('id')
    ).order_by('-total')
    
    return {
        'project': project,
        'total_records': records.count(),
        'total_value': total_value,
        'confirmed_value': confirmed_value,
        'calculated_value': calculated_value,
        'pending_value': calculated_value,
        'records': records,
        'stage_stats': stage_stats,
        'user_stats': user_stats,
    }


def get_project_output_value_for_settlement(project):
    """获取项目产值统计（用于结算）
    
    Args:
        project: Project 实例或项目ID
    
    Returns:
        dict: 包含累计产值、已确认产值等用于结算的产值信息
    """
    summary = get_project_output_value_summary(project)
    return {
        'total_output_value': summary['total_value'],
        'confirmed_output_value': summary['confirmed_value'],
        'records_count': summary['total_records'],
    }
