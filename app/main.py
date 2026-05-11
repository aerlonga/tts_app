from fastapi import FastAPI

from app.core.config import get_settings
from app.repositories.db import initialize_database
from app.routers.analytics import router as analytics_router
from app.routers.ai import router as ai_router
from app.routers.usage import router as usage_router
from app.routers.broll import router as broll_router
from app.routers.health import router as health_router
from app.routers.ideas import router as ideas_router
from app.routers.media import router as media_router
from app.routers.youtube import router as youtube_router
from app.services.video_service import video_service
from app.storage.local_storage import ensure_storage_layout


settings = get_settings()

app = FastAPI(
    title=settings.fastapi_app_name,
    version="0.1.0",
    description=(
        "FastAPI foundation for the local video automation backend. "
        "This app coexists with the legacy Flask server during migration."
    ),
)

app.include_router(health_router)
app.include_router(ai_router)
app.include_router(media_router)
app.include_router(broll_router)
app.include_router(ideas_router)
app.include_router(youtube_router)
app.include_router(analytics_router)
app.include_router(usage_router)


@app.on_event("startup")
def startup() -> None:
    ensure_storage_layout()
    initialize_database()
    video_service.start_cleanup_worker()
