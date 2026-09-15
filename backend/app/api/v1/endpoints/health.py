from fastapi import APIRouter
from app.schemas.health import HealthResponse
from app.core.config import settings
from app.db.session import check_db_health

router = APIRouter()


@router.get(
    "/health",
    response_model=HealthResponse,
    summary="Service Health Check",
    description="Returns current operational status of the SIH1518 backend service and database connectivity.",
)
async def health_check() -> HealthResponse:
    """Returns standard service health response with database connectivity."""
    db_health = check_db_health()

    return HealthResponse(
        status="ok",
        service="SIH1518 backend",
        version=settings.APP_VERSION,
        database=db_health,
    )
