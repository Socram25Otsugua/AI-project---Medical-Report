from pathlib import Path
from types import SimpleNamespace

from app.services import rag


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


def test_load_or_build_vectorstore_indexes_kb_documents(monkeypatch, tmp_path):
    kb_dir = tmp_path / "knowledge_base"
    kb_dir.mkdir()
    (kb_dir / "one.md").write_text("# A", encoding="utf-8")
    (kb_dir / "two.txt").write_text("B", encoding="utf-8")
    (kb_dir / "three.bin").write_bytes(b"\x00\x01")
    persist_dir = tmp_path / "db"

    monkeypatch.setattr(rag, "_kb_dir", lambda: kb_dir)
    monkeypatch.setattr(rag, "Chroma", _FakeChroma)
    monkeypatch.setattr(rag, "OllamaEmbeddings", lambda model, base_url: {"model": model, "base_url": base_url})
    monkeypatch.setattr(rag.settings, "rag_persist_dir", str(persist_dir))
    monkeypatch.setattr(rag.settings, "rag_collection", "test-kb")

    deps = rag.load_or_build_vectorstore()

    assert isinstance(deps.vectorstore, _FakeChroma)
    assert Path(deps.vectorstore.persist_directory) == persist_dir
    assert len(deps.vectorstore.saved_docs) == 2
    assert deps.vectorstore.persist_called is True
    assert {doc.metadata["source"] for doc in deps.vectorstore.saved_docs} == {"one.md", "two.txt"}


def test_rag_search_delegates_to_vectorstore():
    vectorstore = _FakeChroma("c", {}, "p")
    out = rag.rag_search(vectorstore, query="abc", k=7)
    assert out == [{"query": "abc", "k": 7}]
