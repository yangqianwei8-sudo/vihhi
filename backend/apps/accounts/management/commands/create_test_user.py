from django.core.management.base import BaseCommand
from django.contrib.auth import get_user_model
from backend.apps.accounts.models import UserProfile
from backend.apps.org.models import Company, Department


class Command(BaseCommand):
    help = "Create a normal (non-superuser) test user and bind UserProfile."

    def add_arguments(self, parser):
        parser.add_argument("--username", default="tester1")
        parser.add_argument("--password", default="123456")
        parser.add_argument("--email", default="tester1@vihgroup.com.cn")

    def handle(self, *args, **options):
        username = options["username"]
        password = options["password"]
        email = options["email"]

        User = get_user_model()

        user, created = User.objects.get_or_create(
            username=username,
            defaults={
                "email": email,
                "is_staff": True,        # 允许进 admin（可选）
                "is_superuser": False,   # 关键：不是超管
                "is_active": True,
            },
        )

        if created:
            user.set_password(password)
            user.save(update_fields=["password"])
        else:
            # 确保它不是超管
            changed = False
            if user.is_superuser:
                user.is_superuser = False
                changed = True
            if not user.is_staff:
                user.is_staff = True
                changed = True
            if changed:
                user.save(update_fields=["is_superuser", "is_staff"])

        company = Company.objects.get(code="VIHHI")
        hq = Department.objects.get(company=company, name="总部", parent=None)

        profile, _ = UserProfile.objects.get_or_create(user=user)
        profile.company = company
        profile.department = hq
        profile.is_enabled = True
        profile.save(update_fields=["company", "department", "is_enabled", "updated_at"])

        self.stdout.write(self.style.SUCCESS(
            f"OK user={username} created={created} is_superuser={user.is_superuser} is_staff={user.is_staff}"
        ))

