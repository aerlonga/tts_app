from fastapi import APIRouter

from app.schemas.health import HealthResponse
from app.schemas.operations import (
    CostControlStatus,
    ExternalServiceStatus,
    HealthDetailsResponse,
    StorageStatusItem,
)
from app.services.operations_service import operations_service


router = APIRouter(tags=["health"])


@router.get("/health", response_model=HealthResponse)
def health_check() -> HealthResponse:
    return HealthResponse(status="ok")


@router.get("/health/details", response_model=HealthDetailsResponse)
def health_details() -> HealthDetailsResponse:
    result = operations_service.get_health_details()
    return HealthDetailsResponse(
        status=result["status"],
        python_version=result["python_version"],
        database_url=result["database_url"],
        database_reachable=result["database_reachable"],
        ffmpeg_available=result["ffmpeg_available"],
        storage=[StorageStatusItem(**item) for item in result["storage"]],
        external_services=[ExternalServiceStatus(**item) for item in result["external_services"]],
        cost_control=CostControlStatus(**result["cost_control"]),
    )
