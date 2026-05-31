from typing import Dict, Any

from langchain_core.messages import AIMessage
from graph.state import GraphState
from graph.chains.generate_sql import generate_sql_chain


def generate_sql_node(state: GraphState) -> Dict[str, Any]:
    """
    Generate SQL query. If error_message exists from previous attempt,
    include it in the question so the LLM can fix the mistake.
    Includes conversation history for multi-turn context.
    """
    question = state["question"]
    error_message = state.get("error_message", "")
    retry_count = state.get("retry_count", 0)
    messages = state.get("messages", [])

    human_messages = [m.content for m in messages if m.type == "human"]
    if human_messages:
        question = " ".join(human_messages)
    print(f"\n--- QUESTION ---\n{question}\n--- END QUESTION ---\n")
    if error_message:
        question = f"""{question}

        The previous SQL query failed with this error:
        Error: {error_message}
        Please fix the SQL query and try again."""
    
    result = generate_sql_chain.invoke({"question": question})
    print(f"\n--- GENERATED SQL ---\n{result.sql_query}\n--- END SQL ---\n")
    
    return {
        "sql_query": result.sql_query,
        "error_message": "",
        "retry_count": retry_count + 1,
    }