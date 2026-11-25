from datetime import datetime

from django.contrib.auth import get_user_model
from django.utils import timezone

from apps.budget.models import AuditLog, BudgetRequest
from apps.budget.services.formatting import DEFAULT_CURRENCY, _money, _person
from apps.common import paginate

ENTITY_TYPE = "budget_request"

DETAIL_FIELDS = (
    ("title", "Title"),
    ("amount", "Amount"),
    ("currency", "Currency"),
    ("justification", "Justification"),
    ("status", "Status"),
    ("requester_id", "Requester"),
    ("reviewer_id", "Reviewer"),
    ("reviewer_feedback", "Reviewer note"),
    ("reviewed_at", "Reviewed"),
)
PERSON_FIELDS = {"requester_id", "reviewer_id"}


def activity_page(*, page: int, page_size: int) -> tuple[list[dict], dict]:
    logs = (
        AuditLog.objects.filter(entity_type=ENTITY_TYPE)
        .select_related("actor")
        .order_by("-created_at")
    )
    activity_obj, pagination = paginate(logs, page=page, page_size=page_size)
    return _activity_rows(activity_obj), pagination


def _record(
    actor, action: str, budget_request: BudgetRequest, *, old_values, new_values
):
    AuditLog.objects.create(
        actor=actor,
        action=action,
        entity_type=ENTITY_TYPE,
        entity_id=budget_request.pk,
        old_values=old_values,
        new_values=new_values,
    )


def _created_snapshot(budget_request: BudgetRequest) -> dict:
    return {
        "title": budget_request.title,
        "amount": _money(budget_request.amount),
        "currency": budget_request.currency,
        "justification": budget_request.justification,
        "status": budget_request.status,
        "requester_id": budget_request.requester_id,
    }


def _edited_snapshot(budget_request: BudgetRequest) -> dict:
    return {
        "title": budget_request.title,
        "amount": _money(budget_request.amount),
        "justification": budget_request.justification,
    }


def _full_snapshot(budget_request: BudgetRequest) -> dict:
    return {
        **_created_snapshot(budget_request),
        "reviewer_id": budget_request.reviewer_id,
        "reviewer_feedback": budget_request.reviewer_feedback,
        "reviewed_at": (
            budget_request.reviewed_at.isoformat()
            if budget_request.reviewed_at
            else None
        ),
    }


def _activity_rows(logs) -> list[dict]:
    user_ids = set()
    for log in logs:
        for values in (log.old_values, log.new_values):
            if not isinstance(values, dict):
                continue
            for key in PERSON_FIELDS:
                user_id = _coerce_user_id(values.get(key))
                if user_id is not None:
                    user_ids.add(user_id)
    names = {}
    if user_ids:
        User = get_user_model()
        names = {
            user.pk: _person(user) for user in User.objects.filter(pk__in=user_ids)
        }
    return [_activity_row(log, names) for log in logs]


def _activity_row(log: AuditLog, names: dict) -> dict:
    values = log.new_values or log.old_values or {}
    return {
        "id": str(log.pk),
        "action": log.action,
        "actor": _person(log.actor),
        "request_id": str(log.entity_id),
        "title": values.get("title", ""),
        "created_at": log.created_at.isoformat(),
        "changes": _changes(log.old_values, log.new_values, names),
    }


def _changes(old_values, new_values, names: dict) -> list[dict]:
    old_values = old_values or {}
    new_values = new_values or {}
    currency = (
        new_values.get("currency") or old_values.get("currency") or DEFAULT_CURRENCY
    )
    rows = []
    for key, label in DETAIL_FIELDS:
        if key not in old_values and key not in new_values:
            continue
        before = (
            _change_value(key, old_values.get(key), currency, names)
            if key in old_values
            else None
        )
        after = (
            _change_value(key, new_values.get(key), currency, names)
            if key in new_values
            else None
        )
        rows.append(
            {
                "label": label,
                "before": before,
                "after": after,
                "changed": before != after,
            }
        )
    return rows


def _change_value(key: str, value, currency: str, names: dict):
    if value is None or value == "":
        return None
    if key in PERSON_FIELDS:
        user_id = _coerce_user_id(value)
        person = names.get(user_id) if user_id is not None else None
        return person["name"] if person else str(value)
    if key == "amount":
        return f"{currency} {value}"
    if key == "status":
        return dict(BudgetRequest.Status.choices).get(value, str(value))
    if key == "reviewed_at":
        parsed = datetime.fromisoformat(value)
        if timezone.is_aware(parsed):
            parsed = timezone.localtime(parsed)
        return parsed.strftime("%b %d, %Y, %H:%M")
    return str(value)


def _coerce_user_id(value):
    if value is None or value == "":
        return None
    if isinstance(value, int):
        return value
    try:
        return int(value)
    except (TypeError, ValueError):
        return None
