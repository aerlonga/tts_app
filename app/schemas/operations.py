from pydantic import BaseModel


class StorageStatusItem(BaseModel):
    path: str
    exists: bool
    is_dir: bool
    writable: bool


class ExternalServiceStatus(BaseModel):
    name: str
    configured: bool
    detail: str


class CostControlStatus(BaseModel):
    usage_routes_available: bool
    ai_usage_logging_ready: bool
    pricing_configured: bool
    top_risk: str


class HealthDetailsResponse(BaseModel):
    status: str
    python_version: str
    database_url: str
    database_reachable: bool
    ffmpeg_available: bool
    storage: list[StorageStatusItem]
    external_services: list[ExternalServiceStatus]
    cost_control: CostControlStatus
