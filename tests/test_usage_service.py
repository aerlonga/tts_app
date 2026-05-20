import tempfile
import unittest
from pathlib import Path

from app.repositories.ai_usage_repository import AIUsageLogRecord, AIUsageRepository
from app.services.usage_service import UsageService


class UsageServiceTestCase(unittest.TestCase):
    def test_summary_and_grouping(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            repository = AIUsageRepository(Path(tmpdir) / "usage.db")
            service = UsageService(repository=repository)
            repository.log_usage(
                AIUsageLogRecord(
                    feature="assistant_chat",
                    provider="gemini",
                    model="gemini-2.5-flash",
                    input_tokens=100,
                    output_tokens=50,
                    estimated_cost_usd=0.12,
                )
            )
            repository.log_usage(
                AIUsageLogRecord(
                    feature="assistant_chat",
                    provider="ollama",
                    model="llama3.1:8b",
                    input_tokens=20,
                    output_tokens=10,
                    estimated_cost_usd=0.0,
                )
            )

            summary = service.get_summary()
            grouped = service.get_by_feature()

            self.assertEqual(summary["total_calls"], 2)
            self.assertEqual(summary["total_input_tokens"], 120)
            self.assertEqual(len(grouped), 2)


if __name__ == "__main__":
    unittest.main()
