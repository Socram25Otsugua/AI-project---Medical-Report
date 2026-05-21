from types import SimpleNamespace

from app.services import chat_service
from app.services.analysis_guardrails import filter_questions
from app.services.chat_service import _is_actionable_follow_up, _strip_questions_from_reply
from app.services.conversation_state import clear_state


def test_strip_questions_from_reply_removes_narrative_duplicates():
    reply = """Dear officer,

Assessment text here.

I would like to ask a few questions:
* Have you considered administering an anti-emetic?
* Are there any signs of peritonitis?

Best regards, Radio Medical Denmark"""
    questions = [
        "Have you considered administering an anti-emetic?",
        "Are there any signs of peritonitis?",
    ]
    out = _strip_questions_from_reply(reply, questions)
    assert "I would like to ask" not in out
    assert "anti-emetic" not in out
    assert "peritonitis" not in out
    assert "Assessment text here" in out
    assert "Best regards, Radio Medical Denmark" in out


def test_is_actionable_follow_up_rejects_generic_status_prompts():
    assert _is_actionable_follow_up(
        "Please report any changes in the patient's condition, including pain relief, vomiting, or other symptoms."
    ) is False
    assert _is_actionable_follow_up("Any signs of peritonitis or rebound tenderness?") is True


def test_user_reply_clears_pending_and_unlocks_summary(monkeypatch):
    clear_state("s-reply")
    monkeypatch.setattr(
        chat_service,
        "run_chat",
        lambda session_id, message, record_summary="": {
            "reply": "Noted. Continue NPO and monitor closely. Best regards, Radio Medical Denmark",
            "case_status": "ongoing",
            "next_check_minutes": 30,
            "questions_for_participants": [
                "Please report any changes in the patient's condition, including pain relief, vomiting, or other symptoms."
            ],
            "answered_questions": [],
        },
    )

    rag = SimpleNamespace(vectorstore=object())
    chat_service.chat_doctor_turn(
        rag=rag,
        session_id="s-reply",
        report_text="report",
        user_message="",
    )
    out = chat_service.chat_doctor_turn(
        rag=rag,
        session_id="s-reply",
        report_text="report with update",
        user_message="Patient is vomiting again and anxious",
    )

    assert out["pending_questions"] == []
    assert out["can_finalize_summary"] is True


def test_filter_questions_skips_chart_vitals_when_documented_in_observation_column():
    report = """
## Observation chart
### Observation column 1
- Heart rate / min. (60–80): 88
- Oxygen saturation in % (95–100): 94
"""
    questions = ["What is the current heart rate?", "Any new abdominal pain?"]
    out = filter_questions(report, questions)
    assert out == ["Any new abdominal pain?"]
