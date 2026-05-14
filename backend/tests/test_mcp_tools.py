from rmrr_mcp.medical_mcp_server import checklist_missing_sections, extract_vitals, triage_priority


def test_checklist_missing_sections_basic():
    text = "Name: John. Ship: Test. Breathing rate 18. SpO2 96%. Blood pressure 120/80."
    out = checklist_missing_sections(text)
    assert "present" in out and "missing" in out
    assert "breathing" in out["present"]
    assert "field_presence" in out


def test_extract_vitals_parses_bp_and_spo2():
    text = "Oxygen saturation 91%. Blood pressure: 85/55. Heart rate 130."
    vitals = extract_vitals(text)
    assert vitals["spo2_percent"] == 91
    assert vitals["bp_systolic"] == 85
    assert vitals["bp_diastolic"] == 55
    assert vitals["heart_rate_bpm"] == 130


def test_extract_vitals_parses_rr_frequency_and_split_bp_fields():
    text = "Breathing frequency /min: 16. Blood pressure systolic mmHg: 115. Blood pressure diastolic mmHg: 84."
    vitals = extract_vitals(text)
    assert vitals["resp_rate_per_min"] == 16
    assert vitals["bp_systolic"] == 115
    assert vitals["bp_diastolic"] == 84


def test_extract_vitals_parses_integer_temperature():
    text = "Temperature (mouth) 39 C."
    vitals = extract_vitals(text)
    assert vitals["temp_c"] == 39.0


def test_triage_priority_marks_critical():
    out = triage_priority({"spo2_percent": 90, "bp_systolic": 80})
    assert out["priority"] == "critical"


def test_checklist_presence_detects_ship_and_airway_details():
    text = """
    - Shipping company: LEGO
    - Nearest port and ETA: Esbjerg, 4h
    - Jaw lift performed: Yes
    - Breathing frequency: 16 /min
    - If abnormal: describe: slow and lost
    """
    out = checklist_missing_sections(text)
    fp = out["field_presence"]
    assert fp["shipping_company"] is True
    assert fp["nearest_port_eta"] is True
    assert fp["jaw_lift_performed"] is True
    assert fp["breathing_frequency"] is True
    assert fp["pupil_reaction_description"] is True


def test_triage_priority_marks_temperature_ranges():
    fever = triage_priority({"temp_c": 39.0})
    hypo = triage_priority({"temp_c": 34.2})
    assert "fever_or_hyperthermia" in fever["risk_markers"]
    assert "possible_hypothermia" in hypo["risk_markers"]

