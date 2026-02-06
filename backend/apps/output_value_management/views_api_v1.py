# 产值管理 V1 API 视图
# 权威依据：docs/output_value_v1_execution.md 章节八
from decimal import Decimal

from rest_framework import status
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response

from backend.apps.opportunity_management.models import BusinessOpportunity
from backend.apps.output_value_management.services.calculator_v1 import calculate_dynamic_output


def _serialize_decimal(value):
    """JSON 可序列化：Decimal -> float（保留 2 位）。"""
    if value is None:
        return None
    if isinstance(value, Decimal):
        return float(value.quantize(Decimal('0.01')))
    return value


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def opportunity_dynamic_output_v1(request, id):
    """
    查询当前动态产值（V1）
    依据：docs/output_value_v1_execution.md 八.1
    GET /api/output/v1/opportunity/{id}
    返回：dynamic_output, stage, milestone, milestone_weight, confidence
    """
    if not BusinessOpportunity.objects.filter(pk=id).exists():
        return Response(
            {'detail': '商机不存在'},
            status=status.HTTP_404_NOT_FOUND,
        )
    result = calculate_dynamic_output(id)
    payload = {
        'dynamic_output': _serialize_decimal(result['dynamic_output']),
        'stage': result['stage'] or '',
        'milestone': result['milestone'],
        'milestone_weight': _serialize_decimal(result['milestone_weight']),
        'confidence': result['confidence'],
    }
    return Response(payload, status=status.HTTP_200_OK)
