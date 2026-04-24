from __future__ import annotations

import asyncio
from pathlib import Path
from typing import Any, Dict

from fastmcp import Client

from app.settings import settings


def _server_script_path() -> str:
    # Resolve path relative to the backend/ directory.
    here = Path(__file__).resolve()
    backend_root = here.parents[2]
    return str((backend_root / settings.mcp_server_script).resolve())


async def call_mcp_tool(tool_name: str, args: Dict[str, Any]) -> Dict[str, Any]:
    client = Client(_server_script_path())
    async with client:
        result = await client.call_tool(tool_name, args)
        # fastmcp returns an object with .data (serializable dict)
        return dict(result.data)


def call_mcp_tool_sync(tool_name: str, args: Dict[str, Any]) -> Dict[str, Any]:
    return asyncio.run(call_mcp_tool(tool_name, args))
