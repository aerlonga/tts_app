from pydantic import BaseModel


class YouTubeVideoItem(BaseModel):
    youtube_video_id: str
    title: str
    description: str = ""
    channel_id: str
    channel_title: str = ""
    published_at: str | None = None
    duration_seconds: int = 0
    views: int = 0
    likes: int = 0
    comments: int = 0
    views_per_day: float = 0.0
    like_rate_percent: float = 0.0
    relevance_score: float = 0.0
    thumbnail_url: str | None = None
    url: str | None = None


class YouTubeChannelItem(BaseModel):
    youtube_channel_id: str
    title: str
    description: str = ""
    custom_url: str | None = None
    published_at: str | None = None
    subscriber_count: int = 0
    view_count: int = 0
    video_count: int = 0
    channel_age_days: int = 0
    country: str | None = None
    thumbnail_url: str | None = None
    url: str | None = None


class YouTubeSearchResponse(BaseModel):
    query: str
    order: str
    count: int
    from_cache: bool
    items: list[YouTubeVideoItem]


class YouTubeVideoResponse(BaseModel):
    from_cache: bool
    item: YouTubeVideoItem


class YouTubeChannelResponse(BaseModel):
    from_cache: bool
    item: YouTubeChannelItem
