"""Helpers to load and reuse the legacy Flask module during migration."""

from importlib.util import module_from_spec, spec_from_file_location
from pathlib import Path
from types import ModuleType


def _load_legacy_module() -> ModuleType:
    legacy_path = Path(__file__).resolve().parent.parent / "app.py"
    spec = spec_from_file_location("legacy_flask_app", legacy_path)
    if spec is None or spec.loader is None:
        raise ImportError(f"Unable to load legacy Flask module from {legacy_path}")

    module = module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


legacy_app = _load_legacy_module()

