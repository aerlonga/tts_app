from __future__ import annotations

import json
from pathlib import Path

from sqlalchemy import func

from app.models.tables import Channel, CompetitorVideo, ContentReference
from app.repositories.utils import SQLAlchemyRepository, model_to_dict, parse_datetime


class YouTubeRepository(SQLAlchemyRepository):
    def __init__(self, db_path: str | Path | None = None) -> None:
        super().__init__(db_path)

    def get_cached_payload(self, *, reference_type: str, external_id: str, max_age_hours: int) -> dict | None:
        with self._session() as session:
            row = (
                session.query(ContentReference)
                .filter(
                    ContentReference.reference_type == reference_type,
                    ContentReference.external_id == external_id,
                    self._fresh_clause(ContentReference.collected_at, max_age_hours),
                )
                .one_or_none()
            )
        if not row:
            return None
        return json.loads(row.metadata_json or "{}")

    def _fresh_clause(self, column, max_age_hours: int):
        if self.database_url.startswith("sqlite"):
            return column >= func.datetime("now", f"-{max_age_hours} hours")
        return column >= func.now() - func.make_interval(0, 0, 0, 0, max_age_hours)

    def cache_payload(
        self,
        *,
        reference_type: str,
        external_id: str,
        payload: dict,
        source: str,
        title: str = "",
        url: str = "",
    ) -> None:
        with self._session() as session:
            row = (
                session.query(ContentReference)
                .filter(
                    ContentReference.reference_type == reference_type,
                    ContentReference.external_id == external_id,
                )
                .one_or_none()
            )
            if row is None:
                row = ContentReference(reference_type=reference_type, external_id=external_id)
                session.add(row)
            row.source = source
            row.title = title
            row.url = url
            row.metadata_json = json.dumps(payload, ensure_ascii=True)
            row.collected_at = func.now()

    def upsert_channel(self, channel: dict) -> dict:
        with self._session() as session:
            row = session.query(Channel).filter(Channel.youtube_channel_id == channel["youtube_channel_id"]).one_or_none()
            if row is None:
                row = Channel(youtube_channel_id=channel["youtube_channel_id"])
                session.add(row)
            row.title = channel.get("title")
            row.description = channel.get("description")
            row.custom_url = channel.get("custom_url")
            row.published_at = parse_datetime(channel.get("published_at"))
            row.subscriber_count = channel.get("subscriber_count", 0)
            row.view_count = channel.get("view_count", 0)
            row.video_count = channel.get("video_count", 0)
            row.country = channel.get("country")
            row.thumbnail_url = channel.get("thumbnail_url")
            row.raw_json = json.dumps(channel.get("raw_json", {}), ensure_ascii=True)
            row.collected_at = func.now()
            session.flush()
            session.refresh(row)
        return self._deserialize_channel(row) if row else channel

    def get_channel(self, youtube_channel_id: str, max_age_hours: int | None = None) -> dict | None:
        with self._session() as session:
            query = session.query(Channel).filter(Channel.youtube_channel_id == youtube_channel_id)
            if max_age_hours is not None:
                query = query.filter(self._fresh_clause(Channel.collected_at, max_age_hours))
            row = query.one_or_none()
        return self._deserialize_channel(row) if row else None

    def _deserialize_channel(self, row) -> dict:
        data = model_to_dict(row)
        raw_json = data.get("raw_json")
        data["raw_json"] = json.loads(raw_json) if raw_json else {}
        return data

    def upsert_competitor_video(self, video: dict) -> dict:
        with self._session() as session:
            row = (
                session.query(CompetitorVideo)
                .filter(CompetitorVideo.youtube_video_id == video["youtube_video_id"])
                .one_or_none()
            )
            if row is None:
                row = CompetitorVideo(youtube_video_id=video["youtube_video_id"])
                session.add(row)
            row.title = video.get("title")
            row.description = video.get("description")
            row.channel_id = video.get("channel_id")
            row.channel_title = video.get("channel_title")
            row.published_at = parse_datetime(video.get("published_at"))
            row.duration_seconds = video.get("duration_seconds")
            row.views = video.get("views", 0)
            row.likes = video.get("likes", 0)
            row.comments = video.get("comments", 0)
            row.views_per_day = video.get("views_per_day", 0.0)
            row.like_rate_percent = video.get("like_rate_percent", 0.0)
            row.thumbnail_url = video.get("thumbnail_url")
            row.search_query = video.get("search_query")
            row.raw_json = json.dumps(video.get("raw_json", {}), ensure_ascii=True)
            row.collected_at = func.now()
            session.flush()
            session.refresh(row)
        return self._deserialize_competitor_video(row) if row else video

    def get_competitor_video(self, youtube_video_id: str, max_age_hours: int | None = None) -> dict | None:
        with self._session() as session:
            query = session.query(CompetitorVideo).filter(CompetitorVideo.youtube_video_id == youtube_video_id)
            if max_age_hours is not None:
                query = query.filter(self._fresh_clause(CompetitorVideo.collected_at, max_age_hours))
            row = query.one_or_none()
        return self._deserialize_competitor_video(row) if row else None

    def _deserialize_competitor_video(self, row) -> dict:
        data = model_to_dict(row)
        raw_json = data.get("raw_json")
        data["raw_json"] = json.loads(raw_json) if raw_json else {}
        return data
