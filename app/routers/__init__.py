"""FastAPI routers (presentation layer).

Shared plumbing lives here: the request-scoped database session used by every
router, and the helper that documents the error envelope in the OpenAPI schema.
"""

from http import HTTPStatus
from typing import Annotated, Any

from fastapi import Depends
from sqlalchemy.orm import Session

from app.database import get_db
from app.schemas.common import ErrorResponse

DbSession = Annotated[Session, Depends(get_db)]


def error_responses(*statuses: int) -> dict[int | str, dict[str, Any]]:
    """Declare the documented error responses for a route (GUIDE A-5)."""
    return {
        status: {"model": ErrorResponse, "description": HTTPStatus(status).phrase}
        for status in statuses
    }
