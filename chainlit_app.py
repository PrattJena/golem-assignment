from dotenv import load_dotenv

load_dotenv()

from ingestion.sync_catalog import init_database

init_database()

import uuid

import chainlit as cl

from graph.agent import stream_agent
from graph.chains.stream_response import stream_response_chain

step_labels = {
    "resolve_query": "Understanding your question...",
    "generate_sql": "Searching inventory...",
    "execute_sql": "Running query...",
    "recommend": "Generating recommendations...",
}


@cl.on_chat_start
async def on_chat_start():
    thread_id = cl.user_session.get("id") or str(uuid.uuid4())
    cl.user_session.set("thread_id", thread_id)
    await cl.Message(
        content="Hi! I can help you find auto parts. Describe your vehicle issue or what you need."
    ).send()


@cl.on_message
async def on_message(message: cl.Message):
    thread_id = cl.user_session.get("thread_id")
    if not thread_id:
        thread_id = str(uuid.uuid4())
        cl.user_session.set("thread_id", thread_id)

    generation = ""
    resolved_question = ""

    for node_name, output in await cl.make_async(list)(
        stream_agent(message.content, thread_id)
    ):
        label = step_labels.get(node_name, node_name)
        async with cl.Step(name=label) as s:
            s.output = "Done"

        if node_name == "resolve_query":
            resolved_question = output.get("resolved_question", "")
            if output.get("intent") == "off_topic":
                await cl.Message(content=output.get("generation", "")).send()
                return

        if node_name == "recommend":
            generation = output.get("generation", "")

    if not generation:
        await cl.Message(content="Sorry, I could not generate a response.").send()
        return

    question = resolved_question or message.content
    msg = cl.Message(content="")
    async for chunk in stream_response_chain.astream(
        {
            "question": question,
            "recommendations": generation,
        }
    ):
        await msg.stream_token(chunk)
    await msg.send()
