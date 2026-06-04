import os
from contextlib import asynccontextmanager
from pathlib import Path
from typing import Any

from mcp import ClientSession, StdioServerParameters
from mcp.client.stdio import stdio_client
from mcp.client.streamable_http import streamable_http_client


ROOT_DIR = Path(__file__).resolve().parents[2]
MCP_SERVER_PATH = ROOT_DIR / "mcp_server.py"

MCP_TRANSPORT = os.getenv("MCP_TRANSPORT", "stdio")
MCP_SERVER_URL = os.getenv("MCP_SERVER_URL", "http://localhost:8000/mcp")


server_params = StdioServerParameters(
    command="uv",
    args=["run", "python", str(MCP_SERVER_PATH)],
)


@asynccontextmanager
async def get_mcp_session():
    """
    Create an MCP session using either local STDIO or remote Streamable HTTP.

    Local/dev:
        MCP_TRANSPORT=stdio

    Remote/deployed:
        MCP_TRANSPORT=streamable-http
        MCP_SERVER_URL=https://your-server.com/mcp
    """
    if MCP_TRANSPORT == "streamable-http":
        async with streamable_http_client(MCP_SERVER_URL) as (read, write, _):
            async with ClientSession(read, write) as session:
                await session.initialize()
                yield session
    else:
        async with stdio_client(server_params) as (read, write):
            async with ClientSession(read, write) as session:
                await session.initialize()
                yield session


def tool_result_to_text(result: Any) -> str:
    """
    Extract plain text from an MCP tool result.
    """
    if not getattr(result, "content", None):
        return ""

    first = result.content[0]

    if hasattr(first, "text"):
        return first.text

    return str(first)


def resource_result_to_text(result: Any) -> str:
    """
    Extract plain text from an MCP resource result.
    """
    if not getattr(result, "contents", None):
        return ""

    first = result.contents[0]

    if hasattr(first, "text"):
        return first.text

    return str(first)