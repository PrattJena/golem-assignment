from dotenv import load_dotenv
load_dotenv()

import uuid
import chainlit as cl

from ingestion.sync_catalog import init_database
from graph.agent import run_agent

@cl.on_chat_start
async def on_chat_start():
    """
    Runs whenever a new Chainlit chat starts.
    """
    init_database()

    # Use Chainlit session id if available, otherwise fallback to UUID.
    thread_id = cl.user_session.get("id") or str(uuid.uuid4())
    cl.user_session.set("thread_id", thread_id)
    print(f"[CHAINLIT] Started chat with thread_id: {thread_id}")

    await cl.Message(
        content=(
            "Hi! I can help you find auto parts from the inventory. "
            "Describe your vehicle issue, trip, or part need."
        )
    ).send()


@cl.on_message
async def on_message(message: cl.Message):
    """
    Runs whenever the user sends a message.
    """
    thread_id = cl.user_session.get("thread_id")
    print(f"[CHAINLIT] Message using thread_id: {thread_id}")
    if not thread_id:
        thread_id = str(uuid.uuid4())
        cl.user_session.set("thread_id", thread_id)
        print(f"[CHAINLIT] Assigned new thread_id: {thread_id}")

    result = await cl.make_async(run_agent)(
        question=message.content,
        thread_id=thread_id,
    )

    response = result.get(
        "generation",
        "Sorry, I could not generate a response.",
    )

    await cl.Message(content=response).send()