from __future__ import annotations

import json
import re
from typing import Any, Dict

from langchain_core.prompts import PromptTemplate
from langchain_ollama import OllamaLLM

from app.mcp.medical_guidelines_mcp import medical_guidelines_mcp
from app.mcp.scenario_context_mcp import scenario_context_mcp
from app.mcp.session_memory_mcp import session_memory_mcp
from app.services.conversation_state import get_state, normalize_question
from app.config import OLLAMA_BASE_URL, OLLAMA_CHAT_MODEL, OLLAMA_CHAT_TEMPERATURE
from app.tools.rag import RagDeps

llm = OllamaLLM(
    model=OLLAMA_CHAT_MODEL,
    base_url=OLLAMA_BASE_URL,
    temperature=OLLAMA_CHAT_TEMPERATURE,
)

CHAT_SYSTEM = """You are Radio Medical Denmark, the Danish telemedicine medical advice service for ships at sea.
You are responding to a medical officer on board a vessel who is treating a patient.

AVAILABLE MEDICINES ON BOARD (reference by number):
{guidelines}

PREVIOUS CONVERSATION:
{history}

SCENARIO CONTEXT:
{scenario}

You must respond as a real Radio Medical doctor would, professional, clear, and actionable.

RULES:
- Always sign off with "Best regards, Radio Medical Denmark"
- Reference medicines by their number when relevant (example: "3.1 Paracetamol 1g")
- Ask specific follow-up questions only when needed
- Give clear numbered instructions when action is needed
- Assess if the case should be: ongoing, recovering, critical, or closed
- A case is CLOSED when: patient has recovered, been transferred to hospital, or no further advice is possible
- A case is CRITICAL when: MEDEVAC or immediate evacuation is needed
- A case is RECOVERING when: patient is improving and just needs monitoring
- A case is ONGOING when: treatment is in progress and regular check-ins are needed

OUTPUT FORMAT - respond ONLY with valid JSON:
{{
  "reply": "Your full Radio Medical response here, ending with Best regards, Radio Medical Denmark",
  "case_status": "ongoing or recovering or critical or closed",
  "next_check_minutes": 30,
  "questions_for_participants": ["string"],
  "answered_questions": ["string"]
}}"""

CHAT_USER = """Medical officer update:
{message}

Patient context: {record_summary}

Respond as Radio Medical Denmark and assess the current case status."""

prompt = PromptTemplate(
    input_variables=["guidelines", "history", "scenario", "message", "record_summary"],
    template=CHAT_SYSTEM + "\n\n" + CHAT_USER,
)

chat_chain = prompt | llm


def _extract_questions_from_reply(reply: str) -> list[str]:
    candidates = re.findall(r"([^?.!]*\?)", reply)
    out: list[str] = []
    for c in candidates:
        q = " ".join(c.split()).strip()
        if len(q) < 8:
            continue
        out.append(q)
    return out[:3]


def _parse_json_response(text: str) -> dict | None:
    raw = (text or "").strip()
    if not raw:
        return None
    try:
        parsed = json.loads(raw)
        return parsed if isinstance(parsed, dict) else None
    except Exception:
        pass

    start = raw.find("{")
    end = raw.rfind("}")
    if start != -1 and end != -1 and end > start:
        chunk = raw[start : end + 1]
        try:
            parsed = json.loads(chunk)
            return parsed if isinstance(parsed, dict) else None
        except Exception:
            return None
    return None


def _decode_json_like_string(value: str) -> str:
    out = value.replace('\\"', '"').replace("\\n", "\n").replace("\\t", "\t")
    return out.strip()


def _parse_json_like_fields(text: str) -> dict | None:
    raw = (text or "").strip()
    if '"reply"' not in raw or '"case_status"' not in raw:
        return None

    reply_match = re.search(r'"reply"\s*:\s*"([\s\S]*?)"\s*,\s*"case_status"', raw)
    status_match = re.search(r'"case_status"\s*:\s*"([^"]+)"', raw)
    minutes_match = re.search(r'"next_check_minutes"\s*:\s*(\d+)', raw)
    questions_match = re.search(r'"questions_for_participants"\s*:\s*\[([\s\S]*?)\]', raw)
    answered_match = re.search(r'"answered_questions"\s*:\s*\[([\s\S]*?)\]', raw)

    if not reply_match or not status_match:
        return None

    def _parse_string_array(block: str | None) -> list[str]:
        if not block:
            return []
        return [_decode_json_like_string(x) for x in re.findall(r'"([^"]*?)"', block)]

    parsed = {
        "reply": _decode_json_like_string(reply_match.group(1)),
        "case_status": _decode_json_like_string(status_match.group(1)),
        "next_check_minutes": int(minutes_match.group(1)) if minutes_match else 30,
        "questions_for_participants": _parse_string_array(questions_match.group(1) if questions_match else None),
        "answered_questions": _parse_string_array(answered_match.group(1) if answered_match else None),
    }
    return parsed


