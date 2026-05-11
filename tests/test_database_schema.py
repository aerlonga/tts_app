import tempfile
import unittest
from pathlib import Path

from sqlalchemy import inspect

from app.repositories.db import get_engine, initialize_database, normalize_database_url


class DatabaseSchemaTestCase(unittest.TestCase):
    def test_expected_tables_exist(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            db_path = Path(tmpdir) / "schema.db"
            initialize_database(db_path)
            engine = get_engine(normalize_database_url(db_path))

            names = set(inspect(engine).get_table_names())
            expected = {
                "videos",
                "ideas",
                "channels",
                "competitor_videos",
                "metrics_snapshots",
                "content_references",
                "experiments",
                "ai_usage_logs",
            }
            self.assertTrue(expected.issubset(names))


if __name__ == "__main__":
    unittest.main()
