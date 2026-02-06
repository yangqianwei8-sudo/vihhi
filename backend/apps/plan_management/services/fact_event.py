# -*- coding: utf-8 -*-
"""
FactEvent 唯一写入口。禁止业务/测试直接 FactEvent.objects.create，必须经本入口写入。
强制 source_app，并校验 type 在白名单。
"""
from django.utils import timezone

# 事件类型白名单（至少包含 CONSULT_OPINION_SUBMITTED）
FACT_EVENT_TYPE_WHITELIST = frozenset([
    'CONSULT_OPINION_SUBMITTED',
    'PREPARATION_WORK_DONE',
])


def record_fact_event(
    type: str,
    ref_model: str = '',
    ref_id: str = '',
    source_app: str = '',
    payload: dict = None,
    occurred_at=None,
    idempotency_key: str = None,
):
    """
    唯一入口：写入 FactEvent。强制 source_app，type 必须在白名单。
    Returns: FactEvent 实例
    """
    if type not in FACT_EVENT_TYPE_WHITELIST:
        raise ValueError('FactEvent type 必须在白名单内，当前白名单: %s' % sorted(FACT_EVENT_TYPE_WHITELIST))
    if not source_app or not source_app.strip():
        raise ValueError('FactEvent 必须提供 source_app')
    from backend.apps.plan_management.models import FactEvent, allow_fact_event_write, reset_fact_event_write
    if payload is None:
        payload = {}
    if occurred_at is None:
        occurred_at = timezone.now()
    key = (idempotency_key or '').strip() or None
    if key and FactEvent.objects.filter(idempotency_key=key).exists():
        return FactEvent.objects.get(idempotency_key=key)
    token = allow_fact_event_write()
    try:
        return FactEvent.objects.create(
            type=type,
            ref_model=ref_model or '',
            ref_id=ref_id or '',
            source_app=source_app.strip(),
            payload=payload,
            occurred_at=occurred_at,
            idempotency_key=key,
        )
    finally:
        reset_fact_event_write(token)
