from typing import Dict, Any

from graph.state import GraphState
from graph.chains.generate_sql import generate_sql_chain


def generate_sql_node(state: GraphState) -> Dict[str, Any]:
    """
    Generate SQL query from the resolved question if present. If error_message exists from previous attempt, include it in the question so the LLM can fix the mistake.
    """
    question = state.get("resolved_question") or state["question"]
    error_message = state.get("error_message", "")
    retry_count = state.get("retry_count", 0)
    
    print(f"\n--- QUESTION SENT TO SQL LLM ---\n{question}\n--- END QUESTION ---\n")

    if error_message:
        question = f"""{question}

        The previous SQL query failed with this error:
        Error: {error_message}
        Please fix the SQL query and try again."""
    
    try:
        result = generate_sql_chain.invoke({"question": question})
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