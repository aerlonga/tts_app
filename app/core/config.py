from functools import lru_cache
from pydantic import AliasChoices, Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
        populate_by_name=True,
    )

    app_env: str = Field(default="development", validation_alias=AliasChoices("APP_ENV"))
    fastapi_app_name: str = Field(
        default="Video AI Automation API",
        validation_alias=AliasChoices("APP_NAME", "FASTAPI_APP_NAME"),
    )
    fastapi_host: str = Field(
        default="127.0.0.1",
        validation_alias=AliasChoices("APP_HOST", "FASTAPI_HOST"),
    )
    fastapi_port: int = Field(
        default=8000,
        validation_alias=AliasChoices("APP_PORT", "FASTAPI_PORT"),
    )
    app_debug: bool = Field(
        default=False,
        validation_alias=AliasChoices("APP_DEBUG"),
    )
    database_url: str = Field(
        default="postgresql://ttsapp:ttsapp_local@localhost:5432/video_ai_automation",
        validation_alias=AliasChoices("DATABASE_URL"),
    )
    storage_root: str = Field(
        default="storage",
        validation_alias=AliasChoices("STORAGE_PATH", "STORAGE_ROOT"),
    )
    tmp_sessions_dir: str = Field(default="/tmp/tts_sessions")
    tmp_jobs_dir: str = Field(default="/tmp/tts_jobs")
    broll_dir: str = Field(default="/tmp/broll")

    gemini_api_key: str = Field(default="")
    gemini_model: str = Field(default="gemini-1.5-flash", validation_alias=AliasChoices("GEMINI_MODEL"))
    gemini_embedding_model: str = Field(
        default="text-embedding-004",
        validation_alias=AliasChoices("GEMINI_EMBEDDING_MODEL"),
    )
    youtube_api_key: str = Field(default="")
    youtube_client_id: str = Field(default="")
    youtube_client_secret: str = Field(default="")
    youtube_refresh_token: str = Field(default="")
    youtube_redirect_uri: str = Field(default="http://localhost:8000/auth/youtube/callback")
    youtube_data_api_base: str = Field(default="https://www.googleapis.com/youtube/v3")
    youtube_analytics_api_base: str = Field(default="https://youtubeanalytics.googleapis.com/v2")
    ollama_base_url: str = Field(default="http://localhost:11434", validation_alias=AliasChoices("OLLAMA_BASE_URL"))
    ollama_model: str = Field(default="llama3.1:8b", validation_alias=AliasChoices("OLLAMA_MODEL"))
    ollama_embedding_model: str = Field(
        default="nomic-embed-text",
        validation_alias=AliasChoices("OLLAMA_EMBEDDING_MODEL"),
    )
    gemini_text_input_cost_per_1m: float = Field(default=0.0, validation_alias=AliasChoices("GEMINI_TEXT_INPUT_COST_PER_1M"))
    gemini_text_output_cost_per_1m: float = Field(default=0.0, validation_alias=AliasChoices("GEMINI_TEXT_OUTPUT_COST_PER_1M"))
    gemini_tts_input_cost_per_1m: float = Field(default=0.0, validation_alias=AliasChoices("GEMINI_TTS_INPUT_COST_PER_1M"))
    gemini_tts_output_cost_per_1m: float = Field(default=0.0, validation_alias=AliasChoices("GEMINI_TTS_OUTPUT_COST_PER_1M"))
    ollama_estimated_cost_per_1m: float = Field(default=0.0, validation_alias=AliasChoices("OLLAMA_ESTIMATED_COST_PER_1M"))
    flask_port: int = Field(default=5000)
    flask_debug: bool = Field(default=False)

@lru_cache(maxsize=1)
def get_settings() -> Settings:
    return Settings()
