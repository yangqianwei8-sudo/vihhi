"""
服务费结算方案服务
从 settlement_center 迁入，使用 settlement_management 的 models
"""
from decimal import Decimal
from django.db import transaction
from django.db.models import Sum, Count, Avg, Max, Min

from .models import (
    ServiceFeeSettlementScheme,
    ServiceFeeSegmentedRate,
    ServiceFeeJumpPointRate,
    ServiceFeeUnitCapDetail,
    ProjectSettlement,
)


def get_service_fee_scheme(contract=None, project=None, scheme_id=None, contract_id=None, project_id=None):
    """获取服务费结算方案"""
    if scheme_id:
        try:
            return ServiceFeeSettlementScheme.objects.get(id=scheme_id, is_active=True)
        except ServiceFeeSettlementScheme.DoesNotExist:
            return None

    if contract_id and not contract:
        from backend.apps.contract_management.models import BusinessContract
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

    if project:
        scheme = ServiceFeeSettlementScheme.objects.filter(
            project=project, is_active=True
        ).order_by('sort_order', '-created_time').first()
        if scheme:
            return scheme

    if contract:
        scheme = ServiceFeeSettlementScheme.objects.filter(
            contract=contract, is_active=True
        ).order_by('sort_order', '-created_time').first()
        if scheme:
            return scheme

    scheme = ServiceFeeSettlementScheme.objects.filter(
        contract__isnull=True, project__isnull=True,
        is_default=True, is_active=True
    ).order_by('sort_order', '-created_time').first()
    if scheme:
        return scheme

    return ServiceFeeSettlementScheme.objects.filter(
        contract__isnull=True, project__isnull=True, is_active=True
    ).order_by('sort_order', '-created_time').first()


def calculate_service_fee_by_scheme(scheme, saving_amount=None, service_area=None,
                                    area_type=None, unit_cap_details=None):
    """根据结算方案计算服务费"""
    if isinstance(scheme, int):
        scheme = ServiceFeeSettlementScheme.objects.get(id=scheme)

    if not scheme or not scheme.is_active:
        return {
            'settlement_price': Decimal('0'),
            'final_fee': Decimal('0'),
            'fixed_part': Decimal('0'),
            'actual_part': Decimal('0'),
            'cap_fee': None,
            'calculation_details': {}
        }

    if scheme.has_cap_fee and scheme.cap_type == 'unit_cap' and not unit_cap_details:
        unit_cap_details = []
        for detail in scheme.unit_cap_details.all():
            unit_cap_details.append({
                'unit_name': detail.unit_name,
                'area': service_area if service_area else Decimal('0'),
                'cap_unit_price': detail.cap_unit_price
            })

    final_fee = scheme.calculate_settlement_fee(
        saving_amount=saving_amount,
        service_area=service_area,
        unit_cap_details=unit_cap_details
    )

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
        if scheme.combined_fixed_method == 'fixed_total':
            fixed_part = scheme.combined_fixed_total or Decimal('0')
        elif scheme.combined_fixed_method == 'fixed_unit':
            if service_area and scheme.combined_fixed_unit:
                fixed_part = Decimal(str(service_area)) * scheme.combined_fixed_unit
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

    return {
        'settlement_price': settlement_price,
        'final_fee': final_fee,
        'fixed_part': fixed_part,
        'actual_part': actual_part,
        'cap_fee': cap_fee,
        'calculation_details': {
            'scheme_id': scheme.id,
            'scheme_name': scheme.name,
            'settlement_method': scheme.get_settlement_method_display(),
            'saving_amount': saving_amount,
            'service_area': service_area,
        }
    }


