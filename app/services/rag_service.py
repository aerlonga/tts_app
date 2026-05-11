from __future__ import annotations

import math
import re
from collections import Counter
from typing import Any

import requests

from app.core.config import get_settings
from app.repositories.knowledge_repository import KnowledgeRepository


TOKEN_RE = re.compile(r"[a-zA-Z0-9_]+")
EMBEDDING_DIMENSIONS = 768


class RagService:
    def __init__(self, repository: KnowledgeRepository | None = None) -> None:
        self.repository = repository or KnowledgeRepository()
        self.settings = get_settings()

    @staticmethod
    def _tokenize(text: str) -> list[str]:
        return [token.lower() for token in TOKEN_RE.findall(text or "")]

    @classmethod
    def _local_fallback_embedding(cls, text: str) -> list[float]:
        vector = [0.0] * EMBEDDING_DIMENSIONS
        counts = Counter(cls._tokenize(text))
        for token, count in counts.items():
            vector[hash(token) % EMBEDDING_DIMENSIONS] += float(count)

        norm = math.sqrt(sum(value * value for value in vector))
        if norm:
            vector = [value / norm for value in vector]
        return vector

    @staticmethod
    def _normalize_dimensions(embedding: Any) -> list[float]:
        values = [float(value) for value in list(embedding or [])]
        if len(values) == EMBEDDING_DIMENSIONS:
            return values
        if len(values) > EMBEDDING_DIMENSIONS:
            return values[:EMBEDDING_DIMENSIONS]
        return values + [0.0] * (EMBEDDING_DIMENSIONS - len(values))

    def _generate_embedding(self, text: str) -> list[float]:
        if self.settings.gemini_api_key:
            try:
                return self._generate_gemini_embedding(text)
            except Exception:
                pass

        if self.settings.ollama_base_url:
            try:
                return self._generate_ollama_embedding(text)
            except requests.RequestException:
                pass

        return self._local_fallback_embedding(text)

    def _generate_ollama_embedding(self, text: str) -> list[float]:
        response = requests.post(
            f"{self.settings.ollama_base_url}/api/embeddings",
            json={"model": self.settings.ollama_embedding_model, "prompt": text},
            timeout=60,
        )
        response.raise_for_status()
        payload = response.json()
        embedding = payload.get("embedding") or (payload.get("embeddings") or [[]])[0]
        return self._normalize_dimensions(embedding)

    def _generate_gemini_embedding(self, text: str) -> list[float]:
        from google import genai

        client = genai.Client(api_key=self.settings.gemini_api_key)
        response = client.models.embed_content(
            model=self.settings.gemini_embedding_model,
            contents=text,
        )
        return self._normalize_dimensions(response.embeddings[0].values)


    def rebuild_index(self) -> list[dict]:
        documents = self.repository.get_documents()
        for document in documents:
            if document.get("embedding"):
                continue
            embedding = self._generate_embedding(f"{document['title']} {document['content']}")
            self.repository.save_embedding(document["doc_id"], embedding)
            document["embedding"] = embedding
        return documents

    def search(self, *, query: str, limit: int = 5) -> list[dict]:
        self.rebuild_index()
        query_embedding = self._generate_embedding(query)
        return self.repository.search_by_embedding(query_embedding, limit=limit)


rag_service = RagService()
