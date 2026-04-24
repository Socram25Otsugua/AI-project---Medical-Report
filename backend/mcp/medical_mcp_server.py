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


def _presence(report_text: str, patterns: List[str]) -> bool:
    t = report_text.lower()
    return any(re.search(p, t) for p in patterns)


@mcp.tool
def checklist_missing_sections(report_text: str) -> Dict[str, Any]:
    """Heurística rápida: devolve secções possivelmente em falta no texto do relatório."""
    missing = []
    present = []
    for section, pats in _FIELD_HINTS:
        if _presence(report_text, pats):
            present.append(section)
        else:
            missing.append(section)
    return {"present": present, "missing": missing}


@mcp.tool
def extract_vitals(report_text: str) -> Dict[str, Any]:
    """Extrai vitais aproximados por regex (bpm/TA/SpO2/FR/Temp)."""
    t = report_text
    out: Dict[str, Any] = {}

    # BPM
    m = re.search(r"(pulse|hr|heart rate)[^0-9]{0,10}(\d{2,3})", t, re.IGNORECASE)
    if m:
        out["heart_rate_bpm"] = int(m.group(2))

    # SpO2
    m = re.search(r"(spo2|oxygen saturation)[^0-9]{0,10}(\d{2,3})\s*%?", t, re.IGNORECASE)
    if m:
        out["spo2_percent"] = int(m.group(2))

    # RR
    m = re.search(r"(breath(ing)? rate|rr|breaths per min)[^0-9]{0,10}(\d{1,2})", t, re.IGNORECASE)
    if m:
        out["resp_rate_per_min"] = int(m.group(3))

    # BP
    m = re.search(r"(blood pressure|bp)[^0-9]{0,10}(\d{2,3})\s*/\s*(\d{2,3})", t, re.IGNORECASE)
    if m:
        out["bp_systolic"] = int(m.group(2))
        out["bp_diastolic"] = int(m.group(3))

    # Temp
    m = re.search(r"(temp|temperature)[^0-9]{0,10}(\d{2})[.,](\d)", t, re.IGNORECASE)
    if m:
        out["temp_c"] = float(f"{m.group(2)}.{m.group(3)}")

    return out


@mcp.tool
def triage_priority(vitals: Dict[str, Any]) -> Dict[str, Any]:
    """Classifica prioridade (heurística) com base em vitais conhecidos."""
    hr = vitals.get("heart_rate_bpm")
    spo2 = vitals.get("spo2_percent")
    sys = vitals.get("bp_systolic")
    rr = vitals.get("resp_rate_per_min")

    risk = []
    if spo2 is not None and spo2 < 92:
        risk.append("low_spo2")
    if sys is not None and sys < 90:
        risk.append("hypotension")
    if rr is not None and (rr < 8 or rr > 30):
        risk.append("abnormal_rr")
    if hr is not None and (hr < 50 or hr > 120):
        risk.append("abnormal_hr")

    level: Literal["routine", "urgent", "critical"] = "routine"
    if any(x in risk for x in ["hypotension", "low_spo2"]):
        level = "critical"
    elif risk:
        level = "urgent"

    return {"priority": level, "risk_markers": risk}


if __name__ == "__main__":
    mcp.run()

