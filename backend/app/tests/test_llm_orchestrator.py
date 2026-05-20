import json
from types import SimpleNamespace

from app.services import llm_orchestrator
from app.services.conversation_state import clear_state
from tools.memory import InMemorySessionStore


class _FakeChain:
    def __init__(self, response):
        self.response = response
        self.last_payload = None

    def __or__(self, other):
        return self

    def invoke(self, payload):
        self.last_payload = payload
        return self.response


def test_format_rag_context_joins_sources():
    docs = [
        SimpleNamespace(metadata={"source": "a.md"}, page_content="alpha"),
        SimpleNamespace(metadata={"source": "b.md"}, page_content="beta"),
    ]
    out = llm_orchestrator._format_rag_context(docs)
    assert "[source: a.md]" in out
    assert "alpha" in out
    assert "[source: b.md]" in out
    assert "beta" in out
    assert "\n\n---\n\n" in out


def test_review_report_uses_tools_and_updates_memory(monkeypatch):
    fake_chain = _FakeChain(
        {
            "extracted": {"x": 1},
            "deficiencies": [],
            "safety_flags": [],
            "completeness_score": 90,
        }
    )
    fake_store = InMemorySessionStore()

    monkeypatch.setattr(llm_orchestrator, "session_store", fake_store)
    monkeypatch.setattr(llm_orchestrator, "rag_search", lambda *args, **kwargs: [])
    monkeypatch.setattr(llm_orchestrator, "_chat", lambda: object())
    monkeypatch.setattr(llm_orchestrator, "JsonOutputParser", lambda pydantic_object: object())
    monkeypatch.setattr(
        llm_orchestrator.ChatPromptTemplate,
        "from_messages",
        staticmethod(lambda messages: fake_chain),
    )
    monkeypatch.setattr(
        llm_orchestrator,
        "get_report_mcp_context",
        lambda report_text, include_checklist: {
            "missing_sections": {"missing": ["history"]},
            "vitals": {"spo2_percent": 93},
            "triage": {"priority": "urgent"},
        },
    )
    monkeypatch.setattr(
        llm_orchestrator,
        "scenario_context_mcp",
        SimpleNamespace(get_scenario=lambda _text: {"success": True, "scenario": {"detected_type": "default"}}),
    )
    monkeypatch.setattr(
        llm_orchestrator,
        "medical_guidelines_mcp",
        SimpleNamespace(get_context_string=lambda _text, k=3: "guidelines"),
    )
    monkeypatch.setattr(
        llm_orchestrator,
        "session_memory_mcp",
        SimpleNamespace(get_context_string=lambda _sid: "No previous exchanges in this session."),
    )

    rag = SimpleNamespace(vectorstore=object())
    out = llm_orchestrator.review_report(rag=rag, session_id="s1", report_text="report")

    assert out["completeness_score"] == 90
    assert out["vitals_score"] == 20
    turns = fake_store.get("s1")
    assert len(turns) == 2
    assert turns[0].role == "user"
    assert turns[1].role == "assistant"
    payload = json.loads(fake_chain.last_payload["payload"])
    assert payload["mcp"]["triage"]["priority"] == "urgent"


def test_generate_next_step_returns_chain_output(monkeypatch):
    fake_chain = _FakeChain(
        {
            "next_step_message": "Do ABCDE.",
            "rationale_bullets": ["Reason"],
            "questions_for_participants": ["What is the current level of consciousness?", "Any chest pain?"],
        }
    )
    fake_store = InMemorySessionStore()

    monkeypatch.setattr(llm_orchestrator, "session_store", fake_store)
    monkeypatch.setattr(llm_orchestrator, "rag_search", lambda *args, **kwargs: [])
    monkeypatch.setattr(llm_orchestrator, "_chat", lambda: object())
    monkeypatch.setattr(llm_orchestrator, "JsonOutputParser", lambda pydantic_object: object())
    monkeypatch.setattr(
        llm_orchestrator.ChatPromptTemplate,
        "from_messages",
        staticmethod(lambda messages: fake_chain),
    )
    monkeypatch.setattr(
        llm_orchestrator,
        "get_report_mcp_context",
        lambda report_text, include_checklist: {
            "vitals": {"spo2_percent": 94},
            "triage": {"priority": "urgent"},
        },
    )
    monkeypatch.setattr(
        llm_orchestrator,
        "scenario_context_mcp",
        SimpleNamespace(get_scenario=lambda _text: {"success": True, "scenario": {"detected_type": "default"}}),
    )
    monkeypatch.setattr(
        llm_orchestrator,
        "medical_guidelines_mcp",
        SimpleNamespace(get_context_string=lambda _text, k=3: "guidelines"),
    )
    monkeypatch.setattr(
        llm_orchestrator,
        "session_memory_mcp",
        SimpleNamespace(get_context_string=lambda _sid: "No previous exchanges in this session."),
    )

    rag = SimpleNamespace(vectorstore=object())
    out = llm_orchestrator.generate_next_step(
        rag=rag,
        session_id="s1",
        report_text="Level of consciousness (1-4): 2",
        review_json={"completeness_score": 80},
    )

    assert out["next_step_message"] == "Do ABCDE."
    assert fake_store.get("s1")[0].role == "assistant"
    assert out["questions_for_participants"] == ["Any chest pain?"]
    payload = json.loads(fake_chain.last_payload["payload"])
    assert payload["mcp"]["triage"]["priority"] == "urgent"


