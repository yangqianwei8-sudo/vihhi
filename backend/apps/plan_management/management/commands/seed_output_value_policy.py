# -*- coding: utf-8 -*-
"""
产值口径默认配置：创建一条 enabled=True 的 OutputValuePolicy（幂等）。
权重 2%/2%/10%/5%/6%/2%，event_modifier [0.2, 1.2]，confidence_high_threshold 0.30，stage_weight 1.0。
部署后执行一次即可；也可在 Admin 中修改。
"""
from decimal import Decimal

from django.core.management.base import BaseCommand

from backend.apps.output_value_management.models import OutputValuePolicy


DEFAULT_SERVICE_TYPE_WEIGHTS = {
    '转化阶段': '0.02', '合同阶段': '0.02', '生产阶段': '0.10',
    '结算阶段': '0.05', '回款阶段': '0.06', '售后阶段': '0.02',
    'conversion': '0.02', 'contract': '0.02', 'production': '0.10',
    'settlement': '0.05', 'payment': '0.06', 'after_sales': '0.02',
}


class Command(BaseCommand):
    help = '创建/更新默认产值口径配置（幂等），保证存在一条 enabled=True 的 policy'

    def handle(self, *args, **options):
        policy = OutputValuePolicy.objects.filter(enabled=True).first()
        if policy:
            self.stdout.write(self.style.SUCCESS(f'已有生效口径：{policy.name} (id={policy.id})'))
            return

        # 若存在未启用的，启用第一条并更新为默认值
        any_policy = OutputValuePolicy.objects.first()
        if any_policy:
            any_policy.name = 'V1 默认口径'
            any_policy.service_type_weights = DEFAULT_SERVICE_TYPE_WEIGHTS
            any_policy.stage_weight = Decimal('1.0')
            any_policy.event_modifier_min = Decimal('0.2')
            any_policy.event_modifier_max = Decimal('1.2')
            any_policy.confidence_high_threshold = Decimal('0.30')
            any_policy.enabled = True
            any_policy.save()
            self.stdout.write(self.style.SUCCESS(f'已启用并更新为默认口径：id={any_policy.id}'))
            return

        OutputValuePolicy.objects.create(
            name='V1 默认口径',
            service_type_weights=DEFAULT_SERVICE_TYPE_WEIGHTS,
            stage_weight=Decimal('1.0'),
            event_modifier_min=Decimal('0.2'),
            event_modifier_max=Decimal('1.2'),
            confidence_high_threshold=Decimal('0.30'),
            enabled=True,
        )
        self.stdout.write(self.style.SUCCESS('已创建默认产值口径配置（enabled=True）'))
