"""Declarative base and shared column definitions for the ORM models."""

from datetime import datetime

from sqlalchemy import DateTime, Numeric, func
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column

from app.constants import MONEY_MAX_DIGITS, MONEY_PRECISION

# Declared once so every monetary column in the schema has identical precision.
MONEY_TYPE = Numeric(MONEY_MAX_DIGITS, MONEY_PRECISION)


class Base(DeclarativeBase):
    """Declarative base shared by every ORM model."""


class CreatedAtMixin:
    """Adds a database-generated creation timestamp.

    The default is produced by the database rather than by Python so that the
    value is correct regardless of which process inserted the row.
    """

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        nullable=False,
    )
