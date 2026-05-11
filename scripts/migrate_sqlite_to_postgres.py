from __future__ import annotations

import sqlite3
from pathlib import Path

from app.models.tables import (
    AIUsageLog,
    Channel,
    CompetitorVideo,
    ContentReference,
    Experiment,
    Idea,
    MetricsSnapshot,
    Video,
)
from app.repositories.db import initialize_database, session_scope
from app.repositories.utils import parse_date, parse_datetime


SQLITE_SOURCE = Path("storage/app.db")

TABLES = [
    ("videos", Video, {"published_at": parse_datetime, "created_at": parse_datetime}),
    ("ideas", Idea, {"created_at": parse_datetime}),
    ("channels", Channel, {"published_at": parse_datetime, "collected_at": parse_datetime}),
    ("competitor_videos", CompetitorVideo, {"published_at": parse_datetime, "collected_at": parse_datetime}),
    ("content_references", ContentReference, {"collected_at": parse_datetime}),
    ("experiments", Experiment, {"created_at": parse_datetime}),
    ("ai_usage_logs", AIUsageLog, {"created_at": parse_datetime}),
    ("metrics_snapshots", MetricsSnapshot, {"snapshot_date": parse_date}),
]


def _table_exists(connection: sqlite3.Connection, table_name: str) -> bool:
    row = connection.execute(
        "SELECT name FROM sqlite_master WHERE type = 'table' AND name = ?",
        (table_name,),
    ).fetchone()
    return row is not None


def migrate(sqlite_path: Path = SQLITE_SOURCE) -> None:
    if not sqlite_path.exists():
        raise FileNotFoundError(f"SQLite source not found: {sqlite_path}")

    initialize_database()
    sqlite_conn = sqlite3.connect(sqlite_path)
    sqlite_conn.row_factory = sqlite3.Row

    try:
        with session_scope() as session:
            for table_name, model_class, converters in TABLES:
                if not _table_exists(sqlite_conn, table_name):
                    continue
                for row in sqlite_conn.execute(f"SELECT * FROM {table_name}"):
                    payload = dict(row)
                    for field, converter in converters.items():
                        if field in payload:
                            payload[field] = converter(payload[field])
                    session.merge(model_class(**payload))
    finally:
        sqlite_conn.close()


if __name__ == "__main__":
    migrate()
    print("Migração SQLite -> PostgreSQL concluída.")
