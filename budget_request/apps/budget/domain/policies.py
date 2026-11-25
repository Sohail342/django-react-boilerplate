"""Role rules for budget requests. The user.role field is the source of truth."""

from django.contrib.auth.models import AbstractBaseUser, AnonymousUser
from django.urls import reverse

from apps.budget.models import BudgetRequest
from apps.users.models import User

UserLike = AbstractBaseUser | AnonymousUser


def _role(user: UserLike) -> str:
    return getattr(user, "role", "") or ""


def is_active_user(user: UserLike) -> bool:
    return bool(
        getattr(user, "is_authenticated", False) and getattr(user, "is_active", False)
    )


def is_client(user: UserLike) -> bool:
    return is_active_user(user) and _role(user) == User.Roles.CLIENT


def is_manager(user: UserLike) -> bool:
    return is_active_user(user) and _role(user) == User.Roles.MANAGER


def is_admin(user: UserLike) -> bool:
    return is_active_user(user) and _role(user) == User.Roles.ADMIN


def role_home(user: UserLike) -> dict[str, str]:
    """Sidebar home for the signed-in role. Unknown roles use the client home."""
    if is_admin(user):
        return {"label": "Summary", "route": "budget_admin"}
    if is_manager(user):
        return {"label": "Reviews", "route": "budget_reviews"}
    return {"label": "My requests", "route": "budget_requests"}


def role_home_url(user: UserLike) -> str:
    return reverse(role_home(user)["route"])


def can_list_own(user: UserLike) -> bool:
    return is_client(user)


def can_create(user: UserLike) -> bool:
    return is_client(user)


def can_review(user: UserLike) -> bool:
    return is_manager(user) or is_admin(user)


def can_view_admin(user: UserLike) -> bool:
    return is_admin(user)


def can_read_audit(user: UserLike) -> bool:
    return is_admin(user)


def can_view(user: UserLike, budget_request: BudgetRequest) -> bool:
    if is_admin(user) or is_manager(user):
        return True
    if is_client(user):
        return budget_request.requester_id == user.pk
    return False


def can_update(user: UserLike, budget_request: BudgetRequest) -> bool:
    return (
        is_client(user)
        and budget_request.requester_id == user.pk
        and budget_request.status == BudgetRequest.Status.PENDING
    )


def can_withdraw(user: UserLike, budget_request: BudgetRequest) -> bool:
    return can_update(user, budget_request)


def can_decide(user: UserLike, budget_request: BudgetRequest) -> bool:
    return can_review(user) and budget_request.status == BudgetRequest.Status.PENDING


def can_delete(user: UserLike) -> bool:
    return is_admin(user)
