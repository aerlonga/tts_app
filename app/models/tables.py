from __future__ import annotations

from sqlalchemy import Date, DateTime, Float, ForeignKey, Index, Integer, String, Text, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column
from sqlalchemy.sql import func

from app.models.base import Base
from app.models.types import EmbeddingVector


class Video(Base):
    __tablename__ = "videos"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    title: Mapped[str | None] = mapped_column(Text)
    description: Mapped[str | None] = mapped_column(Text)
    platform: Mapped[str | None] = mapped_column(String(20))
    content_type: Mapped[str | None] = mapped_column(String(20))
    duration_seconds: Mapped[int | None] = mapped_column(Integer)
    topic: Mapped[str | None] = mapped_column(Text)
    nicho: Mapped[str | None] = mapped_column(Text)
    published_at: Mapped[object | None] = mapped_column(DateTime(timezone=True))
    youtube_video_id: Mapped[str | None] = mapped_column(String(50), unique=True, index=True)
    script_path: Mapped[str | None] = mapped_column(Text)
    audio_path: Mapped[str | None] = mapped_column(Text)
    video_path: Mapped[str | None] = mapped_column(Text)
    created_at: Mapped[object | None] = mapped_column(DateTime(timezone=True), server_default=func.now())
    embedding: Mapped[list[float] | None] = mapped_column(EmbeddingVector(768), nullable=True)


class MetricsSnapshot(Base):
    __tablename__ = "metrics_snapshots"
    __table_args__ = (Index("idx_metrics_snapshots_video_date", "video_id", "snapshot_date"),)

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    video_id: Mapped[int | None] = mapped_column(Integer, ForeignKey("videos.id"))
    snapshot_date: Mapped[object | None] = mapped_column(Date)
    views: Mapped[int | None] = mapped_column(Integer)
    watch_time_minutes: Mapped[int | None] = mapped_column(Integer)
    avg_retention_percent: Mapped[float | None] = mapped_column(Float)
    ctr_percent: Mapped[float | None] = mapped_column(Float)
    likes: Mapped[int | None] = mapped_column(Integer)
    comments: Mapped[int | None] = mapped_column(Integer)
    subscribers_gained: Mapped[int | None] = mapped_column(Integer)


class Idea(Base):
    __tablename__ = "ideas"
    __table_args__ = (Index("idx_ideas_topic_generated_on", "topic", "generated_on"),)

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    title: Mapped[str | None] = mapped_column(Text)
    hook: Mapped[str | None] = mapped_column(Text)
    format: Mapped[str | None] = mapped_column(String(20))
    platform: Mapped[str | None] = mapped_column(String(20))
    topic: Mapped[str | None] = mapped_column(Text)
    keywords: Mapped[str | None] = mapped_column(Text)
    source: Mapped[str | None] = mapped_column(String(20))
    status: Mapped[str | None] = mapped_column(String(20))
    reason: Mapped[str | None] = mapped_column(Text)
    estimated_duration_seconds: Mapped[int | None] = mapped_column(Integer, default=0)
    content_type: Mapped[str | None] = mapped_column(String(20))
    language: Mapped[str | None] = mapped_column(String(10))
    request_fingerprint: Mapped[str | None] = mapped_column(Text)
    generated_on: Mapped[str | None] = mapped_column(String(10))
    created_at: Mapped[object | None] = mapped_column(DateTime(timezone=True), server_default=func.now())
    embedding: Mapped[list[float] | None] = mapped_column(EmbeddingVector(768), nullable=True)


class Channel(Base):
    __tablename__ = "channels"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    youtube_channel_id: Mapped[str | None] = mapped_column(Text, unique=True, index=True)
    title: Mapped[str | None] = mapped_column(Text)
    description: Mapped[str | None] = mapped_column(Text)
    custom_url: Mapped[str | None] = mapped_column(Text)
    published_at: Mapped[object | None] = mapped_column(DateTime(timezone=True))
    subscriber_count: Mapped[int | None] = mapped_column(Integer)
    view_count: Mapped[int | None] = mapped_column(Integer)
    video_count: Mapped[int | None] = mapped_column(Integer)
    country: Mapped[str | None] = mapped_column(Text)
    thumbnail_url: Mapped[str | None] = mapped_column(Text)
    raw_json: Mapped[str | None] = mapped_column(Text)
    collected_at: Mapped[object | None] = mapped_column(DateTime(timezone=True), server_default=func.now())
    embedding: Mapped[list[float] | None] = mapped_column(EmbeddingVector(768), nullable=True)


