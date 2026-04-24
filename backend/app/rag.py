from __future__ import annotations

import os
from dataclasses import dataclass
from pathlib import Path

from langchain_community.vectorstores import Chroma
from langchain_core.documents import Document
from langchain_ollama import OllamaEmbeddings

from app.settings import settings


@dataclass(frozen=True)
class RagDeps:
    vectorstore: Chroma


def _kb_dir() -> Path:
    return Path(__file__).resolve().parents[1] / "knowledge_base"


def load_or_build_vectorstore() -> RagDeps:
    persist_dir = Path(settings.rag_persist_dir)
    persist_dir.mkdir(parents=True, exist_ok=True)

    embeddings = OllamaEmbeddings(model=settings.ollama_model, base_url=settings.ollama_base_url)
    vs = Chroma(
        collection_name=settings.rag_collection,
        embedding_function=embeddings,
        persist_directory=str(persist_dir),
    )

    # Idempotent: if empty, index local knowledge-base docs.
    if vs._collection.count() == 0:
        docs: list[Document] = []
        for p in sorted(_kb_dir().glob("**/*")):
            if not p.is_file():
                continue
            if p.suffix.lower() not in {".md", ".txt"}:
                continue
            text = p.read_text(encoding="utf-8", errors="ignore")
            if text.strip():
                docs.append(Document(page_content=text, metadata={"source": str(p.relative_to(_kb_dir()))}))
        if docs:
            vs.add_documents(docs)
            vs.persist()

    return RagDeps(vectorstore=vs)


def rag_search(vectorstore: Chroma, query: str, k: int = 4) -> list[Document]:
    return vectorstore.similarity_search(query, k=k)

