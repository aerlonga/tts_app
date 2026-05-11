from __future__ import annotations

from app.services.broll_service import BrollService, broll_service


class ImageSearchService:
    def __init__(self, broll: BrollService | None = None) -> None:
        self.broll = broll or broll_service

    def search_assets(self, *, keywords: list[str], collection: str = "prelinger") -> dict:
        return {"clips": self.broll.search(keywords=keywords, collection=collection)}


image_search_service = ImageSearchService()
