from __future__ import annotations

from typing import Any, Dict

from app.mcp.context import get_report_mcp_context, vitals_coverage_feedback, vitals_coverage_score
from app.mcp.medical_guidelines_mcp import medical_guidelines_mcp
from app.mcp.scenario_context_mcp import detect_scenario, scenario_context_mcp
from app.mcp.session_memory_mcp import session_memory_mcp


def build_enriched_mcp_context(report_text: str, *, include_checklist: bool = True) -> Dict[str, Any]:
    mcp_context = get_report_mcp_context(report_text, include_checklist=include_checklist)
    mcp_context["scenario_context"] = scenario_context_mcp.get_scenario(report_text)
    mcp_context["guidelines_context"] = medical_guidelines_mcp.get_context_string(report_text, k=3)
    return mcp_context


__all__ = [
    "build_enriched_mcp_context",
    "detect_scenario",
    "get_report_mcp_context",
    "medical_guidelines_mcp",
    "scenario_context_mcp",
    "session_memory_mcp",
    "vitals_coverage_feedback",
    "vitals_coverage_score",
]
