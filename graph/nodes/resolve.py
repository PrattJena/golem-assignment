from typing import Any, Dict

from langchain_core.messages import AIMessage

from graph.chains.resolve_query import resolve_query_chain
from graph.state import GraphState

OFF_TOPIC_RESPONSE = "I can only help with auto parts. Please describe your vehicle issue or the part you need."


def resolve_query_node(state: GraphState) -> Dict[str, Any]:
    """
    Classifies the latest user message and rewrites it into a standalone
    auto-parts request when appropriate.
    """
    question = state["question"]
    messages = state.get("messages", [])
    previous_resolved_question = state.get("resolved_question", "")
    history_messages = messages[:-1]

    history = "\n".join(f"{m.type}: {m.content}" for m in history_messages[-6:])

    result = resolve_query_chain.invoke(
        {
            "previous_resolved_question": previous_resolved_question,
            "history": history,
            "question": question,
        }
    )

    print(f"\n--- INTENT ---\n{result.intent}\n--- END INTENT ---\n")
    print(
        f"\n--- RESOLVED QUESTION ---\n{result.resolved_question}\n--- END RESOLVED QUESTION ---\n"
    )

    if result.intent == "off_topic":
        return {
            "intent": result.intent,
            "resolved_question": "",
            "generation": OFF_TOPIC_RESPONSE,
            "query_results": [],
            "error_message": "",
            "messages": [AIMessage(content=OFF_TOPIC_RESPONSE)],
        }

    return {
        "intent": result.intent,
        "resolved_question": result.resolved_question,
    }
