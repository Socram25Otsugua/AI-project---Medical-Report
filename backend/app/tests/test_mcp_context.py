from app import mcp


def test_get_report_mcp_context_with_checklist(monkeypatch):
    monkeypatch.setattr(
        mcp.context,
        "call_mcp_tool_sync",
        lambda tool_name, args: {
            "extract_vitals": {"spo2_percent": 93},
            "triage_priority": {"priority": "urgent"},
            "checklist_missing_sections": {"missing": ["identity"]},
        }[tool_name],
    )

    out = mcp.get_report_mcp_context("example report", include_checklist=True)

    assert out["vitals"]["spo2_percent"] == 93
    assert out["triage"]["priority"] == "urgent"
    assert out["missing_sections"]["missing"] == ["identity"]


def test_get_report_mcp_context_without_checklist(monkeypatch):
    monkeypatch.setattr(
        mcp.context,
        "call_mcp_tool_sync",
        lambda tool_name, args: {
            "extract_vitals": {"heart_rate_bpm": 120},
            "triage_priority": {"priority": "critical"},
        }[tool_name],
    )

    out = mcp.get_report_mcp_context("example report", include_checklist=False)

    assert out["vitals"]["heart_rate_bpm"] == 120
    assert out["triage"]["priority"] == "critical"
    assert "missing_sections" not in out


def test_build_enriched_mcp_context_adds_scenario_and_guidelines(monkeypatch):
    from types import SimpleNamespace

    monkeypatch.setattr(
        mcp,
        "get_report_mcp_context",
        lambda report_text, include_checklist=True: {"vitals": {"spo2_percent": 95}, "triage": {"priority": "ok"}},
    )
    monkeypatch.setattr(
        mcp,
        "scenario_context_mcp",
        SimpleNamespace(
            get_scenario=lambda _text: {"success": True, "scenario": {"detected_type": "default"}},
        ),
    )
    monkeypatch.setattr(
        mcp,
        "medical_guidelines_mcp",
        SimpleNamespace(get_context_string=lambda _text, k=3: "guidelines"),
    )

    out = mcp.build_enriched_mcp_context("report")

    assert out["scenario_context"]["success"] is True
    assert out["guidelines_context"] == "guidelines"


def test_vitals_coverage_score_all_slots():
    assert (
        mcp.vitals_coverage_score(
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
    assert mcp.vitals_coverage_score({"spo2_percent": 95}) == 20
    assert mcp.vitals_coverage_score({}) == 0