def run_chat(session_id: str, message: str, record_summary: str = "") -> dict:
    guidelines = medical_guidelines_mcp.get_context_string(message)
    history = session_memory_mcp.get_context_string(session_id)
    scenario = scenario_context_mcp.get_context_string(message)

    result = chat_chain.invoke(
        {
            "guidelines": guidelines,
            "history": history,
            "scenario": scenario,
            "message": message,
            "record_summary": record_summary or "See previous conversation history",
        }
    )

    cleaned = str(result).strip()
    if "```" in cleaned:
        cleaned = cleaned.split("```")[1]
        if cleaned.startswith("json"):
            cleaned = cleaned[4:]
        cleaned = cleaned.strip()

    parsed = _parse_json_response(cleaned)
    if parsed is None:
        parsed = _parse_json_like_fields(cleaned)
    if parsed is None:
        parsed = {
            "reply": cleaned,
            "case_status": "ongoing",
            "next_check_minutes": 30,
            "questions_for_participants": _extract_questions_from_reply(cleaned),
            "answered_questions": [],
        }

    # Some model outputs nest JSON as a string in "reply"; unpack when possible.
    reply = parsed.get("reply")
    if isinstance(reply, str):
        nested = _parse_json_response(reply)
        if nested and any(k in nested for k in ["case_status", "next_check_minutes", "questions_for_participants"]):
            parsed = {**nested, "reply": nested.get("reply", reply)}

    if not isinstance(parsed.get("next_check_minutes"), int):
        parsed["next_check_minutes"] = 30
    if not isinstance(parsed.get("reply"), str):
        parsed["reply"] = str(parsed.get("reply", ""))
    if not isinstance(parsed.get("case_status"), str):
        parsed["case_status"] = "ongoing"
    if not isinstance(parsed.get("questions_for_participants"), list):
        parsed["questions_for_participants"] = _extract_questions_from_reply(parsed.get("reply", ""))
    if not isinstance(parsed.get("answered_questions"), list):
        parsed["answered_questions"] = []

    session_memory_mcp.save_exchange(
        session_id,
        f"Medical officer: {message}",
        parsed.get("reply", ""),
    )
    return parsed


def chat_doctor_turn(rag: RagDeps, session_id: str, report_text: str, user_message: str = "") -> Dict[str, Any]:
    _ = rag  # kept for endpoint signature compatibility
    state = get_state(session_id)
    trimmed_user = user_message.strip()

    if trimmed_user and state.pending_questions:
        first = state.pending_questions.pop(0)
        state.answered_keys.add(normalize_question(first))

    parsed = run_chat(
        session_id=session_id,
        message=trimmed_user or "No new update.",
        record_summary=report_text,
    )

    answered_now = [str(q).strip() for q in parsed.get("answered_questions", []) if str(q).strip()]
    if answered_now and state.pending_questions:
        pending_norm_map = {normalize_question(q): q for q in state.pending_questions}
        to_remove: set[str] = set()
        for answered in answered_now:
            ak = normalize_question(answered)
            if ak in pending_norm_map:
                state.answered_keys.add(ak)
                to_remove.add(ak)
        if to_remove:
            state.pending_questions = [q for q in state.pending_questions if normalize_question(q) not in to_remove]

    suggested_questions = [str(q).strip() for q in parsed.get("questions_for_participants", []) if str(q).strip()]
    deduped_new: list[str] = []
    existing_pending_keys = {normalize_question(q) for q in state.pending_questions}
    for q in suggested_questions:
        key = normalize_question(q)
        if key in state.asked_keys or key in state.answered_keys or key in existing_pending_keys:
            continue
        state.asked_keys.add(key)
        deduped_new.append(q)

    state.pending_questions.extend(deduped_new)
    assistant_message = str(parsed.get("reply", "")).strip()
    return {
        "assistant_message": assistant_message,
        "questions_for_participants": deduped_new,
        "pending_questions": list(state.pending_questions),
        "can_finalize_summary": len(state.pending_questions) == 0,
    }
