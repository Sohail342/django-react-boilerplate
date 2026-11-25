from django.contrib.auth.models import AbstractBaseUser, AnonymousUser

from apps.admin_panel.services.navigation import get_admin_navigation
from apps.budget.domain import policies


def get_budget_navigation(*, actor: AbstractBaseUser | AnonymousUser) -> list[dict]:
    """Budget sidebar entries for the actor's business role."""
    if policies.is_admin(actor):
        return [
            {
                "section": "Budget",
                "label": "Summary",
                "icon": "summary",
                "route": "budget_admin",
            }
        ]
    if policies.is_manager(actor):
        return [
            {
                "section": "Budget",
                "label": "Reviews",
                "icon": "reviews",
                "route": "budget_reviews",
            }
        ]
    if policies.is_client(actor):
        return [
            {
                "section": "Budget",
                "label": "My requests",
                "icon": "requests",
                "route": "budget_requests",
            },
            {
                "section": "Budget",
                "label": "New request",
                "icon": "plus",
                "route": "budget_request_create",
            },
        ]
    return []


def get_navigation(*, actor: AbstractBaseUser | AnonymousUser) -> list[dict]:
    """Staff console links, then the budget links for this role."""
    return get_admin_navigation(actor=actor) + get_budget_navigation(actor=actor)
