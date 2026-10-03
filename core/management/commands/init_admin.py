from django.contrib.auth import get_user_model
from django.core.management.base import BaseCommand
from config.settings import ADMIN_USERNAME, ADMIN_PASSWORD, ADMIN_EMAIL


class Command(BaseCommand):
    help = "Create the default admin user if it does not exist"

    def handle(self, *args, **options):
        User = get_user_model()

        username = ADMIN_USERNAME
        email = ADMIN_EMAIL
        password = ADMIN_PASSWORD

        user, created = User.objects.get_or_create(
            username=username,
            defaults={
                "email": email,
                "is_staff": True,
                "is_superuser": True,
            },
        )

        if created:
            user.set_password(password)
            user.save()

            self.stdout.write(self.style.SUCCESS(f"Superuser '{username}' created."))
        else:
            self.stdout.write(self.style.WARNING(f"Superuser '{username}' already exists."))
