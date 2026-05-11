import tempfile
import unittest
from pathlib import Path

from app.repositories.ai_usage_repository import AIUsageLogRecord, AIUsageRepository


class AIUsageRepositoryTestCase(unittest.TestCase):
    def test_log_usage_persists_row(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            repository = AIUsageRepository(Path(tmpdir) / "usage.db")
            row = repository.log_usage(
                AIUsageLogRecord(
                    feature="idea_generation",
                    provider="gemini",
                    model="gemini-2.5-flash",
                    input_tokens=123,
                    output_tokens=45,
                    estimated_cost_usd=0.0,
                )
            )

            self.assertIsNotNone(row["id"])
            self.assertEqual(row["feature"], "idea_generation")
            self.assertEqual(row["input_tokens"], 123)


if __name__ == "__main__":
    unittest.main()
