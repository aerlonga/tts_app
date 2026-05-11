from __future__ import annotations

from typing import Callable

import requests

from app.core.config import get_settings
from app.repositories.ai_usage_repository import AIUsageLogRecord, AIUsageRepository
from app.services.gemini_service import GeminiService, gemini_service
from app.services.rag_service import RagService, rag_service
from app.services.usage_service import UsageService, usage_service


ASSISTANT_SYSTEM_PROMPT = """You are a backend-local AI assistant for a video automation workspace.
Use the supplied project context first. Be practical, concise, and do not invent facts.
If the context is insufficient, say what is missing.
"""


class AIAssistantService:
    def __init__(
        self,
        *,
        gemini: GeminiService | None = None,
        rag: RagService | None = None,
        usage: UsageService | None = None,
        usage_repository: AIUsageRepository | None = None,
        ollama_generate: Callable[[str, str], str] | None = None,
    ) -> None:
        self.settings = get_settings()
        self.gemini = gemini or gemini_service
        self.rag = rag or rag_service
        self.usage = usage or usage_service
        self.usage_repository = usage_repository or AIUsageRepository()
        self.ollama_generate = ollama_generate or self._ollama_generate

    def _build_context_block(self, prompt: str, max_context_docs: int) -> tuple[str, list[dict]]:
        context_items = self.rag.search(query=prompt, limit=max_context_docs)
        usage_summary = self.usage.get_summary()
        context_lines = [
            f"- {item['source_type']} | {item['title']} | score={item['score']}: {item['snippet']}"
            for item in context_items
        ]
        summary_line = (
            "Usage summary: "
            f"calls={usage_summary['total_calls']}, "
            f"input_tokens={usage_summary['total_input_tokens']}, "
            f"output_tokens={usage_summary['total_output_tokens']}, "
            f"estimated_cost_usd={usage_summary['total_estimated_cost_usd']}"
        )
        block = "\n".join([summary_line, *context_lines]) if context_lines else summary_line
        return block, context_items

    def _pick_provider(self, *, task_type: str, preferred_provider: str | None) -> tuple[str, str]:
        preferred = (preferred_provider or "").strip().lower()
        if preferred in {"gemini", "ollama"}:
            return preferred, "explicit provider preference"

        if task_type.strip().lower() in {"quick", "summarize", "classification", "simple"} and self.settings.ollama_base_url:
            return "ollama", "simple task routed to local model"

        return "gemini", "strategic or default task routed to Gemini"

    def _ollama_generate(self, prompt: str, model: str) -> str:
        response = requests.post(
            f"{self.settings.ollama_base_url}/api/generate",
            json={"model": model, "prompt": prompt, "stream": False},
            timeout=120,
        )
        response.raise_for_status()
        payload = response.json()
        return str(payload.get("response", "")).strip()

    def _log_ollama_usage(self, *, prompt: str, answer: str, model: str) -> dict:
        input_tokens = max(len(prompt.split()), 0)
        output_tokens = max(len(answer.split()), 0)
        estimated_cost = round(
            ((input_tokens + output_tokens) / 1_000_000.0) * max(self.settings.ollama_estimated_cost_per_1m, 0.0),
            6,
        )
        return self.usage_repository.log_usage(
            AIUsageLogRecord(
                feature="assistant_chat",
                provider="ollama",
                model=model,
                input_tokens=input_tokens,
                output_tokens=output_tokens,
                estimated_cost_usd=estimated_cost,
            )
        )

    def ask(
        self,
        *,
        prompt: str,
        task_type: str = "strategy",
        preferred_provider: str | None = None,
        api_key: str | None = None,
        max_context_docs: int = 5,
    ) -> dict:
        context_block, context_items = self._build_context_block(prompt, max_context_docs)
        provider, routing_reason = self._pick_provider(task_type=task_type, preferred_provider=preferred_provider)
        full_prompt = f"PROJECT CONTEXT:\n{context_block}\n\nUSER REQUEST:\n{prompt}"

        if provider == "ollama":
            answer = self.ollama_generate(full_prompt, self.settings.ollama_model)
            usage = self._log_ollama_usage(prompt=full_prompt, answer=answer, model=self.settings.ollama_model)
            return {
                "answer": answer,
                "provider_used": "ollama",
                "model_used": self.settings.ollama_model,
                "routing_reason": routing_reason,
                "context": context_items,
                "usage": usage,
            }

        result = self.gemini.generate_text(
            feature="assistant_chat",
            contents=full_prompt,
            api_key=api_key,
            model=self.settings.gemini_model,
            system_instruction=ASSISTANT_SYSTEM_PROMPT,
            temperature=0.4,
        )
        return {
            "answer": result["text"],
            "provider_used": "gemini",
            "model_used": self.settings.gemini_model,
            "routing_reason": routing_reason,
            "context": context_items,
            "usage": result["usage"],
        }


ai_assistant_service = AIAssistantService()
