from fastapi.testclient import TestClient

from app.main import app


def test_history_list_and_create_and_delete(monkeypatch):
    client = TestClient(app)

    store = []

    def _fake_list_reports(limit=50):
        return list(store)[:limit]

    def _fake_create_report(doc):
        out = dict(doc)
        out["id"] = "r1"
        store.insert(0, out)
        return out

    def _fake_delete_report(report_id: str):
        before = len(store)
        store[:] = [x for x in store if x.get("id") != report_id]
        return len(store) != before

    def _fake_clear_reports():
        n = len(store)
        store.clear()
        return n

    monkeypatch.setattr("app.routers.history.list_reports", _fake_list_reports)
    monkeypatch.setattr("app.routers.history.create_report", _fake_create_report)
    monkeypatch.setattr("app.routers.history.delete_report", _fake_delete_report)
    monkeypatch.setattr("app.routers.history.clear_reports", _fake_clear_reports)

    # Create
    payload = {
        "createdAt": 123,
        "sourceLabel": "Patient A",
        "reportText": "text",
        "result": {"review": {"completeness_score": 80, "deficiencies": [], "safety_flags": [], "vitals_score": 0, "vitals_feedback": []}, "response": {"immediate_actions": ["x"], "monitoring_parameters": [], "escalation_criteria": [], "rationale_bullets": [], "questions_for_participants": []}},
        "mode": "form",
        "indicators": {"patient_name": "Patient A"},
    }
    r = client.post("/api/v1/reports/history", json=payload)
    assert r.status_code == 200
    assert r.json()["id"] == "r1"

    # List
    r2 = client.get("/api/v1/reports/history")
    assert r2.status_code == 200
    assert len(r2.json()) == 1

    # Delete one
    r3 = client.delete("/api/v1/reports/history/r1")
    assert r3.status_code == 200
    assert r3.json()["deleted"] is True

    # Clear all
    client.post("/api/v1/reports/history", json=payload)
    r4 = client.delete("/api/v1/reports/history")
    assert r4.status_code == 200
    assert r4.json()["deleted"] == 1

