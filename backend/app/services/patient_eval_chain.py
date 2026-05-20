from __future__ import annotations

import json
from typing import Any, Dict

from langchain_core.messages import SystemMessage
from langchain_core.output_parsers import JsonOutputParser
from langchain_core.prompts import ChatPromptTemplate

from app.mcp import get_report_mcp_context, medical_guidelines_mcp, scenario_context_mcp, session_memory_mcp
from app.models.schemas import PatientEvaluation
from app.prompts import PATIENT_EVAL_SYSTEM_PROMPT
from app.services.analysis_guardrails import filter_temperature_labels
from app.services.common_chain import build_chat_model, format_rag_context
from app.tools.memory import session_store
from app.tools.rag import RagDeps, rag_search


def evaluate_patient(rag: RagDeps, session_id: str, report_text: str, review_json: Dict[str, Any]) -> Dict[str, Any]:
    docs = rag_search(rag.vectorstore, query="ABCDE red flags triage assessment vitals", k=4)
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

    parser = JsonOutputParser(pydantic_object=PatientEvaluation)
    prompt = ChatPromptTemplate.from_messages(
        [
            SystemMessage(content=PATIENT_EVAL_SYSTEM_PROMPT),
            ("human", "{payload}\n\nReturn only JSON."),
        ]
    )
    chain = prompt | build_chat_model() | parser
    data = chain.invoke({"payload": json.dumps(user_payload, ensure_ascii=False)})
    if hasattr(data, "model_dump"):
        raw = data.model_dump()
    else:
        raw = dict(data)

    # Defensive normalization: guarantee schema required by endpoint response model.
    if raw.get("status") not in {"ok", "concerning", "critical", "unknown"}:
        raw["status"] = "unknown"
    if not isinstance(raw.get("summary"), str) or not str(raw.get("summary")).strip():
        raw["summary"] = "Insufficient structured evidence for a definitive status. Continue reassessment."
    if not isinstance(raw.get("suspected_problems"), list):
        raw["suspected_problems"] = []
    if not isinstance(raw.get("red_flags"), list):
        raw["red_flags"] = []

    raw["suspected_problems"] = filter_temperature_labels(report_text, raw.get("suspected_problems", []))
    raw["red_flags"] = filter_temperature_labels(report_text, raw.get("red_flags", []))
    session_store.append(session_id, "assistant", json.dumps(raw, ensure_ascii=False)[:8000])
    return raw
