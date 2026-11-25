from django.http import HttpRequest
from django.urls import reverse
from inertia import render

from apps.budget.domain.policies import role_home


def permission_denied(request: HttpRequest, exception: Exception):
    """Inertia page for PermissionDenied, including direct URL visits."""
    user = getattr(request, "user", None)
    if user is not None and getattr(user, "is_authenticated", False):
        home_link = role_home(user)
        home_url_name = home_link["route"]
        home_label = home_link["label"]
    else:
        home_url_name = "login"
        home_label = "Sign in"

    message = str(exception).strip() or "You do not have access to this page."
    response = render(
        request,
        "Errors/Forbidden",
        {
            "message": message,
            "home_url": reverse(home_url_name),
            "home_label": home_label,
        },
    )
    response.status_code = 403
    return response
