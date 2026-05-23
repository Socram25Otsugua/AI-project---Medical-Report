from __future__ import annotations

import re
from typing import Any, Dict, List, Literal

from fastmcp import FastMCP


mcp = FastMCP(name="radio-medical-mcp")


_FIELD_HINTS = [
    ("identity", [r"name", r"birth", r"gender", r"nationality", r"date", r"utc"]),
    ("ship_context", [r"ship", r"company", r"email", r"satellite", r"call signal", r"coordinates", r"eta", r"nearest port"]),
    ("airway", [r"airway", r"jaw lift", r"suction", r"guedel", r"cpr"]),
    ("breathing", [r"breathing", r"resp", r"spo2", r"oxygen", r"l/min", r"hudson", r"nasal cannula"]),
    ("circulation", [r"capillary", r"pulse", r"blood pressure", r"skin", r"venous"]),
    ("disability", [r"conscious", r"pupil", r"convulsion", r"paralysis"]),
    ("exposure", [r"top to toe", r"hypothermia", r"overheating", r"temperature"]),
    ("problem_description", [r"what has happened", r"symptoms", r"where", r"when"]),
    ("actions_meds", [r"performed", r"medication", r"fluid", r"iv", r"cannula"]),
]

_STRUCTURED_FIELDS = {
    "shipping_company": [r"shipping company"],
    "nearest_port_eta": [r"nearest port(?: and eta)?", r"nearest port\s*/\s*eta"],
    "jaw_lift_performed": [r"jaw lift performed"],
    "oxygen_flow_rate": [r"oxygen administered", r"oxygen(?:\s+\(?.*?\)?)?\s*:\s*[\d.,]+\s*l/min"],
    "breathing_frequency": [r"breathing frequency", r"breathing rate", r"respiratory rate"],
    "pupil_reaction_normal": [r"pupil reaction normal"],
    "pupil_reaction_description": [r"if abnormal:\s*describe", r"pupil reaction"],
}


def _structured_value_present(report_text: str, label_patterns: List[str]) -> bool:
    for p in label_patterns:
        m = re.search(rf"{p}\s*:\s*(.+)", report_text, re.IGNORECASE)
        if not m:
            continue
        value = m.group(1).strip()
        if value:
            return True
    return False


def _extract_structured_presence(report_text: str) -> Dict[str, bool]:
    return {key: _structured_value_present(report_text, pats) for key, pats in _STRUCTURED_FIELDS.items()}


def _presence(report_text: str, patterns: List[str]) -> bool:
    t = report_text.lower()
    return any(re.search(p, t) for p in patterns)


@mcp.tool
def checklist_missing_sections(report_text: str) -> Dict[str, Any]:
    """Quick heuristic: return sections that may be missing from report text."""
    missing = []
    present = []
    for section, pats in _FIELD_HINTS:
        if _presence(report_text, pats):
            present.append(section)
        else:
            missing.append(section)
    return {
        "present": present,
        "missing": missing,
        "field_presence": _extract_structured_presence(report_text),
    }


@mcp.tool
def extract_vitals(report_text: str) -> Dict[str, Any]:
    """Extract approximate vital signs via regex (bpm/BP/SpO2/RR/Temp)."""
    t = report_text
    out: Dict[str, Any] = {}

    # Heart rate (BPM)
    m = re.search(r"(pulse|hr|heart rate)[^0-9]{0,10}(\d{2,3})", t, re.IGNORECASE)
    if m:
        out["heart_rate_bpm"] = int(m.group(2))

    # SpO2
    m = re.search(r"(spo2|oxygen saturation)[^0-9]{0,10}(\d{2,3})\s*%?", t, re.IGNORECASE)
    if m:
        out["spo2_percent"] = int(m.group(2))

    # RR (accept "breathing frequency" from form rendering)
    m = re.search(r"(breath(ing)? rate|breathing frequency|rr|breaths per min)[^0-9]{0,16}(\d{1,2})", t, re.IGNORECASE)
    if m:
        out["resp_rate_per_min"] = int(m.group(3))

    # BP as ratio (e.g., BP 120/80)
    m = re.search(r"(blood pressure|bp)[^0-9]{0,10}(\d{2,3})\s*/\s*(\d{2,3})", t, re.IGNORECASE)
    if m:
        out["bp_systolic"] = int(m.group(2))
        out["bp_diastolic"] = int(m.group(3))

    # BP from split fields (e.g., "Blood pressure systolic: 115", "Blood pressure diastolic: 84")
    if "bp_systolic" not in out:
        m = re.search(r"blood pressure systolic[^0-9]{0,16}(\d{2,3})", t, re.IGNORECASE)
        if m:
            out["bp_systolic"] = int(m.group(1))
    if "bp_diastolic" not in out:
        m = re.search(r"blood pressure diastolic[^0-9]{0,16}(\d{2,3})", t, re.IGNORECASE)
        if m:
            out["bp_diastolic"] = int(m.group(1))

    # Temp (accept integer like 39 and decimal like 36.7)
    m = re.search(r"(temp|temperature)[^0-9]{0,24}(\d{2}(?:[.,]\d)?)", t, re.IGNORECASE)
    if m:
        out["temp_c"] = float(m.group(2).replace(",", "."))

    return out


@mcp.tool
def triage_priority(vitals: Dict[str, Any]) -> Dict[str, Any]:
    """Classify priority (heuristic) from known vital signs."""
    hr = vitals.get("heart_rate_bpm")
    spo2 = vitals.get("spo2_percent")
    sys = vitals.get("bp_systolic")
    rr = vitals.get("resp_rate_per_min")
    temp_c = vitals.get("temp_c")

    risk = []
    if spo2 is not None and spo2 < 92:
        risk.append("low_spo2")
    if sys is not None and sys < 90:
        risk.append("hypotension")
    if rr is not None and (rr < 8 or rr > 30):
        risk.append("abnormal_rr")
    if hr is not None and (hr < 50 or hr > 120):
        risk.append("abnormal_hr")
    if temp_c is not None and temp_c < 35:
        risk.append("possible_hypothermia")
    if temp_c is not None and temp_c >= 38:
        risk.append("fever_or_hyperthermia")

    level: Literal["routine", "urgent", "critical"] = "routine"
    if any(x in risk for x in ["hypotension", "low_spo2"]):
        level = "critical"
    elif risk:
        level = "urgent"

    return {"priority": level, "risk_markers": risk}


if __name__ == "__main__":
    mcp.run()

