from fastapi.testclient import TestClient

from app.main import app


def test_health():
    client = TestClient(app)
    r = client.get("/health")
    assert r.status_code == 200
    assert r.json()["ok"] is True


def test_analyze_endpoint_mocked(monkeypatch):
    client = TestClient(app)

    def _fake_review(*args, **kwargs):
        return {
            "extracted": {"patient": "x"},
            "deficiencies": [],
            "safety_flags": [],
            "completeness_score": 80,
            "vitals_score": 40,
        }

    def _fake_respond(*args, **kwargs):
        return {
            "immediate_actions": ["Do ABCDE."],
            "monitoring_parameters": ["Recheck SpO2 every 15 minutes."],
            "escalation_criteria": ["Call again if SpO2 drops below 92%."],
            "rationale_bullets": ["Because."],
            "questions_for_participants": ["What is the SpO2?"],
        }

    def _fake_eval(*args, **kwargs):
        return {
            "status": "unknown",
            "summary": "Insufficient data to assess.",
            "suspected_problems": [],
            "red_flags": [],
        }

    monkeypatch.setattr("app.routers.reports.review_report", _fake_review)
    monkeypatch.setattr("app.routers.reports.generate_next_step", _fake_respond)
    monkeypatch.setattr("app.routers.reports.evaluate_patient", _fake_eval)

    r = client.post(
        "/api/v1/reports/analyze",
        json={"session_id": "s1", "report_text": "test", "locale": "en-UK"},
    )
    assert r.status_code == 200
    body = r.json()
    assert body["review"]["completeness_score"] == 80
    assert body["response"]["immediate_actions"][0] == "Do ABCDE."
    assert body["patient_evaluation"]["status"] == "unknown"


def test_review_endpoint_mocked(monkeypatch):
    client = TestClient(app)

    def _fake_review(*args, **kwargs):
        return {
            "extracted": {"patient": "x"},
            "deficiencies": [],
            "safety_flags": [],
            "completeness_score": 88,
            "vitals_score": 60,
        }

    monkeypatch.setattr("app.routers.reports.review_report", _fake_review)

    r = client.post(
        "/api/v1/reports/review",
        json={"session_id": "s1", "report_text": "test", "locale": "en-UK"},
    )

    assert r.status_code == 200
    assert r.json()["completeness_score"] == 88


def test_respond_endpoint_mocked(monkeypatch):
    client = TestClient(app)

    def _fake_review(*args, **kwargs):
        return {
            "extracted": {"patient": "x"},
            "deficiencies": [],
            "safety_flags": [],
            "completeness_score": 81,
            "vitals_score": 20,
        }

    def _fake_respond(*args, **kwargs):
        return {
            "immediate_actions": ["Proceed with ABCDE."],
            "monitoring_parameters": ["Monitor vitals every 15 minutes."],
            "escalation_criteria": ["Call again if condition worsens."],
            "rationale_bullets": ["reason"],
            "questions_for_participants": ["question"],
        }

    monkeypatch.setattr("app.routers.reports.review_report", _fake_review)
    monkeypatch.setattr("app.routers.reports.generate_next_step", _fake_respond)

    r = client.post(
        "/api/v1/reports/respond",
        json={"session_id": "s1", "report_text": "test", "locale": "en-UK"},
    )

    assert r.status_code == 200
    assert r.json()["immediate_actions"][0] == "Proceed with ABCDE."
