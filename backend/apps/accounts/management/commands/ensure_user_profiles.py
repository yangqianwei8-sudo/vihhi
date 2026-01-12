from django.core.management.base import BaseCommand
from django.contrib.auth import get_user_model
from backend.apps.accounts.models import UserProfile


class Command(BaseCommand):
    help = "Ensure every user has a UserProfile (idempotent)."

    def handle(self, *args, **options):
        User = get_user_model()

        total = User.objects.count()
        created = 0

        for user in User.objects.all().iterator():
            _, is_created = UserProfile.objects.get_or_create(
                user=user,
                defaults={"is_enabled": True}
            )
            if is_created:
                created += 1

        self.stdout.write(self.style.SUCCESS(
            f"Done. users={total}, created_profiles={created}, existing_profiles={total - created}"
        ))

