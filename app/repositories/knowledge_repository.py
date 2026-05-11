from __future__ import annotations

import json
from pathlib import Path

from sqlalchemy import text

from app.models.tables import Channel, CompetitorVideo, ContentReference, Idea, Video
from app.repositories.utils import SQLAlchemyRepository, serialize_value


class KnowledgeRepository(SQLAlchemyRepository):
    def __init__(self, db_path: str | Path | None = None) -> None:
        super().__init__(db_path)

    def get_documents(self, limit_per_source: int = 50) -> list[dict]:
        documents: list[dict] = []
        with self._session() as session:
            ideas = session.query(Idea).order_by(Idea.created_at.desc()).limit(limit_per_source).all()
            for row in ideas:
                keywords = json.loads(row.keywords or "[]")
                text = " ".join(
                    filter(
                        None,
                        [
                            row.title,
                            row.hook,
                            row.reason,
                            row.topic,
                            " ".join(keywords),
                        ],
                    )
                )
                documents.append(
                    {
                        "doc_id": f"idea:{row.id}",
                        "source_type": "idea",
                        "title": row.title or "Idea",
                        "content": text,
                        "metadata": {
                            "platform": row.platform,
                            "status": row.status,
                            "created_at": serialize_value(row.created_at),
                        },
                        "embedding": row.embedding,
                    }
                )

            videos = session.query(Video).order_by(Video.created_at.desc()).limit(limit_per_source).all()
            for row in videos:
                text = " ".join(filter(None, [row.title, row.description, row.topic, row.platform, row.content_type]))
                documents.append(
                    {
                        "doc_id": f"video:{row.id}",
                        "source_type": "video",
                        "title": row.title or "Video",
                        "content": text,
                        "metadata": {
                            "youtube_video_id": row.youtube_video_id,
                            "created_at": serialize_value(row.created_at),
                        },
                        "embedding": row.embedding,
                    }
                )

            channels = session.query(Channel).order_by(Channel.collected_at.desc()).limit(limit_per_source).all()
            for row in channels:
                text = " ".join(
                    filter(
                        None,
                        [
                            row.title,
                            row.description,
                            f"subscribers {row.subscriber_count}",
                            f"views {row.view_count}",
                        ],
                    )
                )
                documents.append(
                    {
                        "doc_id": f"channel:{row.id}",
                        "source_type": "channel",
                        "title": row.title or "Channel",
                        "content": text,
                        "metadata": {
                            "youtube_channel_id": row.youtube_channel_id,
                            "collected_at": serialize_value(row.collected_at),
                        },
                        "embedding": row.embedding,
                    }
                )

            competitors = session.query(CompetitorVideo).order_by(CompetitorVideo.collected_at.desc()).limit(limit_per_source).all()
            for row in competitors:
                text = " ".join(
                    filter(
                        None,
                        [
                            row.title,
                            row.description,
                            row.channel_title,
                            f"views {row.views}",
                            f"likes {row.likes}",
                            f"views per day {row.views_per_day}",
                            f"like rate {row.like_rate_percent}",
                        ],
                    )
                )
                documents.append(
                    {
                        "doc_id": f"competitor:{row.id}",
                        "source_type": "competitor_video",
                        "title": row.title or "Competitor Video",
                        "content": text,
                        "metadata": {
                            "youtube_video_id": row.youtube_video_id,
                            "collected_at": serialize_value(row.collected_at),
                        },
                        "embedding": row.embedding,
                    }
                )

            references = session.query(ContentReference).order_by(ContentReference.collected_at.desc()).limit(limit_per_source).all()
            for row in references:
                metadata_json = row.metadata_json or "{}"
                documents.append(
                    {
                        "doc_id": f"reference:{row.id}",
                        "source_type": row.reference_type,
                        "title": row.title or row.reference_type,
                        "content": " ".join(filter(None, [row.title, row.url, metadata_json])),
                        "metadata": {
                            "url": row.url,
                            "collected_at": serialize_value(row.collected_at),
                        },
                        "embedding": row.embedding,
                    }
                )

        return documents

    def save_embedding(self, doc_id: str, embedding: list[float]) -> None:
        model_class, row_id = self._resolve_document(doc_id)
        if model_class is None:
            return
        with self._session() as session:
            row = session.get(model_class, row_id)
            if row is not None:
                row.embedding = embedding

    def search_by_embedding(self, query_embedding: list[float], limit: int = 5) -> list[dict]:
        if self.database_url.startswith("postgresql"):
            return self._search_pgvector(query_embedding, limit)
        return self._search_in_python(query_embedding, limit)

    @staticmethod
    def _resolve_document(doc_id: str):
        source, _, raw_id = doc_id.partition(":")
        if not raw_id.isdigit():
            return None, None
        mapping = {
            "idea": Idea,
            "video": Video,
            "channel": Channel,
            "competitor": CompetitorVideo,
            "reference": ContentReference,
        }
        return mapping.get(source), int(raw_id)

    def _search_pgvector(self, query_embedding: list[float], limit: int) -> list[dict]:
        embedding_text = "[" + ",".join(str(value) for value in query_embedding) + "]"
        sql = text(
            """
            SELECT *
            FROM (
                SELECT 'idea:' || id AS doc_id, 'idea' AS source_type,
                       COALESCE(title, 'Idea') AS title,
                       LEFT(CONCAT_WS(' ', title, hook, reason, topic, keywords), 240) AS snippet,
                       json_build_object('platform', platform, 'status', status, 'created_at', created_at) AS metadata,
                       1 - (embedding <=> CAST(:embedding AS vector)) AS score
                FROM ideas
                WHERE embedding IS NOT NULL
                UNION ALL
                SELECT 'video:' || id AS doc_id, 'video' AS source_type,
                       COALESCE(title, 'Video') AS title,
                       LEFT(CONCAT_WS(' ', title, description, topic, platform, content_type), 240) AS snippet,
                       json_build_object('youtube_video_id', youtube_video_id, 'created_at', created_at) AS metadata,
                       1 - (embedding <=> CAST(:embedding AS vector)) AS score
                FROM videos
                WHERE embedding IS NOT NULL
                UNION ALL
                SELECT 'channel:' || id AS doc_id, 'channel' AS source_type,
                       COALESCE(title, 'Channel') AS title,
                       LEFT(CONCAT_WS(' ', title, description, subscriber_count, view_count), 240) AS snippet,
                       json_build_object('youtube_channel_id', youtube_channel_id, 'collected_at', collected_at) AS metadata,
                       1 - (embedding <=> CAST(:embedding AS vector)) AS score
                FROM channels
                WHERE embedding IS NOT NULL
                UNION ALL
                SELECT 'competitor:' || id AS doc_id, 'competitor_video' AS source_type,
                       COALESCE(title, 'Competitor Video') AS title,
                       LEFT(CONCAT_WS(' ', title, description, channel_title, views, likes, views_per_day, like_rate_percent), 240) AS snippet,
                       json_build_object('youtube_video_id', youtube_video_id, 'collected_at', collected_at) AS metadata,
                       1 - (embedding <=> CAST(:embedding AS vector)) AS score
                FROM competitor_videos
                WHERE embedding IS NOT NULL
                UNION ALL
                SELECT 'reference:' || id AS doc_id, reference_type AS source_type,
                       COALESCE(title, reference_type) AS title,
                       LEFT(CONCAT_WS(' ', title, url, metadata_json), 240) AS snippet,
                       json_build_object('url', url, 'collected_at', collected_at) AS metadata,
                       1 - (embedding <=> CAST(:embedding AS vector)) AS score
                FROM content_references
                WHERE embedding IS NOT NULL
            ) ranked
            WHERE score > 0
            ORDER BY score DESC
            LIMIT :limit
            """
        )
        with self._session() as session:
            rows = session.execute(sql, {"embedding": embedding_text, "limit": limit}).mappings().all()
            return [dict(row) for row in rows]

    def _search_in_python(self, query_embedding: list[float], limit: int) -> list[dict]:
        def cosine(left: list[float], right: list[float]) -> float:
            return round(sum(a * b for a, b in zip(left, right)), 6)

        scored = []
        for document in self.get_documents():
            embedding = document.get("embedding") or []
            score = cosine(query_embedding, embedding)
            if score <= 0:
                continue
            scored.append(
                {
                    "doc_id": document["doc_id"],
                    "source_type": document["source_type"],
                    "title": document["title"],
                    "score": score,
                    "snippet": document["content"][:240],
                    "metadata": document.get("metadata", {}),
                }
            )
        scored.sort(key=lambda item: item["score"], reverse=True)
        return scored[:limit]
