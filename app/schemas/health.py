"""Response contract for the health endpoint."""

from typing import Literal

from pydantic import BaseModel, Field


class HealthRead(BaseModel):
    """Service liveness and identity information."""

    status: Literal["ok"] = Field(description="Always 'ok' when the service is responding.")
    service: str = Field(description="Machine-readable service name.", examples=["fairshare-api"])
    version: str = Field(description="Deployed application version.", examples=["1.0.0"])