class CompetitorVideo(Base):
    __tablename__ = "competitor_videos"
    __table_args__ = (Index("idx_competitor_videos_channel_id", "channel_id"),)

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    youtube_video_id: Mapped[str | None] = mapped_column(Text, unique=True, index=True)
    title: Mapped[str | None] = mapped_column(Text)
    description: Mapped[str | None] = mapped_column(Text)
    channel_id: Mapped[str | None] = mapped_column(Text)
    channel_title: Mapped[str | None] = mapped_column(Text)
    published_at: Mapped[object | None] = mapped_column(DateTime(timezone=True))
    duration_seconds: Mapped[int | None] = mapped_column(Integer)
    views: Mapped[int | None] = mapped_column(Integer)
    likes: Mapped[int | None] = mapped_column(Integer)
    comments: Mapped[int | None] = mapped_column(Integer)
    views_per_day: Mapped[float | None] = mapped_column(Float)
    like_rate_percent: Mapped[float | None] = mapped_column(Float)
    thumbnail_url: Mapped[str | None] = mapped_column(Text)
    search_query: Mapped[str | None] = mapped_column(Text)
    raw_json: Mapped[str | None] = mapped_column(Text)
    collected_at: Mapped[object | None] = mapped_column(DateTime(timezone=True), server_default=func.now())
    embedding: Mapped[list[float] | None] = mapped_column(EmbeddingVector(768), nullable=True)


class ContentReference(Base):
    __tablename__ = "content_references"
    __table_args__ = (
        UniqueConstraint("reference_type", "external_id", name="uq_content_references_lookup"),
        Index("idx_content_references_lookup", "reference_type", "external_id"),
    )

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    reference_type: Mapped[str] = mapped_column(Text, nullable=False)
    external_id: Mapped[str] = mapped_column(Text, nullable=False)
    source: Mapped[str | None] = mapped_column(Text)
    title: Mapped[str | None] = mapped_column(Text)
    url: Mapped[str | None] = mapped_column(Text)
    metadata_json: Mapped[str | None] = mapped_column(Text)
    collected_at: Mapped[object | None] = mapped_column(DateTime(timezone=True), server_default=func.now())
    embedding: Mapped[list[float] | None] = mapped_column(EmbeddingVector(768), nullable=True)


class Experiment(Base):
    __tablename__ = "experiments"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    name: Mapped[str | None] = mapped_column(Text)
    platform: Mapped[str | None] = mapped_column(Text)
    hypothesis: Mapped[str | None] = mapped_column(Text)
    variant: Mapped[str | None] = mapped_column(Text)
    status: Mapped[str | None] = mapped_column(Text)
    notes: Mapped[str | None] = mapped_column(Text)
    created_at: Mapped[object | None] = mapped_column(DateTime(timezone=True), server_default=func.now())


class AIUsageLog(Base):
    __tablename__ = "ai_usage_logs"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    feature: Mapped[str] = mapped_column(Text, nullable=False)
    provider: Mapped[str] = mapped_column(Text, nullable=False)
    model: Mapped[str] = mapped_column(Text, nullable=False)
    input_tokens: Mapped[int | None] = mapped_column(Integer, default=0)
    output_tokens: Mapped[int | None] = mapped_column(Integer, default=0)
    estimated_cost_usd: Mapped[float | None] = mapped_column(Float, default=0.0)
    video_id: Mapped[int | None] = mapped_column(Integer)
    created_at: Mapped[object | None] = mapped_column(DateTime(timezone=True), server_default=func.now())
