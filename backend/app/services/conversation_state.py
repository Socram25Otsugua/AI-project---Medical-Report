from __future__ import annotations

from dataclasses import dataclass, field


def normalize_question(question: str) -> str:
    return " ".join(question.lower().strip().replace("?", " ?").split())


@dataclass
class ConversationState:
    pending_questions: list[str] = field(default_factory=list)
    asked_keys: set[str] = field(default_factory=set)
    answered_keys: set[str] = field(default_factory=set)
    cached_rag_context: str = ""
    cached_guidelines_context: str = ""
    cached_scenario_context: dict = field(default_factory=dict)


_STATES: dict[str, ConversationState] = {}


def get_state(session_id: str) -> ConversationState:
    if session_id not in _STATES:
        _STATES[session_id] = ConversationState()
    return _STATES[session_id]


def clear_state(session_id: str) -> None:
    _STATES.pop(session_id, None)
