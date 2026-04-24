from rmrr_mcp.medical_mcp_server import checklist_missing_sections, extract_vitals, triage_priority


def test_checklist_missing_sections_basic():
    text = "Name: John. Ship: Test. Breathing rate 18. SpO2 96%. Blood pressure 120/80."
    out = checklist_missing_sections(text)
    assert "present" in out and "missing" in out
    assert "breathing" in out["present"]


def test_extract_vitals_parses_bp_and_spo2():
    text = "Oxygen saturation 91%. Blood pressure: 85/55. Heart rate 130."
    vitals = extract_vitals(text)
    assert vitals["spo2_percent"] == 91
    assert vitals["bp_systolic"] == 85
    assert vitals["bp_diastolic"] == 55
    assert vitals["heart_rate_bpm"] == 130


def test_triage_priority_marks_critical():
    out = triage_priority({"spo2_percent": 90, "bp_systolic": 80})
    assert out["priority"] == "critical"

