from fastapi import APIRouter

from app.core.config import get_settings
from app.core.constants import HEALTH_STATUS_HEALTHY

settings = get_settings()

router = APIRouter(
    prefix="/health",
    tags=["Health"],
)


@router.get("/")
def health_check() -> dict[str, str]:
    """
    Returns the current health status of the AeroLink backend.
    """

    return {
        "status": HEALTH_STATUS_HEALTHY,
        "service": settings.APP_NAME,
        "version": settings.APP_VERSION,
        "environment": settings.ENVIRONMENT,
    }
