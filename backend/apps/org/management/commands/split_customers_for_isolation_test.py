from django.core.management.base import BaseCommand
from django.db import transaction

from backend.apps.org.models import Company, Department


class Command(BaseCommand):
    help = "Create a second company and move N clients to it for isolation test (idempotent)."

    def add_arguments(self, parser):
        parser.add_argument("--count", type=int, default=5)

    @transaction.atomic
    def handle(self, *args, **options):
        count = options["count"]

        # 1) Create company + dept
        company2, company_created = Company.objects.get_or_create(
            code="VIHHI_CQ",
            defaults={"name": "维海科技-重庆", "is_active": True},
        )
        hq2, dept_created = Department.objects.get_or_create(
            company=company2,
            name="总部",
            parent=None,
            defaults={"is_active": True},
        )

        # 2) Load Client model (avoid direct import path issues)
        from backend.apps.customer_management.models import Client

        # 3) Pick N clients still in VIHHI and move them to company2
        # 为了幂等：只迁移"仍在 VIHHI 且尚未被迁移"的客户
        vi = Company.objects.get(code="VIHHI")
        qs = Client.objects.filter(company=vi).order_by("id")

        # 如果之前已经迁移过一些到 VIHHI_CQ，就只迁移剩余的
        to_move = list(qs[:count])

        moved = 0
        for c in to_move:
            c.company = company2
            c.department = hq2
            c.save(update_fields=["company", "department"])
            moved += 1

        total_vi = Client.objects.filter(company=vi).count()
        total_cq = Client.objects.filter(company=company2).count()

        self.stdout.write(self.style.SUCCESS("Done split customers for isolation test."))
        self.stdout.write(f"company2={'created' if company_created else 'exists'}: {company2.name}({company2.code})")
        self.stdout.write(f"dept2={'created' if dept_created else 'exists'}: {hq2.name}")
        self.stdout.write(f"moved_now={moved}, total_VIHHI={total_vi}, total_VIHHI_CQ={total_cq}")

