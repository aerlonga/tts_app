from pydantic import BaseModel, Field


class IdeaItem(BaseModel):
    title: str
    hook: str
    format: str
    platform: str
    reason: str
    keywords: list[str] = []
    estimated_duration_seconds: int = 0
    source: str = "ai_generated"
    status: str = "pending"


class GenerateIdeasRequest(BaseModel):
    topic: str = Field(min_length=1)
    platforms: list[str] = Field(default_factory=lambda: ["youtube"])
    content_type: str = "long_video"
    language: str = "pt"
    quantity: int = Field(default=10, ge=1, le=20)
    force: bool = False
    api_key: str | None = None


class GenerateIdeasResponse(BaseModel):
    ideas: list[IdeaItem]
    from_cache: bool
