import importlib
from types import SimpleNamespace

from app.mcp.medical_guidelines_mcp import MedicalGuidelinesMCP
from app.mcp.scenario_context_mcp import detect_scenario, scenario_context_mcp
from app.mcp.session_memory_mcp import session_memory_mcp


def test_detect_scenario_trauma():
    out = detect_scenario("Crew member fell from ladder and has chest injury")
    assert out == "trauma"


def test_scenario_context_contains_expected_fields():
    out = scenario_context_mcp.get_scenario("Patient with chest pain and shortness of breath")
    assert out["success"] is True
    assert "scenario" in out
    assert "detected_type" in out["scenario"]
    assert "on_board_resources" in out["scenario"]


def test_medical_guidelines_mcp_context_string(monkeypatch):
    medical_guidelines_module = importlib.import_module("app.mcp.medical_guidelines_mcp")
    fake_doc = SimpleNamespace(page_content="ABCDE guideline chunk", metadata={"source": "kb.txt"})
    monkeypatch.setattr(medical_guidelines_module, "load_or_build_vectorstore", lambda: SimpleNamespace(vectorstore="v"))
    monkeypatch.setattr(medical_guidelines_module, "rag_search", lambda _vs, query, k: [fake_doc])
    helper = MedicalGuidelinesMCP()

    text = helper.get_context_string("airway obstruction", k=1)
    assert "ABCDE guideline chunk" in text


def test_session_memory_mcp_save_and_get_history():
    session_id = "test-session-memory-mcp"
    session_memory_mcp.save_exchange(session_id, "human says hello", "assistant says hi")
    out = session_memory_mcp.get_history(session_id)
    assert out["success"] is True
    assert out["has_history"] is True
    assert "human says hello" in out["history"] or "assistant says hi" in out["history"]
