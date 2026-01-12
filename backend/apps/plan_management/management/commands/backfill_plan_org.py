from django.core.management.base import BaseCommand
from django.contrib.auth import get_user_model
from django.db import transaction

from backend.apps.org.models import Company, Department
from backend.apps.plan_management.models import Plan, StrategicGoal


User = get_user_model()


class Command(BaseCommand):
    help = "Backfill company/org_department for Plan and StrategicGoal."

    def add_arguments(self, parser):
        parser.add_argument("--company-code", default="VIHHI", help="Default company code")
        parser.add_argument("--department-name", default="总部", help="Default department name")
        parser.add_argument("--dry-run", action="store_true", help="Dry run without saving")

    @transaction.atomic
    def handle(self, *args, **options):
        company_code = options["company_code"]
        department_name = options["department_name"]
        dry_run = options["dry_run"]

        company, _ = Company.objects.get_or_create(
            code=company_code, defaults={"name": "维海科技", "is_active": True}
        )
        department, _ = Department.objects.get_or_create(
            company=company, name=department_name, defaults={"is_active": True}
        )

        def pick_org_from_user(user):
            """
            Prefer user.profile.company/department if exists.
            Fallback to default company/department.
            """
            try:
                profile = getattr(user, "profile", None)
                if profile and profile.company_id:
                    c = profile.company
                    d = profile.department if getattr(profile, "department_id", None) else None
                    return c, (d or department)
            except Exception:
                pass
            return company, department

        # ---------- Backfill StrategicGoal ----------
        goals = StrategicGoal.objects.all()
        updated_goals = 0
        for g in goals.iterator():
            if g.company_id and g.org_department_id:
                continue

            c, d = None, None
            # try owner/responsible/created_by fields (use whichever your model has)
            for attr in ("created_by", "creator", "owner", "responsible_person", "responsible_user"):
                u = getattr(g, attr, None)
                if u:
                    c, d = pick_org_from_user(u)
                    break

            if not c:
                c, d = company, department

            if not g.company_id:
                g.company = c
            if not g.org_department_id:
                g.org_department = d

            updated_goals += 1
            if not dry_run:
                g.save(update_fields=["company", "org_department"])

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

            # if still empty, try related_goal
            if not c and getattr(p, "related_goal_id", None):
                try:
                    rg = p.related_goal
                    if rg and rg.company_id:
                        c = rg.company
                        d = rg.org_department if rg.org_department_id else department
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
                f"Done backfill. company={company.code} dept={department.name} "
                f"updated_goals={updated_goals} updated_plans={updated_plans} dry_run={dry_run}"
            )
        )

