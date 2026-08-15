"""Health endpoint used by humans, Docker healthchecks and CI smoke tests."""

from fastapi import APIRouter

from app.constants import SERVICE_NAME, SERVICE_VERSION
from app.schemas.health import HealthRead

router = APIRouter(tags=["health"])


@router.get(
    "/",
    response_model=HealthRead,
    summary="Service health check",
    description=(
        "Reports that the API process is running and returns its identity and "
        "version. Used by the container healthcheck and by the CI smoke test."
    ),
)
def read_health() -> HealthRead:
    """Return service liveness information."""
    return HealthRead(status="ok", service=SERVICE_NAME, version=SERVICE_VERSION)
