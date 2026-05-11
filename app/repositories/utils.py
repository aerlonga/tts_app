from __future__ import annotations

from datetime import date, datetime
from pathlib import Path
from typing import Any

from sqlalchemy import inspect

from app.repositories.db import initialize_database, normalize_database_url, session_scope


class SQLAlchemyRepository:
    def __init__(self, database_url_or_path: str | Path | None = None) -> None:
        self.database_url = normalize_database_url(database_url_or_path)
        self._initialized = False
        if database_url_or_path is not None:
            self._ensure_database()

    @property
    def db_path(self) -> str:
        return self.database_url

    @db_path.setter
    def db_path(self, database_url_or_path: str | Path | None) -> None:
        self.database_url = normalize_database_url(database_url_or_path)
        self._initialized = False
        if database_url_or_path is not None:
            self._ensure_database()

    def _ensure_database(self) -> None:
        if not self._initialized:
            initialize_database(self.database_url)
            self._initialized = True

    def _session(self):
        self._ensure_database()
        return session_scope(self.database_url)


def parse_datetime(value: Any) -> datetime | None:
    if value is None or isinstance(value, datetime):
        return value
    if isinstance(value, date):
        return datetime.combine(value, datetime.min.time())
    if isinstance(value, str) and value.strip():
        normalized = value.strip().replace("Z", "+00:00")
        try:
            return datetime.fromisoformat(normalized)
        except ValueError:
            return None
    return None


def parse_date(value: Any) -> date | None:
    if value is None or isinstance(value, date):
        return value
    if isinstance(value, datetime):
        return value.date()
    if isinstance(value, str) and value.strip():
        try:
            return date.fromisoformat(value.strip()[:10])
        except ValueError:
            return None
    return None


def serialize_value(value: Any) -> Any:
    if isinstance(value, datetime):
        return value.isoformat()
    if isinstance(value, date):
        return value.isoformat()
    return value


def model_to_dict(model: Any, *, exclude: set[str] | None = None) -> dict:
    excluded = exclude or set()
    mapper = inspect(model).mapper
    return {
        column.key: serialize_value(getattr(model, column.key))
        for column in mapper.column_attrs
        if column.key not in excluded
    }
