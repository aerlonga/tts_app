from pydantic import BaseModel, Field, HttpUrl


class EnhanceRequest(BaseModel):
    api_key: str | None = None
    text: str = Field(min_length=1)
    language: str = "pt"
    generate_image_prompts: bool = False


class ScriptPromptItem(BaseModel):
    timestamp: str = "00:00"
    cue: str = ""
    prompt: str


class EnhanceResponse(BaseModel):
    enhanced_text: str
    image_prompts: list[ScriptPromptItem] = Field(default_factory=list)


class GenerateTTSRequest(BaseModel):
    api_key: str | None = None
    text: str = Field(min_length=1)
    voice: str = "Charon"
    language: str = "pt"


class GenerateTTSStreamRequest(GenerateTTSRequest):
    session_id: str | None = None


class GenerateScriptRequest(BaseModel):
    api_key: str | None = None
    url: HttpUrl
    language: str = "pt"


class GenerateScriptResponse(BaseModel):
    script: str
    image_prompts: list[ScriptPromptItem]
    source_chars: int


class ShortPromptItem(BaseModel):
    cue: str = ""
    prompt: str


class WhiskPromptItem(BaseModel):
    cue: str = ""
    prompt: str


class TimelineSegment(BaseModel):
    slot_index: int
    asset_kind: str
    duration_seconds: int
    motion_preset: str
    overlay_text: str | None = None


class ProductionPack(BaseModel):
    template_id: str
    flow_video_prompt: str
    whisk_image_prompts: list[WhiskPromptItem]
    timeline_segments: list[TimelineSegment]
    caption_text: str
    cta_text: str


class ShortItem(BaseModel):
    id: str
    title: str
    hook: str
    script: str
    cta: str
    image_prompts: list[ShortPromptItem]
    broll_keywords: list[str]
    production_pack: ProductionPack | None = None


class GenerateShortRequest(BaseModel):
    api_key: str | None = None
    script: str = Field(min_length=500)
    count: int = 3
    duration_seconds: int = 60
    language: str = "pt"


class GenerateShortResponse(BaseModel):
    shorts: list[ShortItem]
    count: int
    duration_seconds: int


class AssetSearchRequest(BaseModel):
    keywords: list[str] = Field(min_length=1)
    collection: str = "prelinger"


class BrollClip(BaseModel):
    title: str = ""
    identifier: str
    license: str = ""
    download_url: str
    thumb: str = ""
    preview_url: str = ""


class AssetSearchResponse(BaseModel):
    clips: list[BrollClip]


class AssembleJobResponse(BaseModel):
    job_id: str


class AssembleStatusResponse(BaseModel):
    status: str
    progress: float
    download_url: str | None = None
    error: str | None = None


class BrollDownloadRequest(BaseModel):
    url: HttpUrl


class BrollDownloadResponse(BaseModel):
    local_path: str
    filename: str
