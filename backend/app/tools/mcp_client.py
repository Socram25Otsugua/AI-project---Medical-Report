from __future__ import annotations

from typing import Any, Dict

from rmrr_mcp.medical_mcp_server import checklist_missing_sections, extract_vitals, triage_priority


async def call_mcp_tool(tool_name: str, args: Dict[str, Any]) -> Dict[str, Any]:
    if tool_name == "checklist_missing_sections":
        return checklist_missing_sections(**args)
    if tool_name == "extract_vitals":
        return extract_vitals(**args)
    if tool_name == "triage_priority":
        return triage_priority(**args)
    raise ValueError(f"Unknown MCP tool: {tool_name}")


def call_mcp_tool_sync(tool_name: str, args: Dict[str, Any]) -> Dict[str, Any]:
    import asyncio

    return asyncio.run(call_mcp_tool(tool_name, args))
