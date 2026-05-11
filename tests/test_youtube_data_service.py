import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

from app.core.config import Settings
from app.repositories.youtube_repository import YouTubeRepository
from app.services.youtube_data_service import YouTubeDataService


class FakeResponse:
    def __init__(self, payload):
        self.payload = payload

    def json(self):
        return self.payload

    def raise_for_status(self):
        return None


class YouTubeDataServiceTestCase(unittest.TestCase):
    def test_search_uses_cache_on_second_call(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            settings = Settings(
                youtube_api_key="fake-key",
                database_url=f"sqlite:///{Path(tmpdir) / 'app.db'}",
            )
            repository = YouTubeRepository(Path(tmpdir) / "app.db")
            service = YouTubeDataService(repository=repository, settings=settings)

            def fake_get(url, params, timeout):
                if url.endswith("/search"):
                    return FakeResponse(
                        {
                            "items": [
                                {
                                    "id": {"videoId": "abc123"},
                                    "snippet": {"channelId": "chan1"},
                                }
                            ]
                        }
                    )
                if url.endswith("/videos"):
                    return FakeResponse(
                        {
                            "items": [
                                {
                                    "id": "abc123",
                                    "snippet": {
                                        "title": "Cold War Flight",
                                        "description": "Story",
                                        "channelId": "chan1",
                                        "channelTitle": "History Lab",
                                        "publishedAt": "2024-01-01T00:00:00Z",
                                        "thumbnails": {"high": {"url": "https://img/1.jpg"}},
                                    },
                                    "statistics": {
                                        "viewCount": "1000",
                                        "likeCount": "50",
                                        "commentCount": "10",
                                    },
                                    "contentDetails": {"duration": "PT10M5S"},
                                }
                            ]
                        }
                    )
                if url.endswith("/channels"):
                    return FakeResponse(
                        {
                            "items": [
                                {
                                    "id": "chan1",
                                    "snippet": {
                                        "title": "History Lab",
                                        "description": "Desc",
                                        "publishedAt": "2020-01-01T00:00:00Z",
                                        "thumbnails": {"high": {"url": "https://img/c.jpg"}},
                                    },
                                    "statistics": {
                                        "subscriberCount": "5000",
                                        "viewCount": "500000",
                                        "videoCount": "120",
                                    },
                                }
                            ]
                        }
                    )
                raise AssertionError(f"Unexpected URL: {url}")

            with patch("app.services.youtube_data_service.requests.get", side_effect=fake_get) as mocked_get:
                first = service.search(query="cold war", max_results=5, order="relevance")
                second = service.search(query="cold war", max_results=5, order="relevance")

            self.assertFalse(first["from_cache"])
            self.assertTrue(second["from_cache"])
            self.assertEqual(mocked_get.call_count, 3)
            self.assertEqual(first["items"][0]["youtube_video_id"], "abc123")


if __name__ == "__main__":
    unittest.main()
