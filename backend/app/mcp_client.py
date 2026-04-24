import asyncio
from typing import Any, Dict

from app.services.mcp_client import _server_script_path, call_mcp_tool as _call_mcp_tool


async def call_mcp_tool(tool_name: str, args: Dict[str, Any]) -> Dict[str, Any]:
    return await _call_mcp_tool(tool_name, args)


def call_mcp_tool_sync(tool_name: str, args: Dict[str, Any]) -> Dict[str, Any]:
    return asyncio.run(call_mcp_tool(tool_name, args))


__all__ = ["_server_script_path", "call_mcp_tool", "call_mcp_tool_sync"]

