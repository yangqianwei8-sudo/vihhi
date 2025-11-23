from django.core.management.base import BaseCommand
from django.utils import timezone
from django.contrib.auth import get_user_model
from django.db import transaction

from backend.apps.project_center.models import Project, ServiceType


class Command(BaseCommand):
    help = "Seed ~20 demo projects with various statuses for UI testing."

    def add_arguments(self, parser):
        parser.add_argument(
            "--count",
            type=int,
            default=20,
            help="How many demo projects to create (default: 20)",
        )

    def handle(self, *args, **options):
        count = max(1, int(options["count"]))
        now = timezone.now()

        # Prepare service types (ensure at least a few exist)
        service_type_names = ["结果优化", "过程优化", "精细化审图", "全过程咨询"]
        service_types = []
        for idx, name in enumerate(service_type_names, start=1):
            st, _ = ServiceType.objects.get_or_create(
                name=name, defaults={"code": f"st_{idx}", "order": idx}
            )
            service_types.append(st)
        if not service_types:
            self.stderr.write(self.style.ERROR("No ServiceType available, aborting."))
            return

        # Find a default user if the model has FK fields we can populate
        User = get_user_model()
        default_user = User.objects.filter(is_superuser=True).first() or User.objects.first()

        # Helper to generate next project number (VIH-YYYY-NNN)
        def next_number(seq):
            year = now.year
            return f"VIH-{year}-{seq:03d}"

        # The statuses we want to rotate across
        desired_statuses = ["draft", "in_progress", "completed", "archived"]
        created = 0

        with transaction.atomic():
            base_seq = (
                Project.objects.filter(project_number__startswith=f"VIH-{now.year}-")
                .count()
                + 1
            )
            for i in range(count):
                status = desired_statuses[i % len(desired_statuses)]
                seq = base_seq + i
                pn = next_number(seq)

                # Avoid accidental duplicates
                if Project.objects.filter(project_number=pn).exists():
                    continue

                st = service_types[i % len(service_types)]
                proj = Project(
                    project_number=pn,
                    name=f"演示项目 {seq}",
                    status=status,
                    client_company_name=f"测试客户{(i % 5) + 1}有限公司",
                    service_type=st,
                )

                # Optional fields if exist on model
                if hasattr(proj, "design_company"):
                    proj.design_company = f"设计单位{(i % 4) + 1}"
                if hasattr(proj, "created_by") and default_user:
                    proj.created_by = default_user
                if hasattr(proj, "business_manager") and default_user:
                    proj.business_manager = default_user
                if hasattr(proj, "project_manager") and default_user:
                    proj.project_manager = default_user

                proj.save()
                created += 1

        self.stdout.write(
            self.style.SUCCESS(f"Seeded {created} demo projects for testing.")
        )


