from app.services.analysis_guardrails import filter_deficiencies, filter_questions, filter_temperature_labels


def test_filter_deficiencies_removes_contradictions_for_present_fields():
    report = """
    - Shipping company: LEGO
    - Nearest port and ETA: Esbjerg
    - Jaw lift performed: Yes
    - Breathing frequency: 16 /min
    - If abnormal: describe: slow and lost
    """
    deficiencies = [
        {
            "area": "Ship / contact context",
            "issue": "Missing nearest port and ETA",
            "severity": "medium",
            "suggestion": "Ask for nearest port.",
        },
        {
            "area": "Airway",
            "issue": "Jaw lift performed but no mention of jaw lift method or time",
            "severity": "low",
            "suggestion": "Specify jaw lift method and time",
        },
        {
            "area": "Disability",
            "issue": "No description of abnormal pupil reaction",
            "severity": "high",
            "suggestion": "Describe abnormal pupil reaction.",
        },
    ]
    out = filter_deficiencies(report, deficiencies)
    assert out == []


def test_filter_questions_removes_oxygen_flow_prompt_when_rr_present():
    report = "- Breathing frequency: 18 /min"
    questions = ["What is the oxygen flow rate?", "Any chest pain?"]
    out = filter_questions(report, questions)
    assert out == ["Any chest pain?"]


def test_filter_temperature_labels_removes_hypothermia_for_high_temp():
    report = "- Temperature (mouth): 39 C"
    out = filter_temperature_labels(report, ["Possible hypothermia", "Fever likely"])
    assert out == ["Fever likely"]
