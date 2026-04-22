from __future__ import annotations

from typing import Any, Dict, List

from langchain_core.tools import tool

from app.mcp_client import call_mcp_tool_sync
from app.rag import RagDeps, rag_search


@tool
def mcp_checklist_missing_sections(report_text: str) -> Dict[str, Any]:
    """MCP: identifica secções possivelmente em falta no relatório."""
    return call_mcp_tool_sync("checklist_missing_sections", {"report_text": report_text})


@tool
def mcp_extract_vitals(report_text: str) -> Dict[str, Any]:
    """MCP: extrai vitais aproximados (regex)."""
    return call_mcp_tool_sync("extract_vitals", {"report_text": report_text})


@tool
def mcp_triage_priority(vitals: Dict[str, Any]) -> Dict[str, Any]:
    """MCP: classifica prioridade a partir de vitais."""
    return call_mcp_tool_sync("triage_priority", {"vitals": vitals})


def make_rag_lookup_tool(rag: RagDeps):
    @tool
    def rag_lookup(query: str) -> Dict[str, Any]:
        """RAG: pesquisa na base de conhecimento local e devolve excertos com source."""
        docs = rag_search(rag.vectorstore, query=query, k=4)
        return {
            "results": [
                {"source": d.metadata.get("source", "unknown"), "text": d.page_content[:2000]}
                for d in docs
            ]
        }

    return rag_lookup

