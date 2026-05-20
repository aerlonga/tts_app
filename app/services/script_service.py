from __future__ import annotations

import json
import re

from newspaper import Article

from app.core.runtime import get_system_prompt
from app.services.gemini_service import GeminiService, gemini_service


class ScriptService:
    def __init__(self, gemini: GeminiService | None = None) -> None:
        self.gemini = gemini or gemini_service

    def _parse_script_response(self, full_response: str) -> tuple[str, list[dict]]:
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

        return script_part, parsed_prompts

    def _enhance_instruction(self, language: str, *, generate_image_prompts: bool) -> str:
        base_instruction = get_system_prompt("enhance", language)
        if not generate_image_prompts:
            return base_instruction

        image_prompt_rules = """

IMAGE PROMPTS RULES (append AFTER the annotated script):
- Generate exactly 26 image prompts, one approximately every 34 seconds of narration.
- Each prompt MUST be a JSON object with three fields:
  - "timestamp": the [MM:SS] timestamp from the script where this image should appear
  - "cue": a short editorial label
  - "prompt": the full image generation prompt in English
- Style: dramatic black and white photorealistic photography, 16:9 aspect ratio, cinematic lighting.
- Each prompt should describe a specific scene from the script at that timestamp.
- Image prompt timestamps must not go beyond [15:00].
- Format as a JSON array at the very end, after the marker: ===IMAGE_PROMPTS===
"""
        if language == "pt":
            image_prompt_rules = """

REGRAS DOS PROMPTS DE IMAGEM (adicionar APOS o roteiro anotado):
- Gere exatamente 26 prompts de imagem, um aproximadamente a cada 34 segundos de narracao.
- Cada prompt DEVE ser um objeto JSON com tres campos:
  - "timestamp": o timestamp [MM:SS] do roteiro onde esta imagem deve aparecer
  - "cue": um rotulo editorial curto
  - "prompt": o prompt completo de geracao de imagem em ingles
- Estilo: fotografia fotorrealistica dramatica em preto e branco, proporcao 16:9, iluminacao cinematografica.
- Cada prompt deve descrever uma cena especifica do roteiro naquele timestamp.
- Os timestamps dos prompts de imagem nao devem ultrapassar [15:00].
- Formate como um array JSON ao final, apos o marcador: ===IMAGE_PROMPTS===
"""
        return f"{base_instruction}{image_prompt_rules}"

    def enhance_script(
        self,
        *,
        text: str,
        api_key: str | None = None,
        language: str = "pt",
        generate_image_prompts: bool = False,
    ) -> dict:
        result = self.gemini.generate_text(
            feature="enhance_script",
            contents=text,
            api_key=api_key,
            system_instruction=self._enhance_instruction(language, generate_image_prompts=generate_image_prompts),
            temperature=0.4,
        )
        if generate_image_prompts:
            enhanced_text, image_prompts = self._parse_script_response(result["text"])
        else:
            enhanced_text = result["text"]
            image_prompts = []
        return {"enhanced_text": enhanced_text, "image_prompts": image_prompts, "usage": result["usage"]}

    def generate_script_from_url(self, *, url: str, api_key: str | None = None, language: str = "pt") -> dict:
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
            system_instruction=get_system_prompt("scriptify", language),
            temperature=0.7,
        )
        script_part, parsed_prompts = self._parse_script_response(result["text"])

        return {
            "script": script_part,
            "image_prompts": parsed_prompts,
            "source_chars": len(raw_text),
            "usage": result["usage"],
        }


script_service = ScriptService()
