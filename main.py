from dotenv import load_dotenv
load_dotenv()

from ingestion.sync_catalog import init_database
init_database()

import sqlite3
from graph.graph import workflow
from langgraph.checkpoint.sqlite import SqliteSaver
from langchain_core.messages import HumanMessage


def main():
    conn = sqlite3.connect("checkpoints.db", check_same_thread=False)
    memory = SqliteSaver(conn)
    app = workflow.compile(checkpointer=memory)

    thread_id = "session-3"
    config = {"configurable": {"thread_id": thread_id}}

    print("Auto Parts Advisor (type 'quit' to exit)")
    print("=" * 50)

    while True:
        question = input("\nYou: ")

        if question.lower() == "quit" or question.lower() == "exit":
            break

        result = app.invoke(
            {
                "question": question,
                "messages": [HumanMessage(content=question)],
                "retry_count": 0
            },
            config,
        )

        print("\n" + "=" * 50)
        print(result["generation"])
        print("=" * 50)

    conn.close()


if __name__ == "__main__":
    main()