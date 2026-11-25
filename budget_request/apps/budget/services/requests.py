from decimal import Decimal, InvalidOperation

from django.db import transaction
from django.http import Http404
from django.utils import timezone

from apps.budget.domain import policies
from apps.budget.dto.requests import (
    DecisionInputDTO,
    MutationResultDTO,
    RequestFormInputDTO,
)
from apps.budget.models import AuditLog, BudgetRequest
from apps.budget.services.audit import (
    _created_snapshot,
    _edited_snapshot,
    _full_snapshot,
    _record,
)
from apps.budget.services.formatting import AMOUNT_STEP, DEFAULT_CURRENCY
from apps.budget.services.pages import _form_from_input, _form_page, _header
from apps.common import ensure_allowed

MAX_AMOUNT = Decimal("999999999999.99")

PENDING = BudgetRequest.Status.PENDING
APPROVED = BudgetRequest.Status.APPROVED
REJECTED = BudgetRequest.Status.REJECTED


def create_request(*, actor, data: RequestFormInputDTO) -> MutationResultDTO:
    ensure_allowed(policies.can_create(actor))
    errors, amount = _form_errors(data)
    if errors:
        return _form_failure(data, errors)

    with transaction.atomic():
        budget_request = BudgetRequest.objects.create(
            title=data.title.strip(),
            amount=amount,
            currency=DEFAULT_CURRENCY,
            justification=data.justification.strip(),
            status=PENDING,
            requester=actor,
        )
        _record(
            actor,
            AuditLog.Action.CREATED,
            budget_request,
            old_values=None,
            new_values=_created_snapshot(budget_request),
        )
    return MutationResultDTO(
        success=True,
        message=f'Budget request "{budget_request.title}" was submitted.',
        request_id=str(budget_request.pk),
    )


def update_request(
    *, actor, request_id, data: RequestFormInputDTO
) -> MutationResultDTO:
    errors, amount = _form_errors(data)
    with transaction.atomic():
        budget_request = _locked_visible_or_404(actor, request_id)
        ensure_allowed(policies.can_update(actor, budget_request))
        header = _header(budget_request)
        if errors:
            return _form_failure(data, errors, header=header)

        old_values = _edited_snapshot(budget_request)
        budget_request.title = data.title.strip()
        budget_request.amount = amount
        budget_request.justification = data.justification.strip()
        budget_request.save(
            update_fields=["title", "amount", "justification", "updated_at"]
        )
        _record(
            actor,
            AuditLog.Action.UPDATED,
            budget_request,
            old_values=old_values,
            new_values=_edited_snapshot(budget_request),
        )

    return MutationResultDTO(
        success=True,
        message=f'Budget request "{budget_request.title}" was updated.',
        request_id=str(budget_request.pk),
    )


def withdraw_request(*, actor, request_id) -> MutationResultDTO:
    with transaction.atomic():
        budget_request = _locked_visible_or_404(actor, request_id)
        ensure_allowed(policies.can_withdraw(actor, budget_request))
        title = budget_request.title
        _record(
            actor,
            AuditLog.Action.WITHDRAWN,
            budget_request,
            old_values=_full_snapshot(budget_request),
            new_values=None,
        )
        budget_request.delete()
    return MutationResultDTO(
        success=True, message=f'Budget request "{title}" was withdrawn.'
    )


def decide_request(*, actor, request_id, data: DecisionInputDTO) -> MutationResultDTO:
    with transaction.atomic():
        budget_request = _locked_visible_or_404(actor, request_id)
        ensure_allowed(policies.can_decide(actor, budget_request))
        errors = _decision_errors(data)
        if errors:
            return MutationResultDTO(
                success=False,
                message=errors["reviewer_feedback"][0]
                if "reviewer_feedback" in errors
                else errors["status"][0],
                errors=errors,
            )

        budget_request.status = data.status
        budget_request.reviewer = actor
        budget_request.reviewer_feedback = data.reviewer_feedback.strip()
        budget_request.reviewed_at = timezone.now()
        budget_request.save(
            update_fields=[
                "status",
                "reviewer",
                "reviewer_feedback",
                "reviewed_at",
                "updated_at",
            ]
        )
        action = (
            AuditLog.Action.APPROVED
            if budget_request.status == APPROVED
            else AuditLog.Action.REJECTED
        )
        _record(
            actor,
            action,
            budget_request,
            old_values={"status": PENDING},
            new_values={
                "status": budget_request.status,
                "reviewer_id": budget_request.reviewer_id,
                "reviewer_feedback": budget_request.reviewer_feedback,
                "reviewed_at": budget_request.reviewed_at.isoformat(),
            },
        )

    verb = "approved" if data.status == APPROVED else "rejected"
    return MutationResultDTO(
        success=True,
        message=f'Budget request "{budget_request.title}" was {verb}.',
        request_id=str(budget_request.pk),
    )


def delete_request(*, actor, request_id) -> MutationResultDTO:
    ensure_allowed(policies.can_delete(actor))
    with transaction.atomic():
        budget_request = _locked_visible_or_404(actor, request_id)
        title = budget_request.title
        _record(
            actor,
            AuditLog.Action.DELETED,
            budget_request,
            old_values=_full_snapshot(budget_request),
            new_values=None,
        )
        budget_request.delete()
    return MutationResultDTO(
        success=True, message=f'Budget request "{title}" was deleted.'
    )


def _locked_visible_or_404(actor, request_id) -> BudgetRequest:
    budget_request = (
        BudgetRequest.objects.select_for_update()
        .select_related("requester", "reviewer")
        .filter(pk=request_id)
        .first()
    )
    if budget_request is None or not policies.can_view(actor, budget_request):
        raise Http404("Budget request not found.")
    return budget_request


def _form_errors(
    data: RequestFormInputDTO,
) -> tuple[dict[str, list[str]], Decimal | None]:
    errors: dict[str, list[str]] = {}
    title = data.title.strip()
    justification = data.justification.strip()
    if not title:
        errors["title"] = ["This field is required."]
    elif len(title) > 255:
        errors["title"] = ["Title must be 255 characters or fewer."]
    if not justification:
        errors["justification"] = ["This field is required."]

    amount, amount_error = _parse_amount(data.amount)
    if amount_error:
        errors["amount"] = [amount_error]
    return errors, amount


def _parse_amount(value: str) -> tuple[Decimal | None, str | None]:
    raw = (value or "").strip().replace(",", "")
    if not raw:
        return None, "This field is required."
    try:
        amount = Decimal(raw)
    except (InvalidOperation, ValueError):
        return None, "Enter a valid amount."
    if amount != amount.quantize(AMOUNT_STEP):
        return None, "Use at most two decimal places."
    if amount <= 0:
        return None, "Amount must be greater than zero."
    if amount > MAX_AMOUNT:
        return None, "Amount is too large."
    return amount, None


def _decision_errors(data: DecisionInputDTO) -> dict[str, list[str]]:
    if data.status not in {APPROVED, REJECTED}:
        return {"status": ["Choose approve or reject."]}
    if data.status == REJECTED and not data.reviewer_feedback.strip():
        return {"reviewer_feedback": ["A note is required when rejecting a request."]}
    return {}


def _form_failure(
    data: RequestFormInputDTO,
    errors: dict[str, list[str]],
    *,
    header: dict | None = None,
) -> MutationResultDTO:
    return MutationResultDTO(
        success=False,
        message="",
        errors=errors,
        page_props=_form_page(
            form=_form_from_input(data), errors=errors, header=header
        ),
    )
