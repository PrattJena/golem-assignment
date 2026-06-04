import asyncio
from typing import Any, Dict

from graph.chains.generate_sql import generate_sql_chain
from graph.state import GraphState
from graph.utils.mcp_client import get_mcp_session, resource_result_to_text


async def _get_inventory_context_from_mcp() -> tuple[str, str]:
    """
    Read inventory schema and sample rows from MCP resources.
    """
    async with get_mcp_session() as session:
        schema_result = await session.read_resource("inventory://schema")
        sample_rows_result = await session.read_resource("inventory://sample-rows")

        schema = resource_result_to_text(schema_result)
        sample_rows = resource_result_to_text(sample_rows_result)

        return schema, sample_rows


def generate_sql_node(state: GraphState) -> Dict[str, Any]:
    """
    Generate SQL query from the resolved question if present.

    If error_message exists from a previous attempt, include it in the question
    so the LLM can fix the mistake.
    """
    question = state.get("resolved_question") or state["question"]
    error_message = state.get("error_message", "")
    retry_count = state.get("retry_count", 0)

    print(f"\n--- QUESTION SENT TO SQL LLM ---\n{question}\n--- END QUESTION ---\n")

    if error_message:
        question = f"""{question}

The previous SQL query failed with this error:
Error: {error_message}

Please fix the SQL query and try again.
"""

    try:
        schema, sample_rows = asyncio.run(_get_inventory_context_from_mcp())

        result = generate_sql_chain.invoke(
            {
                "question": question,
                "schema": schema,
                "sample_rows": sample_rows,
            }
        )

    except Exception as e:
        return {
            "sql_query": "SELECT * FROM inventory WHERE 1=0",
            "error_message": f"SQL generation failed: {str(e)}",
            "query_results": [],
            "retry_count": retry_count + 1,
        }

    print(f"\n--- GENERATED SQL ---\n{result.sql_query}\n--- END SQL ---\n")

    return {
        "sql_query": result.sql_query,
        "error_message": "",
        "retry_count": retry_count + 1,
    }