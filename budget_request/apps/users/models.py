from django.contrib.auth.models import AbstractUser
from django.db import models


class User(AbstractUser):
    """
    Custom user model that extends the default Django AbstractUser.
    """

    class Roles(models.TextChoices):
        ADMIN = "admin", "Admin"
        CLIENT = "client", "Client"
        MANAGER = "manager", "Manager"

    role = models.CharField(
        max_length=20,
        choices=Roles.choices,
        default=Roles.CLIENT,
        db_index=True,
        help_text="Role of the user in the system.",
    )

    @property
    def is_admin(self):
        """
        Check if the user has an admin role.
        """
        return self.role == self.Roles.ADMIN

    @property
    def is_manager(self):
        """
        Check if the user has a manager role.
        """
        return self.role == self.Roles.MANAGER

    @property
    def is_client(self):
        """
        Check if the user has a client role.
        """
        return self.role == self.Roles.CLIENT
