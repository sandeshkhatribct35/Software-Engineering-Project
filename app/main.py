"""FastAPI application: metadata, error handling and router registration.

This module is the only place that knows about HTTP status codes for domain
errors. Routers raise exceptions from ``app.errors``; the handlers below turn
them into the single documented error envelope (GUIDE FR-33).
"""

import logging
from collections.abc import AsyncGenerator
from contextlib import asynccontextmanager
from http import HTTPStatus

from fastapi import FastAPI, Request
from fastapi.encoders import jsonable_encoder
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse
from starlette.exceptions import HTTPException as StarletteHTTPException

from app.config import get_settings
from app.constants import SERVICE_NAME, SERVICE_VERSION
from app.database import init_db
from app.errors import FairShareError
from app.routers import health

logger = logging.getLogger(SERVICE_NAME)

TAGS_METADATA = [
    {"name": "health", "description": "Service liveness and identity."},
    {"name": "groups", "description": "Create and manage expense-sharing groups."},
    {"name": "members", "description": "Manage the people who belong to a group."},
    {"name": "expenses", "description": "Record shared expenses and how they are split."},
    {"name": "balances", "description": "Net balances, settlement plans and group summaries."},
    {"name": "settlements", "description": "Record payments that clear debts between members."},
]

DESCRIPTION = """
FairShare records shared group expenses and works out who owes whom.

* Expenses are split **equally** or by **exact amounts**, never losing or
  inventing money — shares always sum to the expense total.
* Every member has a **net balance**; the balances of a group always sum to zero.
* The **settlement plan** endpoint returns the smallest practical set of
  payments that clears every debt in the group.

All monetary values are exchanged as strings with two decimal places so that no
precision is lost in JSON.
"""


@asynccontextmanager
async def lifespan(_: FastAPI) -> AsyncGenerator[None, None]:
    """Create the database schema before the application starts serving."""
    logging.basicConfig(level=get_settings().log_level)
    init_db()
    yield


app = FastAPI(
    title="FairShare API",
    description=DESCRIPTION,
    version=SERVICE_VERSION,
    openapi_tags=TAGS_METADATA,
    contact={"name": "Sandesh Khatri", "url": "https://github.com/sandeshkhatribct35"},
    lifespan=lifespan,
)


@app.exception_handler(FairShareError)
async def handle_domain_error(_: Request, exc: FairShareError) -> JSONResponse:
    """Render any domain exception as the documented error envelope."""
    return JSONResponse(
        status_code=exc.status_code,
        content={"detail": exc.detail, "code": exc.code},
    )


@app.exception_handler(StarletteHTTPException)
async def handle_http_error(_: Request, exc: StarletteHTTPException) -> JSONResponse:
    """Give framework-raised errors (404, 405, ...) the same envelope."""
    try:
        code = HTTPStatus(exc.status_code).name
    except ValueError:
        code = "HTTP_ERROR"
    return JSONResponse(status_code=exc.status_code, content={"detail": exc.detail, "code": code})


@app.exception_handler(RequestValidationError)
async def handle_validation_error(_: Request, exc: RequestValidationError) -> JSONResponse:
    """Return schema validation failures with a stable machine-readable code."""
    return JSONResponse(
        status_code=HTTPStatus.UNPROCESSABLE_ENTITY,
        content={"detail": jsonable_encoder(exc.errors()), "code": "VALIDATION_ERROR"},
    )


@app.exception_handler(Exception)
async def handle_unexpected_error(_: Request, exc: Exception) -> JSONResponse:
    """Log the fault and return a generic message, never internal details."""
    logger.exception("Unhandled error", exc_info=exc)
    return JSONResponse(
        status_code=HTTPStatus.INTERNAL_SERVER_ERROR,
        content={"detail": "Internal server error", "code": "INTERNAL_ERROR"},
    )


app.include_router(health.router)
