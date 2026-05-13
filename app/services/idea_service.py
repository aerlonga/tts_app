from __future__ import annotations

import hashlib
import json
from datetime import datetime

from app.core.runtime import extract_json_block
from app.repositories.idea_repository import IdeaRepository
from app.services.gemini_service import GeminiService, gemini_service


IDEAS_SYSTEM_PROMPT = """You generate content ideas for YouTube and TikTok.
Return only valid JSON with this shape:
{
  "ideas": [
    {
      "title": "string",
      "hook": "string",
      "format": "long_video|short",
      "platform": "youtube|tiktok",
      "reason": "string",
      "keywords": ["string"],
      "estimated_duration_seconds": 0
    }
  ]
}
Do not include markdown or explanations.
"""


class IdeaService:
    def __init__(
        self,
        *,
        gemini: GeminiService | None = None,
        repository: IdeaRepository | None = None,
    ) -> None:
        self.gemini = gemini or gemini_service
        self.repository = repository or IdeaRepository()

    @staticmethod
    def build_fingerprint(
        *,
        topic: str,
        platforms: list[str],
        content_type: str,
        language: str,
        quantity: int,
    ) -> str:
        payload = json.dumps(
            {
                "topic": topic.strip().lower(),
                "platforms": sorted(platforms),
                "content_type": content_type.strip().lower(),
                "language": language.strip().lower(),
                "quantity": quantity,
            },
            ensure_ascii=True,
            sort_keys=True,
        )
        return hashlib.sha256(payload.encode("utf-8")).hexdigest()

    @staticmethod
    def _normalize_idea(item: dict, index: int, platforms: list[str], content_type: str) -> dict:
        platform = str(item.get("platform") or platforms[min(index, len(platforms) - 1)]).strip().lower()
        return {
            "title": str(item.get("title") or f"Idea {index + 1}").strip(),
            "hook": str(item.get("hook") or "").strip(),
            "format": str(item.get("format") or content_type).strip(),
            "platform": platform,
            "reason": str(item.get("reason") or "").strip(),
            "keywords": [str(keyword).strip() for keyword in item.get("keywords", []) if str(keyword).strip()],
            "estimated_duration_seconds": int(item.get("estimated_duration_seconds") or 0),
            "source": "ai_generated",
            "status": "pending",
        }

    def generate_ideas(
        self,
        *,
        topic: str,
        platforms: list[str],
        content_type: str,
        language: str,
        quantity: int,
        force: bool = False,
        api_key: str | None = None,
    ) -> dict:
        today = datetime.now().date()
        fingerprint = self.build_fingerprint(
            topic=topic,
            platforms=platforms,
            content_type=content_type,
            language=language,
            quantity=quantity,
        )

        if not force:
            cached = self.repository.get_cached_ideas(topic, fingerprint, today)
            if cached:
                return {"ideas": cached[:quantity], "from_cache": True}

        prompt = (
            f"Topic: {topic}\n"
            f"Platforms: {', '.join(platforms)}\n"
            f"Content type: {content_type}\n"
            f"Language for operator notes: {language}\n"
            f"Generate exactly {quantity} structured ideas.\n"
            "Keep the ideas factual, cinematic, and optimized for dark history or geopolitics style content."
        )
        result = self.gemini.generate_text(
            feature="idea_generation",
            contents=prompt,
            api_key=api_key,
            model="gemini-2.5-flash",
            system_instruction=IDEAS_SYSTEM_PROMPT,
            temperature=0.8,
        )

        parsed = extract_json_block(result["text"])
        raw_ideas = parsed if isinstance(parsed, list) else parsed.get("ideas", [])
        normalized = [
            self._normalize_idea(item, index, platforms, content_type)
            for index, item in enumerate(raw_ideas)
            if isinstance(item, dict)
        ][:quantity]

        if not normalized:
            raise ValueError("O Gemini nao retornou ideias validas.")

        saved = self.repository.save_ideas(
            topic=topic,
            content_type=content_type,
            language=language,
            request_fingerprint=fingerprint,
            generated_on=today,
            ideas=normalized,
        )
        return {"ideas": saved[:quantity], "from_cache": False}


idea_service = IdeaService()
