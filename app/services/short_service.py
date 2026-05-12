from __future__ import annotations

from typing import TYPE_CHECKING
from shorts_contract import SHORTS_SYSTEM_PROMPT, extract_json_block, normalize_short_item

if TYPE_CHECKING:
    from app.services.gemini_service import GeminiService


class ShortService:
    def __init__(self, gemini: GeminiService | None = None) -> None:
        if gemini is None:
            from app.services.gemini_service import gemini_service

            self.gemini = gemini_service
        else:
            self.gemini = gemini

    def generate_shorts(
        self,
        *,
        script: str,
        count: int = 3,
        duration_seconds: int = 60,
        api_key: str | None = None,
    ) -> dict:
        count = 2 if count == 2 else 3
        duration_seconds = duration_seconds if duration_seconds in (45, 60, 65) else 60
        platform = "TikTok Creator Rewards" if duration_seconds == 65 else "YouTube Shorts"
        duration_rule = (
            "Each TikTok script must be long enough for a final narrated video between 61 and 65 seconds. "
            "Do not make it shorter than 61 seconds."
            if duration_seconds == 65
            else f"Each YouTube Shorts script must fit safely within {duration_seconds} seconds."
        )

        prompt = (
            f"Platform: {platform}.\n"
            f"Generate exactly {count} vertical videos.\n"
            f"{duration_rule}\n\n"
            f"LONG DOCUMENTARY SCRIPT:\n{script}"
        )
        result = self.gemini.generate_text(
            feature="short_generation",
            contents=prompt,
            api_key=api_key,
            model="gemini-2.5-flash",
            system_instruction=SHORTS_SYSTEM_PROMPT,
            temperature=0.65,
        )

        parsed = extract_json_block(result["text"])
        raw_shorts = parsed if isinstance(parsed, list) else parsed.get("shorts", [])
        shorts = [
            normalize_short_item(item, i)
            for i, item in enumerate(raw_shorts)
            if isinstance(item, dict)
        ][:count]

        if not shorts:
            raise ValueError("O Gemini nao retornou Shorts validos.")

        return {
            "shorts": shorts,
            "count": len(shorts),
            "duration_seconds": duration_seconds,
            "usage": result["usage"],
        }


class _LazyShortServiceProxy:
    def __init__(self) -> None:
        self._service: ShortService | None = None

    def _resolve(self) -> ShortService:
        if self._service is None:
            self._service = ShortService()
        return self._service

    def __getattr__(self, name: str):
        return getattr(self._resolve(), name)


short_service = _LazyShortServiceProxy()
