"""Health check for the application."""

import pydantic
from fastapi import APIRouter

from phiphi import config

router = APIRouter()


class HealthCheck(pydantic.BaseModel):
    """HealthCheck."""

    title: str
    version: str


@router.get("/", response_model=HealthCheck, tags=["status"])
@router.get("/health", response_model=HealthCheck, tags=["status"])
async def health_check() -> HealthCheck:
    """HealthCheck."""
    return HealthCheck(
        title=config.settings.TITLE,
        version=config.settings.VERSION,
    )


@router.get("/errors/internal", tags=["status"])
async def errors_internal() -> None:
    """Raise an internal server error."""
    _ = 1 / 0  # noqa: F841


@router.get("/errors/500", tags=["status"])
async def errors_500() -> None:
    """Raise a 500 error."""
    raise Exception("This is a test exception")
