from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.http import HttpRequest
from django.shortcuts import redirect
from django.urls import reverse
from django.views.decorators.http import require_http_methods, require_POST
from inertia import render

from apps.admin_panel.api.request_utils import client_ip, get_request_data, parse_str
from apps.admin_panel.dto.auth import LoginInputDTO
from apps.admin_panel.services.auth import get_login_page, login_user, logout_user
from apps.budget.domain.policies import role_home_url


def legacy_login_redirect(request: HttpRequest):
    """Old sign-in URL. Keeps the query string so `next` still works."""
    target = reverse("login")
    query = request.META.get("QUERY_STRING", "")
    if query:
        target = f"{target}?{query}"
    return redirect(target)


@require_http_methods(["GET", "POST"])
def login_view(request: HttpRequest):
    if getattr(request.user, "is_authenticated", False):
        return redirect(role_home_url(request.user))

    if request.method == "GET":
        next_url = request.GET.get("next", "")
        return render(request, "Auth/Login", get_login_page(next_url=next_url))

    data = get_request_data(request)
    dto = LoginInputDTO(
        username=parse_str(data.get("username")),
        password=parse_str(data.get("password")),
        next_url=parse_str(data.get("next")) or request.GET.get("next", ""),
        client_ip=client_ip(request),
    )
    result = login_user(request, dto)
    if result.success:
        return redirect(result.redirect_url)
    return render(request, "Auth/Login", result.page_props)


@require_POST
@login_required
def logout_view(request: HttpRequest):
    logout_user(request)
    messages.info(request, "You have been signed out.")
    return redirect("login")
