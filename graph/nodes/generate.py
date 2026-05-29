from typing import Dict, Any
from graph.state import GraphState
from graph.chains.generate_sql import generate_sql_chain


def generate_sql_node(state: GraphState) -> Dict[str, Any]:
    """
    Generate SQL query. If error_message exists from previous attempt,
    include it in the question so the LLM can fix the mistake.
    """
    question = state["question"]
    error_message = state.get("error_message", "")
    
    if error_message:
        question = f"""The previous SQL query failed with this error:
        Error: {error_message}
        Please fix the SQL query and try again. Original question: {question}"""
    
    result = generate_sql_chain.invoke({"question": question})
    
    return {
        "sql_query": result.sql_query,
        "error_message": "",
    }