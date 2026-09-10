from __future__ import annotations

import base64
import glob
import io
import json
import os
import time
import uuid
import wave

from app.core.config import get_settings
from app.core.pronunciation import apply_pronunciation, resolve_language_code
from app.core.runtime import STREAM_CHUNK_MAX_CHARS, STREAM_THROTTLE_SECONDS, chunk_text
from app.services.gemini_service import GeminiService, gemini_service
from app.storage.local_storage import ensure_storage_layout


class AudioService:
    def __init__(self, gemini: GeminiService | None = None) -> None:
        self.gemini = gemini or gemini_service
        self.settings = get_settings()

    @staticmethod
    def pcm_to_wav_bytes(audio_data: bytes) -> bytes:
        buffer = io.BytesIO()
        with wave.open(buffer, "wb") as wav_file:
            wav_file.setnchannels(1)
            wav_file.setsampwidth(2)
            wav_file.setframerate(24000)
            wav_file.writeframes(audio_data)
        buffer.seek(0)
        return buffer.read()

    def generate_tts_wav_bytes(
        self, *, text: str, voice: str, api_key: str | None = None, language: str = "pt"
    ) -> dict:
        result = self.gemini.generate_audio_pcm(
            feature="tts",
            text=apply_pronunciation(text, language=language),
            voice=voice,
            api_key=api_key,
            model=self.settings.gemini_tts_model,
            language_code=resolve_language_code(language),
        )
        return {"wav_bytes": self.pcm_to_wav_bytes(result["audio_data"]), "usage": result["usage"]}

    def generate_tts_to_path(
        self, *, text: str, voice: str, output_path: str, api_key: str | None = None, language: str = "pt"
    ) -> dict:
        result = self.generate_tts_wav_bytes(text=text, voice=voice, api_key=api_key, language=language)
        with open(output_path, "wb") as wav_file:
            wav_file.write(result["wav_bytes"])
        return result

    def stream_tts_events(
        self,
        *,
        text: str,
        voice: str,
        api_key: str | None = None,
        session_id: str | None = None,
        language: str = "pt",
    ):
        ensure_storage_layout()
        text = apply_pronunciation(text, language=language)
        language_code = resolve_language_code(language)
        session_id = session_id or str(uuid.uuid4())
        session_dir = os.path.join(self.settings.tmp_sessions_dir, session_id)
        os.makedirs(session_dir, exist_ok=True)

        yield f"data: {json.dumps({'type': 'session', 'session_id': session_id})}\n\n"

        chunks_meta = os.path.join(session_dir, "chunks.json")
        if os.path.exists(chunks_meta):
            with open(chunks_meta, "r", encoding="utf-8") as file_obj:
                chunks = json.load(file_obj)
        else:
            chunks = chunk_text(text, max_chars=STREAM_CHUNK_MAX_CHARS)
            with open(chunks_meta, "w", encoding="utf-8") as file_obj:
                json.dump(chunks, file_obj)

        chunks_processed = 0
        for index, chunk in enumerate(chunks):
            chunk_path = os.path.join(session_dir, f"chunk_{index:04d}.pcm")
            if os.path.exists(chunk_path) and os.path.getsize(chunk_path) > 0:
                yield f"data: {json.dumps({'type': 'skipped', 'chunk': index + 1, 'total': len(chunks)})}\n\n"
                chunks_processed += 1
                continue

            progress_event = json.dumps(
                {
                    "type": "progress",
                    "current": index + 1,
                    "total": len(chunks),
                    "preview": chunk[:80],
                }
            )
            yield f"data: {progress_event}\n\n"

            try:
                result = self.gemini.generate_audio_pcm(
                    feature="tts_stream",
                    text=chunk,
                    voice=voice,
                    api_key=api_key,
                    model=self.settings.gemini_tts_model,
                    language_code=language_code,
                )
                with open(chunk_path, "wb") as file_obj:
                    file_obj.write(result["audio_data"])
                chunks_processed += 1

                has_pending_chunks = any(
                    not (
                        os.path.exists(os.path.join(session_dir, f"chunk_{future_index:04d}.pcm"))
                        and os.path.getsize(os.path.join(session_dir, f"chunk_{future_index:04d}.pcm")) > 0
                    )
                    for future_index in range(index + 1, len(chunks))
                )
                if has_pending_chunks:
                    waiting_event = json.dumps(
                        {
                            "type": "waiting",
                            "seconds": STREAM_THROTTLE_SECONDS,
                            "chunk": index + 1,
                            "total": len(chunks),
                        }
                    )
                    yield f"data: {waiting_event}\n\n"
                    time.sleep(STREAM_THROTTLE_SECONDS)
            except Exception as exc:
                error_event = json.dumps(
                    {
                        "type": "error",
                        "chunk": index + 1,
                        "message": str(exc),
                    }
                )
                yield f"data: {error_event}\n\n"

        pcm_files = sorted(glob.glob(os.path.join(session_dir, "chunk_*.pcm")))
        if not pcm_files:
            yield f"data: {json.dumps({'type': 'error', 'chunk': 0, 'message': 'Nenhum chunk processado com sucesso.'})}\n\n"
            return

        combined_parts = []
        for path in pcm_files:
            with open(path, "rb") as file_obj:
                combined_parts.append(file_obj.read())
        combined_pcm = b"".join(combined_parts)
        wav_bytes = self.pcm_to_wav_bytes(combined_pcm)
        done_event = json.dumps(
            {
                "type": "done",
                "audio_b64": base64.b64encode(wav_bytes).decode("utf-8"),
                "chunks_processed": chunks_processed,
            }
        )
        yield f"data: {done_event}\n\n"


audio_service = AudioService()
