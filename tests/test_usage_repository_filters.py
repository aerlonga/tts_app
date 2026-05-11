import tempfile
import unittest
from pathlib import Path

from app.repositories.ai_usage_repository import AIUsageLogRecord, AIUsageRepository


class UsageRepositoryFiltersTestCase(unittest.TestCase):
    def test_summary_supports_date_filters_and_projection(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            repository = AIUsageRepository(Path(tmpdir) / "usage.db")
            repository.log_usage(
                AIUsageLogRecord(
                    feature="video_script_generation",
                    provider="gemini",
                    model="gemini-1.5-flash",
                    input_tokens=100,
                    output_tokens=50,
                    estimated_cost_usd=1.5,
                )
            )

            summary = repository.get_summary(start_date="2000-01-01", end_date="2100-01-01")

            self.assertEqual(summary["total_calls"], 1)
            self.assertEqual(summary["start_date"], "2000-01-01")
            self.assertGreaterEqual(summary["projected_monthly_cost_usd"], 1.5)


if __name__ == "__main__":
    unittest.main()
