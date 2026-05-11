from __future__ import annotations

from typing import Any

from sqlalchemy import JSON
from sqlalchemy.types import TypeDecorator

try:
    from pgvector.sqlalchemy import Vector
except ImportError:  # pragma: no cover - exercised only before dependencies are installed.
    Vector = None  # type: ignore[assignment]


class EmbeddingVector(TypeDecorator):
    """Use pgvector on PostgreSQL and JSON elsewhere for local tests."""

    impl = JSON
    cache_ok = True

    def __init__(self, dimensions: int = 768, *args: Any, **kwargs: Any) -> None:
        super().__init__(*args, **kwargs)
        self.dimensions = dimensions

    def load_dialect_impl(self, dialect):
        if dialect.name == "postgresql" and Vector is not None:
            return dialect.type_descriptor(Vector(self.dimensions))
        return dialect.type_descriptor(JSON())
