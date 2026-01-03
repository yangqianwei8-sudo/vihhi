"""
产值计算服务
提供产值自动计算的相关功能
"""
from decimal import Decimal
from django.db import transaction
from django.db.models import Sum, Count
from django.utils import timezone
from backend.apps.settlement_center.models import (
    OutputValueStage, OutputValueMilestone, OutputValueEvent, OutputValueRecord,
    ServiceFeeSettlementScheme, ServiceFeeSegmentedRate, ServiceFeeJumpPointRate,
    ServiceFeeUnitCapDetail
)
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


# ==================== 服务费结算方案服务 ====================

def get_service_fee_scheme(contract=None, project=None, scheme_id=None, contract_id=None, project_id=None):
    """获取服务费结算方案
    
    Args:
        contract: 合同实例（可选）
        project: 项目实例（可选）
        scheme_id: 方案ID（可选，优先使用）
        contract_id: 合同ID（可选，如果contract未提供）
        project_id: 项目ID（可选，如果project未提供）
    
    Returns:
        ServiceFeeSettlementScheme 实例或 None
    """
    if scheme_id:
        try:
            return ServiceFeeSettlementScheme.objects.get(id=scheme_id, is_active=True)
        except ServiceFeeSettlementScheme.DoesNotExist:
            return None
    
    # 如果提供了ID但没有实例，尝试获取实例
    if contract_id and not contract:
        from backend.apps.production_management.models import BusinessContract
        try:
            contract = BusinessContract.objects.get(id=contract_id)
        except BusinessContract.DoesNotExist:
            pass
    
    if project_id and not project:
        from backend.apps.production_management.models import Project
        try:
            project = Project.objects.get(id=project_id)
        except Project.DoesNotExist:
            pass
    
    # 优先查找项目特定的方案
    if project:
        scheme = ServiceFeeSettlementScheme.objects.filter(
            project=project,
            is_active=True
        ).order_by('sort_order', '-created_time').first()
        if scheme:
            return scheme
    
    # 查找合同关联的方案
    if contract:
        scheme = ServiceFeeSettlementScheme.objects.filter(
            contract=contract,
            is_active=True
        ).order_by('sort_order', '-created_time').first()
        if scheme:
            return scheme
    
    # 查找默认全局方案
    scheme = ServiceFeeSettlementScheme.objects.filter(
        contract__isnull=True,
        project__isnull=True,
        is_default=True,
        is_active=True
    ).order_by('sort_order', '-created_time').first()
    
    if scheme:
        return scheme
    
    # 查找任意全局方案
    return ServiceFeeSettlementScheme.objects.filter(
        contract__isnull=True,
        project__isnull=True,
        is_active=True
    ).order_by('sort_order', '-created_time').first()


