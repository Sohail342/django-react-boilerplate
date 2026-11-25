from django.db.models import QuerySet

from apps.budget.domain import policies
from apps.budget.models import BudgetRequest


def visible_requests(user) -> QuerySet[BudgetRequest]:
    queryset = BudgetRequest.objects.select_related("requester", "reviewer")
    if policies.is_admin(user) or policies.is_manager(user):
        return queryset
    if policies.is_client(user):
        return queryset.filter(requester=user)
    return queryset.none()
