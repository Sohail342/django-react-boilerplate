from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.http import HttpRequest
from django.shortcuts import redirect
from django.views.decorators.http import require_GET, require_http_methods, require_POST
from inertia import render

from apps.admin_panel.api.request_utils import get_request_data, parse_int, parse_str
from apps.budget.domain import policies
from apps.budget.dto.requests import DecisionInputDTO, RequestFormInputDTO
from apps.budget.services import pages as page_services
from apps.budget.services import requests as request_services


def _form_input(request: HttpRequest) -> RequestFormInputDTO:
    data = get_request_data(request)
    amount = data.get("amount")
    if isinstance(amount, bool) or amount is None:
        amount_text = ""
    elif isinstance(amount, str):
        amount_text = amount
    else:
        amount_text = str(amount)
    return RequestFormInputDTO(
        title=parse_str(data.get("title")),
        amount=amount_text,
        justification=parse_str(data.get("justification")),
    )


def _decision_input(request: HttpRequest) -> DecisionInputDTO:
    data = get_request_data(request)
    return DecisionInputDTO(
        status=parse_str(data.get("status")),
        reviewer_feedback=parse_str(data.get("reviewer_feedback")),
    )


def _page(request: HttpRequest, name: str = "page") -> int:
    return parse_int(request.GET.get(name), 1)


def _decide_redirect(actor) -> str:
    if policies.is_admin(actor):
        return "budget_admin"
    return "budget_reviews"


@require_GET
@login_required
def my_requests(request: HttpRequest):
    return render(
        request,
        "Budget/MyRequests",
        page_services.get_my_requests_page(actor=request.user, page=_page(request)),
    )


@require_http_methods(["GET", "POST"])
@login_required
def request_create(request: HttpRequest):
    if request.method == "GET":
        return render(
            request,
            "Budget/Form",
            page_services.get_create_page(actor=request.user),
        )

    result = request_services.create_request(
        actor=request.user, data=_form_input(request)
    )
    if not result.success:
        return render(request, "Budget/Form", result.page_props)
    messages.success(request, result.message)
    return redirect("budget_requests")


@require_http_methods(["GET", "POST"])
@login_required
def request_edit(request: HttpRequest, request_id):
    if request.method == "GET":
        return render(
            request,
            "Budget/Form",
            page_services.get_edit_page(actor=request.user, request_id=request_id),
        )

    result = request_services.update_request(
        actor=request.user, request_id=request_id, data=_form_input(request)
    )
    if not result.success:
        return render(request, "Budget/Form", result.page_props)
    messages.success(request, result.message)
    return redirect("budget_requests")


@require_POST
@login_required
def request_withdraw(request: HttpRequest, request_id):
    result = request_services.withdraw_request(
        actor=request.user, request_id=request_id
    )
    messages.success(request, result.message)
    return redirect("budget_requests")


@require_GET
@login_required
def reviews(request: HttpRequest):
    return render(
        request,
        "Budget/Reviews",
        page_services.get_reviews_page(
            actor=request.user,
            page=_page(request),
            history_page=_page(request, "history_page"),
        ),
    )


@require_POST
@login_required
def request_decide(request: HttpRequest, request_id):
    result = request_services.decide_request(
        actor=request.user, request_id=request_id, data=_decision_input(request)
    )
    add_message = messages.success if result.success else messages.error
    add_message(request, result.message)
    return redirect(_decide_redirect(request.user))


@require_GET
@login_required
def admin_summary(request: HttpRequest):
    return render(
        request,
        "Budget/Admin",
        page_services.get_admin_page(
            actor=request.user,
            page=_page(request),
            activity_page=_page(request, "activity_page"),
        ),
    )


@require_POST
@login_required
def request_delete(request: HttpRequest, request_id):
    result = request_services.delete_request(actor=request.user, request_id=request_id)
    messages.success(request, result.message)
    return redirect("budget_admin")
