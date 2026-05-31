import sqlite3
from typing import Any, Dict

from langchain_core.messages import HumanMessage
from langgraph.checkpoint.sqlite import SqliteSaver

from graph.graph import workflow


conn = sqlite3.connect("checkpoints.db", check_same_thread=False)
memory = SqliteSaver(conn)
app = workflow.compile(checkpointer=memory)


def run_agent(question: str, thread_id: str) -> Dict[str, Any]:
    """
    Run the auto-parts advisor graph for a specific conversation thread.

    Same thread_id = continue existing conversation.
    New thread_id = start a separate conversation.
    """
    config = {"configurable": {"thread_id": thread_id}}

    return app.invoke(
        {
            "question": question,
            "messages": [HumanMessage(content=question)],
            "retry_count": 0,
        },
        config,
    )