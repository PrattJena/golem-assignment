import asyncio
import json
from typing import Any, Dict

from graph.state import GraphState
from graph.utils.mcp_client import get_mcp_session, tool_result_to_text


async def _call_query_inventory_tool(sql: str) -> dict:
    """
    Calls the query_inventory tool exposed by the MCP server.

    The MCP server returns a JSON string shaped like:
        {
            "rows": [],
            "error": null
        }
    """
    async with get_mcp_session() as session:
        result = await session.call_tool(
            "query_inventory",
            {"sql": sql},
        )

        raw_text = tool_result_to_text(result)

        if not raw_text:
            return {
                "rows": [],
                "error": "MCP tool returned no content.",
            }

        return json.loads(raw_text)


def execute_sql(state: GraphState) -> Dict[str, Any]:
    """
    Executes the generated SQL query through the MCP inventory server.

    If execution succeeds:
        - stores rows in query_results
        - clears error_message

    If execution fails:
        - stores empty query_results
        - stores the error in error_message
    """
    sql_query = state["sql_query"]

    try:
        result = asyncio.run(_call_query_inventory_tool(sql_query))

        if result.get("error"):
            return {
                "query_results": [],
                "error_message": result["error"],
            }

        return {
            "query_results": result.get("rows", []),
            "error_message": "",
        }

    except Exception as e:
        return {
            "query_results": [],
            "error_message": str(e),
        }