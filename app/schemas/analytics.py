from pydantic import BaseModel


class AnalyticsChannelSummary(BaseModel):
    start_date: str
    end_date: str
    views: int = 0
    watch_time_minutes: float = 0.0
    avg_view_duration_seconds: float = 0.0
    avg_retention_percent: float = 0.0
    impressions: int = 0
    ctr_percent: float = 0.0
    likes: int = 0
    comments: int = 0
    subscribers_gained: int = 0
    likes_per_view_percent: float = 0.0
    comments_per_view_percent: float = 0.0


class AnalyticsChannelSummaryResponse(BaseModel):
    item: AnalyticsChannelSummary


class AnalyticsVideoMetric(BaseModel):
    youtube_video_id: str
    title: str | None = None
    views: int = 0
    watch_time_minutes: float = 0.0
    avg_retention_percent: float = 0.0
    ctr_percent: float = 0.0
    likes: int = 0
    comments: int = 0
    subscribers_gained: int = 0


class AnalyticsVideosResponse(BaseModel):
    start_date: str
    end_date: str
    count: int
    items: list[AnalyticsVideoMetric]


class AnalyticsVideoDetailResponse(BaseModel):
    start_date: str
    end_date: str
    item: AnalyticsVideoMetric
