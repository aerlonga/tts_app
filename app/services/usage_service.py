from __future__ import annotations

from app.repositories.ai_usage_repository import AIUsageRepository


class UsageService:
    def __init__(self, repository: AIUsageRepository | None = None) -> None:
        self.repository = repository or AIUsageRepository()

    def get_summary(self, start_date: str | None = None, end_date: str | None = None) -> dict:
        return self.repository.get_summary(start_date=start_date, end_date=end_date)

    def get_by_feature(self, start_date: str | None = None, end_date: str | None = None) -> list[dict]:
        return self.repository.get_usage_by_feature(start_date=start_date, end_date=end_date)


usage_service = UsageService()
