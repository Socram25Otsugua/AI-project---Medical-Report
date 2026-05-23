from __future__ import annotations

import json
from typing import Any, Dict

from langchain_core.messages import SystemMessage
from langchain_core.output_parsers import JsonOutputParser
from langchain_core.prompts import ChatPromptTemplate

from app.mcp import (
    build_enriched_mcp_context,
    session_memory_mcp,
    vitals_coverage_feedback,
    vitals_coverage_score,
)
from app.models.schemas import ReviewResult
from app.prompts import FORM_REVIEW_SYSTEM_PROMPT
from app.services.analysis_guardrails import filter_deficiencies, filter_temperature_labels
from app.services.llm_chain_utils import build_chat_model, format_rag_context
from app.tools.memory import session_store
from app.tools.rag import RagDeps, rag_search


def analyze_form(rag: RagDeps, session_id: str, report_text: str) -> Dict[str, Any]:
    memory_snippet = session_memory_mcp.get_context_string(session_id)
    mcp_context = build_enriched_mcp_context(report_text, include_checklist=True)

    docs = rag_search(rag.vectorstore, query="Radio Medical Record checklist ABCDE vitals history actions", k=4)
    context = format_rag_context(docs)

    user_payload = {
        "report_text": report_text,
        "memory": memory_snippet,
        "rag_context": context,
        "mcp": mcp_context,
    }

    parser = JsonOutputParser(pydantic_object=ReviewResult)
    prompt = ChatPromptTemplate.from_messages(
        [
            SystemMessage(content=FORM_REVIEW_SYSTEM_PROMPT),
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
    raw["deficiencies"] = filter_deficiencies(report_text, raw.get("deficiencies", []))
    raw["safety_flags"] = filter_temperature_labels(report_text, raw.get("safety_flags", []))
    raw["vitals_score"] = vitals_coverage_score(mcp_context["vitals"])
    raw["vitals_feedback"] = vitals_coverage_feedback(mcp_context["vitals"])
    session_store.append(session_id, "user", report_text[:8000])
    session_store.append(session_id, "assistant", json.dumps(raw, ensure_ascii=False)[:8000])
    return raw
