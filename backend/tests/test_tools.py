from types import SimpleNamespace

from app import tools


def test_mcp_tools_delegate_to_mcp_client(monkeypatch):
    calls = []

    def _fake_call(name, args):
        calls.append((name, args))
        return {"ok": True, "name": name}

    monkeypatch.setattr(tools, "call_mcp_tool_sync", _fake_call)

    out_a = tools.mcp_checklist_missing_sections.invoke({"report_text": "report"})
    out_b = tools.mcp_extract_vitals.invoke({"report_text": "report"})
    out_c = tools.mcp_triage_priority.invoke({"vitals": {"spo2_percent": 92}})

    assert out_a["name"] == "checklist_missing_sections"
    assert out_b["name"] == "extract_vitals"
    assert out_c["name"] == "triage_priority"
    assert calls[0] == ("checklist_missing_sections", {"report_text": "report"})


def test_make_rag_lookup_tool_formats_results(monkeypatch):
    fake_docs = [
        SimpleNamespace(metadata={"source": "a.md"}, page_content="A" * 2500),
        SimpleNamespace(metadata={}, page_content="B"),
    ]

    def _fake_rag_search(vectorstore, query, k):
        assert vectorstore == "vectorstore"
        assert query == "abc"
        assert k == 4
        return fake_docs

    monkeypatch.setattr(tools, "rag_search", _fake_rag_search)
    rag = SimpleNamespace(vectorstore="vectorstore")
    rag_lookup = tools.make_rag_lookup_tool(rag)

    out = rag_lookup.invoke({"query": "abc"})

    assert len(out["results"]) == 2
    assert out["results"][0]["source"] == "a.md"
    assert len(out["results"][0]["text"]) == 2000
    assert out["results"][1]["source"] == "unknown"
