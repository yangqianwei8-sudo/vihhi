# -*- coding: utf-8 -*-
"""
【已废弃，不得被任何路由/页面引用】

本文件由原 services.py 重命名而来，仅作封存。产值计算权威为 services.calculator_v1，
API 权威为 GET /api/output/v1/opportunity/<id>/。禁止从本模块导入或调用。
见 backend/docs/output_value_v1_execution.md。
"""
# 以下为原产值计算服务（旧版：按事件/项目记录产值），从 settlement_center 迁移而来。
from decimal import Decimal
from django.db import transaction
from django.db.models import Sum, Count
from django.utils import timezone
from .models import (
    OutputValueStage, OutputValueMilestone, OutputValueEvent, OutputValueRecord
)
from backend.apps.production_management.models import Project
from backend.apps.system_management.models import User


def get_base_amount(project, base_amount_type):
    """获取项目的计取基数"""
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
    """根据角色编码找到责任人"""
    if role_code == 'business_manager':
        return project.business_manager
    elif role_code == 'project_manager':
        return project.project_manager
    elif role_code == 'technical_manager':
        return User.objects.filter(roles__code='technical_manager', is_active=True).first()
    elif role_code == 'professional_engineer':
        from backend.apps.production_management.models import ProjectTeam
        team_member = ProjectTeam.objects.filter(
            project=project, role='professional_engineer', is_active=True
        ).select_related('user').first()
        return team_member.user if team_member else None
    elif role_code == 'professional_lead':
        from backend.apps.production_management.models import ProjectTeam
        team_member = ProjectTeam.objects.filter(
            project=project, role='professional_lead', is_active=True
        ).select_related('user').first()
        return team_member.user if team_member else None
    elif role_code == 'cost_manager':
        return User.objects.filter(roles__code='cost_manager', is_active=True).first()
    elif role_code == 'cost_engineer':
        return User.objects.filter(roles__code='cost_engineer', is_active=True).first()
    elif role_code == 'cost_team':
        return User.objects.filter(roles__code='cost_team', is_active=True).first()
    elif role_code == 'admin_office':
        return User.objects.filter(roles__code='admin_office', is_active=True).first()
    elif role_code == 'finance_supervisor':
        return User.objects.filter(roles__code='finance_supervisor', is_active=True).first()
    return None


@transaction.atomic
def calculate_output_value(project, event_code, trigger_condition=None, responsible_user=None):
    """计算并记录产值（已废弃，勿引用）"""
    try:
        event = OutputValueEvent.objects.filter(
            code=event_code, is_active=True
        ).select_related('milestone', 'milestone__stage').first()
        if not event and trigger_condition:
            event = OutputValueEvent.objects.filter(
                trigger_condition=trigger_condition, is_active=True
            ).select_related('milestone', 'milestone__stage').first()
        if not event:
            return None
        milestone = event.milestone
        stage = milestone.stage
        base_amount = get_base_amount(project, stage.base_amount_type)
        if base_amount <= 0:
            return None
        if not responsible_user:
            responsible_user = find_responsible_user(project, event.responsible_role_code)
        if not responsible_user:
            return None
        existing_record = OutputValueRecord.objects.filter(
            project=project, event=event, status__in=['calculated', 'confirmed']
        ).first()
        if existing_record:
            return existing_record
        calculated_value = event.calculate_value(base_amount)
        record = OutputValueRecord.objects.create(
            project=project, stage=stage, milestone=milestone, event=event,
            responsible_user=responsible_user, base_amount=base_amount,
            base_amount_type=stage.base_amount_type,
            stage_percentage=stage.stage_percentage,
            milestone_percentage=milestone.milestone_percentage,
            event_percentage=event.event_percentage,
            calculated_value=calculated_value, status='calculated',
            calculated_time=timezone.now(),
        )
        return record
    except Exception as e:
        import logging
        logging.getLogger(__name__).error(
            "计算产值失败: project=%s, event_code=%s, error=%s", project.id, event_code, str(e)
        )
        return None


def calculate_output_value_by_trigger(project, trigger_condition, responsible_user=None):
    """通过触发条件计算产值（已废弃，勿引用）"""
    event = OutputValueEvent.objects.filter(
        trigger_condition=trigger_condition, is_active=True
    ).select_related('milestone', 'milestone__stage').first()
    if not event:
        return None
    return calculate_output_value(project, event.code, trigger_condition, responsible_user)


def get_user_output_value_summary(user, start_date=None, end_date=None):
    """获取用户的产值汇总（已废弃，勿引用）"""
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
    """获取项目的产值汇总（已废弃，勿引用）"""
    if isinstance(project, int):
        project = Project.objects.get(id=project)
    records = OutputValueRecord.objects.filter(
        project=project, status__in=['calculated', 'confirmed']
    ).select_related('stage', 'milestone', 'event', 'responsible_user')
    total_value = records.aggregate(total=Sum('calculated_value'))['total'] or Decimal('0')
    confirmed_value = records.filter(status='confirmed').aggregate(
        total=Sum('calculated_value')
    )['total'] or Decimal('0')
    calculated_value = records.filter(status='calculated').aggregate(
        total=Sum('calculated_value')
    )['total'] or Decimal('0')
    stage_stats = records.values('stage__name', 'stage__code').annotate(
        total=Sum('calculated_value'), count=Count('id')
    ).order_by('stage__order')
    user_stats = records.values(
        'responsible_user__id', 'responsible_user__username',
        'responsible_user__first_name', 'responsible_user__last_name'
    ).annotate(total=Sum('calculated_value'), count=Count('id')).order_by('-total')
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
    """获取项目产值统计用于结算（已废弃，勿引用）"""
    summary = get_project_output_value_summary(project)
    return {
        'total_output_value': summary['total_value'],
        'confirmed_output_value': summary['confirmed_value'],
        'records_count': summary['total_records'],
    }
