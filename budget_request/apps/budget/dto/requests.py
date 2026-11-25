from dataclasses import dataclass, field
from typing import Any


@dataclass(frozen=True)
class RequestFormInputDTO:
    title: str
    amount: str
    justification: str


@dataclass(frozen=True)
class DecisionInputDTO:
    status: str
    reviewer_feedback: str


@dataclass(frozen=True)
class MutationResultDTO:
    success: bool
    message: str
    request_id: str | None = None
    errors: dict[str, list[str]] = field(default_factory=dict)
    page_props: dict[str, Any] | None = None
