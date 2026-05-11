from __future__ import annotations

import hashlib
import math
import re
from datetime import UTC, datetime

import requests

from app.core.config import Settings, get_settings
from app.repositories.youtube_repository import YouTubeRepository


_ISO8601_DURATION_RE = re.compile(
    r"^P(?:(?P<days>\d+)D)?(?:T(?:(?P<hours>\d+)H)?(?:(?P<minutes>\d+)M)?(?:(?P<seconds>\d+)S)?)?$"
)


class YouTubeDataService:
    def __init__(
        self,
        *,
        repository: YouTubeRepository | None = None,
        settings: Settings | None = None,
    ) -> None:
        self.repository = repository or YouTubeRepository()
        self.settings = settings or get_settings()

    def _resolve_api_key(self) -> str:
        api_key = (self.settings.youtube_api_key or "").strip()
        if not api_key:
            raise ValueError("YouTube Data API nao configurada. Defina YOUTUBE_API_KEY no .env.")
        return api_key

    def _request_json(self, path: str, params: dict) -> dict:
        api_key = self._resolve_api_key()
        response = requests.get(
            f"{self.settings.youtube_data_api_base}/{path}",
            params={**params, "key": api_key},
            timeout=30,
        )
        response.raise_for_status()
        return response.json()

    @staticmethod
    def _make_cache_key(prefix: str, *parts: object) -> str:
        joined = "::".join(str(part) for part in parts)
        return hashlib.sha256(f"{prefix}::{joined}".encode("utf-8")).hexdigest()

    @staticmethod
    def _parse_datetime(value: str | None) -> datetime | None:
        if not value:
            return None
        try:
            return datetime.fromisoformat(value.replace("Z", "+00:00"))
        except ValueError:
            return None

    @classmethod
    def _parse_duration_seconds(cls, value: str | None) -> int:
        if not value:
            return 0
        match = _ISO8601_DURATION_RE.match(value)
        if not match:
            return 0
        parts = {name: int(amount or 0) for name, amount in match.groupdict().items()}
        return parts["days"] * 86400 + parts["hours"] * 3600 + parts["minutes"] * 60 + parts["seconds"]

    @classmethod
    def _views_per_day(cls, views: int, published_at: str | None) -> float:
        published = cls._parse_datetime(published_at)
        if not published:
            return 0.0
        days = max((datetime.now(UTC) - published.astimezone(UTC)).days, 1)
        return round(views / days, 3)

    @staticmethod
    def _like_rate_percent(views: int, likes: int) -> float:
        if views <= 0:
            return 0.0
        return round((likes / views) * 100, 3)

    @staticmethod
    def _relevance_score(views_per_day: float, like_rate_percent: float, views: int) -> float:
        return round((views_per_day * 0.6) + (like_rate_percent * 10) + (math.log10(max(views, 1)) * 5), 3)

    @staticmethod
    def _thumbnail_url(thumbnails: dict | None) -> str | None:
        thumbnails = thumbnails or {}
        for key in ("maxres", "high", "medium", "default"):
            if key in thumbnails and thumbnails[key].get("url"):
                return thumbnails[key]["url"]
        return None

    def _normalize_channel(self, item: dict) -> dict:
        snippet = item.get("snippet", {})
        statistics = item.get("statistics", {})
        published_at = snippet.get("publishedAt")
        published_dt = self._parse_datetime(published_at)
        age_days = 0
        if published_dt:
            age_days = max((datetime.now(UTC) - published_dt.astimezone(UTC)).days, 0)

        return {
            "youtube_channel_id": item["id"],
            "title": snippet.get("title", ""),
            "description": snippet.get("description", ""),
            "custom_url": snippet.get("customUrl"),
            "published_at": published_at,
            "subscriber_count": int(statistics.get("subscriberCount", 0) or 0),
            "view_count": int(statistics.get("viewCount", 0) or 0),
            "video_count": int(statistics.get("videoCount", 0) or 0),
            "country": snippet.get("country"),
            "thumbnail_url": self._thumbnail_url(snippet.get("thumbnails")),
            "channel_age_days": age_days,
            "url": f"https://www.youtube.com/channel/{item['id']}",
            "raw_json": item,
        }

    def _normalize_video(self, *, item: dict, search_query: str = "") -> dict:
        snippet = item.get("snippet", {})
        statistics = item.get("statistics", {})
        content_details = item.get("contentDetails", {})
        published_at = snippet.get("publishedAt")
        views = int(statistics.get("viewCount", 0) or 0)
        likes = int(statistics.get("likeCount", 0) or 0)
        comments = int(statistics.get("commentCount", 0) or 0)
        views_per_day = self._views_per_day(views, published_at)
        like_rate_percent = self._like_rate_percent(views, likes)

        return {
            "youtube_video_id": item["id"],
            "title": snippet.get("title", ""),
            "description": snippet.get("description", ""),
            "channel_id": snippet.get("channelId", ""),
            "channel_title": snippet.get("channelTitle", ""),
            "published_at": published_at,
            "duration_seconds": self._parse_duration_seconds(content_details.get("duration")),
            "views": views,
            "likes": likes,
            "comments": comments,
            "views_per_day": views_per_day,
            "like_rate_percent": like_rate_percent,
            "relevance_score": self._relevance_score(views_per_day, like_rate_percent, views),
            "thumbnail_url": self._thumbnail_url(snippet.get("thumbnails")),
            "url": f"https://www.youtube.com/watch?v={item['id']}",
            "search_query": search_query,
            "raw_json": item,
        }

    def _load_video_items(self, video_ids: list[str]) -> list[dict]:
        if not video_ids:
            return []
        response = self._request_json(
            "videos",
            {
                "part": "snippet,statistics,contentDetails",
                "id": ",".join(video_ids),
                "maxResults": len(video_ids),
            },
        )
        return response.get("items", [])

    def _load_channel_items(self, channel_ids: list[str]) -> list[dict]:
        if not channel_ids:
            return []
        response = self._request_json(
            "channels",
            {
                "part": "snippet,statistics",
                "id": ",".join(channel_ids),
                "maxResults": len(channel_ids),
            },
        )
        return response.get("items", [])

    def search(self, *, query: str, max_results: int = 10, order: str = "relevance") -> dict:
        cache_key = self._make_cache_key("youtube_search", query.strip().lower(), max_results, order)
        cached = self.repository.get_cached_payload(
            reference_type="youtube_search",
            external_id=cache_key,
            max_age_hours=12,
        )
        if cached:
            return {**cached, "from_cache": True}

        search_response = self._request_json(
            "search",
            {
                "part": "snippet",
                "type": "video",
                "q": query,
                "maxResults": max_results,
                "order": order,
            },
        )
        video_ids = [item["id"]["videoId"] for item in search_response.get("items", []) if item.get("id", {}).get("videoId")]
        channel_ids = list(
            {
                item["snippet"]["channelId"]
                for item in search_response.get("items", [])
                if item.get("snippet", {}).get("channelId")
            }
        )

        videos = [self._normalize_video(item=item, search_query=query) for item in self._load_video_items(video_ids)]
        channels = [self._normalize_channel(item) for item in self._load_channel_items(channel_ids)]

        for channel in channels:
            self.repository.upsert_channel(channel)
        for video in videos:
            self.repository.upsert_competitor_video(video)

        if order == "viewCount":
            videos.sort(key=lambda item: item["views"], reverse=True)
        elif order == "date":
            videos.sort(key=lambda item: item.get("published_at") or "", reverse=True)
        else:
            videos.sort(key=lambda item: item["relevance_score"], reverse=True)

        payload = {
            "query": query,
            "order": order,
            "count": len(videos),
            "items": videos,
        }
        self.repository.cache_payload(
            reference_type="youtube_search",
            external_id=cache_key,
            payload=payload,
            source="youtube_data_api",
            title=query,
        )
        return {**payload, "from_cache": False}

    def get_video(self, *, video_id: str) -> dict:
        cached = self.repository.get_competitor_video(video_id, max_age_hours=24)
        if cached:
            normalized = {key: value for key, value in cached.items() if key != "raw_json"}
            normalized["relevance_score"] = self._relevance_score(
                normalized.get("views_per_day", 0.0),
                normalized.get("like_rate_percent", 0.0),
                normalized.get("views", 0),
            )
            normalized["url"] = f"https://www.youtube.com/watch?v={video_id}"
            return {"from_cache": True, "item": normalized}

        items = self._load_video_items([video_id])
        if not items:
            raise ValueError("Video nao encontrado no YouTube.")
        normalized = self._normalize_video(item=items[0])
        self.repository.upsert_competitor_video(normalized)
        return {"from_cache": False, "item": normalized}

    def get_channel(self, *, channel_id: str) -> dict:
        cached = self.repository.get_channel(channel_id, max_age_hours=24)
        if cached:
            normalized = {key: value for key, value in cached.items() if key != "raw_json"}
            normalized["url"] = f"https://www.youtube.com/channel/{channel_id}"
            return {"from_cache": True, "item": normalized}

        items = self._load_channel_items([channel_id])
        if not items:
            raise ValueError("Canal nao encontrado no YouTube.")
        normalized = self._normalize_channel(items[0])
        self.repository.upsert_channel(normalized)
        return {"from_cache": False, "item": normalized}


youtube_data_service = YouTubeDataService()
