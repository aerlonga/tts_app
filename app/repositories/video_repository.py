from __future__ import annotations

from pathlib import Path

from app.models.tables import MetricsSnapshot, Video
from app.repositories.utils import SQLAlchemyRepository, model_to_dict, parse_date, parse_datetime


class VideoRepository(SQLAlchemyRepository):
    def __init__(self, db_path: str | Path | None = None) -> None:
        super().__init__(db_path)

    def ensure_video(
        self,
        *,
        youtube_video_id: str,
        title: str | None = None,
        description: str | None = None,
        platform: str = "youtube",
        content_type: str = "long_video",
        duration_seconds: int | None = None,
        published_at: str | None = None,
    ) -> dict:
        with self._session() as session:
            row = session.query(Video).filter(Video.youtube_video_id == youtube_video_id).one_or_none()
            if row is None:
                row = Video(youtube_video_id=youtube_video_id)
                session.add(row)

            updates = {
                "title": title,
                "description": description,
                "platform": platform,
                "content_type": content_type,
                "duration_seconds": duration_seconds,
                "published_at": parse_datetime(published_at),
            }
            for field, value in updates.items():
                if value is not None:
                    setattr(row, field, value)
            session.flush()
            session.refresh(row)
            return model_to_dict(row)

    def get_video_by_youtube_id(self, youtube_video_id: str) -> dict | None:
        with self._session() as session:
            row = session.query(Video).filter(Video.youtube_video_id == youtube_video_id).one_or_none()
            return model_to_dict(row) if row else None

    def save_metrics_snapshot(
        self,
        *,
        video_id: int,
        snapshot_date: str,
        views: int = 0,
        watch_time_minutes: int = 0,
        avg_retention_percent: float = 0.0,
        ctr_percent: float = 0.0,
        likes: int = 0,
        comments: int = 0,
        subscribers_gained: int = 0,
    ) -> dict:
        with self._session() as session:
            row = MetricsSnapshot(
                video_id=video_id,
                snapshot_date=parse_date(snapshot_date),
                views=views,
                watch_time_minutes=watch_time_minutes,
                avg_retention_percent=avg_retention_percent,
                ctr_percent=ctr_percent,
                likes=likes,
                comments=comments,
                subscribers_gained=subscribers_gained,
            )
            session.add(row)
            session.flush()
            session.refresh(row)
            return model_to_dict(row)
