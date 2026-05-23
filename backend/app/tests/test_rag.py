from pathlib import Path
from types import SimpleNamespace

from app.config import RAG_COLLECTION, RAG_PERSIST_DIR
from app.tools.rag import load_or_build_vectorstore, rag_search
from app.tools import rag as rag_module


class _FakeCollection:
    def __init__(self, count_value):
        self._count_value = count_value

    def count(self):
        return self._count_value


class _FakeChroma:
    def __init__(self, collection_name, embedding_function, persist_directory):
        self.collection_name = collection_name
        self.embedding_function = embedding_function
        self.persist_directory = persist_directory
        self._collection = _FakeCollection(0)
        self.saved_docs = []
        self.persist_called = False

    def add_documents(self, docs):
        self.saved_docs.extend(docs)

    def persist(self):
        self.persist_called = True

    def similarity_search(self, query, k=4):
        return [{"query": query, "k": k}]


def test_load_or_build_vectorstore_indexes_rag_documents(monkeypatch, tmp_path):
    rag_data_dir = tmp_path / "rag_data"
    rag_data_dir.mkdir()
    (rag_data_dir / "one.md").write_text("# A", encoding="utf-8")
    (rag_data_dir / "two.txt").write_text("B", encoding="utf-8")
    (rag_data_dir / "three.bin").write_bytes(b"\x00\x01")
    persist_dir = tmp_path / "db"

    monkeypatch.setattr(rag_module, "_rag_data_dir", lambda: rag_data_dir)
    monkeypatch.setattr(rag_module, "Chroma", _FakeChroma)
    monkeypatch.setattr(rag_module, "OllamaEmbeddings", lambda model, base_url: {"model": model, "base_url": base_url})
    monkeypatch.setattr(rag_module, "RAG_PERSIST_DIR", str(persist_dir))
    monkeypatch.setattr(rag_module, "RAG_COLLECTION", "test-kb")

    deps = rag_module.load_or_build_vectorstore()

    assert isinstance(deps.vectorstore, _FakeChroma)
    assert Path(deps.vectorstore.persist_directory) == persist_dir
    assert len(deps.vectorstore.saved_docs) == 2
    assert deps.vectorstore.persist_called is True
    assert {doc.metadata["source"] for doc in deps.vectorstore.saved_docs} == {
        "rag_data/one.md",
        "rag_data/two.txt",
    }


def test_rag_search_delegates_to_vectorstore():
    vectorstore = _FakeChroma(RAG_COLLECTION, {}, RAG_PERSIST_DIR)
    out = rag_module.rag_search(vectorstore, query="abc", k=7)
    assert out == [{"query": "abc", "k": 7}]
