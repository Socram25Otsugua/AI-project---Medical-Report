from __future__ import annotations

import json
from typing import Any, Dict, List

from langchain_core.messages import HumanMessage, SystemMessage
from langchain_core.output_parsers import JsonOutputParser
from langchain_core.prompts import ChatPromptTemplate
from langchain_ollama import ChatOllama

from app.memory import session_store
from app.prompts import PATIENT_EVAL_SYSTEM_PROMPT, RESPONSE_SYSTEM_PROMPT, REVIEW_SYSTEM_PROMPT
from app.rag import RagDeps, rag_search
from app.settings import settings
from app.tools import make_rag_lookup_tool, mcp_checklist_missing_sections, mcp_extract_vitals, mcp_triage_priority
from app.schemas import PatientEvaluation, ResponseResult, ReviewResult


def _chat() -> ChatOllama:
    return ChatOllama(
        model=settings.ollama_model,
        base_url=settings.ollama_base_url,
        temperature=settings.ollama_temperature,
    )


def _format_rag_context(docs: List[Any]) -> str:
    if not docs:
        return ""
    parts = []
    for d in docs:
        src = d.metadata.get("source", "unknown")
        parts.append(f"[source: {src}]\n{d.page_content}".strip())
    return "\n\n---\n\n".join(parts)


def review_report(rag: RagDeps, session_id: str, report_text: str) -> Dict[str, Any]:
    # Memory: include last assistant output to keep style consistent (lightweight).
    history = session_store.get(session_id)[-6:]
    memory_snippet = "\n".join([f"{t.role}: {t.content}" for t in history]) if history else ""

    # Tools (MCP) to enrich context before the LLM.
    missing = mcp_checklist_missing_sections.invoke({"report_text": report_text})
    vitals = mcp_extract_vitals.invoke({"report_text": report_text})
    triage = mcp_triage_priority.invoke({"vitals": vitals})

    docs = rag_search(rag.vectorstore, query="Radio Medical Record checklist ABCDE vitals history actions", k=4)
    context = _format_rag_context(docs)

    user_payload = {
        "report_text": report_text,
        "memory": memory_snippet,
        "rag_context": context,
        "mcp": {"missing_sections": missing, "vitals": vitals, "triage": triage},
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
    session_store.append(session_id, "user", report_text[:8000])
    session_store.append(session_id, "assistant", json.dumps(data, ensure_ascii=False)[:8000])
    return data


def generate_next_step(rag: RagDeps, session_id: str, report_text: str, review_json: Dict[str, Any]) -> Dict[str, Any]:
    docs = rag_search(rag.vectorstore, query="ABCDE stabilization escalation guidance questions", k=4)
    context = _format_rag_context(docs)

    user_payload = {
        "report_text": report_text,
        "review": review_json,
        "rag_context": context,
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
    session_store.append(session_id, "assistant", json.dumps(data, ensure_ascii=False)[:8000])
    return data


def evaluate_patient(rag: RagDeps, session_id: str, report_text: str, review_json: Dict[str, Any]) -> Dict[str, Any]:
    docs = rag_search(rag.vectorstore, query="ABCDE red flags triage assessment vitals", k=4)
    context = _format_rag_context(docs)

    vitals = mcp_extract_vitals.invoke({"report_text": report_text})
    triage = mcp_triage_priority.invoke({"vitals": vitals})

    user_payload = {
        "report_text": report_text,
        "review": review_json,
        "rag_context": context,
        "mcp": {"vitals": vitals, "triage": triage},
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
    session_store.append(session_id, "assistant", json.dumps(data, ensure_ascii=False)[:8000])
    return data

