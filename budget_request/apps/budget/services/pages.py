from decimal import Decimal
from typing import Any

from django.db.models import Sum
from django.http import Http404

from apps.budget.domain import policies
from apps.budget.models import BudgetRequest
from apps.budget.selectors.requests import visible_requests
from apps.budget.services.audit import activity_page as list_activity
from apps.budget.services.formatting import DEFAULT_CURRENCY, _money, _person
from apps.common import ensure_allowed, paginate

PAGE_SIZE = 25

PENDING = BudgetRequest.Status.PENDING
APPROVED = BudgetRequest.Status.APPROVED


def get_my_requests_page(*, actor, page: int) -> dict:
    ensure_allowed(policies.can_list_own(actor))
    queryset = visible_requests(actor).order_by("-created_at")
    page_obj, pagination = paginate(queryset, page=page, page_size=PAGE_SIZE)
    return {
        "requests": [_serialize(item, actor) for item in page_obj],
        "pagination": pagination,
        "can": {"create": policies.can_create(actor)},
    }


def get_create_page(*, actor) -> dict:
    ensure_allowed(policies.can_create(actor))
    return _form_page(form=_empty_form(), errors={})


def get_edit_page(*, actor, request_id) -> dict:
    budget_request = _visible_or_404(actor, request_id)
    ensure_allowed(policies.can_update(actor, budget_request))
    return _form_page(
        form=_form_from_request(budget_request),
        errors={},
        header=_header(budget_request),
    )


def get_reviews_page(*, actor, page: int, history_page: int) -> dict:
    ensure_allowed(policies.can_review(actor))
    queryset = visible_requests(actor)
    pending_page, pending_pagination = paginate(
        queryset.filter(status=PENDING).order_by("created_at"),
        page=page,
        page_size=PAGE_SIZE,
    )
    history_obj, history_pagination = paginate(
        queryset.exclude(status=PENDING).order_by("-reviewed_at", "-created_at"),
        page=history_page,
        page_size=PAGE_SIZE,
    )
    return {
        "pending": [_serialize(item, actor) for item in pending_page],
        "pending_pagination": pending_pagination,
        "history": [_serialize(item, actor) for item in history_obj],
        "history_pagination": history_pagination,
    }


def get_admin_page(*, actor, page: int, activity_page: int) -> dict:
    ensure_allowed(policies.can_view_admin(actor))
    queryset = visible_requests(actor).order_by("-created_at")
    page_obj, pagination = paginate(queryset, page=page, page_size=PAGE_SIZE)
    activity: list[dict] = []
    activity_pagination = None
    if policies.can_read_audit(actor):
        activity, activity_pagination = list_activity(
            page=activity_page, page_size=PAGE_SIZE
        )
    return {
        "totals": _totals(),
        "requests": [_serialize(item, actor) for item in page_obj],
        "pagination": pagination,
        "activity": activity,
        "activity_pagination": activity_pagination,
    }


def _form_page(*, form: dict, errors: dict, header: dict | None = None) -> dict:
    props: dict[str, Any] = {"form": form, "errors": errors}
    if header is not None:
        props["request"] = header
    return props


def _empty_form() -> dict:
    return {"title": "", "amount": "", "justification": ""}


def _form_from_input(data) -> dict:
    return {
        "title": data.title,
        "amount": data.amount,
        "justification": data.justification,
    }


def _form_from_request(budget_request: BudgetRequest) -> dict:
    return {
        "title": budget_request.title,
        "amount": _money(budget_request.amount),
        "justification": budget_request.justification,
    }


def _header(budget_request: BudgetRequest) -> dict:
    return {"id": str(budget_request.pk), "title": budget_request.title}


def _visible_or_404(actor, request_id) -> BudgetRequest:
    budget_request = visible_requests(actor).filter(pk=request_id).first()
    if budget_request is None:
        raise Http404("Budget request not found.")
    return budget_request


def _serialize(budget_request: BudgetRequest, actor) -> dict:
    return {
        "id": str(budget_request.pk),
        "title": budget_request.title,
        "amount": _money(budget_request.amount),
        "currency": budget_request.currency,
        "justification": budget_request.justification,
        "status": budget_request.status,
        "requester": _person(budget_request.requester),
        "reviewer": _person(budget_request.reviewer),
        "reviewer_feedback": budget_request.reviewer_feedback,
        "created_at": budget_request.created_at.isoformat(),
        "updated_at": budget_request.updated_at.isoformat(),
        "reviewed_at": (
            budget_request.reviewed_at.isoformat()
            if budget_request.reviewed_at
            else None
        ),
        "can_update": policies.can_update(actor, budget_request),
        "can_withdraw": policies.can_withdraw(actor, budget_request),
        "can_decide": policies.can_decide(actor, budget_request),
        "can_delete": policies.can_delete(actor),
    }


def _totals() -> dict[str, str]:
    pending = _sum_status(PENDING)
    approved = _sum_status(APPROVED)
    return {
        "pending": _money(pending),
        "approved": _money(approved),
        "currency": DEFAULT_CURRENCY,
    }


def _sum_status(status: str) -> Decimal:
    total = BudgetRequest.objects.filter(status=status).aggregate(total=Sum("amount"))[
        "total"
    ]
    return total or Decimal("0")
