import os
import json
import sqlite3

from dotenv import load_dotenv
from mcp.server.fastmcp import FastMCP
from graph.utils.get_inventory_context import get_schema, get_sample_rows
from ingestion.sync_catalog import init_database


load_dotenv()

port = int(os.environ.get("PORT", 8000))

mcp = FastMCP(
    "auto-parts-inventory",
    host="0.0.0.0",
    port=port,
)

@mcp.resource("inventory://schema")
def schema() -> str:
    """
    Provides the SQLite schema for the auto-parts inventory database.

    Use this resource when generating SQL queries or understanding the available
    inventory table, columns, and data types.

    Returns:
        The CREATE TABLE statement or schema description for the inventory table.
    """
    return get_schema()

@mcp.resource("inventory://sample-rows")
def sample_rows() -> str:
    """
    Provides sample rows from the auto-parts inventory database.

    Use this resource to understand the kind of product data stored in the inventory,
    including example values for names, categories, descriptions, prices, stock,
    compatibility, and other fields.

    Returns:
        A small formatted sample of inventory rows.
    """
    return get_sample_rows()

@mcp.tool()
def query_inventory(sql: str) -> str:
    """
    Execute a read-only SQLite SELECT query against the auto-parts inventory database.
    Use LIKE with wildcards for text matching.

    Args:
        sql: The SQLite SELECT query to execute.

    Returns:
        Matching inventory rows or an error message.
    """

    sql_query = sql.strip()

    if not sql_query.lower().startswith("select"):
        return json.dumps({"rows": [], "error": "Only SELECT queries are allowed."})

    try:
        db_path = os.getenv("INVENTORY_DB_PATH")
        if not db_path:
            raise ValueError("INVENTORY_DB_PATH environment variable is not set.")

        with sqlite3.connect(f"file:{db_path}?mode=ro", uri=True) as conn:
            cursor = conn.cursor()
            cursor.execute(sql_query)
            columns = [desc[0] for desc in cursor.description]
            rows = [dict(zip(columns, row)) for row in cursor.fetchall()]

        return json.dumps({"rows": rows, "error": None})

    except Exception as e:
        return json.dumps({"rows": [], "error": str(e)})


if __name__ == "__main__":
    init_database()
    print("Database initialized successfully.")
    transport = os.environ.get("MCP_TRANSPORT", "stdio")
    mcp.run(transport=transport)
