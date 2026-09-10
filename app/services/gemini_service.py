from __future__ import annotations

from typing import Any

from google import genai
from google.genai import types

from app.core.config import get_settings
from app.repositories.ai_usage_repository import AIUsageLogRecord, AIUsageRepository


class GeminiService:
    def __init__(self, usage_repository: AIUsageRepository | None = None) -> None:
        self.settings = get_settings()
        self.usage_repository = usage_repository or AIUsageRepository()

    def _resolve_api_key(self, api_key: str | None) -> str:
        resolved = (api_key or self.settings.gemini_api_key or "").strip()
        if not resolved:
            raise ValueError("API Key do Gemini e obrigatoria.")
        return resolved

    def _build_client(self, api_key: str | None):
        return genai.Client(api_key=self._resolve_api_key(api_key))

    @staticmethod
    def _extract_usage(response: Any) -> tuple[int, int]:
        usage = getattr(response, "usage_metadata", None)
        if usage is None:
            return 0, 0

        input_tokens = 0
        output_tokens = 0
        for attr in ("prompt_token_count", "input_token_count", "candidates_token_count"):
            value = getattr(usage, attr, None)
            if isinstance(value, int):
                if "prompt" in attr or "input" in attr:
                    input_tokens = value
                else:
                    output_tokens = value

        input_tokens = input_tokens or int(getattr(usage, "total_token_count", 0) or 0)
        if output_tokens == 0 and input_tokens:
            output_tokens = max(int(getattr(usage, "total_token_count", 0) or 0) - input_tokens, 0)

        return input_tokens, output_tokens

    @staticmethod
    def _estimate_cost_usd(
        input_tokens: int,
        output_tokens: int,
        input_rate_per_1m: float,
        output_rate_per_1m: float,
    ) -> float:
        if input_tokens <= 0 and output_tokens <= 0:
            return 0.0
        input_cost = (max(input_tokens, 0) / 1_000_000.0) * max(input_rate_per_1m, 0.0)
        output_cost = (max(output_tokens, 0) / 1_000_000.0) * max(output_rate_per_1m, 0.0)
        return round(input_cost + output_cost, 6)

    def _rates_for_model(self, model: str) -> tuple[float, float]:
        if "tts" in (model or "").lower():
            return (
                self.settings.gemini_tts_input_cost_per_1m,
                self.settings.gemini_tts_output_cost_per_1m,
            )
        return (
            self.settings.gemini_text_input_cost_per_1m,
            self.settings.gemini_text_output_cost_per_1m,
        )

    def _log_usage(self, *, feature: str, model: str, response: Any, video_id: int | None = None) -> dict:
        input_tokens, output_tokens = self._extract_usage(response)
        input_rate, output_rate = self._rates_for_model(model)
        record = AIUsageLogRecord(
            feature=feature,
            provider="gemini",
            model=model,
            input_tokens=input_tokens,
            output_tokens=output_tokens,
            estimated_cost_usd=self._estimate_cost_usd(input_tokens, output_tokens, input_rate, output_rate),
            video_id=video_id,
        )
        return self.usage_repository.log_usage(record)

    def generate_text(
        self,
        *,
        feature: str,
        contents: str,
        api_key: str | None = None,
        model: str | None = None,
        system_instruction: str | None = None,
        temperature: float = 0.7,
    ) -> dict:
        model = model or self.settings.gemini_model
        client = self._build_client(api_key)
        response = client.models.generate_content(
            model=model,
            contents=contents,
            config=types.GenerateContentConfig(
                system_instruction=system_instruction,
                temperature=temperature,
            ),
        )
        usage = self._log_usage(feature=feature, model=model, response=response)
        return {
            "text": (response.text or "").strip(),
            "usage": usage,
            "raw_response": response,
        }

    def generate_audio_pcm(
        self,
        *,
        feature: str,
        text: str,
        voice: str,
        api_key: str | None = None,
        model: str | None = None,
        language_code: str = "pt-BR",
    ) -> dict:
        model = model or self.settings.gemini_tts_model
        client = self._build_client(api_key)
        response = client.models.generate_content(
            model=model,
            contents=text,
            config=types.GenerateContentConfig(
                response_modalities=["AUDIO"],
                speech_config=types.SpeechConfig(
                    language_code=language_code,
                    voice_config=types.VoiceConfig(
                        prebuilt_voice_config=types.PrebuiltVoiceConfig(voice_name=voice)
                    ),
                ),
            ),
        )
        usage = self._log_usage(feature=feature, model=model, response=response)
        audio_data = response.candidates[0].content.parts[0].inline_data.data
        return {
            "audio_data": audio_data,
            "usage": usage,
            "raw_response": response,
        }


gemini_service = GeminiService()