def calculate_service_fee_by_scheme(scheme, saving_amount=None, service_area=None,
                                    area_type=None, unit_cap_details=None):
    """根据结算方案计算服务费
    
    Args:
        scheme: ServiceFeeSettlementScheme 实例或方案ID
        saving_amount: 节省金额（按实结算时使用）
        service_area: 服务面积（固定单价时使用）
        area_type: 面积类型（可选，如果scheme中已配置则不需要）
        unit_cap_details: 单价封顶明细列表，格式：
            [{'unit_name': '单体名称', 'area': 面积, 'cap_unit_price': 封顶单价}]
            或从ServiceFeeUnitCapDetail自动获取
    
    Returns:
        dict: {
            'settlement_price': Decimal,  # 结算价（应用封顶和保底前）
            'final_fee': Decimal,        # 最终服务费（应用封顶和保底后）
            'fixed_part': Decimal,       # 固定部分（组合方式时）
            'actual_part': Decimal,      # 按实结算部分（组合方式时）
            'cap_fee': Decimal,         # 封顶费
            # 'minimum_fee': Decimal,      # 保底费 - 已删除
            'calculation_details': dict  # 计算明细
        }
    """
    from decimal import Decimal
    
    if isinstance(scheme, int):
        scheme = ServiceFeeSettlementScheme.objects.get(id=scheme)
    
    if not scheme or not scheme.is_active:
        return {
            'settlement_price': Decimal('0'),
            'final_fee': Decimal('0'),
            'fixed_part': Decimal('0'),
            'actual_part': Decimal('0'),
            'cap_fee': None,
            # 'minimum_fee': None,  # 保底费 - 已删除
            'calculation_details': {}
        }
    
    # 如果单价封顶且未提供明细，尝试从方案中获取
    if scheme.has_cap_fee and scheme.cap_type == 'unit_cap' and not unit_cap_details:
        unit_cap_details = []
        for detail in scheme.unit_cap_details.all():
            unit_cap_details.append({
                'unit_name': detail.unit_name,
                'area': service_area if service_area else Decimal('0'),
                'cap_unit_price': detail.cap_unit_price
            })
    
    # 调用方案的calculate_settlement_fee方法
    final_fee = scheme.calculate_settlement_fee(
        saving_amount=saving_amount,
        service_area=service_area,
        unit_cap_details=unit_cap_details
    )
    
    # 计算结算价（应用封顶和保底前）
    settlement_price = Decimal('0')
    fixed_part = Decimal('0')
    actual_part = Decimal('0')
    
    if scheme.settlement_method == 'fixed_total':
        settlement_price = scheme.fixed_total_price or Decimal('0')
        fixed_part = settlement_price
    
    elif scheme.settlement_method == 'fixed_unit':
        if service_area and scheme.fixed_unit_price:
            settlement_price = Decimal(str(service_area)) * scheme.fixed_unit_price
            fixed_part = settlement_price
    
    elif scheme.settlement_method == 'cumulative_commission':
        if saving_amount and scheme.cumulative_rate:
            settlement_price = Decimal(str(saving_amount)) * (scheme.cumulative_rate / 100)
            actual_part = settlement_price
    
    elif scheme.settlement_method == 'segmented_commission':
        if saving_amount:
            settlement_price = scheme._calculate_segmented_commission(saving_amount)
            actual_part = settlement_price
    
    elif scheme.settlement_method == 'jump_point_commission':
        if saving_amount:
            settlement_price = scheme._calculate_jump_point_commission(saving_amount)
            actual_part = settlement_price
    
    elif scheme.settlement_method == 'combined':
        # 固定部分
        if scheme.combined_fixed_method == 'fixed_total':
            fixed_part = scheme.combined_fixed_total or Decimal('0')
        elif scheme.combined_fixed_method == 'fixed_unit':
            if service_area and scheme.combined_fixed_unit:
                fixed_part = Decimal(str(service_area)) * scheme.combined_fixed_unit
        
        # 按实结算部分
        if saving_amount:
            if scheme.combined_actual_method == 'cumulative_commission':
                if scheme.combined_cumulative_rate:
                    base_amount = Decimal(str(saving_amount))
                    if scheme.combined_deduct_fixed:
                        base_amount = max(Decimal('0'), base_amount - fixed_part)
                    actual_part = base_amount * (scheme.combined_cumulative_rate / 100)
            
            elif scheme.combined_actual_method == 'segmented_commission':
                base_amount = Decimal(str(saving_amount))
                if scheme.combined_deduct_fixed:
                    base_amount = max(Decimal('0'), base_amount - fixed_part)
                actual_part = scheme._calculate_segmented_commission(base_amount)
            
            elif scheme.combined_actual_method == 'jump_point_commission':
                base_amount = Decimal(str(saving_amount))
                if scheme.combined_deduct_fixed:
                    base_amount = max(Decimal('0'), base_amount - fixed_part)
                actual_part = scheme._calculate_jump_point_commission(base_amount)
        
        settlement_price = fixed_part + actual_part
    
    # 计算封顶费和保底费
    cap_fee = None
    if scheme.has_cap_fee:
        if scheme.cap_type == 'total_cap':
            cap_fee = scheme.total_cap_amount
        elif scheme.cap_type == 'unit_cap' and unit_cap_details:
            cap_fee = Decimal('0')
            for detail in unit_cap_details:
                area = Decimal(str(detail.get('area', 0)))
                cap_unit_price = Decimal(str(detail.get('cap_unit_price', 0)))
                cap_fee += area * cap_unit_price
    
    # 保底费计算已删除
    # minimum_fee = None
    # if scheme.has_minimum_fee:
    #     minimum_fee = scheme.minimum_fee_amount
    
    return {
        'settlement_price': settlement_price,
        'final_fee': final_fee,
        'fixed_part': fixed_part,
        'actual_part': actual_part,
        'cap_fee': cap_fee,
        # 'minimum_fee': minimum_fee,  # 保底费 - 已删除
        'calculation_details': {
            'scheme_id': scheme.id,
            'scheme_name': scheme.name,
            'settlement_method': scheme.get_settlement_method_display(),
            'saving_amount': saving_amount,
            'service_area': service_area,
        }
    }


