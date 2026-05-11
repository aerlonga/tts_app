from __future__ import annotations
from pathlib import Path

from app.core.config import Settings, get_settings


def get_storage_paths(settings: Settings | None = None) -> list[Path]:
    settings = settings or get_settings()
    return [
        Path(settings.storage_root),
        Path(settings.storage_root) / "videos",
        Path(settings.storage_root) / "shorts",
        Path(settings.storage_root) / "audio",
        Path(settings.storage_root) / "assets",
        Path(settings.tmp_sessions_dir),
        Path(settings.tmp_jobs_dir),
        Path(settings.broll_dir),
    ]


def ensure_storage_layout(settings: Settings | None = None) -> None:
    roots = get_storage_paths(settings)
    for root in roots:
        root.mkdir(parents=True, exist_ok=True)


def is_path_writable(path: Path) -> bool:
    try:
        path.mkdir(parents=True, exist_ok=True)
        probe = path / ".write_test"
        probe.write_text("ok", encoding="utf-8")
        probe.unlink(missing_ok=True)
        return True
    except OSError:
        return False


def get_storage_report(settings: Settings | None = None) -> list[dict]:
    ensure_storage_layout(settings)
    report = []
    for path in get_storage_paths(settings):
        resolved = path.resolve()
        report.append(
            {
                "path": str(resolved),
                "exists": resolved.exists(),
                "is_dir": resolved.is_dir(),
                "writable": is_path_writable(resolved),
            }
        )
    return report
