from __future__ import annotations

from typing import Any, Dict

from langchain_core.tools import tool

from tools.mcp_client import call_mcp_tool_sync


@tool
def mcp_checklist_missing_sections(report_text: str) -> Dict[str, Any]:
    """MCP: identify sections that may be missing in the report."""
    return call_mcp_tool_sync("checklist_missing_sections", {"report_text": report_text})


@tool
def mcp_extract_vitals(report_text: str) -> Dict[str, Any]:
    """MCP: extract approximate vital signs (regex)."""
    return call_mcp_tool_sync("extract_vitals", {"report_text": report_text})


@tool
def mcp_triage_priority(vitals: Dict[str, Any]) -> Dict[str, Any]:
    """MCP: classify priority from vital signs."""
    return call_mcp_tool_sync("triage_priority", {"vitals": vitals})
