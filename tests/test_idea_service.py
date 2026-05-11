import json
import tempfile
import unittest
from pathlib import Path

from app.repositories.idea_repository import IdeaRepository
from app.services.idea_service import IdeaService


class FakeGeminiService:
    def __init__(self) -> None:
        self.calls = 0

    def generate_text(self, **kwargs):
        self.calls += 1
        payload = {
            "ideas": [
                {
                    "title": "SR-71 mission nobody expected",
                    "hook": "The runway problem started before takeoff.",
                    "format": "long_video",
                    "platform": "youtube",
                    "reason": "Strong cold war tension and visual storytelling.",
                    "keywords": ["sr-71", "cold war"],
                    "estimated_duration_seconds": 900,
                }
            ]
        }
        return {"text": json.dumps(payload), "usage": {"id": 1}}


class IdeaServiceTestCase(unittest.TestCase):
    def test_second_call_uses_cache_when_force_is_false(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            repository = IdeaRepository(Path(tmpdir) / "ideas.db")
            gemini = FakeGeminiService()
            service = IdeaService(gemini=gemini, repository=repository)

            first = service.generate_ideas(
                topic="military aviation history",
                platforms=["youtube"],
                content_type="long_video",
                language="pt",
                quantity=1,
                force=False,
                api_key="fake",
            )
            second = service.generate_ideas(
                topic="military aviation history",
                platforms=["youtube"],
                content_type="long_video",
                language="pt",
                quantity=1,
                force=False,
                api_key="fake",
            )

            self.assertFalse(first["from_cache"])
            self.assertTrue(second["from_cache"])
            self.assertEqual(gemini.calls, 1)
            self.assertEqual(second["ideas"][0]["title"], "SR-71 mission nobody expected")


if __name__ == "__main__":
    unittest.main()