def get_project_area_by_type(project, area_type):
    """根据面积类型获取项目的面积
    
    Args:
        project: Project 实例
        area_type: 面积类型编码（drawing_building_area, drawing_structure_area等）
    
    Returns:
        Decimal: 面积值，如果不存在则返回0
    """
    from decimal import Decimal
    
    # 从项目对象获取面积值
    area_value = getattr(project, area_type, None)
    if area_value:
        return Decimal(str(area_value))
    
    return Decimal('0')


# ==================== 服务费结算方案统计和工具函数 ====================

def get_scheme_statistics(scheme_id=None, contract_id=None, project_id=None):
    """获取结算方案统计信息
    
    Args:
        scheme_id: 方案ID（可选）
        contract_id: 合同ID（可选）
        project_id: 项目ID（可选）
    
    Returns:
        dict: 统计信息
    """
    from django.db.models import Count, Sum, Avg, Max, Min
    from backend.apps.settlement_center.models import ProjectSettlement
    
    queryset = ServiceFeeSettlementScheme.objects.filter(is_active=True)
    
    if scheme_id:
        queryset = queryset.filter(id=scheme_id)
    if contract_id:
        queryset = queryset.filter(contract_id=contract_id)
    if project_id:
        queryset = queryset.filter(project_id=project_id)
    
    # 方案统计
    scheme_stats = queryset.aggregate(
        total_count=Count('id'),
        by_method=Count('id', distinct=True)
    )
    
    # 使用统计（关联的结算单）
    usage_stats = ProjectSettlement.objects.filter(
        service_fee_scheme__in=queryset
    ).aggregate(
        usage_count=Count('id'),
        total_settlement_amount=Sum('total_settlement_amount'),
        avg_settlement_amount=Avg('total_settlement_amount'),
        max_settlement_amount=Max('total_settlement_amount'),
        min_settlement_amount=Min('total_settlement_amount')
    )
    
    # 按结算方式统计
    method_stats = queryset.values('settlement_method').annotate(
        count=Count('id')
    ).order_by('-count')
    
    return {
        'scheme_stats': scheme_stats,
        'usage_stats': usage_stats,
        'method_stats': list(method_stats),
        'total_schemes': scheme_stats['total_count'],
        'total_usage': usage_stats['usage_count'] or 0,
    }


def get_scheme_usage_by_contract(contract_id):
    """获取合同使用的结算方案列表
    
    Args:
        contract_id: 合同ID
    
    Returns:
        list: 结算方案列表
    """
    schemes = ServiceFeeSettlementScheme.objects.filter(
        contract_id=contract_id,
        is_active=True
    ).order_by('sort_order', '-created_time')
    
    return list(schemes)


def get_scheme_usage_by_project(project_id):
    """获取项目使用的结算方案列表
    
    Args:
        project_id: 项目ID
    
    Returns:
        list: 结算方案列表
    """
    schemes = ServiceFeeSettlementScheme.objects.filter(
        project_id=project_id,
        is_active=True
    ).order_by('sort_order', '-created_time')
    
    return list(schemes)


