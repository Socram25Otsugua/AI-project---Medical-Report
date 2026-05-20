from __future__ import annotations

import asyncio
from pathlib import Path
from typing import Any, Dict

from fastmcp import Client

from app.config import MCP_SERVER_SCRIPT
from rmrr_mcp.medical_mcp_server import checklist_missing_sections, extract_vitals, triage_priority


def _server_script_path() -> str:
    # Resolve path relative to the backend/ directory.
    here = Path(__file__).resolve()
    backend_root = here.parents[1]
    return str((backend_root / MCP_SERVER_SCRIPT).resolve())


async def call_mcp_tool(tool_name: str, args: Dict[str, Any]) -> Dict[str, Any]:
    # Fast path: execute known local MCP tools in-process to avoid per-call server startup.
    if tool_name == "checklist_missing_sections":
        return checklist_missing_sections(**args)
    if tool_name == "extract_vitals":
        return extract_vitals(**args)
    if tool_name == "triage_priority":
        return triage_priority(**args)

    # Fallback: external MCP invocation for unsupported tools.
    client = Client(_server_script_path())
    async with client:
        result = await client.call_tool(tool_name, args)
        return dict(result.data)


def call_mcp_tool_sync(tool_name: str, args: Dict[str, Any]) -> Dict[str, Any]:
    return asyncio.run(call_mcp_tool(tool_name, args))
