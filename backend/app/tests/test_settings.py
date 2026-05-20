from app import config


def test_config_defaults_are_stable():
    assert config.APP_NAME == "radio-medical-ai"
    assert config.API_PREFIX == "/api/v1"
    assert config.OLLAMA_MODEL == "llama3.1"
    assert config.OLLAMA_TEMPERATURE == 0.2


def test_config_exposes_api_prefix():
    assert config.API_PREFIX.startswith("/api/")
