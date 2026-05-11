"""FastAPI package that coexists with the legacy Flask module."""

import sys
from types import ModuleType

from app.legacy import legacy_app


_LEGACY_EXPORTS = {
    "ARCHIVE_SEARCH",
    "ENHANCE_SYSTEM_PROMPT",
    "FFMPEG_AVAILABLE",
    "JOBS",
    "MAX_AGE_SECS",
    "PART_NAME_RE",
    "SAFE_COLLECTIONS",
    "SCRIPTIFY_SYSTEM_PROMPT",
    "SHORTS_SYSTEM_PROMPT",
    "STREAM_CHUNK_MAX_CHARS",
    "STREAM_THROTTLE_SECONDS",
    "TMP_JOBS",
    "TMP_SESSIONS",
    "app",
    "assemble_video",
    "check_ffmpeg",
    "chunk_text",
    "cleanup_worker",
    "extract_json_block",
    "get_audio_duration",
    "get_video_encoder",
    "natural_asset_sort_key",
    "normalize_short_item",
    "search_broll",
}

for _name in _LEGACY_EXPORTS:
    if hasattr(legacy_app, _name):
        globals()[_name] = getattr(legacy_app, _name)


__all__ = sorted(_LEGACY_EXPORTS)


class _CompatibilityModule(ModuleType):
    def __getattr__(self, name: str):
        if hasattr(legacy_app, name):
            return getattr(legacy_app, name)
        raise AttributeError(name)

    def __setattr__(self, name: str, value):
        super().__setattr__(name, value)
        if hasattr(legacy_app, name):
            setattr(legacy_app, name, value)


sys.modules[__name__].__class__ = _CompatibilityModule
