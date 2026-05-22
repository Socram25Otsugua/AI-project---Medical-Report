from __future__ import annotations

from typing import Any, List

from langchain_ollama import ChatOllama

from app.config import OLLAMA_BASE_URL, OLLAMA_MODEL, OLLAMA_TEMPERATURE


def build_chat_model() -> ChatOllama:
    return ChatOllama(
        model=OLLAMA_MODEL,
        base_url=OLLAMA_BASE_URL,
        temperature=OLLAMA_TEMPERATURE,
    )


def format_rag_context(docs: List[Any]) -> str:
    if not docs:
        return ""
    parts = []
    for d in docs:
        src = d.metadata.get("source", "unknown")
        parts.append(f"[source: {src}]\n{d.page_content}".strip())
    return "\n\n---\n\n".join(parts)
