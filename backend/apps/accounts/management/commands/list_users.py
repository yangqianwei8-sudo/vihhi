from django.core.management.base import BaseCommand
from django.contrib.auth import get_user_model


class Command(BaseCommand):
    help = "List users (username/email/is_superuser/is_active)."

    def handle(self, *args, **options):
        User = get_user_model()
        qs = User.objects.all().order_by("id")
        self.stdout.write(f"total={qs.count()}")
        for u in qs:
            self.stdout.write(
                f"id={u.id} username={u.username} email={getattr(u,'email','')} "
                f"is_superuser={u.is_superuser} is_active={u.is_active}"
            )

