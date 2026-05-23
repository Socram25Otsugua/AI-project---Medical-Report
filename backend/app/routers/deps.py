from __future__ import annotations

from app.tools.rag import RagDeps, load_or_build_vectorstore

_rag_deps: RagDeps | None = None


def get_rag() -> RagDeps:
    global _rag_deps
    if _rag_deps is None:
        _rag_deps = load_or_build_vectorstore()
    return _rag_deps
