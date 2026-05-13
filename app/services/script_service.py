from __future__ import annotations

import json
import re

from newspaper import Article

from app.core.runtime import ENHANCE_SYSTEM_PROMPT, SCRIPTIFY_SYSTEM_PROMPT
from app.services.gemini_service import GeminiService, gemini_service


class ScriptService:
    def __init__(self, gemini: GeminiService | None = None) -> None:
        self.gemini = gemini or gemini_service

    def enhance_script(self, *, text: str, api_key: str | None = None) -> dict:
        result = self.gemini.generate_text(
            feature="enhance_script",
            contents=text,
            api_key=api_key,
            model="gemini-2.5-flash",
            system_instruction=ENHANCE_SYSTEM_PROMPT,
            temperature=0.4,
        )
        return {"enhanced_text": result["text"], "usage": result["usage"]}

    def generate_script_from_url(self, *, url: str, api_key: str | None = None) -> dict:
        article = Article(url)
        article.download()
        article.parse()
        raw_text = article.text

        if len(raw_text) < 200:
            raise ValueError("Nao foi possivel extrair conteudo da URL. Tente outra URL.")

        result = self.gemini.generate_text(
            feature="video_script",
            contents=raw_text,
            api_key=api_key,
            model="gemini-2.5-flash",
            system_instruction=SCRIPTIFY_SYSTEM_PROMPT,
            temperature=0.7,
        )
        full_response = result["text"]
        script_part = full_response
        image_raw = full_response
        image_prompts: list[dict] = []

        if "===IMAGE_PROMPTS===" in full_response:
            parts = full_response.split("===IMAGE_PROMPTS===", 1)
            script_part = parts[0].strip()
            image_raw = parts[1].strip()

        start = image_raw.find("[")
        end = image_raw.rfind("]") + 1
        if start != -1 and end > start:
            json_str = image_raw[start:end]
            json_str = re.sub(r",\s*]", "]", json_str)
            try:
                image_prompts = json.loads(json_str)
                if "===IMAGE_PROMPTS===" not in full_response:
                    script_part = full_response[: full_response.rfind("[")].strip()
            except json.JSONDecodeError:
                image_prompts = []

        parsed_prompts = []
        for item in image_prompts:
            if isinstance(item, dict) and "prompt" in item:
                parsed_prompts.append(item)
            elif isinstance(item, str):
                parsed_prompts.append({"timestamp": "00:00", "cue": "", "prompt": item})

        return {
            "script": script_part,
            "image_prompts": parsed_prompts,
            "source_chars": len(raw_text),
            "usage": result["usage"],
        }


script_service = ScriptService()
