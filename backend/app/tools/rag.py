from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

from langchain_community.vectorstores import Chroma
from langchain_core.documents import Document
from langchain_ollama import OllamaEmbeddings

from app.config import OLLAMA_BASE_URL, OLLAMA_MODEL, RAG_COLLECTION, RAG_PERSIST_DIR


@dataclass(frozen=True)
class RagDeps:
    vectorstore: Chroma


def _rag_data_dir() -> Path:
    return Path(__file__).resolve().parents[1] / "rag_data"


def load_or_build_vectorstore() -> RagDeps:
    persist_dir = Path(RAG_PERSIST_DIR)
    persist_dir.mkdir(parents=True, exist_ok=True)

    embeddings = OllamaEmbeddings(model=OLLAMA_MODEL, base_url=OLLAMA_BASE_URL)
    vs = Chroma(
        collection_name=RAG_COLLECTION,
        embedding_function=embeddings,
        persist_directory=str(persist_dir),
    )

    if vs._collection.count() == 0:
        docs: list[Document] = []
        source_dir = _rag_data_dir()
        if source_dir.exists():
            for p in sorted(source_dir.glob("**/*")):
                if not p.is_file():
                    continue
                if p.suffix.lower() not in {".md", ".txt"}:
                    continue
                text = p.read_text(encoding="utf-8", errors="ignore")
                if text.strip():
                    docs.append(
                        Document(
                            page_content=text,
                            metadata={"source": f"{source_dir.name}/{p.relative_to(source_dir)}"},
                        )
                    )
        if docs:
            vs.add_documents(docs)
            vs.persist()

    return RagDeps(vectorstore=vs)


def rag_search(vectorstore: Chroma, query: str, k: int = 4) -> list[Document]:
    return vectorstore.similarity_search(query, k=k)
