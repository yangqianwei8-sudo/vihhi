from django.core.management.base import BaseCommand
from backend.apps.org.models import Company, Department
from backend.apps.accounts.models import UserProfile


class Command(BaseCommand):
    help = "Fill default company/department for UserProfile if missing (idempotent)."

    def handle(self, *args, **options):
        company = Company.objects.get(code="VIHHI")
        hq = Department.objects.get(company=company, name="总部", parent=None)

        qs = UserProfile.objects.select_related("user").all()
        total = qs.count()
        updated = 0

        for p in qs.iterator():
            changed = False
            if p.company_id is None:
                p.company = company
                changed = True
            if p.department_id is None:
                p.department = hq
                changed = True
            if changed:
                p.save(update_fields=["company", "department", "updated_at"])
                updated += 1

        self.stdout.write(self.style.SUCCESS(
            f"Done. profiles={total}, updated={updated}, unchanged={total - updated}"
        ))

