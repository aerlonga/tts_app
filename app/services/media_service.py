from __future__ import annotations

from fastapi import UploadFile

from app.services.audio_service import AudioService, audio_service
from app.services.image_search_service import ImageSearchService, image_search_service
from app.services.script_service import ScriptService, script_service
from app.services.short_service import ShortService, short_service
from app.services.video_service import VideoService, video_service


class MediaService:
    def __init__(
        self,
        *,
        audio: AudioService | None = None,
        image_search: ImageSearchService | None = None,
        script: ScriptService | None = None,
        short: ShortService | None = None,
        video: VideoService | None = None,
    ) -> None:
        self.audio = audio or audio_service
        self.image_search = image_search or image_search_service
        self.script = script or script_service
        self.short = short or short_service
        self.video = video or video_service

    def search_assets(self, *, keywords: list[str], collection: str = "prelinger") -> dict:
        return self.image_search.search_assets(keywords=keywords, collection=collection)

    def generate_video_job(
        self,
        *,
        script: str,
        voice: str,
        api_key: str | None,
        asset_uploads: list[UploadFile],
        manifest_str: str | None,
        video_format: str = "long",
    ) -> str:
        return self.video.create_generated_video_job(
            script=script,
            voice=voice,
            api_key=api_key,
            asset_uploads=asset_uploads,
            manifest_str=manifest_str,
            video_format=video_format,
        )


media_service = MediaService()
