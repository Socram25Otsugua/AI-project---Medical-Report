from app.settings import Settings, settings


def test_settings_defaults_are_stable():
    cfg = Settings()
    assert cfg.app_name == "radio-medical-ai"
    assert cfg.api_prefix == "/api/v1"
    assert cfg.ollama_model == "llama3.1"
    assert cfg.ollama_temperature == 0.2


def test_settings_allows_runtime_overrides():
    cfg = Settings(api_prefix="/api/test", ollama_model="my-model")
    assert cfg.api_prefix == "/api/test"
    assert cfg.ollama_model == "my-model"


def test_singleton_settings_object_exposes_api_prefix():
    assert settings.api_prefix.startswith("/api/")
