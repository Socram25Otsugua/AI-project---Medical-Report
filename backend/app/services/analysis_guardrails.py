from __future__ import annotations

import re
from typing import Any, Dict, List


def _has_labeled_value(report_text: str, labels: list[str]) -> bool:
    for label in labels:
        m = re.search(rf"{label}(?:[^:\n]){{0,48}}:\s*(.+)", report_text, re.IGNORECASE)
        if not m:
            continue
        if m.group(1).strip():
            return True
    return False


def _extract_temp_c(report_text: str) -> float | None:
    m = re.search(r"(temp|temperature)[^0-9]{0,24}(\d{2}(?:[.,]\d)?)", report_text, re.IGNORECASE)
    if not m:
        return None
    return float(m.group(2).replace(",", "."))


def _report_signals(report_text: str) -> Dict[str, bool]:
    return {
        "shipping_company": _has_labeled_value(report_text, [r"shipping company"]),
        "nearest_port_eta": _has_labeled_value(
            report_text,
            [r"nearest port(?: and eta)?", r"nearest port\s*/\s*eta"],
        ),
        "jaw_lift_performed": _has_labeled_value(report_text, [r"jaw lift performed"]),
        "oxygen_flow_rate": _has_labeled_value(
            report_text,
            [r"oxygen administered", r"oxygen", r"obs_oxygen_l_min", r"oxygen flow", r"oxygen liters/min"],
        ),
        "breathing_frequency": _has_labeled_value(
            report_text,
            [r"breathing frequency", r"breathing rate", r"respiratory rate"],
        ),
        "heart_rate": _has_labeled_value(report_text, [r"heart rate", r"pulse"]),
        "spo2": _has_labeled_value(report_text, [r"spo2", r"oxygen saturation"]),
        "blood_pressure": _has_labeled_value(report_text, [r"blood pressure", r"bp systolic", r"bp diastolic"]),
        "temperature": _has_labeled_value(
            report_text,
            [r"temperature", r"temp\. measured", r"temp \(mouth\)", r"temp_mouth"],
        ),
        "consciousness": _has_labeled_value(
            report_text,
            [r"level of consciousness", r"consciousness \(1", r"avpu", r"gcs"],
        ),
        "pupil_reaction_description": _has_labeled_value(
            report_text,
            [r"if abnormal:\s*describe", r"pupil reaction description", r"pupil reaction \(normal"],
        ),
    }


def _should_drop_contradictory_text(text: str, signals: Dict[str, bool]) -> bool:
    t = text.lower()
    if signals["shipping_company"] and "shipping company" in t and any(k in t for k in ["missing", "not provided"]):
        return True
    if signals["nearest_port_eta"] and "nearest port" in t and any(k in t for k in ["missing", "not provided"]):
        return True
    if signals["jaw_lift_performed"] and "jaw lift" in t and any(k in t for k in ["method", "time", "timestamp"]):
        return True
    if (signals["oxygen_flow_rate"] or signals["breathing_frequency"]) and any(
        k in t for k in ["oxygen flow", "flow rate"]
    ) and any(k in t for k in ["missing", "not documented", "no mention", "what is", "please provide", "record"]):
        return True
    if signals["pupil_reaction_description"] and "pupil" in t and any(
        k in t for k in ["missing", "not described", "no description"]
    ):
        return True
    if signals["heart_rate"] and any(k in t for k in ["heart rate", "pulse"]) and any(
        k in t for k in ["what is", "please provide", "record", "missing", "not documented", "current"]
    ):
        return True
    if signals["spo2"] and "spo2" in t and any(
        k in t for k in ["what is", "please provide", "record", "missing", "not documented", "current", "oxygen saturation"]
    ):
        return True
    if signals["breathing_frequency"] and any(k in t for k in ["breathing", "respiratory"]) and any(
        k in t for k in ["what is", "please provide", "record", "missing", "not documented", "current"]
    ):
        return True
    if signals["blood_pressure"] and "blood pressure" in t and any(
        k in t for k in ["what is", "please provide", "record", "missing", "not documented", "current"]
    ):
        return True
    if signals["temperature"] and "temperature" in t and any(
        k in t for k in ["what is", "please provide", "record", "missing", "not documented", "current", "temp"]
    ):
        return True
    if signals["consciousness"] and "consciousness" in t and any(
        k in t for k in ["what is", "please provide", "record", "missing", "not documented", "current", "avpu", "gcs"]
    ):
        return True
    return False


def filter_deficiencies(report_text: str, deficiencies: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    signals = _report_signals(report_text)
    filtered: List[Dict[str, Any]] = []
    for item in deficiencies:
        issue = str(item.get("issue", ""))
        suggestion = str(item.get("suggestion", ""))
        if _should_drop_contradictory_text(f"{issue}\n{suggestion}", signals):
            continue
        filtered.append(item)
    return filtered


def filter_questions(report_text: str, questions: List[str]) -> List[str]:
    signals = _report_signals(report_text)
    filtered: List[str] = []
    for q in questions:
        if _should_drop_contradictory_text(str(q), signals):
            continue
        filtered.append(str(q))
    return filtered


def filter_temperature_labels(report_text: str, items: List[str]) -> List[str]:
    temp_c = _extract_temp_c(report_text)
    if temp_c is None:
        return [str(x) for x in items]

    filtered: List[str] = []
    for raw in items:
        text = str(raw)
        lower = text.lower()
        if temp_c >= 35 and "hypothermia" in lower:
            continue
        filtered.append(text)
    return filtered
