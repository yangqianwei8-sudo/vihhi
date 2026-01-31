from django.core.management.base import BaseCommand
from django.contrib.auth import get_user_model
from django.db import transaction

from backend.apps.system_management.models import OurCompany, Department
from backend.apps.plan_management.models import Plan


User = get_user_model()


class Command(BaseCommand):
    help = "Backfill company/org_department for Plan（使用 system_management.OurCompany 与 Department）"

    def add_arguments(self, parser):
        parser.add_argument("--company-name", default="维海科技", help="Default company name")
        parser.add_argument("--department-code", default="HQ", help="Default department code")
        parser.add_argument("--dry-run", action="store_true", help="Dry run without saving")

    @transaction.atomic
    def handle(self, *args, **options):
        company_name = options["company_name"]
        department_code = options["department_code"]
        dry_run = options["dry_run"]

        company, _ = OurCompany.objects.get_or_create(
            company_name=company_name, defaults={"is_active": True}
        )
        department, _ = Department.objects.get_or_create(
            code=department_code, defaults={"name": company_name + "总部", "is_active": True}
        )

        def pick_org_from_user(user):
            """
            优先使用 user.department；若无则使用默认 department。
            公司使用默认 OurCompany（system_management 无 user.company 概念）。
            """
            try:
                user_dept = getattr(user, "department", None)
                if user_dept:
                    return company, user_dept
            except Exception:
                pass
            return company, department

        # ---------- Backfill Plan ----------
        plans = Plan.objects.all()
        updated_plans = 0
        for p in plans.iterator():
            if p.company_id and p.org_department_id:
                continue

            c, d = None, None
            # prefer responsible_person, then created_by/creator
            for attr in ("responsible_person", "created_by", "creator", "owner"):
                u = getattr(p, attr, None)
                if u:
                    c, d = pick_org_from_user(u)
                    break

            # if still empty, try related_goal（仅当 StrategicGoal 有 company 时）
            if not c and getattr(p, "related_goal_id", None):
                try:
                    rg = p.related_goal
                    if rg and hasattr(rg, "company_id") and rg.company_id:
                        c = rg.company
                        d = rg.org_department if (hasattr(rg, "org_department_id") and rg.org_department_id) else department
                except Exception:
                    pass

            if not c:
                c, d = company, department

            if not p.company_id:
                p.company = c
            if not p.org_department_id:
                p.org_department = d

            updated_plans += 1
            if not dry_run:
                p.save(update_fields=["company", "org_department"])

        self.stdout.write(
            self.style.SUCCESS(
                f"Done backfill. company={company.company_name} dept={department.name} "
                f"updated_plans={updated_plans} dry_run={dry_run}"
            )
        )

