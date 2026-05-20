from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Dict

from app.tools.memory import session_store


@dataclass(frozen=True)
class SessionMemoryMCP:
    name: str = "session_memory_mcp"
    description: str = "Store and retrieve conversation memory for training sessions."

    def get_history(self, session_id: str) -> Dict[str, Any]:
        try:
            turns = session_store.get(session_id)
            history = "\n".join([f"{t.role}: {t.content}" for t in turns]) if turns else ""
            return {
                "success": True,
                "session_id": session_id,
                "history": history,
                "has_history": bool(history),
            }
        except Exception as e:
            return {"success": False, "error": str(e), "history": "", "has_history": False}

    def save_exchange(self, session_id: str, human_input: str, ai_output: str) -> Dict[str, Any]:
        try:
            session_store.append(session_id, "user", human_input)
            session_store.append(session_id, "assistant", ai_output)
            return {"success": True, "session_id": session_id}
        except Exception as e:
            return {"success": False, "error": str(e)}

    def get_context_string(self, session_id: str) -> str:
        result = self.get_history(session_id)
        if not result["success"] or not result["has_history"]:
            return "No previous exchanges in this session."
        return result["history"]


session_memory_mcp = SessionMemoryMCP()
