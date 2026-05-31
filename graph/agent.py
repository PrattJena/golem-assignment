import sqlite3
from typing import Any, Dict

from langchain_core.messages import HumanMessage
from langgraph.checkpoint.sqlite import SqliteSaver

from graph.graph import workflow


conn = sqlite3.connect("checkpoints.db", check_same_thread=False)
persistent = SqliteSaver(conn)
app = workflow.compile(checkpointer=persistent)


def stream_agent(question: str, thread_id: str):
    """
    Yields (node_name, output) tuples as each node completes.
    """
    config = {"configurable": {"thread_id": thread_id}}
    for step in app.stream(
        {
            "question": question,
            "messages": [HumanMessage(content=question)],
            "retry_count": 0,
        },
        config,
    ):
        for node_name, output in step.items():
            yield node_name, output