"""Project-wide constants.

Every limit, default and magic value used by more than one module lives here so
that the rest of the codebase contains no unexplained literals (GUIDE C-6).
The length limits mirror the column definitions in ``app.models``.
"""

from decimal import Decimal
from enum import StrEnum
from typing import Final


class SplitType(StrEnum):
    """How the cost of an expense is divided between its participants."""

    EQUAL = "EQUAL"
    EXACT = "EXACT"


# Service identity, surfaced by the health endpoint and the OpenAPI document.
SERVICE_NAME: Final[str] = "fairshare-api"
SERVICE_VERSION: Final[str] = "1.0.0"
API_PREFIX: Final[str] = "/api/v1"

# Money. Amounts are fixed-point decimals everywhere; floats are never used.
MONEY_PRECISION: Final[int] = 2
MONEY_MAX_DIGITS: Final[int] = 12
MONEY_QUANTUM: Final[Decimal] = Decimal("0.01")
ZERO_MONEY: Final[Decimal] = Decimal("0.00")
MAX_EXPENSE_AMOUNT: Final[Decimal] = Decimal("1000000.00")

# Field limits, mirrored by the database schema.
GROUP_NAME_MAX_LENGTH: Final[int] = 100
GROUP_DESCRIPTION_MAX_LENGTH: Final[int] = 500
MEMBER_NAME_MAX_LENGTH: Final[int] = 80
EXPENSE_DESCRIPTION_MAX_LENGTH: Final[int] = 200
SETTLEMENT_NOTE_MAX_LENGTH: Final[int] = 200

# Currency is recorded per group for display only; no conversion is performed.
CURRENCY_CODE_LENGTH: Final[int] = 3
DEFAULT_CURRENCY: Final[str] = "NPR"

# Pagination bounds for expense listings.
DEFAULT_PAGE_SIZE: Final[int] = 50
MAX_PAGE_SIZE: Final[int] = 100
