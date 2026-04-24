from pathlib import Path

from app import mcp_client


def test_server_script_path_resolves_under_backend_root():
    path = Path(mcp_client._server_script_path())
    assert path.is_absolute()
    assert path.name == "medical_mcp_server.py"
    assert "rmrr_mcp" in str(path)


def test_call_mcp_tool_sync_delegates_to_asyncio_run(monkeypatch):
    captured = {"called": False}

    async def _fake_call_mcp_tool(tool_name, args):
        return {"tool_name": tool_name, "args": args}

    def _fake_run(coro):
        captured["called"] = True
        # Close coroutine to avoid RuntimeWarning in tests.
        coro.close()
        return {"ok": True}

    monkeypatch.setattr(mcp_client, "call_mcp_tool", _fake_call_mcp_tool)
    monkeypatch.setattr(mcp_client.asyncio, "run", _fake_run)

    result = mcp_client.call_mcp_tool_sync("extract_vitals", {"report_text": "x"})

    assert captured["called"] is True
    assert result == {"ok": True}
