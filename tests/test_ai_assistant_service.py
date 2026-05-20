import tempfile
import unittest
from pathlib import Path

from app.repositories.ai_usage_repository import AIUsageRepository
from app.repositories.idea_repository import IdeaRepository
from app.services.ai_assistant_service import AIAssistantService
from app.services.rag_service import RagService
from app.services.usage_service import UsageService


class FakeGeminiService:
    def generate_text(self, **kwargs):
        return {
            "text": "Strategic answer from Gemini.",
            "usage": {
                "id": 1,
                "feature": "assistant_chat",
                "provider": "gemini",
                "model": "gemini-2.5-flash",
                "input_tokens": 120,
                "output_tokens": 40,
                "estimated_cost_usd": 0.0,
            },
        }


class AIAssistantServiceTestCase(unittest.TestCase):
    def test_assistant_retrieves_context_and_routes_to_gemini(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            db_path = Path(tmpdir) / "assistant.db"
            idea_repository = IdeaRepository(db_path)
            idea_repository.save_ideas(
                topic="cold war",
                content_type="long_video",
                language="pt",
                request_fingerprint="fp",
                generated_on=__import__("datetime").date.today(),
                ideas=[
                    {
                        "title": "Blackbird mission",
                        "hook": "The mission almost failed before takeoff.",
                        "format": "long_video",
                        "platform": "youtube",
                        "reason": "Strong historical hook",
                        "keywords": ["sr-71", "blackbird"],
                        "estimated_duration_seconds": 900,
                    }
                ],
            )

            usage_repository = AIUsageRepository(db_path)
            rag = RagService()
            rag.repository.db_path = db_path
            usage = UsageService(repository=usage_repository)
            service = AIAssistantService(
                gemini=FakeGeminiService(),
                rag=rag,
                usage=usage,
                usage_repository=usage_repository,
            )

            result = service.ask(prompt="Give me a strategic idea about the blackbird.", task_type="strategy")

            self.assertEqual(result["provider_used"], "gemini")
            self.assertTrue(result["context"])
            self.assertIn("Strategic answer", result["answer"])


if __name__ == "__main__":
    unittest.main()
