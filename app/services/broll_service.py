from __future__ import annotations

import os

import requests

from app import search_broll
from app.core.config import get_settings
from app.storage.local_storage import ensure_storage_layout


class BrollService:
    def __init__(self) -> None:
        self.settings = get_settings()

    def search(self, *, keywords: list[str], collection: str = "prelinger") -> list[dict]:
        return search_broll(keywords, collection)

    def download(self, *, url: str) -> dict:
        if not url.startswith("https://archive.org/"):
            raise ValueError("URL invalida. Deve ser do archive.org.")

        ensure_storage_layout()
        filename = url.split("/")[-1]
        dest = os.path.join(self.settings.broll_dir, filename)

        with requests.get(url, stream=True, timeout=60) as response:
            response.raise_for_status()
            with open(dest, "wb") as file_obj:
                for chunk in response.iter_content(chunk_size=8192):
                    file_obj.write(chunk)

        return {"local_path": dest, "filename": filename}


broll_service = BrollService()