def test_evaluate_patient_includes_mcp_vitals(monkeypatch):
    fake_chain = _FakeChain(
        {
            "status": "concerning",
            "summary": "Needs reassessment.",
            "suspected_problems": ["hypoxia"],
            "red_flags": ["low oxygen"],
        }
    )
    fake_store = InMemorySessionStore()

    monkeypatch.setattr(llm_orchestrator, "session_store", fake_store)
    monkeypatch.setattr(llm_orchestrator, "rag_search", lambda *args, **kwargs: [])
    monkeypatch.setattr(llm_orchestrator, "_chat", lambda: object())
    monkeypatch.setattr(llm_orchestrator, "JsonOutputParser", lambda pydantic_object: object())
    monkeypatch.setattr(
        llm_orchestrator.ChatPromptTemplate,
        "from_messages",
        staticmethod(lambda messages: fake_chain),
    )
    monkeypatch.setattr(
        llm_orchestrator,
        "get_report_mcp_context",
        lambda report_text, include_checklist: {
            "vitals": {"spo2_percent": 91},
            "triage": {"priority": "critical"},
        },
    )
    monkeypatch.setattr(
        llm_orchestrator,
        "scenario_context_mcp",
        SimpleNamespace(get_scenario=lambda _text: {"success": True, "scenario": {"detected_type": "default"}}),
    )
    monkeypatch.setattr(
        llm_orchestrator,
        "medical_guidelines_mcp",
        SimpleNamespace(get_context_string=lambda _text, k=3: "guidelines"),
    )
    monkeypatch.setattr(
        llm_orchestrator,
        "session_memory_mcp",
        SimpleNamespace(get_context_string=lambda _sid: "No previous exchanges in this session."),
    )

    rag = SimpleNamespace(vectorstore=object())
    out = llm_orchestrator.evaluate_patient(
        rag=rag,
        session_id="s1",
        report_text="report",
        review_json={"completeness_score": 70},
    )

    assert out["status"] == "concerning"
    payload = json.loads(fake_chain.last_payload["payload"])
    assert payload["mcp"]["vitals"]["spo2_percent"] == 91
    assert payload["mcp"]["triage"]["priority"] == "critical"


def test_is_answer_already_in_report_uses_mcp_vitals():
    report_text = """
    - Oxygen saturation: 91 %
    - Clear airways: yes
    - Does the patient have any allergies?: No
    """.strip()
    mcp_context = {"vitals": {"spo2_percent": 91}}

    assert llm_orchestrator._is_answer_already_in_report("What is the patient's oxygen saturation?", report_text, mcp_context)
    assert llm_orchestrator._is_answer_already_in_report("Is the patient's airway clear?", report_text, mcp_context)
    assert llm_orchestrator._is_answer_already_in_report(
        "Does the patient have any known drug allergies?", report_text, mcp_context
    )


def test_chat_doctor_turn_filters_questions_already_in_report(monkeypatch):
    clear_state("s-chat-filter")
    fake_store = InMemorySessionStore()

    monkeypatch.setattr(llm_orchestrator, "session_store", fake_store)
    monkeypatch.setattr(llm_orchestrator, "rag_search", lambda *args, **kwargs: [])
    monkeypatch.setattr(
        llm_orchestrator,
        "medical_guidelines_mcp",
        SimpleNamespace(get_context_string=lambda _text, k=1: "guidelines"),
    )
    monkeypatch.setattr(
        llm_orchestrator,
        "scenario_context_mcp",
        SimpleNamespace(get_scenario=lambda _text: {"success": True, "scenario": {"detected_type": "default"}}),
    )
    monkeypatch.setattr(
        llm_orchestrator,
        "get_report_mcp_context",
        lambda report_text, include_checklist: {"vitals": {"spo2_percent": 91}, "triage": {"priority": "urgent"}},
    )
    monkeypatch.setattr(
        llm_orchestrator,
        "invoke_short_term_chat_turn",
        lambda session_id, payload: {
            "assistant_message": "Continue monitoring and reassess in 5 minutes.",
            "questions_for_participants": [
                "What is the patient's oxygen saturation?",
                "Is active bleeding controlled now?",
            ],
            "answered_questions": [],
        },
    )

    report_text = """
    - Oxygen saturation: 91 %
    - Clear airways: yes
    """.strip()
    rag = SimpleNamespace(vectorstore=object())
    out = llm_orchestrator.chat_doctor_turn(rag=rag, session_id="s-chat-filter", report_text=report_text, user_message="")

    assert out["questions_for_participants"] == ["Is active bleeding controlled now?"]
