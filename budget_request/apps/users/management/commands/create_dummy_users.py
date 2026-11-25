from django.contrib.auth import get_user_model
from django.core.management.base import BaseCommand

User = get_user_model()

PASSWORD = "1234"

DUMMY_USERS = (
    {
        "username": "client",
        "role": User.Roles.CLIENT,
        "first_name": "Dummy",
        "last_name": "Client",
        "is_staff": False,
        "is_superuser": False,
    },
    {
        "username": "manager",
        "role": User.Roles.MANAGER,
        "first_name": "Dummy",
        "last_name": "Manager",
        "is_staff": False,
        "is_superuser": False,
    },
    {
        "username": "admin",
        "role": User.Roles.ADMIN,
        "first_name": "Dummy",
        "last_name": "Admin",
        "is_staff": True,
        "is_superuser": True,
    },
)


class Command(BaseCommand):
    help = "Create dummy client, manager, and admin users."

    def handle(self, *args, **options):
        for spec in DUMMY_USERS:
            username = spec["username"]
            user, created = User.objects.get_or_create(
                username=username,
                defaults={"email": f"{username}@example.com"},
            )
            user.role = spec["role"]
            user.first_name = spec["first_name"]
            user.last_name = spec["last_name"]
            user.is_staff = spec["is_staff"]
            user.is_superuser = spec["is_superuser"]
            user.is_active = True
            if not user.email:
                user.email = f"{username}@example.com"
            user.set_password(PASSWORD)
            user.save()
            verb = (
                f"Created for {user.username}"
                if created
                else f"Updated {user.username}"
            )
            self.stdout.write(self.style.SUCCESS(f"{verb} {username} ({user.role})"))

        self.stdout.write(f"Password for all three accounts: {PASSWORD}")
