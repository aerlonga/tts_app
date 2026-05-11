import tempfile
import unittest
from pathlib import Path

from app.core.config import Settings
from app.repositories.video_repository import VideoRepository
from app.services.youtube_analytics_service import YouTubeAnalyticsService


class YouTubeAnalyticsServiceTestCase(unittest.TestCase):
    def test_missing_oauth_configuration_raises_clear_error(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            settings = Settings(database_url=f"sqlite:///{Path(tmpdir) / 'app.db'}")
            repository = VideoRepository(Path(tmpdir) / "app.db")
            service = YouTubeAnalyticsService(video_repository=repository, settings=settings)

            with self.assertRaises(ValueError) as context:
                service.get_channel_summary()

            self.assertIn("YOUTUBE_CLIENT_ID", str(context.exception))


if __name__ == "__main__":
    unittest.main()