def validate_scheme_configuration(scheme):
    """验证结算方案配置的完整性
    
    Args:
        scheme: ServiceFeeSettlementScheme 实例
    
    Returns:
        dict: {
            'is_valid': bool,
            'errors': list,
            'warnings': list
        }
    """
    from decimal import Decimal
    
    errors = []
    warnings = []
    
    # 验证结算方式配置
    if scheme.settlement_method == 'fixed_total':
        if not scheme.fixed_total_price:
            errors.append('固定总价方式必须填写固定总价')
    
    elif scheme.settlement_method == 'fixed_unit':
        if not scheme.fixed_unit_price:
            errors.append('固定单价方式必须填写固定单价')
        if not scheme.area_type:
            errors.append('固定单价方式必须选择面积类型')
    
    elif scheme.settlement_method == 'cumulative_commission':
        if not scheme.cumulative_rate:
            errors.append('累计提成方式必须填写取费系数')
        elif scheme.cumulative_rate < 0 or scheme.cumulative_rate > 100:
            errors.append('取费系数必须在0-100之间')
    
    elif scheme.settlement_method == 'segmented_commission':
        if not scheme.segmented_rates.filter(is_active=True).exists():
            errors.append('分段递增提成方式必须至少配置一个分段')
        else:
            # 检查分段配置是否合理
            segments = scheme.segmented_rates.filter(is_active=True).order_by('threshold')
            prev_threshold = Decimal('0')
            for seg in segments:
                if seg.threshold <= prev_threshold:
                    errors.append(f'分段阈值必须递增：当前分段阈值 {seg.threshold} 应大于前一个阈值 {prev_threshold}')
                if seg.rate < 0 or seg.rate > 100:
                    errors.append(f'分段 {seg.threshold} 的取费系数必须在0-100之间')
                prev_threshold = seg.threshold
    
    elif scheme.settlement_method == 'jump_point_commission':
        if not scheme.jump_point_rates.filter(is_active=True).exists():
            errors.append('跳点提成方式必须至少配置一个跳点')
        else:
            # 检查跳点配置
            jump_points = scheme.jump_point_rates.filter(is_active=True).order_by('threshold')
            for jp in jump_points:
                if jp.rate < 0 or jp.rate > 100:
                    errors.append(f'跳点 {jp.threshold} 的取费系数必须在0-100之间')
    
    elif scheme.settlement_method == 'combined':
        if not scheme.combined_fixed_method:
            errors.append('组合方式必须选择固定部分方式')
        if not scheme.combined_actual_method:
            errors.append('组合方式必须选择按实结算部分方式')
        
        # 验证固定部分
        if scheme.combined_fixed_method == 'fixed_total' and not scheme.combined_fixed_total:
            errors.append('组合方式固定部分为固定总价时必须填写金额')
        elif scheme.combined_fixed_method == 'fixed_unit':
            if not scheme.combined_fixed_unit:
                errors.append('组合方式固定部分为固定单价时必须填写单价')
            if not scheme.combined_fixed_area_type:
                errors.append('组合方式固定部分为固定单价时必须选择面积类型')
        
        # 验证按实结算部分
        if scheme.combined_actual_method == 'cumulative_commission':
            if not scheme.combined_cumulative_rate:
                errors.append('组合方式按实结算部分为累计提成时必须填写系数')
        elif scheme.combined_actual_method == 'segmented_commission':
            if not scheme.segmented_rates.filter(is_active=True).exists():
                errors.append('组合方式按实结算部分为分段递增提成时必须至少配置一个分段')
        elif scheme.combined_actual_method == 'jump_point_commission':
            if not scheme.jump_point_rates.filter(is_active=True).exists():
                errors.append('组合方式按实结算部分为跳点提成时必须至少配置一个跳点')
    
    # 验证封顶费
    if scheme.has_cap_fee:
        if not scheme.cap_type or scheme.cap_type == 'no_cap':
            errors.append('设置封顶费时必须选择封顶费类型')
        elif scheme.cap_type == 'total_cap':
            if not scheme.total_cap_amount:
                errors.append('总价封顶时必须填写封顶金额')
            elif scheme.total_cap_amount < 0:
                errors.append('封顶金额不能为负数')
        elif scheme.cap_type == 'unit_cap':
            if not scheme.unit_cap_details.exists():
                errors.append('单价封顶时必须至少配置一个单体明细')
            else:
                for detail in scheme.unit_cap_details.all():
                    if detail.cap_unit_price < 0:
                        errors.append(f'单体 {detail.unit_name} 的封顶单价不能为负数')
    
    # 验证保底费
    if scheme.has_minimum_fee:
        if not scheme.minimum_fee_amount:
            errors.append('设置保底费时必须填写保底费金额')
        elif scheme.minimum_fee_amount < 0:
            errors.append('保底费金额不能为负数')
        
        # 检查保底费是否大于封顶费
        if scheme.has_cap_fee and scheme.cap_type == 'total_cap':
            if scheme.minimum_fee_amount > scheme.total_cap_amount:
                warnings.append('保底费金额大于封顶费金额，可能导致无法应用')
    
    return {
        'is_valid': len(errors) == 0,
        'errors': errors,
        'warnings': warnings
    }


