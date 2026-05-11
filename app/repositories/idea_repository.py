from __future__ import annotations

import json
from datetime import date
from pathlib import Path

from app.models.tables import Idea
from app.repositories.utils import SQLAlchemyRepository


class IdeaRepository(SQLAlchemyRepository):
    def __init__(self, db_path: str | Path | None = None) -> None:
        super().__init__(db_path)

    def get_cached_ideas(self, topic: str, request_fingerprint: str, target_date: date) -> list[dict]:
        with self._session() as session:
            rows = (
                session.query(Idea)
                .filter(
                    Idea.topic == topic,
                    Idea.request_fingerprint == request_fingerprint,
                    Idea.generated_on == target_date.isoformat(),
                )
                .order_by(Idea.id.asc())
                .all()
            )

        ideas = []
        for row in rows:
            idea = {
                "title": row.title,
                "hook": row.hook,
                "format": row.format,
                "platform": row.platform,
                "topic": row.topic,
                "keywords": row.keywords,
                "source": row.source,
                "status": row.status,
                "reason": row.reason,
                "estimated_duration_seconds": row.estimated_duration_seconds,
                "content_type": row.content_type,
                "language": row.language,
            }
            idea["keywords"] = json.loads(idea.get("keywords") or "[]")
            ideas.append(idea)
        return ideas

    def save_ideas(
        self,
        *,
        topic: str,
        content_type: str,
        language: str,
        request_fingerprint: str,
        generated_on: date,
        ideas: list[dict],
    ) -> list[dict]:
        with self._session() as session:
            (
                session.query(Idea)
                .filter(
                    Idea.topic == topic,
                    Idea.request_fingerprint == request_fingerprint,
                    Idea.generated_on == generated_on.isoformat(),
                )
                .delete(synchronize_session=False)
            )
            for idea in ideas:
                session.add(
                    Idea(
                        title=idea.get("title", ""),
                        hook=idea.get("hook", ""),
                        format=idea.get("format", ""),
                        platform=idea.get("platform", ""),
                        topic=topic,
                        keywords=json.dumps(idea.get("keywords", []), ensure_ascii=True),
                        source=idea.get("source", "ai_generated"),
                        status=idea.get("status", "pending"),
                        reason=idea.get("reason", ""),
                        estimated_duration_seconds=int(idea.get("estimated_duration_seconds", 0) or 0),
                        content_type=content_type,
                        language=language,
                        request_fingerprint=request_fingerprint,
                        generated_on=generated_on.isoformat(),
                    )
                )

        return self.get_cached_ideas(topic, request_fingerprint, generated_on)
