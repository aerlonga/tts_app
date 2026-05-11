"""initial schema

Revision ID: 20260511_0001
Revises:
Create Date: 2026-05-11
"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from pgvector.sqlalchemy import Vector

revision: str = "20260511_0001"
down_revision: Union[str, None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.execute("CREATE EXTENSION IF NOT EXISTS vector")
    op.create_table(
        "videos",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("title", sa.Text(), nullable=True),
        sa.Column("description", sa.Text(), nullable=True),
        sa.Column("platform", sa.String(length=20), nullable=True),
        sa.Column("content_type", sa.String(length=20), nullable=True),
        sa.Column("duration_seconds", sa.Integer(), nullable=True),
        sa.Column("topic", sa.Text(), nullable=True),
        sa.Column("nicho", sa.Text(), nullable=True),
        sa.Column("published_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("youtube_video_id", sa.String(length=50), nullable=True),
        sa.Column("script_path", sa.Text(), nullable=True),
        sa.Column("audio_path", sa.Text(), nullable=True),
        sa.Column("video_path", sa.Text(), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=True),
        sa.Column("embedding", Vector(768), nullable=True),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(op.f("ix_videos_youtube_video_id"), "videos", ["youtube_video_id"], unique=True)
    op.create_table(
        "ideas",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("title", sa.Text(), nullable=True),
        sa.Column("hook", sa.Text(), nullable=True),
        sa.Column("format", sa.String(length=20), nullable=True),
        sa.Column("platform", sa.String(length=20), nullable=True),
        sa.Column("topic", sa.Text(), nullable=True),
        sa.Column("keywords", sa.Text(), nullable=True),
        sa.Column("source", sa.String(length=20), nullable=True),
        sa.Column("status", sa.String(length=20), nullable=True),
        sa.Column("reason", sa.Text(), nullable=True),
        sa.Column("estimated_duration_seconds", sa.Integer(), nullable=True),
        sa.Column("content_type", sa.String(length=20), nullable=True),
        sa.Column("language", sa.String(length=10), nullable=True),
        sa.Column("request_fingerprint", sa.Text(), nullable=True),
        sa.Column("generated_on", sa.String(length=10), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=True),
        sa.Column("embedding", Vector(768), nullable=True),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("idx_ideas_topic_generated_on", "ideas", ["topic", "generated_on"], unique=False)
    op.create_table(
        "channels",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("youtube_channel_id", sa.Text(), nullable=True),
        sa.Column("title", sa.Text(), nullable=True),
        sa.Column("description", sa.Text(), nullable=True),
        sa.Column("custom_url", sa.Text(), nullable=True),
        sa.Column("published_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("subscriber_count", sa.Integer(), nullable=True),
        sa.Column("view_count", sa.Integer(), nullable=True),
        sa.Column("video_count", sa.Integer(), nullable=True),
        sa.Column("country", sa.Text(), nullable=True),
        sa.Column("thumbnail_url", sa.Text(), nullable=True),
        sa.Column("raw_json", sa.Text(), nullable=True),
        sa.Column("collected_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=True),
        sa.Column("embedding", Vector(768), nullable=True),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(op.f("ix_channels_youtube_channel_id"), "channels", ["youtube_channel_id"], unique=True)
    op.create_table(
        "competitor_videos",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("youtube_video_id", sa.Text(), nullable=True),
        sa.Column("title", sa.Text(), nullable=True),
        sa.Column("description", sa.Text(), nullable=True),
        sa.Column("channel_id", sa.Text(), nullable=True),
        sa.Column("channel_title", sa.Text(), nullable=True),
        sa.Column("published_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("duration_seconds", sa.Integer(), nullable=True),
        sa.Column("views", sa.Integer(), nullable=True),
        sa.Column("likes", sa.Integer(), nullable=True),
        sa.Column("comments", sa.Integer(), nullable=True),
        sa.Column("views_per_day", sa.Float(), nullable=True),
        sa.Column("like_rate_percent", sa.Float(), nullable=True),
        sa.Column("thumbnail_url", sa.Text(), nullable=True),
        sa.Column("search_query", sa.Text(), nullable=True),
        sa.Column("raw_json", sa.Text(), nullable=True),
        sa.Column("collected_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=True),
        sa.Column("embedding", Vector(768), nullable=True),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("idx_competitor_videos_channel_id", "competitor_videos", ["channel_id"], unique=False)
    op.create_index(op.f("ix_competitor_videos_youtube_video_id"), "competitor_videos", ["youtube_video_id"], unique=True)
    op.create_table(
        "content_references",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("reference_type", sa.Text(), nullable=False),
        sa.Column("external_id", sa.Text(), nullable=False),
        sa.Column("source", sa.Text(), nullable=True),
        sa.Column("title", sa.Text(), nullable=True),
        sa.Column("url", sa.Text(), nullable=True),
        sa.Column("metadata_json", sa.Text(), nullable=True),
        sa.Column("collected_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=True),
        sa.Column("embedding", Vector(768), nullable=True),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("reference_type", "external_id", name="uq_content_references_lookup"),
    )
    op.create_index("idx_content_references_lookup", "content_references", ["reference_type", "external_id"], unique=False)
    op.create_table(
        "experiments",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("name", sa.Text(), nullable=True),
        sa.Column("platform", sa.Text(), nullable=True),
        sa.Column("hypothesis", sa.Text(), nullable=True),
        sa.Column("variant", sa.Text(), nullable=True),
        sa.Column("status", sa.Text(), nullable=True),
        sa.Column("notes", sa.Text(), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=True),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_table(
        "ai_usage_logs",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("feature", sa.Text(), nullable=False),
        sa.Column("provider", sa.Text(), nullable=False),
        sa.Column("model", sa.Text(), nullable=False),
        sa.Column("input_tokens", sa.Integer(), nullable=True),
        sa.Column("output_tokens", sa.Integer(), nullable=True),
        sa.Column("estimated_cost_usd", sa.Float(), nullable=True),
        sa.Column("video_id", sa.Integer(), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=True),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_table(
        "metrics_snapshots",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("video_id", sa.Integer(), nullable=True),
        sa.Column("snapshot_date", sa.Date(), nullable=True),
        sa.Column("views", sa.Integer(), nullable=True),
        sa.Column("watch_time_minutes", sa.Integer(), nullable=True),
        sa.Column("avg_retention_percent", sa.Float(), nullable=True),
        sa.Column("ctr_percent", sa.Float(), nullable=True),
        sa.Column("likes", sa.Integer(), nullable=True),
        sa.Column("comments", sa.Integer(), nullable=True),
        sa.Column("subscribers_gained", sa.Integer(), nullable=True),
        sa.ForeignKeyConstraint(["video_id"], ["videos.id"]),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("idx_metrics_snapshots_video_date", "metrics_snapshots", ["video_id", "snapshot_date"], unique=False)


def downgrade() -> None:
    op.drop_index("idx_metrics_snapshots_video_date", table_name="metrics_snapshots")
    op.drop_table("metrics_snapshots")
    op.drop_table("ai_usage_logs")
    op.drop_table("experiments")
    op.drop_index("idx_content_references_lookup", table_name="content_references")
    op.drop_table("content_references")
    op.drop_index(op.f("ix_competitor_videos_youtube_video_id"), table_name="competitor_videos")
    op.drop_index("idx_competitor_videos_channel_id", table_name="competitor_videos")
    op.drop_table("competitor_videos")
    op.drop_index(op.f("ix_channels_youtube_channel_id"), table_name="channels")
    op.drop_table("channels")
    op.drop_index("idx_ideas_topic_generated_on", table_name="ideas")
    op.drop_table("ideas")
    op.drop_index(op.f("ix_videos_youtube_video_id"), table_name="videos")
    op.drop_table("videos")
