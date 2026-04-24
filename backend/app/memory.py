from __future__ import annotations

from dataclasses import dataclass
from typing import Dict, List


@dataclass
class ChatTurn:
    role: str
    content: str


class InMemorySessionStore:
    """
    Simple per-session memory store for this offline project.
    In production, replace with Redis/DB.
    """

    def __init__(self) -> None:
        self._sessions: Dict[str, List[ChatTurn]] = {}

    def append(self, session_id: str, role: str, content: str) -> None:
        self._sessions.setdefault(session_id, []).append(ChatTurn(role=role, content=content))

    def get(self, session_id: str) -> List[ChatTurn]:
        return list(self._sessions.get(session_id, []))

    def clear(self, session_id: str) -> None:
        self._sessions.pop(session_id, None)


session_store = InMemorySessionStore()

