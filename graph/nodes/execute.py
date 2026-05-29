import os
import sqlite3
from typing import Dict, Any, List
from graph.state import GraphState

def execute_sql(state: GraphState)-> Dict[str, Any]:
    """
    Executes the generated SQL query against the SQLite database.

    If execution succeeds:
        - stores rows in query_results
        - clears error_message

    If execution fails:
        - stores empty query_results
        - stores the error in error_message
    """
    sql_query = state["sql_query"]

    if not sql_query.lower().startswith("select"):
        return {
            "query_results": [],
            "error_message": "Only SELECT queries are allowed.",
        }
    
    conn = None
    
    try:
        conn = sqlite3.connect(os.getenv("INVENTORY_DB_PATH"))
        cursor = conn.cursor()
        cursor.execute(sql_query)
        rows = cursor.fetchall()
        columns = [desc[0] for desc in cursor.description] 
        query_results: List[Dict[str, Any]] = [ dict(zip(columns, row)) for row in rows ]
        return {
            "query_results": query_results,
            "error_message": "",
        }
    except Exception as e:
        return {
            "query_results": [],
            "error_message": str(e),
        }
    finally:
        if conn:
            conn.close()
    

        
