from __future__ import annotations

import json
import re
from typing import Any, Dict

from langchain_core.messages import SystemMessage
from langchain_core.output_parsers import JsonOutputParser
from langchain_core.prompts import ChatPromptTemplate

from app.mcp import get_report_mcp_context, medical_guidelines_mcp, scenario_context_mcp, session_memory_mcp
from app.models.schemas import ResponseResult
from app.prompts import RESPONSE_SYSTEM_PROMPT
from app.services.analysis_guardrails import filter_questions, filter_temperature_labels
from app.services.common_chain import build_chat_model, format_rag_context
from app.tools.memory import session_store
from app.tools.rag import RagDeps, rag_search


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


def generate_next_step(rag: RagDeps, session_id: str, report_text: str, review_json: Dict[str, Any]) -> Dict[str, Any]:
    docs = rag_search(rag.vectorstore, query="ABCDE stabilization escalation guidance questions", k=4)
    context = format_rag_context(docs)
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
    chain = prompt | build_chat_model() | parser
    data = chain.invoke({"payload": json.dumps(user_payload, ensure_ascii=False)})
    raw: Dict[str, Any]
    if hasattr(data, "model_dump"):
        raw = data.model_dump()
    else:
        raw = dict(data)

    # Defensive normalization: some models can drift into review-style JSON.
    if not isinstance(raw.get("next_step_message"), str) or not str(raw.get("next_step_message")).strip():
        raw["next_step_message"] = (
            "Continue ABCDE reassessment, stabilize current abnormalities, and document the next set of observations."
        )
    if not isinstance(raw.get("rationale_bullets"), list):
        raw["rationale_bullets"] = []
    if not isinstance(raw.get("questions_for_participants"), list):
        raw["questions_for_participants"] = []

    raw["questions_for_participants"] = _filter_redundant_questions(
        report_text, raw.get("questions_for_participants", [])
    )
    raw["questions_for_participants"] = filter_questions(report_text, raw.get("questions_for_participants", []))
    raw["rationale_bullets"] = filter_temperature_labels(report_text, raw.get("rationale_bullets", []))
    session_store.append(session_id, "assistant", json.dumps(raw, ensure_ascii=False)[:8000])
    return raw
