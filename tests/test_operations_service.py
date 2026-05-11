import tempfile
import unittest
from pathlib import Path

from app.core.config import Settings
from app.services.operations_service import OperationsService


class OperationsServiceTestCase(unittest.TestCase):
    def test_health_details_reports_local_backend_status(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            settings = Settings(
                database_url=f"sqlite:///{Path(tmpdir) / 'app.db'}",
                storage_root=tmpdir,
                broll_dir=str(Path(tmpdir) / "broll"),
                tmp_sessions_dir=str(Path(tmpdir) / "sessions"),
                tmp_jobs_dir=str(Path(tmpdir) / "jobs"),
            )
            service = OperationsService(settings=settings)

            result = service.get_health_details()

            self.assertEqual(result["status"], "ok")
            self.assertTrue(result["database_reachable"])
            self.assertTrue(result["storage"])


if __name__ == "__main__":
    unittest.main()