def get_scheme_statistics(scheme_id=None, contract_id=None, project_id=None):
    """获取结算方案统计信息"""
    queryset = ServiceFeeSettlementScheme.objects.filter(is_active=True)
    if scheme_id:
        queryset = queryset.filter(id=scheme_id)
    if contract_id:
        queryset = queryset.filter(contract_id=contract_id)
    if project_id:
        queryset = queryset.filter(project_id=project_id)

    scheme_stats = queryset.aggregate(
        total_count=Count('id'),
        by_method=Count('id', distinct=True)
    )

    usage_stats = ProjectSettlement.objects.filter(
        service_fee_scheme__in=queryset
    ).aggregate(
        usage_count=Count('id'),
        total_settlement_amount=Sum('total_settlement_amount'),
        avg_settlement_amount=Avg('total_settlement_amount'),
        max_settlement_amount=Max('total_settlement_amount'),
        min_settlement_amount=Min('total_settlement_amount')
    )

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


def validate_scheme_configuration(scheme):
    """验证结算方案配置的完整性"""
    errors = []
    warnings = []

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
            for jp in scheme.jump_point_rates.filter(is_active=True).order_by('threshold'):
                if jp.rate < 0 or jp.rate > 100:
                    errors.append(f'跳点 {jp.threshold} 的取费系数必须在0-100之间')
    elif scheme.settlement_method == 'combined':
        if not scheme.combined_fixed_method:
            errors.append('组合方式必须选择固定部分方式')
        if not scheme.combined_actual_method:
            errors.append('组合方式必须选择按实结算部分方式')
        if scheme.combined_fixed_method == 'fixed_total' and not scheme.combined_fixed_total:
            errors.append('组合方式固定部分为固定总价时必须填写金额')
        elif scheme.combined_fixed_method == 'fixed_unit':
            if not scheme.combined_fixed_unit:
                errors.append('组合方式固定部分为固定单价时必须填写单价')
            if not scheme.combined_fixed_area_type:
                errors.append('组合方式固定部分为固定单价时必须选择面积类型')
        if scheme.combined_actual_method == 'cumulative_commission':
            if not scheme.combined_cumulative_rate:
                errors.append('组合方式按实结算部分为累计提成时必须填写系数')
        elif scheme.combined_actual_method == 'segmented_commission':
            if not scheme.segmented_rates.filter(is_active=True).exists():
                errors.append('组合方式按实结算部分为分段递增提成时必须至少配置一个分段')
        elif scheme.combined_actual_method == 'jump_point_commission':
            if not scheme.jump_point_rates.filter(is_active=True).exists():
                errors.append('组合方式按实结算部分为跳点提成时必须至少配置一个跳点')

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

    if scheme.has_minimum_fee:
        if not scheme.minimum_fee_amount:
            errors.append('设置保底费时必须填写保底费金额')
        elif scheme.minimum_fee_amount < 0:
            errors.append('保底费金额不能为负数')

    return {'is_valid': len(errors) == 0, 'errors': errors, 'warnings': warnings}


def duplicate_scheme(scheme, new_name=None, new_contract=None, new_project=None):
    """复制结算方案"""
    with transaction.atomic():
        new_scheme = ServiceFeeSettlementScheme.objects.create(
            name=new_name or f"{scheme.name} (副本)",
            code=None,
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
            is_default=False,
            sort_order=scheme.sort_order,
            created_by=scheme.created_by,
        )
        for rate in scheme.segmented_rates.all():
            ServiceFeeSegmentedRate.objects.create(
                scheme=new_scheme,
                threshold=rate.threshold,
                rate=rate.rate,
                description=rate.description,
                order=rate.order,
                is_active=rate.is_active,
            )
        for rate in scheme.jump_point_rates.all():
            ServiceFeeJumpPointRate.objects.create(
                scheme=new_scheme,
                threshold=rate.threshold,
                rate=rate.rate,
                description=rate.description,
                order=rate.order,
                is_active=rate.is_active,
            )
        for detail in scheme.unit_cap_details.all():
            ServiceFeeUnitCapDetail.objects.create(
                scheme=new_scheme,
                unit_name=detail.unit_name,
                cap_unit_price=detail.cap_unit_price,
                description=detail.description,
                order=detail.order,
            )
        return new_scheme
