"""Unit tests for the application-wide error handlers.

These are exercised directly rather than through a route, because the failures
they cover (an unexpected crash, a non-standard status code) cannot be produced
by any legitimate request.
"""

import asyncio
import json
from typing import Any

from starlette.exceptions import HTTPException as StarletteHTTPException

from app.main import handle_http_error, handle_unexpected_error


def run_handler(handler: Any, exception: Exception) -> dict[str, Any]:
    """Invoke an async exception handler and return the decoded JSON body."""
    response = asyncio.run(handler(None, exception))
    return {"status": response.status_code, "body": json.loads(response.body)}


def test_unexpected_errors_never_leak_internal_details() -> None:
    """A crash must not tell the caller about the database, paths or stack (NFR-12)."""
    result = run_handler(handle_unexpected_error, RuntimeError("connection string leaked"))

    assert result["status"] == 500
    assert result["body"] == {"detail": "Internal server error", "code": "INTERNAL_ERROR"}
    assert "connection string" not in json.dumps(result["body"])


def test_a_non_standard_status_code_still_produces_an_error_code() -> None:
    result = run_handler(handle_http_error, StarletteHTTPException(status_code=599, detail="odd"))

    assert result["status"] == 599
    assert result["body"] == {"detail": "odd", "code": "HTTP_ERROR"}


def test_a_standard_status_code_is_named_after_its_meaning() -> None:
    result = run_handler(handle_http_error, StarletteHTTPException(status_code=404, detail="gone"))

    assert result["body"]["code"] == "NOT_FOUND"
