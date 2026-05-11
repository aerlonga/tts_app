from __future__ import annotations

from contextlib import contextmanager
from functools import lru_cache
from pathlib import Path
from typing import Iterator

from sqlalchemy import create_engine, text
from sqlalchemy.engine import Connection, Engine
from sqlalchemy.orm import Session, sessionmaker

from app.core.config import get_settings
from app.models.base import Base
from app.models import tables  # noqa: F401 - import registers ORM models.


def normalize_database_url(database_url_or_path: str | Path | None = None) -> str:
    if database_url_or_path is None:
        return get_settings().database_url

    raw_value = str(database_url_or_path)
    if "://" in raw_value:
        return raw_value

    path = Path(raw_value).expanduser().resolve()
    path.parent.mkdir(parents=True, exist_ok=True)
    return f"sqlite:///{path}"


@lru_cache(maxsize=16)
def get_engine(database_url: str | None = None) -> Engine:
    resolved_url = normalize_database_url(database_url)
    connect_args = {"check_same_thread": False} if resolved_url.startswith("sqlite") else {}
    return create_engine(resolved_url, echo=False, future=True, connect_args=connect_args)


@lru_cache(maxsize=16)
def get_session_factory(database_url: str | None = None) -> sessionmaker[Session]:
    return sessionmaker(bind=get_engine(database_url), autoflush=False, expire_on_commit=False, future=True)


def _enable_pgvector(engine: Engine) -> None:
    if engine.dialect.name != "postgresql":
        return
    with engine.begin() as connection:
        connection.execute(text("CREATE EXTENSION IF NOT EXISTS vector"))


def initialize_database(database_url_or_path: str | Path | None = None) -> None:
    database_url = normalize_database_url(database_url_or_path)
    engine = get_engine(database_url)
    _enable_pgvector(engine)
    Base.metadata.create_all(bind=engine)


@contextmanager
def session_scope(database_url_or_path: str | Path | None = None) -> Iterator[Session]:
    database_url = normalize_database_url(database_url_or_path)
    session = get_session_factory(database_url)()
    try:
        yield session
        session.commit()
    except Exception:
        session.rollback()
        raise
    finally:
        session.close()


def get_db() -> Iterator[Session]:
    with session_scope() as session:
        yield session


def get_connection(database_url_or_path: str | Path | None = None) -> Connection:
    database_url = normalize_database_url(database_url_or_path)
    return get_engine(database_url).connect()
