from __future__ import annotations

import json
import re
from typing import Any, Dict, List

from pydantic import BaseModel, Field
from langchain_core.messages import SystemMessage
from langchain_core.output_parsers import JsonOutputParser
from langchain_core.prompts import ChatPromptTemplate
from langchain_ollama import ChatOllama

from app.mcp import (
    get_report_mcp_context,
    medical_guidelines_mcp,
    scenario_context_mcp,
    session_memory_mcp,
    vitals_coverage_feedback,
    vitals_coverage_score,
)
from app.models.schemas import PatientEvaluation, ResponseResult, ReviewResult
from app.prompts import CHAT_DOCTOR_SYSTEM_PROMPT, PATIENT_EVAL_SYSTEM_PROMPT, RESPONSE_SYSTEM_PROMPT, REVIEW_SYSTEM_PROMPT
from app.services.analysis_guardrails import filter_deficiencies, filter_questions, filter_temperature_labels
from app.services.conversation_state import get_state, normalize_question
from tools.memory import session_store
from tools.rag import RagDeps, rag_search
from app.settings import settings


def _chat() -> ChatOllama:
    return ChatOllama(
        model=settings.ollama_model,
        base_url=settings.ollama_base_url,
        temperature=settings.ollama_temperature,
    )


class ChatDoctorResult(BaseModel):
    assistant_message: str
    questions_for_participants: list[str] = Field(default_factory=list)


def _format_rag_context(docs: List[Any]) -> str:
    if not docs:
        return ""
    parts = []
    for d in docs:
        src = d.metadata.get("source", "unknown")
        parts.append(f"[source: {src}]\n{d.page_content}".strip())
    return "\n\n---\n\n".join(parts)


def _filter_redundant_questions(report_text: str, questions: list[str]) -> list[str]:
    text = report_text.lower()
    has_consciousness = bool(re.search(r"(level of consciousness|consciousness|avpu|gcs)", text))
    if not has_consciousness:
        return questions
    filtered: list[str] = []
    for q in questions:
        ql = str(q).lower()
        if re.search(r"(consciousness|avpu|alert.*voice.*pain|gcs)", ql):
            continue
        filtered.append(str(q))
    return filtered


def review_report(rag: RagDeps, session_id: str, report_text: str) -> Dict[str, Any]:
    history = session_store.get(session_id)[-6:]
    memory_snippet = "\n".join([f"{t.role}: {t.content}" for t in history]) if history else ""
    mcp_history = session_memory_mcp.get_context_string(session_id)
    if mcp_history != "No previous exchanges in this session.":
        memory_snippet = mcp_history

    mcp_context = get_report_mcp_context(report_text, include_checklist=True)
    mcp_context["scenario_context"] = scenario_context_mcp.get_scenario(report_text)
    mcp_context["guidelines_context"] = medical_guidelines_mcp.get_context_string(report_text, k=3)

    docs = rag_search(rag.vectorstore, query="Radio Medical Record checklist ABCDE vitals history actions", k=4)
    context = _format_rag_context(docs)

    user_payload = {
        "report_text": report_text,
        "memory": memory_snippet,
        "rag_context": context,
        "mcp": mcp_context,
    }

    parser = JsonOutputParser(pydantic_object=ReviewResult)
    prompt = ChatPromptTemplate.from_messages(
        [
            SystemMessage(content=REVIEW_SYSTEM_PROMPT),
            ("human", "{payload}\n\nReturn only JSON."),
        ]
    )
    chain = prompt | _chat() | parser
    data = chain.invoke({"payload": json.dumps(user_payload, ensure_ascii=False)})
    raw: Dict[str, Any]
    if hasattr(data, "model_dump"):
        raw = data.model_dump()
    else:
        raw = dict(data)
    raw["deficiencies"] = filter_deficiencies(report_text, raw.get("deficiencies", []))
    raw["safety_flags"] = filter_temperature_labels(report_text, raw.get("safety_flags", []))
    raw["vitals_score"] = vitals_coverage_score(mcp_context["vitals"])
    raw["vitals_feedback"] = vitals_coverage_feedback(mcp_context["vitals"])
    session_store.append(session_id, "user", report_text[:8000])
    session_store.append(session_id, "assistant", json.dumps(raw, ensure_ascii=False)[:8000])
    return raw


