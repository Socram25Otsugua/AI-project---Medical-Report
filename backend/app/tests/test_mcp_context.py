from app import mcp


def test_get_report_mcp_context_with_checklist(monkeypatch):
    monkeypatch.setattr(
        mcp.context,
        "mcp_extract_vitals",
        type("T", (), {"invoke": staticmethod(lambda args: {"spo2_percent": 93})}),
    )
    monkeypatch.setattr(
        mcp.context,
        "mcp_triage_priority",
        type("T", (), {"invoke": staticmethod(lambda args: {"priority": "urgent"})}),
    )
    monkeypatch.setattr(
        mcp.context,
        "mcp_checklist_missing_sections",
        type("T", (), {"invoke": staticmethod(lambda args: {"missing": ["identity"]})}),
    )

    out = mcp.get_report_mcp_context("example report", include_checklist=True)

    assert out["vitals"]["spo2_percent"] == 93
    assert out["triage"]["priority"] == "urgent"
    assert out["missing_sections"]["missing"] == ["identity"]


def test_get_report_mcp_context_without_checklist(monkeypatch):
    monkeypatch.setattr(
        mcp.context,
        "mcp_extract_vitals",
        type("T", (), {"invoke": staticmethod(lambda args: {"heart_rate_bpm": 120})}),
    )
    monkeypatch.setattr(
        mcp.context,
        "mcp_triage_priority",
        type("T", (), {"invoke": staticmethod(lambda args: {"priority": "critical"})}),
    )

    out = mcp.get_report_mcp_context("example report", include_checklist=False)

    assert out["vitals"]["heart_rate_bpm"] == 120
    assert out["triage"]["priority"] == "critical"
    assert "missing_sections" not in out


def test_vitals_coverage_score_all_slots():
    from app.mcp import vitals_coverage_score

    assert (
        vitals_coverage_score(
            {
                "heart_rate_bpm": 80,
                "spo2_percent": 97,
                "resp_rate_per_min": 16,
                "bp_systolic": 120,
                "bp_diastolic": 80,
                "temp_c": 36.5,
            }
        )
        == 100
    )


def test_vitals_coverage_score_partial():
    from app.mcp import vitals_coverage_score

    assert vitals_coverage_score({"spo2_percent": 95}) == 20
    assert vitals_coverage_score({}) == 0
