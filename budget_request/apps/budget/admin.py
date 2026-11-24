from django.contrib import admin

from .models import AuditLog, BudgetRequest


@admin.register(BudgetRequest)
class BudgetRequestAdmin(admin.ModelAdmin):
    list_display = (
        "title",
        "status",
        "requester",
        "reviewer",
        "created_at",
        "updated_at",
        "reviewed_at",
    )
    list_filter = ("status", "requester", "created_at")
    readonly_fields = ("id", "created_at", "updated_at")


@admin.register(AuditLog)
class AuditLogAdmin(admin.ModelAdmin):
    list_display = ("action", "entity_type", "entity_id", "actor", "created_at")
    list_filter = ("actor", "entity_type", "created_at")
    readonly_fields = ("id", "created_at")