def generate_next_step(rag: RagDeps, session_id: str, report_text: str, review_json: Dict[str, Any]) -> Dict[str, Any]:
    docs = rag_search(rag.vectorstore, query="ABCDE stabilization escalation guidance questions", k=4)
    context = _format_rag_context(docs)
    mcp_context = get_report_mcp_context(report_text, include_checklist=True)
    mcp_context["scenario_context"] = scenario_context_mcp.get_scenario(report_text)
    mcp_context["guidelines_context"] = medical_guidelines_mcp.get_context_string(report_text, k=3)
    mcp_history = session_memory_mcp.get_context_string(session_id)

    user_payload = {
        "report_text": report_text,
        "review": review_json,
        "rag_context": context,
        "memory": mcp_history,
        "mcp": mcp_context,
    }

    parser = JsonOutputParser(pydantic_object=ResponseResult)
    prompt = ChatPromptTemplate.from_messages(
        [
            SystemMessage(content=RESPONSE_SYSTEM_PROMPT),
            ("human", "{payload}\n\nReturn only JSON."),
        ]
    )
    chain = prompt | _chat() | parser
    data = chain.invoke({"payload": json.dumps(user_payload, ensure_ascii=False)})
    raw: Dict[str, Any]
    if hasattr(data, "model_dump"):
        raw = data.model_dump()
    else:
        raw = dict(data)
    raw["questions_for_participants"] = _filter_redundant_questions(
        report_text, raw.get("questions_for_participants", [])
    )
    raw["questions_for_participants"] = filter_questions(report_text, raw.get("questions_for_participants", []))
    raw["rationale_bullets"] = filter_temperature_labels(report_text, raw.get("rationale_bullets", []))
    session_store.append(session_id, "assistant", json.dumps(raw, ensure_ascii=False)[:8000])
    return raw


def evaluate_patient(rag: RagDeps, session_id: str, report_text: str, review_json: Dict[str, Any]) -> Dict[str, Any]:
    docs = rag_search(rag.vectorstore, query="ABCDE red flags triage assessment vitals", k=4)
    context = _format_rag_context(docs)
    mcp_context = get_report_mcp_context(report_text, include_checklist=True)
    mcp_context["scenario_context"] = scenario_context_mcp.get_scenario(report_text)
    mcp_context["guidelines_context"] = medical_guidelines_mcp.get_context_string(report_text, k=3)
    mcp_history = session_memory_mcp.get_context_string(session_id)

    user_payload = {
        "report_text": report_text,
        "review": review_json,
        "rag_context": context,
        "memory": mcp_history,
        "mcp": mcp_context,
    }

    parser = JsonOutputParser(pydantic_object=PatientEvaluation)
    prompt = ChatPromptTemplate.from_messages(
        [
            SystemMessage(content=PATIENT_EVAL_SYSTEM_PROMPT),
            ("human", "{payload}\n\nReturn only JSON."),
        ]
    )
    chain = prompt | _chat() | parser
    data = chain.invoke({"payload": json.dumps(user_payload, ensure_ascii=False)})
    if hasattr(data, "model_dump"):
        raw = data.model_dump()
    else:
        raw = dict(data)
    raw["suspected_problems"] = filter_temperature_labels(report_text, raw.get("suspected_problems", []))
    raw["red_flags"] = filter_temperature_labels(report_text, raw.get("red_flags", []))
    session_store.append(session_id, "assistant", json.dumps(raw, ensure_ascii=False)[:8000])
    return raw


def chat_doctor_turn(rag: RagDeps, session_id: str, report_text: str, user_message: str = "") -> Dict[str, Any]:
    state = get_state(session_id)
    trimmed_user = user_message.strip()
    if trimmed_user and state.pending_questions:
        answered = normalize_question(state.pending_questions.pop(0))
        state.answered_keys.add(answered)

    docs = rag_search(rag.vectorstore, query="maritime remote medicine concise next step and focused questions", k=2)
    context = _format_rag_context(docs)
    mcp_context = get_report_mcp_context(report_text, include_checklist=True)
    mcp_context["scenario_context"] = scenario_context_mcp.get_scenario(report_text)
    mcp_context["guidelines_context"] = medical_guidelines_mcp.get_context_string(report_text, k=2)
    memory = session_memory_mcp.get_context_string(session_id)

    payload = {
        "report_text": report_text,
        "latest_user_message": trimmed_user,
        "pending_questions": state.pending_questions,
        "answered_question_keys": sorted(state.answered_keys),
        "memory": memory,
        "rag_context": context,
        "mcp": mcp_context,
    }

    parser = JsonOutputParser(pydantic_object=ChatDoctorResult)
    prompt = ChatPromptTemplate.from_messages(
        [
            SystemMessage(content=CHAT_DOCTOR_SYSTEM_PROMPT),
            ("human", "{payload}\n\nReturn only JSON."),
        ]
    )
    chain = prompt | _chat() | parser
    data = chain.invoke({"payload": json.dumps(payload, ensure_ascii=False)})

    raw = data.model_dump() if hasattr(data, "model_dump") else dict(data)
    suggested_questions = [str(q).strip() for q in raw.get("questions_for_participants", []) if str(q).strip()]
    deduped_new: list[str] = []
    for q in suggested_questions:
        key = normalize_question(q)
        if key in state.asked_keys or key in state.answered_keys:
            continue
        state.asked_keys.add(key)
        deduped_new.append(q)
    state.pending_questions.extend(deduped_new)

    if trimmed_user:
        session_store.append(session_id, "user", trimmed_user[:4000])
    session_store.append(session_id, "assistant", str(raw.get("assistant_message", ""))[:4000])

    return {
        "assistant_message": str(raw.get("assistant_message", "")).strip(),
        "questions_for_participants": deduped_new,
        "pending_questions": list(state.pending_questions),
        "can_finalize_summary": len(state.pending_questions) == 0,
    }