def duplicate_scheme(scheme, new_name=None, new_contract=None, new_project=None):
    """复制结算方案
    
    Args:
        scheme: ServiceFeeSettlementScheme 实例
        new_name: 新方案名称（可选）
        new_contract: 新关联合同（可选）
        new_project: 新关联项目（可选）
    
    Returns:
        ServiceFeeSettlementScheme: 新创建的方案实例
    """
    from django.db import transaction
    
    with transaction.atomic():
        # 复制主方案
        new_scheme = ServiceFeeSettlementScheme.objects.create(
            name=new_name or f"{scheme.name} (副本)",
            code=None,  # 代码唯一，不复制
            description=scheme.description,
            contract=new_contract or scheme.contract,
            project=new_project or scheme.project,
            settlement_method=scheme.settlement_method,
            fixed_total_price=scheme.fixed_total_price,
            fixed_unit_price=scheme.fixed_unit_price,
            area_type=scheme.area_type,
            cumulative_rate=scheme.cumulative_rate,
            combined_fixed_method=scheme.combined_fixed_method,
            combined_fixed_total=scheme.combined_fixed_total,
            combined_fixed_unit=scheme.combined_fixed_unit,
            combined_fixed_area_type=scheme.combined_fixed_area_type,
            combined_actual_method=scheme.combined_actual_method,
            combined_cumulative_rate=scheme.combined_cumulative_rate,
            combined_deduct_fixed=scheme.combined_deduct_fixed,
            has_cap_fee=scheme.has_cap_fee,
            cap_type=scheme.cap_type,
            total_cap_amount=scheme.total_cap_amount,
            has_minimum_fee=scheme.has_minimum_fee,
            minimum_fee_amount=scheme.minimum_fee_amount,
            is_active=scheme.is_active,
            is_default=False,  # 副本不设为默认
            sort_order=scheme.sort_order,
            created_by=scheme.created_by,
        )
        
        # 复制分段递增提成配置
        for rate in scheme.segmented_rates.all():
            ServiceFeeSegmentedRate.objects.create(
                scheme=new_scheme,
                threshold=rate.threshold,
                rate=rate.rate,
                description=rate.description,
                order=rate.order,
                is_active=rate.is_active,
            )
        
        # 复制跳点提成配置
        for rate in scheme.jump_point_rates.all():
            ServiceFeeJumpPointRate.objects.create(
                scheme=new_scheme,
                threshold=rate.threshold,
                rate=rate.rate,
                description=rate.description,
                order=rate.order,
                is_active=rate.is_active,
            )
        
        # 复制单价封顶费明细
        for detail in scheme.unit_cap_details.all():
            ServiceFeeUnitCapDetail.objects.create(
                scheme=new_scheme,
                unit_name=detail.unit_name,
                cap_unit_price=detail.cap_unit_price,
                description=detail.description,
                order=detail.order,
            )
        
        return new_scheme
