"""Reusable field types shared by the request and response models.

Declaring these once keeps validation rules and the JSON representation of money
consistent across every endpoint, instead of repeating constraints in each
schema (GUIDE C-7).
"""

from decimal import Decimal
from typing import Annotated

from pydantic import AfterValidator, BaseModel, Field, PlainSerializer

from app.constants import (
    CURRENCY_CODE_LENGTH,
    EXPENSE_DESCRIPTION_MAX_LENGTH,
    GROUP_DESCRIPTION_MAX_LENGTH,
    GROUP_NAME_MAX_LENGTH,
    MAX_EXPENSE_AMOUNT,
    MEMBER_NAME_MAX_LENGTH,
    MONEY_MAX_DIGITS,
    MONEY_PRECISION,
    SETTLEMENT_NOTE_MAX_LENGTH,
)


class ErrorResponse(BaseModel):
    """The single shape every failing request returns (GUIDE FR-33)."""

    detail: str | list[dict] = Field(
        description="Human-readable explanation, or the list of schema violations.",
        examples=["Group 7 does not exist"],
    )
    code: str = Field(
        description="Stable machine-readable error code.",
        examples=["GROUP_NOT_FOUND"],
    )


def _format_money(value: Decimal) -> str:
    """Render a monetary amount with exactly two decimals (GUIDE FR-35)."""
    return f"{value:.{MONEY_PRECISION}f}"


def _require_non_blank(value: str) -> str:
    """Reject values that are empty once surrounding whitespace is removed."""
    stripped = value.strip()
    if not stripped:
        raise ValueError("must not be empty or contain only whitespace")
    return stripped


# Money leaves the API as a JSON string so that no precision is lost in transit.
MoneyOut = Annotated[
    Decimal,
    PlainSerializer(_format_money, return_type=str, when_used="json"),
]

ExpenseAmount = Annotated[
    Decimal,
    Field(
        gt=0,
        le=MAX_EXPENSE_AMOUNT,
        max_digits=MONEY_MAX_DIGITS,
        decimal_places=MONEY_PRECISION,
        description="Total amount of the expense, greater than zero, at most two decimals.",
        examples=["1000.00"],
    ),
]

ShareAmount = Annotated[
    Decimal,
    Field(
        ge=0,
        le=MAX_EXPENSE_AMOUNT,
        max_digits=MONEY_MAX_DIGITS,
        decimal_places=MONEY_PRECISION,
        description="Portion of the expense owed by one member; may be zero.",
        examples=["333.33"],
    ),
]

SettlementAmount = Annotated[
    Decimal,
    Field(
        gt=0,
        le=MAX_EXPENSE_AMOUNT,
        max_digits=MONEY_MAX_DIGITS,
        decimal_places=MONEY_PRECISION,
        description="Amount actually paid from one member to another.",
        examples=["333.33"],
    ),
]

GroupName = Annotated[
    str,
    Field(
        min_length=1,
        max_length=GROUP_NAME_MAX_LENGTH,
        description="Display name of the group.",
        examples=["Pokhara Trip"],
    ),
    AfterValidator(_require_non_blank),
]

GroupDescription = Annotated[
    str | None,
    Field(
        max_length=GROUP_DESCRIPTION_MAX_LENGTH,
        description="Optional free-text note describing the group.",
    ),
]

CurrencyCode = Annotated[
    str,
    Field(
        pattern=r"^[A-Z]{3}$",
        min_length=CURRENCY_CODE_LENGTH,
        max_length=CURRENCY_CODE_LENGTH,
        description="Three-letter uppercase currency code, recorded for display only.",
        examples=["NPR"],
    ),
]

MemberName = Annotated[
    str,
    Field(
        min_length=1,
        max_length=MEMBER_NAME_MAX_LENGTH,
        description="Name of the person, unique within the group.",
        examples=["Sandesh"],
    ),
    AfterValidator(_require_non_blank),
]

ExpenseDescription = Annotated[
    str,
    Field(
        min_length=1,
        max_length=EXPENSE_DESCRIPTION_MAX_LENGTH,
        description="What the money was spent on.",
        examples=["Hotel in Pokhara"],
    ),
    AfterValidator(_require_non_blank),
]

SettlementNote = Annotated[
    str | None,
    Field(
        max_length=SETTLEMENT_NOTE_MAX_LENGTH,
        description="Optional note describing how the payment was made.",
        examples=["Paid by eSewa"],
    ),
]
