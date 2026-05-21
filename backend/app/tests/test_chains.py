import json
from types import SimpleNamespace

from langchain_core.output_parsers import JsonOutputParser
from langchain_core.prompts import ChatPromptTemplate

from app.services import chat_service, patient_eval_chain, response_chain, review_chain
from app.services.common_chain import format_rag_context
from app.tools.memory import InMemorySessionStore


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
    out = format_rag_context(docs)
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

    monkeypatch.setattr(review_chain, "session_store", fake_store)
    monkeypatch.setattr(review_chain, "rag_search", lambda *args, **kwargs: [])
    monkeypatch.setattr(review_chain, "build_chat_model", lambda: object())
    monkeypatch.setattr(review_chain, "JsonOutputParser", JsonOutputParser)
    monkeypatch.setattr(
        ChatPromptTemplate,
        "from_messages",
        staticmethod(lambda messages: fake_chain),
    )
    monkeypatch.setattr(
        review_chain,
        "build_enriched_mcp_context",
        lambda report_text, include_checklist: {
            "missing_sections": {"missing": ["history"]},
            "vitals": {"spo2_percent": 93},
            "triage": {"priority": "urgent"},
        },
    )
    monkeypatch.setattr(
        review_chain,
        "session_memory_mcp",
        SimpleNamespace(get_context_string=lambda _sid: "No previous exchanges in this session."),
    )

    rag = SimpleNamespace(vectorstore=object())
    out = review_chain.review_report(rag=rag, session_id="s1", report_text="report")

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

    monkeypatch.setattr(response_chain, "session_store", fake_store)
    monkeypatch.setattr(response_chain, "rag_search", lambda *args, **kwargs: [])
    monkeypatch.setattr(response_chain, "build_chat_model", lambda: object())
    monkeypatch.setattr(response_chain, "JsonOutputParser", JsonOutputParser)
    monkeypatch.setattr(
        ChatPromptTemplate,
        "from_messages",
        staticmethod(lambda messages: fake_chain),
    )
    monkeypatch.setattr(
        response_chain,
        "build_enriched_mcp_context",
        lambda report_text, include_checklist: {
            "vitals": {"spo2_percent": 94},
            "triage": {"priority": "urgent"},
        },
    )
    monkeypatch.setattr(
        response_chain,
        "session_memory_mcp",
        SimpleNamespace(get_context_string=lambda _sid: "No previous exchanges in this session."),
    )

    rag = SimpleNamespace(vectorstore=object())
    out = response_chain.generate_next_step(
        rag=rag,
        session_id="s1",
        report_text="Level of consciousness (1-4): 2",
        review_json={"completeness_score": 80},
    )

    assert out["immediate_actions"] == ["Do ABCDE."]
    assert out["next_step_message"] == "Do ABCDE."
    assert len(out["monitoring_parameters"]) >= 1
    assert len(out["escalation_criteria"]) >= 1
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

    monkeypatch.setattr(patient_eval_chain, "session_store", fake_store)
    monkeypatch.setattr(patient_eval_chain, "rag_search", lambda *args, **kwargs: [])
    monkeypatch.setattr(patient_eval_chain, "build_chat_model", lambda: object())
    monkeypatch.setattr(patient_eval_chain, "JsonOutputParser", JsonOutputParser)
    monkeypatch.setattr(
        ChatPromptTemplate,
        "from_messages",
        staticmethod(lambda messages: fake_chain),
    )
    monkeypatch.setattr(
        patient_eval_chain,
        "build_enriched_mcp_context",
        lambda report_text, include_checklist: {
            "vitals": {"spo2_percent": 91},
            "triage": {"priority": "critical"},
        },
    )
    monkeypatch.setattr(
        patient_eval_chain,
        "session_memory_mcp",
        SimpleNamespace(get_context_string=lambda _sid: "No previous exchanges in this session."),
    )

    rag = SimpleNamespace(vectorstore=object())
    out = patient_eval_chain.evaluate_patient(
        rag=rag,
        session_id="s1",
        report_text="report",
        review_json={"completeness_score": 70},
    )

    assert out["status"] == "concerning"
    payload = json.loads(fake_chain.last_payload["payload"])
    assert payload["mcp"]["vitals"]["spo2_percent"] == 91
    assert payload["mcp"]["triage"]["priority"] == "critical"


def test_chat_doctor_turn_tracks_pending_questions(monkeypatch):
    from app.services.conversation_state import clear_state

    clear_state("s-chat")
    monkeypatch.setattr(
        chat_service,
        "run_chat",
        lambda session_id, message, record_summary="": {
            "reply": "Continue monitoring.",
            "case_status": "ongoing",
            "next_check_minutes": 30,
            "questions_for_participants": ["Is active bleeding controlled now?"],
            "answered_questions": [],
        },
    )

    rag = SimpleNamespace(vectorstore=object())
    out = chat_service.chat_doctor_turn(
        rag=rag, session_id="s-chat", report_text="report", user_message=""
    )

    assert out["questions_for_participants"] == ["Is active bleeding controlled now?"]
    assert out["pending_questions"] == ["Is active bleeding controlled now?"]
    assert out["can_finalize_summary"] is False

    answered = chat_service.chat_doctor_turn(
        rag=rag, session_id="s-chat", report_text="report", user_message="Bleeding is controlled now."
    )
    assert answered["pending_questions"] == []
    assert answered["can_finalize_summary"] is True


def test_chat_doctor_turn_strips_duplicate_questions_from_reply(monkeypatch):
    from app.services.conversation_state import clear_state

    clear_state("s-chat-strip")
    monkeypatch.setattr(
        chat_service,
        "run_chat",
        lambda session_id, message, record_summary="": {
            "reply": (
                "Dear officer,\n\n"
                "I would like to ask a few questions:\n"
                "* Have you considered an anti-emetic?\n"
                "* Any signs of peritonitis?\n\n"
                "Best regards, Radio Medical Denmark"
            ),
            "case_status": "ongoing",
            "next_check_minutes": 30,
            "questions_for_participants": [
                "Have you considered an anti-emetic?",
                "Any signs of peritonitis?",
            ],
            "answered_questions": [],
        },
    )

    rag = SimpleNamespace(vectorstore=object())
    out = chat_service.chat_doctor_turn(
        rag=rag, session_id="s-chat-strip", report_text="report", user_message=""
    )

    assert "I would like to ask" not in out["assistant_message"]
    assert "anti-emetic" not in out["assistant_message"]
    assert out["pending_questions"] == [
        "Have you considered an anti-emetic?",
        "Any signs of peritonitis?",
    ]
