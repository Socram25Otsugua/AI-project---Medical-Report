from __future__ import annotations

import json
import re
from typing import Any, Dict

from langchain_core.prompts import PromptTemplate
from langchain_ollama import OllamaLLM

from app.mcp.medical_guidelines_mcp import medical_guidelines_mcp
from app.mcp.scenario_context_mcp import scenario_context_mcp
from app.mcp.session_memory_mcp import session_memory_mcp
from app.services.analysis_guardrails import filter_questions
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
- Give clear numbered instructions when action is needed
- Assess if the case should be: ongoing, recovering, critical, or closed
- A case is CLOSED when: patient has recovered, been transferred to hospital, or no further advice is possible
- A case is CRITICAL when: MEDEVAC or immediate evacuation is needed
- A case is RECOVERING when: patient is improving and just needs monitoring
- A case is ONGOING when: treatment is in progress and regular check-ins are needed

FOLLOW-UP QUESTIONS (critical):
- Put ONLY specific clinical questions in questions_for_participants (max 1 per turn).
- Do NOT include questions in the reply text: no "I would like to ask", no bullet lists of questions, no sentences ending with "?".
- Never add generic standing instructions as questions (e.g. "report any changes", "update us on condition", "let us know if anything changes") — the officer is already in an active chat.
- If no specific clinical gap exists, return an empty questions_for_participants array.

FOLLOW-UP REPLIES (when PREVIOUS CONVERSATION is not empty):
- This is a continuing case, not the first contact. Reply in 2–6 short sentences.
- Address ONLY what is new in the latest officer message: changed symptoms, vitals trends, or adjusted advice.
- Do NOT repeat advice already given earlier (NPO, bed rest, positioning, standard monitoring, medicine dosing, investigation wording) unless the clinical picture changed.
- Do NOT rewrite the full initial assessment letter; add only what matters now.

PATIENT DATA AND OBSERVATION CHART:
- Patient context may include an observation chart with up to 8 columns (serial time points, left to right).
- Use every filled column; compare trends when multiple columns have data.
- The crew may add new readings in the next empty column while this chat continues — prefer asking them to record serial vitals there instead of repeating chart questions in chat.
- Do not ask for vitals or findings already documented in the form or in any observation column.
- Ask chat questions only for non-chart information needed to proceed safely (e.g. treatment response, new symptoms, complications).

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

Turn type: {turn_type}

Respond as Radio Medical Denmark and assess the current case status."""

prompt = PromptTemplate(
    input_variables=["guidelines", "history", "scenario", "message", "record_summary", "turn_type"],
    template=CHAT_SYSTEM + "\n\n" + CHAT_USER,
)

_GENERIC_QUESTION_PATTERNS = (
    r"report any changes",
    r"please (?:report|update|inform|notify|advise)",
    r"(?:keep|stay) (?:us|me) (?:informed|updated)",
    r"changes in the patient'?s condition",
    r"available for further consultation",
    r"let (?:us|me) know",
    r"including pain relief",
    r"monitor (?:the patient )?closely",
    r"contact (?:us|radio medical) (?:if|should)",
)


def _is_actionable_follow_up(question: str) -> bool:
    """Standing instructions are not blocking chat questions."""
    norm = normalize_question(question).replace(" ?", " ")
    if len(norm) < 12:
        return False
    for pattern in _GENERIC_QUESTION_PATTERNS:
        if re.search(pattern, norm):
            return False
    return True


def _has_prior_conversation(session_id: str) -> bool:
    history = session_memory_mcp.get_context_string(session_id)
    return history.strip() != "No previous exchanges in this session."

chat_chain = prompt | llm


def _strip_questions_from_reply(reply: str, structured_questions: list[str]) -> str:
    """Remove narrative question blocks when structured questions are returned separately."""
    if not structured_questions:
        return reply.strip()

    text = reply.strip()
    signoff = ""
    signoff_match = re.search(r"(?is)\n\s*best regards, radio medical denmark\s*$", text)
    if signoff_match:
        signoff = text[signoff_match.start() :].strip()
        text = text[: signoff_match.start()].strip()

    text = re.sub(
        r"(?is)^(?:i would like to ask(?: a few)? questions?|important follow[- ]?up questions?|"
        r"follow[- ]?up questions?|please (?:answer|respond to)|questions for you:?).*",
        "",
        text,
    ).strip()

    structured_keys = {normalize_question(q) for q in structured_questions if str(q).strip()}
    kept_lines: list[str] = []
    for line in text.splitlines():
        stripped = line.strip()
        if stripped.endswith("?"):
            norm = normalize_question(stripped.lstrip("-*• "))
            if norm in structured_keys:
                continue
            if any(norm in key or key in norm for key in structured_keys):
                continue
        kept_lines.append(line)

    cleaned = re.sub(r"\n{3,}", "\n\n", "\n".join(kept_lines)).strip()
    if signoff:
        cleaned = f"{cleaned}\n\n{signoff}" if cleaned else signoff
    return cleaned


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
    is_follow_up = _has_prior_conversation(session_id)
    turn_type = (
        "Follow-up — officer sent a new update; reply briefly with only new/changed advice."
        if is_follow_up
        else "Initial assessment — first contact for this case."
    )

    result = chat_chain.invoke(
        {
            "guidelines": guidelines,
            "history": history,
            "scenario": scenario,
            "message": message,
            "record_summary": record_summary or "See previous conversation history",
            "turn_type": turn_type,
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
        for q in state.pending_questions:
            state.answered_keys.add(normalize_question(q))
        state.pending_questions.clear()

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
    suggested_questions = [q for q in suggested_questions if _is_actionable_follow_up(q)]
    suggested_questions = filter_questions(report_text, suggested_questions)
    if trimmed_user:
        # Officer updates in chat satisfy standing information requests; only block on new clinical gaps.
        suggested_questions = []
    deduped_new: list[str] = []
    existing_pending_keys = {normalize_question(q) for q in state.pending_questions}
    for q in suggested_questions:
        key = normalize_question(q)
        if key in state.asked_keys or key in state.answered_keys or key in existing_pending_keys:
            continue
        state.asked_keys.add(key)
        deduped_new.append(q)

    state.pending_questions.extend(deduped_new)
    assistant_message = _strip_questions_from_reply(
        str(parsed.get("reply", "")).strip(),
        suggested_questions,
    )
    return {
        "assistant_message": assistant_message,
        "questions_for_participants": deduped_new,
        "pending_questions": list(state.pending_questions),
        "can_finalize_summary": len(state.pending_questions) == 0,
    }
