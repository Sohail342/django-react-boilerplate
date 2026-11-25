from django.urls import path

from apps.budget.api.views import (
    admin_summary,
    my_requests,
    request_create,
    request_decide,
    request_delete,
    request_edit,
    request_withdraw,
    reviews,
)

urlpatterns = [
    path("requests/", my_requests, name="budget_requests"),
    path("requests/new/", request_create, name="budget_request_create"),
    path("requests/<uuid:request_id>/edit/", request_edit, name="budget_request_edit"),
    path(
        "requests/<uuid:request_id>/withdraw/",
        request_withdraw,
        name="budget_request_withdraw",
    ),
    path("reviews/", reviews, name="budget_reviews"),
    path(
        "reviews/<uuid:request_id>/decide/",
        request_decide,
        name="budget_request_decide",
    ),
    path("budget/", admin_summary, name="budget_admin"),
    path(
        "budget/<uuid:request_id>/delete/",
        request_delete,
        name="budget_request_delete",
    ),
]
