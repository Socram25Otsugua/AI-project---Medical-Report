from __future__ import annotations

from typing import Any, Dict

from agents.tools.mcp_tools import mcp_checklist_missing_sections, mcp_extract_vitals, mcp_triage_priority


_VITAL_SLOTS = [
    ("heart_rate_bpm", "heart rate"),
    ("spo2_percent", "oxygen saturation (SpO2)"),
    ("resp_rate_per_min", "respiratory rate"),
    ("bp", "blood pressure"),
    ("temp_c", "temperature"),
]


def _has_vital_slot(vitals: Dict[str, Any], key: str) -> bool:
    if key == "bp":
        return vitals.get("bp_systolic") is not None and vitals.get("bp_diastolic") is not None
    return vitals.get(key) is not None


def vitals_coverage_score(vitals: Dict[str, Any]) -> int:
    """
    Map MCP extract_vitals coverage to 0–100 (five slots: HR, SpO2, RR, BP pair, temp).
    """
    slots = [_has_vital_slot(vitals, key) for key, _label in _VITAL_SLOTS]
    n = sum(slots)
    return round(100 * n / len(slots))


def vitals_coverage_feedback(vitals: Dict[str, Any]) -> list[str]:
    present = [label for key, label in _VITAL_SLOTS if _has_vital_slot(vitals, key)]
    missing = [label for key, label in _VITAL_SLOTS if not _has_vital_slot(vitals, key)]

    feedback: list[str] = []
    if present:
        feedback.append(f"Captured: {', '.join(present)}.")
    else:
        feedback.append("No key vitals were captured from the report text.")
    if missing:
        feedback.append(f"Missing: {', '.join(missing)}.")
        feedback.append("To improve the vitals score, add the missing measurements using clear labels and units.")
    if "blood pressure" in missing:
        feedback.append("Blood pressure counts only when both systolic and diastolic values are present, for example BP 120/80.")
    return feedback


def get_report_mcp_context(report_text: str, *, include_checklist: bool = True) -> Dict[str, Any]:
    """
    Build MCP-derived context from report text for orchestration payloads.

    This keeps MCP calls centralized so orchestrators can consistently enrich
    prompts with structured safety and completeness signals.
    """
    vitals = mcp_extract_vitals.invoke({"report_text": report_text})
    triage = mcp_triage_priority.invoke({"vitals": vitals})

    context: Dict[str, Any] = {"vitals": vitals, "triage": triage}
    if include_checklist:
        context["missing_sections"] = mcp_checklist_missing_sections.invoke({"report_text": report_text})

    return context
