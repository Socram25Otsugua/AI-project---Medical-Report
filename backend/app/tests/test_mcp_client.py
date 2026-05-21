from pathlib import Path

from app.tools.mcp_client import call_mcp_tool_sync


def test_call_mcp_tool_sync_runs_known_tools():
    out = call_mcp_tool_sync(
        "extract_vitals",
        {"report_text": "Heart rate: 80 bpm\nSpO2: 97%"},
    )
    assert "heart_rate_bpm" in out or "spo2_percent" in out


def test_call_mcp_tool_sync_rejects_unknown_tool():
    try:
        call_mcp_tool_sync("unknown_tool", {})
        assert False, "expected ValueError"
    except ValueError as exc:
        assert "Unknown MCP tool" in str(exc)
