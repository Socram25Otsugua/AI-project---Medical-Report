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
        }

    def _fake_respond(*args, **kwargs):
        return {
            "next_step_message": "Do ABCDE.",
            "rationale_bullets": ["Because."],
            "questions_for_participants": ["What is the SpO2?"],
        }

    monkeypatch.setattr("app.main.review_report", _fake_review)
    monkeypatch.setattr("app.main.generate_next_step", _fake_respond)

    r = client.post(
        "/api/v1/reports/analyze",
        json={"session_id": "s1", "report_text": "test", "locale": "en-UK"},
    )
    assert r.status_code == 200
    body = r.json()
    assert body["review"]["completeness_score"] == 80
    assert "next_step_message" in body["response"]

