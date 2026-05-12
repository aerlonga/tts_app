from __future__ import annotations

import json
import os
import shutil
import threading
import time
import uuid

from fastapi import UploadFile

from app import JOBS, MAX_AGE_SECS, natural_asset_sort_key
from app.core.config import get_settings
from app.services.audio_service import AudioService, audio_service
from app.services.video_assembler import (
    assemble_video,
    is_ffmpeg_available,
    uses_template_manifest,
    validate_template_manifest,
)
from app.storage.local_storage import ensure_storage_layout


class VideoService:
    def __init__(self, audio: AudioService | None = None) -> None:
        self.audio = audio or audio_service
        self.settings = get_settings()
        self._cleanup_started = False

    def start_cleanup_worker(self) -> None:
        if self._cleanup_started:
            return
        self._cleanup_started = True
        threading.Thread(target=self._cleanup_loop, daemon=True).start()

    def _cleanup_loop(self) -> None:
        while True:
            now = time.time()
            for base_dir in (self.settings.tmp_jobs_dir, self.settings.tmp_sessions_dir):
                if not os.path.exists(base_dir):
                    continue
                try:
                    for entry in os.scandir(base_dir):
                        if not entry.is_dir():
                            continue
                        age = now - entry.stat().st_mtime
                        if age > MAX_AGE_SECS:
                            shutil.rmtree(entry.path, ignore_errors=True)
                            JOBS.pop(entry.name, None)
                except Exception:
                    continue
            time.sleep(30 * 60)

    def _save_upload_file(self, upload: UploadFile, destination: str) -> None:
        upload.file.seek(0)
        with open(destination, "wb") as file_obj:
            shutil.copyfileobj(upload.file, file_obj)

    def _normalize_manifest(self, manifest_str: str | None) -> list[dict]:
        try:
            manifest = json.loads(manifest_str or "[]")
            return manifest if isinstance(manifest, list) else []
        except Exception:
            return []

    def _save_assets(self, *, job_dir: str, uploads: list[UploadFile], manifest: list[dict]) -> list[dict]:
        assets: list[dict] = []
        if manifest and all(item.get("type") == "upload" for item in manifest):
            manifest = [
                item
                for _, item in sorted(
                    enumerate(manifest),
                    key=lambda pair: natural_asset_sort_key(pair[1].get("filename", ""), pair[0]),
                )
            ]

        if manifest:
            uploaded_files = {file.filename: file for file in uploads if file.filename}
            for item in manifest:
                if item.get("type") == "upload":
                    filename = item.get("filename")
                    if filename in uploaded_files:
                        ext = os.path.splitext(filename)[1].lower() or ".jpg"
                        path = os.path.join(job_dir, f"asset_{len(assets):04d}{ext}")
                        self._save_upload_file(uploaded_files[filename], path)
                        assets.append({**item, "path": path})
                elif item.get("type") == "server":
                    server_path = item.get("path")
                    if server_path and server_path.startswith(self.settings.broll_dir) and os.path.exists(server_path):
                        ext = os.path.splitext(server_path)[1].lower() or ".mp4"
                        path = os.path.join(job_dir, f"asset_{len(assets):04d}{ext}")
                        shutil.copy2(server_path, path)
                        asset = dict(item)
                        asset["source_path"] = server_path
                        asset["path"] = path
                        assets.append(asset)
        else:
            ordered_files = [
                file
                for _, file in sorted(
                    enumerate(uploads),
                    key=lambda pair: natural_asset_sort_key(pair[1].filename or "", pair[0]),
                )
            ]
            for index, upload in enumerate(ordered_files):
                filename = upload.filename or f"asset_{index}"
                ext = os.path.splitext(filename)[1].lower() or ".jpg"
                path = os.path.join(job_dir, f"asset_{len(assets):04d}{ext}")
                self._save_upload_file(upload, path)
                assets.append({"path": path, "filename": filename, "type": "upload"})

        return assets

    def _register_job(self, *, output_path: str, video_format: str) -> str:
        job_id = uuid.uuid4().hex
        JOBS[job_id] = {
            "status": "processing",
            "progress": 0.0,
            "output_path": output_path,
            "format": video_format,
            "error": None,
            "created_at": time.time(),
        }
        return job_id

    def create_assembly_job(
        self,
        *,
        audio_upload: UploadFile,
        asset_uploads: list[UploadFile],
        manifest_str: str | None,
        video_format: str = "long",
    ) -> str:
        ensure_storage_layout()
        if not is_ffmpeg_available():
            raise RuntimeError("FFmpeg nao esta instalado no servidor. Instale FFmpeg para usar esta funcionalidade.")

        job_id = uuid.uuid4().hex
        job_dir = os.path.join(self.settings.tmp_jobs_dir, job_id)
        os.makedirs(job_dir, exist_ok=True)

        audio_path = os.path.join(job_dir, f"audio_{job_id}.wav")
        self._save_upload_file(audio_upload, audio_path)
        manifest = self._normalize_manifest(manifest_str)
        assets = self._save_assets(
            job_dir=job_dir,
            uploads=asset_uploads,
            manifest=manifest,
        )
        if not assets:
            raise ValueError("Nenhum asset valido foi encontrado para montar o video.")
        if uses_template_manifest(assets):
            validate_template_manifest(assets)

        output_path = os.path.join(job_dir, f"video_{job_id}.mp4")
        JOBS[job_id] = {
            "status": "processing",
            "progress": 0.0,
            "output_path": output_path,
            "format": video_format,
            "error": None,
            "created_at": time.time(),
        }

        def run_job() -> None:
            try:
                success = assemble_video(
                    audio_path,
                    assets,
                    output_path,
                    job_id=job_id,
                    video_format=video_format,
                    jobs=JOBS,
                )
                if success and os.path.exists(output_path):
                    JOBS[job_id]["status"] = "done"
                    JOBS[job_id]["progress"] = 1.0
                else:
                    JOBS[job_id]["status"] = "error"
                    JOBS[job_id]["error"] = "FFmpeg falhou ao montar o video."
            except Exception as exc:
                JOBS[job_id]["status"] = "error"
                JOBS[job_id]["error"] = str(exc)

        threading.Thread(target=run_job, daemon=True).start()
        return job_id

    def create_generated_video_job(
        self,
        *,
        script: str,
        voice: str,
        api_key: str | None,
        asset_uploads: list[UploadFile],
        manifest_str: str | None,
        video_format: str = "long",
    ) -> str:
        ensure_storage_layout()
        if not is_ffmpeg_available():
            raise RuntimeError("FFmpeg nao esta instalado no servidor. Instale FFmpeg para usar esta funcionalidade.")

        job_id = uuid.uuid4().hex
        job_dir = os.path.join(self.settings.tmp_jobs_dir, job_id)
        os.makedirs(job_dir, exist_ok=True)
        manifest = self._normalize_manifest(manifest_str)
        assets = self._save_assets(
            job_dir=job_dir,
            uploads=asset_uploads,
            manifest=manifest,
        )
        if not assets:
            raise ValueError("Pelo menos 1 asset e obrigatorio.")
        if uses_template_manifest(assets):
            validate_template_manifest(assets)

        audio_path = os.path.join(job_dir, f"audio_{job_id}.wav")
        output_path = os.path.join(job_dir, f"video_{job_id}.mp4")
        JOBS[job_id] = {
            "status": "processing",
            "progress": 0.0,
            "output_path": output_path,
            "format": video_format,
            "error": None,
            "created_at": time.time(),
        }

        def run_job() -> None:
            try:
                self.audio.generate_tts_to_path(text=script, voice=voice, output_path=audio_path, api_key=api_key)
                success = assemble_video(
                    audio_path,
                    assets,
                    output_path,
                    job_id=job_id,
                    video_format=video_format,
                    jobs=JOBS,
                )
                if success and os.path.exists(output_path):
                    JOBS[job_id]["status"] = "done"
                    JOBS[job_id]["progress"] = 1.0
                else:
                    JOBS[job_id]["status"] = "error"
                    JOBS[job_id]["error"] = "FFmpeg falhou ao montar o video."
            except Exception as exc:
                JOBS[job_id]["status"] = "error"
                JOBS[job_id]["error"] = str(exc)

        threading.Thread(target=run_job, daemon=True).start()
        return job_id

    def get_job_status(self, job_id: str) -> dict | None:
        job = JOBS.get(job_id)
        if not job:
            return None
        result = {
            "status": job["status"],
            "progress": round(job["progress"], 3),
        }
        if job["status"] == "done":
            result["download_url"] = f"/media/assemble/download/{job_id}"
        elif job["status"] == "error":
            result["error"] = job["error"]
        return result

    def get_download_path(self, job_id: str) -> tuple[str, str] | None:
        job = JOBS.get(job_id)
        if not job or job["status"] != "done":
            return None
        path = job["output_path"]
        if not os.path.exists(path):
            return None
        filename = "short_final.mp4" if job.get("format") == "short" else "video_final.mp4"
        return path, filename


video_service = VideoService()
