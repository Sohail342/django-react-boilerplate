from django.contrib import admin
from django.contrib.auth.admin import UserAdmin
from .models import User


@admin.register(User)
class UserAdmin(UserAdmin):
    list_display = ("username", "email", "role", "is_staff")
    list_filter = ("role", "is_staff", "is_active")

    # Add the role field to the user edit page
    fieldsets = UserAdmin.fieldsets + (("Role Information", {"fields": ("role",)}),)

    # Add the role field to the user creation page
    add_fieldsets = UserAdmin.add_fieldsets + (
        ("Role Information", {"fields": ("role",)}),
    )
