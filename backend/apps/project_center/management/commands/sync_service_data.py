from django.core.management.base import BaseCommand

from backend.apps.project_center.models import ServiceType, ServiceProfession

SERVICE_DEFINITIONS = [
    (
        'result_optimization',
        '结果优化',
        [
            '结构', '构造', '地库减面积', '地库加车位', '停车效率', '节能',
            '门窗栏杆', '幕墙', '总坪景观', '电气', '给排水', '暖通', '市政道路'
        ],
    ),
    (
        'process_optimization',
        '过程优化',
        [
            '结构', '停车效率'
        ],
    ),
    (
        'detailed_review',
        '精细化审图',
        [
            '建筑', '结构', '电气', '给排水', '暖通'
        ],
    ),
    (
        'full_process_consulting',
        '全过程咨询',
        [
            '建筑', '结构', '电气', '给排水', '暖通'
        ],
    ),
    (
        'cost_consulting',
        '造价咨询',
        [
            '建筑', '结构', '电气', '给排水', '暖通'
        ],
    ),
]

PROFESSION_CODE_MAP = {
    '建筑': 'architecture',
    '结构': 'structure',
    '构造': 'construction',
    '地库减面积': 'basement_reduce_area',
    '地库加车位': 'basement_add_parking',
    '停车效率': 'parking_efficiency',
    '节能': 'energy_saving',
    '门窗栏杆': 'doors_windows_railings',
    '幕墙': 'curtain_wall',
    '总坪景观': 'landscape',
    '电气': 'electrical',
    '给排水': 'water_supply_drainage',
    '暖通': 'hvac',
    '市政道路': 'municipal_road',
}


class Command(BaseCommand):
    """同步服务类型与服务专业定义"""

    help = 'Synchronise service type / profession definitions with the database.'

    def handle(self, *args, **options):
        created_types = 0
        updated_types = 0
        created_professions = 0
        updated_professions = 0
        removed_professions = 0

        for order, (code, name, profession_names) in enumerate(SERVICE_DEFINITIONS, start=1):
            service_type, created = ServiceType.objects.update_or_create(
                code=code,
                defaults={'name': name, 'order': order},
            )
            if created:
                created_types += 1
            else:
                updated_types += 1

            keep_ids = []
            for prof_order, prof_name in enumerate(profession_names, start=1):
                prof_code = PROFESSION_CODE_MAP.get(prof_name, f'auto_{prof_order}')
                profession, prof_created = ServiceProfession.objects.update_or_create(
                    service_type=service_type,
                    code=prof_code,
                    defaults={'name': prof_name, 'order': prof_order},
                )
                keep_ids.append(profession.id)
                if prof_created:
                    created_professions += 1
                else:
                    updated_professions += 1

            removed = ServiceProfession.objects.filter(service_type=service_type).exclude(id__in=keep_ids)
            removed_count = removed.count()
            if removed_count:
                removed_professions += removed_count
                removed.delete()

        self.stdout.write(self.style.SUCCESS(
            f"服务类型新增 {created_types} 个，更新 {updated_types} 个；服务专业新增 {created_professions} 个，更新 {updated_professions} 个，移除 {removed_professions} 个。"
        ))
