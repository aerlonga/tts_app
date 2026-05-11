from __future__ import annotations

import time
from datetime import date, timedelta

import requests

from app.core.config import Settings, get_settings
from app.repositories.video_repository import VideoRepository


class YouTubeAnalyticsService:
    def __init__(
        self,
        *,
        video_repository: VideoRepository | None = None,
        settings: Settings | None = None,
    ) -> None:
        self.video_repository = video_repository or VideoRepository()
        self.settings = settings or get_settings()
        self._access_token: str | None = None
        self._access_token_expires_at: float = 0.0

    def _require_oauth_config(self) -> None:
        missing = [
            name
            for name, value in (
                ("YOUTUBE_CLIENT_ID", self.settings.youtube_client_id),
                ("YOUTUBE_CLIENT_SECRET", self.settings.youtube_client_secret),
                ("YOUTUBE_REFRESH_TOKEN", self.settings.youtube_refresh_token),
            )
            if not value
        ]
        if missing:
            missing_list = ", ".join(missing)
            raise ValueError(
                f"YouTube Analytics OAuth nao configurado. Defina {missing_list} no .env."
            )

    def _token_is_valid(self) -> bool:
        return bool(self._access_token and time.time() < self._access_token_expires_at - 60)

    def _refresh_access_token(self) -> str:
        self._require_oauth_config()
        if self._token_is_valid():
            return self._access_token or ""

        response = requests.post(
            "https://oauth2.googleapis.com/token",
            data={
                "client_id": self.settings.youtube_client_id,
                "client_secret": self.settings.youtube_client_secret,
                "refresh_token": self.settings.youtube_refresh_token,
                "grant_type": "refresh_token",
            },
            timeout=30,
        )
        response.raise_for_status()
        payload = response.json()
        self._access_token = payload["access_token"]
        self._access_token_expires_at = time.time() + int(payload.get("expires_in", 3600))
        return self._access_token

    def _request_report(self, params: dict) -> dict:
        token = self._refresh_access_token()
        response = requests.get(
            f"{self.settings.youtube_analytics_api_base}/reports",
            headers={"Authorization": f"Bearer {token}"},
            params=params,
            timeout=30,
        )
        response.raise_for_status()
        return response.json()

    @staticmethod
    def _default_date_range() -> tuple[str, str]:
        end = date.today()
        start = end - timedelta(days=28)
        return start.isoformat(), end.isoformat()

    @staticmethod
    def _row_to_dict(headers: list[dict], row: list) -> dict:
        return {header["name"]: row[index] for index, header in enumerate(headers)}

    def _run_video_report(self, *, start_date: str, end_date: str, video_id: str | None = None, max_results: int = 10) -> list[dict]:
        payload = self._request_report(
            {
                "ids": "channel==MINE",
                "startDate": start_date,
                "endDate": end_date,
                "metrics": (
                    "views,estimatedMinutesWatched,averageViewPercentage,"
                    "impressionsClickThroughRate,likes,comments,subscribersGained"
                ),
                "dimensions": "video",
                "sort": "-views",
                "maxResults": max_results,
                **({"filters": f"video=={video_id}"} if video_id else {}),
            }
        )
        headers = payload.get("columnHeaders", [])
        rows = payload.get("rows", [])
        return [self._row_to_dict(headers, row) for row in rows]

    def get_channel_summary(self, *, start_date: str | None = None, end_date: str | None = None) -> dict:
        start_date = start_date or self._default_date_range()[0]
        end_date = end_date or self._default_date_range()[1]
        payload = self._request_report(
            {
                "ids": "channel==MINE",
                "startDate": start_date,
                "endDate": end_date,
                "metrics": (
                    "views,estimatedMinutesWatched,averageViewDuration,"
                    "averageViewPercentage,impressions,impressionsClickThroughRate,"
                    "likes,comments,subscribersGained"
                ),
            }
        )
        headers = payload.get("columnHeaders", [])
        row = payload.get("rows", [[]])[0] if payload.get("rows") else []
        mapped = self._row_to_dict(headers, row) if row else {}
        views = int(mapped.get("views", 0) or 0)
        likes = int(mapped.get("likes", 0) or 0)
        comments = int(mapped.get("comments", 0) or 0)
        return {
            "start_date": start_date,
            "end_date": end_date,
            "views": views,
            "watch_time_minutes": float(mapped.get("estimatedMinutesWatched", 0) or 0),
            "avg_view_duration_seconds": float(mapped.get("averageViewDuration", 0) or 0),
            "avg_retention_percent": float(mapped.get("averageViewPercentage", 0) or 0),
            "impressions": int(mapped.get("impressions", 0) or 0),
            "ctr_percent": float(mapped.get("impressionsClickThroughRate", 0) or 0),
            "likes": likes,
            "comments": comments,
            "subscribers_gained": int(mapped.get("subscribersGained", 0) or 0),
            "likes_per_view_percent": round((likes / views) * 100, 3) if views else 0.0,
            "comments_per_view_percent": round((comments / views) * 100, 3) if views else 0.0,
        }

    def list_video_metrics(self, *, start_date: str | None = None, end_date: str | None = None, max_results: int = 10) -> dict:
        start_date = start_date or self._default_date_range()[0]
        end_date = end_date or self._default_date_range()[1]
        rows = self._run_video_report(start_date=start_date, end_date=end_date, max_results=max_results)
        items = [self._normalize_video_metric(row, end_date) for row in rows]
        return {"start_date": start_date, "end_date": end_date, "count": len(items), "items": items}

    def get_video_metrics(self, *, video_id: str, start_date: str | None = None, end_date: str | None = None) -> dict:
        start_date = start_date or self._default_date_range()[0]
        end_date = end_date or self._default_date_range()[1]
        rows = self._run_video_report(start_date=start_date, end_date=end_date, video_id=video_id, max_results=1)
        if not rows:
            raise ValueError("Metricas nao encontradas para o video informado.")
        item = self._normalize_video_metric(rows[0], end_date)
        return {"start_date": start_date, "end_date": end_date, "item": item}

    def _normalize_video_metric(self, row: dict, snapshot_date: str) -> dict:
        youtube_video_id = str(row.get("video", ""))
        local_video = self.video_repository.ensure_video(youtube_video_id=youtube_video_id, title=youtube_video_id)
        normalized = {
            "youtube_video_id": youtube_video_id,
            "title": local_video.get("title"),
            "views": int(row.get("views", 0) or 0),
            "watch_time_minutes": float(row.get("estimatedMinutesWatched", 0) or 0),
            "avg_retention_percent": float(row.get("averageViewPercentage", 0) or 0),
            "ctr_percent": float(row.get("impressionsClickThroughRate", 0) or 0),
            "likes": int(row.get("likes", 0) or 0),
            "comments": int(row.get("comments", 0) or 0),
            "subscribers_gained": int(row.get("subscribersGained", 0) or 0),
        }
        self.video_repository.save_metrics_snapshot(
            video_id=local_video["id"],
            snapshot_date=snapshot_date,
            views=normalized["views"],
            watch_time_minutes=int(normalized["watch_time_minutes"]),
            avg_retention_percent=normalized["avg_retention_percent"],
            ctr_percent=normalized["ctr_percent"],
            likes=normalized["likes"],
            comments=normalized["comments"],
            subscribers_gained=normalized["subscribers_gained"],
        )
        return normalized


youtube_analytics_service = YouTubeAnalyticsService()
