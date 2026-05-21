from __future__ import annotations

import os
from pathlib import Path


def _load_dotenv() -> None:
    env_path = Path(__file__).resolve().parents[1] / ".env"
    if not env_path.exists():
        return
    for raw_line in env_path.read_text(encoding="utf-8").splitlines():
        line = raw_line.strip()
        if not line or line.startswith("#") or "=" not in line:
            continue
        key, value = line.split("=", 1)
        key = key.strip()
        value = value.strip().strip('"').strip("'")
        os.environ.setdefault(key, value)


def _get_str(key: str, default: str) -> str:
    return os.getenv(key, default)


def _get_float(key: str, default: float) -> float:
    raw = os.getenv(key)
    if raw is None:
        return default
    try:
        return float(raw)
    except ValueError:
        return default


_load_dotenv()

APP_NAME = _get_str("APP_NAME", "radio-medical-ai")
API_PREFIX = _get_str("API_PREFIX", "/api/v1")

OLLAMA_BASE_URL = _get_str("OLLAMA_BASE_URL", "http://localhost:11434")
OLLAMA_MODEL = _get_str("OLLAMA_MODEL", "llama3.1")
OLLAMA_CHAT_MODEL = _get_str("OLLAMA_CHAT_MODEL", "llama3.1")
OLLAMA_TEMPERATURE = _get_float("OLLAMA_TEMPERATURE", 0.2)
OLLAMA_CHAT_TEMPERATURE = _get_float("OLLAMA_CHAT_TEMPERATURE", 0.1)

RAG_PERSIST_DIR = _get_str("RAG_PERSIST_DIR", ".chroma")
RAG_COLLECTION = _get_str("RAG_COLLECTION", "medical_training_kb")
