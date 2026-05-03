from __future__ import annotations

import json
from dataclasses import dataclass
from typing import Any, Dict, List

from langchain.agents import AgentExecutor, create_tool_calling_agent
from langchain_core.messages import SystemMessage
from langchain_core.output_parsers import JsonOutputParser
from langchain_core.prompts import ChatPromptTemplate, MessagesPlaceholder
from langchain_ollama import ChatOllama

from agents.tools import make_rag_lookup_tool, mcp_checklist_missing_sections, mcp_extract_vitals, mcp_triage_priority
from app.mcp import vitals_coverage_feedback, vitals_coverage_score
from app.prompts import PATIENT_EVAL_SYSTEM_PROMPT, RESPONSE_SYSTEM_PROMPT, REVIEW_SYSTEM_PROMPT
from app.settings import settings
from models.schemas import AnalyzeResult, PatientEvaluation, ResponseResult, ReviewResult
from tools.memory import session_store
from tools.rag import RagDeps, rag_search


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


def _parse_agent_json_output(output: Any) -> Dict[str, Any]:
    if isinstance(output, dict):
        return output
    if isinstance(output, str):
        try:
            return json.loads(output)
        except json.JSONDecodeError as exc:
            raise ValueError("Agent output is not valid JSON.") from exc
    raise ValueError("Agent output has unsupported type.")


@dataclass
class ReportAgent:
    rag: RagDeps

    def _build_agent_executor(self, system_prompt: str) -> AgentExecutor:
        tools = [
            mcp_checklist_missing_sections,
            mcp_extract_vitals,
            mcp_triage_priority,
            make_rag_lookup_tool(self.rag),
        ]
        prompt = ChatPromptTemplate.from_messages(
            [
                ("system", system_prompt),
                ("human", "{input}"),
                MessagesPlaceholder("agent_scratchpad"),
            ]
        )
        agent = create_tool_calling_agent(_chat(), tools, prompt)
        return AgentExecutor(agent=agent, tools=tools, verbose=False)

    def _invoke_chain(self, system_prompt: str, schema: type, payload: Dict[str, Any]) -> Dict[str, Any]:
        parser = JsonOutputParser(pydantic_object=schema)
        prompt = ChatPromptTemplate.from_messages(
            [
                SystemMessage(content=system_prompt),
                ("human", "{payload}\n\nReturn only JSON."),
            ]
        )
        chain = prompt | _chat() | parser
        return chain.invoke({"payload": json.dumps(payload, ensure_ascii=False)})

    def _invoke_agent_with_fallback(self, system_prompt: str, schema: type, payload: Dict[str, Any]) -> Dict[str, Any]:
        try:
            executor = self._build_agent_executor(system_prompt)
            result = executor.invoke(
                {
                    "input": (
                        "Use available tools when needed, then return only JSON.\n\n"
                        f"{json.dumps(payload, ensure_ascii=False)}"
                    )
                }
            )
            return _parse_agent_json_output(result.get("output"))
        except Exception:
            # Fallback keeps behavior stable when local model/tool-calling is unavailable.
            return self._invoke_chain(system_prompt, schema, payload)

    def review_report(self, session_id: str, report_text: str) -> Dict[str, Any]:
        history = session_store.get(session_id)[-6:]
        memory_snippet = "\n".join([f"{t.role}: {t.content}" for t in history]) if history else ""
        docs = rag_search(self.rag.vectorstore, query="Radio Medical Record checklist ABCDE vitals history actions", k=4)
        context = _format_rag_context(docs)
        user_payload = {"report_text": report_text, "memory": memory_snippet, "rag_context": context}

        data = self._invoke_agent_with_fallback(REVIEW_SYSTEM_PROMPT, ReviewResult, user_payload)
        raw: Dict[str, Any]
        if hasattr(data, "model_dump"):
            raw = data.model_dump()
        else:
            raw = dict(data)
        vitals = mcp_extract_vitals.invoke({"report_text": report_text})
        raw["vitals_score"] = vitals_coverage_score(vitals)
        raw["vitals_feedback"] = vitals_coverage_feedback(vitals)
        session_store.append(session_id, "user", report_text[:8000])
        session_store.append(session_id, "assistant", json.dumps(raw, ensure_ascii=False)[:8000])
        return raw

    def generate_next_step(self, session_id: str, report_text: str, review_json: Dict[str, Any]) -> Dict[str, Any]:
        docs = rag_search(self.rag.vectorstore, query="ABCDE stabilization escalation guidance questions", k=4)
        context = _format_rag_context(docs)
        user_payload = {"report_text": report_text, "review": review_json, "rag_context": context}

        data = self._invoke_agent_with_fallback(RESPONSE_SYSTEM_PROMPT, ResponseResult, user_payload)
        session_store.append(session_id, "assistant", json.dumps(data, ensure_ascii=False)[:8000])
        return data

    def evaluate_patient(self, session_id: str, report_text: str, review_json: Dict[str, Any]) -> Dict[str, Any]:
        docs = rag_search(self.rag.vectorstore, query="ABCDE red flags triage assessment vitals", k=4)
        context = _format_rag_context(docs)
        user_payload = {"report_text": report_text, "review": review_json, "rag_context": context}

        data = self._invoke_agent_with_fallback(PATIENT_EVAL_SYSTEM_PROMPT, PatientEvaluation, user_payload)
        session_store.append(session_id, "assistant", json.dumps(data, ensure_ascii=False)[:8000])
        return data

    def analyze(self, session_id: str, report_text: str) -> Dict[str, Any]:
        review = self.review_report(session_id=session_id, report_text=report_text)
        response = self.generate_next_step(session_id=session_id, report_text=report_text, review_json=review)
        patient_evaluation = self.evaluate_patient(session_id=session_id, report_text=report_text, review_json=review)
        return AnalyzeResult(review=review, response=response, patient_evaluation=patient_evaluation).model_dump()
