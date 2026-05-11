from __future__ import annotations

import platform
import shutil

from sqlalchemy import text

from app.core.config import Settings, get_settings
from app.repositories.ai_usage_repository import AIUsageRepository
from app.repositories.db import get_connection, initialize_database
from app.storage.local_storage import get_storage_report


class OperationsService:
    def __init__(
        self,
        usage_repository: AIUsageRepository | None = None,
        settings: Settings | None = None,
    ) -> None:
        self.settings = settings or get_settings()
        self.usage_repository = usage_repository or AIUsageRepository()

    def _database_reachable(self) -> bool:
        try:
            initialize_database(self.settings.database_url)
            with get_connection(self.settings.database_url) as connection:
                connection.execute(text("SELECT 1")).fetchone()
            return True
        except Exception:
            return False

    def _external_services(self) -> list[dict]:
        analytics_configured = all(
            [
                self.settings.youtube_client_id,
                self.settings.youtube_client_secret,
                self.settings.youtube_refresh_token,
            ]
        )
        return [
            {
                "name": "gemini",
                "configured": bool(self.settings.gemini_api_key),
                "detail": "GEMINI_API_KEY present" if self.settings.gemini_api_key else "GEMINI_API_KEY missing",
            },
            {
                "name": "archive_org_broll",
                "configured": True,
                "detail": "HTTP integration without dedicated credentials",
            },
            {
                "name": "youtube_data_api",
                "configured": bool(self.settings.youtube_api_key),
                "detail": "YOUTUBE_API_KEY present" if self.settings.youtube_api_key else "YOUTUBE_API_KEY missing",
            },
            {
                "name": "youtube_analytics_oauth",
                "configured": analytics_configured,
                "detail": "OAuth refresh flow configured" if analytics_configured else "OAuth fields missing in .env",
            },
            {
                "name": "ollama",
                "configured": bool(self.settings.ollama_base_url and self.settings.ollama_model),
                "detail": f"{self.settings.ollama_model} via {self.settings.ollama_base_url}",
            },
        ]

    def _pricing_configured(self) -> bool:
        return any(
            value > 0
            for value in (
                self.settings.gemini_text_input_cost_per_1m,
                self.settings.gemini_text_output_cost_per_1m,
                self.settings.gemini_tts_input_cost_per_1m,
                self.settings.gemini_tts_output_cost_per_1m,
                self.settings.ollama_estimated_cost_per_1m,
            )
        )

    def get_health_details(self) -> dict:
        return {
            "status": "ok",
            "python_version": platform.python_version(),
            "database_url": self.settings.database_url,
            "database_reachable": self._database_reachable(),
            "ffmpeg_available": shutil.which("ffmpeg") is not None,
            "storage": get_storage_report(self.settings),
            "external_services": self._external_services(),
            "cost_control": {
                "usage_routes_available": True,
                "ai_usage_logging_ready": True,
                "pricing_configured": self._pricing_configured(),
                "top_risk": "tts_rework",
            },
        }


operations_service = OperationsService()
