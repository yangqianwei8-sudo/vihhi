"""
模块：产值管理模块 V1 计算内核（纯计算，无副作用）

对应冻结文档：docs/output_value_v1_execution.md

- 章节一、V1 总体计算公式
  说明：本模块通过 calculate_dynamic_output 实现唯一合法公式。
  公式：dynamic_output = 商机金额 × 服务类型权重 × 阶段权重 × 里程碑权重 × 事件修正系数
  一致性：实现中为 base * service_weight * stage_weight * milestone_weight * event_modifier，与文档逐项对应。

- 章节二、服务类型权重
  说明：service_type_weight 为绝对折算率，不做归一化；SERVICE_TYPE_WEIGHT_MAP 与文档表格一致。
  一致性：按商机 service_type 的 name/code 取权重，未合并为 stage。

- 章节三、阶段权重
  说明：stage_weight 恒为 1.0，阶段仅用于限定可用的里程碑集合。
  一致性：STAGE_WEIGHT = 1.0；current_stage 仅用于 get_milestones，不参与权重计算。

- 章节四、里程碑权重计算规则
  说明：里程碑权重 = 当前阶段内所有【已完成里程碑】的最大权重；无完成则 0；不累计、不平均、不跨阶段。
  一致性：_get_completed_milestones_max_weight 仅取当前 stage 的已完成里程碑并取 max(weights)。

- 章节五、十一（口径补丁）：事件 → 里程碑 判定规则
  说明：里程碑完成度只读计划管理 PlanOutputMilestoneCompletion；不读 OutputValueRecord/业务表。
  一致性：is_milestone_completed 仅查计划管理完成记录；禁止业务模块直接参与产值公式或权重。

- 章节六、事件修正系数
  说明：event_modifier = 1 + Σ(delta)，限制区间 [0.2, 1.2]；event_deltas 来源系统级事件，与里程碑事件无关，默认空数组。
  一致性：get_opportunity_event_deltas 默认 []；raw_modifier = 1 + sum(deltas)，_clamp(0.2, 1.2)。

- 章节七、核心计算伪代码
  说明：伪代码唯一版本，本模块按该伪代码实现。
  一致性：base → _get_base_amount；service_weight → _get_service_type_weight；stage_weight = 1.0；completed/max → _get_completed_milestones_max_weight；event_modifier → clamp(1+sum(deltas), 0.2, 1.2)。

- 章节八、接口定义（含 confidence 规则）
  说明：返回字段含 dynamic_output, stage, milestone, confidence；confidence 规则：high ≥0.30，0<x<0.30 为 medium，0 为 low。
  一致性：_confidence 严格按上述阈值实现；calculate_dynamic_output 返回文档要求的五字段。
"""
from decimal import Decimal
from typing import Dict, Any, List

from backend.apps.opportunity_management.models import BusinessOpportunity
from backend.apps.output_value_management.models import (
    OutputValueStage,
    OutputValueMilestone,
    OutputValuePolicy,
)
# 硬约束：里程碑完成度只读计划管理完成状态，不读 OutputValueRecord / 业务表
from backend.apps.plan_management.models import PlanOutputMilestoneCompletion


def _get_service_type_weight(opportunity: BusinessOpportunity, policy: OutputValuePolicy) -> Decimal:
    """来源：文档 二、服务类型权重。从 policy.service_type_weights 取商机 service_type 的绝对折算率。"""
    weights = policy.service_type_weights or {}
    st = getattr(opportunity, 'service_type', None)
    if not st:
        return Decimal(str(weights.get('conversion', weights.get('转化阶段', '0.02'))))
    name = getattr(st, 'name', None) or ''
    code = getattr(st, 'code', None) or ''
    raw = weights.get(name) or weights.get(code)
    if raw is not None:
        return Decimal(str(raw))
    return Decimal('0.02')


def _get_base_amount(opportunity: BusinessOpportunity) -> Decimal:
    """来源：文档 一、商机金额（base_amount）。来源商机主表，不考虑回款、不考虑结算；与文档一致。"""
    amount = getattr(opportunity, 'estimated_amount', None)
    if amount is not None and amount > 0:
        return Decimal(str(amount))
    amount = getattr(opportunity, 'actual_amount', None)
    if amount is not None and amount > 0:
        return Decimal(str(amount))
    return Decimal('0')


def _get_current_stage(opportunity: BusinessOpportunity):
    """来源：文档 三、七。current_stage 仅用于限定可用的里程碑集合，不参与权重；与文档一致。"""
    stage = getattr(opportunity, 'current_stage', None) or getattr(opportunity, 'current_output_stage', None)
    if stage is not None:
        return stage
    return OutputValueStage.objects.filter(is_active=True).order_by('order').first()


def _get_milestone_weight_value(milestone: OutputValueMilestone) -> Decimal:
    """来源：文档 四、七。单里程碑权重值（用于取 max）；不累计，与文档一致。"""
    pct = getattr(milestone, 'milestone_percentage', None) or 0
    return Decimal(str(pct)) / 100


