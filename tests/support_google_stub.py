import sys
import types


def install_google_genai_stub() -> None:
    if "google.genai" in sys.modules:
        return

    google_module = sys.modules.get("google") or types.ModuleType("google")
    genai_module = types.ModuleType("google.genai")

    class _DummyClient:
        def __init__(self, *args, **kwargs) -> None:
            self.models = types.SimpleNamespace(generate_content=lambda *a, **k: None)

    class _DummyGenerateContentConfig:
        def __init__(self, *args, **kwargs) -> None:
            self.args = args
            self.kwargs = kwargs

    class _DummySpeechConfig(_DummyGenerateContentConfig):
        pass

    class _DummyVoiceConfig(_DummyGenerateContentConfig):
        pass

    class _DummyPrebuiltVoiceConfig(_DummyGenerateContentConfig):
        pass

    genai_module.Client = _DummyClient
    genai_module.types = types.SimpleNamespace(
        GenerateContentConfig=_DummyGenerateContentConfig,
        SpeechConfig=_DummySpeechConfig,
        VoiceConfig=_DummyVoiceConfig,
        PrebuiltVoiceConfig=_DummyPrebuiltVoiceConfig,
    )

    google_module.genai = genai_module
    sys.modules["google"] = google_module
    sys.modules["google.genai"] = genai_module


def install_pydantic_settings_stub() -> None:
    if "pydantic_settings" in sys.modules:
        return

    from pydantic import BaseModel

    pydantic_settings_module = types.ModuleType("pydantic_settings")

    class _DummyBaseSettings(BaseModel):
        pass

    def _dummy_settings_config_dict(**kwargs):
        return kwargs

    pydantic_settings_module.BaseSettings = _DummyBaseSettings
    pydantic_settings_module.SettingsConfigDict = _dummy_settings_config_dict
    sys.modules["pydantic_settings"] = pydantic_settings_module


def install_test_stubs() -> None:
    install_google_genai_stub()
    install_pydantic_settings_stub()