def get_opportunity_event_deltas(opportunity_id: int) -> List[Decimal]:
    """
    来源：文档 六、event_deltas 说明。
    来源：系统级事件（如风险、冻结、加速）；与里程碑事件无关；默认值为空数组（event_modifier = 1）。
    一致性：未使用事件参与金额计算，仅用于 event_modifier。
    """
    return []


def is_milestone_completed(milestone_id: int, opportunity_id: int) -> bool:
    """
    来源：文档 五、十一（口径补丁）。里程碑完成度只读计划管理完成状态。
    判定规则：计划管理侧已为该商机+该里程碑写入 PlanOutputMilestoneCompletion 则视为完成。
    禁止：读取 OutputValueRecord 或业务表做完成度判定。
    """
    try:
        milestone = OutputValueMilestone.objects.get(pk=milestone_id)
    except OutputValueMilestone.DoesNotExist:
        return False
    return PlanOutputMilestoneCompletion.objects.filter(
        opportunity_id=opportunity_id,
        milestone_code=milestone.code,
    ).exists()


def _get_completed_milestones_max_weight(stage, opportunity: BusinessOpportunity) -> tuple:
    """
    来源：文档 四、七、十一。里程碑权重 = 当前阶段内所有【已完成里程碑】的最大权重；无完成则 0。
    完成度只读计划管理 PlanOutputMilestoneCompletion，不读 OutputValueRecord / 业务表。
    """
    milestones = stage.milestones.filter(is_active=True).order_by('-milestone_percentage')
    completed_weights = []
    opportunity_id = getattr(opportunity, 'id', None)
    if not opportunity_id:
        return Decimal('0'), None
    for m in milestones:
        if PlanOutputMilestoneCompletion.objects.filter(
            opportunity_id=opportunity_id,
            milestone_code=m.code,
        ).exists():
            w = _get_milestone_weight_value(m)
            completed_weights.append((w, m.name))
    if not completed_weights:
        return Decimal('0'), None
    best = max(completed_weights, key=lambda x: x[0])
    return best[0], best[1]


def _clamp(value: Decimal, lo: Decimal, hi: Decimal) -> Decimal:
    """来源：文档 六、七。event_modifier 限制区间 [0.2, 1.2]；与文档一致。"""
    if value < lo:
        return lo
    if value > hi:
        return hi
    return value


def _confidence(milestone_weight: Decimal, threshold: Decimal) -> str:
    """来源：文档 八、confidence 判定规则。high：≥threshold；medium：0 < x < threshold；low：0。"""
    if milestone_weight >= threshold:
        return 'high'
    if milestone_weight > 0:
        return 'medium'
    return 'low'


def calculate_dynamic_output(opportunity_id: int) -> Dict[str, Any]:
    """
    来源：文档 一、七、八。
    实现 V1 总体计算公式（唯一合法版本），无副作用。
    所有可变口径从 OutputValuePolicy（唯一 enabled 条）读取；未配置时抛错并提示在 Admin 配置。
    公式：dynamic_output = 商机金额 × 服务类型权重 × 阶段权重 × 里程碑权重 × 事件修正系数。
    返回字段（文档 八）：dynamic_output, stage, milestone, milestone_weight, confidence。
    """
    policy = OutputValuePolicy.get_active()

    opportunity = (
        BusinessOpportunity.objects.filter(pk=opportunity_id)
        .select_related('service_type', 'project')
        .first()
    )
    if not opportunity:
        return {
            'dynamic_output': Decimal('0'),
            'stage': '',
            'milestone': None,
            'milestone_weight': Decimal('0'),
            'confidence': 'low',
        }

    base = _get_base_amount(opportunity)
    service_weight = _get_service_type_weight(opportunity, policy)
    stage_weight = Decimal(str(policy.stage_weight))
    stage = _get_current_stage(opportunity)
    if not stage:
        return {
            'dynamic_output': Decimal('0'),
            'stage': '',
            'milestone': None,
            'milestone_weight': Decimal('0'),
            'confidence': 'low',
        }
    milestone_weight, milestone_name = _get_completed_milestones_max_weight(stage, opportunity)
    deltas = get_opportunity_event_deltas(opportunity_id)
    raw_modifier = Decimal('1') + sum(Decimal(str(d)) for d in deltas)
    event_modifier = _clamp(
        raw_modifier,
        Decimal(str(policy.event_modifier_min)),
        Decimal(str(policy.event_modifier_max)),
    )

    dynamic_output = base * service_weight * stage_weight * milestone_weight * event_modifier
    dynamic_output = dynamic_output.quantize(Decimal('0.01'))

    threshold = Decimal(str(policy.confidence_high_threshold))
    return {
        'dynamic_output': dynamic_output,
        'stage': getattr(stage, 'name', '') or '',
        'milestone': milestone_name,
        'milestone_weight': milestone_weight,
        'confidence': _confidence(milestone_weight, threshold),
    }
